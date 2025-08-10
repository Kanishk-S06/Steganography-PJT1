# enroll_biometric.py
import argparse, os
from bio_fuzzy import enroll_helper, save_helper

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--face", required=True, help="Path to your enrollment face image")
    ap.add_argument("--out", default="helper.json", help="Where to save helper.json")
    args = ap.parse_args()

    helper = enroll_helper(args.face)     # generates proj seed, secret R, W, hR
    save_helper(helper, args.out)
    print(f"✅ Enrollment complete. Helper saved to {os.path.abspath(args.out)}")
