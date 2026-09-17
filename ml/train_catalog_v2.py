"""Regularized 200-catalog candidate trainer; reports actual covered classes."""
import json
import random
import sys
from pathlib import Path
import numpy as np
import tensorflow as tf

def main(data, output):
    random.seed(42)
    np.random.seed(42)
    tf.random.set_seed(42)
    train = tf.keras.utils.image_dataset_from_directory(
        data / "train", image_size=(224, 224), batch_size=32, shuffle=True, seed=42)
    val = tf.keras.utils.image_dataset_from_directory(
        data / "val", image_size=(224, 224), batch_size=32, shuffle=False)
    names = train.class_names
    if len(names) < 4 or names != val.class_names:
        raise ValueError("Train and validation classes do not match")
    augmenter = tf.keras.Sequential([
        tf.keras.layers.RandomFlip("horizontal"),
        tf.keras.layers.RandomRotation(0.12),
        tf.keras.layers.RandomZoom(0.15),
        tf.keras.layers.RandomTranslation(0.08, 0.08),
        tf.keras.layers.RandomContrast(0.15),
    ])
    base = tf.keras.applications.MobileNetV2(
        input_shape=(224, 224, 3), include_top=False, weights="imagenet")
    base.trainable = False
    inputs = tf.keras.Input((224, 224, 3))
    x = augmenter(inputs)
    x = tf.keras.layers.Rescaling(1 / 127.5, offset=-1)(x)
    x = base(x, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dropout(0.4)(x)
    outputs = tf.keras.layers.Dense(len(names), activation="softmax",
        kernel_regularizer=tf.keras.regularizers.l2(0.001))(x)
    model = tf.keras.Model(inputs, outputs)
    model.compile(optimizer=tf.keras.optimizers.Adam(3e-4),
        loss="sparse_categorical_crossentropy", metrics=["accuracy"])
    model.fit(train, validation_data=val, epochs=20, verbose=2,
        callbacks=[tf.keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=4, restore_best_weights=True)])
    loss, accuracy = model.evaluate(val, verbose=0)
    truth, predictions = [], []
    for images, labels in val:
        predictions.append(model(images, training=False).numpy())
        truth.append(labels.numpy())
    truth = np.concatenate(truth)
    predictions = np.concatenate(predictions)
    top3 = float(np.mean([label in np.argsort(row)[-3:]
                          for row, label in zip(predictions, truth)]))
    output.mkdir(parents=True, exist_ok=True)
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    model_bytes = converter.convert()
    interpreter = tf.lite.Interpreter(model_content=model_bytes)
    interpreter.allocate_tensors()
    input_info = interpreter.get_input_details()[0]
    output_info = interpreter.get_output_details()[0]
    if input_info["dtype"] != np.float32:
        raise ValueError("Android expects float32 input")
    interpreter.set_tensor(input_info["index"], np.zeros((1, 224, 224, 3), np.float32))
    interpreter.invoke()
    scores = interpreter.get_tensor(output_info["index"])[0]
    if not np.isfinite(scores).all() or abs(float(scores.sum()) - 1.0) > .02:
        raise ValueError("Converted model output invalid")
    (output / "species.tflite").write_bytes(model_bytes)
    (output / "species-labels.json").write_text(json.dumps(names, indent=2))
    (output / "species-metrics.json").write_text(json.dumps({
        "classes": len(names), "validation_images": len(truth),
        "val_accuracy": float(accuracy), "val_top3_accuracy": top3,
        "val_loss": float(loss), "counts": json.loads((data / "counts.json").read_text()),
        "note": "GBIF observation held-out split. External real-phone evaluation pending."
    }, indent=2))
    (output / "attribution.json").write_bytes((data / "attribution.json").read_bytes())
    print("RESULT", json.dumps({"classes": len(names), "val_accuracy": float(accuracy),
                                "val_top3_accuracy": top3}), flush=True)

if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
