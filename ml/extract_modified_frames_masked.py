#!/usr/bin/env python3
"""
extract_modified_frames_masked.py — Extract bits using the SAME masks
- Reads modified PNG frames and corresponding masks.
- Reads 32-bit big-endian prefix to get payload length.
- Extracts payload bits from BLUE-channel LSBs where mask==255.
- Writes reconstructed encrypted message to file.
"""
import os
import cv2
import argparse
import numpy as np
from tqdm import tqdm

def bits_to_bytes(bits: np.ndarray) -> bytes:
    pad = (-len(bits)) % 8
    if pad:
        bits = np.concatenate([bits, np.zeros(pad, dtype=np.uint8)])
    arr = np.packbits(bits).tobytes()
    return arr

def read_bits_from_frame(img, mask, need_bits, bit_idx):
    H, W, _ = img.shape
    B = img[:,:,0]  # Blue channel
    flat_B = B.reshape(-1)
    flat_mask = (mask.reshape(-1) == 255)
    idxs = np.nonzero(flat_mask)[0]
    capacity = idxs.shape[0]

    remain = need_bits - bit_idx
    take = min(capacity, remain)
    if take > 0:
        grabbed = flat_B[idxs[:take]] & 1
        return grabbed, bit_idx + take, capacity
    return np.array([], dtype=np.uint8), bit_idx, capacity

def main():
    ap = argparse.ArgumentParser(description="Extract message bits using masks (blue-channel LSB)")
    ap.add_argument("--frames_dir", required=True, help="Directory of modified frames (PNG)")
    ap.add_argument("--masks_dir", required=True, help="Masks directory used during embedding")
    ap.add_argument("--out_file", required=True, help="Output file path for reconstructed encrypted message")
    args = ap.parse_args()

    frame_names = sorted([n for n in os.listdir(args.frames_dir) if n.lower().endswith(".png")])
    mask_names = sorted([n for n in os.listdir(args.masks_dir) if n.lower().endswith(".png")])

    if len(frame_names) != len(mask_names):
        print(f"WARNING: frame count ({len(frame_names)}) != mask count ({len(mask_names)}). Proceeding by sorted order.")

    # First, read the first 32 bits to know payload length
    need_bits = 32
    bit_idx = 0
    header_bits = []

    for fn, mn in tqdm(list(zip(frame_names, mask_names)), desc="Reading header"):
        if bit_idx >= need_bits:
            break
        fp = os.path.join(args.frames_dir, fn)
        mp = os.path.join(args.masks_dir, mn)
        img = cv2.imread(fp, cv2.IMREAD_COLOR)
        mask = cv2.imread(mp, cv2.IMREAD_GRAYSCALE)
        if img is None or mask is None:
            continue
        grabbed, bit_idx, _ = read_bits_from_frame(img, mask, need_bits, bit_idx)
        if grabbed.size:
            header_bits.append(grabbed)

    if bit_idx < need_bits:
        raise SystemExit(f"ERROR: Not enough capacity to read header. Read {bit_idx}/32 bits.")

    header_bits = np.concatenate(header_bits)
    header_bytes = np.frombuffer(np.packbits(header_bits), dtype=np.uint8)
    # 4 bytes big-endian length
    payload_len = (int(header_bytes[0])<<24) | (int(header_bytes[1])<<16) | (int(header_bytes[2])<<8) | int(header_bytes[3])

    # Now read the payload bits
    payload_bits_needed = payload_len * 8
    total_needed = 32 + payload_bits_needed
    bit_idx = 0
    all_bits = []

    for fn, mn in tqdm(list(zip(frame_names, mask_names)), desc="Reading payload"):
        if bit_idx >= total_needed:
            break
        fp = os.path.join(args.frames_dir, fn)
        mp = os.path.join(args.masks_dir, mn)
        img = cv2.imread(fp, cv2.IMREAD_COLOR)
        mask = cv2.imread(mp, cv2.IMREAD_GRAYSCALE)
        if img is None or mask is None:
            continue
        grabbed, bit_idx2, _ = read_bits_from_frame(img, mask, total_needed, bit_idx)
        if grabbed.size:
            all_bits.append(grabbed)
        bit_idx = bit_idx2

    if bit_idx < total_needed:
        raise SystemExit(f"ERROR: Not enough capacity. Read {bit_idx}/{total_needed} bits.")

    all_bits = np.concatenate(all_bits)
    # strip header bits
    payload_bits = all_bits[32:32+payload_bits_needed]
    payload = bits_to_bytes(payload_bits)

    with open(args.out_file, "wb") as f:
        f.write(payload)
    print(f"Wrote reconstructed encrypted message to: {args.out_file} (length {payload_len} bytes)")

if __name__ == "__main__":
    main()
