import os
import sys
from joblib import Parallel, delayed

# Import clean sub-modules safely from repository paths
import t_dep_step0_all
import t_dep_step1_all
import t_dep_step2_all
import t_dep_model_all
import t_dep_step3_all
import t_dep_apply_all
import t_dep_imaging_all

# ==============================================================================
# 🎛️ GLOBAL SCIENTIFIC CONFIGURATION DESK
# ==============================================================================
MODEL_SELECTION = "CasA+Sun"      # Options: "CasA" or "CasA+Sun" (Toggles gaincal vs ddecal)
SOLINT_INTERVAL = 0              # 0 = Time-Independent instrumental gains; >0 = Time-Dependent
NUM_SELFCAL_ROUNDS = 2           # 0 = Skymodel application only; >0 = Phase-Only Self-Cal loops
DIR_NAME_TAG = "calibrated"

# Telescope Target Fields Metadata Layout arrays
SB_Sun = ['SB009', 'SB029', 'SB049']
SB_Calibrator = ['SB009', 'SB029', 'SB049']

date_set = ["21Sep2023"]
obsvID_set = ["L2025887"]
obsvID2_set = ["L2025886"]
calibrator_set = ["CasA"]
pointings_set = [["Sun", "CasA"]]

# Validation Time Coordinates (Quiet Sun Profiles)
tstart_set = ["10:00:00"]
tstop_set = ["10:05:00"]

# Active Target Time Coordinates (Solar Flare Tracking events)
flare_tstart_set = ["12:48:00"]
flare_tstop_set = ["12:55:00"]
# ==============================================================================

def execute_full_pipeline():
    print(f"🚀 INITIALIZING LOFAR SOLAR PIPELINE SYSTEM SUITE")
    print(f"Configuration: Mode={MODEL_SELECTION} | SolInt={SOLINT_INTERVAL} | SelfCal Rounds={NUM_SELFCAL_ROUNDS}\n")

    num_datasets = len(date_set)

    # --------------------------------------------------------------------------
    # STEP 0: Slicing Baseline Validation Data Windows
    # --------------------------------------------------------------------------
    print("--- Executing Step 0: Data Slicing ---")
    Parallel(n_jobs=-1)(
        delayed(t_dep_step0_all.run_step0)(
            date_set[k], tstart_set[k], tstop_set[k], obsvID_set[k], obsvID2_set[k],
            pointings_set[k], SB_Sun, SB_Calibrator, calibrator_set[k], dir_name=DIR_NAME_TAG
        ) for k in range(num_datasets)
    )

    # --------------------------------------------------------------------------
    # STEP 1: Calibrator Calibration (Solving Instrumental Gains)
    # --------------------------------------------------------------------------
    print("--- Executing Step 1: Calibrator Solutions Solver ---")
    Parallel(n_jobs=-1)(
        delayed(t_dep_step1_all.run_step1)(
            obsvID_set[k], SB_Sun, SB_Calibrator, calibrator_set[k],
            model=MODEL_SELECTION, solint=SOLINT_INTERVAL, dir_name=DIR_NAME_TAG
        ) for k in range(num_datasets)
    )

    # --------------------------------------------------------------------------
    # STEP 1.5: Build Structural Catalog Multi-Patch Databases
    # --------------------------------------------------------------------------
    if MODEL_SELECTION == "CasA+Sun":
        print("--- Executing Sky-Model Formatting Engine ---")
        Parallel(n_jobs=-1)(
            delayed(t_dep_model_all.create_model)(
                obsvID_set[k], SB_Sun, SB_Calibrator, model=MODEL_SELECTION, dir_name=DIR_NAME_TAG
            ) for k in range(num_datasets)
        )

    # --------------------------------------------------------------------------
    # STEP 2: Cross-Applying Baseline Solutions onto Solar Target
    # --------------------------------------------------------------------------
    print("--- Executing Step 2: Cross-Applying and Solar Model Extraction ---")
    Parallel(n_jobs=-1)(
        delayed(t_dep_step2_all.run_step2)(
            obsvID_set[k], SB_Sun, SB_Calibrator, calibrator_set[k],
            model=MODEL_SELECTION, dir_name=DIR_NAME_TAG
        ) for k in range(num_datasets)
    )

    # --------------------------------------------------------------------------
    # STEP 3: Iterative Phase-Only Solar Self-Calibration
    # --------------------------------------------------------------------------
    if NUM_SELFCAL_ROUNDS > 0:
        print(f"--- Executing Step 3: Running {NUM_SELFCAL_ROUNDS} Phase-Only Self-Cal Loops ---")
        Parallel(n_jobs=-1)(
            delayed(t_dep_step3_all.run_step3)(
                obsvID_set[k], SB_Sun, SB_Calibrator, model=MODEL_SELECTION,
                calibrator=calibrator_set[k], num_rounds=NUM_SELFCAL_ROUNDS, dir_name=DIR_NAME_TAG
            ) for k in range(num_datasets)
        )

    # --------------------------------------------------------------------------
    # STEP 4: Flare Extraction and Asymmetric Gain Matrix Blending
    # --------------------------------------------------------------------------
    print("--- Executing Step 4: Flare Application & Gain Blending ---")
    Parallel(n_jobs=-1)(
        delayed(t_dep_apply_all.run_apply)(
            date_set[k], obsvID_set[k], flare_tstart_set[k], flare_tstop_set[k],
            pointings_set[k], SB_Sun, SB_Calibrator, calibrator_set[k],
            model=MODEL_SELECTION, num_rounds=NUM_SELFCAL_ROUNDS, dir_name=DIR_NAME_TAG
        ) for k in range(num_datasets)
    )

    # --------------------------------------------------------------------------
    # STEP 5: Final Evaluation Telemetry Synthesis Imaging
    # --------------------------------------------------------------------------
    print("--- Executing Step 5: Final Synthesis Imaging Outputs ---")
    Parallel(n_jobs=-1)(
        delayed(t_dep_imaging_all.all_imaging)(
            obsvID_set[k], SB_Sun, SB_Calibrator, model=MODEL_SELECTION, dir_name=DIR_NAME_TAG
        ) for k in range(num_datasets)
    )

    print("\n✅ PIPELINE TASK COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    execute_full_pipeline()
