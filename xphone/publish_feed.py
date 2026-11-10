#!/usr/bin/env python3
"""Convert XPhone manual-upload package to two URL-based Avito feeds."""
from collections import Counter
from pathlib import Path
from zipfile import ZipFile
from urllib.parse import quote
import io
import sys
import xml.etree.ElementTree as ET

RAW_ROOT = "https://raw.githubusercontent.com/voinkov20025-del/smartx-avito-feed/main/xphone/images/"
EXPECTED = {"xphone-feed-part-1.xml","xphone-feed-part-2.xml","XPhone_PHOTOS_103_JPG.zip"}

def publish(package_path, dest):
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    image_dir = dest / "images"
    image_dir.mkdir(exist_ok=True)
    with ZipFile(package_path) as package:
        assert EXPECTED.issubset(package.namelist()), "Incomplete XPhone release package"
        with ZipFile(io.BytesIO(package.read("XPhone_PHOTOS_103_JPG.zip"))) as photos:
            names = photos.namelist()
            assert len(names) == len(set(names)) == 103, "Expected 103 distinct JPG"
            assert all("/" not in name and name.lower().endswith(".jpg") for name in names)
            for name in names:
                raw = photos.read(name)
                assert raw[:3] == b"\xff\xd8\xff", "Broken JPEG: "+name
                (image_dir / name).write_bytes(raw)
        photo_names = set(names)
        ids = set()
        addresses = set()
        address_cover_pairs = set()
        covers = Counter()
        refs = 0
        for part in (1,2):
            root = ET.fromstring(package.read(f"xphone-feed-part-{part}.xml"))
            assert root.tag == "Ads" and root.get("target") == "Avito.ru"
            ads = root.findall("Ad")
            assert len(ads) == 20000, f"Part {part} has {len(ads)} ads"
            for ad in ads:
                identity = ad.findtext("Id")
                assert identity and identity not in ids, "Duplicate or missing ID: "+str(identity)
                ids.add(identity)
                address = ad.findtext("Address")
                assert address, "Missing address"
                addresses.add(address)
                images = ad.find("Images")
                assert images is not None and 1 <= len(images) <= 10
                for position, img in enumerate(images):
                    name = img.attrib.pop("name", None)
                    assert name in photo_names, "Image missing from archive: "+str(name)
                    if position == 0:
                        pair = (address, name)
                        assert pair not in address_cover_pairs, "Duplicate city+SKU: " + str(pair)
                        address_cover_pairs.add(pair)
                    assert "url" not in img.attrib, "Unexpected original URL"
                    img.set("url", RAW_ROOT + quote(name))
                    refs += 1
                    if position == 0:
                        covers[name] += 1
            ET.ElementTree(root).write(dest / f"feed-part-{part}.xml", encoding="utf-8", xml_declaration=True)
        assert len(ids) == 40000, "Unexpected number of unique IDs"
        assert len(addresses) == 409, "Unexpected number of pickup addresses"
        assert len(covers) == 98, "Unexpected number of SKU covers"
        assert len(address_cover_pairs) == 40000, "Duplicate address+SKU pairs"
        (dest / "VALIDATION.txt").write_text(
            f"ADS: {len(ids)}\nADDRESSES: {len(addresses)}\nSKU COVERS: {len(covers)}\n"
            f"JPG: {len(photo_names)}\nIMAGE REFS: {refs}\n"
            "STATUS: STRUCTURAL PASS. AVITO ACCEPTANCE NOT VERIFIED.\n",encoding="utf-8")
        print(f"PASS: {len(ids)} ads, {len(addresses)} addresses, {len(photo_names)} photos, {refs} image URL references")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: publish_feed.py PACKAGE.zip DESTINATION")
    publish(sys.argv[1], sys.argv[2])
