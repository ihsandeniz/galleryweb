import os
import sqlite3
from pathlib import Path
from typing import Optional

class CacheManager:
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @staticmethod
    def _like_escape(s: str) -> str:
        """Escape % and _ for use in SQLite LIKE patterns (ESCAPE '\\')."""
        return s.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')

    @classmethod
    def _dir_prefix_like(cls, gallery_dir: str) -> str:
        """Bir klasör altındaki tüm yolları eşleyen LIKE deseni üret.
        Yollar OS-native ayraçla saklanır (Linux '/', Windows '\\'); sabit '/'
        kullanmak Windows'ta klasör-kapsamlı sorguları (etiket/çöp/puan) BOŞ
        döndürüyordu → os.sep ile OS'a duyarlı hale getirildi (Windows uyumu)."""
        base = gallery_dir.rstrip('/\\')
        return cls._like_escape(base) + cls._like_escape(os.sep) + '%'

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=5000")
        c = conn.cursor()

        c.execute("""
            CREATE TABLE IF NOT EXISTS thumbnails (
                original_path TEXT PRIMARY KEY,
                thumb_path TEXT NOT NULL,
                mtime REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_mtime ON thumbnails(mtime)")

        c.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                path TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ===== Tags =====
        c.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS image_tags (
                image_path TEXT NOT NULL,
                tag_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (image_path, tag_id),
                FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
            )
        """)

        # ===== Trash =====
        c.execute("""
            CREATE TABLE IF NOT EXISTS trash (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_path TEXT NOT NULL,
                trash_path TEXT NOT NULL,
                deleted_at REAL DEFAULT (strftime('%s', 'now'))
            )
        """)

        # ===== Notes =====
        c.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                image_path TEXT PRIMARY KEY,
                content TEXT NOT NULL DEFAULT '',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ===== Ratings =====
        c.execute("""
            CREATE TABLE IF NOT EXISTS ratings (
                image_path TEXT PRIMARY KEY,
                stars INTEGER NOT NULL CHECK(stars BETWEEN 1 AND 5),
                rated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ===== Bookmarks =====
        c.execute("""
            CREATE TABLE IF NOT EXISTS bookmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE NOT NULL,
                label TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ===== Albums =====
        c.execute("""
            CREATE TABLE IF NOT EXISTS albums (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                cover_path TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS album_images (
                album_id INTEGER REFERENCES albums(id) ON DELETE CASCADE,
                image_path TEXT NOT NULL,
                added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (album_id, image_path)
            )
        """)

        # ===== Image Metadata (for Timeline + Map) =====
        c.execute("""
            CREATE TABLE IF NOT EXISTS image_metadata (
                path TEXT PRIMARY KEY,
                exif_datetime TEXT,
                mtime REAL,
                gps_latitude REAL,
                gps_longitude REAL
            )
        """)

        conn.commit()
        conn.close()

    # ========== Thumbnail Cache ==========

    def set_thumbnail(self, original_path: str, thumb_path: str, mtime: float):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT OR REPLACE INTO thumbnails (original_path, thumb_path, mtime) VALUES (?, ?, ?)",
            (original_path, thumb_path, mtime)
        )
        conn.commit()
        conn.close()

    def get_mtime(self, original_path: str) -> Optional[float]:
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT mtime FROM thumbnails WHERE original_path = ?", (original_path,)
        ).fetchone()
        conn.close()
        return row[0] if row else None

    def clear_cache(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM thumbnails")
        conn.commit()
        conn.close()

    # ========== Favorites ==========

    def toggle_favorite(self, path: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        exists = conn.execute("SELECT path FROM favorites WHERE path = ?", (path,)).fetchone()
        if exists:
            conn.execute("DELETE FROM favorites WHERE path = ?", (path,))
            is_fav = False
        else:
            conn.execute("INSERT INTO favorites (path) VALUES (?)", (path,))
            is_fav = True
        conn.commit()
        conn.close()
        return is_fav

    def get_favorites(self) -> list:
        conn = sqlite3.connect(self.db_path)
        result = [row[0] for row in conn.execute(
            "SELECT path FROM favorites ORDER BY created_at DESC"
        ).fetchall()]
        conn.close()
        return result

    # ========== Tags ==========

    def add_tag(self, image_path: str, tag: str) -> bool:
        """Tag ekle; True → yeni eklendi, False → zaten vardı."""
        tag = tag.strip().lower()
        if not tag:
            return False
        conn = sqlite3.connect(self.db_path)
        conn.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag,))
        row = conn.execute("SELECT id FROM tags WHERE name = ?", (tag,)).fetchone()
        if not row:
            conn.close()
            return False
        tag_id = row[0]
        try:
            conn.execute(
                "INSERT INTO image_tags (image_path, tag_id) VALUES (?, ?)", (image_path, tag_id)
            )
            added = True
        except sqlite3.IntegrityError:
            added = False
        conn.commit()
        conn.close()
        return added

    def remove_tag(self, image_path: str, tag: str) -> bool:
        tag = tag.strip().lower()
        conn = sqlite3.connect(self.db_path)
        row = conn.execute("SELECT id FROM tags WHERE name = ?", (tag,)).fetchone()
        if not row:
            conn.close()
            return False
        conn.execute(
            "DELETE FROM image_tags WHERE image_path = ? AND tag_id = ?", (image_path, row[0])
        )
        removed = conn.execute("SELECT changes()").fetchone()[0] > 0
        conn.commit()
        conn.close()
        return removed

    def get_image_tags(self, image_path: str) -> list:
        conn = sqlite3.connect(self.db_path)
        result = [row[0] for row in conn.execute("""
            SELECT t.name FROM tags t
            JOIN image_tags it ON t.id = it.tag_id
            WHERE it.image_path = ?
            ORDER BY t.name
        """, (image_path,)).fetchall()]
        conn.close()
        return result

    def get_all_tags_for_dir(self, gallery_dir: str) -> list:
        """Verilen dizindeki resimlerin tüm etiketlerini say."""
        conn = sqlite3.connect(self.db_path)
        result = [
            {"name": row[0], "count": row[1]}
            for row in conn.execute("""
                SELECT t.name, COUNT(it.image_path) as cnt
                FROM tags t
                JOIN image_tags it ON t.id = it.tag_id
                WHERE it.image_path LIKE ? ESCAPE '\\'
                GROUP BY t.name
                ORDER BY cnt DESC, t.name
            """, (self._dir_prefix_like(gallery_dir),)).fetchall()
        ]
        conn.close()
        return result

    def get_images_with_tags(self, tags: list) -> list:
        """Tüm belirtilen etiketlere sahip resim yollarını döndür (AND mantığı)."""
        if not tags:
            return []
        tags = [t.strip().lower() for t in tags]
        conn = sqlite3.connect(self.db_path)
        placeholders = ','.join('?' * len(tags))
        result = [row[0] for row in conn.execute(f"""
            SELECT image_path FROM image_tags
            WHERE tag_id IN (SELECT id FROM tags WHERE name IN ({placeholders}))
            GROUP BY image_path
            HAVING COUNT(DISTINCT tag_id) = ?
        """, tags + [len(tags)]).fetchall()]
        conn.close()
        return result

    # ========== Notes ==========

    def get_note(self, image_path: str) -> str:
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT content FROM notes WHERE image_path = ?", (image_path,)
        ).fetchone()
        conn.close()
        return row[0] if row else ""

    def set_note(self, image_path: str, content: str):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT OR REPLACE INTO notes (image_path, content, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
            (image_path, content)
        )
        conn.commit()
        conn.close()

    # ========== Trash ==========

    def add_to_trash(self, original_path: str, trash_path: str) -> int:
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO trash (original_path, trash_path) VALUES (?, ?)",
            (original_path, trash_path)
        )
        trash_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.commit()
        conn.close()
        return trash_id

    def remove_from_trash(self, trash_id: int) -> Optional[tuple]:
        """Kaydı sil ve (original_path, trash_path) döndür."""
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT original_path, trash_path FROM trash WHERE id = ?", (trash_id,)
        ).fetchone()
        if row:
            conn.execute("DELETE FROM trash WHERE id = ?", (trash_id,))
            conn.commit()
        conn.close()
        return row

    def get_trash_items(self, gallery_dir: str) -> list:
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute("""
            SELECT id, original_path, trash_path, deleted_at
            FROM trash
            WHERE original_path LIKE ? ESCAPE '\\'
            ORDER BY deleted_at DESC
        """, (self._dir_prefix_like(gallery_dir),)).fetchall()
        conn.close()
        return [
            {"id": r[0], "original": r[1], "trash": r[2], "deleted_at": r[3]}
            for r in rows
        ]

    # ========== Ratings ==========

    def set_rating(self, image_path: str, stars: int):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT OR REPLACE INTO ratings (image_path, stars) VALUES (?, ?)",
            (image_path, stars)
        )
        conn.commit()
        conn.close()

    def get_rating(self, image_path: str) -> Optional[int]:
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT stars FROM ratings WHERE image_path = ?", (image_path,)
        ).fetchone()
        conn.close()
        return row[0] if row else None

    def delete_rating(self, image_path: str):
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM ratings WHERE image_path = ?", (image_path,))
        conn.commit()
        conn.close()

    def get_rating_distribution(self) -> dict:
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(
            "SELECT stars, COUNT(*) FROM ratings GROUP BY stars"
        ).fetchall()
        conn.close()
        dist = {i: 0 for i in range(1, 6)}
        for stars, count in rows:
            dist[stars] = count
        return dist

    def get_ratings_for_dir(self, gallery_dir: str) -> dict:
        """Returns {image_path: stars} for all rated images in gallery_dir."""
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(
            "SELECT image_path, stars FROM ratings WHERE image_path LIKE ? ESCAPE '\\'",
            (self._dir_prefix_like(gallery_dir),)
        ).fetchall()
        conn.close()
        return {row[0]: row[1] for row in rows}

    def get_all_ratings(self) -> dict:
        """Returns {image_path: stars} for ALL rated images (all dirs)."""
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute("SELECT image_path, stars FROM ratings").fetchall()
        conn.close()
        return {row[0]: row[1] for row in rows}

    def get_all_tags(self) -> list:
        """Returns tag counts across ALL directories."""
        conn = sqlite3.connect(self.db_path)
        result = [
            {"name": row[0], "count": row[1]}
            for row in conn.execute("""
                SELECT t.name, COUNT(it.image_path) as cnt
                FROM tags t
                JOIN image_tags it ON t.id = it.tag_id
                GROUP BY t.name
                ORDER BY cnt DESC, t.name
            """).fetchall()
        ]
        conn.close()
        return result

    # ========== Bookmarks ==========

    def add_bookmark(self, path: str, label: str = "") -> int:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                "INSERT INTO bookmarks (path, label) VALUES (?, ?)", (path, label or path)
            )
            bm_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.commit()
        except sqlite3.IntegrityError:
            row = conn.execute(
                "SELECT id FROM bookmarks WHERE path = ?", (path,)
            ).fetchone()
            bm_id = row[0] if row else -1
        conn.close()
        return bm_id

    def remove_bookmark(self, bm_id: int) -> bool:
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM bookmarks WHERE id = ?", (bm_id,))
        removed = conn.execute("SELECT changes()").fetchone()[0] > 0
        conn.commit()
        conn.close()
        return removed

    def get_bookmarks(self) -> list:
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(
            "SELECT id, path, label FROM bookmarks ORDER BY created_at DESC"
        ).fetchall()
        conn.close()
        return [{"id": r[0], "path": r[1], "label": r[2]} for r in rows]

    # ──────────────────────────────────────────────
    # Albums
    # ──────────────────────────────────────────────

    def create_album(self, name: str, description: str = "") -> int:
        conn = sqlite3.connect(self.db_path)
        try:
            cur = conn.execute(
                "INSERT INTO albums (name, description) VALUES (?, ?)", (name, description)
            )
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

    def get_albums(self) -> list:
        conn = sqlite3.connect(self.db_path)
        try:
            rows = conn.execute(
                "SELECT id, name, description, cover_path, created_at FROM albums ORDER BY created_at DESC"
            ).fetchall()
            result = []
            for r in rows:
                count = conn.execute(
                    "SELECT COUNT(*) FROM album_images WHERE album_id=?", (r[0],)
                ).fetchone()[0]
                result.append({"id": r[0], "name": r[1], "description": r[2],
                                "cover_path": r[3], "created_at": r[4], "count": count})
            return result
        finally:
            conn.close()

    def get_album(self, album_id: int) -> Optional[dict]:
        conn = sqlite3.connect(self.db_path)
        try:
            row = conn.execute(
                "SELECT id, name, description, cover_path, created_at FROM albums WHERE id=?", (album_id,)
            ).fetchone()
            if not row:
                return None
            images = [r[0] for r in conn.execute(
                "SELECT image_path FROM album_images WHERE album_id=? ORDER BY added_at", (album_id,)
            ).fetchall()]
            return {"id": row[0], "name": row[1], "description": row[2],
                    "cover_path": row[3], "created_at": row[4], "images": images}
        finally:
            conn.close()

    def update_album(self, album_id: int, name: str = None, description: str = None, cover_path: str = None):
        conn = sqlite3.connect(self.db_path)
        try:
            if name is not None:
                conn.execute("UPDATE albums SET name=? WHERE id=?", (name, album_id))
            if description is not None:
                conn.execute("UPDATE albums SET description=? WHERE id=?", (description, album_id))
            if cover_path is not None:
                conn.execute("UPDATE albums SET cover_path=? WHERE id=?", (cover_path, album_id))
            conn.commit()
        finally:
            conn.close()

    def delete_album(self, album_id: int):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("DELETE FROM albums WHERE id=?", (album_id,))
            conn.commit()
        finally:
            conn.close()

    def add_images_to_album(self, album_id: int, image_paths: list):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.executemany(
                "INSERT OR IGNORE INTO album_images (album_id, image_path) VALUES (?, ?)",
                [(album_id, p) for p in image_paths]
            )
            # Set cover if not set
            conn.execute(
                "UPDATE albums SET cover_path=? WHERE id=? AND cover_path IS NULL",
                (image_paths[0] if image_paths else None, album_id)
            )
            conn.commit()
        finally:
            conn.close()

    def remove_image_from_album(self, album_id: int, image_path: str):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                "DELETE FROM album_images WHERE album_id=? AND image_path=?", (album_id, image_path)
            )
            conn.commit()
        finally:
            conn.close()

    # ──────────────────────────────────────────────
    # Batch Move — metadata migration
    # ──────────────────────────────────────────────

    def move_metadata(self, old_path: str, new_path: str):
        """Tags, notes, favorites, ratings → old_path'i new_path ile güncelle"""
        conn = sqlite3.connect(self.db_path)
        try:
            for table, col in [
                ('favorites', 'path'),
                ('notes', 'path'),
                ('ratings', 'image_path'),
                ('image_tags', 'image_path'),
            ]:
                conn.execute(
                    f"UPDATE {table} SET {col}=? WHERE {col}=?",
                    (new_path, old_path)
                )
            conn.commit()
        finally:
            conn.close()

    def invalidate_thumbnail(self, path: str):
        """Thumbnail cache kaydını sil (dosya değişince)"""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("DELETE FROM thumbnails WHERE original_path=?", (path,))
            conn.commit()
        finally:
            conn.close()

    # ===== Image Metadata (Timeline + Map) =====

    def get_image_metadata(self, path: str) -> dict | None:
        conn = sqlite3.connect(self.db_path)
        try:
            row = conn.execute(
                "SELECT exif_datetime, mtime, gps_latitude, gps_longitude FROM image_metadata WHERE path=?",
                (path,)
            ).fetchone()
            if row:
                return {"exif_datetime": row[0], "mtime": row[1],
                        "gps_latitude": row[2], "gps_longitude": row[3]}
            return None
        finally:
            conn.close()

    def upsert_image_metadata(self, path: str, exif_datetime: str = None,
                               mtime: float = None, gps_latitude: float = None,
                               gps_longitude: float = None):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT INTO image_metadata (path, exif_datetime, mtime, gps_latitude, gps_longitude)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(path) DO UPDATE SET
                    exif_datetime=COALESCE(excluded.exif_datetime, exif_datetime),
                    mtime=COALESCE(excluded.mtime, mtime),
                    gps_latitude=COALESCE(excluded.gps_latitude, gps_latitude),
                    gps_longitude=COALESCE(excluded.gps_longitude, gps_longitude)
            """, (path, exif_datetime, mtime, gps_latitude, gps_longitude))
            conn.commit()
        finally:
            conn.close()
