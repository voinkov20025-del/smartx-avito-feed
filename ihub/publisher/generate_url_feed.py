#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from xml.sax.saxutils import escape, quoteattr
from collections import Counter
import argparse, json, base64, zlib, math, os, re, hashlib
import xml.etree.ElementTree as ET

W=H=1254
OWNER="voinkov20025-del"
REPO="smartx-avito-feed"
BRANCH="main"
IMG_REL="ihub/images/2026-10-05"
BASE_URL=f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{BRANCH}/{IMG_REL}"

def font(size,bold=False):
    paths=[
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for p in paths:
        if Path(p).exists():
            return ImageFont.truetype(p,size=size)
    return ImageFont.load_default()

def lerp(a,b,t): return int(a*(1-t)+b*t)

def background(tint=(215,228,245)):
    img=Image.new("RGB",(W,H))
    px=img.load()
    top=(252,253,255)
    bot=tuple(min(255,int(x*0.35+225)) for x in tint)
    for y in range(H):
        t=y/(H-1)
        c=tuple(lerp(top[i],bot[i],t) for i in range(3))
        for x in range(W): px[x,y]=c
    return img

def centered(draw,text,y,fnt,fill):
    box=draw.textbbox((0,0),text,font=fnt)
    draw.text(((W-(box[2]-box[0]))//2,y),text,font=fnt,fill=fill)

def color_rgb(model,color):
    c=color.lower()
    table={
        "белый":(231,228,220),
        "зеленый":(143,184,159),
        "синий":(84,135,177),
        "голубой":(148,190,220),
        "фиолетовый":(167,147,191),
        "черный":(55,58,62),
        "розовый":(232,174,184),
        "золотистый":(211,183,136),
        "серебристый":(212,215,215),
    }
    if c=="черный" and "13 Pro" in model: return (78,78,76)
    if c=="черный" and "14 Pro" in model: return (52,50,49)
    return table.get(c,(140,150,160))

def roundrect(draw,xy,r,fill,outline=None,width=1):
    draw.rounded_rectangle(xy,radius=r,fill=fill,outline=outline,width=width)

def camera_lens(draw,cx,cy,r,outline=(25,25,28)):
    draw.ellipse((cx-r,cy-r,cx+r,cy+r),fill=(20,22,25),outline=outline,width=4)
    draw.ellipse((cx-r*0.62,cy-r*0.62,cx+r*0.62,cy+r*0.62),fill=(50,58,67))
    draw.ellipse((cx-r*0.24,cy-r*0.24,cx+r*0.24,cy+r*0.24),fill=(8,10,14))
    draw.ellipse((cx-r*0.05,cy-r*0.22,cx+r*0.17,cy),fill=(112,157,199))

def draw_back_phone(draw, model, body_color, x, y, scale=1.0):
    w=int(350*scale); h=int(690*scale); r=int(55*scale)
    roundrect(draw,(x,y,x+w,y+h),r,body_color,outline=(120,125,132),width=max(2,int(4*scale)))
    draw.line((x+22*scale,y+75*scale,x+22*scale,y+h-75*scale),fill=tuple(min(255,v+40) for v in body_color),width=max(2,int(5*scale)))
    bx=x+int(34*scale); by=y+int(40*scale); bump=int(170*scale)
    roundrect(draw,(bx,by,bx+bump,by+bump),int(35*scale),tuple(max(0,v-8) for v in body_color),outline=tuple(min(255,v+25) for v in body_color),width=max(2,int(3*scale)))
    lr=int(42*scale)
    if "Pro" in model:
        pts=[(bx+int(52*scale),by+int(52*scale)),(bx+int(120*scale),by+int(55*scale)),(bx+int(55*scale),by+int(122*scale))]
        for cx,cy in pts: camera_lens(draw,cx,cy,lr)
        draw.ellipse((bx+int(112*scale),by+int(112*scale),bx+int(137*scale),by+int(137*scale)),fill=(30,32,34))
        draw.ellipse((bx+int(125*scale),by+int(91*scale),bx+int(143*scale),by+int(109*scale)),fill=(242,236,200))
    else:
        if "12" in model:
            pts=[(bx+int(61*scale),by+int(52*scale)),(bx+int(61*scale),by+int(120*scale))]
        else:
            pts=[(bx+int(55*scale),by+int(55*scale)),(bx+int(120*scale),by+int(120*scale))]
        for cx,cy in pts: camera_lens(draw,cx,cy,lr)
        draw.ellipse((bx+int(118*scale),by+int(52*scale),bx+int(140*scale),by+int(74*scale)),fill=(244,237,198))
    draw.ellipse((x+w//2-int(22*scale),y+h//2-int(22*scale),x+w//2+int(22*scale),y+h//2+int(22*scale)),outline=tuple(max(0,v-35) for v in body_color),width=max(2,int(4*scale)))

def draw_front_phone(draw, model, x, y, scale=1.0, accent=(80,140,230)):
    w=int(350*scale); h=int(690*scale); r=int(55*scale)
    roundrect(draw,(x,y,x+w,y+h),r,(28,30,33),outline=(112,118,126),width=max(2,int(4*scale)))
    margin=int(14*scale)
    roundrect(draw,(x+margin,y+margin,x+w-margin,y+h-margin),int(44*scale),(25,34,50))
    cx=x+w//2; cy=y+h//2
    draw.ellipse((cx-int(155*scale),cy-int(155*scale),cx+int(155*scale),cy+int(155*scale)),fill=tuple(max(0,v-40) for v in accent))
    draw.ellipse((cx-int(112*scale),cy-int(112*scale),cx+int(112*scale),cy+int(112*scale)),fill=accent)
    draw.ellipse((cx-int(65*scale),cy-int(65*scale),cx+int(65*scale),cy+int(65*scale)),fill=tuple(min(255,v+45) for v in accent))
    if ("14 Pro" in model) or (model=="iPhone 15"):
        iw=int(112*scale); ih=int(32*scale)
        roundrect(draw,(cx-iw//2,y+int(30*scale),cx+iw//2,y+int(30*scale)+ih),ih//2,(5,6,8))
    else:
        nw=int(148*scale); nh=int(40*scale)
        draw.rectangle((cx-nw//2,y+margin,cx+nw//2,y+margin+nh),fill=(5,6,8))
        draw.ellipse((cx-nw//2,y+margin+nh//2-int(18*scale),cx-nw//2+int(36*scale),y+margin+nh//2+int(18*scale)),fill=(5,6,8))
        draw.ellipse((cx+nw//2-int(36*scale),y+margin+nh//2-int(18*scale),cx+nw//2,y+margin+nh//2+int(18*scale)),fill=(5,6,8))

def render_sku(sku,out):
    model=next(x['text'] for x in sku['fields'] if x['tag']=='Model')
    mem=next(x['text'] for x in sku['fields'] if x['tag']=='MemorySize')
    col=next(x['text'] for x in sku['fields'] if x['tag']=='Color')
    body=color_rgb(model,col)
    img=background(body)
    d=ImageDraw.Draw(img)
    centered(d,model,78,font(63,True),(15,31,55))
    badge_text=mem.replace(" ГБ"," GB")
    bb=d.textbbox((0,0),badge_text,font=font(38,True)); bw=bb[2]-bb[0]
    roundrect(d,((W-bw)//2-34,170,(W+bw)//2+34,230),30,(46,128,238))
    centered(d,badge_text,178,font(38,True),"white")
    centered(d,col.capitalize(),252,font(34,True),(80,85,96))
    mini="mini" in model.lower()
    scale=0.84 if mini else 0.96
    base_y=355 if mini else 330
    draw_back_phone(d,model,body,245,base_y,scale)
    accent=(82,150,232)
    if col=="розовый": accent=(225,126,157)
    elif col=="зеленый": accent=(96,178,124)
    elif col=="фиолетовый": accent=(139,102,208)
    elif col=="черный": accent=(80,98,130)
    elif col=="белый" or col=="серебристый": accent=(163,185,220)
    elif col=="золотистый": accent=(218,161,70)
    elif col=="голубой" or col=="синий": accent=(55,145,225)
    draw_front_phone(d,model,665,base_y,scale,accent)
    img.save(out,"JPEG",quality=88,optimize=True,progressive=True,subsampling=0)

def check_icon(d,cx,cy,r=21,fill=(42,132,239)):
    d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=fill)
    d.line((cx-r*.45,cy,cx-r*.10,cy+r*.35),fill="white",width=5)
    d.line((cx-r*.10,cy+r*.35,cx+r*.55,cy-r*.35),fill="white",width=5)

def card_base(title,subtitle=""):
    img=background((184,213,248)); d=ImageDraw.Draw(img)
    roundrect(d,(50,42,225,105),30,(16,37,70)); d.text((83,56),"iHub",font=font(34,True),fill="white")
    centered(d,title,135,font(57,True),(15,38,73))
    if subtitle: centered(d,subtitle,225,font(26,False),(74,91,116))
    return img,d

def render_universal(name,out):
    if name=="universal-02-avito-delivery":
        img,d=card_base("Доставка по всей России","Надёжно, быстро и с проверкой при получении")
        roundrect(d,(170,440,815,800),44,(255,255,255),outline=(170,200,234),width=5)
        d.rectangle((245,530,585,720),fill=(235,197,124)); d.line((415,530,415,720),fill=(203,163,93),width=7)
        d.rectangle((610,585,750,720),fill=(59,130,214)); d.polygon([(750,585),(810,632),(810,720),(750,720)],fill=(45,105,190))
        for cx in (355,700):
            d.ellipse((cx-55,730,cx+55,840),fill=(37,47,60)); d.ellipse((cx-25,760,cx+25,810),fill=(190,204,220))
        d.line((890,500,1025,620,930,760),fill=(65,146,240),width=10)
        for cx,cy in [(890,500),(1025,620),(930,760)]: d.ellipse((cx-14,cy-14,cx+14,cy+14),fill=(42,132,239))
        bullets=["Надёжная упаковка","Отправка по России","Проверка при получении"]
    elif name=="universal-03-check-phone":
        img,d=card_base("Проверка при получении","Сверьте заказ до окончательного получения")
        roundrect(d,(155,450,650,795),40,(255,255,255),outline=(170,200,234),width=5)
        d.rectangle((225,535,580,730),fill=(235,197,124)); d.line((402,535,402,730),fill=(203,163,93),width=7)
        roundrect(d,(715,450,1080,815),36,(255,255,255),outline=(170,200,234),width=5)
        for i,t in enumerate(["Упаковка","Комплект","Соответствие"]):
            cy=545+i*105; check_icon(d,775,cy,22,(35,163,99)); d.text((820,cy-25),t,font=font(29,True),fill=(42,59,85))
        bullets=["Осмотрите товар","Сверьте комплект","При несоответствии — откажитесь"]
    elif name=="universal-04-yandex-split":
        img,d=card_base("Покупка частями","Распределите оплату на несколько платежей")
        cols=[(63,137,245),(72,193,150),(255,184,69),(172,104,230)]
        for i,a in enumerate([0,90,180,270]): d.pieslice((230,460,620,850),start=a,end=a+86,fill=cols[i])
        d.ellipse((345,575,505,735),fill=(242,247,254))
        for x,y,c in [(690,485,(31,85,154)),(755,600,(44,127,235)),(685,715,(38,159,109))]:
            roundrect(d,(x,y,x+310,y+125),24,c); d.text((x+30,y+58),"••••  ••••",font=font(23,True),fill="white")
        bullets=["Несколько платежей","Оформление онлайн","Условия видны до оплаты"]
    elif name=="universal-05-store-moscow":
        img,d=card_base("Наш магазин в Москве","Самовывоз и консультация в магазине iHub")
        roundrect(d,(205,440,1045,820),42,(255,255,255),outline=(174,202,234),width=5)
        d.rectangle((285,535,970,790),fill=(234,240,249)); d.rectangle((490,610,765,790),fill=(35,52,76))
        for i,x in enumerate(range(285,971,98)): d.rectangle((x,515,min(x+98,970),580),fill=((40,113,205) if i%2==0 else (255,255,255)))
        d.text((555,665),"iHub",font=font(48,True),fill="white")
        bullets=["Самовывоз","Проверка заказа","Профессиональная консультация"]
    else:
        img,d=card_base("Почему выбирают iHub","Понятные условия и поддержка после покупки")
        cx,cy=350,620
        pts=[(cx,480),(cx+105,525),(cx+90,665),(cx,770),(cx-90,665),(cx-105,525)]
        d.polygon(pts,fill=(42,130,236)); d.line((cx-45,620,cx-8,660),fill="white",width=15); d.line((cx-8,660,cx+62,570),fill="white",width=15)
        d.rectangle((570,520,880,740),fill=(235,197,124)); d.polygon([(570,520),(725,445),(880,520),(725,600)],fill=(248,215,151))
        bullets=["Оригинальная техника","Честные условия","Надёжная упаковка","Поддержка после покупки"]
    y=900
    for b in bullets:
        check_icon(d,120,y+20,20,(39,151,103)); d.text((165,y),b,font=font(29,True),fill=(35,55,84)); y+=69
    img.save(out,"JPEG",quality=88,optimize=True,progressive=True,subsampling=0)

def load_config(path):
    txt=Path(path).read_text(encoding='ascii').strip()
    raw=zlib.decompress(base64.b64decode(txt))
    return json.loads(raw.decode('utf-8'))

def write_tag(f,tag,text):
    f.write(f"<{tag}>{escape(text or '')}</{tag}>")

def generate(config_path,out_root):
    cfg=load_config(config_path)
    out_root=Path(out_root)
    img_dir=out_root/IMG_REL
    feed_dir=out_root/"ihub/feeds"
    img_dir.mkdir(parents=True,exist_ok=True); feed_dir.mkdir(parents=True,exist_ok=True)
    ids=zlib.decompress(base64.b64decode(cfg['ids_zlib_b64'])).decode('utf-8').splitlines()
    addresses=cfg['addresses']; skus=cfg['skus']
    if len(ids)!=40020 or len(addresses)!=580 or len(skus)!=69: raise SystemExit("config cardinality failed")
    files=[]
    for sku in skus:
        jpg=Path(sku['cover_png']).stem+".jpg"
        render_sku(sku,img_dir/jpg); files.append(jpg)
    for png in cfg['universal_png']:
        stem=Path(png).stem
        jpg=stem+".jpg"
        render_universal(stem,img_dir/jpg); files.append(jpg)
    if len(files)!=74 or len(set(files))!=74: raise SystemExit("image set failed")
    manifest=[{"number":i+1,"filename":fn,"url":f"{BASE_URL}/{fn}"} for i,fn in enumerate(files)]
    (out_root/"ihub/iHub_PUBLIC_PHOTO_URLS.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    universal_jpg=[Path(x).stem+".jpg" for x in cfg['universal_png']]
    idx=0
    feed_paths=[]
    for part,(c0,c1) in enumerate([(0,290),(290,580)],1):
        out=feed_dir/f"iHub_STRUCTURE_40020_URL_FINAL_PART_{part}_{1 if part==1 else 20011:05d}-{20010 if part==1 else 40020}.xml"
        with out.open('w',encoding='utf-8',newline='') as f:
            f.write('<?xml version="1.0" encoding="utf-8"?>')
            f.write('<Ads formatVersion="3" target="Avito.ru">')
            for city_i in range(c0,c1):
                addr=addresses[city_i]
                for sku in skus:
                    aid=ids[idx]; idx+=1
                    f.write('<Ad>')
                    write_tag(f,'Id',aid)
                    inserted_addr=False
                    for field in sku['fields']:
                        tag=field['tag']
                        if tag=='Set':
                            f.write('<Set>')
                            for opt in field['options']: write_tag(f,'Option',opt)
                            f.write('</Set>')
                        else:
                            write_tag(f,tag,field['text'])
                        if tag=='ContactMethod':
                            write_tag(f,'Address',addr); inserted_addr=True
                    if not inserted_addr: raise SystemExit("Address insertion point missing")
                    cover=Path(sku['cover_png']).stem+".jpg"
                    urls=[f"{BASE_URL}/{cover}"]+[f"{BASE_URL}/{x}" for x in universal_jpg]
                    f.write('<Images>')
                    for u in urls: f.write(f'<Image url={quoteattr(u)}/>')
                    f.write('</Images></Ad>')
            f.write('</Ads>')
        feed_paths.append(out)
    total=0; all_ids=set(); all_urls=Counter(); first=Counter()
    for out in feed_paths:
        for _,ad in ET.iterparse(out,events=('end',)):
            if ad.tag!='Ad': continue
            total+=1
            aid=(ad.findtext('Id') or '').strip()
            if aid in all_ids: raise SystemExit(f"duplicate id {aid}")
            all_ids.add(aid)
            ims=[x.attrib.get('url','') for x in ad.find('Images').findall('Image')]
            if len(ims)!=6: raise SystemExit(f"bad image count {aid}")
            first[ims[0]]+=1
            for u in ims: all_urls[u]+=1
            ad.clear()
    if total!=40020 or len(all_ids)!=40020: raise SystemExit("ad/id count failed")
    if len(all_urls)!=74 or len(first)!=69 or set(first.values())!={580}: raise SystemExit("image usage failed")
    for fn in universal_jpg:
        if all_urls[f"{BASE_URL}/{fn}"]!=40020: raise SystemExit("universal usage failed")
    report=f"""iHub URL FEED FINAL VALIDATION
================================
STATUS: PASS

Images published: 74
Feed PART 1 ads: 20010
Feed PART 2 ads: 20010
Total ads: {total}
Unique IDs: {len(all_ids)}
Ads with exactly 6 image URLs: {total}
Total image references: {sum(all_urls.values())}
Unique image URLs: {len(all_urls)}
Unique SKU cover URLs: {len(first)}
Each SKU cover used as first image exactly 580 times: PASS
Each universal image used exactly 40020 times: PASS
Direct HTTPS image URLs: PASS

PART 1 URL:
https://raw.githubusercontent.com/{OWNER}/{REPO}/{BRANCH}/ihub/feeds/{feed_paths[0].name}

PART 2 URL:
https://raw.githubusercontent.com/{OWNER}/{REPO}/{BRANCH}/ihub/feeds/{feed_paths[1].name}
"""
    (out_root/"ihub/iHub_URL_FEED_FINAL_VALIDATION.txt").write_text(report,encoding='utf-8')
    return feed_paths

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--config",required=True)
    ap.add_argument("--out",default=".")
    args=ap.parse_args()
    generate(args.config,args.out)
