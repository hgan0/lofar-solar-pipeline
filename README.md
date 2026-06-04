lofar-solar-pipeline/
│
├── .github/workflows/
│   └── docs.yml                 # Automated Git Pages publisher
│
├── lofar_solar_pipeline/        # Main Python Package Directory
│   ├── __init__.py              # Exposes internal package imports
│   ├── cli.py                   # Central Command Line Interface (CLI)
│   │
│   ├── core/                    # The Calibration Pipeline Modules
│   │   ├── __init__.py
│   │   ├── step0_preprocess.py  # Converted from t_dep_step0_all.py
│   │   ├── step1_calibrator.py  # Converted from t_dep_step1_all.py
│   │   ├── step2_model_sun.py   # Converted from t_dep_step2_all.py
│   │   ├── step3_selfcal.py     # Converted from t_dep_step3_all.py
│   │   ├── step4_apply.py       # Converted from t_dep_step4_all.py
│   │   └── step5_imaging.py     # Converted from t_dep_imaging_all.py
│   │
│   └── utils/                   # Analysis & Diagnostics Modules
│       ├── __init__.py
│       ├── ephemeris.py         # Our Astropy patch-coordinate fix script
│       └── diagnostics.py       # Merged logic from get_SNR, elevation, etc.
│
├── notebooks/                   # Sandbox for working with notebooks
│   ├── summary_plots.ipynb
│   └── test_diagnostics.ipynb
│
├── docs/                        # Markdown files for your documentation page
│   ├── index.md
│   └── usage.md
│
├── Dockerfile                   # Unified, professional environment build
├── docker-compose.yml           # Cluster storage mounter & runtime switch
├── mkdocs.yml                   # Git Page UI Layout settings
├── requirements.txt             # Python dependencies (astropy, sunpy, jupyter)
├── setup.py                     # Package construction script
└── README.md                    # Landing page documentation
