import os
import numpy as np
import subprocess
from casacore.tables import table

def get_ms_central_frequency(ms_path):
    """Retrieves the mean physical tracking frequency of the subband."""
    sw_path = os.path.join(ms_path, "SPECTRAL_WINDOW")
    with table(sw_path, ack=False) as sw:
        chan_freqs = sw.getcol("CHAN_FREQ")[0]
    return np.mean(chan_freqs)

def run_step1(obsvID, SB_Sun, SB_Calibrator, calibrator,
              model, solint, processed_base, model_dir_base,
              timewindow1="600", threshold1="1.",
              dir_name="calibrated", ):
    """
    Cleans RFI and calculates full complex gains. If model='CasA' -> gaincal (DI).
    If model='CasA+Sun' -> ddecal (DD) tracking multi-directional patches.
    """
    data_dir = f"/net/zernike/scratch3/hgan/processed/{obsvID}/{dir_name}/"
    save_dir = f"/net/zernike/scratch3/hgan/processed/{obsvID}/{dir_name}/{model}/"
    model_dir = "/net/zernike/scratch3/hgan/data/model/"

    for i in range(len(SB_Calibrator)):
        data_dir_SB = os.path.join(data_dir, SB_Sun[i], "")
        save_dir_SB = os.path.join(save_dir, SB_Sun[i], "")
        model_dir_SB = f"/net/zernike/scratch3/hgan/processed/{obsvID}/{dir_name}/CasA/{SB_Sun[i]}/"
        log_dir = os.path.join(save_dir_SB, "logs")
        os.makedirs(save_dir_SB, exist_ok=True)
        os.makedirs(os.path.join(save_dir_SB, "images"), exist_ok=True)
        os.makedirs(log_dir, exist_ok=True)

        ms_raw = f"{data_dir_SB}{calibrator}_{SB_Calibrator[i]}_Cycle0_raw.MS"
        ms_avg = f"{save_dir_SB}{calibrator}_{SB_Calibrator[i]}_Cycle0_avg.MS"
        os.system(f"rm -rf {ms_avg}")

        # RFI Flagging and averaging down to 1 channel per subband
        cmd_prep = (f"DP3 msin={ms_raw} msout={ms_avg} "
                    f"steps=[flag] flag.type=madflagger flag.threshold={threshold1} "
                    f"flag.timewindow={timewindow1} flag.correlations=[0,3,1,2]")
        with open(os.path.join(log_dir, "step1_rfi_flag_avg.log"), "w") as logf:
                    subprocess.run(cmd_prep, stdout=logf, stderr=subprocess.STDOUT, shell=True)

        # Dynamic Calibration Solver Routing
        if model == "CasA":
            # Direction-Independent Calibration Branch
            cmd_solve = (f"DP3 msin={ms_avg} msout=. steps=[cal] "
                         f"cal.type=gaincal cal.caltype=diagonal cal.parmdb={save_dir_SB}{calibrator}_{SB_Calibrator[i]}_Cycle0_avg.h5 "
                         f"cal.sourcedb={model_dir_SB}models/CasA.sourcedb cal.solint={solint} cal.usebeammodel=false cal.blrange=[500,12000]")
            with open(os.path.join(log_dir, "step1_gaincal_solve.log"), "w") as logf:
                            subprocess.run(cmd_solve, stdout=logf, stderr=subprocess.STDOUT, shell=True)

            cmd_apply = (f"DP3 msin={ms_avg} msout={ms_avg} msout.datacolumn=CORRECTED_DATA steps=[apply] "
                         f"apply.type=applycal apply.parmdb={save_dir_SB}{calibrator}_{SB_Calibrator[i]}_Cycle0_avg.h5 "
                         f"apply.steps=[amp,phase] apply.amp.correction=amplitude000 apply.phase.correction=phase000")
            with open(os.path.join(log_dir, "step1_gaincal_apply.log"), "w") as logf:
                            subprocess.run(cmd_apply, stdout=logf, stderr=subprocess.STDOUT, shell=True)

        elif model == "CasA+Sun":
            # Direction-Dependent Calibration Branch
            cmd_solve = (f"DP3 msin={ms_avg} msout=. steps=[cal] "
                         f"cal.type=ddecal cal.mode=diagonal cal.h5parm={save_dir_SB}{calibrator}_{SB_Calibrator[i]}_Cycle0_avg_dd.h5 "
                         f"cal.sourcedb={model_dir_SB}models/sun+CasA.sourcedb cal.directions=[Sun,CasA] cal.solint={solint} cal.usebeammodel=false "
                         f"cal.uvmmin=500 cal.uvmmax=12000")
            with open(os.path.join(log_dir, "step1_ddecal_solve.log"), "w") as logf:
                            subprocess.run(cmd_solve, stdout=logf, stderr=subprocess.STDOUT, shell=True)

            cmd_apply = (f"DP3 msin={ms_avg} msout={ms_avg} msout.datacolumn=CORRECTED_DATA steps=[apply] "
                         f"apply.type=applycal apply.parmdb={save_dir_SB}{calibrator}_{SB_Calibrator[i]}_Cycle0_avg_dd.h5 "
                         f"apply.direction=[CasA] apply.steps=[amp,phase] apply.amp.correction=amplitude000 apply.phase.correction=phase000")
                         # Note: You can customize if you want to skip applying the Sun direction matrix here
            with open(os.path.join(log_dir, "step1_ddecal_apply.log"), "w") as logf:
                            subprocess.run(cmd_apply, stdout=logf, stderr=subprocess.STDOUT, shell=True)

        # Clean-up Post Flagging and Verification Synthesis Imaging
        cmd_post_flag = (f"DP3 msin={ms_avg} msin.datacolumn=CORRECTED_DATA msout={ms_avg} msout.datacolumn=CORRECTED_DATA steps=[flag] flag.type=madflagger "
                         f"flag.threshold={threshold1} flag.timewindow={timewindow1} flag.correlations=[0,3,1,2]")
        with open(os.path.join(log_dir, "step1_post_flg.log"), "w") as logf:
                        subprocess.run(cmd_post_flag, stdout=logf, stderr=subprocess.STDOUT, shell=True)

        cmd_img = (f"wsclean -j 40 -mem 100 -auto-mask 5 -auto-threshold 0.5 -fit-beam -apply-primary-beam -size 600 600 -scale 20asec "
                   f"-multiscale-scales 0,10,30,90,150 -mgain 0.05 -weight briggs 0 "
                   f"-pol I -niter 100000 -nmiter 100  -data-column CORRECTED_DATA -name {save_dir_SB}images/calibrator_check {ms_avg}")
        with open(os.path.join(log_dir, "step1_verification_wsclean.log"), "w") as logf:
                    subprocess.run(cmd_img.split(), stdout=logf, stderr=subprocess.STDOUT)
