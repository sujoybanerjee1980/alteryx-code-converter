import os
import vertexai 
import json
from openai import AzureOpenAI as Agenai
from dotenv import load_dotenv
from cryptography.fernet import Fernet

load_dotenv()

with open("config.json", "r") as config_file:
    config = json.load(config_file)

def decrypts(var_name,cipher):
    value=os.getenv(var_name)
    if value is None:
        raise ValueError(f"Missing environment variable:{var_name}")
    value=value.strip().strip('"').strip("'")
    return cipher.decrypt(str(value).encode()).decode()

def get_llm(selected: str):
    with open("secret.key","rb") as key_file:
        key=key_file.read()
    cipher=Fernet(key)

    if selected == "azure":  # Azure
        # API_KEY = config["api_key"]
        # API_BASE = config["azure_endpoint"]
        # API_VERSION = config["api_version"]
        API_BASE=decrypts("AZURE_OPENAI_ENDPOINT",cipher)
        API_KEY=decrypts("AZURE_OPENAI_API_KEY",cipher)
        API_VERSION=decrypts("AZURE_OPENAI_API_VERSION",cipher)

        llm_client = Agenai(api_key=API_KEY, azure_endpoint=API_BASE, api_version=API_VERSION)
        
        return llm_client
        
    elif selected == "google":  # Google

        PROJECT_ID = "" # need to be filled
        KEY_FILE_PATH = r"" # need to be filled
        
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = KEY_FILE_PATH
        vertexai.init(project=PROJECT_ID, location="") # location to be given
    else:
        raise ValueError("Invalid selection for LLM.")