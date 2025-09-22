#!/usr/bin/env python3
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import os
import sys

# ضع هنا رابط الـ Atom الخاص بمدونتك
BASE_ATOM = "https://www.elmostshfaa.com/atom.xml?redirect=false"
MAX_PER_REQUEST = 500
OUTPUT_PATH = "docs/sitemap.xml"

session = requests.Session()
namespaces = {'atom': 'http://www.w3.org/2005/Atom'}

def fetch_entries(start_index):
    params = {'start-index': str(start_index), 'max-results': str(MAX_PER_REQUEST)}
    r = session.get(BASE_ATOM, params=params, timeout=30)
    r.raise_for_status()
    root = ET.fromstring(r.text.encode('utf-8'))
    entries = root.findall('atom:entry', namespaces)
    result = []
    for e in entries:
        link = None
        for l in e.findall('atom:link', namespaces):
            if l.attrib.get('rel','') == 'alternate' and l.attrib.get('href'):
                link = l.attrib.get('href'); break
        updated = e.find('atom:updated', namespaces)
        updated_text = updated.text if updated is not None else None
        if link:
            result.append((link, updated_text))
    return result

start = 1
urls = []
while True:
    try:
        batch = fetch_entries(start)
    except Exception as exc:
        print("Error fetching Atom feed:", exc, file=sys.stderr)
        break
    if not batch: break
    urls.extend(batch)
    if len(batch) < MAX_PER_REQUEST: break
    start += MAX_PER_REQUEST

if not urls:
    print("No URLs found in feed. Exiting.", file=sys.stderr)
    sys.exit(1)

seen = set(); unique = []
for u, updated in urls:
    if u in seen: continue
    seen.add(u); unique.append((u, updated))

urlset = ET.Element('urlset', xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
for u, updated in unique:
    url_el = ET.SubElement(urlset, 'url')
    loc = ET.SubElement(url_el, 'loc'); loc.text = u
    if updated:
        try:
            dt = datetime.fromisoformat(updated.replace('Z', '+00:00'))
            lastmod = ET.SubElement(url_el, 'lastmod'); lastmod.text = dt.date().isoformat()
        except Exception:
            pass

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
tree = ET.ElementTree(urlset)
tree.write(OUTPUT_PATH, encoding='utf-8', xml_declaration=True)
print(f"Wrote sitemap with {len(unique)} URLs to {OUTPUT_PATH}")
