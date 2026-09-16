"""Experimental species model; requires licensed data and independent validation."""
import json
import sys
from pathlib import Path
from validate_dataset import validate


def main(data: Path, output: Path):
    labels, counts = validate(data)
    import tensorflow as tf
    tf.random.set_seed(42)
    size = (224, 224)
    train = tf.keras.utils.image_dataset_from_directory(data / 'train', image_size=size, batch_size=32, shuffle=True, seed=42)
    val = tf.keras.utils.image_dataset_from_directory(data / 'val', image_size=size, batch_size=32, shuffle=False)
    names = train.class_names
    if names != val.class_names or set(names) != labels:
        raise ValueError('Training and validation classes do not match')
    base = tf.keras.applications.MobileNetV2(input_shape=(224, 224, 3), include_top=False, weights='imagenet')
    base.trainable = False
    inputs = tf.keras.Input(shape=(224, 224, 3))
    x = tf.keras.layers.Rescaling(1. / 127.5, offset=-1)(inputs)
    x = base(x, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    outputs = tf.keras.layers.Dense(len(names), activation='softmax')(x)
    model = tf.keras.Model(inputs, outputs)
    model.compile(optimizer=tf.keras.optimizers.Adam(1e-3), loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    model.fit(train, validation_data=val, epochs=12, callbacks=[tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=3, restore_best_weights=True)])
    loss, accuracy = model.evaluate(val, verbose=0)
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    output.mkdir(parents=True, exist_ok=True)
    (output / 'model.tflite').write_bytes(converter.convert())
    (output / 'labels.json').write_text(json.dumps(names, ensure_ascii=False, indent=2))
    (output / 'metrics.json').write_text(json.dumps({'val_accuracy': float(accuracy), 'val_loss': float(loss), 'counts': {f'{a}/{b}': n for (a,b),n in counts.items()}}, indent=2))


if __name__ == '__main__':
    main(Path(sys.argv[1]), Path(sys.argv[2]))
