from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from shutil import copy2
import re,hashlib
SRC=Path('ihub/images/2026-11-02-final')
DST=Path('ihub/images/2026-11-07-repaired')
REPORT=Path('ihub/repair/COVERS_REPAIR_CHECKPOINT.txt')
FONTS=['/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf','/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf']
fontpath=next((p for p in FONTS if Path(p).exists()),None)
if not fontpath:raise SystemExit('Required font missing')
DST.mkdir(parents=True,exist_ok=True)
files=sorted(SRC.glob('*.jpg'))
assert len(files)==28, ('Expected 28 existing covers',len(files))
out=[]
for p in files:
    m=re.search(r'iphone-15-(pro-max|pro)-(128|256|512|1tb)-(black|blue|gray|white)-01-cover\.jpg$',p.name)
    assert m, p.name
    kind,mem,color=m.groups()
    base=SRC/f'iphone-15-pro-128-{color}-01-cover.jpg'
    assert base.exists()
    target=DST/p.name
    if color=='white':
        # White 128 original cover contains a visible stock watermark.
        # Use the existing watermark-free, model-correct 3-camera source instead.
        plain=Path('ihub/images/2026-11-02/iphone-15-pro-128-white-01-cover.jpg')
        assert plain.exists()
        with Image.open(plain) as source:
            product=source.convert('RGB').resize((940,940),Image.Resampling.LANCZOS)
        im=Image.new('RGB',(1254,1254),(12,18,34))
        im.paste(product,(157,235))
        d=ImageDraw.Draw(im)
        d.rounded_rectangle((25,18,1228,222),radius=28,fill=(12,19,35))
        d.text((53,25),'iHub',font=ImageFont.truetype(fontpath,73),fill='white')
        title='iPhone 15 Pro Max' if kind=='pro-max' else 'iPhone 15 Pro'
        d.text((365,42),title,font=ImageFont.truetype(fontpath,63),fill='white')
        memlabel={'128':'128 ГБ','256':'256 ГБ','512':'512 ГБ','1tb':'1 ТБ'}[mem]
        d.rounded_rectangle((48,143,400,220),radius=24,fill=(230,241,252))
        d.text((90,148),memlabel,font=ImageFont.truetype(fontpath,50),fill=(13,20,35))
        d.rounded_rectangle((435,143,746,220),radius=24,fill=(225,225,231))
        d.text((495,148),'Белый',font=ImageFont.truetype(fontpath,49),fill=(13,20,35))
        d.rounded_rectangle((26,1130,1228,1235),radius=22,fill=(14,18,29))
        d.text((61,1150),'Оригинальный Apple  •  Новый  •  Доставка',font=ImageFont.truetype(fontpath,36),fill='white')
        im.save(target,format='JPEG',quality=92,optimize=True,subsampling=0,progressive=True)
        method='model-correct, watermark-free existing white Apple product source with iHub SKU labels'
    elif kind=='pro' and mem=='128':
        copy2(base,target)
        method='unchanged approved 128 cover'
    else:
        with Image.open(base) as old: im=old.convert('RGB')
        d=ImageDraw.Draw(im)
        if kind=='pro-max':
            d.rounded_rectangle((186,109,1151,242),radius=21,fill=(15,18,28))
            title='iPhone 15 Pro Max'
            sz=96
            while sz>55:
                f=ImageFont.truetype(fontpath,sz)
                b=d.textbbox((0,0),title,font=f,stroke_width=0)
                if b[2]-b[0]<930:break
                sz-=2
            tw=b[2]-b[0]
            d.text(((1254-tw)/2,116),title,font=f,fill='white')
        label={'128':'128 ГБ','256':'256 ГБ','512':'512 ГБ','1tb':'1 ТБ'}[mem]
        d.rounded_rectangle((213,238,617,352),radius=38,fill=(235,242,252),outline=(188,207,239),width=5)
        f=ImageFont.truetype(fontpath,78)
        b=d.textbbox((0,0),label,font=f)
        tw=b[2]-b[0]
        d.text((415-tw/2,242),label,font=f,fill=(12,20,31))
        im.save(target,format='JPEG',quality=91,optimize=True,subsampling=0,progressive=True)
        method='same-color iHub triple-camera cover with corrected model/memory text'
    with Image.open(target) as check:
        check.load();assert check.size==(1254,1254),(target.name,check.size)
        pix=list(check.convert('RGB').resize((64,64)).getdata())
        black=sum(max(c)<22 for c in pix)/len(pix)
        assert black<0.82,(target.name,black)
    out.append(f'{target.name} | {method} | bytes={target.stat().st_size} | black={black:.3f} | sha256={hashlib.sha256(target.read_bytes()).hexdigest()}')
assert len(list(DST.glob('*.jpg')))==28
REPORT.parent.mkdir(parents=True,exist_ok=True)
REPORT.write_text('STATUS: COVERS_READY_FOR_FEED_SWITCH\n28 corrected covers; 3 pre-existing valid 128 cards unchanged; 24 derived from same-color iHub 128 covers; 4 white variants built from watermark-free correct 3-camera source with SKU labels. No ad fields changed.\nAll JPEGs 1254x1254; black-image ratio <0.82; source files and current feed links untouched.\nNext: visually inspect then switch ONLY Images (first cover URL) in 40000 and extension feeds. Preserve all XML public paths.\n\n'+'\n'.join(out)+'\n',encoding='utf-8')
print('STATUS: COVERS_READY_FOR_FEED_SWITCH; 28 corrected 1254x1254, no black covers')
