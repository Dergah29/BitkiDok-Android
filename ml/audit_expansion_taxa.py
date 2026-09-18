"""Taxonomy-only prospecting for commonly grown aroids, prayer plants and ferns."""
import json
import time
from pathlib import Path
from audit_replacement_taxa import query, get

NAMES = (
    "Maranta leuconeura", "Goeppertia orbifolia", "Goeppertia makoyana",
    "Goeppertia insignis", "Goeppertia ornata", "Goeppertia roseopicta",
    "Goeppertia zebrina", "Stromanthe sanguinea", "Ctenanthe burle-marxii",
    "Ctenanthe lubbersiana", "Nephrolepis exaltata", "Asplenium nidus",
    "Platycerium bifurcatum", "Davallia fejeensis", "Phlebodium aureum",
    "Alocasia odora", "Alocasia lauterbachiana", "Alocasia sinuata",
    "Monstera standleyana", "Anthurium warocqueanum",
    "Anthurium forgetii", "Peperomia ferreyrae", "Pilea involucrata",
    "Begonia pavonina", "Dischidia ruscifolia",
)

def audit(catalog_path, audit_path, previous_path, output_path):
    catalog = json.loads(Path(catalog_path).read_text(encoding="utf-8"))
    prior = json.loads(Path(audit_path).read_text(encoding="utf-8"))
    old = json.loads(Path(previous_path).read_text(encoding="utf-8"))
    used_keys = {x["resolved_accepted_key"] for x in prior["records"]}
    previous_keys = {x["gbif_match"]["key"] for x in old["candidates"] if x["gbif_match"]}
    names = {x["accepted_name"] for x in catalog}
    results = []
    for name in NAMES:
        row = {"requested_name": name, "already_named": name in names,
               "gbif_match": None, "inat_exact_species": [], "errors": []}
        try:
            hit = query("https://api.gbif.org/v1/species/match", {"name": name, "strict": "true"})
            key = hit.get("acceptedUsageKey") or hit.get("usageKey")
            row["gbif_match"] = {"matchType": hit.get("matchType"), "confidence": hit.get("confidence"),
                "scientificName": hit.get("scientificName"), "rank": hit.get("rank"),
                "status": hit.get("status"), "key": key,
                "already_in_catalog_accepted_keys": key in used_keys,
                "already_in_previous_candidate_keys": key in previous_keys}
            if key:
                taxon = get(f"https://api.gbif.org/v1/species/{key}")
                row["gbif_accepted"] = {"scientificName": taxon.get("scientificName"),
                    "rank": taxon.get("rank"), "taxonomicStatus": taxon.get("taxonomicStatus")}
        except Exception as exc:
            row["errors"].append("GBIF " + str(exc)[:150])
        time.sleep(0.5)
        try:
            data = query("https://api.inaturalist.org/v1/taxa/autocomplete", {"q": name, "per_page": 30})
            row["inat_exact_species"] = [{"id": x["id"], "observations_count": x.get("observations_count")}
                for x in data.get("results", []) if x.get("name") == name and x.get("rank") == "species"]
        except Exception as exc:
            row["errors"].append("iNaturalist " + str(exc)[:150])
        results.append(row)
        print(name, row["gbif_match"], row["inat_exact_species"], flush=True)
        time.sleep(0.6)
    report = {"warning": "Metadata and botanical candidates only, no commercially licensed photo count or approved training class.",
        "sources": ["https://api.gbif.org/v1/species/match",
                    "https://api.inaturalist.org/v1/taxa/autocomplete"],
        "candidates": results}
    Path(output_path).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

if __name__ == "__main__":
    import sys
    audit(*sys.argv[1:5])
