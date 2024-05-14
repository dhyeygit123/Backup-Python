import os
import os.path
import shutil
import hashlib
import logging
import time
import json
import gzip
from cryptography.fernet import Fernet
import smtplib


from email.message import EmailMessage
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

def email_part(subject, body, to):
    msg = EmailMessage()
    msg.set_content(body)
    msg['subject'] = subject
    msg['to'] = to
    user = "dhyey.c.patel@gmail.com"
    msg['from'] = user
    password = "qgqywhhqhogksurn"
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(user, password)
    server.send_message(msg)
    server.quit()
    
# Configure logging
logging.basicConfig(filename='backup.log', level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')

SCOPES = ["https://www.googleapis.com/auth/drive"]

def upload_directory_to_drive(directory_path):
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build("drive", "v3", credentials=creds)

        # Create a new folder with the current timestamp
        current_time = datetime.now().strftime("%Y%m%d-%H%M%S")
        folder_name = f"backup_{current_time}"
        file_metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder"
        }
        folder = service.files().create(body=file_metadata, fields="id").execute()
        folder_id = folder.get('id')

        for root, dirs, files in os.walk(directory_path):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                relative_path = os.path.relpath(file_path, directory_path)
                file_metadata = {
                    "name": relative_path,
                    "parents": [folder_id]
                }
                media = MediaFileUpload(file_path, resumable=True)
                upload_file = service.files().create(body=file_metadata, media_body=media, fields="id").execute()
                print(f"Backed up File: {relative_path}")

    except HttpError as e:
        print("Error: " + str(e))


# Generate or load encryption key
def generate_key(key_file):
    key = Fernet.generate_key()
    with open(key_file, 'wb') as f:
        f.write(key)

def load_key(key_file):
    with open(key_file, 'rb') as f:
        return f.read()

# Encrypt and decrypt functions
def encrypt_file(key, source_file, dest_file):
    cipher = Fernet(key)
    with open(source_file, 'rb') as f:
        data = f.read()
    encrypted_data = cipher.encrypt(data)
    with open(dest_file, 'wb') as f:
        f.write(encrypted_data)

def decrypt_file(key, source_file, dest_file):
    cipher = Fernet(key)
    with open(source_file, 'rb') as f:
        encrypted_data = f.read()
    decrypted_data = cipher.decrypt(encrypted_data)
    with open(dest_file, 'wb') as f:
        f.write(decrypted_data)

def calculate_file_hash(file_path):
    """
    Calculate the SHA256 hash of a file.
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while True:
            data = f.read(65536)  # Read in 64KB chunks
            if not data:
                break
            sha256.update(data)
    return sha256.hexdigest()

def rotate_backups(destination_directory, num_backups_to_keep):
    """
    Rotate backups by keeping a specified number of most recent backups.
    """
    backup_dirs = sorted([d for d in os.listdir(destination_directory) if os.path.isdir(os.path.join(destination_directory, d))])
    num_backups = len(backup_dirs)
    if num_backups > num_backups_to_keep:
        backups_to_delete = backup_dirs[:num_backups - num_backups_to_keep]
        for backup_dir in backups_to_delete:
            shutil.rmtree(os.path.join(destination_directory, backup_dir))
            logging.info("Deleted old backup: %s", backup_dir)

def backup_directory(source_dir, dest_dir, key, num_backups_to_keep=5):
    """
    Perform an incremental backup of a directory.
    """
    # Create destination directory if it doesn't exist
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    # Create a subdirectory for this backup action
    backup_subdir = os.path.join(dest_dir, 'backup_' + str(int(time.time())))
    os.makedirs(backup_subdir)

    backup_info = {'timestamp': int(time.time()), 'files': [], 'file_hashes': {}}  # Initialize file_hashes key
    
    # Load previous backup info if available
    previous_backup_info = None
    previous_backup_info_file = os.path.join(dest_dir, 'latest_backup_info.json')
    if os.path.exists(previous_backup_info_file):
        with open(previous_backup_info_file, 'r') as f:
            previous_backup_info = json.load(f)

    # Iterate over files in the source directory
    for root, _, files in os.walk(source_dir):
        for filename in files:
            source_file = os.path.join(root, filename)
            dest_file = os.path.join(backup_subdir, os.path.relpath(source_file, source_dir))

            # Check if file exists in previous backup and has not been modified
            if previous_backup_info and os.path.relpath(source_file, source_dir) in previous_backup_info['files']:
                previous_file_hash = previous_backup_info['file_hashes'][os.path.relpath(source_file, source_dir)]
                current_file_hash = calculate_file_hash(source_file)
                if previous_file_hash == current_file_hash:
                    continue  # Skip unchanged files

            # Create necessary directories in destination path
            os.makedirs(os.path.dirname(dest_file), exist_ok=True)
            # Encrypt and compress the file
            with open(source_file, 'rb') as f_in, gzip.open(dest_file + '.gz', 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
            logging.info("Compressed and encrypted file: %s", source_file)
            # Record file in backup info
            backup_info['files'].append(os.path.relpath(source_file, source_dir))
            backup_info['file_hashes'][os.path.relpath(source_file, source_dir)] = calculate_file_hash(source_file)

    # Write backup info to file
    with open(os.path.join(backup_subdir, 'backup_info.json'), 'w') as f:
        json.dump(backup_info, f)


    # Update latest backup info
    shutil.copy2(os.path.join(backup_subdir, 'backup_info.json'), previous_backup_info_file)

    upload_directory_to_drive(backup_subdir)
    
       # Gather backup details and information
    backup_details = {
        "Backup Directory": backup_subdir,
        "Backup Timestamp": time.ctime(backup_info['timestamp']),
        "Number of Files Backed Up": len(backup_info['files']),
        "Backup Size": get_directory_size(backup_subdir),
        "Source Directory": source_dir,
        "Destination Directory": dest_dir
    }
    
    # Create the email body with backup details
    email_body = "Backup Details:\n\n"
    for key, value in backup_details.items():
        email_body += f"{key}: {value}\n"
        
    # Send the email with backup details
    email_part("Backup Completed", email_body, "dhyey4073@gmail.com")
    
    # Rotate backups
    rotate_backups(dest_dir, num_backups_to_keep)

    logging.info("Backup completed. Backup info saved.\n")

def get_directory_size(directory):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(directory):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return convert_bytes(total_size)

def convert_bytes(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"

if __name__ == "__main__":
    source_directory = "/media/dhyey/Data/BTEP_Final/Nextcloud"
    destination_directory = "/media/dhyey/Data/BTEP_Final/Backup"
    key_file = 'backup_key.key'

    # Generate or load encryption key
    if not os.path.exists(key_file):
        generate_key(key_file)
        logging.info("Encryption key generated.")
    key = load_key(key_file)

    backup_directory(source_directory, destination_directory, key)
