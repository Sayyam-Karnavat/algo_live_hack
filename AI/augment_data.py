import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = "0"
import numpy as np
from tensorflow.keras.preprocessing.image import ImageDataGenerator, load_img, img_to_array, save_img

# Constants
INPUT_DIR = "dataset/known_faces"
OUTPUT_DIR = "dataset/augmented_faces"
NUM_AUGMENTATIONS = 15  # Number of augmented images per original image
IMG_HEIGHT, IMG_WIDTH = 224, 224  # Target image size

# Create output directory if it doesn't exist
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Define data augmentation parameters
datagen = ImageDataGenerator(
    rescale=1./255,  # Normalize pixel values
    rotation_range=15,  # ±15 degrees rotation
    width_shift_range=0.1,  # ±10% horizontal shift
    height_shift_range=0.1,  # ±10% vertical shift
    shear_range=0.2,  # ±20% shear
    zoom_range=[0.8, 1.2],  # Zoom in/out between 80% and 120%
    horizontal_flip=True,  # Random horizontal flip
    vertical_flip=True,  # Random vertical flip
    brightness_range=[0.8, 1.2],  # Brightness adjustment
    channel_shift_range=10.0,  # Mild contrast adjustment via channel shift
    fill_mode='nearest'  # Fill mode for transformed pixels
)

# Function to augment and save images
import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = "0"
import numpy as np
from tensorflow.keras.preprocessing.image import ImageDataGenerator, load_img, img_to_array, save_img

# Constants
INPUT_DIR = "dataset/known_faces"
OUTPUT_DIR = "dataset/augmented_faces"
NUM_AUGMENTATIONS = 15  # Number of augmented images per original image
IMG_HEIGHT, IMG_WIDTH = 224, 224  # Target image size

# Create output directory if it doesn't exist
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
    print(f"Created output directory: {OUTPUT_DIR}")

# Define data augmentation parameters
datagen = ImageDataGenerator(
    rescale=1./255,  # Normalize pixel values
    rotation_range=15,  # ±15 degrees rotation
    width_shift_range=0.1,  # ±10% horizontal shift
    height_shift_range=0.1,  # ±10% vertical shift
    shear_range=0.2,  # ±20% shear
    zoom_range=[0.8, 1.2],  # Zoom in/out between 80% and 120%
    horizontal_flip=True,  # Random horizontal flip
    vertical_flip=False,  # Turn off vertical flip for faces (not natural)
    brightness_range=[0.8, 1.2],  # Brightness adjustment
    channel_shift_range=10.0,  # Mild contrast adjustment via channel shift
    fill_mode='nearest'  # Fill mode for transformed pixels
)

# Function to augment and save images
def augment_images():
    # Check if input directory exists
    if not os.path.exists(INPUT_DIR):
        print(f"Error: Input directory '{INPUT_DIR}' does not exist!")
        return
    
    # Get list of image files
    image_files = [f for f in os.listdir(INPUT_DIR) 
                   if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff'))]
    
    if not image_files:
        print(f"No image files found in {INPUT_DIR}")
        return
    
    print(f"Found {len(image_files)} images to augment")
    
    total_generated = 0
    
    for image_filename in image_files:
        try:
            # Create full path using os.path.join for cross-platform compatibility
            full_path = os.path.join(INPUT_DIR, image_filename)
            print(f"Processing: {image_filename}")
            
            # Extract filename without extension for naming augmented images
            filename_without_ext = os.path.splitext(image_filename)[0]
            
            # Load and preprocess image
            img = load_img(full_path, target_size=(IMG_HEIGHT, IMG_WIDTH))
            img_array = img_to_array(img)
            img_array = np.expand_dims(img_array, axis=0)
            
            # Generate augmented images
            i = 0
            for batch in datagen.flow(
                img_array,
                batch_size=1,
                save_to_dir=OUTPUT_DIR,
                save_prefix=f"aug_{filename_without_ext}_",
                save_format='jpg'
            ):
                i += 1
                total_generated += 1
                
                # Stop after generating desired number of augmentations
                if i >= NUM_AUGMENTATIONS:
                    break
            
            print(f"  Generated {i} augmented images for {image_filename}")
            
        except Exception as e:
            print(f"Error processing {image_filename}: {str(e)}")
            continue
    
    print(f"\nAugmentation complete!")
    print(f"Total original images: {len(image_files)}")
    print(f"Total augmented images generated: {total_generated}")
    print(f"Augmented images saved in: {OUTPUT_DIR}")


if __name__ == "__main__":
    augment_images()

    print(f"Augmentation complete. Augmented images saved in {OUTPUT_DIR}")