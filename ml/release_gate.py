"""Explicit release gate: reject candidate species models without evidence."""
import json
import sys
from pathlib import Path

def validate(directory, target=200, min_accuracy=0.80):
    directory = Path(directory)
    metrics = json.loads((directory / "species-metrics.json").read_text())
    labels = json.loads((directory / "species-labels.json").read_text())
    coverage = json.loads((directory / "coverage.json").read_text())
    result = {
        "class_count": len(labels),
        "required_class_count": target,
        "held_out_accuracy": metrics["val_accuracy"],
        "required_held_out_accuracy": min_accuracy,
        "independent_device_test_passed": False,
        "unknown_species_rejection_test_passed": False,
        "coverage_matches_labels": coverage["trained_species"] == len(labels),
        "ready_for_200_species_claim": False,
    }
    result["ready_for_200_species_claim"] = (
        len(labels) == target
        and coverage["trained_species"] == target
        and metrics["val_accuracy"] >= min_accuracy
        and result["independent_device_test_passed"]
        and result["unknown_species_rejection_test_passed"]
    )
    (directory / "release-gate.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    validate(sys.argv[1])
