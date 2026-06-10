import os
import subprocess

def run_apply(obs_date, obsvID, obsvID2, flare_tstart, flare_tstop, pointings, SB_Sun, SB_Calibrator, calibrator, model, raw_data_base, processed_base, num_rounds, dir_name):
    """
    Extracts active solar flare time windows, applies instrumental calibrator amplitude scales
    and fast ionospheric solar phase solutions before executing station beam fixes.
    """
    raw_data_dir = os.path.join(raw_data_base, obs_date, "")
    save_dir = os.path.join(processed_base, obsvID, dir_name, model, "")

    for i in range(len(SB_Sun)):
        save_dir_SB = os.path.join(save_dir, SB_Sun[i], "")
        save_dir_SB_img = os.path.join(save_dir_SB, "images", "")
        log_dir = os.path.join(save_dir_SB, "logs", "")

        os.makedirs(save_dir_SB_img, exist_ok=True)
        os.makedirs(log_dir, exist_ok=True)

        # Fix string addition parsing errors using exact target pointing layouts
        ms_in = os.path.join(raw_data_dir, f"{obsvID2}_SAP000_{SB_Sun[i]}_uv.MS")
        ms_flare = os.path.join(save_dir_SB, f"Sun_flare_{SB_Sun[i]}_Cycle{num_rounds}.MS")

        os.system(f"rm -rf {ms_flare}")

        # 1. Slice out the dynamic flare data block
        cmd_cut = f"DP3 msin={ms_in} msin.starttime={flare_tstart} msin.endtime={flare_tstop} msout={ms_flare} steps=[]"
        with open(os.path.join(log_dir, "step4_flare_time_slice.log"), "w") as logf:
            subprocess.run(cmd_cut, stdout=logf, stderr=subprocess.STDOUT, shell=True)

        # ----------------------------------------------------------------------
        # DYNAMIC CYCLE DETERMINATION LOGIC
        # ----------------------------------------------------------------------
        # Determine whether to use self-cal matrices or step 1 baseline matrices
        if int(num_rounds) > 0:
            phase_h5_name = f"Sun_{SB_Sun[i]}_Cycle{num_rounds}_avg.h5"
            phase_h5_name_dd = f"Sun_{SB_Sun[i]}_Cycle{num_rounds}_avg_dd.h5"
        else:
            # Fallback: Use initial solution matrices if self-cal optimization loops were skipped
            phase_h5_name = f"{calibrator}_{SB_Calibrator[i]}_Cycle0_avg.h5"
            phase_h5_name_dd = f"{calibrator}_{SB_Calibrator[i]}_Cycle0_avg_dd.h5"

        phase_parmdb_path = os.path.join(save_dir_SB, phase_h5_name)
        phase_parmdb_path_dd = os.path.join(save_dir_SB, phase_h5_name_dd)
        amp_parmdb_path = os.path.join(save_dir_SB, f"{calibrator}_{SB_Calibrator[i]}_Cycle0_avg.h5")
        amp_parmdb_path_dd = os.path.join(save_dir_SB, f"{calibrator}_{SB_Calibrator[i]}_Cycle0_avg_dd.h5")
        # ----------------------------------------------------------------------

        # 2. Dynamic Asymmetric Gain Matrix Blending Engine
        if model == "CasA":
            cmd_blend = (f"DP3 msin={ms_flare} msout={ms_flare} msout.datacolumn=CORRECTED_DATA steps=[applycal_amp,applycal_phase,applybeam] "
                         f"applycal_amp.type=applycal applycal_amp.parmdb={amp_parmdb_path} applycal_amp.steps=[amp] applycal_amp.amp.correction=amplitude000 "
                         f"applycal_phase.type=applycal applycal_phase.parmdb={phase_parmdb_path} applycal_phase.steps=[phase] applycal_phase.phase.correction=phase000")
            with open(os.path.join(log_dir, "step4_asymmetric_gains_blending.log"), "w") as logf:
                subprocess.run(cmd_blend, stdout=logf, stderr=subprocess.STDOUT, shell=True)

        elif model == "CasA+Sun":
            if int(num_rounds) > 0:
                cmd_blend = (f"DP3 msin={ms_flare} msout={ms_flare} msout.datacolumn=CORRECTED_DATA steps=[applycal_amp,applycal_phase,applybeam] "
                            f"applycal_amp.type=applycal applycal_amp.direction=[CasA] applycal_amp.parmdb={amp_parmdb_path_dd} applycal_amp.steps=[amp] applycal_amp.amp.correction=amplitude000 "
                            f"applycal_phase.type=applycal applycal_phase.direction=[MODEL_DATA] applycal_phase.parmdb={phase_parmdb_path_dd} applycal_phase.steps=[phase] applycal_phase.phase.correction=phase000")
                with open(os.path.join(log_dir, "step4_asymmetric_dde_gains_blending.log"), "w") as logf:
                    subprocess.run(cmd_blend, stdout=logf, stderr=subprocess.STDOUT, shell=True)
            else:
                cmd_blend = (f"DP3 msin={ms_flare} msout={ms_flare} msout.datacolumn=CORRECTED_DATA steps=[applycal_amp,applycal_phase,applybeam] "
                            f"applycal_amp.type=applycal applycal_amp.direction=[CasA] applycal_amp.parmdb={amp_parmdb_path_dd} applycal_amp.steps=[amp] applycal_amp.amp.correction=amplitude000 "
                            f"applycal_phase.type=applycal applycal_phase.direction=[Sun] applycal_phase.parmdb={phase_parmdb_path_dd} applycal_phase.steps=[phase] applycal_phase.phase.correction=phase000")
                with open(os.path.join(log_dir, "step4_asymmetric_dde_gains_blending.log"), "w") as logf:
                    subprocess.run(cmd_blend, stdout=logf, stderr=subprocess.STDOUT, shell=True)

        # 3. Final synthesis imaging using full LOFAR differential beam arrays
        cmd_img = (f"wsclean -j 40 -mem 100 -auto-mask 5 -auto-threshold 0.5 -fit-beam -apply-primary-beam "
                   f"-use-differential-lofar-beam -reorder -multiscale-scales 0,10,30,90,150 -mgain 0.05 "
                   f"-weight briggs 0 -size 600 600 -minuvw-m 500 -maxuvw-m 12000 -scale 20asec -pol I "
                   f"-niter 100000 -nmiter 100 -intervals-out 5 -data-column CORRECTED_DATA -name {save_dir_SB_img}Sun_flare_cal_Cycle{num_rounds} {ms_flare}")
        with open(os.path.join(log_dir, "step4_final_synthesis_wsclean.log"), "w") as logf:
            subprocess.run(cmd_img.split(), stdout=logf, stderr=subprocess.STDOUT)
