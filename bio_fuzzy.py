# bio_fuzzy.py  (InsightFace + Reed-Solomon, fixed)
import os, json, base64, hashlib, numpy as np, cv2
from typing import Dict
from reedsolo import RSCodec
from insightface.app import FaceAnalysis

# ----------------------------
# Reed–Solomon parameters
# ----------------------------
# RS(255, k) over GF(256) with nsym parity bytes; corrects t = nsym/2 byte errors.
RS_NSYM = 32               # try 32 first; bump to 48 or 64 if your photos vary a lot
RS_K = 255 - RS_NSYM       # payload bytes
R_LEN = RS_K               # secret length (bytes) to RS-encode

# ----------------------------
# Face embedding (InsightFace)
# ----------------------------
_FACE_APP = None
def _get_face_app(model_name: str = "buffalo_l", ctx_id: int = -1, det_size=(640, 640)):
    global _FACE_APP
    if _FACE_APP is None:
        app = FaceAnalysis(name=model_name)
        app.prepare(ctx_id=ctx_id, det_size=det_size)
        _FACE_APP = app
    return _FACE_APP

def get_face_embedding(img_path: str, model_name: str = "buffalo_l") -> np.ndarray:
    """
    Return a normalized face embedding vector (float32, length 512).
    Uses InsightFace ArcFace (buffalo_l). CPU by default (ctx_id=-1).
    """
    app = _get_face_app(model_name=model_name, ctx_id=-1)
    img = cv2.imread(img_path)  # BGR
    if img is None:
        raise ValueError(f"Cannot read image: {img_path}")
    faces = app.get(img)
    if not faces:
        raise ValueError("No face detected in the image.")
    # choose largest face
    def area(f):
        x1, y1, x2, y2 = f.bbox.astype(int)
        return max(0, x2 - x1) * max(0, y2 - y1)
    face = max(faces, key=area)
    emb = face.normed_embedding.astype(np.float32)  # already L2-normalized
    return emb

# ----------------------------
# Quantize embedding -> bytes
# ----------------------------
def embedding_to_bytes(emb: np.ndarray, proj_seed: bytes, out_bytes: int = 255) -> bytes:
    """
    Project embedding to out_bytes*8 bits via random hyperplanes; pack to bytes.
    Deterministic per proj_seed.
    """
    out_bits = out_bytes * 8
    # Seed must be 32-bit for RandomState
    digest = hashlib.sha256(proj_seed).digest()
    seed_int = int.from_bytes(digest[:4], "big")  # 0..2**32-1
    rng = np.random.RandomState(seed_int)

    # Random hyperplanes: (out_bits, dim)
    H = rng.randn(out_bits, emb.shape[0]).astype(np.float32)
    s = (H @ emb) >= 0.0  # boolean sign bits

    # pack bits -> bytes (MSB-first)
    b = bytearray()
    for i in range(0, out_bits, 8):
        byte = 0
        for j in range(8):
            if s[i + j]:
                byte |= (1 << (7 - j))
        b.append(byte)
    return bytes(b)

# ----------------------------
# Fuzzy commitment (code-offset)
# ----------------------------
def enroll_helper(face_img_path: str, proj_seed: bytes = None) -> Dict:
    """
    Enrollment:
      - Generate random secret R (R_LEN bytes)
      - RS encode to 255B codeword
      - Quantize face to 255B Qx
      - Store helper W = codeword XOR Qx (public), plus params
    """
    if proj_seed is None:
        proj_seed = os.urandom(16)

    emb = get_face_embedding(face_img_path)
    Qx = embedding_to_bytes(emb, proj_seed, out_bytes=255)

    R = os.urandom(R_LEN)  # recovered later
    rsc = RSCodec(RS_NSYM)
    codeword = rsc.encode(R)  # 255 bytes
    if len(codeword) != 255:
        raise RuntimeError("Unexpected RS codeword length.")

    W = bytes(a ^ b for a, b in zip(codeword, Qx))
    hR = hashlib.sha256(R).hexdigest()

    helper = {
        "version": 1,
        "proj_seed_b64": base64.b64encode(proj_seed).decode(),
        "W_b64": base64.b64encode(W).decode(),
        "hR": hR,
        "rs_nsym": RS_NSYM,
        "model": "buffalo_l"
    }
    return helper

def recover_secret(face_img_path: str, helper: Dict) -> bytes:
    """
    Recovery:
      - Compute Qy from new face
      - codeword' = W XOR Qy
      - RS decode -> R'
      - Verify SHA-256(R')
    """
    proj_seed = base64.b64decode(helper["proj_seed_b64"])
    W = base64.b64decode(helper["W_b64"])
    rsc = RSCodec(helper.get("rs_nsym", RS_NSYM))

    emb = get_face_embedding(face_img_path, helper.get("model", "buffalo_l"))
    Qy = embedding_to_bytes(emb, proj_seed, out_bytes=255)
    codeword_prime = bytes(a ^ b for a, b in zip(W, Qy))

    decoded = rsc.decode(codeword_prime)
    # reedsolo versions differ: some return just message (bytes), others a tuple.
    if isinstance(decoded, (bytes, bytearray)):
        R_prime = bytes(decoded)
    elif isinstance(decoded, tuple) and len(decoded) >= 1:
        R_prime = bytes(decoded[0])
    else:
        raise RuntimeError("Unexpected RS decode return format.")

    if hashlib.sha256(R_prime).hexdigest() != helper["hR"]:
        raise ValueError("Biometric does not match; secret recovery failed.")
    return R_prime

def save_helper(helper: Dict, path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(helper, f, indent=2)

def load_helper(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
