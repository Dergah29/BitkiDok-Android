# BitkiDok image model pipeline

This is a training scaffold, NOT an image recognition model. No weights or copyrighted images are included. The app's manual guide continues to work without this model.

## Dataset layout

Place separately licensed photos in `ml/data/train/<label>/` and `ml/data/val/<label>/`; put a `ml/data/manifest.csv` with columns `path,label,license,source,creator`. `path` must be relative to `ml/data/`, and every listed file must have all fields. Only use photos for which reuse and model training are permitted. Check each source's license separately, especially if publishing a paid app. Do not add the dataset to GitHub.

Classes should start with the eight species listed in `public/offline.js`, plus examples of unknown/other plants. Capture different phones, lighting, backgrounds, ages and leaf angles. Keep all photos of the same individual plant in one split, never both train and validation. Validate on real user photos not used in training. A high validation score on staged photos does not establish real-world accuracy.

`python validate_dataset.py ml/data` checks paths, required metadata and split overlap. `python train.py ml/data ml/output` needs TensorFlow and Pillow installed (`pip install -r requirements.txt`), trains MobileNetV2 transfer learning and exports `model.tflite`, `labels.json`, and `metrics.json`. Do not ship those files until validated on real photos; for plant health use a separately labeled, species-aware dataset and uncertainty thresholds. This script intentionally does not prescribe treatments or run the camera.

Candidate datasets for further license and coverage review: [Pl@ntNet-300K](https://github.com/plantnet/PlantNet-300K) (individual images have license metadata), [iNaturalist 2021](https://github.com/visipedia/inat_comp/tree/master/2021) (per-image rights fields). [PlantVillage](https://github.com/spMohanty/PlantVillage-Dataset) focuses on crops, so it is not evidence for diagnosis on ornamental houseplants.
