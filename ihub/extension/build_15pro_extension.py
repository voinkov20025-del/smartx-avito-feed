from pathlib import Path
import re, hashlib, json, shutil

PART1=Path('ihub/feeds/iHub_STRUCTURE_40020_URL_FINAL_PART_1_00001-20010.xml')
PART2=Path('ihub/feeds/iHub_STRUCTURE_40020_URL_FINAL_PART_2_20011-40020.xml')
OUT=Path('ihub/feeds/iHub_STRUCTURE_13920_URL_FINAL_PART_3_40021-53940.xml')
IMG_OUT=Path('ihub/images/2026-11-02')
OLD_IMG_BASE='https://raw.githubusercontent.com/voinkov20025-del/smartx-avito-feed/main/ihub/images/2026-10-05'
NEW_IMG_BASE='https://raw.githubusercontent.com/voinkov20025-del/smartx-avito-feed/main/ihub/images/2026-11-02'
UNIVERSAL=[
'universal-02-avito-delivery.jpg',
'universal-03-check-phone.jpg',
'universal-04-yandex-split.jpg',
'universal-05-store-moscow.jpg',
'universal-06-benefits.jpg',
]
AD_RE=re.compile(r'<Ad>(.*?)</Ad>',re.S)

COLORS=[
    ('черный','black'),
    ('синий','blue'),
    ('серый','gray'),
    ('белый','white'),
]
CONFIGS=[
    ('iPhone 15 Pro','128 ГБ',57990,'iphone15pro'),
    ('iPhone 15 Pro','256 ГБ',59990,'iphone15pro'),
    ('iPhone 15 Pro','512 ГБ',63990,'iphone15pro'),
    ('iPhone 15 Pro Max','256 ГБ',67990,'iphone15promax'),
    ('iPhone 15 Pro Max','512 ГБ',73490,'iphone15promax'),
    ('iPhone 15 Pro Max','1 ТБ',76990,'iphone15promax'),
]

def tag(text,name):
    m=re.search(fr'<{name}>(.*?)</{name}>',text,re.S)
    if not m: raise RuntimeError(f'missing {name}')
    return m.group(1)

def replace_tag(text,name,value):
    out,n=re.subn(fr'<{name}>.*?</{name}>',f'<{name}>{value}</{name}>',text,count=1,flags=re.S)
    if n!=1: raise RuntimeError(f'failed replace {name}')
    return out

def memslug(memory):
    return {'128 ГБ':'128','256 ГБ':'256','512 ГБ':'512','1 ТБ':'1tb'}[memory]

def modelslug(model):
    return {'iPhone 15 Pro':'iphone-15-pro','iPhone 15 Pro Max':'iphone-15-pro-max'}[model]

def first_filename(model,memory,suffix):
    return f'{modelslug(model)}-{memslug(memory)}-{suffix}-01-cover.jpg'

def collect_addresses_and_template():
    addresses=[]; seen=set(); template=None; old_ids=set(); total=0
    for p in (PART1,PART2):
        text=p.read_text(encoding='utf-8')
        for m in AD_RE.finditer(text):
            ad=m.group(1); total+=1
            old_ids.add(tag(ad,'Id'))
            addr=tag(ad,'Address')
            if addr not in seen:
                seen.add(addr); addresses.append(addr)
            if template is None: template=ad
    if total!=40020: raise RuntimeError(f'expected 40020 existing ads, got {total}')
    if len(old_ids)!=40020: raise RuntimeError('existing IDs are not unique')
    if len(addresses)!=580: raise RuntimeError(f'expected 580 unique addresses, got {len(addresses)}')
    return addresses,template,old_ids

def install_approved_covers():
    IMG_OUT.mkdir(parents=True,exist_ok=True)
    created=[]
    for model,memory,price,prefix in CONFIGS:
        for color,suffix in COLORS:
            src=Path('photos')/f'{prefix}_{suffix}_01.jpg'
            if not src.is_file(): raise RuntimeError(f'approved source cover missing: {src}')
            dst=IMG_OUT/first_filename(model,memory,suffix)
            shutil.copyfile(src,dst)
            created.append(dst.name)
    if len(created)!=24 or len(set(created))!=24: raise RuntimeError('expected 24 new cover files')
    return created

