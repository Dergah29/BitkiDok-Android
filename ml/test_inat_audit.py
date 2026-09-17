"""Check that restricted photos and related taxa never enter candidate counts."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import audit_inat_candidates as audit


class CandidateFilteringTest(unittest.TestCase):
    def test_only_exact_species_and_individually_commercial_photos(self):
        with tempfile.TemporaryDirectory() as directory:
            baseline = Path(directory) / "baseline.json"
            output = Path(directory) / "report.json"
            baseline.write_text(json.dumps({"counts": [{"species": "Monstera deliciosa", "usable_photos": 0}]}))

            def fake_json(endpoint, _params):
                if endpoint == "taxa/autocomplete":
                    return {"results": [{"id": 1, "name": "Monstera deliciosa", "rank": "species"}]}
                return {"total_results": 3, "results": [
                    {"id": 10, "taxon": {"id": 1}, "photos": [
                        {"id": 100, "license_code": "cc-by-nc", "url": "https://example.com/100.jpg"},
                        {"id": 101, "license_code": "cc-by", "url": "https://example.com/101.jpg"},
                        {"id": 102, "license_code": None, "url": "https://example.com/102.jpg"}]},
                    {"id": 11, "taxon": {"id": 2}, "photos": [
                        {"id": 103, "license_code": "cc0", "url": "https://example.com/103.jpg"}]},
                    {"id": 12, "taxon": {"id": 1}, "photos": [
                        {"id": 101, "license_code": "cc-by", "url": "https://example.com/101.jpg"},
                        {"id": 104, "license_code": "cc0", "url": "http://example.com/104.jpg"}]}]}

            with patch.object(audit, "get_json", side_effect=fake_json), patch.object(audit.time, "sleep"):
                audit.audit(baseline, output, limit=1, pages=1, pause=0)
            row = json.loads(output.read_text())["results"][0]
            self.assertEqual(row["candidate_photos"], 1)
            self.assertEqual(row["candidate_observations"], 1)
            self.assertEqual(row["candidates"][0]["photo_license"], "cc-by")


if __name__ == "__main__":
    unittest.main()
