import cv2
import numpy as np
import os

def remove_black_pixels_and_neighbors(image, threshold=50, dilation_kernel_size=5, dilation_iterations=2):
    """Image se black pixels aur unke neighbors hata kar white replace karta hai."""
    mask = cv2.inRange(image, (0, 0, 0), (threshold, threshold, threshold))  
    kernel = np.ones((dilation_kernel_size, dilation_kernel_size), np.uint8)  
    mask_dilated = cv2.dilate(mask, kernel, iterations=dilation_iterations)  
    
    image[mask_dilated > 0] = (255, 255, 255)  
    return image

def process_images_in_directory(input_dir, output_dir):
    """Diye gaye directory ke sab images process kar ke output_dir mein save karta hai."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif')):
            input_path = os.path.join(input_dir, filename)
            image = cv2.imread(input_path)
            if image is None:
                print(f"Error reading {input_path}. Skipping this file.")
                continue
            
            processed_image = remove_black_pixels_and_neighbors(image)
            output_path = os.path.join(output_dir, filename)
            cv2.imwrite(output_path, processed_image)
            print(f"Processed and saved: {output_path}")

if __name__ == "__main__":
    input_directory = "sample/mushaf"   
    output_directory = "/home/infiniti/Tarteel/app/QuranTajweedComparision-/sample/mushaf without black"  

    process_images_in_directory(input_directory, output_directory)
