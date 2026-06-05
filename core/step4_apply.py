import os
import subprocess
import logging

def run_apply(date_str, obsvID, tstart_full, tstop_full, pointings, SB_Sun, SB_Calibrator, calibrator_name, model_schema, num_rounds, dir_name):
    """
    Applies the solved DDE phase/amplitude matrix corrections to the
    Measurement Set columns.
    """
    logging.info("💾 Executing Step 4: Applying Solution Matrices and Correcting Visibilities")

    working_dir = f"/net/zernike/scratch3/hgan/processed/{obsvID}/{dir_name}"
    final_cycle = num_rounds - 1

    for sb in SB_Sun:
        ms_target = os.path.join(working_dir, f"{obsvID}_{sb}_trimmed.MS")

        apply_cmd = [
            "DP3",
            f"msin={ms_target}",
            "msout=.",
            "steps=[apply_di, apply_dde]",
            "apply_di.type=applycal",
            f"apply_di.parmdb={ms_target}/instrument_di.h5",
            "apply_dde.type=applycal",
            f"apply_dde.parmdb={ms_target}/instrument_dde_cycle_{final_cycle}.h5",
            "apply_dde.direction=Sun"
        ]
        subprocess.run(apply_cmd, check=True)

    logging.info("✅ Step 4 visibility correction corrections applied to DATA column formats.")
