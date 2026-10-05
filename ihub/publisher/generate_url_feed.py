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
        if Path(p).exists(): return ImageFont.truetype(p,size=size)
    return ImageFont.load_default()

def lerp(a,b,t): return int(a*(1-t)+b*t)
def background(tint=(215,228,245)):
    img=Image.new("RGB",(W,H)); px=img.load(); top=(252,253,255); bot=tuple(min(255,int(x*0.35+225)) for x in tint)
    for y in range(H):
        t=y/(H-1); c=tuple(lerp(top[i],bot[i],t) for i in range(3))
        for x in range(W): px[x,y]=c
    return img

def centered(draw,text,y,fnt,fill):
    box=draw.textbbox((0,0),text,font=fnt); draw.text(((W-(box[2]-box[0]))//2,y),text,font=fnt,fill=fill)

def color_rgb(model,color):
    c=color.lower(); table={"белый":(231,228,220),"зеленый":(143,184,159),"синий":(84,135,177),"голубой":(148,190,220),"фиолетовый":(167,147,191),"черный":(55,58,62),"розовый":(232,174,184),"золотистый":(211,183,136),"серебристый":(212,215,215)}
    if c=="черный" and "13 Pro" in model: return (78,78,76)
    if c=="черный" and "14 Pro" in model: return (52,50,49)
    return table.get(c,(140,150,160))

def roundrect(draw,xy,r,fill,outline=None,width=1): draw.rounded_rectangle(xy,radius=r,fill=fill,outline=outline,width=width)
def camera_lens(draw,cx,cy,r,outline=(25,25,28)):
    draw.ellipse((cx-r,cy-r,cx+r,cy+r),fill=(20,22,25),outline=outline,width=4); draw.ellipse((cx-r*0.62,cy-r*0.62,cx+r*0.62,cy+r*0.62),fill=(50,58,67)); draw.ellipse((cx-r*0.24,cy-r*0.24,cx+r*0.24,cy+r*0.24),fill=(8,10,14)); draw.ellipse((cx-r*0.05,cy-r*0.22,cx+r*0.17,cy),fill=(112,157,199))

def draw_back_phone(draw, model, body_color, x, y, scale=1.0):
    w=int(350*scale); h=int(690*scale); r=int(55*scale); roundrect(draw,(x,y,x+w,y+h),r,body_color,outline=(120,125,132),width=max(2,int(4*scale))); draw.line((x+22*scale,y+75*scale,x+22*scale,y+h-75*scale),fill=tuple(min(255,v+40) for v in body_color),width=max(2,int(5*scale)))
    bx=x+int(34*scale); by=y+int(40*scale); bump=int(170*scale); roundrect(draw,(bx,by,bx+bump,by+bump),int(35*scale),tuple(max(0,v-8) for v in body_color),outline=tuple(min(255,v+25) for v in body_color),width=max(2,int(3*scale))); lr=int(42*scale)
    if "Pro" in model:
        pts=[(bx+int(52*scale),by+int(52*scale)),(bx+int(120*scale),by+int(55*scale)),(bx+int(55*scale),by+int(122*scale))]
        for cx,cy in pts: camera_lens(draw,cx,cy,lr)
        draw.ellipse((bx+int(112*scale),by+int(112*scale),bx+int(137*scale),by+int(137*scale)),fill=(30,32,34)); draw.ellipse((bx+int(125*scale),by+int(91*scale),bx+int(143*scale),by+int(109*scale)),fill=(242,236,200))
    else:
        pts=[(bx+int(61*scale),by+int(52*scale)),(bx+int(61*scale),by+int(120*scale))] if "12" in model else [(bx+int(55*scale),by+int(55*scale)),(bx+int(120*scale),by+int(120*scale))]
        for cx,cy in pts: camera_lens(draw,cx,cy,lr)
        draw.ellipse((bx+int(118*scale),by+int(52*scale),bx+int(140*scale),by+int(74*scale)),fill=(244,237,198))
    draw.ellipse((x+w//2-int(22*scale),y+h//2-int(22*scale),x+w//2+int(22*scale),y+h//2+int(22*scale)),outline=tuple(max(0,v-35) for v in body_color),width=max(2,int(4*scale)))

def draw_front_phone(draw, model, x, y, scale=1.0, accent=(80,140,230)):
    w=int(350*scale); h=int(690*scale); r=int(55*scale); roundrect(draw,(x,y,x+w,y+h),r,(28,30,33),outline=(112,118,126),width=max(2,int(4*scale))); margin=int(14*scale); roundrect(draw,(x+margin,y+margin,x+w-margin,y+h-margin),int(44*scale),(25,34,50)); cx=x+w//2; cy=y+h//2
    draw.ellipse((cx-int(155*scale),cy-int(155*scale),cx+int(155*scale),cy+int(155*scale)),fill=tuple(max(0,v-40) for v in accent)); draw.ellipse((cx-int(112*scale),cy-int(112*scale),cx+int(112*scale),cy+int(112*scale)),fill=accent); draw.ellipse((cx-int(65*scale),cy-int(65*scale),cx+int(65*scale),cy+int(65*scale)),fill=tuple(min(255,v+45) for v in accent))
    if ("14 Pro" in model) or (model=="iPhone 15"):
        iw=int(112*scale); ih=int(32*scale); roundrect(draw,(cx-iw//2,y+int(30*scale),cx+iw//2,y+int(30*scale)+ih),ih//2,(5,6,8))
    else:
        nw=int(148*scale); nh=int(40*scale); draw.rectangle((cx-nw//2,y+margin,cx+nw//2,y+margin+nh),fill=(5,6,8)); draw.ellipse((cx-nw//2,y+margin+nh//2-int(18*scale),cx-nw//2+int(36*scale),y+margin+nh//2+int(18*scale)),fill=(5,6,8)); draw.ellipse((cx+nw//2-int(36*scale),y+margin+nh//2-int(18*scale),cx+nw//2,y+margin+nh//2+int(18*scale)),fill=(5,6,8))

def render_sku(sku,out):
    raise RuntimeError("Photo regeneration is disabled for this iHub publication")
def check_icon(d,cx,cy,r=21,fill=(42,132,239)): pass
def card_base(title,subtitle=""): raise RuntimeError("Photo regeneration is disabled for this iHub publication")
def render_universal(name,out): raise RuntimeError("Photo regeneration is disabled for this iHub publication")

def load_config(path):
    txt=Path(path).read_text(encoding='ascii').strip(); raw=zlib.decompress(base64.b64decode(txt)); return json.loads(raw.decode('utf-8'))
def write_tag(f,tag,text): f.write(f"<{tag}>{escape(text or '')}</{tag}>")

def generate(config_path,out_root):
    cfg=load_config(config_path); out_root=Path(out_root); img_dir=out_root/IMG_REL; feed_dir=out_root/"ihub/feeds"; img_dir.mkdir(parents=True,exist_ok=True); feed_dir.mkdir(parents=True,exist_ok=True)
    ids=zlib.decompress(base64.b64decode(cfg['ids_zlib_b64'])).decode('utf-8').splitlines(); addresses=cfg['addresses']; skus=cfg['skus']
    if len(ids)!=40020 or len(addresses)!=580 or len(skus)!=69: raise SystemExit("config cardinality failed")
    files=[]
    for sku in skus:
        jpg=Path(sku['cover_png']).stem+".jpg"
        if not (img_dir/jpg).is_file(): raise SystemExit(f"approved SKU image missing: {jpg}")
        files.append(jpg)
    for png in cfg['universal_png']:
        jpg=Path(png).stem+".jpg"
        if not (img_dir/jpg).is_file(): raise SystemExit(f"approved universal image missing: {jpg}")
        files.append(jpg)
    if len(files)!=74 or len(set(files))!=74: raise SystemExit("image set failed")
    for jpg in files:
        with Image.open(img_dir/jpg) as im: im.verify()
    manifest=[{"number":i+1,"filename":fn,"url":f"{BASE_URL}/{fn}"} for i,fn in enumerate(files)]
    (out_root/"ihub/iHub_PUBLIC_PHOTO_URLS.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    universal_jpg=[Path(x).stem+".jpg" for x in cfg['universal_png']]; idx=0; feed_paths=[]
    for part,(c0,c1) in enumerate([(0,290),(290,580)],1):
        out=feed_dir/f"iHub_STRUCTURE_40020_URL_FINAL_PART_{part}_{1 if part==1 else 20011:05d}-{20010 if part==1 else 40020}.xml"
        with out.open('w',encoding='utf-8',newline='') as f:
            f.write('<?xml version="1.0" encoding="utf-8"?>'); f.write('<Ads formatVersion="3" target="Avito.ru">')
            for city_i in range(c0,c1):
                addr=addresses[city_i]
                for sku in skus:
                    aid=ids[idx]; idx+=1; f.write('<Ad>'); write_tag(f,'Id',aid); inserted_addr=False
                    for field in sku['fields']:
                        tag=field['tag']
                        if tag=='Set':
                            f.write('<Set>')
                            for opt in field['options']: write_tag(f,'Option',opt)
                            f.write('</Set>')
                        else: write_tag(f,tag,field['text'])
                        if tag=='ContactMethod': write_tag(f,'Address',addr); inserted_addr=True
                    if not inserted_addr: raise SystemExit("Address insertion point missing")
                    cover=Path(sku['cover_png']).stem+".jpg"; urls=[f"{BASE_URL}/{cover}"]+[f"{BASE_URL}/{x}" for x in universal_jpg]
                    f.write('<Images>')
                    for u in urls: f.write(f'<Image url={quoteattr(u)}/>')
                    f.write('</Images></Ad>')
            f.write('</Ads>')
        feed_paths.append(out)
    total=0; all_ids=set(); all_urls=Counter(); first=Counter()
    for out in feed_paths:
        for _,ad in ET.iterparse(out,events=('end',)):
            if ad.tag!='Ad': continue
            total+=1; aid=(ad.findtext('Id') or '').strip()
            if aid in all_ids: raise SystemExit(f"duplicate id {aid}")
            all_ids.add(aid); ims=[x.attrib.get('url','') for x in ad.find('Images').findall('Image')]
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
    (out_root/"ihub/iHub_URL_FEED_FINAL_VALIDATION.txt").write_text(report,encoding='utf-8'); return feed_paths

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--config",required=True); ap.add_argument("--out",default="."); args=ap.parse_args(); generate(args.config,args.out)
