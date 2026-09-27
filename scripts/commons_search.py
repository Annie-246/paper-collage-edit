# search Wikimedia Commons and download 1200px thumbnails: python commons.py "<query>" prefix N
import sys, json, urllib.request, urllib.parse, os
q, pre, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
UA = {"User-Agent": "paper-collage-edit/1.0 (educational video)"}
url = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({
    "action": "query", "format": "json", "generator": "search", "gsrsearch": q, "gsrnamespace": 6, "gsrlimit": n,
    "prop": "imageinfo", "iiprop": "url|extmetadata", "iiurlwidth": 1200})
data = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA)))
pages = sorted(data.get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 0))
for i, p in enumerate(pages):
    ii = p["imageinfo"][0]
    th = ii.get("thumburl", ii["url"])
    if not th.lower().split("?")[0].endswith((".jpg", ".jpeg", ".png")):
        continue
    lic = ii.get("extmetadata", {}).get("LicenseShortName", {}).get("value", "?")
    out = f"assets/{pre}_{i}.jpg"
    try:
        open(out, "wb").write(urllib.request.urlopen(urllib.request.Request(th, headers=UA)).read())
        print(out, "|", p["title"], "|", lic)
    except Exception as e:
        print("fail", p["title"], e)
