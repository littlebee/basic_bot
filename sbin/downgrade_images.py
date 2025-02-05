"""
A python script to downgrade images in a given folder to 640x480 resolution
using cv2.

It saves the downgraded images to a new .png file with the original filename
appended with "_downgraded".
"""

import cv2
import os
import argparse
import numpy as np


def downgrade_image(image_path):
    """Downgrade a single image to 640x480 resolution while maintaining aspect ratio."""
    # Read image
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error loading image: {image_path}")
        return False

    # Calculate new dimensions maintaining aspect ratio
    target_width, target_height = 640, 480
    h, w = img.shape[:2]
    aspect = w / h

    if aspect > target_width / target_height:  # wider than target
        new_w = target_width
        new_h = int(target_width / aspect)
    else:  # taller than target
        new_h = target_height
        new_w = int(target_height * aspect)

    # Resize with calculated dimensions
    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

    # Create blank canvas
    canvas = np.zeros((target_height, target_width, 3), dtype=np.uint8)

    # Calculate positioning
    y_offset = (target_height - new_h) // 2
    x_offset = (target_width - new_w) // 2

    # Place resized image on canvas
    canvas[y_offset : y_offset + new_h, x_offset : x_offset + new_w] = resized

    # Save result
    filename, ext = os.path.splitext(image_path)
    output_path = f"{filename}.480p.png"
    return cv2.imwrite(output_path, canvas)


def main():
    """Process all images in the folder specified via command line argument."""
    parser = argparse.ArgumentParser(
        description="Downgrade images in a folder to 640x480 resolution"
    )
    parser.add_argument("folder_path", help="Path to folder containing images")
    args = parser.parse_args()

    if not os.path.isdir(args.folder_path):
        print("Invalid folder path!")
        return

    image_extensions = (".jpg", ".jpeg", ".png", ".bmp")
    processed = 0

    for filename in os.listdir(args.folder_path):
        if filename.lower().endswith(image_extensions):
            image_path = os.path.join(args.folder_path, filename)
            if downgrade_image(image_path):
                processed += 1
                print(f"Processed: {filename}")

    print(f"\nCompleted! Processed {processed} images.")


if __name__ == "__main__":
    main()
