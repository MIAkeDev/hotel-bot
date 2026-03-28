import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
RECEPTIONIST_NUMBER = os.getenv("RECEPTIONIST_NUMBER")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
