from pathlib import Path
from PIL import Image
import re, hashlib, json, csv, io, os, sys

PARTS=[
 Path('ihub/feeds/iHub_STRUCTURE_40020_URL_FINAL_PART_1_00001-20010.xml'),
 Path('ihub/feeds/iHub_STRUCTURE_40020_URL_FINAL_PART_2_20011-40020.xml'),
]
OUT1=Path('ihub/feeds/ihub-final-part-1-00001-20000.xml')
OUT2=Path('ihub/feeds/ihub-final-part-2-20001-40000.xml')
IMG_OUT=Path('ihub/images/2026-11-02-final')
OLD_IMG_BASE='https://raw.githubusercontent.com/voinkov20025-del/smartx-avito-feed/main/ihub/images/2026-10-05'
NEW_IMG_BASE='https://raw.githubusercontent.com/voinkov20025-del/smartx-avito-feed/main/ihub/images/2026-11-02-final'
UNIVERSAL=['universal-02-avito-delivery.jpg','universal-03-check-phone.jpg','universal-04-yandex-split.jpg','universal-05-store-moscow.jpg','universal-06-benefits.jpg']
AD_RE=re.compile(r'<Ad>(.*?)</Ad>', re.S)

NEW_SKUS=[
 ('iPhone 15 Pro','128 ГБ','черный',57990,'iphone-15-pro-128-black-01-cover.jpg'),
 ('iPhone 15 Pro','128 ГБ','синий',57990,'iphone-15-pro-128-blue-01-cover.jpg'),
 ('iPhone 15 Pro','128 ГБ','серый',57990,'iphone-15-pro-128-gray-01-cover.jpg'),
 ('iPhone 15 Pro','128 ГБ','белый',57990,'iphone-15-pro-128-white-01-cover.jpg'),
 ('iPhone 15 Pro','256 ГБ','черный',59990,'iphone-15-pro-256-black-01-cover.jpg'),
 ('iPhone 15 Pro','256 ГБ','синий',59990,'iphone-15-pro-256-blue-01-cover.jpg'),
 ('iPhone 15 Pro','256 ГБ','серый',59990,'iphone-15-pro-256-gray-01-cover.jpg'),
 ('iPhone 15 Pro','256 ГБ','белый',59990,'iphone-15-pro-256-white-01-cover.jpg'),
 ('iPhone 15 Pro','512 ГБ','черный',63990,'iphone-15-pro-512-black-01-cover.jpg'),
 ('iPhone 15 Pro','512 ГБ','синий',63990,'iphone-15-pro-512-blue-01-cover.jpg'),
 ('iPhone 15 Pro','512 ГБ','серый',63990,'iphone-15-pro-512-gray-01-cover.jpg'),
 ('iPhone 15 Pro','512 ГБ','белый',63990,'iphone-15-pro-512-white-01-cover.jpg'),
 ('iPhone 15 Pro','1 ТБ','черный',67990,'iphone-15-pro-1tb-black-01-cover.jpg'),
 ('iPhone 15 Pro','1 ТБ','синий',67990,'iphone-15-pro-1tb-blue-01-cover.jpg'),
 ('iPhone 15 Pro','1 ТБ','серый',67990,'iphone-15-pro-1tb-gray-01-cover.jpg'),
 ('iPhone 15 Pro','1 ТБ','белый',67990,'iphone-15-pro-1tb-white-01-cover.jpg'),
 ('iPhone 15 Pro Max','256 ГБ','черный',67990,'iphone-15-pro-max-256-black-01-cover.jpg'),
 ('iPhone 15 Pro Max','256 ГБ','синий',67990,'iphone-15-pro-max-256-blue-01-cover.jpg'),
 ('iPhone 15 Pro Max','256 ГБ','серый',67990,'iphone-15-pro-max-256-gray-01-cover.jpg'),
 ('iPhone 15 Pro Max','256 ГБ','белый',67990,'iphone-15-pro-max-256-white-01-cover.jpg'),
 ('iPhone 15 Pro Max','512 ГБ','черный',73490,'iphone-15-pro-max-512-black-01-cover.jpg'),
 ('iPhone 15 Pro Max','512 ГБ','синий',73490,'iphone-15-pro-max-512-blue-01-cover.jpg'),
 ('iPhone 15 Pro Max','512 ГБ','серый',73490,'iphone-15-pro-max-512-gray-01-cover.jpg'),
 ('iPhone 15 Pro Max','512 ГБ','белый',73490,'iphone-15-pro-max-512-white-01-cover.jpg'),
 ('iPhone 15 Pro Max','1 ТБ','черный',76990,'iphone-15-pro-max-1tb-black-01-cover.jpg'),
 ('iPhone 15 Pro Max','1 ТБ','синий',76990,'iphone-15-pro-max-1tb-blue-01-cover.jpg'),
 ('iPhone 15 Pro Max','1 ТБ','серый',76990,'iphone-15-pro-max-1tb-gray-01-cover.jpg'),
 ('iPhone 15 Pro Max','1 ТБ','белый',76990,'iphone-15-pro-max-1tb-white-01-cover.jpg'),
]
ATLAS_NAMES=sorted([x[4] for x in NEW_SKUS])

