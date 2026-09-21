#!/usr/bin/env python3
"""Re-check current iNaturalist observation taxon and per-photo licenses (live audit).

Reads only already-downloaded candidate manifests. This audit does not approve
botanical identity or image quality and does not download images.
"""
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
INPUTS = [
    REPO / "data/expansion_download_validation_24.json",
    REPO / "data/replacement_download_validation_11.json",
]
ALLOWED = {"cc0", "cc-by"}

def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "BitkiDok license audit/1.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)

rows = []
for path in INPUTS:
    payload = json.loads(path.read_text(encoding="utf-8"))
    for result in payload["results"]:
        species = result["species"]
        for photo in result.get("validated_photos", []):
            rows.append({
                "manifest": path.name,
                "species": species,
                "observation_id": int(photo["observation_id"]),
                "photo_id": int(photo["photo_id"]),
                "manifest_license": str(photo.get("license_metadata") or "").lower(),
            })

by_observation = {}
for row in rows:
    by_observation.setdefault(row["observation_id"], []).append(row)

live = {}
ids = list(by_observation)
for offset in range(0, len(ids), 100):
    batch = ids[offset:offset + 100]
    query = urllib.parse.urlencode({"id": ",".join(map(str, batch)), "per_page": 100})
    data = get_json("https://api.inaturalist.org/v1/observations?" + query)
    for obs in data.get("results", []):
        live[int(obs["id"])] = obs
    time.sleep(1)

checks = []
for row in rows:
    obs = live.get(row["observation_id"])
    item = dict(row)
    if not obs:
        item.update({"status": "missing_observation"})
        checks.append(item)
        continue
    photo = next((p for p in obs.get("photos", []) if int(p.get("id", -1)) == row["photo_id"]), None)
    live_taxon = (obs.get("taxon") or {}).get("name")
    live_license = str((photo or {}).get("license_code") or "").lower()
    item.update({
        "live_taxon": live_taxon,
        "live_photo_license": live_license,
        "quality_grade": obs.get("quality_grade"),
        "photo_present": photo is not None,
        "taxon_exact_match": live_taxon == row["species"],
        "license_allowed": live_license in ALLOWED,
        "license_unchanged": live_license == row["manifest_license"],
    })
    if not photo:
        item["status"] = "photo_missing"
    elif live_license not in ALLOWED:
        item["status"] = "license_not_allowed"
    elif live_taxon != row["species"]:
        item["status"] = "taxon_changed_or_not_exact"
    else:
        item["status"] = "metadata_pass"
    checks.append(item)

summary = {}
for item in checks:
    summary[item["status"]] = summary.get(item["status"], 0) + 1

out = {
    "audited_at_utc": datetime.now(timezone.utc).isoformat(),
    "source_api": "https://api.inaturalist.org/v1/observations",
    "allowed_photo_licenses": sorted(ALLOWED),
    "meaning": "Live metadata audit only; not botanical visual verification, duplicate clearance, specimen independence, or training approval.",
    "candidate_photos_checked": len(checks),
    "summary": summary,
    "checks": checks,
}
target = REPO / "data/inat_live_license_taxon_audit.json"
target.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"target": str(target), "summary": summary, "checked": len(checks)}, indent=2))
