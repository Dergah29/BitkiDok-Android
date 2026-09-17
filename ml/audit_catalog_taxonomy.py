"""Audit all catalog GBIF keys; report accepted-taxon collisions, never auto-merge labels."""
import argparse
import json
import time
import urllib.request
from collections import defaultdict
from pathlib import Path


def fetch_taxon(key):
    req = urllib.request.Request(
        f"https://api.gbif.org/v1/species/{key}",
        headers={"Accept": "application/json",
                 "User-Agent": "BitkiDokCatalogAudit/0.1 (github.com/Dergah29/BitkiDok-Android)"})
    with urllib.request.urlopen(req, timeout=20) as response:
        return json.load(response)


def audit(catalog_path, out_path):
    catalog = json.loads(Path(catalog_path).read_text(encoding="utf-8"))
    if len(catalog) != 200 or len({x["gbif_taxon_key"] for x in catalog}) != 200:
        raise ValueError("Expected exactly 200 entries with unique GBIF keys")
    records = []
    for index, item in enumerate(catalog, 1):
        key = item["gbif_taxon_key"]
        record = {"catalog_name": item["accepted_name"], "gbif_taxon_key": key}
        for attempt in range(3):
            try:
                taxon = fetch_taxon(key)
                record.update({field: taxon.get(field) for field in
                    ("canonicalName", "scientificName", "rank", "taxonomicStatus", "acceptedKey", "accepted")})
                break
            except Exception as error:
                record["error"] = f"{type(error).__name__}: {str(error)[:120]}"
                if attempt < 2:
                    time.sleep(1 + attempt)
        else:
            record["status"] = "unresolved"
        if "taxonomicStatus" in record:
            record.pop("error", None)
        records.append(record)
        print(f"{index}/{len(catalog)} {record['catalog_name']}", flush=True)
        time.sleep(0.3)
    groups = defaultdict(list)
    for record in records:
        if "taxonomicStatus" not in record:
            continue
        status = record["taxonomicStatus"]
        resolved_key = record["acceptedKey"] if status == "SYNONYM" else record["gbif_taxon_key"]
        if resolved_key is None:
            record["status"] = "unresolved"
            continue
        record["resolved_accepted_key"] = resolved_key
        groups[resolved_key].append(record["catalog_name"])
    collisions = [{"accepted_key": key, "catalog_names": names}
                  for key, names in sorted(groups.items()) if len(names) > 1]
    result = {
        "source": "https://api.gbif.org/v1/species/{gbif_taxon_key}",
        "catalog_entry_count": len(catalog),
        "resolved_count": sum("resolved_accepted_key" in r for r in records),
        "distinct_resolved_accepted_keys": len(groups),
        "duplicate_accepted_taxa": collisions,
        "warning": "GBIF accepted-key grouping is taxonomy metadata, not proof that horticultural forms are visually identical. Review non-species ranks and every proposed label merge.",
        "records": records,
    }
    Path(out_path).write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("catalog", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    audit(args.catalog, args.out)
