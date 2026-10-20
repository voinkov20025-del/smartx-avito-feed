#!/usr/bin/env python3
import json
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

CITY_URL = 'https://raw.githubusercontent.com/pensnarik/russian-cities/master/russian-cities.json'
OUT = Path('feeds/Moncler_Cardigan_3000_4900.xml')
PRICE = '4900'
PHONE = '79175142375'
SIZES = '46 / 48 / 50 / 52'

VARIANTS = [
    {
        'code': 'BLK',
        'title_color': 'черный',
        'desc_color': 'Черный',
        'color': 'Черный',
        'color_name': 'Черный',
        'images': [f'moncler_black_{i:02d}.jpg' for i in range(1, 7)],
    },
    {
        'code': 'GRY',
        'title_color': 'серый',
        'desc_color': 'Серый',
        'color': 'Серый',
        'color_name': 'Серый',
        'images': [f'moncler_gray_{i:02d}.png' for i in range(1, 7)],
    },
    {
        'code': 'KHK',
        'title_color': 'хаки',
        'desc_color': 'Хаки',
        'color': 'Зеленый',
        'color_name': 'Хаки',
        'images': [f'moncler_khaki_{i:02d}.png' for i in range(1, 7)],
    },
]

def sub(ad, tag, text):
    ET.SubElement(ad, tag).text = text

with urllib.request.urlopen(CITY_URL, timeout=30) as r:
    cities_data = json.load(r)

# 1000 крупнейших городов по населению: меньше риска проблем с географией, чем у мелких населённых пунктов.
cities_data.sort(key=lambda x: int(x.get('population') or 0), reverse=True)
cities = []
seen = set()
for item in cities_data:
    name = str(item.get('name') or '').strip()
    if name and name not in seen:
        seen.add(name)
        cities.append(name)
    if len(cities) == 1000:
        break

if len(cities) != 1000:
    raise RuntimeError(f'Expected 1000 unique cities, got {len(cities)}')

root = ET.Element('Ads', {'formatVersion': '3', 'target': 'Avito.ru'})
for city_num, city in enumerate(cities, start=1):
    multi_name = f'MONCLER-CARD-{city_num:04d}'
    for v in VARIANTS:
        ad = ET.SubElement(root, 'Ad')
        sub(ad, 'Id', f'MC-CARD-20261020-{city_num:04d}-{v["code"]}')
        sub(ad, 'ListingFee', 'Package')
        sub(ad, 'ContactPhone', PHONE)
        sub(ad, 'Address', city)
        sub(ad, 'ContactMethod', 'В сообщениях')
        sub(ad, 'Title', f'Кардиган Moncler мужской {v["title_color"]} LUX качество')

        description = f'''<p><strong>Мужской кардиган Moncler — LUX качество.</strong></p>
<p><strong>Цвет:</strong> {v['desc_color']}.</p>
<p><strong>Размеры в наличии:</strong> {SIZES}.<br>Напишите в чат — поможем подобрать подходящий размер.</p>
<p>Комбинированная модель с утеплённой стёганой передней частью, капюшоном и трикотажными рукавами. Подходит для повседневных образов и прохладной погоды.</p>
<p><strong>Почему выбирают нас:</strong><br>— честные фото и описание;<br>— быстро отвечаем в чате;<br>— перед отправкой можем сделать фото / видео товара;<br>— аккуратная и быстрая отправка.</p>
<p><strong>Безопасная покупка:</strong><br>Оформление через Авито Доставку.<br>Без переводов на карту.<br>Товар можно проверить при получении, а если не подойдёт — отказаться по правилам Авито.</p>
<p><strong>Перед заказом напишите в чат:</strong><br>— подтвердим наличие нужного цвета и размера;<br>— ответим на вопросы;<br>— поможем оформить заказ.</p>
<p><strong>Цена: 4 900 ₽</strong></p>'''
        sub(ad, 'Description', description)
        sub(ad, 'Category', 'Одежда, обувь, аксессуары')
        sub(ad, 'Price', PRICE)
        sub(ad, 'GoodsType', 'Мужская одежда')
        sub(ad, 'Condition', 'Новое с биркой')
        sub(ad, 'Season', 'Демисезон')
        sub(ad, 'AdType', 'Товар приобретен на продажу')
        sub(ad, 'Brand', 'Moncler')
        sub(ad, 'Apparel', 'Джемперы, свитеры, кардиганы')
        sub(ad, 'Color', v['color'])
        sub(ad, 'ColorName', v['color_name'])
        # Размеры намеренно не размножаются по отдельным объявлениям и не задаются тегом Size.
        sub(ad, 'MultiItem', 'Да')
        sub(ad, 'MultiName', multi_name)
        images = ET.SubElement(ad, 'Images')
        for image_name in v['images']:
            ET.SubElement(images, 'Image', {'name': image_name})

ET.indent(root, space='  ')
OUT.parent.mkdir(parents=True, exist_ok=True)
ET.ElementTree(root).write(OUT, encoding='utf-8', xml_declaration=True)

# Проверки
check = ET.parse(OUT).getroot()
ads = check.findall('Ad')
ids = [a.findtext('Id') for a in ads]
addresses = [a.findtext('Address') for a in ads]
colors = [a.findtext('ColorName') for a in ads]
assert len(ads) == 3000
assert len(ids) == len(set(ids)) == 3000
assert len(set(addresses)) == 1000
assert colors.count('Черный') == 1000
assert colors.count('Серый') == 1000
assert colors.count('Хаки') == 1000
assert all(a.find('Size') is None for a in ads)
assert all(len(a.find('Images').findall('Image')) == 6 for a in ads)
print(f'OK: {len(ads)} ads, 1000 cities, 3 colors, no Size tags, price {PRICE}')
