"""Small auditable coverage summary; full candidate metadata remains in CI artifact."""
import json
import sys
from pathlib import Path

source = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
rows = []
for row in source["results"]:
    rows.append({"species": row["species"], "inat_taxon_id": row["inat_taxon_id"],
                 "status": row["status"], "candidate_observations": row["eligible_observations"],
                 "candidate_photos": row["candidate_photos"],
                 "sample_photo_ids": [p["photo_id"] for p in row["photo_candidates"][:8]],
                 **({"error": row["error"]} if row.get("error") else {})})
summary = {
    "warning": "Metadata coverage only: image files, independent identity, licensing and duplicate audits remain.",
    "species_queried": len(rows),
    "candidate_photo_count": sum(x["candidate_photos"] for x in rows),
    "candidate_species_at_least_12_observations": sum(x["candidate_observations"] >= 12 for x in rows),
    "results": rows}
Path(sys.argv[2]).write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
