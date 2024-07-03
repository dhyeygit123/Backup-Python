import os
import logging
from src.backup import backup_directory
from src.encryption import generate_key, load_key

if __name__ == "__main__":
    logging.basicConfig(filename='logs/backup.log', level=logging.INFO, 
                        format='%(asctime)s - %(levelname)s: %(message)s')

    source_directory = "/path/to/source"
    destination_directory = "/path/to/destination"
    key_file = 'config/backup_key.key'

    if not os.path.exists(key_file):
        generate_key(key_file)
        logging.info("Encryption key generated.")
    key = load_key(key_file)

    backup_directory(source_directory, destination_directory, key)