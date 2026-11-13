#!/usr/bin/env python3
"""Change ONLY descriptions of both published XPhone feeds."""
from pathlib import Path
from html import escape
from hashlib import sha256
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent

DESCRIPTION = """📱 Ваш следующий iPhone — здесь!

Любимые модели Apple, стильные цвета и разные объёмы памяти. Подберём iPhone для красивых фотографий, работы, общения и всего, что важно именно вам.

✨ Поможем определиться с выбором
Расскажем о различиях между моделями, ответим на вопросы и уточним состояние и комплектацию выбранного телефона. Напишите свои пожелания — предложим подходящие варианты.

📍 Самовывоз в Москве
Заберите iPhone лично. Адрес и удобное время согласуем в переписке.

📦 Авито Доставка по всей России
Заказывайте из своего города через Авито. Бережно упакуем телефон, чтобы он был защищён в дороге.

💬 Напишите нам прямо сейчас
Укажите модель, цвет и объём памяти — уточним актуальную стоимость и наличие.

❤️ Добавляйте объявление в избранное, чтобы не потерять!"""

PATTERN = re.compile(rb"<Description>.*?</Description>", re.DOTALL)
REPLACEMENT = ("<Description>" + escape(DESCRIPTION, quote=False).replace("\n", "&lt;br&gt;") + "</Description>").encode("utf-8")
PLACEHOLDER = b"<Description>__DESCRIPTION_ONLY__</Description>"
ids = set()
addresses = set()
image_urls = set()
results = []

for part in (1, 2):
    path = ROOT / f"feed-part-{part}.xml"
    original = path.read_bytes()
    new, count = PATTERN.subn(lambda _: REPLACEMENT, original)
    assert count == 20000, (path, count)
    assert PATTERN.sub(PLACEHOLDER, original) == PATTERN.sub(PLACEHOLDER, new), "Non-description XML content changed"
    tree = ET.fromstring(new)
    ads = tree.findall("Ad")
    assert tree.tag == "Ads" and len(ads) == 20000
    for ad in ads:
        id_ = ad.findtext("Id")
        address = ad.findtext("Address")
        text = ad.findtext("Description")
        assert id_ and id_ not in ids
        assert address
        assert text == DESCRIPTION.replace("\n", "<br>"), "Description differs from approved text"
        ids.add(id_)
        addresses.add(address)
        for image in ad.findall("Images/Image"):
            assert image.get("url", "").startswith("https://"), "Missing HTTPS photo"
            image_urls.add(image.get("url"))
    path.write_bytes(new)
    results.append((part, count, len(new), sha256(new).hexdigest()))

assert len(ids) == 40000, len(ids)
assert len(addresses) == 409, len(addresses)
assert len(image_urls) == 103, len(image_urls)
report = (
    "XPhone — updated descriptions, 2026-11-13\n"
    + "Only the contents of <Description> tags changed.\n"
    + "User-provided description preserved verbatim; line breaks rendered as <br>.\n"
    + "IDs and all other XML fields remain unchanged, confirmed by byte-for-byte masked comparison.\n"
    + f"ADS={len(ids)}\nADDRESSES={len(addresses)}\nUNIQUE_IMAGE_URLS={len(image_urls)}\n"
    + ''.join(f'PART_{p}: ads={cnt} size={size} sha256={sha}\n' for p,cnt,size,sha in results)
    + "STATUS=PASS (GitHub XML checks; Avito processing after update not yet verified)\n"
)
(ROOT / "DESCRIPTION_UPDATE_REPORT.txt").write_text(report, encoding="utf-8")
print(report)
