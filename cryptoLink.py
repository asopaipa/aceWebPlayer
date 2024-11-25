from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import os

def generate_key(password, salt):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt.encode(),
        iterations=100000,
        backend=default_backend()
    )
    return kdf.derive(password.encode())

def encrypt(plaintext, key, iv):
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    return encryptor.update(plaintext.encode()) + encryptor.finalize()

def decrypt(ciphertext, key, iv):
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    return decryptor.update(ciphertext) + decryptor.finalize()

# Ejemplo de uso
plaintext = "https://google.com"
password = "ks9PmxgfIwnu"
salt = "b185vyh42IO4"
iv = os.urandom(16)

key = generate_key(password, salt)
ciphertext = encrypt(plaintext, key, iv)
decrypted_plaintext = decrypt(ciphertext, key, iv)

print("Texto cifrado:", ciphertext)
print("iv:", iv)
print("Texto descifrado:", decrypted_plaintext.decode())
