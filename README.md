# Nextcloud Backup System

This project implements a backup system for Nextcloud with file versioning and selective sync capabilities.

## Features

- Incremental backups
- File versioning
- Selective sync
- Encryption
- Compression
- Google Drive integration
- Email notifications

## Setup

1. Install dependencies:

2. Configure the source and destination directories in `main.py`.

3. Set up Google Drive API credentials and place the `credentials.json` file in the project root.

4. Configure email settings in `src/email_notification.py`.

5. Run the backup:

## Configuration

- Modify `config/selective_sync_config.json` to specify which folders to sync.
- Adjust backup settings in `main.py` as needed.

## Screenshots

<img width="2102" height="1191" alt="image" src="https://github.com/user-attachments/assets/ed295ca0-201d-49c8-998b-6078b788d2b3" />

<img width="2102" height="1191" alt="image" src="https://github.com/user-attachments/assets/ffbb9f12-f84c-45ff-ac54-59966cb20ca8" />

<img width="2083" height="1174" alt="image" src="https://github.com/user-attachments/assets/dc083292-39c4-450a-93db-d60abf02cff6" />

<img width="2077" height="1662" alt="image" src="https://github.com/user-attachments/assets/6d3d4093-1a0f-4d26-9b2b-b17767e9108d" />
