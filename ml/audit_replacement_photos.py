"""Photo-license metadata audit of proposed replacement species; no automatic training."""
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from audit_inat_candidates import get_json, ALLOWED_PHOTO_LICENSES


def audit(source_path, out_path):
    source = json.loads(Path(source_path).read_text(encoding="utf-8"))
    rows = []
    for row in source["candidates"]:
        gbif = row.get("gbif_accepted") or {}
        match = row.get("gbif_match") or {}
        if (gbif.get("rank") != "SPECIES" or gbif.get("taxonomicStatus") != "ACCEPTED"
                or match.get("already_in_catalog_accepted_keys")
                or match.get("already_in_previous_candidate_keys")):
            continue
        name = row["requested_name"]
        exact = row["inat_exact_species"] or []
        item = {"species": name, "inat_taxon_id": exact[0]["id"] if len(exact) == 1 else None,
                "eligible_observations": 0, "candidate_photos": 0, "photo_candidates": [],
                "status": "pending"}
        if len(exact) != 1:
            item["status"] = "no_unambiguous_exact_species_match"
        else:
            seen_ids, obs_ids = set(), set()
            try:
                for page in (1, 2):
                    data = get_json("observations", {
                        "taxon_id": item["inat_taxon_id"], "quality_grade": "research",
                        "photos": "true", "photo_license": "cc0,cc-by",
                        "per_page": 100, "page": page, "order_by": "id", "order": "desc"})
                    for obs in data.get("results", []):
                        if (obs.get("taxon") or {}).get("id") != item["inat_taxon_id"]:
                            continue
                        for photo in obs.get("photos") or []:
                            pid = photo.get("id")
                            lic = (photo.get("license_code") or "").lower()
                            url = photo.get("url") or ""
                            if not pid or pid in seen_ids or lic not in ALLOWED_PHOTO_LICENSES or not url.startswith("https://"):
                                continue
                            seen_ids.add(pid)
                            obs_ids.add(obs["id"])
                            item["photo_candidates"].append({
                                "photo_id": pid, "observation_id": obs["id"],
                                "photo_license": lic, "photo_url": url,
                                "photographer": photo.get("attribution") or (obs.get("user") or {}).get("login") or "unknown"})
                    if len(data.get("results", [])) < 100:
                        break
                    time.sleep(1)
                item["eligible_observations"] = len(obs_ids)
                item["candidate_photos"] = len(seen_ids)
                item["status"] = "metadata_candidates_only"
            except Exception as exc:
                item["status"] = "query_error"
                item["error"] = f"{type(exc).__name__}: {str(exc)[:150]}"
        rows.append(item)
        print(name, item["status"], item["candidate_photos"], flush=True)
        time.sleep(1)
    report = {"as_of_utc": datetime.now(timezone.utc).isoformat(),
        "source": "https://api.inaturalist.org/v1/observations",
        "warning": "Photo-specific CC0/CC-BY metadata only; file rights, species identity, image download, and duplicate review are still required.",
        "species_queried": len(rows), "candidate_photo_count": sum(x["candidate_photos"] for x in rows),
        "results": rows}
    Path(out_path).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("source", type=Path)
    p.add_argument("out", type=Path)
    a = p.parse_args()
    audit(a.source, a.out)
