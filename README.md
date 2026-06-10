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
│   │   ├── t_dep_step0_all.py   # Step 0: Base data slicing and time window partitioning
│   │   ├── t_dep_step1_all.py   # Step 1: Solving instrumental gains on calibrator sources
│   │   ├── t_dep_model_all.py   # Model: Clustering sky components & structuring multi-patch source DBs
│   │   ├── t_dep_step2_all.py   # Step 2: Cross-application of solutions to target solar fields
│   │   ├── t_dep_step3_all.py   # Step 3: Iterative phase-only self-cal optimization loops
│   │   ├── t_dep_apply_all.py   # Step 4: Flare window slicing and asymmetric gain matrix blending
│   │   └── t_dep_imaging_all.py # Step 5: Final synthesis review imaging via WSClean
│   └── utils/                   # Analysis & Diagnostics Modules
│       ├── __init__.py
│       ├── ephemeris.py         # Custom Astropy patch-coordinate ephemeris calculations
│       └── diagnostics.py       # Quality metrics tracking (SNR, elevations, uv-coverage)
├── models/                      # Models for calibration
│   ├──CasA.sourcedb
│   └──CasA.txt
├── notebooks/                   # Interactive Development Workspace
│   ├── summary_plots.ipynb
│   └── interactive_pipeline.ipynb # Granular notebook workspace orchestrator
├── docs/                        # Structural markdown tracking for documentation site
│   ├── index.md
│   └── usage.md
├── Dockerfile                   # Unified, professional multi-stage environment build
├── docker-compose.yml           # Cluster storage volume mapper & runtime controller
├── mkdocs.yml                   # Git Page UI layout configuration settings
├── requirements.txt             # Environment Python packages (astropy, joblib, tqdm, etc.)
├── setup.py                     # Package construction and execution script
└── README.md                    # Landing documentation guide
```

## :gear: Core Pipeline Steps Explained
The pipeline breaks down long radio interferometry processing scripts into modular, step-by-step parallel executions using `joblib`:

### `t_dep_step0_all.py`
* **Purpose:** Initial data window selection.
* **Key Actions:** Runs `DP3` to slice short, quiet reference time sections from raw measurement sets (`_uv.MS`) for both the target sun and chosen calibrator.

### `t_dep_step1_all.py`
* **Purpose:** Establishes instrumental cross-calibration.
* **Key Actions:** Resolves direction-independent electronic complex gain solutions on a known calibrator dataset (e.g., `CasA`) and exports foundational baseline gain tables using the `DP3` solver.

### `t_dep_step2_all.py`
* **Purpose:** Cross-applies calibration to target fields.
* **Key Actions:** Cross-applies baseline solutions derived from the calibrator to the target Solar subbands, preparing the initial visibilities for target self-calibration.

### `t_dep_model_all.py`
* **Purpose:** Clusters direction-dependent sky model components.
* **Key Actions:** Dynamically structures multi-patch component layouts. Invokes `makesourcedb` and `cluster` patches to rename targets (e.g., `Sun`, `CasA`) for direction-dependent calibration.

### `t_dep_apply_all.py`
* **Purpose:** Slices solar flare windows and blends gain matrices.
* **Key Actions:** Extracts active solar flare event windows from raw target data, applies instrumental amplitudes alongside high-cadence self-cal phase adjustments, and outputs blended visibility arrays.

### `t_dep_imaging_all.py`
* **Purpose:** Synthesis Imaging.
* **Key Actions:** Feeds fully corrected visibility rows from different cycles into `WSClean` using customized cleaning loops to generate spatial radio maps saved as `.fits` arrays.
---

## :dart: Quick Start & Installation

Because compiling radio astronomy libraries natively takes hours and often fails due to complex underlying OS library versions, this entire suite runs inside a **Docker Container** configured specifically to preserve user storage permissions on shared cluster drives (like Zernike).

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
ssh -N -f -L 9999:localhost:9999 hgan@cluster
```

### :notebook: Interactive Notebook Processing Workflow
To manipulate datasets, tweak parameters, and selectively activate or deactivate pipeline layers on the fly without using the terminal, create a notebook inside Jupyter Lab and implement this modular execution block:

```Python
import sys
from joblib import Parallel, delayed
from tqdm import tqdm

sys.path.append('/app/core')
import t_dep_step0_all, t_dep_step1_all, t_dep_model_all, t_dep_step2_all, t_dep_step3_all, t_dep_apply_all, t_dep_imaging_all

# Workspace Data Mapping
RAW_DATA_BASE  = "/net/zernike/scratch3/hgan/data/raw_data"
PROCESSED_BASE = "/net/zernike/scratch3/hgan/processed"

# Run Strategy Configuration
MODEL_SELECTION    = "CasA+Sun"
NUM_SELFCAL_ROUNDS = 2
DIR_NAME_TAG       = "t-dep-selfcal-phase-only-2"

SB_Sun = ['SB009', 'SB029', 'SB049']
date_set = ["21Sep2023"]; obsvID_set = ["L2025887"]; calibrator_set = ["CasA"]

def run_pipeline_with_progress_telemetry():
    num_datasets = len(date_set)

    print(" Starting Step 0: Data Slicing...")
    with tqdm(total=num_datasets, desc="Step 0 Progress") as pbar:
        Parallel(n_jobs=-1)(delayed(t_dep_step0_all.run_step0)(
            date_set[k], "10:00:00", "10:05:00", obsvID_set[k], "L2025886",
            [["Sun", "CasA"]], SB_Sun, SB_Sun, calibrator_set[k],
            dir_name=DIR_NAME_TAG, raw_data_base=RAW_DATA_BASE, processed_base=PROCESSED_BASE, model_dir_base=""
        ) for k in range(num_datasets))
        pbar.update(num_datasets)

    # Additional execution blocks run sequentially with tracking...
    print("\n Pipeline loop cluster block successfully concluded.")

run_pipeline_with_progress_telemetry()
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
