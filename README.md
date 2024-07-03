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

