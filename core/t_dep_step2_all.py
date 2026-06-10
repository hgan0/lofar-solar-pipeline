import os
import subprocess

def run_step2(obsvID, SB_Sun, SB_Calibrator, calibrator, model, dir_name, processed_base, timewindow1="600", threshold1="1."):
    """Cross-applies calibration parameters onto target solar fields."""
    data_dir = os.path.join(processed_base, obsvID, dir_name, "")
    save_dir = os.path.join(processed_base, obsvID, dir_name, model, "")

    for i in range(len(SB_Sun)):
        data_dir_SB = os.path.join(data_dir, SB_Sun[i], "")
        save_dir_SB = os.path.join(save_dir, SB_Sun[i], "")
        model_dir_SB = os.path.join(save_dir_SB, "models", "")
        img_dir_SB = os.path.join(save_dir_SB, "images", "")
        log_dir = os.path.join(save_dir_SB, "logs", "")

        ms_raw = f"{data_dir_SB}Sun_{SB_Sun[i]}_Cycle0_raw.MS"
        ms_avg = f"{save_dir_SB}Sun_{SB_Sun[i]}_Cycle0_avg.MS"

        os.system(f"rm -rf {ms_avg}")
        os.makedirs(model_dir_SB, exist_ok=True)
        os.makedirs(img_dir_SB, exist_ok=True)
        os.makedirs(log_dir, exist_ok=True)

        # Flag and average target data rows
        cmd_prep = (f"DP3 msin={ms_raw} msout={ms_avg} "
                    f"steps=[flag] flag.type=madflagger flag.threshold={threshold1} "
                    f"flag.timewindow={timewindow1} flag.correlations=[0,3,1,2]")
        with open(os.path.join(log_dir, "step2_flag_and_average.log"), "w") as logf:
                    subprocess.run(cmd_prep, stdout=logf, stderr=subprocess.STDOUT, shell=True)

        # Apply Cross-Calibration Gains based on Model Architecture Type
        if model == "CasA":
            cmd_apply = (f"DP3 msin={ms_avg} msout={ms_avg} msout.datacolumn=CORRECTED_DATA steps=[apply] "
                         f"apply.type=applycal apply.parmdb={save_dir_SB}{calibrator}_{SB_Calibrator[i]}_Cycle0_avg.h5 "
                         f"apply.steps=[amp,phase] apply.amp.correction=amplitude000 apply.phase.correction=phase000")
            with open(os.path.join(log_dir, "step2_apply_calibrator_gains.log"), "w") as logf:
                            subprocess.run(cmd_apply, stdout=logf, stderr=subprocess.STDOUT, shell=True)


        elif model == "CasA+Sun":
            cmd_apply = (f"DP3 msin={ms_avg} msout={ms_avg} msout.datacolumn=CORRECTED_DATA steps=[apply1,apply2] "
                         f"apply1.type=applycal apply1.direction=[CasA] apply1.parmdb={save_dir_SB}{calibrator}_{SB_Calibrator[i]}_Cycle0_avg_dd.h5 "
                         f"apply1.steps=[amp] apply1.amp.correction=amplitude000 "
                         f"apply2.type=applycal apply2.direction=[Sun] apply2.parmdb={save_dir_SB}{calibrator}_{SB_Calibrator[i]}_Cycle0_avg_dd.h5 "
                         f"apply2.steps=[phase] apply2.phase.correction=phase000")
            with open(os.path.join(log_dir, "step2_apply_calibrator_dd_gains.log"), "w") as logf:
                            subprocess.run(cmd_apply, stdout=logf, stderr=subprocess.STDOUT, shell=True)

        # Quality control flagging post application
        cmd_flag = f"DP3 msin={ms_avg} msin.datacolumn=CORRECTED_DATA msout={ms_avg} msout.datacolumn=CORRECTED_DATA steps=[flag] flag.type=madflagger"
        with open(os.path.join(log_dir, "step2_post_cal_flagging.log"), "w") as logf:
                    subprocess.run(cmd_flag, stdout=logf, stderr=subprocess.STDOUT, shell=True)


        # Generate deep solar model map via specialized cleaning thresholds
        if model == "CasA":
            cmd_model_img = (f"wsclean -j 40 -mem 100 -size 1500 1500 -scale 10asec -pol I -weight briggs 0.0 "
                                f"-auto-mask 3.0 -auto-threshold 1.0 -multiscale -multiscale-scales 0,10,30,90,150,300 "
                                f"-niter 100000 -mgain 0.75 -save-source-list -name {save_dir_SB}models/sun_model {ms_avg}")
            with open(os.path.join(log_dir, "step2_solar_model_wsclean.log"), "w") as logf:
                            subprocess.run(cmd_model_img.split(), stdout=logf, stderr=subprocess.STDOUT)

        # Quality verification imaging
        cmd_img = (f"wsclean -j 40 -mem 100 -auto-mask 5 -auto-threshold 0.5 -fit-beam -apply-primary-beam -size 600 600 -scale 20asec "
                   f"-multiscale-scales 0,10,30,90,150 -mgain 0.05 -weight briggs 0 "
                   f"-pol I -niter 100000 -nmiter 100  -data-column CORRECTED_DATA -name {save_dir_SB}images/calibrator_check {ms_avg}")
        with open(os.path.join(log_dir, "step2_verification_wsclean.log"), "w") as logf:
                    subprocess.run(cmd_img.split(), stdout=logf, stderr=subprocess.STDOUT)
