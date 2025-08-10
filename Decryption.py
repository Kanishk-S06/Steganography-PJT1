# Decryption.py
import base64, zlib
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import HKDF
from Crypto.Hash import SHA256

from bio_fuzzy import load_helper, recover_secret

# --- CONFIG: update these to your paths ---
HELPER_JSON = r"C:\Users\KANISHK\Desktop\Steganography-PJT-main\Steganography\helper.json"
FACE_IMAGE_FOR_DECRYPTION = r"C:\Users\KANISHK\Desktop\Steganography-PJT-main\Steganography\face.jpg"
EXTRACTED_ENCRYPTED_TXT = r"C:\Users\KANISHK\Desktop\Steganography-PJT-main\Steganography\extracted_encrypted_message.txt"
DECRYPTED_MESSAGE_TXT = r"C:\Users\KANISHK\Desktop\Steganography-PJT-main\Steganography\decrypted_message.txt"
# -----------------------------------------

def decrypt_with_biometrics(token_b64: str, helper_path: str, face_path: str) -> str:
    data = base64.b64decode(token_b64)
    if data[0] != 1:
        raise ValueError("Unsupported envelope version")
    salt  = data[1:17]
    nonce = data[17:29]
    tag   = data[29:45]
    ct    = data[45:]

    helper = load_helper(helper_path)
    R = recover_secret(face_path, helper)
    cek = HKDF(R, 32, salt, SHA256)

    cipher = AES.new(cek, AES.MODE_GCM, nonce=nonce)
    pt = cipher.decrypt_and_verify(ct, tag)
    return zlib.decompress(pt).decode("utf-8")

def load_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()

def save_text(s: str, path: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(s)

if __name__ == "__main__":
    token = load_text(EXTRACTED_ENCRYPTED_TXT)
    msg = decrypt_with_biometrics(token, HELPER_JSON, FACE_IMAGE_FOR_DECRYPTION)
    save_text(msg, DECRYPTED_MESSAGE_TXT)
    print(f"✅ Decrypted message saved to '{DECRYPTED_MESSAGE_TXT}'")
