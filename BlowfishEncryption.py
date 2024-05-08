from Crypto.Cipher import Blowfish
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
from base64 import b64encode, b64decode

def decrypt_text(encrypted_text, key):
    # Decode the Base64-encoded string
    ciphertext_bytes = b64decode(encrypted_text)
    
    # Ensure the length of the ciphertext is a multiple of the block size
    if len(ciphertext_bytes) % Blowfish.block_size != 0:
        raise ValueError("Input is not a multiple of the block size. It may not be properly encrypted.")
    
    # Extract the IV
    iv = ciphertext_bytes[:Blowfish.block_size]
    ciphertext_bytes = ciphertext_bytes[Blowfish.block_size:]
    
    # Convert key to bytes
    key_bytes = key.encode('utf-8')
    
    # Create a Blowfish cipher object with the IV
    cipher = Blowfish.new(key_bytes, Blowfish.MODE_CBC, iv)
    
    # Decrypt the text and remove padding
    decrypted_bytes = unpad(cipher.decrypt(ciphertext_bytes), Blowfish.block_size)
    
    # Return the decrypted text as a string
    return decrypted_bytes.decode('utf-8')

def encrypt_text(text, key):
    # Convert text and key to bytes
    text_bytes = text.encode('utf-8')
    key_bytes = key.encode('utf-8')
    
    # Generate a random initialization vector (IV)
    iv = get_random_bytes(Blowfish.block_size)
    
    # Create a Blowfish cipher object
    cipher = Blowfish.new(key_bytes, Blowfish.MODE_CBC, iv)
    
    # Pad the text and encrypt it
    ciphertext_bytes = cipher.iv + cipher.encrypt(pad(text_bytes, Blowfish.block_size))
    
    # Return the IV and the encrypted text as a Base64-encoded string
    return b64encode(ciphertext_bytes).decode('utf-8')
