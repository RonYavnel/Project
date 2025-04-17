# Import RSA encryption library
from Crypto.PublicKey import RSA
# Import PKCS1_OAEP - an encryption scheme(padding) for RSA
from Crypto.Cipher import PKCS1_OAEP

class Encryption:
    # Initializes file paths for storing public and private keys.
    def __init__(self, server_private_key_file='server_private.pem', server_public_key_file='server_public.pem', 
                 client_private_key_file='client_private.pem', client_public_key_file='client_public.pem'):
        self.server_private_key_file = server_private_key_file
        self.server_public_key_file = server_public_key_file
        self.client_private_key_file = client_private_key_file
        self.client_public_key_file = client_public_key_file

    
    # Generate public and private keys
    # Run only once!!!
    def generate_keys(self):

        # Generate Server Keys
        server_key = RSA.generate(2048)
        server_private_key = server_key.export_key()
        server_public_key = server_key.publickey().export_key()

        # Save the server private key
        with open(self.server_private_key_file, 'wb') as f:
            f.write(server_private_key)

        # Save the server public key
        with open(self.server_public_key_file, 'wb') as f:
            f.write(server_public_key)
        
        # Generate Client Keys
        client_key = RSA.generate(2048)
        client_private_key = client_key.export_key()
        client_public_key = client_key.publickey().export_key()

        # Save the client private key
        with open(self.client_private_key_file, 'wb') as f:
            f.write(client_private_key)

        # Save the client public key
        with open(self.client_public_key_file, 'wb') as f:
            f.write(client_public_key)

        print(f"Server keys saved to {self.server_private_key_file} and {self.server_public_key_file}")
        print(f"Client keys saved to {self.client_private_key_file} and {self.client_public_key_file}")

    # Function to load the server public key
    def load_server_public_key(self, file_path='server_public.pem'):
        with open(file_path, 'rb') as f:
            return RSA.import_key(f.read())

    # Function to load the server private key
    def load_server_private_key(self, file_path='server_private.pem'):
        with open(file_path, 'rb') as f:
            return RSA.import_key(f.read())

    # Function to load the client public key
    def load_client_public_key(self, file_path='client_public.pem'):
        with open(file_path, 'rb') as f:
            return RSA.import_key(f.read())

    # Function to load the client private key
    def load_client_private_key(self, file_path='client_private.pem'):
        with open(file_path, 'rb') as f:
            return RSA.import_key(f.read())

    # Encrypt data using the public key
    def encrypt_data(self, data, public_key):
        cipher = PKCS1_OAEP.new(public_key)
        max_chunk_size = 190  # for 2048-bit key + PKCS1_OAEP
        data_bytes = data.encode('utf-8')

        encrypted_chunks = []
        for i in range(0, len(data_bytes), max_chunk_size):
            chunk = data_bytes[i:i + max_chunk_size]
            encrypted_chunk = cipher.encrypt(chunk)
            encrypted_chunks.append(encrypted_chunk)

        return b''.join(encrypted_chunks)


    # Decrypt data using the private key
    def decrypt_data(self, encrypted_data, private_key):
        cipher = PKCS1_OAEP.new(private_key)
        chunk_size = 256  # RSA 2048-bit key output size (in bytes)

        decrypted_chunks = []
        for i in range(0, len(encrypted_data), chunk_size):
            chunk = encrypted_data[i:i + chunk_size]
            decrypted_chunk = cipher.decrypt(chunk)
            decrypted_chunks.append(decrypted_chunk)

        return b''.join(decrypted_chunks).decode('utf-8')


if __name__ == "__main__":
    encryption = Encryption()
    encryption.generate_keys()  # Run this only once to generate keys