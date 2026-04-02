import os
import pickle
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split

# Konfiguration
MODEL_DIR = Path(__file__).resolve().parent
BASE_DIR = MODEL_DIR.parent
MODEL_FILES = {
    "GradientBoostingRegressor": "GradientBoostingRegressor.pkl",
    "LinearRegression": "LinearRegression.pkl",
}

def train_model():
    # 1. .env laden
    env_path = BASE_DIR / ".env"
    load_dotenv(env_path, override=True)
    
    mongo_uri = os.getenv("MONGO_DB_CONNECTION_STRING")
    if not mongo_uri:
        print("FEHLER: MONGO_DB_CONNECTION_STRING nicht in Umgebungsvariablen gefunden!")
        return

    # 2. Daten aus MongoDB laden
    print("Lade Daten aus MongoDB...")
    client = MongoClient(mongo_uri)
    db = client["tracks"]
    collection = db["tracks"]
    
    cursor = collection.find({}, {
        "downhill": 1, 
        "uphill": 1, 
        "length_3d": 1, 
        "max_elevation": 1, 
        "moving_time": 1,
        "_id": 0
    })
    
    df = pd.DataFrame(list(cursor))
    
    if df.empty:
        print("FEHLER: Keine Daten in MongoDB gefunden! Trainieren nicht möglich.")
        return
        
    print(f"{len(df)} Tracks geladen.")

    # 3. Vorbereitung der Features und Target
    # Wir filtern extrem kleine Werte oder Ausreißer (einfache Validierung)
    df = df[(df['moving_time'] > 60) & (df['length_3d'] > 100)]
    df = df.dropna(subset=['downhill', 'uphill', 'length_3d', 'max_elevation', 'moving_time'])

    X = df[['downhill', 'uphill', 'length_3d', 'max_elevation']]
    y = df['moving_time']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 4. Modelle trainieren
    models = {
        "GradientBoostingRegressor": GradientBoostingRegressor(n_estimators=100, random_state=42),
        "LinearRegression": LinearRegression()
    }
    
    for name, model in models.items():
        print(f"Trainiere {name}...")
        model.fit(X_train, y_train)
        
        # Validierung
        y_pred = model.predict(X_test)
        score = r2_score(y_test, y_pred)
        print(f"{name} R2 Score: {score:.4f}")
        
        # Speichern
        model_path = MODEL_DIR / MODEL_FILES[name]
        with open(model_path, "wb") as f:
            pickle.dump(model, f)
        print(f"Modell gespeichert unter: {model_path}")

    print("ERFOLG: Alle Modelle wurden trainiert und gespeichert!")

if __name__ == "__main__":
    train_model()
