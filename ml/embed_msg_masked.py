#!/usr/bin/env python3
"""
embed_msg_masked.py — LSB embed using content-aware masks
- Reads encrypted text file (bytes).
- Prefixes payload with 32-bit big-endian length (bytes).
- Embeds bits into BLUE-channel LSBs where mask==255.
- Writes modified frames as PNG to preserve LSBs.
"""
import os
import cv2
import argparse
import numpy as np
from tqdm import tqdm

def bytes_to_bits(b: bytes):
    return np.unpackbits(np.frombuffer(b, dtype=np.uint8))

def int32_to_bits(n: int):
    # 32-bit BE integer
    arr = np.array([(n >> shift) & 0xFF for shift in (24,16,8,0)], dtype=np.uint8)
    return np.unpackbits(arr)

def embed_bits_in_frame(img, mask, bits, bit_idx):
    # img: HxWx3 uint8 (BGR), mask: HxW {0,255}
    H, W, _ = img.shape
    B = img[:,:,0]  # Blue channel
    flat_B = B.reshape(-1)
    flat_mask = (mask.reshape(-1) == 255)

    # indices where we can write
    idxs = np.nonzero(flat_mask)[0]
    capacity = idxs.shape[0]

    # how many bits can we write here
    remain = bits.shape[0] - bit_idx
    write_n = min(capacity, remain)
    if write_n > 0:
        target = idxs[:write_n]
        # clear LSB then set
        flat_B[target] = (flat_B[target] & 0xFE) | bits[bit_idx: bit_idx + write_n]
        bit_idx += write_n

    # put back
    B = flat_B.reshape(H, W)
    img[:,:,0] = B
    return img, bit_idx, capacity

def main():
    ap = argparse.ArgumentParser(description="Embed message bits using masks (blue-channel LSB)")
    ap.add_argument("--frames_dir", required=True, help="Input frames directory (original frames)")
    ap.add_argument("--masks_dir", required=True, help="Masks directory created by mask_generator.py")
    ap.add_argument("--message_file", required=True, help="Encrypted message file to embed")
    ap.add_argument("--out_dir", required=True, help="Output directory for modified frames (PNG)")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    # Read payload
    with open(args.message_file, "rb") as f:
        payload = f.read()
    payload_bits = np.concatenate([int32_to_bits(len(payload)), bytes_to_bits(payload)])

    # Gather frames and masks (match by sorted order/filename)
    frame_names = sorted([n for n in os.listdir(args.frames_dir) if n.lower().endswith((".png",".jpg",".jpeg"))])
    mask_names = sorted([n for n in os.listdir(args.masks_dir) if n.lower().endswith(".png")])

    if len(frame_names) != len(mask_names):
        print(f"WARNING: frame count ({len(frame_names)}) != mask count ({len(mask_names)}). Proceeding by sorted order.")

    bit_idx = 0
    total_capacity = 0

    for fn, mn in tqdm(list(zip(frame_names, mask_names)), desc="Embedding"):
        fp = os.path.join(args.frames_dir, fn)
        mp = os.path.join(args.masks_dir, mn)
        img = cv2.imread(fp, cv2.IMREAD_COLOR)
        mask = cv2.imread(mp, cv2.IMREAD_GRAYSCALE)
        if img is None or mask is None:
            continue
        img, bit_idx, cap = embed_bits_in_frame(img, mask, payload_bits, bit_idx)
        total_capacity += cap
        outp = os.path.join(args.out_dir, os.path.splitext(fn)[0] + ".png")
        cv2.imwrite(outp, img)

    if bit_idx < payload_bits.shape[0]:
        need = payload_bits.shape[0] - bit_idx
        raise SystemExit(f"ERROR: Ran out of capacity. Needed {payload_bits.shape[0]} bits, wrote {bit_idx}. Short by {need} bits. "
                         f"Consider increasing mask keep_ratio or number of frames. Total per-frame capacity written: {total_capacity}.")
    print(f"Done. Embedded {bit_idx} bits into {len(frame_names)} frames. Saved to {args.out_dir}")

if __name__ == "__main__":
    main()
