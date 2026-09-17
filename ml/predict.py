"""Try the experimental offline classifier on a local photo.

Usage: python ml/predict.py path/to/photo.jpg path/to/downloaded-artifact-folder
Requires: pip install tensorflow pillow
"""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps
import tensorflow as tf


def predict(photo: Path, model_dir: Path):
    labels = json.loads((model_dir / "labels.json").read_text(encoding="utf-8"))
    interpreter = tf.lite.Interpreter(model_path=str(model_dir / "model.tflite"))
    interpreter.allocate_tensors()
    input_info = interpreter.get_input_details()[0]
    output_info = interpreter.get_output_details()[0]
    if input_info["dtype"] != np.float32:
        raise ValueError("This example expects float32 model input")
    height, width = input_info["shape"][1:3]
    with Image.open(photo) as original:
        rgb = ImageOps.exif_transpose(original).convert("RGB")
        resized = rgb.resize((int(width), int(height)), Image.Resampling.BILINEAR)
        batch = np.asarray(resized, dtype=np.float32)[None, ...]
    # Rescaling to [-1, 1] is already embedded in model.tflite.
    interpreter.set_tensor(input_info["index"], batch)
    interpreter.invoke()
    scores = interpreter.get_tensor(output_info["index"])[0]
    if len(scores) != len(labels):
        raise ValueError("Label count does not match model output")
    return sorted(zip(labels, map(float, scores)), key=lambda item: item[1], reverse=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("photo", type=Path)
    parser.add_argument("model_dir", type=Path)
    args = parser.parse_args()
    results = predict(args.photo, args.model_dir)
    print("Experimental predictions (not a confirmed diagnosis):")
    for label, probability in results[:3]:
        print(f"{label}: {probability:.1%}")
    print("Only money plant, snake plant and spider plant are in the training data.")
    print("The model may confidently misclassify unsupported plants or conditions.")
