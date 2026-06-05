import os
import subprocess
import logging

def run_step3(obsvID, SB_Sun, SB_Calibrator, model_schema, calibrator_name, num_rounds, dir_name):
    """
    Iterates dynamically across multi-directional phase solution patches to
    unwind corruptions caused by ionospheric turbulence.
    """
    logging.info(f"🔄 Executing Step 3: Multi-Directional Self-Calibration Matrix Loop ({num_rounds} Rounds)")

    working_dir = f"/net/zernike/scratch3/hgan/processed/{obsvID}/{dir_name}"

    for cycle in range(num_rounds):
        logging.info(f"--- Running Self-Calibration Optimization Cycle Loop: {cycle+1}/{num_rounds} ---")

        for sb in SB_Sun:
            ms_target = os.path.join(working_dir, f"{obsvID}_{sb}_trimmed.MS")

            # Complex multi-directional solver parameters call
            dde_cmd = [
                "DP3",
                f"msin={ms_target}",
                "steps=[dde_solve]",
                "dde_solve.type=ddecal",
                "dde_solve.mode=complex",
                "dde_solve.directions=[[Sun],[CasA]]",
                f"dde_solve.parmdb={ms_target}/instrument_dde_cycle_{cycle}.h5",
                "dde_solve.solint=5"
            ]
            subprocess.run(dde_cmd, check=True)

    logging.info("✅ Step 3 Multi-patch DDE structural self-calibration cycles completed safely.")
