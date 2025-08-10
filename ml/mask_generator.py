#!/usr/bin/env python3
"""
mask_generator.py — Path 1 (Content-aware embedding)
Creates per-frame binary masks highlighting textured and/or moving regions.
Now robust to mixed frame sizes.
"""
import os
import cv2
import argparse
import numpy as np
from tqdm import tqdm

def ensure_dir(p):
    os.makedirs(p, exist_ok=True)

def score_frame(gray, prev_gray=None, alpha_motion=0.5, resize_prev=True):
    # Texture score via Laplacian magnitude
    lap = cv2.Laplacian(gray, cv2.CV_32F, ksize=3)
    tex = np.abs(lap)

    # Motion score via frame difference
    if prev_gray is None:
        mot = np.zeros_like(gray, dtype=np.float32)
    else:
        # If sizes differ, either resize prev or skip motion
        if prev_gray.shape != gray.shape:
            if resize_prev:
                prev_gray = cv2.resize(prev_gray, (gray.shape[1], gray.shape[0]), interpolation=cv2.INTER_AREA)
            else:
                prev_gray = None
        if prev_gray is None:
            mot = np.zeros_like(gray, dtype=np.float32)
        else:
            mot = cv2.absdiff(gray, prev_gray).astype(np.float32)

    # Normalize each to [0,1]
    def norm01(x):
        x = x - x.min()
        d = x.max() - x.min()
        return x / (d + 1e-8)

    tex_n = norm01(tex)
    mot_n = norm01(mot)
    score = tex_n * (1.0 - alpha_motion) + mot_n * alpha_motion
    return score

def mask_from_score(score, keep_ratio=0.25, dilate=1):
    # Keep top "keep_ratio" fraction of pixels
    thresh_val = np.quantile(score, 1.0 - keep_ratio)
    mask = (score >= thresh_val).astype(np.uint8) * 255
    if dilate > 0:
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * dilate + 1, 2 * dilate + 1))
        mask = cv2.dilate(mask, k, iterations=1)
    return mask

def main():
    ap = argparse.ArgumentParser(description="Generate content-aware masks for frames")
    ap.add_argument("--frames_dir", required=True, help="Input frames folder (e.g., output_frames)")
    ap.add_argument("--out_dir", required=True, help="Output masks folder (will be created)")
    ap.add_argument("--keep_ratio", type=float, default=0.25, help="Fraction of pixels to keep in mask (0..1)")
    ap.add_argument("--alpha_motion", type=float, default=0.5, help="Weight for motion vs texture (0..1)")
    ap.add_argument("--dilate", type=int, default=1, help="Dilate radius (pixels) to slightly expand mask")
    ap.add_argument("--no_resize_prev", action="store_true",
                    help="If set, do NOT resize previous frame; motion becomes zero when sizes differ.")
    args = ap.parse_args()

    ensure_dir(args.out_dir)

    names = sorted([n for n in os.listdir(args.frames_dir)
                    if n.lower().endswith((".png", ".jpg", ".jpeg"))])
    prev_gray = None
    for n in tqdm(names, desc="Generating masks"):
        p = os.path.join(args.frames_dir, n)
        img = cv2.imread(p, cv2.IMREAD_COLOR)
        if img is None:
            # Skip unreadable files
            continue
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
        score = score_frame(gray, prev_gray, alpha_motion=args.alpha_motion,
                            resize_prev=(not args.no_resize_prev))
        mask = mask_from_score(score, keep_ratio=args.keep_ratio, dilate=args.dilate)
        outp = os.path.join(args.out_dir, os.path.splitext(n)[0] + "_mask.png")
        cv2.imwrite(outp, mask)
        prev_gray = gray
    print(f"Saved masks to: {args.out_dir}")

if __name__ == "__main__":
    main()
