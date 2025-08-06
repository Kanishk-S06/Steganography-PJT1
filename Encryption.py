from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Random import get_random_bytes
import base64

# Function to save the encryption key to a file
def save_key(key, filename):
    with open(filename, 'wb') as file:
        file.write(key)

# Function to encrypt the message
def encrypt_message(message, key):
    cipher = AES.new(key, AES.MODE_CBC)  # AES CBC mode
    padded_message = pad(message.encode(), AES.block_size)  # Padding the message to block size
    encrypted_message = cipher.encrypt(padded_message)
    
    # Return the encrypted message and the initialization vector (IV)
    return base64.b64encode(cipher.iv + encrypted_message).decode('utf-8')

# Function to save the encrypted message to a file
def save_encrypted_message(encrypted_message, filename):
    with open(filename, 'w') as file:
        file.write(encrypted_message)

# Generate a random key (128-bit key)
key = get_random_bytes(16)

# Simulating a long message
long_message = "This is a very long message. " * 100

# Encrypt the message
encrypted_message = encrypt_message(long_message, key)

# ✅ Corrected paths using raw strings
encrypted_message_path = r"C:\Users\KANISHK\Desktop\Steganography-PJT-main\Steganography\encrypted_message.txt"
encryption_key_path = r"C:\Users\KANISHK\Desktop\Steganography-PJT-main\Steganography\encryption_key.bin"

# Save the encrypted message and key
save_encrypted_message(encrypted_message, encrypted_message_path)
save_key(key, encryption_key_path)

print(f"✅ Encrypted message saved to: {encrypted_message_path}")
print(f"✅ Encryption key saved to: {encryption_key_path}")
