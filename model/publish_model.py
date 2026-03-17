import os
from pathlib import Path
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

# Konfiguration
MODEL_DIR = Path(__file__).resolve().parent
BASE_DIR = MODEL_DIR.parent
MODEL_FILES = ["GradientBoostingRegressor.pkl", "LinearRegression.pkl"]
MODEL_CONTAINER_PREFIX = "hikeplanner-model"

def publish_model():
    # 1. .env laden
    env_path = BASE_DIR / ".env"
    load_dotenv(env_path, override=True)
    
    conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    if not conn_str:
        print("FEHLER: AZURE_STORAGE_CONNECTION_STRING nicht in .env gefunden!")
        return

    # 2. Azure Verbindung aufbauen
    blob_service_client = BlobServiceClient.from_connection_string(conn_str)
    
    # 3. Nächste Version finden (z.B. hikeplanner-model-1, -2, ...)
    containers = list(blob_service_client.list_containers())
    max_version = 0
    for c in containers:
        if c.name.startswith(MODEL_CONTAINER_PREFIX):
            try:
                version = int(c.name.split("-")[-1])
                max_version = max(max_version, version)
            except ValueError:
                continue
    
    new_version = max_version + 1
    new_container_name = f"{MODEL_CONTAINER_PREFIX}-{new_version}"
    
    print(f"Erstelle neuen Container: {new_container_name}")
    container_client = blob_service_client.create_container(new_container_name)
    
    # 4. Modelle hochladen
    for model_file in MODEL_FILES:
        local_path = MODEL_DIR / model_file
        if not local_path.exists():
            print(f"WARNUNG: {model_file} nicht in {MODEL_DIR} gefunden! Überspringe...")
            continue
            
        print(f"Lade {model_file} hoch...")
        with open(local_path, "rb") as data:
            container_client.upload_blob(name=model_file, data=data)
            
    print(f"ERFOLG: Modell Version {new_version} wurde veröffentlicht!")

if __name__ == "__main__":
    publish_model()
