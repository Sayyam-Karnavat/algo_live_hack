Facial Recognition Biometric System
This project is a secure biometric verification system that uses AI-powered facial recognition for user registration and login. Users register with a username, password, and photo, triggering an AI training pipeline to recognize their face. The photo is encrypted using XOR-based matrix multiplication and stored in a database, uploaded to Pinata IPFS, and minted as an NFT on the Algorand blockchain. During login, the system verifies the user’s face via AI and double-checks against the decrypted IPFS image. The system complies with the DPDP Act by securely managing and deleting user data.
Setup Instructions
Follow these steps to run the project locally:

Create a Python virtual environment:
python -m venv .venv


Activate the virtual environment:
.venv\Scripts\activate


Run the server:
python server.py


Access the application:

Open your browser and navigate to http://localhost:3333.



Requirements

Python 3.8+
Dependencies: Install required packages using pip install -r requirements.txt (create a requirements.txt with packages like tensorflow, flask, deepface, etc.).
Pinata IPFS account for image storage.
Algorand blockchain setup for NFT minting.

Notes

Ensure the dataset (dataset/augmented_faces) is structured with subfolders for each employee.
The model (face_recognition.keras) must be present for inference.
For blockchain and IPFS integration, configure API keys and credentials as per your setup.

