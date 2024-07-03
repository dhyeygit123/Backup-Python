import hashlib
import gzip
import shutil

def calculate_file_hash(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def compress_file(source_file, dest_file):
    with open(source_file, 'rb') as f_in, gzip.open(dest_file, 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)
    return dest_file