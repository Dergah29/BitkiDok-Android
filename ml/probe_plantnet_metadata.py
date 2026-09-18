"""Probe official Pl@ntNet metadata-only share without downloading the 31.7 GB archive."""
import json
import re
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

URL = "https://lab.plantnet.org/seafile/d/bed81bc15e8944969cf6/"

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and "href" in attrs:
            self.links.append(attrs["href"])

def audit(output):
    report = {"source": URL, "status": "unknown", "metadata_files": [], "redirected_host": None}
    try:
        request = urllib.request.Request(URL, headers={"User-Agent": "BitkiDokMetadataResearch/0.1"})
        with urllib.request.urlopen(request, timeout=25) as response:
            page = response.read(150_000).decode("utf-8", errors="replace")
            report["status"] = response.status
            report["redirected_host"] = urllib.request.urlparse(response.geturl()).hostname
            for name in ("plantnet300K_metadata.json", "plantnet300K_species_id_2_name.json",
                         "class_idx_to_species_id.json"):
                if name in page:
                    report["metadata_files"].append(name)
            parser = Links()
            parser.feed(page)
            report["metadata_download_links_visible"] = sum(
                "download" in x.lower() or x.lower().endswith(".json") for x in parser.links)
    except Exception as error:
        report["error"] = f"{type(error).__name__}: {str(error)[:160]}"
    report["warning"] = "HTML probe only; no dataset images fetched and no commercial photo rights inferred."
    Path(output).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    import sys
    audit(sys.argv[1])
