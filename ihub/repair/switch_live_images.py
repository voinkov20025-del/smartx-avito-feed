from pathlib import Path
from collections import Counter
import re,hashlib,json,gzip
BASE='https://raw.githubusercontent.com/voinkov20025-del/smartx-avito-feed/main/ihub/images/'
NEW=BASE+'2026-11-07-repaired/'
IMAGE_DIR=Path('ihub/images/2026-11-07-repaired')
assert len(list(IMAGE_DIR.glob('*.jpg')))==28,'Expected exactly 28 prepared covers'
files=[
 ('ihub/feeds/ihub-final-part-1-00001-20000.xml',20000,'40000-1'),
 ('ihub/feeds/ihub-final-part-2-20001-40000.xml',20000,'40000-2'),
 ('ihub/feeds/iHub_STRUCTURE_13920_URL_FINAL_PART_3_40021-53940.xml',13920,'extension-3'),
]
IMG=re.compile(rb'<Images>.*?</Images>',re.S)
ONE=re.compile(rb'<Image url="([^"]+)"\s*/>')
AD=re.compile(rb'<Ad>.*?</Ad>',re.S)
LOG=[]
for filename,expected,key in files:
    path=Path(filename)
    old=path.read_bytes()
    cover_counter=Counter()
    changed=[0]
    def fix_images(match):
        block=match.group(0)
        found=ONE.findall(block)
        if len(found)!=6:raise RuntimeError(f'{key}: not exactly 6 image links')
        first=found[0].decode('utf-8')
        if '/ihub/images/2026-11-02-final/' in first or '/ihub/images/2026-11-02/' in first:
            name=first.split('/')[-1].split('?')[0]
            dest=IMAGE_DIR/name
            if not dest.is_file():raise RuntimeError(f'{key}: no repaired JPG for {name}')
            new_url=(NEW+name).encode('utf-8')
            block=block.replace(found[0],new_url,1)
            changed[0]+=1
            cover_counter[name]+=1
        return block
    new,blocks=IMG.subn(fix_images,old)
    if blocks!=expected:raise RuntimeError(f'{key}: image blocks {blocks}, expected {expected}')
    if len(AD.findall(new))!=expected:raise RuntimeError(f'{key}: Ad count changed')
    if IMG.sub(b'<Images/>',old)!=IMG.sub(b'<Images/>',new):
        raise RuntimeError(f'{key}: a non-Images byte changed')
    if key.startswith('40000') and changed[0]==0:raise RuntimeError(f'{key}: no broken first URLs were updated')
    if key=='extension-3' and changed[0]!=13920:raise RuntimeError(f'{key}: expected 13920 replacements, got {changed[0]}')
    path.write_bytes(new)
    if key.startswith('40000'):
        gzpath=Path(filename+'.gz')
        with gzpath.open('wb') as f:
            with gzip.GzipFile(filename='',mode='wb',fileobj=f,compresslevel=6,mtime=0) as z:z.write(new)
    LOG.append({'file':filename,'ad_count':expected,'replaced_first_image_url_count':changed[0],'repaired_sku_count':len(cover_counter),'sha256_before':hashlib.sha256(old).hexdigest(),'sha256_after':hashlib.sha256(new).hexdigest(),'gzip_sha256':hashlib.sha256(Path(filename+'.gz').read_bytes()).hexdigest() if key.startswith('40000') else None})
assert sum(x['replaced_first_image_url_count'] for x in LOG[:2])>0
manifest=Path('ihub/extension/ihub_compressed_feeds_manifest.json')
if manifest.exists():
    d=json.loads(manifest.read_text(encoding='utf-8'))
    for k,part in enumerate(d['parts']):
        p=Path(LOG[k]['file']);gp=Path(str(p)+'.gz')
        part.update({'original_bytes':p.stat().st_size,'compressed_bytes':gp.stat().st_size,'sha256_xml':LOG[k]['sha256_after'],'sha256_gzip':LOG[k]['gzip_sha256']})
    manifest.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
report=Path('ihub/repair/FEED_SWITCH_CHECKPOINT.txt')
report.write_text('STATUS: FEEDS_UPDATED_PENDING_EXTERNAL_CHECK\nExisting 5 public XML URL paths unchanged; three relevant XML files updated in-place only inside Images, 40020 originals untouched.\nAll existing Id, Model, Title, Price, Address, Description and other data byte-identical before/after Images normalization.\nChanged first-image URLs now point to new 28 repaired nonblack files; 5 universal images preserved unchanged per ad.\nRailway gateway continues to use /ihub-1.xml and /ihub-2.xml, fed by the two .gz paths.\n'+json.dumps(LOG,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(LOG,ensure_ascii=False,indent=2))
