import os
import pickle
import shutil
from pathlib import Path

from dotenv import load_dotenv
import pandas as pd
from azure.storage.blob import BlobServiceClient
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from backend.formulas import din33466, sac, timedelta_minutes

ENV_STORAGE_KEY = "AZURE_STORAGE_CONNECTION_STRING"
MODEL_CONTAINER_PREFIX = "hikeplanner-model"
# init app, load model from storage
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / ".env"
load_dotenv(env_path, override=True)

print("*** Load Model from Blob Storage ***")
local_model_dir = BASE_DIR / "model"

if ENV_STORAGE_KEY in os.environ:
    azureStorageConnectionString = os.environ[ENV_STORAGE_KEY]
    blob_service_client = BlobServiceClient.from_connection_string(azureStorageConnectionString)

    containers = blob_service_client.list_containers(include_metadata=True)
    suffixes = []
    for container in containers:
        if container.name.startswith(MODEL_CONTAINER_PREFIX):
            try:
                suffixes.append(int(container.name.split("-")[-1]))
            except (ValueError, IndexError):
                continue
    
    if not suffixes:
        print(f"No containers found starting with {MODEL_CONTAINER_PREFIX} and ending with a number.")
    else:
        suffix = max(suffixes)
        model_folder = f"{MODEL_CONTAINER_PREFIX}-{suffix}"
        print(f"using version {model_folder}")

        container_client = blob_service_client.get_container_client(model_folder)
        blob_list = list(container_client.list_blobs())

        # Download all blobs to a clean local folder
        if local_model_dir.exists():
            shutil.rmtree(local_model_dir)
        local_model_dir.mkdir(parents=True, exist_ok=True)
        for blob in blob_list:
            download_file_path = local_model_dir / blob.name
            print(f"downloading blob to {download_file_path.resolve()}")
            with open(file=download_file_path, mode="wb") as download_file:
                download_file.write(container_client.download_blob(blob.name).readall())

else:
    print("CANNOT ACCESS AZURE BLOB STORAGE - Please set AZURE_STORAGE_CONNECTION_STRING.")

gbr_model_path = local_model_dir / "GradientBoostingRegressor.pkl"
linear_model_path = local_model_dir / "LinearRegression.pkl"

if not gbr_model_path.exists() or not linear_model_path.exists():
    print(f"ERROR: Model files not found in {local_model_dir}")

with open(gbr_model_path, 'rb') as fid:
    gradient_model = pickle.load(fid)

with open(linear_model_path, 'rb') as fid:
    linear_model = pickle.load(fid)

print("\n*** Flask Backend ***")
# Use absolute paths for static files to work in both local and Docker environments
frontend_path = (BASE_DIR / "frontend" / "build").resolve()
app = Flask(__name__, static_url_path='/', static_folder=str(frontend_path))
cors = CORS(app)

@app.route("/")
def indexPage():
     return send_file(str(frontend_path / "index.html"))  
@app.route("/api/predict")
def hello_world():
    downhill = request.args.get('downhill', default = 0, type = int)
    uphill = request.args.get('uphill', default = 0, type = int)
    length = request.args.get('length', default = 0, type = int)

    demoinput = [[downhill,uphill,length,0]]
    demodf = pd.DataFrame(columns=['downhill', 'uphill', 'length_3d', 'max_elevation'], data=demoinput)
    gradient_prediction = gradient_model.predict(demodf)[0]
    linear_prediction = linear_model.predict(demodf)[0]

    return jsonify({
        'time': timedelta_minutes(gradient_prediction),
        'linear': timedelta_minutes(linear_prediction),
        'din33466': timedelta_minutes(din33466(uphill=uphill, downhill=downhill, distance=length)),
        'sac': timedelta_minutes(sac(uphill=uphill, downhill=downhill, distance=length))
        })
