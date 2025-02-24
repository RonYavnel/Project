from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

class Encryption:
    def __init__(self, private_key_file='server_private.pem', public_key_file='server_public.pem'):
        self.private_key_file = private_key_file
        self.public_key_file = public_key_file

    def generate_keys(self):
        key = RSA.generate(2048)
        private_key = key.export_key()
        public_key = key.publickey().export_key()

        # Save the private key
        with open(self.private_key_file, 'wb') as f:
            f.write(private_key)

        # Save the public key
        with open(self.public_key_file, 'wb') as f:
            f.write(public_key)
        print(f"Keys saved to {self.private_key_file} and {self.public_key_file}")

    def load_server_public_key(self, file_path='server_public.pem'):
        with open(file_path, 'rb') as f:
            return RSA.import_key(f.read())

    def load_server_private_key(self, file_path='server_private.pem'):
        with open(file_path, 'rb') as f:
            return RSA.import_key(f.read())

    def load_client_public_key(self, file_path='client_public.pem'):
        with open(file_path, 'rb') as f:
            return RSA.import_key(f.read())

    def load_client_private_key(self, file_path='client_private.pem'):
        with open(file_path, 'rb') as f:
            return RSA.import_key(f.read())

    def encrypt_data(self, data, public_key):
        cipher = PKCS1_OAEP.new(public_key)
        encrypted = cipher.encrypt(data.encode('utf-8'))
        return encrypted

    def decrypt_data(self, encrypted_data, private_key):
        cipher = PKCS1_OAEP.new(private_key)
        decrypted = cipher.decrypt(encrypted_data)
        return decrypted.decode('utf-8')

if __name__ == "__main__":
    encryption = Encryption()
    encryption.generate_keys()  # Run this only once to generate keys