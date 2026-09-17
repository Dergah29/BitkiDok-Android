"""Find explicit-license image candidates on Wikimedia Commons for GBIF gaps.

Metadata audit only. Search matches are not verified species labels.
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ALLOWED = {"CC0", "CC BY 4.0", "CC-BY-4.0", "Public domain"}
def search(species):
    params = {
        "action": "query", "format": "json", "generator": "search",
        "gsrsearch": '"' + species + '"', "gsrnamespace": 6, "gsrlimit": 50,
        "prop": "imageinfo", "iiprop": "url|mime|extmetadata",
        "iiextmetadatafilter": "LicenseShortName|LicenseUrl|Artist|Attribution",
    }
    req = urllib.request.Request("https://commons.wikimedia.org/w/api.php?"
        + urllib.parse.urlencode(params),
        headers={"User-Agent": "BitkiDokResearch/0.2 (Commons image metadata audit; github.com/Dergah29/BitkiDok-Android)"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)

def audit(coverage_file, output_file):
    baseline = json.loads(Path(coverage_file).read_text())
    missing = [x["species"] for x in baseline["species"] if x["usable_photos"] < 12]
    result = []
    for index, species in enumerate(missing, 1):
        try:
            pages = search(species).get("query", {}).get("pages", {})
            candidates = []
            for page in pages.values():
                info = (page.get("imageinfo") or [{}])[0]
                metadata = info.get("extmetadata") or {}
                license_name = metadata.get("LicenseShortName", {}).get("value", "")
                if license_name not in ALLOWED:
                    continue
                if info.get("mime") not in ("image/jpeg", "image/png", "image/webp"):
                    continue
                if species.lower() not in page["title"].lower().replace("_", " "):
                    continue
                candidates.append({"file_page": info.get("descriptionurl"),
                                   "image_url": info.get("url"),
                                   "license": license_name,
                                   "license_url": metadata.get("LicenseUrl", {}).get("value"),
                                   "attribution_html": metadata.get("Attribution", {}).get("value"),
                                   "author_html": metadata.get("Artist", {}).get("value")})
            result.append({"species": species, "matching_licensed_files": len(candidates),
                           "candidates": candidates})
        except Exception as exc:
            result.append({"species": species, "matching_licensed_files": 0,
                           "error": str(exc)[:200], "candidates": []})
        print(f"{index}/{len(missing)} {species}: {result[-1]['matching_licensed_files']}", flush=True)
        time.sleep(0.25)
    out = {"source": "Wikimedia Commons MediaWiki imageinfo API",
           "meaning": "Unreviewed candidate files with species string in title; requires human label and license verification before training.",
           "missing_species_checked": len(missing),
           "with_candidates": sum(bool(r["matching_licensed_files"]) for r in result),
           "results": result}
    Path(output_file).write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")

if __name__ == "__main__":
    audit(sys.argv[1], sys.argv[2])
