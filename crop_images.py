import cv2
import os

HEADER_HEIGHT = 250  
FOOTER_HEIGHT = 260  

def preprocess_app_image(image):

    if image.shape[0] <= HEADER_HEIGHT + FOOTER_HEIGHT:
        print("Warning: Image is too small to crop with the specified header/footer sizes.")
        return image
    return image[HEADER_HEIGHT:-FOOTER_HEIGHT, :]

def crop_images_in_directory(input_dir, output_dir):
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    for filename in os.listdir(input_dir):

        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif')):
            input_path = os.path.join(input_dir, filename)
            image = cv2.imread(input_path)
            if image is None:
                print(f"Error reading {input_path}. Skipping this file.")
                continue

            cropped_image = preprocess_app_image(image)

            output_path = os.path.join(output_dir, filename)
            cv2.imwrite(output_path, cropped_image)
            print(f"Processed and saved: {output_path}")

if __name__ == "__main__":
    input_directory = "path/to/your/input_directory"   
    output_directory = "path/to/your/output_directory"  

    crop_images_in_directory(input_directory, output_directory)
