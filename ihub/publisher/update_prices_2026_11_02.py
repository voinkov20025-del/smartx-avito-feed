from pathlib import Path
import re

FILES = [
    Path('ihub/feeds/ihub-final-part-1-00001-20000.xml'),
    Path('ihub/feeds/ihub-final-part-2-20001-40000.xml'),
]

PRICE_OVERRIDES = {
    ('iPhone 13 Pro', '256 ГБ'): 38490,
    ('iPhone 14', '128 ГБ'): 31990,
    ('iPhone 14', '256 ГБ'): 33490,
    ('iPhone 14 Pro', '128 ГБ'): 43490,
    ('iPhone 14 Pro', '256 ГБ'): 46990,
    ('iPhone 14 Pro', '512 ГБ'): 49990,
    ('iPhone 15', '128 ГБ'): 39990,
    ('iPhone 15', '256 ГБ'): 43990,
    ('iPhone 15 Pro', '128 ГБ'): 52990,
    ('iPhone 15 Pro', '256 ГБ'): 55490,
    ('iPhone 15 Pro', '512 ГБ'): 58990,
    ('iPhone 15 Pro', '1 ТБ'): 62990,
    ('iPhone 15 Pro Max', '256 ГБ'): 62990,
    ('iPhone 15 Pro Max', '512 ГБ'): 67990,
    ('iPhone 15 Pro Max', '1 ТБ'): 69990,
}

AD_RE = re.compile(r'<Ad>(.*?)</Ad>', re.S)

def tag(inner, name):
    m = re.search(fr'<{name}>(.*?)</{name}>', inner, re.S)
    if not m:
        raise RuntimeError(f'missing tag {name}')
    return m.group(1)

def replace_price(inner, price):
    out, n = re.subn(r'<Price>.*?</Price>', f'<Price>{price}</Price>', inner, count=1, flags=re.S)
    if n != 1:
        raise RuntimeError('Price replace failed')
    return out

changed = 0
total = 0
counts = {k: 0 for k in PRICE_OVERRIDES}

for path in FILES:
    text = path.read_text(encoding='utf-8')
    def repl(m):
        global changed, total
        inner = m.group(1)
        total += 1
        key = (tag(inner, 'Model'), tag(inner, 'MemorySize'))
        if key not in PRICE_OVERRIDES:
            return m.group(0)
        target = PRICE_OVERRIDES[key]
        old = int(tag(inner, 'Price'))
        counts[key] += 1
        if old != target:
            changed += 1
            inner = replace_price(inner, target)
        return '<Ad>' + inner + '</Ad>'
    new_text = AD_RE.sub(repl, text)
    path.write_text(new_text, encoding='utf-8')

if total != 40000:
    raise RuntimeError(f'expected 40000 ads, got {total}')

expected_counts = {
    ('iPhone 13 Pro', '256 ГБ'): 2060,
    ('iPhone 14', '128 ГБ'): 1648,
    ('iPhone 14', '256 ГБ'): 1648,
    ('iPhone 14 Pro', '128 ГБ'): 1648,
    ('iPhone 14 Pro', '256 ГБ'): 1648,
    ('iPhone 14 Pro', '512 ГБ'): 1648,
    ('iPhone 15', '128 ГБ'): 1652,
    ('iPhone 15', '256 ГБ'): 1652,
    ('iPhone 15 Pro', '128 ГБ'): 1652,
    ('iPhone 15 Pro', '256 ГБ'): 1652,
    ('iPhone 15 Pro', '512 ГБ'): 1652,
    ('iPhone 15 Pro', '1 ТБ'): 1652,
    ('iPhone 15 Pro Max', '256 ГБ'): 1652,
    ('iPhone 15 Pro Max', '512 ГБ'): 1652,
    ('iPhone 15 Pro Max', '1 ТБ'): 1652,
}
if counts != expected_counts:
    raise RuntimeError(f'price target counts mismatch: {counts}')

report = Path('ihub/extension/iHub_PRICE_UPDATE_2026-11-02.txt')
lines = [
    'STATUS: PASS',
    'Total ads: 40000',
    f'Ads changed this run: {changed}',
    'Requested target ads: 25168',
    'Interpretation: iPhone 15 Pro 156 -> 256 GB',
]
for (model, memory), price in PRICE_OVERRIDES.items():
    lines.append(f'{model} | {memory} | {price} RUB | ads={counts[(model,memory)]}')
report.write_text('\n'.join(lines) + '\n', encoding='utf-8')
print(report.read_text(encoding='utf-8'))
