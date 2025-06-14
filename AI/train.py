import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = "0"
import tensorflow as tf
from tensorflow.keras import layers
import glob

# Constants
IMAGE_SHAPE = (224, 224, 3)
NUM_CLASSES = 5
IMAGES_DIR = "dataset/augmented_faces"
BATCH_SIZE = 4
CLASS_NAMES = ["grace", "john", "lily", "michelle", "sebastin"]  # Lowercase for matching

def load_and_preprocess(file_path):
    """Load and preprocess image, assign label based on file path."""
    # Read and decode image
    img = tf.io.read_file(file_path)
    img = tf.image.decode_jpeg(img, channels=3)
    img = tf.image.resize(img, (IMAGE_SHAPE[0], IMAGE_SHAPE[1]))
    img = img / 255.0

    # Convert file path to lowercase for label assignment
    file_path_lower = tf.strings.lower(file_path)
    
    # Assign label based on employee name in path
    label = tf.cond(
        tf.strings.regex_full_match(file_path_lower, ".*john.*"),
        lambda: tf.constant(0, dtype=tf.int32),
        lambda: tf.cond(
            tf.strings.regex_full_match(file_path_lower, ".*grace.*"),
            lambda: tf.constant(1, dtype=tf.int32),
            lambda: tf.cond(
                tf.strings.regex_full_match(file_path_lower, ".*lily.*"),
                lambda: tf.constant(2, dtype=tf.int32),
                lambda: tf.cond(
                    tf.strings.regex_full_match(file_path_lower, ".*michelle.*"),
                    lambda: tf.constant(3, dtype=tf.int32),
                    lambda: tf.constant(4, dtype=tf.int32)  # sebastin
                )
            )
        )
    )
    
    return img, label

def create_model():
    """Create CNN model for face recognition."""
    model = tf.keras.models.Sequential([
        layers.Input(shape=IMAGE_SHAPE),
        layers.Conv2D(64, (3, 3), padding="valid", activation="relu"),
        layers.Conv2D(64, (2, 2), padding="valid", activation="relu"),
        layers.MaxPool2D((2, 2)),
        layers.Conv2D(32, (3, 3), padding="valid", activation="relu"),
        layers.Conv2D(32, (2, 2), padding="valid", activation="relu"),
        layers.MaxPool2D((2, 2)),
        layers.Conv2D(16, (3, 3), padding="valid", activation="relu"),
        layers.Conv2D(16, (2, 2), padding="valid", activation="relu"),
        layers.MaxPool2D((2, 2)),
        layers.Flatten(),  # Flatten to 1D for Dense layers
        layers.Dense(64, activation="relu"),
        layers.Dense(32, activation="relu"),
        layers.Dense(NUM_CLASSES, activation="softmax")
    ])
    return model

if __name__ == "__main__":
    # Collect image paths from subfolders
    image_paths = []
    for ext in ['*.jpg', '*.png']:
        image_paths.extend(glob.glob(os.path.join(IMAGES_DIR, '**', ext), recursive=True))
    
    if not image_paths:
        raise FileNotFoundError(f"No images found in {IMAGES_DIR}")
    
    # Create dataset
    dataset = tf.data.Dataset.from_tensor_slices(image_paths)
    dataset = dataset.shuffle(buffer_size=len(image_paths))  # Shuffle for better training
    dataset = dataset.map(load_and_preprocess, num_parallel_calls=tf.data.AUTOTUNE)
    dataset = dataset.batch(BATCH_SIZE).prefetch(tf.data.AUTOTUNE)

    # Create and compile model
    model = create_model()
    model.compile(
        optimizer="adam",
        loss="sparse_categorical_crossentropy",
        metrics=['accuracy']
    )

    # Define callbacks
    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor='accuracy',
            restore_best_weights=True,
            patience=10,
            mode = "max"
        )
    ]

    # Train model
    model.fit(
        dataset,
        epochs=10,
        callbacks=callbacks
    )

    # Save model
    model.save("face_recognition.keras")
    print("Model saved to face_recognition.keras")