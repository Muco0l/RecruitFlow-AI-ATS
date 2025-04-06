import os
from dotenv import load_dotenv

load_dotenv() # Load environment variables from a .env file if it exists

# --- General Settings ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESUME_FOLDER = os.path.join(BASE_DIR, "resumes")
DB_PATH = os.path.join(BASE_DIR, "data", "recruitment.db")

# --- Ollama Settings ---
OLLAMA_BASE_URL = "http://localhost:11434" # Default Ollama API URL
# OLLAMA_MODEL = "llama3:latest"  # Or "mistral:latest", etc. Choose the model you have pulled
OLLAMA_MODEL = "llama3.2:latest"  # Using mistral as an example

# --- Recruitment Logic Settings ---
MATCH_THRESHOLD = 75 # Score out of 100 needed to shortlist

# --- Email Settings (IMPORTANT: Use environment variables or a secure method in a real app) ---
# Create a .env file in the root directory (hackathon-recruiter-app/)
# Add these lines to your .env file, replacing with your actual details:
# EMAIL_ADDRESS="your_email@example.com"
# EMAIL_PASSWORD="your_app_password" # Use App Password for Gmail/Outlook etc.
# SMTP_SERVER="smtp.example.com"
# SMTP_PORT=587

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "default_email@example.com") # Fallback default
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "default_password") # Fallback default
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com") # Example for Gmail
SMTP_PORT = int(os.getenv("SMTP_PORT", 587)) # Example for Gmail (TLS)

# --- Ensure necessary folders exist ---
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
os.makedirs(RESUME_FOLDER, exist_ok=True)

print(f"Resume Folder: {RESUME_FOLDER}")
print(f"Database Path: {DB_PATH}")