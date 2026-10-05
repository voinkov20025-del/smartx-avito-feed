from pathlib import Path
import re, json, hashlib

BASE='https://raw.githubusercontent.com/voinkov20025-del/smartx-avito-feed/main/ihub/images/2026-10-05'
SRC=[Path('/tmp/ihub_bundle/source_part1.xml'), Path('/tmp/ihub_bundle/source_part2.xml')]
OUT=[Path('ihub/feeds/iHub_STRUCTURE_40020_URL_FINAL_PART_1_00001-20010.xml'), Path('ihub/feeds/iHub_STRUCTURE_40020_URL_FINAL_PART_2_20011-40020.xml')]
IMG_DIR=Path('ihub/images/2026-10-05')
UNIVERSAL=['universal-02-avito-delivery.jpg','universal-03-check-phone.jpg','universal-04-yandex-split.jpg','universal-05-store-moscow.jpg','universal-06-benefits.jpg']
AD_RE=re.compile(rb'<Ad>(.*?)</Ad>', re.S)
IMG_RE=re.compile(rb'<Images>.*?</Images>', re.S)

def extract(ad, tag):
    m=re.search(rb'<'+tag.encode()+rb'>(.*?)</'+tag.encode()+rb'>', ad, re.S)
    if not m: raise RuntimeError(f'missing <{tag}>')
    return m.group(1).decode('utf-8').strip()

def cover_filename(model, memory, color):
    model_slug={'iPhone 12':'iphone-12','iPhone 12 mini':'iphone-12-mini','iPhone 13':'iphone-13','iPhone 13 mini':'iphone-13-mini','iPhone 13 Pro':'iphone-13-pro','iPhone 14':'iphone-14','iPhone 14 Pro':'iphone-14-pro','iPhone 15':'iphone-15'}[model]
    mem=memory.replace(' ГБ','').strip()
    if color=='черный':
        c={'iPhone 13':'midnight','iPhone 13 mini':'midnight','iPhone 13 Pro':'graphite','iPhone 14':'midnight','iPhone 14 Pro':'space-black'}.get(model,'black')
    elif color=='белый': c='starlight' if model in ('iPhone 13','iPhone 13 mini','iPhone 14') else 'white'
    elif color=='зеленый': c='alpine-green' if model=='iPhone 13 Pro' else 'green'
    elif color in ('синий','голубой'): c='sierra-blue' if model=='iPhone 13 Pro' else 'blue'
    elif color=='фиолетовый': c='deep-purple' if model=='iPhone 14 Pro' else 'purple'
    elif color=='розовый': c='pink'
    elif color=='золотистый': c='gold'
    elif color=='серебристый': c='silver'
    else: raise RuntimeError(f'unknown color: {model} {memory} {color}')
    return f'{model_slug}-{mem}-{c}-01-cover.jpg'

def replacement_for_ad(ad):
    fn=cover_filename(extract(ad,'Model'),extract(ad,'MemorySize'),extract(ad,'Color'))
    if not (IMG_DIR/fn).is_file(): raise RuntimeError(f'cover missing: {fn}')
    names=[fn]+UNIVERSAL
    for n in names:
        if not (IMG_DIR/n).is_file(): raise RuntimeError(f'image missing: {n}')
    urls=[f'{BASE}/{n}' for n in names]
    return ('<Images>'+''.join(f'<Image url="{u}"/>' for u in urls)+'</Images>').encode('utf-8'), fn

def normalized_digest(data):
    return hashlib.sha256(IMG_RE.sub(b'<Images>__IMAGES__</Images>', data)).hexdigest()

def process(src, out):
    data=src.read_bytes(); before_norm=normalized_digest(data)
    result=bytearray(); pos=0; ads=0; covers=[]; ids=[]
    for m in AD_RE.finditer(data):
        result.extend(data[pos:m.start()]); full=m.group(0); inner=m.group(1)
        repl,cover=replacement_for_ad(inner)
        new_full=IMG_RE.sub(repl, full, count=1)
        if new_full==full: raise RuntimeError(f'Images block not replaced in ad {ads+1}')
        result.extend(new_full); pos=m.end(); ads+=1; covers.append(cover); ids.append(extract(inner,'Id'))
    result.extend(data[pos:]); out.parent.mkdir(parents=True,exist_ok=True); out.write_bytes(bytes(result))
    outdata=bytes(result)
    if before_norm!=normalized_digest(outdata): raise RuntimeError(f'non-Images fields changed in {src.name}')
    return ads, ids, covers, hashlib.sha256(data).hexdigest(), hashlib.sha256(outdata).hexdigest()

def main():
    img_files=sorted(p.name for p in IMG_DIR.glob('*.jpg'))
    if len(img_files)!=74 or len(set(img_files))!=74: raise RuntimeError(f'expected 74 images, got {len(img_files)}')
    manifest=[{'number':i+1,'filename':n,'url':f'{BASE}/{n}'} for i,n in enumerate(img_files)]
    Path('ihub').mkdir(exist_ok=True)
    Path('ihub/iHub_PUBLIC_PHOTO_URLS.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    total=0; allids=[]; allcovers=[]; rows=[]
    for s,o in zip(SRC,OUT):
        if not s.is_file(): raise RuntimeError(f'source missing: {s}')
        ads,ids,covers,srcsha,outsha=process(s,o); rows.append((s,o,ads,srcsha,outsha)); total+=ads; allids.extend(ids); allcovers.extend(covers)
    if total!=40020: raise RuntimeError(f'expected 40020 ads, got {total}')
    if len(set(allids))!=40020: raise RuntimeError('IDs are not unique/preserved')
    if len(set(allcovers))!=69: raise RuntimeError(f'expected 69 SKU covers used, got {len(set(allcovers))}')
    allowed={f'{BASE}/{n}' for n in img_files}
    for o in OUT:
        data=o.read_bytes(); cnt=0
        for m in AD_RE.finditer(data):
            imgs=IMG_RE.search(m.group(0))
            if not imgs: raise RuntimeError('output Images missing')
            urls=[x.decode('utf-8') for x in re.findall(rb'<Image url="([^"]+)"\s*/>', imgs.group(0))]
            if len(urls)!=6: raise RuntimeError(f'{o.name}: ad has {len(urls)} images')
            if any(u not in allowed for u in urls): raise RuntimeError(f'{o.name}: unexpected image URL')
            cnt+=1
        if cnt!=20010: raise RuntimeError(f'{o.name}: {cnt} ads')
    lines=['STATUS: PASS','Total ads: 40020','Parts: 20010 + 20010','Unique IDs: 40020','Images per ad: exactly 6','Unique SKU covers used: 69','Unique image URLs: 74','Non-Images fields: byte-identical after Images normalization']
    for s,o,ads,ss,os_ in rows:
        lines += [f'Source {s.name} SHA256: {ss}',f'Output {o.name} SHA256: {os_}']
    Path('ihub/iHub_URL_FEED_FINAL_VALIDATION.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('\n'.join(lines))

if __name__=='__main__': main()
