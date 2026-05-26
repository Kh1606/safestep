# masil — Seoul pedestrian-hazard mapping

**masil (마실)** explores walkability and pedestrian hazards in Seoul by combining
three sources of signal:

1. **OpenStreetMap feature extraction** — pull pedestrian-relevant features (stairs,
   elevators, crossings) out of a Seoul `.osm.pbf` extract into tidy CSVs.
2. **YOLO hazard detection** — a YOLOv11 model trained to detect accessibility
   features in street-level images: `step`, `stair`, `grab_bar`, `ramp`.
3. **Monocular depth estimation** — run MiDaS / ZoeDepth on stair images to estimate
   relative depth (a proxy for step height / steepness).

A small **demo** ties hazards and a route together on a Leaflet map.

> ⚠️ Data, OSM extracts, trained weights and generated maps are **not** included
> (they're large). This repo holds the code + a tiny demo. See "Getting the data".

**Stack:** Python · osmium · folium / Leaflet · Ultralytics (YOLOv11) · PyTorch (MiDaS, ZoeDepth) · OpenCV

---

## Layout

```
extract.py              # OSM .pbf -> features_seoul.csv (stairs / elevators / crossings)
tags.py                 # tally OSM tag key/value frequencies (exploration)
make_map.py             # render extracted features onto a folium map
peek.py                 # quick peek at a .pbf
features*.csv           # small sample of extracted features (output of extract.py)

train_1/                # YOLOv11 accessibility-feature detector
  ├── train.py          #   training entrypoint (4 classes)
  ├── inference.py      #   run predictions with trained weights
  └── data.yaml         #   dataset config / class names

masil_depth/            # monocular depth estimation on stairs
  ├── test_midas.py     #   MiDaS_small via torch.hub
  └── zoe.py            #   ZoeDepth

masil_demo/             # Leaflet demo: route + hazards
  ├── index.html
  ├── hazards.geojson
  ├── route.geojson
  └── kr/               #   scripts to turn Korean open-data CSVs into map geojson
```

## Setup

```bash
pip install -r requirements.txt
```

## Usage

**1. Extract pedestrian features from OSM**

```bash
# put a Seoul extract named Seoul.osm.pbf next to extract.py, then:
python extract.py          # -> features_seoul.csv
python make_map.py         # -> a folium map of the features
```

**2. Train / run the hazard detector** (needs a YOLO dataset under `train_1/`)

```bash
python train_1/train.py        # trains YOLOv11n on step/stair/grab_bar/ramp
python train_1/inference.py    # runs the trained weights on test images
```

**3. Depth estimation on stairs**

```bash
python masil_depth/test_midas.py    # MiDaS_small
python masil_depth/zoe.py           # ZoeDepth
```

**4. Demo** — open `masil_demo/index.html` in a browser to see the route + hazards.

## Getting the data

- **OSM extract:** download a Seoul/South-Korea `.osm.pbf` (e.g. from Geofabrik) and
  place it as `Seoul.osm.pbf`.
- **YOLO dataset:** a labelled image set with the 4 classes above (exported in YOLO
  format), placed under `train_1/images` + `train_1/labels` per `data.yaml`.
- **Depth models** download automatically via `torch.hub` on first run.

## License

MIT — see [LICENSE](LICENSE).
