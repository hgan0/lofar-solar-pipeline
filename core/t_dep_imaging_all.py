import os
import subprocess

def imaging_FITS(setting, FITSname, MSname, log_dir):
    cmdstr = f"{setting} -data-column CORRECTED_DATA -name {FITSname} {MSname}"
    with open(os.path.join(log_dir, "step5_fits_generation.log"), "w") as logf:
        subprocess.run(cmdstr.split(), stdout=logf, stderr=subprocess.STDOUT, shell=True)

def all_imaging(obsvID, SB_Sun, SB_Calibrator, model, processed_base, dir_name="calibrated"):
    """Batch processes verification visual telemetry profiles across historical cycles."""
    save_dir = os.path.join(processed_base, obsvID, dir_name, model, "")
    wsclean_base = ("wsclean -j 40 -mem 100 -auto-mask 5 -auto-threshold 0.5 -fit-beam -make-psf -reorder "
                    "-multiscale-scales 0,10,30,90,150 -mgain 0.05 -weight briggs 0 -apply-primary-beam "
                    "-size 600 600 -minuvw-m 500 -maxuvw-m 10000 -scale 20asec -pol I -niter 100000 -nmiter 100 -intervals-out 500")

    for i in range(len(SB_Sun)):
        save_dir_SB = os.path.join(save_dir, SB_Sun[i], "")
        save_dir_SB_img = os.path.join(save_dir_SB, "images", "")
        log_dir = os.path.join(save_dir_SB, "logs", "")
        os.makedirs(log_dir, exist_ok=True)

        ms_name = f"{save_dir_SB}Sun_flare_{SB_Sun[i]}_Cycle0.MS"
        fits_name = f"{save_dir_SB_img}Sun_flare_Final_Review"

        if os.path.exists(ms_name):
            imaging_FITS(wsclean_base, fits_name, ms_name)
