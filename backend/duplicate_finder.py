"""Perceptual hash tabanlı duplicate resim tespiti."""

from pathlib import Path
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed


def compute_phash(path: Path):
    """Bir resmin perceptual hash'ini hesapla. Hata varsa None döndür."""
    try:
        import imagehash
        from PIL import Image
        img = Image.open(path).convert('RGB')
        return str(imagehash.phash(img))
    except Exception:
        return None


def find_duplicates(
    image_paths: List[Path],
    threshold: int = 8,
    max_workers: int = 4
) -> List[List[str]]:
    """
    Verilen dosyalar arasındaki duplikatları bul.
    threshold: Hamming distance eşiği (0=aynı, <8 benzer)
    Döndürür: Gruplar listesi — her grup birbirine benzer dosya yolları.
    """
    import imagehash

    hashes: Dict[str, str] = {}  # path → hash_str

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(compute_phash, p): str(p) for p in image_paths}
        for fut in as_completed(futures):
            path_str = futures[fut]
            h = fut.result()
            if h:
                hashes[path_str] = h

    # Hash'leri karşılaştır
    paths = list(hashes.keys())
    visited = set()
    groups: List[List[str]] = []

    for i, p1 in enumerate(paths):
        if p1 in visited:
            continue
        group = [p1]
        h1 = imagehash.hex_to_hash(hashes[p1])
        for j in range(i + 1, len(paths)):
            p2 = paths[j]
            if p2 in visited:
                continue
            h2 = imagehash.hex_to_hash(hashes[p2])
            if (h1 - h2) <= threshold:
                group.append(p2)
                visited.add(p2)
        if len(group) > 1:
            visited.add(p1)
            groups.append(group)

    return groups
