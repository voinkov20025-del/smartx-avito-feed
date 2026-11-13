#!/usr/bin/env python3
"""Attach existing Avito listing numbers to old XPhone feed rows without changing IDs."""
import csv
import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parent
MAP=ROOT/"legacy_avito_id_map_2026-11-13.csv"
mapping={}
statuses=Counter()
with MAP.open(encoding="utf-8",newline="") as fh:
    for row in csv.DictReader(fh):
        key=row["Id"].strip()
        avito=row["AvitoId"].strip()
        st=row["OldStatus"].strip()
        assert re.fullmatch(r"xph_20261013_\d{6}",key)
        assert avito.isdigit() and 9<=len(avito)<=12
        assert key not in mapping
        assert st in ("expired","removed")
        mapping[key]=(avito,st)
        statuses[st]+=1
assert len(mapping)==1527 and statuses=={"expired":1524,"removed":3},statuses
assert len({v[0] for v in mapping.values()})==1527

id_pattern=re.compile(rb"(<Id>(xph_20261013_\d{6})</Id>)")
avito_tag=re.compile(rb"<AvitoId>\d+</AvitoId>")
seen=set()
all_ids=set()
all_affected=Counter()
result=[]
changed=0
for part in (1,2):
    path=ROOT/f"feed-part-{part}.xml"
    original=path.read_bytes()
    assert b"<AvitoId>" not in original, "Unexpected pre-existing AvitoId requires manual review"
    def replace_match(m):
        global changed
        key=m.group(2).decode("ascii")
        if key not in mapping:
            return m.group(0)
        assert key not in seen
        seen.add(key)
        changed+=1
        avito,st=mapping[key]
        all_affected[st]+=1
        return m.group(1)+f"<AvitoId>{avito}</AvitoId>".encode("ascii")
    updated=id_pattern.sub(replace_match,original)
    assert avito_tag.sub(b"",updated)==original,"Unexpected modification outside new AvitoId"
    root=ET.fromstring(updated)
    ads=root.findall("Ad")
    assert len(ads)==20000,(part,len(ads))
    count=0
    for a in ads:
        id_=a.findtext("Id")
        assert id_ and id_ not in all_ids
        all_ids.add(id_)
        id_link=a.findtext("AvitoId")
        if id_ in mapping:
            assert id_link==mapping[id_][0]
            assert a.find("DateEnd") is None
            assert a.find("DateBegin") is None
            assert a.find("ListingFee") is None
            count+=1
        else:
            assert id_link is None
    path.write_bytes(updated)
    result.append((part,len(ads),count,len(updated)))
assert len(all_ids)==40000
assert len(seen)==1517,(len(seen), sorted(set(mapping)-seen)[:15])
assert len(set(mapping)-seen)==10
assert all_affected=={"expired":1514,"removed":3},all_affected
report=(
    "XPhone Avito legacy reactivation linkage / 2026-11-13\n"
    "Links previously published AvitoId numbers to 1517 XPhone rows.\n"
    "All other XML bytes are unchanged: PASS\n"
    "Unchanged custom IDs (all ads): 40000\n"
    "Existing ads linked by AvitoId: 1517\n"
    "Expired linked: 1514\n"
    "Removed linked: 3\n"
    "Out-of-plan old ads omitted: 10\n"
    "No DateBegin, DateEnd, ListingFee added or edited.\n"
    "Paid-wallet fallback NOT enabled: PASS\n"
    "Avito processing / balance / moderation NOT VERIFIED.\n"
    + "\n".join(f"Part {p}: {n} ads, {c} linked, {size} bytes" for p,n,c,size in result)+"\n"
)
(ROOT/"REACTIVATION_LINKAGE_REPORT.txt").write_text(report,encoding="utf-8")
print(report)
