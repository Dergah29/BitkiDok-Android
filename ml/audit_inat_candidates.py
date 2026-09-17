"""Audit iNaturalist photo *candidates* for species missing from GBIF training.

Never train directly from this report: taxonomy, photo licenses, image bytes,
duplicates and independent smartphone-photo performance still need review.
"""
import argparse
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API = "https://api.inaturalist.org/v1/"
ALLOWED_PHOTO_LICENSES = {"cc0", "cc-by"}
USER_AGENT = "BitkiDokResearch/0.3 (photo-license metadata audit; github.com/Dergah29/BitkiDok-Android)"


def get_json(endpoint, params):
    url = API + endpoint + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=35) as response:
        return json.load(response)


def exact_taxon(species):
    data = get_json("taxa/autocomplete", {"q": species, "per_page": 30})
    exact = [taxon for taxon in data.get("results", [])
             if taxon.get("rank") == "species" and
             (taxon.get("name") or "").casefold() == species.casefold()]
    # An ambiguous exact taxon cannot safely serve as a class label.
    return exact[0] if len(exact) == 1 else None


def audit(baseline, out, limit, pages, pause):
    rows = json.loads(Path(baseline).read_text(encoding="utf-8"))["counts"]
    missing = [row for row in rows if row["usable_photos"] < 12]
    results = []
    for index, row in enumerate(missing[:limit], 1):
        name = row["species"]
        result = {"species": name, "gbif_usable_photos": row["usable_photos"],
                  "inat_taxon_id": None, "api_reported_observations": 0,
                  "candidate_observations": 0, "candidate_photos": 0,
                  "candidates": [], "status": "pending"}
        try:
            taxon = exact_taxon(name)
            if taxon is None:
                result["status"] = "no_unambiguous_exact_species_match"
            else:
                result["inat_taxon_id"] = taxon["id"]
                seen_observations, seen_photos = set(), set()
                for page in range(1, pages + 1):
                    time.sleep(pause)
                    data = get_json("observations", {
                        "taxon_id": taxon["id"], "quality_grade": "research",
                        "photos": "true", "photo_license": "cc0,cc-by",
                        "per_page": 100, "page": page, "order_by": "id", "order": "desc"})
                    result["api_reported_observations"] = data.get("total_results", 0)
                    observations = data.get("results", [])
                    for observation in observations:
                        observed_taxon = observation.get("taxon") or {}
                        # Taxon ID query can include descendants. Exclude varieties,
                        # subspecies and observations classified as another species.
                        if observed_taxon.get("id") != taxon["id"]:
                            continue
                        obs_id = observation.get("id")
                        if not obs_id or obs_id in seen_observations:
                            continue
                        seen_observations.add(obs_id)
                        for photo in observation.get("photos") or []:
                            photo_id = photo.get("id")
                            license_code = (photo.get("license_code") or "").lower()
                            url = photo.get("url") or ""
                            if (not photo_id or photo_id in seen_photos or
                                    license_code not in ALLOWED_PHOTO_LICENSES or
                                    not url.startswith("https://")):
                                continue
                            seen_photos.add(photo_id)
                            result["candidates"].append({
                                "observation_id": obs_id, "photo_id": photo_id,
                                "photo_license": license_code,
                                "photographer": (photo.get("attribution") or
                                                 (observation.get("user") or {}).get("login") or "unknown"),
                                "photo_url": url,
                                "observation_url": f"https://www.inaturalist.org/observations/{obs_id}"})
                    if len(observations) < 100:
                        break
                result["candidate_photos"] = len(result["candidates"])
                result["candidate_observations"] = len(seen_observations)
                result["status"] = "metadata_candidates_only"
        except Exception as exc:
            # A transport/HTTP error is unknown coverage, not zero photos.
            result["status"] = "query_error"
            result["error"] = f"{type(exc).__name__}: {str(exc)[:180]}"
        results.append(result)
        print(f"{index}/{min(len(missing), limit)} {name}: {result['status']} / {result['candidate_photos']}", flush=True)
        time.sleep(pause)
    report = {"source": "iNaturalist public API v1",
              "as_of_utc": datetime.now(timezone.utc).isoformat(),
              "source_terms": "https://www.inaturalist.org/pages/terms",
              "total_gbif_gap_species": len(missing),
              "species_queried": len(results),
              "species_with_photo_candidates": sum(r["candidate_photos"] > 0 for r in results),
              "candidate_photo_count": sum(r["candidate_photos"] for r in results),
              "query_errors": sum(r["status"] == "query_error" for r in results),
              "limitations": ["Only CC0/CC-BY per-photo metadata is retained; observation license alone is insufficient.",
                              "API counts are not downloaded, decoded or independently reviewed images.",
                              "Candidate taxon labels, licensing and photo duplicates need manual verification.",
                              "Some iNaturalist photos may overlap the earlier GBIF collection.",
                              "This is not a model evaluation and does not change the 101 trained classes."],
              "results": results}
    Path(out).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in
                      ("total_gbif_gap_species", "species_queried", "species_with_photo_candidates",
                       "candidate_photo_count", "query_errors")}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("baseline", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--limit", type=int, default=99)
    parser.add_argument("--pages", type=int, default=2)
    parser.add_argument("--pause", type=float, default=1.1)
    args = parser.parse_args()
    audit(args.baseline, args.out, args.limit, args.pages, args.pause)
