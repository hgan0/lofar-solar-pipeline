import os
import subprocess

def create_model(obsvID, SB_Sun, SB_Calibrator, model, dir_name, processed_base):
    """Converts wsclean point source tracking tables into standard multi-patch LOFAR source text files."""
    save_dir = os.path.join(processed_base, obsvID, dir_name, model, "")

    if model == "CasA":
        for i in range(len(SB_Sun)):
            model_dir_SB = os.path.join(save_dir, SB_Sun[i], "models", "")
            log_dir = os.path.join(save_dir, SB_Sun[i], "logs", "")
            os.makedirs(log_dir, exist_ok=True)
            os.makedirs(model_dir_SB, exist_ok=True)

            if os.path.exists(model_dir_SB):
                os.system(f"rm -rf {model_dir_SB}*.sourcedb")

            # 1. Cluster Sun components into 1 single sky patch
            cmd_cluster = ["cluster", f"{model_dir_SB}sun_model-sources.txt", f"{model_dir_SB}model_1c.txt", "1"]
            with open(os.path.join(log_dir, "model_step_cluster.log"), "w") as logf:
                subprocess.run(cmd_cluster, stdout=logf, stderr=subprocess.STDOUT)

            os.system(f"cp /app/models/CasA.txt {model_dir_SB}")

            # Replace CasA_4_patch
            CasA_path = model_dir_SB + "CasA.txt"
            if os.path.exists(CasA_path):
                with open(CasA_path, 'r') as f:
                    content = f.read()
                # Swap out the default cluster name for your DP3 direction identifier
                content = content.replace("CasA_4_patch", "CasA")
                with open(CasA_path, 'w') as f:
                    f.write(content)

            # 2. Assign patch identity names recognized by DP3 directions arrays
            model_1c_path = os.path.join(model_dir_SB, "model_1c.txt")
            if os.path.exists(model_1c_path):
                with open(model_1c_path, 'r') as f:
                    content = f.read()
                content = content.replace("cluster1", "Sun")
                with open(model_1c_path, 'w') as f:
                    f.write(content)

            # 3. Merge discrete directional sources via editmodel commands
            cmd_merge = ["editmodel", "-m", f"{model_dir_SB}sun+CasA.txt", f"{model_dir_SB}model_1c.txt", f"{model_dir_SB}CasA.txt"]
            with open(os.path.join(log_dir, "model_step_editmodel_merge.log"), "w") as logf:
                subprocess.run(cmd_merge, stdout=logf, stderr=subprocess.STDOUT)

            # Format to LOFAR skymodel standard
            cmd_format = ["editmodel", "-skymodel", f"{model_dir_SB}sun+CasA.txt2", f"{model_dir_SB}sun+CasA.txt"]
            with open(os.path.join(log_dir, "model_step_skymodel_format.log"), "w") as logf:
                subprocess.run(cmd_format, stdout=logf, stderr=subprocess.STDOUT)

            # Build the physical searchable multi-directional sourcedb folder
            cmd_db = ["makesourcedb", f"in={model_dir_SB}sun+CasA.txt2", f"out={model_dir_SB}sun+CasA.sourcedb"]
            with open(os.path.join(log_dir, "model_step_makesourcedb.log"), "w") as logf:
                subprocess.run(cmd_db, stdout=logf, stderr=subprocess.STDOUT)