def tag(text,name):
 m=re.search(fr'<{name}>(.*?)</{name}>',text,re.S)
 if not m: raise RuntimeError(f'missing {name}')
 return m.group(1)

def replace_tag(text,name,value):
 out,n=re.subn(fr'<{name}>.*?</{name}>',f'<{name}>{value}</{name}>',text,count=1,flags=re.S)
 if n!=1: raise RuntimeError(f'failed replace {name}')
 return out

def extract_atlases(frame_paths):
 if len(frame_paths)!=7: raise RuntimeError('expected 7 atlas frames')
 IMG_OUT.mkdir(parents=True,exist_ok=True)
 for old in IMG_OUT.glob('*.jpg'): old.unlink()
 names=ATLAS_NAMES
 for gi,p in enumerate(frame_paths):
  im=Image.open(p).convert('RGB')
  w,h=im.size
  side=min(w,h); x0=(w-side)//2; y0=(h-side)//2
  sq=im.crop((x0,y0,x0+side,y0+side))
  group=names[gi*4:(gi+1)*4]
  for j,name in enumerate(group):
   c=j%2; r=j//2
   left=round(c*side/2); right=round((c+1)*side/2)
   top=round(r*side/2); bottom=round((r+1)*side/2)
   tile=sq.crop((left,top,right,bottom)).resize((1254,1254),Image.Resampling.LANCZOS)
   tile.save(IMG_OUT/name,'JPEG',quality=92,subsampling=0,optimize=True,progressive=True)
 if len(list(IMG_OUT.glob('*.jpg'))) != 28: raise RuntimeError('failed to create exactly 28 covers')

def load_source():
 by_addr={}; all_ids=set(); total=0
 for p in PARTS:
  text=p.read_text(encoding='utf-8')
  for m in AD_RE.finditer(text):
   inner=m.group(1); total+=1
   addr=tag(inner,'Address'); aid=tag(inner,'Id')
   if aid in all_ids: raise RuntimeError('duplicate source id')
   all_ids.add(aid)
   by_addr.setdefault(addr,[]).append('<Ad>'+inner+'</Ad>')
 if total!=40020 or len(by_addr)!=580: raise RuntimeError((total,len(by_addr)))
 return by_addr,all_ids

def selected_addresses():
 import base64,zlib
 b64=Path('ihub/publisher/iHub_40000_CITY_SELECTION.zlib.b64').read_text(encoding='ascii').strip()
 data=zlib.decompress(base64.b64decode(b64)).decode('utf-8')
 rows=list(csv.DictReader(io.StringIO(data)))
 if len(rows)!=413: raise RuntimeError(f'expected 413 selected, got {len(rows)}')
 for r in rows:
  if r['status']=='PARTIAL_36': r['status']='PARTIAL'
 rows.sort(key=lambda r:int(r['rank']))
 if sum(int(r['ads']) for r in rows)!=40000: raise RuntimeError('selection does not total 40000')
 return rows

