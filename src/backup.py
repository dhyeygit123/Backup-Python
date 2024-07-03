import os
import time
import json
import logging
from src.encryption import encrypt_file
from src.file_handling import calculate_file_hash, compress_file
from src.google_drive import upload_directory_to_drive
from src.email_notification import send_backup_email
from src.utils import get_directory_size, convert_bytes

def get_selective_sync_folders(config_file):
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return json.load(f)
    return []

def backup_directory(source_dir, dest_dir, key, num_backups_to_keep=5, max_versions=5):
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    backup_subdir = os.path.join(dest_dir, 'backup_' + str(int(time.time())))
    os.makedirs(backup_subdir)

    backup_info = {'timestamp': int(time.time()), 'files': [], 'file_hashes': {}}
    
    previous_backup_info = None
    previous_backup_info_file = os.path.join(dest_dir, 'latest_backup_info.json')
    if os.path.exists(previous_backup_info_file):
        with open(previous_backup_info_file, 'r') as f:
            previous_backup_info = json.load(f)

    selective_sync_folders = get_selective_sync_folders('config/selective_sync_config.json')

    for root, _, files in os.walk(source_dir):
        if selective_sync_folders and not any(root.startswith(os.path.join(source_dir, folder)) for folder in selective_sync_folders):
            continue

        for filename in files:
            source_file = os.path.join(root, filename)
            rel_path = os.path.relpath(source_file, source_dir)
            dest_file = os.path.join(backup_subdir, rel_path)

            # File versioning
            if previous_backup_info and rel_path in previous_backup_info['files']:
                versions_dir = os.path.join(dest_dir, 'versions', rel_path)
                os.makedirs(versions_dir, exist_ok=True)
                
                old_file = os.path.join(dest_dir, str(previous_backup_info['timestamp']), rel_path)
                if os.path.exists(old_file):
                    version_file = os.path.join(versions_dir, f"{previous_backup_info['timestamp']}_{filename}")
                    os.rename(old_file, version_file)

                versions = sorted(os.listdir(versions_dir), reverse=True)
                for old_version in versions[max_versions-1:]:
                    os.remove(os.path.join(versions_dir, old_version))

            current_file_hash = calculate_file_hash(source_file)
            if previous_backup_info and rel_path in previous_backup_info['file_hashes']:
                if current_file_hash == previous_backup_info['file_hashes'][rel_path]:
                    continue  # Skip unchanged files

            os.makedirs(os.path.dirname(dest_file), exist_ok=True)
            
            compressed_file = compress_file(source_file, dest_file + '.gz')
            encrypt_file(key, compressed_file, dest_file + '.enc')
            os.remove(compressed_file)
            
            logging.info("Compressed and encrypted file: %s", source_file)
            
            backup_info['files'].append(rel_path)
            backup_info['file_hashes'][rel_path] = current_file_hash

    with open(os.path.join(backup_subdir, 'backup_info.json'), 'w') as f:
        json.dump(backup_info, f)

    os.replace(os.path.join(backup_subdir, 'backup_info.json'), previous_backup_info_file)

    upload_directory_to_drive(backup_subdir)
    
    backup_details = {
        "Backup Directory": backup_subdir,
        "Backup Timestamp": time.ctime(backup_info['timestamp']),
        "Number of Files Backed Up": len(backup_info['files']),
        "Backup Size": get_directory_size(backup_subdir),
        "Source Directory": source_dir,
        "Destination Directory": dest_dir
    }
    
    send_backup_email(backup_details)
    
    rotate_backups(dest_dir, num_backups_to_keep)

    logging.info("Backup completed. Backup info saved.")

def rotate_backups(destination_directory, num_backups_to_keep):
    backup_dirs = sorted([d for d in os.listdir(destination_directory) if os.path.isdir(os.path.join(destination_directory, d)) and d.startswith('backup_')])
    num_backups = len(backup_dirs)
    if num_backups > num_backups_to_keep:
        backups_to_delete = backup_dirs[:num_backups - num_backups_to_keep]
        for backup_dir in backups_to_delete:
            shutil.rmtree(os.path.join(destination_directory, backup_dir))
            logging.info("Deleted old backup: %s", backup_dir)