import os
import shutil
import datetime

def backup_phase(phase_name):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backups/{phase_name}_{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)
    
    # Files to backup
    targets = [
        "app/",
        "docs/",
        "backups/",
        ".env",
        "run_crm.sh",
        "requirements.txt"
    ]
    
    for target in targets:
        if os.path.isdir(target):
            # Avoid recursive backup
            if target == "backups/":
                continue
            shutil.copytree(target, os.path.join(backup_dir, target), dirs_exist_ok=True)
        elif os.path.isfile(target):
            shutil.copy2(target, backup_dir)

    print(f"📦 Phase {phase_name} backup completed at {backup_dir}")

if __name__ == "__main__":
    backup_phase("phase14_detail_view")
