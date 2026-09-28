import pandas as pd, numpy as np, joblib
from sklearn.ensemble import RandomForestRegressor

np.random.seed(42)
n = 5000
df = pd.DataFrame({
    "distance_km": np.random.uniform(0.5, 12, n), # generates an array of n random floating-point numbers evenly distributed between 0.5 and 12.
    "prep_time_min": np.random.uniform(5, 30, n),
    "rider_available": np.random.randint(0, 2, n),
    "is_raining": np.random.randint(0, 2, n),
})
# ETA = base + distance*3 + prep*0.7 + rain penalty*9(0 for 0 and 9 for 1) + rider penalty(6 for1 & 0 for 0) + noise
df["eta_min"] = (8 + df.distance_km*3 + df.prep_time_min*0.7
                 + df.is_raining*9 + (1-df.rider_available)*6
                 + np.random.normal(0, 2, n))

X, y = df.drop(columns=["eta_min"]), df["eta_min"]
model = RandomForestRegressor(n_estimators=60, random_state=42).fit(X, y)
joblib.dump(model, "eta_model.pkl") #  saves the model to a file named "eta_model.pkl" on hard drive
print("Model saved: eta_model.pkl ✅")