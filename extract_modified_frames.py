import cv2
import os
import numpy as np

# Function to extract the encrypted message from a frame
def extract_message_from_frame(frame, bits_needed):
    frame_array = np.array(frame)
    extracted_bits = []

    for row in range(frame_array.shape[0]):
        for col in range(frame_array.shape[1]):
            if len(extracted_bits) < bits_needed:
                b = frame_array[row, col][0]  # Extract the blue channel
                extracted_bits.append(str(b & 0x01))
            else:
                break
        if len(extracted_bits) >= bits_needed:
            break

    # Ensure that the number of bits is a multiple of 8
    num_full_bytes = len(extracted_bits) // 8
    extracted_bits = extracted_bits[:num_full_bytes * 8]

    message_bytes = [int(''.join(extracted_bits[i:i+8]), 2) for i in range(0, len(extracted_bits), 8)]
    return bytes(message_bytes).decode('utf-8', errors='ignore')

# Function to extract the encrypted message from all frames
def extract_message_from_video(frames, message_length):
    extracted_message = ''
    bits_needed = message_length * 8  # Total bits to extract

    for frame in frames:
        if len(extracted_message) < message_length:
            remaining_bits = bits_needed - len(extracted_message) * 8
            chunk = extract_message_from_frame(frame, remaining_bits)
            extracted_message += chunk
            print(f"Extracted chunk from frame: {chunk}")
        else:
            break

    # Truncate in case of over-extraction
    extracted_message = extracted_message[:message_length]
    return extracted_message

# Function to save the extracted message to a file
def save_extracted_message(message, filename):
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(message)
    print(f"Extracted message saved to {filename}")

# Example usage
if __name__ == "__main__":
    frame_folder = r"C:\Users\KANISHK\Desktop\Steganography-PJT-main\Steganography\output_frames_with_message"
    extracted_message_filename = r"C:\Users\KANISHK\Desktop\Steganography-PJT-main\Steganography\extracted_encrypted_message.txt"
    original_message_filename = r"C:\Users\KANISHK\Desktop\Steganography-PJT-main\Steganography\encrypted_message.txt"


    # Load the frames as PNG images
    frames = []
    for filename in sorted(os.listdir(frame_folder)):
        if filename.lower().endswith('.png'):
            frame_path = os.path.join(frame_folder, filename)
            frame = cv2.imread(frame_path)
            if frame is not None:
                frames.append(frame)
            else:
                print(f"Warning: Unable to read frame {filename}.")

    if not frames:
        raise ValueError("No frames found to extract the message.")

    print(f"Total frames loaded: {len(frames)}")

    # Read the length of the original message
    with open(original_message_filename, 'r', encoding='utf-8') as file:
        original_message = file.read().strip()

    message_length = len(original_message)
    print(f"Original message length: {message_length} characters.")

    # Extract the message from the video frames
    extracted_message = extract_message_from_video(frames, message_length)
    print(f"Extracted Message: {extracted_message}")

    # Save the extracted message to a file
    save_extracted_message(extracted_message, extracted_message_filename)