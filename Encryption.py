# Encryption.py
import base64, zlib
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import HKDF
from Crypto.Hash import SHA256
from Crypto.Random import get_random_bytes

# NEW: biometric helper
from bio_fuzzy import load_helper, recover_secret

# --- CONFIG: update these to your paths ---
HELPER_JSON = r"C:\Users\KANISHK\Desktop\Steganography-PJT-main\Steganography\helper.json"
FACE_IMAGE_FOR_ENCRYPTION = r"C:\Users\KANISHK\Desktop\Steganography-PJT-main\Steganography\face.jpg"
ENCRYPTED_MESSAGE_TXT = r"C:\Users\KANISHK\Desktop\Steganography-PJT-main\Steganography\encrypted_message.txt"
# -----------------------------------------

def encrypt_message_with_biometrics(plaintext: str, helper_path: str, face_path: str) -> str:
    helper = load_helper(helper_path)
    R = recover_secret(face_path, helper)               # recover 223-byte secret from your face

    salt = get_random_bytes(16)                         # per-message HKDF salt
    cek  = HKDF(R, 32, salt, SHA256)                    # 256-bit CEK

    nonce = get_random_bytes(12)                        # GCM nonce
    pt = zlib.compress(plaintext.encode("utf-8"))       # optional but recommended
    cipher = AES.new(cek, AES.MODE_GCM, nonce=nonce)
    ct, tag = cipher.encrypt_and_digest(pt)

    # Envelope: [0x01 | salt(16) | nonce(12) | tag(16) | ct]
    blob = b'\x01' + salt + nonce + tag + ct
    return base64.b64encode(blob).decode("utf-8")

def save_encrypted_message(encrypted_b64: str, path: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(encrypted_b64)

if __name__ == "__main__":
    # Example plaintext (replace with your real message source if needed)
    long_message = "This is a very long message. " * 100
    token = encrypt_message_with_biometrics(long_message, HELPER_JSON, FACE_IMAGE_FOR_ENCRYPTION)
    save_encrypted_message(token, ENCRYPTED_MESSAGE_TXT)
    print(f"✅ Encrypted message saved to: {ENCRYPTED_MESSAGE_TXT}")
