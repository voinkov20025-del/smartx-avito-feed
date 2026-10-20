from __future__ import annotations

import csv
import io
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

CSV_URL = "https://raw.githubusercontent.com/epogrebnyak/ru-cities/main/assets/towns.csv"
OUT = Path("feeds/Moncler_Cardigan_3000_4900.xml")

PRICE = "4900"
PHONE = "79175142375"
SIZES = "46 / 48 / 50 / 52"

VARIANTS = [
    {
        "code": "BLK",
        "title_color": "черный",
        "desc_color": "Черный",
        "color": "Черный",
        "color_name": "Черный",
        "prefix": "moncler_black",
        "ext": "jpg",
    },
    {
        "code": "GRY",
        "title_color": "серый",
        "desc_color": "Серый",
        "color": "Серый",
        "color_name": "Серый",
        "prefix": "moncler_gray",
        "ext": "png",
    },
    {
        "code": "KHK",
        "title_color": "хаки",
        "desc_color": "Хаки",
        "color": "Зеленый",
        "color_name": "Хаки",
        "prefix": "moncler_khaki",
        "ext": "png",
    },
]


def add(parent: ET.Element, tag: str, text: str) -> ET.Element:
    el = ET.SubElement(parent, tag)
    el.text = text
    return el


def load_cities() -> list[str]:
    req = urllib.request.Request(CSV_URL, headers={"User-Agent": "avito-feed-generator/1.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        text = response.read().decode("utf-8")

    rows = list(csv.DictReader(io.StringIO(text)))
    rows.sort(key=lambda r: float(r.get("population") or 0), reverse=True)

    cities: list[str] = []
    seen: set[str] = set()
    for row in rows:
        city = (row.get("city") or "").strip()
        if city and city not in seen:
            seen.add(city)
            cities.append(city)
        if len(cities) == 1000:
            break

    if len(cities) != 1000:
        raise RuntimeError(f"Expected 1000 unique cities, got {len(cities)}")
    return cities


def description(color: str) -> str:
    return (
        "<p><strong>Мужской кардиган Moncler — LUX качество.</strong></p>"
        f"<p><strong>Цвет:</strong> {color}.</p>"
        f"<p><strong>Размеры в наличии:</strong> {SIZES}.<br>"
        "Напишите в чат — поможем подобрать подходящий размер.</p>"
        "<p>Комбинированная модель с утеплённой стёганой передней частью, "
        "капюшоном и трикотажными рукавами. Подходит для повседневных образов "
        "и прохладной погоды.</p>"
        "<p><strong>Почему выбирают нас:</strong><br>"
        "— честные фото и описание;<br>"
        "— быстро отвечаем в чате;<br>"
        "— перед отправкой можем сделать фото / видео товара;<br>"
        "— аккуратная и быстрая отправка.</p>"
        "<p><strong>Безопасная покупка:</strong><br>"
        "Оформление через Авито Доставку.<br>"
        "<strong>Без переводов на карту.</strong><br>"
        "Товар можно проверить при получении, а если не подойдёт — отказаться "
        "по правилам Авито.</p>"
        "<p><strong>Перед заказом напишите в чат:</strong><br>"
        "— подтвердим наличие нужного цвета и размера;<br>"
        "— ответим на вопросы;<br>"
        "— поможем оформить заказ.</p>"
        "<p><strong>Цена: 4 900 ₽</strong></p>"
    )


def build() -> None:
    cities = load_cities()
    root = ET.Element("Ads", {"formatVersion": "3", "target": "Avito.ru"})

    for city_no, city in enumerate(cities, start=1):
        idx = f"{city_no:04d}"
        multi_name = f"MONCLER-CARD-{idx}"

        for variant in VARIANTS:
            ad = ET.SubElement(root, "Ad")
            add(ad, "Id", f"MC-CARD-20261020-{idx}-{variant['code']}")
            add(ad, "ListingFee", "Package")
            add(ad, "ContactPhone", PHONE)
            add(ad, "Address", city)
            add(ad, "ContactMethod", "В сообщениях")
            add(ad, "Title", f"Кардиган Moncler мужской {variant['title_color']} LUX качество")
            add(ad, "Description", description(variant["desc_color"]))
            add(ad, "Category", "Одежда, обувь, аксессуары")
            add(ad, "Price", PRICE)
            add(ad, "GoodsType", "Мужская одежда")
            add(ad, "Condition", "Новое с биркой")
            add(ad, "Season", "Демисезон")
            add(ad, "AdType", "Товар приобретен на продажу")
            add(ad, "Brand", "Moncler")

            # Актуальная цепочка параметров одежды Avito:
            # Тип товара -> Предмет одежды -> Размер.
            add(ad, "Apparel", "Джемперы, свитеры, кардиганы")
            add(ad, "ApparelType", "Кофта")
            # Не делаем отдельные карточки по размерам. Обязательное поле
            # заполняем допустимым значением «Без размера», а фактические
            # размеры 46/48/50/52 остаются в описании.
            add(ad, "Size", "Без размера")

            add(ad, "Color", variant["color"])
            add(ad, "ColorName", variant["color_name"])
            add(ad, "MultiItem", "Да")
            add(ad, "MultiName", multi_name)

            images = ET.SubElement(ad, "Images")
            for photo_no in range(1, 7):
                ET.SubElement(
                    images,
                    "Image",
                    {
                        "name": f"{variant['prefix']}_{photo_no:02d}.{variant['ext']}"
                    },
                )

    ET.indent(root, space="  ")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(OUT, encoding="utf-8", xml_declaration=True)

    check = ET.parse(OUT).getroot()
    ads = check.findall("Ad")
    ids = [ad.findtext("Id") for ad in ads]
    if len(ads) != 3000 or len(set(ids)) != 3000:
        raise RuntimeError("Invalid ad/ID count")
    if any(ad.findtext("Apparel") != "Джемперы, свитеры, кардиганы" for ad in ads):
        raise RuntimeError("Invalid Apparel")
    if any(ad.findtext("ApparelType") != "Кофта" for ad in ads):
        raise RuntimeError("Invalid ApparelType")
    if any(ad.findtext("Size") != "Без размера" for ad in ads):
        raise RuntimeError("Invalid Size")
    if any(len(ad.find("Images").findall("Image")) != 6 for ad in ads):
        raise RuntimeError("Every ad must contain exactly 6 images")

    print(
        f"Generated {OUT}: {len(ads)} ads, {len(cities)} cities, price {PRICE}, "
        "ApparelType=Кофта, Size=Без размера"
    )


if __name__ == "__main__":
    build()
