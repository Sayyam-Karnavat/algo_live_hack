import cv2
import numpy as np

def generate_key_matrix(shape, key):
    """Generate a key matrix for XOR encryption using a seed."""
    np.random.seed(key)
    return np.random.randint(0, 256, size=shape, dtype=np.uint8)

def encrypt_image(image, key):
    """Encrypt the image using XOR with a key-based matrix."""
    key_matrix = generate_key_matrix(image.shape, key)
    encrypted = cv2.bitwise_xor(image, key_matrix)
    return encrypted

def decrypt_image(encrypted_image, key):
    """Decrypt the image using XOR with the same key-based matrix."""
    key_matrix = generate_key_matrix(encrypted_image.shape, key)
    decrypted = cv2.bitwise_xor(encrypted_image, key_matrix)
    return decrypted

def main():
    # Load the image
    image_path = 'washing.jpg'  # Replace with your image path
    original_image = cv2.imread(image_path)
    
    if original_image is None:
        print("Error: Could not load the image. Please check the file path.")
        return

    # Define the encryption key (must be an integer for np.random.seed)
    key = 12345  # You can change this key (keep it secret for security)

    # Encrypt the image
    encrypted_image = encrypt_image(original_image, key)
    
    # Decrypt the image
    decrypted_image = decrypt_image(encrypted_image, key)

    # Display the images
    cv2.imshow('Original Image', original_image)
    cv2.imshow('Encrypted Image', encrypted_image)
    cv2.imshow('Decrypted Image', decrypted_image)
    
    # Save the encrypted image (optional, retains image format)
    cv2.imwrite('encrypted_image.png', encrypted_image)
    
    # Wait for a key press and close windows
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()