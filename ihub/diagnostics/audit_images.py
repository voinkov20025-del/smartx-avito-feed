from pathlib import Path
from collections import Counter
import json,xml.etree.ElementTree as ET,urllib.request,urllib.error
from PIL import Image,ImageStat
root=Path(".")
lines=["iHub photo/feed diagnostic — READ-ONLY AUDIT",""]
dirs=["ihub/images/2026-10-05","ihub/images/2026-11-02","ihub/images/2026-11-02-final"]
for dr in dirs:
    entries=sorted((root/dr).glob("*.jpg"))
    black=[]; invalid=[]; sizes=Counter(); sizebytes=[]
    for p in entries:
        try:
            with Image.open(p) as im:
                im.load()
                sizes[str(im.size)]+=1
                small=im.convert("RGB").resize((64,64))
                pixels=list(small.getdata())
                ratio=sum(max(rgb)<22 for rgb in pixels)/len(pixels)
                if ratio>.82: black.append((p.name,round(ratio,3)))
        except Exception as e: invalid.append((p.name,str(e)))
        sizebytes.append(p.stat().st_size)
    lines += [f"FOLDER {dr}: files={len(entries)}, dimensions={dict(sizes)}, bytes_min={min(sizebytes) if sizebytes else 0}, bytes_max={max(sizebytes) if sizebytes else 0}, black_candidates={black}, corrupt={invalid}"]
lines.append("")
feeds=[
 "ihub/feeds/iHub_STRUCTURE_40020_URL_FINAL_PART_1_00001-20010.xml",
 "ihub/feeds/iHub_STRUCTURE_40020_URL_FINAL_PART_2_20011-40020.xml",
 "ihub/feeds/iHub_STRUCTURE_13920_URL_FINAL_PART_3_40021-53940.xml",
 "ihub/feeds/ihub-final-part-1-00001-20000.xml",
 "ihub/feeds/ihub-final-part-2-20001-40000.xml",
]
for f in feeds:
    p=root/f
    if not p.exists(): lines.append(f"FEED MISSING {f}"); continue
    count=0; bad6=0; first=[]; schemes=Counter(); uniq=set(); names=Counter()
    try:
        for _,el in ET.iterparse(p,events=("end",)):
            if el.tag=="Ad":
                count+=1
                imgs=el.find("Images")
                imlist=list(imgs) if imgs is not None else []
                if len(imlist)!=6: bad6+=1
                if count<=2: first.append([dict(item.attrib) for item in imlist])
                for item in imlist:
                    v=item.attrib.get("url",item.attrib.get("name",""))
                    if v.startswith("https://raw.githubusercontent.com/"): schemes["github_raw_https"]+=1
                    elif v.startswith("http://avito.ru/"): schemes["avito_internal_http"]+=1
                    elif v.startswith("https://"):schemes["other_https"]+=1
                    else:schemes["other"]+=1
                    uniq.add(v)
                    names[item.tag]+=1
                el.clear()
        lines += [f"FEED {f}: ads={count}, wrong_image_count={bad6}, image_refs={dict(schemes)}, unique_image_refs={len(uniq)}, first_two={json.dumps(first,ensure_ascii=False)[:1800]}"]
    except Exception as e:lines += [f"FEED PARSE FAILURE {f}: {type(e).__name__}: {e}"]
lines.append("")
rawbase="https://raw.githubusercontent.com/voinkov20025-del/smartx-avito-feed/main/"
samples=[
 "ihub/images/2026-10-05/iphone-12-mini-128-white-01-cover.jpg",
 "ihub/images/2026-10-05/universal-02-avito-delivery.jpg",
 "ihub/images/2026-11-02-final/iphone-15-pro-128-black-01-cover.jpg",
 "ihub/feeds/iHub_STRUCTURE_40020_URL_FINAL_PART_1_00001-20010.xml",
 "ihub/feeds/iHub_STRUCTURE_40020_URL_FINAL_PART_2_20011-40020.xml",
 "ihub/feeds/iHub_STRUCTURE_13920_URL_FINAL_PART_3_40021-53940.xml",
 "ihub/feeds/ihub-final-part-1-00001-20000.xml",
 "ihub/feeds/ihub-final-part-2-20001-40000.xml",
]
for path in samples:
    try:
        req=urllib.request.Request(rawbase+path,headers={"User-Agent":"iHub-public-asset-diagnostic/1.0","Range":"bytes=0-255"})
        with urllib.request.urlopen(req,timeout=25) as r:
            head=r.read(255)
            lines.append(f"PUBLIC {path}: status={r.status}, type={r.headers.get('Content-Type')}, starts={head[:32]!r}")
    except Exception as e:lines.append(f"PUBLIC FAILED {path}: {type(e).__name__}: {e}")
out=Path("ihub/diagnostics/PHOTO_AUDIT_RESULT.txt")
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text("\n".join(lines)+"\n",encoding="utf-8")
print("\n".join(lines))
