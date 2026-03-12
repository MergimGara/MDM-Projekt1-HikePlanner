import os
import pickle
import datetime
from pathlib import Path

from dotenv import load_dotenv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sn
from pymongo import MongoClient

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split, RandomizedSearchCV, cross_val_score

# Load Environment
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path, override=True)
mongo_uri = os.getenv("MONGO_DB_CONNECTION_STRING")
if not mongo_uri:
    raise SystemExit("Missing MongoDB URI. Set MONGO_DB_CONNECTION_STRING in .env or in the environment.")
mongo_db = "tracks"
mongo_collection = "tracks"

client = MongoClient(mongo_uri)
db = client[mongo_db]
collection = db[mongo_collection]

# fetch a single document
projection = {"gpx": 0, "url": 0, "bounds": 0, "name": 0}
track = collection.find_one(projection=projection)
if not track:
    raise SystemExit("No tracks found in MongoDB.")

print("\n*** Loading Tracks from MongoDB ***")
chunks = []
batch = []
chunk_size = 2000
cursor = collection.find(projection=projection)
total_loaded = 0
for idx, doc in enumerate(cursor, start=1):
    batch.append(doc)
    total_loaded = idx
    if idx % chunk_size == 0:
        chunks.append(pd.DataFrame(batch))
        print(f"Loaded {idx} tracks...")
        batch.clear()
if batch:
    chunks.append(pd.DataFrame(batch))
    print(f"Loaded {total_loaded} tracks...")

df = pd.concat(chunks, ignore_index=True).set_index("_id")

df['avg_speed'] = df['length_3d']/df['moving_time']
df['difficulty_num'] = df['difficulty'].map(lambda x: int(x[1]) if pd.notnull(x) and len(x) > 1 else 0).astype('int32')

# drop na values
df.dropna()
df = df[df['avg_speed'] < 2] # an avg of > 2m/s is probably not a hiking activity
df = df[df['min_elevation'] > 0]
df = df[df['length_2d'] < 100000]
print(f"{len(df)} tracks processed.")

corr = df.corr(numeric_only=True)

print("\n*** Correlation Matrix ***")
print(corr)
plt.figure(figsize=(10, 8))
sn.heatmap(corr, annot=True, fmt=".2f", annot_kws={"size": 7})
static_dir = Path(__file__).resolve().parent.parent / "frontend" / "static" / "images"
static_dir.mkdir(parents=True, exist_ok=True)
plt.tight_layout()
plt.savefig(static_dir / "heatmap.png", dpi=150)
plt.close()

# Prepare Data
y = df.reset_index()['moving_time']
x = df.reset_index()[['downhill', 'uphill', 'length_3d', 'max_elevation']]

x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.20, random_state=42)

print(f"\n{'*** Models ***':<30} {'R2':>10} {'MSE':>14} {'CV MSE (5-Fold)':>16}")

# 1. Baseline Linear Regression
lr = LinearRegression()
lr.fit(x_train, y_train)
y_pred_lr = lr.predict(x_test)
r2_lr = r2_score(y_test, y_pred_lr)
mse_lr = mean_squared_error(y_test, y_pred_lr)
cv_scores_lr = cross_val_score(lr, x, y, cv=5, scoring='neg_mean_squared_error')
cv_mse_lr = -cv_scores_lr.mean()
print(f"{'Linear Regression':<30} {r2_lr:>10.4f} {mse_lr:>14.2f} {cv_mse_lr:>16.2f}")

# 2. Random Forest Regressor (Alternative Architecture)
rf = RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=-1)
rf.fit(x_train, y_train)
y_pred_rf = rf.predict(x_test)
r2_rf = r2_score(y_test, y_pred_rf)
mse_rf = mean_squared_error(y_test, y_pred_rf)
cv_scores_rf = cross_val_score(rf, x, y, cv=5, scoring='neg_mean_squared_error')
cv_mse_rf = -cv_scores_rf.mean()
print(f"{'Random Forest Regressor':<30} {r2_rf:>10.4f} {mse_rf:>14.2f} {cv_mse_rf:>16.2f}")

