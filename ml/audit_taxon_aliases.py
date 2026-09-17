"""Research taxonomy name mismatches; never auto-map image labels."""
import argparse
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

USER_AGENT = "BitkiDokTaxonomyAudit/0.1 (github.com/Dergah29/BitkiDok-Android)"


def get_json(url):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=25) as response:
        return json.load(response)


def audit(coverage_path, catalog_path, out_path):
    coverage = json.loads(Path(coverage_path).read_text(encoding="utf-8"))
    catalog = json.loads(Path(catalog_path).read_text(encoding="utf-8"))
    by_name = {p["accepted_name"]: p for p in catalog}
    unmatched = [p["species"] for p in coverage["results"]
                 if p["status"] == "no_unambiguous_exact_species_match"]
    results = []
    for name in unmatched:
        gbif_key = by_name[name]["gbif_taxon_key"]
        row = {"catalog_name": name, "gbif_taxon_key": gbif_key, "gbif": None,
               "inat_autocomplete_candidates": [], "errors": []}
        try:
            taxon = get_json(f"https://api.gbif.org/v1/species/{gbif_key}")
            row["gbif"] = {key: taxon.get(key) for key in
                           ("canonicalName", "rank", "taxonomicStatus", "acceptedKey", "accepted", "scientificName")}
        except Exception as exc:
            row["errors"].append("GBIF: " + str(exc)[:120])
        time.sleep(1.1)
        try:
            params = urllib.parse.urlencode({"q": name, "per_page": 30})
            data = get_json("https://api.inaturalist.org/v1/taxa/autocomplete?" + params)
            row["inat_autocomplete_candidates"] = [
                {"name": t.get("name"), "rank": t.get("rank"), "id": t.get("id"),
                 "observations_count": t.get("observations_count")}
                for t in data.get("results", [])[:8]]
        except Exception as exc:
            row["errors"].append("iNaturalist: " + str(exc)[:120])
        results.append(row)
        print(f"{len(results)}/{len(unmatched)} {name}: {len(row['inat_autocomplete_candidates'])} suggestions", flush=True)
        time.sleep(1.1)
    report = {"catalog_gap_names_checked": len(unmatched), "sources": [
        "https://api.gbif.org/v1/species/{gbif_taxon_key}",
        "https://api.inaturalist.org/v1/taxa/autocomplete?q={catalog_name}"],
        "warning": "Suggestions are not a synonym mapping. Botanical review is required before merging species labels or collecting photos under another name.",
        "results": results}
    Path(out_path).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("coverage", type=Path)
    parser.add_argument("catalog", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    audit(args.coverage, args.catalog, args.out)
