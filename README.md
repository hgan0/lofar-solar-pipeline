# :file_cabinet: LOFAR Solar Pipeline

An automated, containerized data reduction and directional-dependent calibration pipeline optimized for high-cadence solar imaging using LOFAR interferometry. This repository bundles state-of-the-art radio astronomy engines (`Casacore`, `DP3`, `WSClean`, `AOFlagger`) into an isolated runtime ecosystem optimized for deployment on multi-user HPC cluster environments.

---

## :file_folder: Repository Architecture

```text
lofar-solar-pipeline/
├── .github/workflows/
│   └── docs.yml                 # Automated Git Pages publisher
├── lofar_solar_pipeline/        # Main Python Package Directory
│   ├── __init__.py              # Exposes internal package imports
│   ├── cli.py                   # Central Command Line Interface (CLI)
│   ├── core/                    # The Calibration Pipeline Modules
│   │   ├── __init__.py
│   │   ├── step0_preprocess.py  # Data flagging, RFI cleaning, and data selection
│   │   ├── step1_calibrator.py  # Cross-calibration gain calculations using calibrator sources
│   │   ├── step2_model_sun.py   # Appending sky-model catalogs and setting solar profiles
│   │   ├── step3_selfcal.py     # Direction-independent and direction-dependent self-calibration
│   │   ├── step4_apply.py       # Applying derived solutions to target visibility matrices
│   │   └── step5_imaging.py     # High-resolution synthesis imaging with WSClean
│   └── utils/                   # Analysis & Diagnostics Modules
│       ├── __init__.py
│       ├── ephemeris.py         # Custom Astropy patch-coordinate ephemeris calculations
│       └── diagnostics.py       # Quality metrics tracking (SNR, elevations, uv-coverage)
├── notebooks/                   # Interactive Development Workspace
│   ├── summary_plots.ipynb
│   └── interactive_pipeline.ipynb # Granular notebook workflow panel
├── docs/                        # Structural markdown tracking for documentation site
│   ├── index.md
│   └── usage.md
├── Dockerfile                   # Unified, professional multi-stage environment build
├── docker-compose.yml           # Cluster storage volume mapper & runtime controller
├── mkdocs.yml                   # Git Page UI layout configuration settings
├── requirements.txt             # Virtual environment Python package dependencies (astropy, sunpy, jupyter etc)
├── setup.py                     # Package construction and execution script
└── README.md                    # Landing documentation guide
```

## :gear: Core Pipeline Steps Explained

The pipeline breaks down long radio interferometry processing scripts into modular, step-by-step executions:

### `step0_preprocess.py`
* **Purpose:** Initial data filtering and RFI mitigation.
* **Key Actions:** Invokes `AOFlagger` to eliminate radio frequency interference from terrestrial signals. Automatically windows specific frequency channel sections or time arrays to isolate optimal visibility structures.

### `step1_calibrator.py`
* **Purpose:** Establishes cross-calibration solutions.
* **Key Actions:** Opens a known calibrator dataset (e.g., CasA, CygA), reads complex voltage correlation states, and writes direction-independent electronic complex gain solutions to sub-table matrices using `DP3`.

### `step2_model_sun.py`
* **Purpose:** Defines target solar structural parameters.
* **Key Actions:** Couples standard solar ephemerides with specific position vectors. Maps custom point-source models or Gaussian components into a clean reference sky-model configuration format recognized by `DP3`.

### `step3_selfcal.py`
* **Purpose:** Phase and amplitude calibration adjustments.
* **Key Actions:** Iteratively builds direction-dependent self-calibration adjustments. Corrects phase distortions introduced by volatile Earth ionosphere fluctuations above individual LOFAR array stations.

### `step4_apply.py`
* **Purpose:** Applies full solutions to raw targets.
* **Key Actions:** Merges prior cross-calibration and solar self-calibration gain tables, directly altering the data columns within your target MeasurementSet (`.MS`) file.

### `step5_imaging.py`
* **Purpose:** Synthesis Imaging.
* **Key Actions:** Feeds the fully corrected visibility data rows into `WSClean`. Uses Fast Fourier Transforms (FFT) and customized cleaning loops to generate spatial radio maps saved as `.fits` arrays.

---

## :dart: Quick Start & Installation

Because compiling radio astronomy libraries natively takes hours and often fails due to complex underlying OS library versions, this entire suite runs inside a **Docker Container** configured specifically to preserve user storage permissions on shared cluster drives (like `Zernike`).

### 1. Configure System Environment Identifiers
To prevent files created by the container from being locked under `root` ownership, export your user ID parameters to your active bash session:
```bash
export LOCAL_UID=$(id -u)
export LOCAL_GID=$(id -g)
```