# 3. Gradient Boosting Regressor (with Hyperparameter Tuning)
print("\n*** Starting Hyperparameter Tuning for Gradient Boosting ***")
gbr_base = GradientBoostingRegressor(random_state=9000)
param_dist = {
    'n_estimators': [50, 100, 150],
    'learning_rate': [0.01, 0.05, 0.1, 0.2],
    'max_depth': [3, 4, 5],
    'min_samples_split': [2, 5, 10]
}
random_search = RandomizedSearchCV(
    estimator=gbr_base,
    param_distributions=param_dist,
    n_iter=10,
    cv=3,
    scoring='neg_mean_squared_error',
    random_state=42,
    n_jobs=-1
)
random_search.fit(x_train, y_train)

gbr_best = random_search.best_estimator_
print(f"Best parameters found: {random_search.best_params_}")

y_pred_gbr = gbr_best.predict(x_test)
r2_gbr = r2_score(y_test, y_pred_gbr)
mse_gbr = mean_squared_error(y_test, y_pred_gbr)
cv_scores_gbr = cross_val_score(gbr_best, x, y, cv=5, scoring='neg_mean_squared_error')
cv_mse_gbr = -cv_scores_gbr.mean()
print(f"{'Tuned Gradient Boosting':<30} {r2_gbr:>10.4f} {mse_gbr:>14.2f} {cv_mse_gbr:>16.2f}")


def din33466(uphill, downhill, distance):
    km = distance / 1000.0
    vertical = downhill / 500.0 + uphill / 300.0
    horizontal = km / 4.0
    return 3600.0 * (min(vertical, horizontal) / 2 + max(vertical, horizontal))

def sac(uphill, distance):
    km = distance / 1000.0
    return 3600.0 * (uphill/400.0 + km /4.0)

print("\n*** Sample Values ***")
samples = [
    {"downhill": 300, "uphill": 700, "length_3d": 10000, "max_elevation": 1200},
    {"downhill": 600, "uphill": 900, "length_3d": 15000, "max_elevation": 2100},
    {"downhill": 200, "uphill": 400, "length_3d": 7000, "max_elevation": 1400},
]

print(
    f"{'downhill':>8}  {'uphill':>6}  {'length_3d':>9}  {'max_elev':>8}  "
    f"{'DIN33466':>8}  {'SAC':>8}  {'Linear':>8}  {'Gradient':>8}"
)
for sample in samples:
    demodf = pd.DataFrame(
        [sample],
        columns=["downhill", "uphill", "length_3d", "max_elevation"],
    )
    time_lr = lr.predict(demodf)[0]
    time_gbr = gbr_best.predict(demodf)[0]
    din = datetime.timedelta(
        seconds=din33466(
            sample["uphill"], sample["downhill"], sample["length_3d"]
        )
    )
    sac_time = datetime.timedelta(seconds=sac(sample["uphill"], sample["length_3d"]))
    din_str = str(din).rsplit(":", 1)[0]
    sac_str = str(sac_time).rsplit(":", 1)[0]
    lr_str = str(datetime.timedelta(seconds=time_lr)).rsplit(":", 1)[0]
    gbr_str = str(datetime.timedelta(seconds=time_gbr)).rsplit(":", 1)[0]
    print(
        f"{sample['downhill']:>8}  {sample['uphill']:>6}  "
        f"{sample['length_3d']:>9}  {sample['max_elevation']:>8}  "
        f"{din_str:>8}  {sac_str:>8}  {lr_str:>8}  {gbr_str:>8}"
    )

# Save Models to Disk
with open('GradientBoostingRegressor.pkl', 'wb') as fid:
    pickle.dump(gbr_best, fid)    

with open('LinearRegression.pkl', 'wb') as fid:
    pickle.dump(lr, fid)
