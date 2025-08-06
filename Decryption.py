from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import base64

# Function to decrypt the message
def decrypt_message(encrypted_message, key):
    # Decode the base64 encoded encrypted message
    encrypted_message_bytes = base64.b64decode(encrypted_message)
    
    # Extract the IV (first 16 bytes) and the encrypted message (remaining bytes)
    iv = encrypted_message_bytes[:16]
    encrypted_message = encrypted_message_bytes[16:]
    
    # Create the AES cipher with the key and IV
    cipher = AES.new(key, AES.MODE_CBC, iv)
    
    # Decrypt the message and remove padding
    decrypted_message = unpad(cipher.decrypt(encrypted_message), AES.block_size)
    
    # Return the decrypted message as a string
    return decrypted_message.decode('utf-8')

# Function to load the encrypted message from the file
def load_encrypted_message(filename):
    with open(filename, 'r') as file:
        return file.read().strip()

# Function to save the decrypted message to a file
def save_decrypted_message(decrypted_message, filename):
    with open(filename, 'w') as file:
        file.write(decrypted_message)

# Function to load the key (it could be saved in a file or passed as needed)
def load_key(key_filename):
    with open(key_filename, 'rb') as file:
        return file.read()

# Example usage
encrypted_message_filename = r"C:\Users\KANISHK\Desktop\Steganography-PJT-main\Steganography\extracted_encrypted_message.txt"
decrypted_message_filename = r"C:\Users\KANISHK\Desktop\Steganography-PJT-main\Steganography\decrypted_message.txt"
key_filename = r"C:\Users\KANISHK\Desktop\Steganography-PJT-main\Steganography\encryption_key.bin"

# Load the encrypted message from the file
encrypted_message = load_encrypted_message(encrypted_message_filename)

# Load the encryption key
key = load_key(key_filename)

# Decrypt the message using the loaded key
decrypted_message = decrypt_message(encrypted_message, key)

# Save the decrypted message to a new file
save_decrypted_message(decrypted_message, decrypted_message_filename)

print(f"Decrypted message saved to '{decrypted_message_filename}'")