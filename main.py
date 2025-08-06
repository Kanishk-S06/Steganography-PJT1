import subprocess
import os
import sys

# Update this if your working directory is different
PROJECT_DIR = r"C:\Users\KANISHK\Desktop\Steganography-PJT-main\Steganography"

os.chdir(PROJECT_DIR)

# List of scripts in order
steps = [
    ("Encryption", "Encryption.py"),
    ("Extract Frames", "extract_frames.py"),
    ("Embed Message", "embed_msg.py"),
    ("Extract Message", "extract_modified_frames.py"),
    ("Decryption", "Decryption.py")
]

def run_script(name, script):
    print(f"\n🔹 Running step: {name}")
    try:
        result = subprocess.run([sys.executable, script], check=True)
        print(f"✅ {name} completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error while running {script}: {e}")
        sys.exit(1)

def main():
    print("🚀 Starting Steganography Pipeline...\n")
    for name, script in steps:
        run_script(name, script)
    print("\n🎉 All steps completed! Check output in your Steganography folder.")

if __name__ == "__main__":
    main()
