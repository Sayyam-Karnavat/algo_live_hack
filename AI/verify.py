import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = "0"
import tensorflow as tf
import numpy as np

# Constants
MODEL_PATH = "face_recognition.keras"
IMAGE_SHAPE = (224, 224, 3)
CLASS_NAMES = ["John", "Grace", "Lily", "Michelle", "Sebastin"]  # Maps class index to employee name
CONFIDENCE_THRESHOLD = 0.99  # 98% confidence threshold

def load_and_preprocess_image(image_path):
    """Load and preprocess an image for inference."""
    try:
        # Read and decode image
        img = tf.io.read_file(image_path)
        img = tf.image.decode_image(img, channels=3, expand_animations=False)
        img = tf.image.resize(img, [IMAGE_SHAPE[0], IMAGE_SHAPE[1]])
        img = img / 255.0  # Normalize
        img = tf.expand_dims(img, axis=0)  # Add batch dimension: (1, 224, 224, 3)
        return img
    except Exception as e:
        raise Exception(f"Error loading image {image_path}: {str(e)}")

def predict_employee(image_path, model):
    """Predict employee name from an image."""
    try:
        # Preprocess image
        img = load_and_preprocess_image(image_path)
        # Run prediction
        predictions = model.predict(img, verbose=0)
        # Get predicted class and confidence
        predicted_class = np.argmax(predictions[0])
        confidence = predictions[0][predicted_class]
        # Map class to employee name
        if confidence >= CONFIDENCE_THRESHOLD:
            predicted_employee = CLASS_NAMES[predicted_class]
        else:
            predicted_employee = "unknown"
        return predicted_employee, confidence * 100  # Confidence as percentage
    except Exception as e:
        raise Exception(f"Error during prediction: {str(e)}")

def main(image_path):
    """Main function to run inference."""
    # Load model
    try:
        model = tf.keras.models.load_model(MODEL_PATH)
    except Exception as e:
        print(f"Error loading model: {e}")
        return

    # Verify image file exists
    if not os.path.exists(image_path):
        print(f"Error: Image file '{image_path}' not found.")
        return

    # Run prediction
    try:
        employee, confidence = predict_employee(image_path, model)
        print(f"Predicted Employee: {employee}")
        print(f"Confidence: {confidence:.2f}%")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Example usage: replace with your test image path
    test_image_path = "dataset/augmented_faces/aug_john__0_1817.jpg"
    # test_image_path = "dataset/unknown_faces/unknown3.jpg"
    main(test_image_path)