"""Train a separate experimental houseplant species model from GBIF photos."""
import json
import sys
from pathlib import Path
import tensorflow as tf

def main(data, output):
    tf.random.set_seed(42)
    train = tf.keras.utils.image_dataset_from_directory(data / "train", image_size=(224, 224),
                                                         batch_size=32, shuffle=True, seed=42)
    val = tf.keras.utils.image_dataset_from_directory(data / "val", image_size=(224, 224),
                                                       batch_size=32, shuffle=False)
    names = train.class_names
    if len(names) < 4 or names != val.class_names:
        raise ValueError("Insufficient species or class mismatch")
    base = tf.keras.applications.MobileNetV2(input_shape=(224, 224, 3),
                                               include_top=False, weights="imagenet")
    base.trainable = False
    inputs = tf.keras.Input(shape=(224, 224, 3))
    x = tf.keras.layers.Rescaling(1 / 127.5, offset=-1)(inputs)
    x = base(x, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    outputs = tf.keras.layers.Dense(len(names), activation="softmax")(x)
    model = tf.keras.Model(inputs, outputs)
    model.compile(optimizer=tf.keras.optimizers.Adam(1e-3),
                  loss="sparse_categorical_crossentropy", metrics=["accuracy"])
    model.fit(train, validation_data=val, epochs=10,
              callbacks=[tf.keras.callbacks.EarlyStopping(
                  monitor="val_loss", patience=2, restore_best_weights=True)])
    loss, accuracy = model.evaluate(val, verbose=0)
    output.mkdir(parents=True, exist_ok=True)
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    (output / "species.tflite").write_bytes(converter.convert())
    (output / "species-labels.json").write_text(json.dumps(names, indent=2))
    (output / "species-metrics.json").write_text(json.dumps({
        "val_accuracy": float(accuracy), "val_loss": float(loss),
        "counts": json.loads((data / "counts.json").read_text()),
        "note": "Same-source held-out split; real-world validation pending."
    }, indent=2))
    (output / "attribution.json").write_bytes((data / "attribution.json").read_bytes())

if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
