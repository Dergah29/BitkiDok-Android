"""Resolve accepted ranks of GBIF synonyms in the 200-entry catalog audit."""
import argparse
import json
import time
import urllib.request
from pathlib import Path


def fetch(key):
    req = urllib.request.Request(
        f"https://api.gbif.org/v1/species/{key}",
        headers={"User-Agent": "BitkiDokRankAudit/0.1 (github.com/Dergah29/BitkiDok-Android)",
                 "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=25) as response:
        return json.load(response)


def audit(source, output):
    original = json.loads(Path(source).read_text(encoding="utf-8"))
    records = original["records"]
    keys = sorted({r["resolved_accepted_key"] for r in records
                   if r["taxonomicStatus"] == "SYNONYM"})
    target = {}
    for i, key in enumerate(keys, 1):
        for attempt in range(3):
            try:
                taxon = fetch(key)
                target[key] = {"canonicalName": taxon.get("canonicalName"),
                               "scientificName": taxon.get("scientificName"),
                               "rank": taxon.get("rank"),
                               "taxonomicStatus": taxon.get("taxonomicStatus"),
                               "acceptedKey": taxon.get("acceptedKey")}
                break
            except Exception as error:
                target[key] = {"error": f"{type(error).__name__}: {str(error)[:120]}"}
                time.sleep(1 + attempt)
        print(f"{i}/{len(keys)} accepted key {key}", flush=True)
        time.sleep(0.5)
    resolved = {}
    for row in records:
        key = row["resolved_accepted_key"]
        rank = row["rank"] if row["taxonomicStatus"] == "ACCEPTED" else target[key].get("rank")
        resolved.setdefault(key, {"rank": rank, "catalog_names": []})["catalog_names"].append(row["catalog_name"])
    by_rank = {}
    for row in resolved.values():
        rank = row["rank"] or "UNKNOWN"
        by_rank[rank] = by_rank.get(rank, 0) + 1
    report = {"source_run": "https://github.com/Dergah29/BitkiDok-Android/actions/runs/35268209829",
              "resolved_accepted_keys": len(resolved),
              "distinct_accepted_keys_by_rank": by_rank,
              "synonym_accepted_targets": target,
              "non_species_accepted_targets": [
                  {"accepted_key": key, **item} for key, item in resolved.items() if item["rank"] != "SPECIES"],
              "warning": "Taxonomy key counts are not model class counts. Botanical and photo-level verification remains necessary."}
    Path(output).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    audit(args.source, args.output)
