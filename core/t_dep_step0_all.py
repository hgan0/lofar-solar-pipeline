import os
import subprocess

def run_step0(obs_date, tstart, tstop, obsvID, obsvID2, pointings, SB_Sun, SB_Calibrator, calibrator,
              dir_name, raw_data_base, processed_base, model_dir_base):
    """
    Slices raw subband MeasurementSets into clean validation time-windows
    when the Sun is quiet to isolate baseline instrumental response states.
    """
    # Use f-strings to stitch paths cleanly instead of hardcoding server tracks
    data_dir = os.path.join(raw_data_base, obs_date, "")
    save_dir = os.path.join(processed_base, obsvID, dir_name, "")

    for i in range(len(SB_Calibrator)):
        save_dir_SB = os.path.join(save_dir, SB_Sun[i], "")
        log_dir = os.path.join(save_dir_SB, "logs")
        os.makedirs(log_dir, exist_ok=True)
        os.makedirs(save_dir_SB, exist_ok=True)

        # 1. Slice out the calibrator data block
        cal_ms_in = f"{data_dir}{obsvID}_SAP001_{SB_Calibrator[i]}_uv.MS"
        cal_ms_out = f"{save_dir_SB}{calibrator}_{SB_Calibrator[i]}_Cycle0_raw.MS"

        os.system(f"rm -rf {cal_ms_out}")
        cmd_cal = f"DP3 msin={cal_ms_in} msin.starttime={tstart} msin.endtime={tstop} msout={cal_ms_out} steps=[]"
        with open(os.path.join(log_dir, "step0_cut_calibrator.log"), "w") as logf:
                    subprocess.run(cmd_cal, stdout=logf, stderr=subprocess.STDOUT, shell=True)

        # 2. Slice out the matching quiet solar data block
        sun_ms_in = f"{data_dir}{obsvID2}_SAP000_{SB_Sun[i]}_uv.MS"
        sun_ms_out = f"{save_dir_SB}Sun_{SB_Sun[i]}_Cycle0_raw.MS"

        os.system(f"rm -rf {sun_ms_out}")
        cmd_sun = f"DP3 msin={sun_ms_in} msin.starttime={tstart} msin.endtime={tstop} msout={sun_ms_out} steps=[]"
        with open(os.path.join(log_dir, "step0_cut_sun.log"), "w") as logf:
                    subprocess.run(cmd_sun, stdout=logf, stderr=subprocess.STDOUT, shell=True)
