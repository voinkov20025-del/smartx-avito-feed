#!/usr/bin/env python3
"""Fix missing mandatory Color on exactly 1517 existing XPhone ads.

Source of truth: original Avito export stored as legacy_color_mapping_2026-11-13.csv.
Other fields, including public URLs, Id and AvitoId, are never modified.
"""
import csv
import re
from pathlib import Path
from collections import Counter
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent
mapping={}
with (ROOT/"legacy_color_mapping_2026-11-13.csv").open(encoding="utf-8",newline="") as f:
    for row in csv.DictReader(f):
        id_=row["Id"]
        assert id_ not in mapping
        mapping[id_]=(row["AvitoId"],row["Color"])
assert len(mapping)==1527, len(mapping)
allowed={"черный","белый","синий","зеленый","серый","фиолетовый","розовый","голубой","серебристый","золотистый"}
assert {v[1] for v in mapping.values()}==allowed

ad_re=re.compile(rb"<Ad>.*?</Ad>", re.DOTALL)
id_re=re.compile(rb"<Id>([^<]+)</Id>")
avito_re=re.compile(rb"<AvitoId>([^<]+)</AvitoId>")
condition_re=re.compile(rb"<Condition>[^<]+</Condition>")
inserted={}
all_ids=set()
all_address=set()
all_image_urls=set()
report=[]
for part in (1,2):
    path=ROOT/f"feed-part-{part}.xml"
    before=path.read_bytes()
    changed_in_part=[]
    def change_ad(m):
        raw=m.group(0)
        idmatch=id_re.search(raw)
        assert idmatch, "Missing ID"
        id_=idmatch.group(1).decode("utf-8")
        assert id_ not in all_ids, "Duplicate ID"
        all_ids.add(id_)
        if id_ not in mapping:
            return raw
        avito=avito_re.search(raw)
        assert avito and avito.group(1).decode("utf-8")==mapping[id_][0], "Wrong AvitoId for "+id_
        assert b"<Color>" not in raw, "Color already present; stop instead of overwriting"
        condition=condition_re.search(raw)
        assert condition, "Condition element missing for "+id_
        color=mapping[id_][1]
        assert color in allowed
        tag=("<Color>"+color+"</Color>").encode("utf-8")
        updated=raw[:condition.end()]+tag+raw[condition.end():]
        assert updated.replace(tag,b"",1)==raw,"Other XML bytes changed for "+id_
        inserted[id_]=color
        changed_in_part.append(id_)
        return updated
    after,count=ad_re.subn(change_ad,before)
    assert count==20000,(part,count)
    # Prove the rest of each feed is unchanged byte for byte.
    assert ad_re.sub(lambda m: re.sub(rb"<Color>[^<]*</Color>",b"",m.group(0)),after)==before
    tree=ET.fromstring(after)
    ads=tree.findall("Ad")
    assert tree.tag=="Ads" and len(ads)==20000
    for ad in ads:
        id_=ad.findtext("Id")
        assert id_ in all_ids
        if id_ in inserted:
            assert ad.findtext("Color")==inserted[id_]
            assert ad.findtext("AvitoId")==mapping[id_][0]
        else:
            assert ad.find("Color") is None
        addr=ad.findtext("Address")
        if addr:all_address.add(addr)
        for x in ad.findall("Images/Image"):
            url=x.get("url")
            if url:all_image_urls.add(url)
    path.write_bytes(after)
    report.append((part,len(changed_in_part),len(after)))
assert len(all_ids)==40000,len(all_ids)
assert len(all_address)==409,len(all_address)
assert len(all_image_urls)==103,len(all_image_urls)
assert len(inserted)==1517,(len(inserted),sorted(set(mapping)-set(inserted))[:20])
assert len(mapping.keys()-inserted.keys())==10
counts=Counter(inserted.values())
report_text=(
    "XPhone fix: mandatory Color for old listings / 2026-11-14\n"
    "Source: original Avito export of 1527 historical listings\n"
    "Rows actually updated in 40000 XML feed: 1517\n"
    "Out-of-plan original rows skipped: 10\n"
    "Older/expired listings may already have been manually relisted: previous ID and AvitoId preserved\n"
    "Original values retained (Color): "+repr(dict(sorted(counts.items())))+"\n"
    "Other bytes, including price, address, description and images, unchanged: PASS\n"
    "No new Id, no new AvitoId, no DateBegin/DateEnd, no ListingFee: PASS\n"
    "Total ads: 40000; distinct approved addresses: 409; image URLs: 103\n"
    "Avito acceptance / 1512 error resolution / remaining blocked: NOT YET VERIFIED\n"
    + "\n".join(f"PART_{part}: colors_added={num}, feed_bytes={size}" for part,num,size in report)+"\n"
)
(ROOT/"COLOR_FIX_REPORT.txt").write_text(report_text,encoding="utf-8")
print(report_text,flush=True)
