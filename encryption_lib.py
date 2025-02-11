from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

# Generate RSA keys and save them to files
def generate_keys(private_key_file='server_private.pem', public_key_file='server_public.pem'):
    key = RSA.generate(2048)
    private_key = key.export_key()
    public_key = key.publickey().export_key()

    # Save the private key
    with open(private_key_file, 'wb') as f:
        f.write(private_key)

    # Save the public key
    with open(public_key_file, 'wb') as f:
        f.write(public_key)
    print(f"Keys saved to {private_key_file} and {public_key_file}")

# Load the server's public key (for client-side encryption)
def load_public_key(file_path='server_public.pem'):
    with open(file_path, 'rb') as f:
        return RSA.import_key(f.read())

# Load the server's private key (for server-side decryption)
def load_private_key(file_path='server_private.pem'):
    with open(file_path, 'rb') as f:
        return RSA.import_key(f.read())

# Encrypt data using the RSA public key
def encrypt_data(data, public_key):
    cipher = PKCS1_OAEP.new(public_key)
    return cipher.encrypt(data.encode('utf-8'))

# Decrypt data using the RSA private key
def decrypt_data(encrypted_data, private_key):
    cipher = PKCS1_OAEP.new(private_key)
    return cipher.decrypt(encrypted_data).decode('utf-8')

if __name__ == "__main__":
    generate_keys()  # Run this only once to generate keys
