"""Download and validate metadata candidates; output audit only, never train here."""
import argparse
import hashlib
import io
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image, UnidentifiedImageError

LICENSES = {"cc-by", "cc0"}
HOSTS = {"inaturalist-open-data.s3.amazonaws.com", "static.inaturalist.org"}
MAX_BYTES = 4_000_000
PHOTO_PATH = re.compile(r"^/photos/(\d+)/(?:square|thumb|small|medium|large|original)\.(?:jpe?g|png)$", re.I)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def medium_url(photo):
    parsed = urllib.parse.urlsplit(photo["photo_url"])
    matched = PHOTO_PATH.fullmatch(parsed.path)
    if (parsed.scheme != "https" or parsed.hostname not in HOSTS or parsed.port or
            parsed.username or parsed.password or parsed.query or parsed.fragment or
            not matched or int(matched.group(1)) != photo["photo_id"]):
        raise ValueError("untrusted_photo_url")
    ext = parsed.path.rsplit(".", 1)[-1]
    return urllib.parse.urlunsplit(("https", parsed.hostname,
                                   f"/photos/{photo['photo_id']}/medium.{ext}", "", ""))


def read_image(url):
    request = urllib.request.Request(url, headers={"User-Agent": "BitkiDokResearch/0.3 (github.com/Dergah29/BitkiDok-Android)"})
    with urllib.request.build_opener(NoRedirect).open(request, timeout=22) as response:
        data = response.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("image_too_large")
    try:
        with Image.open(io.BytesIO(data)) as image:
            image.verify()
        with Image.open(io.BytesIO(data)) as image:
            width, height = image.size
            if image.format not in {"JPEG", "PNG"} or min(width, height) < 300:
                raise ValueError("small_or_unsupported_image")
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("invalid_image") from exc
    return hashlib.sha256(data).hexdigest(), width, height


def validate(input_path, output_path, max_per_species=25, delay=0.3):
    report = json.loads(Path(input_path).read_text(encoding="utf-8"))
    output = {"source": str(input_path), "meaning": "Downloaded decodable candidates, not verified taxonomy or production training data.",
              "max_per_species": max_per_species, "results": [], "errors": {}, "totals": {}}
    global_hashes = set()
    for row in report["results"]:
        result = {"species": row["species"], "gbif_usable_photos": row["gbif_usable_photos"],
                  "licensed_metadata_candidates": len(row["candidates"]), "downloaded_distinct_observations": 0,
                  "validated_photos": []}
        seen_observations = set()
        for photo in row["candidates"]:
            if len(result["validated_photos"]) >= max_per_species:
                break
            observation_id = photo["observation_id"]
            if observation_id in seen_observations or photo["photo_license"] not in LICENSES:
                continue
            try:
                url = medium_url(photo)
                digest, width, height = read_image(url)
                if digest in global_hashes:
                    raise ValueError("duplicate_image_bytes")
                global_hashes.add(digest)
                seen_observations.add(observation_id)
                result["validated_photos"].append({
                    "observation_id": observation_id, "photo_id": photo["photo_id"],
                    "license_metadata": photo["photo_license"], "photographer": photo["photographer"],
                    "medium_url": url, "sha256_medium": digest, "width": width, "height": height})
            except Exception as exc:
                reason = str(exc)[:65] if isinstance(exc, ValueError) else type(exc).__name__
                output["errors"][reason] = output["errors"].get(reason, 0) + 1
            time.sleep(delay)
        result["downloaded_distinct_observations"] = len(result["validated_photos"])
        output["results"].append(result)
        print(f"{result['species']}: {result['downloaded_distinct_observations']} downloaded", flush=True)
    output["totals"] = {"gap_species_checked": len(output["results"]),
                        "species_with_downloaded_photos": sum(bool(x["validated_photos"]) for x in output["results"]),
                        "downloaded_photos": sum(len(x["validated_photos"]) for x in output["results"]),
                        "species_potentially_reaching_12": sum(x["gbif_usable_photos"]+len(x["validated_photos"]) >= 12 for x in output["results"])}
    Path(output_path).write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(output["totals"], flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--max-per-species", type=int, default=25)
    args = parser.parse_args()
    validate(args.input, args.output, max_per_species=args.max_per_species)
