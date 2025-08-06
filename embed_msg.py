import cv2
import os
import numpy as np

# Function to read the encrypted message from the file
def load_encrypted_message(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        return file.read().strip()

# Function to embed the encrypted message into the frame
def embed_message_in_frame(frame, message_chunk):
    message_bytes = message_chunk.encode('utf-8')
    frame_array = np.array(frame)

    index = 0
    for byte in message_bytes:
        for bit in range(8):
            # Calculate the row and column based on the current bit index
            bit_index = index * 8 + bit
            row = bit_index // frame_array.shape[1]
            col = bit_index % frame_array.shape[1]

            if row >= frame_array.shape[0]:
                # If we've reached the end of the frame, stop embedding
                return frame_array

            # Embed one bit into the blue channel LSB
            frame_array[row, col][0] = (frame_array[row, col][0] & 0xFE) | ((byte >> (7 - bit)) & 0x01)

        index += 1

    return frame_array

# Function to embed the message into the frames
def embed_message_in_video(frames, message, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Created output folder: {output_folder}")

    # Calculate how many characters can be embedded per frame
    chars_per_frame = (frames[0].shape[0] * frames[0].shape[1]) // 8
    total_frames_needed = (len(message) + chars_per_frame - 1) // chars_per_frame

    if total_frames_needed > len(frames):
        raise ValueError("Not enough frames to embed the entire message.")

    frame_count = 0

    for frame in frames:
        if frame_count * chars_per_frame < len(message):
            # Determine the chunk of the message to embed in this frame
            chunk = message[frame_count * chars_per_frame : (frame_count + 1) * chars_per_frame]
            modified_frame = embed_message_in_frame(frame, chunk)
            modified_frame_path = os.path.join(output_folder, f"modified_frame_{frame_count:04d}.png")
            cv2.imwrite(modified_frame_path, modified_frame)
            print(f"Embedded chunk into frame {frame_count} and saved as {modified_frame_path}.")
        else:
            # Save the remaining frames without modification
            modified_frame_path = os.path.join(output_folder, f"modified_frame_{frame_count:04d}.png")
            cv2.imwrite(modified_frame_path, frame)
            print(f"Saved remaining frame {frame_count} without modification as {modified_frame_path}.")

        frame_count += 1

    print(f"Message embedding complete. Total frames processed: {frame_count}")

# Function to combine frames into a video
def combine_frames_to_video(frames_folder, output_video_path, frame_rate=30):
    # Get sorted list of frame filenames
    frame_files = sorted([
        f for f in os.listdir(frames_folder) 
        if f.lower().endswith('.png')
    ])

    if not frame_files:
        raise ValueError("No frames found to create the video.")

    # Read the first frame to get the frame size
    first_frame_path = os.path.join(frames_folder, frame_files[0])
    first_frame = cv2.imread(first_frame_path)
    if first_frame is None:
        raise ValueError(f"Unable to read the first frame: {first_frame_path}")

    height, width, layers = first_frame.shape
    frame_size = (width, height)

    # Define the codec and create VideoWriter object
    # 'mp4v' is a commonly used codec for MP4 files
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video_path, fourcc, frame_rate, frame_size)

    print(f"Combining frames into video: {output_video_path}")
    print(f"Frame size: {frame_size}, Frame rate: {frame_rate} FPS")

    for filename in frame_files:
        frame_path = os.path.join(frames_folder, filename)
        frame = cv2.imread(frame_path)
        if frame is None:
            print(f"Warning: Unable to read frame {filename}. Skipping.")
            continue

        # Verify frame size consistency
        if frame.shape[1] != width or frame.shape[0] != height:
            print(f"Warning: Frame {filename} has a different size. Resizing to match the first frame.")
            frame = cv2.resize(frame, frame_size)

        out.write(frame)
        print(f"Added frame {filename} to video.")

    out.release()
    print(f"Video creation complete: {output_video_path}")

# Example usage
if __name__ == "__main__":
    # Paths configuration
    encrypted_message_filename = r"C:\Users\KANISHK\Desktop\Steganography-PJT-main\Steganography\encrypted_message.txt"
    output_frames_folder = r"C:\Users\KANISHK\Desktop\Steganography-PJT-main\Steganography\output_frames_with_message"
    original_frames_folder = r"C:\Users\KANISHK\Desktop\Steganography-PJT-main\Steganography\output_frames"
    output_video_path = r"C:\Users\KANISHK\Desktop\Steganography-PJT-main\Steganography\output_video_with_message.mp4"
    frame_rate = 30 # Adjust as needed

    # Load the encrypted message
    encrypted_message = load_encrypted_message(encrypted_message_filename)
    print(f"Encrypted message loaded. Length: {len(encrypted_message)} characters.")

    # Load the frames as PNG images
    frames = []
    for filename in sorted(os.listdir(original_frames_folder)):
        if filename.lower().endswith('.jpg'):
            frame_path = os.path.join(original_frames_folder, filename)
            frame = cv2.imread(frame_path)
            if frame is not None:
                frames.append(frame)
            else:
                print(f"Warning: Unable to read frame {filename}.")

    if not frames:
        raise ValueError("No frames found to embed the message.")

    print(f"Total frames loaded: {len(frames)}")

    # Optional: Print frame details for debugging
    for idx, frame in enumerate(frames):
        print(f"Frame {idx}: Shape {frame.shape}")

    # Embed the message into the video frames
    embed_message_in_video(frames, encrypted_message, output_frames_folder)

    # Combine the modified frames back into a video
    combine_frames_to_video(
        frames_folder=output_frames_folder,
        output_video_path=output_video_path,
        frame_rate=frame_rate
    )