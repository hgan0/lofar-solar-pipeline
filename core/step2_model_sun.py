import os
import subprocess
import logging
from lofarsolar_pipeline.utils import ephemeris

def run_step2(obsvID, SB_Sun, SB_Calibrator, calibrator_name, model_schema, dir_name):
    """
    Calculates absolute positional offsets for solar disk tracking during high-cadence flare releases.
    """
    logging.info("☀️ Executing Step 2: Preparing Target Solar Source Multi-Patch Grid Component Models")

    working_dir = f"/net/zernike/scratch3/hgan/processed/{obsvID}/{dir_name}"

    # Utilizing our absolute phase center mapping utility block
    sun_ra, sun_dec = ephemeris.get_solar_coordinates_at_epoch(obsvID)
    logging.info(f"Targeting Solar Ephemeris Lock - Center RA: {sun_ra} | Dec: {sun_dec}")

    for sb in SB_Sun:
        ms_target = os.path.join(working_dir, f"{obsvID}_{sb}_trimmed.MS")

        # Injecting model components directly into measurement data columns using updates
        dp3_predict_cmd = [
            "DP3",
            f"msin={ms_target}",
            "steps=[predict]",
            "predict.type=predict",
            "predict.sourcedb=sun_base.sourcedb",
            "predict.usebeam=strw"
        ]
        subprocess.run(dp3_predict_cmd, check=True)

    logging.info("✅ Step 2 Solar source target patch coordinate definitions initialized.")
