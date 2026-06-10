import os
import subprocess

def run_step3(obsvID, SB_Sun, SB_Calibrator, model, calibrator, processed_base, num_rounds=3, timewindow1="600", threshold1="1.", dir_name="calibrated"):
    """Orchestrates iterative phase-only self-calibration cycles directly over the target Sun."""
    data_dir = os.path.join(processed_base, obsvID, dir_name, "")
    save_dir = os.path.join(processed_base, obsvID, dir_name, model, "")

    if num_rounds <= 0:
        return

    # Define standard clean imaging settings used to generate the next iteration models
    wsclean_clean_base = (
        "wsclean -j 40 -mem 100 -size 1500 1500 -scale 10asec -pol I -weight briggs 0.0 "
        "-minuvw-m 0 -maxuvw-m 12000 -local-rms -local-rms-window 150 -auto-mask 3.0 "
        "-auto-threshold 1.0 -multiscale -multiscale-scales 0,10,30,90,150,300 "
        "-multiscale-scale-bias 0.6 -niter 100000 -nmiter 100 -mgain 0.75 -save-source-list "
        "-weighting-rank-filter 3 -data-column CORRECTED_DATA"
        )

    for n_round in range(num_rounds):
        for i in range(len(SB_Sun)):
            save_dir_SB = os.path.join(save_dir, SB_Sun[i], "")
            save_dir_SB_img = os.path.join(save_dir_SB, "images", "")
            log_dir = os.path.join(save_dir_SB, "logs", "")

            os.makedirs(save_dir_SB_img, exist_ok=True)
            os.makedirs(log_dir, exist_ok=True)

            # Identify source active cycle file vs target output cycle file
            ms_src = f"{save_dir_SB}Sun_{SB_Sun[i]}_Cycle{n_round}_avg.MS" if n_round > 0 else f"{save_dir_SB}Sun_{SB_Sun[i]}_Cycle0_avg.MS"
            ms_dest = f"{save_dir_SB}Sun_{SB_Sun[i]}_Cycle{n_round+1}_avg.MS"

            os.system(f"rm -rf {ms_dest}")
            os.system(f"cp -r {ms_src} {ms_dest}")


            # ------------------------------------------------------------------
            # NEW: CRITICAL PRE-PREDICT IMAGING FOR ADVANCED ROUNDS
            # If we are on Cycle 2+, we must clean the data from the previous
            # cycle to generate the required image-model file first!
            # ------------------------------------------------------------------
            if n_round > 0:
                prev_img_prefix = os.path.join(save_dir_SB_img, f"Sun_Cycle{n_round}")
                cmd_make_model = f"{wsclean_clean_base} -name {prev_img_prefix} {ms_dest}"
                with open(os.path.join(log_dir, f"step3_cycle{n_round+1}_pre_predict_clean.log"), "w") as logf:
                    subprocess.run(cmd_make_model.split(), stdout=logf, stderr=subprocess.STDOUT)

            # ------------------------------------------------------------------
            # 1. Component sky-prediction mapping phase
            # Now the file is guaranteed to exist!
            # ------------------------------------------------------------------
            img_prefix = f"{save_dir_SB}images/Sun_Cycle{n_round}" if n_round > 0 else f"{save_dir_SB}models/sun_model"
            cmd_predict = f"wsclean -predict -j 40 -mem 100 -name {img_prefix} {ms_dest}"
            with open(os.path.join(log_dir, f"step3_cycle{n_round+1}_wsclean_predict.log"), "w") as logf:
                            subprocess.run(cmd_predict.split(), stdout=logf, stderr=subprocess.STDOUT)

            # 2. Execute phase-only parameter calculation checks
            if model == "CasA":
                cmd_solve = (f"DP3 msin={ms_dest} msout=. msout.datacolumn=CORRECTED_DATA steps=[cal] "
                             f"cal.type=gaincal cal.caltype=phaseonly cal.parmdb={save_dir_SB}Sun_{SB_Sun[i]}_Cycle{n_round+1}_avg.h5 "
                             f"cal.solint=0 cal.usemodelcolumn=true cal.caltype=diagonalphase cal.propagatesolutions=False "
                             f"cal.blrange=[500,12000] cal.solint=0 cal.usebeammodel=False")
                with open(os.path.join(log_dir, f"step3_cycle{n_round+1}_gaincal_solve.log"), "w") as logf:
                                    subprocess.run(cmd_solve, stdout=logf, stderr=subprocess.STDOUT, shell=True)

                cmd_apply = (f"DP3 msin={ms_dest} msin.datacolumn=CORRECTED_DATA msout={ms_dest} msout.datacolumn=CORRECTED_DATA steps=[apply1,apply2] "
                             f"apply1.type=applycal apply1.parmdb={save_dir_SB}{calibrator}_{SB_Calibrator[i]}_Cycle0_avg.h5 apply1.correction=amplitude000 "
                             f"apply2.type=applycal apply2.parmdb={save_dir_SB}Sun_{SB_Sun[i]}_Cycle{n_round+1}_avg.h5 apply2.correction=phase000")
                with open(os.path.join(log_dir, f"step3_cycle{n_round+1}_gaincal_apply.log"), "w") as logf:
                                    subprocess.run(cmd_apply, stdout=logf, stderr=subprocess.STDOUT, shell=True)

            elif model == "CasA+Sun":
                cmd_solve = (f"DP3 msin={ms_dest} msout=. msout.datacolumn=CORRECTED_DATA steps=[cal] "
                             f"cal.type=ddecal cal.mode=phaseonly cal.h5parm={save_dir_SB}Sun_{SB_Sun[i]}_Cycle{n_round+1}_avg_dd.h5 cal.modeldatacolumns=MODEL_DATA "
                             f"cal.directions=[Sun,CasA] cal.solint=0 cal.uvmmin=500 cal.uvmmax=12000 cal.usebeammodel=false")
                with open(os.path.join(log_dir, f"step3_cycle{n_round+1}_ddecal_solve.log"), "w") as logf:
                                    subprocess.run(cmd_solve, stdout=logf, stderr=subprocess.STDOUT, shell=True)

                cmd_apply = (f"DP3 msin={ms_dest} msin.datacolumn=CORRECTED_DATA msout={ms_dest} msout.datacolumn=CORRECTED_DATA steps=[apply1,apply2] "
                             f"apply1.type=applycal apply1.direction=[CasA] apply1.parmdb={save_dir_SB}{calibrator}_{SB_Calibrator[i]}_Cycle0_avg_dd.h5 "
                             f"apply1.steps=[amp] apply1.amp.correction=amplitude000 "
                             f"apply2.type=applycal apply2.direction=[Sun] apply2.parmdb={save_dir_SB}Sun_{SB_Sun[i]}_Cycle{n_round+1}_avg_dd.h5 "
                             f"apply2.steps=[phase] apply2.phase.correction=phase000")
                with open(os.path.join(log_dir, f"step3_cycle{n_round+1}_ddecal_apply.log"), "w") as logf:
                                    subprocess.run(cmd_apply, stdout=logf, stderr=subprocess.STDOUT, shell=True)

            # Post-iteration matrix cleanup
            cmd_flag = (f"DP3 msin={ms_dest} msin.datacolumn=CORRECTED_DATA msout={ms_dest} msout.datacolumn=CORRECTED_DATA steps=[flag] flag.type=madflagger "
                        f"flag.threshold={threshold1} flag.timewindow={timewindow1} flag.correlations=[0,3,1,2]")
            with open(os.path.join(log_dir, f"step3_cycle{n_round+1}_post_flag.log"), "w") as logf:
                            subprocess.run(cmd_flag, stdout=logf, stderr=subprocess.STDOUT, shell=True)
