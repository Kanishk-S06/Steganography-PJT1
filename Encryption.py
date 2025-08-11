# Encryption.py — Passphrase + scrypt KDF + AES-GCM (no biometrics, no key file)
import os, base64, zlib
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import scrypt
from Crypto.Random import get_random_bytes

# --- Paths (edit if your project lives elsewhere) ---
PROJECT_DIR = r"C:\Users\KANISHK\Desktop\Steganography-PJT-main\Steganography"
ENCRYPTED_MESSAGE_TXT = os.path.join(PROJECT_DIR, "encrypted_message.txt")
PLAINTEXT_FILE = os.path.join(PROJECT_DIR, "message.txt")   # optional; if exists, we'll read from it
PASS_FILE = os.path.join(PROJECT_DIR, "pass.txt")           # optional; plain-text passphrase file
PASS_ENV = "STEGO_PASS"                                     # optional; env var for passphrase

# --- scrypt cost parameters (tune N_LOG2 for security vs speed) ---
# N = 2**N_LOG2. Typical: 15 (32768) to 18 (262144)
N_LOG2 = 15
R = 8
P = 1

def get_passphrase() -> bytes:
    # 1) Environment variable
    pw = os.environ.get(PASS_ENV)
    if pw:
        return pw.encode("utf-8")
    # 2) Text file (pass.txt)
    if os.path.exists(PASS_FILE):
        with open(PASS_FILE, "r", encoding="utf-8") as f:
            return f.read().strip().encode("utf-8")
    # 3) Visible prompt (fallback)
    return input("Enter passphrase (visible): ").encode("utf-8")

def load_plaintext() -> str:
    if os.path.exists(PLAINTEXT_FILE):
        with open(PLAINTEXT_FILE, "r", encoding="utf-8") as f:
            return f.read()
    return "This is a test message hidden in the video."*100

def encrypt_message(plaintext: str, passphrase: bytes) -> str:
    # Derive 256-bit key with scrypt
    salt = get_random_bytes(16)
    key = scrypt(passphrase, salt, key_len=32, N=1 << N_LOG2, r=R, p=P)

    # AEAD: AES-GCM
    nonce = get_random_bytes(12)
    pt = zlib.compress(plaintext.encode("utf-8"))
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    ct, tag = cipher.encrypt_and_digest(pt)

    # Envelope: [ver(0x03) | N_log2(1B) | r(1B) | p(1B) | salt(16B) | nonce(12B) | tag(16B) | ct]
    blob = b"\x03" + bytes([N_LOG2, R, P]) + salt + nonce + tag + ct
    return base64.b64encode(blob).decode("utf-8")

def save_text(s: str, path: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(s)

if __name__ == "__main__":
    plaintext = load_plaintext()
    pw = get_passphrase()
    token = encrypt_message(plaintext, pw)
    save_text(token, ENCRYPTED_MESSAGE_TXT)
    print(f"✅ Encrypted message saved to: {ENCRYPTED_MESSAGE_TXT}")
