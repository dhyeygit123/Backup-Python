from cryptography.fernet import Fernet

def generate_key(key_file):
    key = Fernet.generate_key()
    with open(key_file, 'wb') as f:
        f.write(key)

def load_key(key_file):
    with open(key_file, 'rb') as f:
        return f.read()

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