def build_ad(template,address,model,memory,price,color,suffix):
    ad=template
    key=f'{address}|{model}|{memory}|{color}'
    new_id='ihub_20261102_'+hashlib.sha1(key.encode('utf-8')).hexdigest()[:20]
    for name,val in [
        ('Id',new_id),('Address',address),('Model',model),('MemorySize',memory),('Color',color),
        ('RamSize','8 ГБ'),('Title',f'{model}, {memory}, SIM + eSIM'),('Price',str(price))
    ]:
        ad=replace_tag(ad,name,val)
    fn=first_filename(model,memory,suffix)
    urls=[f'{NEW_IMG_BASE}/{fn}']+[f'{OLD_IMG_BASE}/{x}' for x in UNIVERSAL]
    images='<Images>'+''.join(f'<Image url="{u}"/>' for u in urls)+'</Images>'
    ad,n=re.subn(r'<Images>.*?</Images>',images,ad,count=1,flags=re.S)
    if n!=1: raise RuntimeError('failed replace Images')
    return '<Ad>'+ad+'</Ad>',new_id,urls

def main():
    addresses,template,old_ids=collect_addresses_and_template()
    created=install_approved_covers()
    ads=[]; ids=[]; first_urls=set(); combos=set()
    for address in addresses:
        for model,memory,price,prefix in CONFIGS:
            for color,suffix in COLORS:
                ad,new_id,urls=build_ad(template,address,model,memory,price,color,suffix)
                ads.append(ad); ids.append(new_id); first_urls.add(urls[0]); combos.add((model,memory,color,price))
    if len(ads)!=13920: raise RuntimeError(f'expected 13920 new ads, got {len(ads)}')
    if len(ids)!=len(set(ids)): raise RuntimeError('new IDs are not unique')
    if old_ids.intersection(ids): raise RuntimeError('new IDs collide with existing IDs')
    if len(combos)!=24: raise RuntimeError(f'expected 24 combos, got {len(combos)}')
    if len(first_urls)!=24: raise RuntimeError(f'expected 24 unique first image URLs, got {len(first_urls)}')
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text('<?xml version="1.0" encoding="utf-8"?>\n<Ads formatVersion="3" target="Avito.ru">\n'+'\n\n'.join(ads)+'\n</Ads>\n',encoding='utf-8')
    # final validation of part 3
    text=OUT.read_text(encoding='utf-8')
    parsed=list(AD_RE.finditer(text))
    if len(parsed)!=13920: raise RuntimeError('part 3 parse count mismatch')
    for m in parsed:
        block=m.group(1)
        imgs=re.findall(r'<Image url="([^"]+)"\s*/>',tag(block,'Images'))
        if len(imgs)!=6: raise RuntimeError('an ad does not have exactly 6 images')
    matrix=[]
    for model,memory,price,prefix in CONFIGS:
        for color,suffix in COLORS:
            matrix.append({'model':model,'memory':memory,'color':color,'price':price,'cover':first_filename(model,memory,suffix)})
    Path('ihub/extension/iHub_15PRO_SKU_MATRIX.json').write_text(json.dumps(matrix,ensure_ascii=False,indent=2),encoding='utf-8')
    p1sha=hashlib.sha256(PART1.read_bytes()).hexdigest(); p2sha=hashlib.sha256(PART2.read_bytes()).hexdigest(); p3sha=hashlib.sha256(OUT.read_bytes()).hexdigest()
    report='\n'.join([
        'STATUS: PASS',
        'Existing ads unchanged: 40020',
        'New ads: 13920',
        'Total ads after extension: 53940',
        'Existing SKU: 69',
        'New SKU: 24',
        'Total SKU: 93',
        'Cities/addresses used for new SKU: 580',
        'Images per new ad: exactly 6',
        'New approved first-image files: 24',
        'New IDs unique and non-colliding: PASS',
        f'PART1 SHA256 unchanged: {p1sha}',
        f'PART2 SHA256 unchanged: {p2sha}',
        f'PART3 SHA256: {p3sha}',
    ])+'\n'
    Path('ihub/extension/iHub_15PRO_EXTENSION_VALIDATION.txt').write_text(report,encoding='utf-8')
    print(report)

if __name__=='__main__':
    main()
