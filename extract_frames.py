import cv2
import os

def extract_frames_from_video(video_path, output_folder, frame_interval=1):
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Capture the video
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print("Error: Could not open video file.")
        return

    frame_count = 0
    saved_frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % frame_interval == 0:
            frame_path = os.path.join(output_folder, f"frame_{saved_frame_count:04d}.jpg")
            cv2.imwrite(frame_path, frame)
            print(f"Extracted frame {frame_count} and saved as {frame_path}.")
            saved_frame_count += 1

        frame_count += 1

    cap.release()
    print(f"✅ Total {saved_frame_count} frames extracted and saved in {output_folder}.")

# ✅ Use raw strings for Windows paths
video_path = r"C:\Users\KANISHK\Desktop\Steganography-PJT-main\Steganography\Bali.MOV"
output_folder = r"C:\Users\KANISHK\Desktop\Steganography-PJT-main\Steganography\output_frames"

# Run the frame extraction
extract_frames_from_video(video_path, output_folder)
