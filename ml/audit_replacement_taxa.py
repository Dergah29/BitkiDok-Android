"""Probe replacement houseplant taxa; results are leads, never approved photo labels."""
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

NAMES = (
    "Alocasia micholitziana", "Hoya obovata", "Pilea mollis",
    "Dischidia nummularia", "Hoya wayetii", "Calathea warscewiczii",
    "Ctenanthe setosa", "Hoya lacunosa", "Monstera pinnatipartita",
    "Begonia amphioxus", "Hoya retusa",
)
HEADERS = {"Accept": "application/json",
           "User-Agent": "BitkiDokReplacementAudit/0.1 (github.com/Dergah29/BitkiDok-Android)"}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=25) as response:
        return json.load(response)


def query(url, params):
    return get(url + "?" + urllib.parse.urlencode(params))


def audit(catalog_path, prior_path, output_path):
    catalog = json.loads(Path(catalog_path).read_text(encoding="utf-8"))
    prior = json.loads(Path(prior_path).read_text(encoding="utf-8"))
    prior_names = {x["catalog_name"] for x in prior["records"]}
    prior_accepted = {x["resolved_accepted_key"] for x in prior["records"]}
    results = []
    for name in NAMES:
        row = {"requested_name": name, "already_named": name in prior_names,
               "gbif_match": None, "inat_exact_species": None, "errors": []}
        try:
            hit = query("https://api.gbif.org/v1/species/match",
                        {"name": name, "strict": "true"})
            key = hit.get("acceptedUsageKey") or hit.get("usageKey")
            row["gbif_match"] = {
                "matchType": hit.get("matchType"), "confidence": hit.get("confidence"),
                "scientificName": hit.get("scientificName"), "rank": hit.get("rank"),
                "status": hit.get("status"), "key": key,
                "already_in_catalog_accepted_keys": key in prior_accepted}
            if key:
                accepted = get(f"https://api.gbif.org/v1/species/{key}")
                row["gbif_accepted"] = {"scientificName": accepted.get("scientificName"),
                    "rank": accepted.get("rank"), "taxonomicStatus": accepted.get("taxonomicStatus"),
                    "acceptedKey": accepted.get("acceptedKey")}
        except Exception as exc:
            row["errors"].append("GBIF " + str(exc)[:150])
        time.sleep(0.5)
        try:
            taxa = query("https://api.inaturalist.org/v1/taxa/autocomplete",
                         {"q": name, "per_page": 30})
            hits = [x for x in taxa.get("results", []) if x.get("name") == name and x.get("rank") == "species"]
            row["inat_exact_species"] = [{"id": x["id"],
                 "observations_count": x.get("observations_count")} for x in hits]
        except Exception as exc:
            row["errors"].append("iNaturalist " + str(exc)[:150])
        results.append(row)
        print(name, row["gbif_match"], row["inat_exact_species"], flush=True)
        time.sleep(0.6)
    report = {"warning": "GBIF matches and iNaturalist observation counts are metadata leads, not licensed photo coverage or approved training classes.",
              "sources": ["https://api.gbif.org/v1/species/match",
                          "https://api.gbif.org/v1/species/{accepted_key}",
                          "https://api.inaturalist.org/v1/taxa/autocomplete"],
              "candidates": results}
    Path(output_path).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("catalog", type=Path)
    p.add_argument("prior", type=Path)
    p.add_argument("output", type=Path)
    a = p.parse_args()
    audit(a.catalog, a.prior, a.output)