def new_ad(template_ad,address,model,memory,color,price,cover):
 inner=re.search(r'<Ad>(.*?)</Ad>',template_ad,re.S).group(1)
 key=f'{address}|{model}|{memory}|{color}'
 aid='ihub_20261102_'+hashlib.sha1(key.encode()).hexdigest()[:20]
 for n,v in [('Id',aid),('Address',address),('Model',model),('MemorySize',memory),('Color',color),('RamSize','8 ГБ'),('Title',f'{model}, {memory}, SIM + eSIM'),('Price',str(price))]:
  inner=replace_tag(inner,n,v)
 urls=[f'{NEW_IMG_BASE}/{cover}']+[f'{OLD_IMG_BASE}/{u}' for u in UNIVERSAL]
 images='<Images>'+''.join(f'<Image url="{u}"/>' for u in urls)+'</Images>'
 inner,n=re.subn(r'<Images>.*?</Images>',images,inner,count=1,flags=re.S)
 if n!=1: raise RuntimeError('images replace failed')
 return '<Ad>'+inner+'</Ad>',aid

def main():
 if len(sys.argv)!=8: raise SystemExit('usage: build_ihub_40000_final.py FRAME1 ... FRAME7')
 extract_atlases(sys.argv[1:])
 by_addr,source_ids=load_source(); selected=selected_addresses()
 final=[]; ids=[]
 for row in selected:
  addr=row['address']; status=row['status']
  old=by_addr.get(addr)
  if not old: raise RuntimeError(f'address absent in source: {addr}')
  if len(old)!=69: raise RuntimeError(f'{addr}: expected 69 old ads, got {len(old)}')
  if status=='FULL':
   keep=old
  else:
   keep=[]
   for ad in old:
    inner=re.search(r'<Ad>(.*?)</Ad>',ad,re.S).group(1)
    if tag(inner,'Model')=='iPhone 15': keep.append(ad)
   if len(keep)!=8: raise RuntimeError(f'partial old count {len(keep)}')
  final.extend(keep); ids.extend(tag(re.search(r'<Ad>(.*?)</Ad>',x,re.S).group(1),'Id') for x in keep)
  template=old[0]
  for model,memory,color,price,cover in NEW_SKUS:
   ad,aid=new_ad(template,addr,model,memory,color,price,cover)
   final.append(ad); ids.append(aid)
 if len(final)!=40000 or len(set(ids))!=40000: raise RuntimeError((len(final),len(set(ids))))
 combos=set(); city_counts={}
 for ad in final:
  inner=re.search(r'<Ad>(.*?)</Ad>',ad,re.S).group(1)
  combos.add((tag(inner,'Model'),tag(inner,'MemorySize'),tag(inner,'Color')))
  city_counts[tag(inner,'Address')]=city_counts.get(tag(inner,'Address'),0)+1
  urls=re.findall(r'<Image url="([^"]+)"\s*/>',tag(inner,'Images'))
  if len(urls)!=6: raise RuntimeError('ad without 6 URLs')
 if len(combos)!=97: raise RuntimeError(f'expected 97 sku, got {len(combos)}')
 if sorted(city_counts.values()).count(97)!=412 or sorted(city_counts.values()).count(36)!=1: raise RuntimeError('city counts invalid')
 header='<?xml version="1.0" encoding="utf-8"?>\n<Ads formatVersion="3" target="Avito.ru">\n'
 footer='\n</Ads>\n'
 OUT1.parent.mkdir(parents=True,exist_ok=True)
 OUT1.write_text(header+'\n\n'.join(final[:20000])+footer,encoding='utf-8')
 OUT2.write_text(header+'\n\n'.join(final[20000:])+footer,encoding='utf-8')
 report='\n'.join(['STATUS: PASS','Total ads: 40000','Part 1: 20000','Part 2: 20000','Unique IDs: 40000','SKU: 97','Selected cities: 413','Full cities: 412','Partial city: 1 (36 ads)','Images per ad: exactly 6','New approved covers: 28'])+'\n'
 Path('ihub/extension/iHub_40000_PUBLIC_VALIDATION.txt').write_text(report,encoding='utf-8')
 urls='\n'.join(['iHub AVITO FEED URLS — 40,000 ads','PART 1 — 20,000 ads:','https://raw.githubusercontent.com/voinkov20025-del/smartx-avito-feed/main/ihub/feeds/ihub-final-part-1-00001-20000.xml','','PART 2 — 20,000 ads:','https://raw.githubusercontent.com/voinkov20025-del/smartx-avito-feed/main/ihub/feeds/ihub-final-part-2-20001-40000.xml'])+'\n'
 Path('ihub/AVITO_FEED_URLS_40000.txt').write_text(urls,encoding='utf-8')
 print(report); print(urls)

if __name__=='__main__': main()