### 2. Launch the Development Workspace
Spin up the analysis container stack in detached background mode:
docker-compose up -d analysis
```bash
docker-compose up -d analysis
```

To verify that the workspace is active, check its runtime status:
```bash
docker-compose ps
```

### 3. Accessing Jupyter Lab
The orchestration script routes internal container parameters safely to local port `9999`.

* Open your browser and navigate to: `http://localhost:9999`
* If working on a remote cluster via SSH, map the port to your home machine by running this command in a new terminal window:
```bash
ssh -N -f -L 9999:localhost:9999 hgan@zernike.astro.rug.nl
```

### :notebook: Interactive Notebook Processing Workflow
To manipulate datasets, tweak parameters, and selectively activate or deactivate pipeline layers on the fly without using the terminal, create a notebook inside Jupyter Lab and implement this modular execution block:

```Python
import os
import subprocess
from astropy.io import fits
import matplotlib.pyplot as plt

# 1. Flexible Data Directory Mapping
DATA_BASE_DIR = "/net/zernike/scratch3/hgan/data/raw_data"
OBS_DATE      = "2023_09_21"
MS_NAME       = "L2025887_SAP001_SB119_uv.MS"

full_ms_path = os.path.join(DATA_BASE_DIR, OBS_DATE, MS_NAME)

# 2. Pipeline Execution Toggles (Switch On/Off)
RUN_SUMMARY = True
RUN_IMAGER  = False  # Toggle iteratively without resetting previous steps!

# 3. Running Modules via Compiled Container Binary Bindings
if RUN_SUMMARY:
    print(f"=== Invoking DP3 Metadata Analysis ===")
    cmd = ["DP3", f"msin={full_ms_path}", "msout=.", "steps=[]"]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    print(result.stdout)
```

### :triangular_flag_on_post: Clean Shutdown
To free up cluster memory resources and cleanly shut down background communication lanes:
```bash
docker-compose down
```
All code modifications, notebook tracking graphs, and calculated .fits matrices are safely saved to your persistent cluster drive layout.


## :red_circle: Issue Diagnoses & Containment Solutions

### 1. Problem Statement
When launching the container stack on the shared cluster path using `docker-compose up -d analysis`, the service terminated instantly. Running `docker-compose exec -it analysis /bin/bash` returned the fatal error: `service "analysis" is not running`.

### 2. Verification & Logs Inspection
Reviewing the internal framework execution status using `docker-compose logs analysis` exposed two critical architectural failure vectors:
1. **`ValueError: '0.0.0.0--port=8888' does not appear to be an IPv4 or IPv6 address`**
   The arguments within the string invocation format had accidentally combined, corrupting the initialization network hook.
2. **`PermissionError: [Errno 13] Permission denied: '/.local'`**
   Because the cluster container runs under an explicit non-root user mapping (`LOCAL_UID:LOCAL_GID`), Jupyter attempted to save tracking configurations inside its default system directory, where write actions are restricted.

### 3. Universal Structural Repair
To fix this, the structural execution path was converted to an array configuration layout, and Jupyter's runtime environments were explicitly redirected to the globally writable temporary cluster directory (`/tmp`).

---

## :large_blue_circle: Definitive `docker-compose.yml` Configuration

Update your `lofar-solar-pipeline/docker-compose.yml` configuration completely to match this layout:

```yaml
services:
  pipeline:
    build: .
    image: lofarsolar-suite:latest
    volumes:
      - /net/zernike/scratch3/hgan:/net/zernike/scratch3/hgan
      - .:/app
    environment:
      - ASTROPY_CACHE_DIR=/tmp/astropy_cache
    user: "${LOCAL_UID}:${LOCAL_GID}"
    network_mode: host

  analysis:
    build: .
    image: lofarsolar-suite:latest
    volumes:
      - /net/zernike/scratch3/hgan:/net/zernike/scratch3/hgan
      - .:/app
    ports:
      - "9999:8888"
    environment:
      - ASTROPY_CACHE_DIR=/tmp/astropy_cache
      # Safely forces Jupyter metadata creation out of root paths and into /tmp
      - HOME=/tmp
      - JUPYTER_RUNTIME_DIR=/tmp/jupyter_runtime
      - JUPYTER_DATA_DIR=/tmp/jupyter_data
    user: "${LOCAL_UID}:${LOCAL_GID}"
    command:
      - "/lofar_env/bin/jupyter"
      - "lab"
      - "--ip=0.0.0.0"
      - "--port=8888"
      - "--no-browser"
      - "--allow-root"
      - "--NotebookApp.token="
      - "--NotebookApp.password="
```
