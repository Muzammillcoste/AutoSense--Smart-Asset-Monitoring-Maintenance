
import numpy as np
import pandas as pd
import pickle
from tensorflow.keras.models import load_model
from tensorflow.keras.models import load_model
import tensorflow.keras.losses
import requests
import csv
import os
from datetime import datetime, timedelta, timezone
import json


# Engine Temperature

custom_objects = {"mse": tensorflow.keras.losses.MeanSquaredError()}

model_ET = load_model('/root/FYP-Python-Script/model_scaler/Final_Temp_Prediction_Model.h5',custom_objects=custom_objects)

with open('/root/FYP-Python-Script/model_scaler/scaler.pkl', 'rb') as f:
    scaler_ET = pickle.load(f)



# Webhook URLs
vehicle_webhook = "https://swift-cloud.ephlux.com/api-swift/ned/workflow/LQDFyK106u?SWIFT_API_KEY=" + os.environ["SWIFT_KEY_VEHICLES"]
sensor_webhook = "https://swift-cloud.ephlux.com/api-swift/ned/integration/OY5sSM4POU?SWIFT_API_KEY=" + os.environ["SWIFT_KEY_SENSOR_READINGS"]

def fetch_vehicle_data():
    try:
        response = requests.post(vehicle_webhook, json={})
        response.raise_for_status()
        vehicles = response.json().get("actions", [{}])[0].get("obj", [])
        return {v["vehicle_id"]: {"vehicle_id": v["vehicle_id"], "sensor_readings": []} for v in vehicles}
    except requests.exceptions.RequestException as e:
        print(f"Error fetching vehicle data: {e}")
        return {}

def fetch_sensor_data():
    try:
        response = requests.post(sensor_webhook, json={})
        response.raise_for_status()
        sensors = response.json().get("response", {}).get("obj", [])
        return [
            {
                "vehicle_id": s["vehicle_id"],
                "timestamp": s.get("timestamp", ""),
                "engine_temperature": s.get("value", {}).get("engine_temperature", 0)
            }
            for s in sensors
        ]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching sensor data: {e}")
        return []

def merge_vehicle_sensor_data():
    vehicles = fetch_vehicle_data()
    sensors = fetch_sensor_data()
    one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)

    for sensor in sensors:
        try:
            sensor_time = datetime.strptime(sensor["timestamp"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
            if sensor_time >= one_week_ago:
                vehicle_id = str(sensor["vehicle_id"])
                if vehicle_id in vehicles:
                    vehicles[vehicle_id]["sensor_readings"].append(sensor)
        except ValueError:
            continue

    return list(vehicles.values())

if __name__ == "__main__":
    combined_data = merge_vehicle_sensor_data()
    output_dir = "Eng_T_vehicle_csvs"
    os.makedirs(output_dir, exist_ok=True)

    for vehicle in combined_data:
        vehicle_id = vehicle.get("vehicle_id")
        sensor_readings = vehicle.get("sensor_readings", [])

        if not sensor_readings:
            print(f"Skipping vehicle {vehicle_id} as it has no sensor readings.")
            continue

        file_name = f"vehicle_{vehicle_id}.csv"
        file_path = os.path.join(output_dir, file_name)

        print(f"Processing vehicle {vehicle_id} with {len(sensor_readings)} records...")

        with open(file_path, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["datetime", "Engine_Temperature"])

            for reading in sensor_readings:
                writer.writerow([
                    reading.get("timestamp"),
                    reading.get("engine_temperature", 0)
                ])

        print(f"Saved engine data for vehicle {vehicle_id} in {file_path}")

    print("CSV file generation complete.")



# Define directories in the current directory
input_dir = "Eng_T_vehicle_csvs"  # Folder where vehicle CSVs are stored
output_dir = "engine_temp_vehicle_predictions"  # Folder where prediction CSVs will be stored
os.makedirs(output_dir, exist_ok=True)  # Create folder if it doesn't exist

# Define feature engineering function
def create_features(df):
    df["Hour"] = df.index.hour
    df["DayOfWeek"] = df.index.dayofweek
    df["Month"] = df.index.month
    df["isWeekend"] = df["DayOfWeek"].apply(lambda x: 1 if x >= 5 else 0)
    df["isRushHour"] = df["Hour"].apply(lambda x: 1 if 7 <= x <= 9 or 17 <= x <= 19 else 0)

    # Cyclical encoding
    df['hour_sin'] = np.sin(2 * np.pi * df['Hour'] / 24)
    df['hour_cos'] = np.cos(2 * np.pi * df['Hour'] / 24)
    df['day_sin'] = np.sin(2 * np.pi * df['DayOfWeek'] / 7)
    df['day_cos'] = np.cos(2 * np.pi * df['DayOfWeek'] / 7)
    df['month_sin'] = np.sin(2 * np.pi * (df['Month'] - 1) / 12)
    df['month_cos'] = np.cos(2 * np.pi * (df['Month'] - 1) / 12)

    # Lag features
    df['temp_lag_24h'] = df['Engine_Temperature'].shift(24)
    df['temp_rolling_avg_3d'] = df['Engine_Temperature'].rolling(window=72).mean()

    df.drop(['Hour', 'DayOfWeek', 'Month'], axis=1, inplace=True)
    df.dropna(inplace=True)
    return df

# Function to inverse scale predictions
def inverse_scale_predictions(scaled_predictions, scaler, feature_index=0):
    n_samples, n_steps = scaled_predictions.shape
    dummy = np.zeros((n_samples * n_steps, len(features)))
    dummy[:, feature_index] = scaled_predictions.flatten()
    inverse_scaled = scaler.inverse_transform(dummy)
    return inverse_scaled[:, feature_index].reshape(n_samples, n_steps)

# List all vehicle CSVs in the input directory
csv_files = [f for f in os.listdir(input_dir) if f.endswith(".csv")]

for csv_file in csv_files:
    vehicle_id = csv_file.split("_")[1].split(".")[0]  # Extract vehicle ID
    file_path = os.path.join(input_dir, csv_file)

    # Load CSV
    df_new = pd.read_csv(file_path)
    df_new['datetime'] = pd.to_datetime(df_new['datetime'])

    df_new.set_index('datetime', inplace=True)


    # Apply feature engineering
    df_new = df_new[df_new["Engine_Temperature"] != 0]
    engine_temp_mean = df_new["Engine_Temperature"].mean()
    print(engine_temp_mean)
    df_new = create_features(df_new)

    #print("data",df_new)

    # Select last 168 hours for prediction
    features = ['Engine_Temperature', 'isWeekend', 'isRushHour',
                'hour_sin', 'hour_cos', 'day_sin', 'day_cos',
                'month_sin', 'month_cos', 'temp_lag_24h',
                'temp_rolling_avg_3d']

    latest_data = df_new[features].iloc[-168:]  # Last 168 hours

    # if latest_data.shape[0] < 168:
    #     print(f"Skipping vehicle {vehicle_id} due to insufficient data.")
    #     continue
    if latest_data.shape[0] < 168:
        print(f"Warning: Vehicle {vehicle_id} has only {latest_data.shape[0]} records. Padding with previous data.")

        # Pad data with first available row until we have 168 records
        while latest_data.shape[0] < 168:
            latest_data = pd.concat([latest_data.iloc[:1]] * (168 - latest_data.shape[0]) + [latest_data])

        latest_data = latest_data.iloc[-168:]  # Ensure exactly 168 rows

    print(f"Final shape of input for vehicle {vehicle_id}: {latest_data.shape}")

    # Scale data
    latest_scaled = scaler_ET.transform(latest_data)
    latest_scaled = np.expand_dims(latest_scaled, axis=0)  # Reshape for LSTM

    # Predict next 24 hours
    predictions_scaled = model_ET.predict(latest_scaled)


    # Convert predictions back to original scale
    predictions = inverse_scale_predictions(predictions_scaled, scaler_ET)

    # Generate timestamps from today's date at 00:00:00
    start_date = pd.to_datetime(datetime.now().date())  # e.g. 2025-04-12 00:00:00
    future_timestamps = pd.date_range(start=start_date, periods=24, freq='H')


    # Format datetime and create DataFrame
    predictions_df = pd.DataFrame({
        'datetime': future_timestamps.strftime('%Y-%m-%d %H:%M:%S'),
        'Predicted_Engine_Temperature': predictions.flatten()
    })


    # Save predictions to a new CSV in the output folder
    output_file_path = os.path.join(output_dir, f"predicted_vehicle_{vehicle_id}.csv")
    predictions_df.to_csv(output_file_path, index=False)

    print(f"Saved predictions for vehicle {vehicle_id} in {output_file_path}")

print("All predictions completed!")

"""# Tyre Pressure

"""

custom_objects = {"mse": tensorflow.keras.losses.MeanSquaredError()}

model_PT = load_model('/root/FYP-Python-Script/model_scaler/Final_TP_Prediction_Model.h5', custom_objects=custom_objects)

with open('/root/FYP-Python-Script/model_scaler/scaler_TP.pkl', 'rb') as f:
    scaler_PT = pickle.load(f)



# Webhook URLs
vehicle_webhook = "https://swift-cloud.ephlux.com/api-swift/ned/workflow/LQDFyK106u?SWIFT_API_KEY=" + os.environ["SWIFT_KEY_VEHICLES"]
sensor_webhook = "https://swift-cloud.ephlux.com/api-swift/ned/integration/OY5sSM4POU?SWIFT_API_KEY=" + os.environ["SWIFT_KEY_SENSOR_READINGS"]

def fetch_vehicle_data():
    try:
        response = requests.post(vehicle_webhook, json={})
        response.raise_for_status()
        vehicles = response.json().get("actions", [{}])[0].get("obj", [])
        return {
            v["vehicle_id"]: {
                "vehicle_id": v["vehicle_id"],
                "status": v.get("status", "Unknown"),
                "sensor_readings": []
            } for v in vehicles
        }
    except requests.exceptions.RequestException as e:
        print(f"Error fetching vehicle data: {e}")
        return {}

def fetch_sensor_data():
    try:
        response = requests.post(sensor_webhook, json={})
        response.raise_for_status()
        sensors = response.json().get("response", {}).get("obj", [])
        return [
            {
                "vehicle_id": s["vehicle_id"],
                "timestamp": s.get("timestamp", ""),
                "front_left": s.get("value", {}).get("front_left", {}).get("pressure", 0),
                "front_right": s.get("value", {}).get("front_right", {}).get("pressure", 0),
                "rear_left": s.get("value", {}).get("rear_left", {}).get("pressure", 0),
                "rear_right": s.get("value", {}).get("rear_right", {}).get("pressure", 0),
            }
            for s in sensors
        ]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching sensor data: {e}")
        return []

def merge_vehicle_sensor_data():
    vehicles = fetch_vehicle_data()
    sensors = fetch_sensor_data()
    one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)

    for sensor in sensors:
        try:
            sensor_time = datetime.strptime(sensor["timestamp"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
            if sensor_time >= one_week_ago:
                vehicle_id = str(sensor["vehicle_id"])
                if vehicle_id in vehicles:
                    vehicles[vehicle_id]["sensor_readings"].append(sensor)
        except ValueError:
            continue

    return list(vehicles.values())

if __name__ == "__main__":
    combined_data = merge_vehicle_sensor_data()
    output_dir = "tyre_pressure_vehicle_csvs"
    os.makedirs(output_dir, exist_ok=True)

    for vehicle in combined_data:
        vehicle_id = vehicle.get("vehicle_id")
        sensor_readings = vehicle.get("sensor_readings", [])

        if not sensor_readings:
            print(f"Skipping vehicle {vehicle_id} as it has no sensor readings.")
            continue

        file_name = f"vehicle_{vehicle_id}.csv"
        file_path = os.path.join(output_dir, file_name)

        print(f"Processing vehicle {vehicle_id} with {len(sensor_readings)} records...")

        with open(file_path, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([
                "datetime",
                "front_left", "front_right",
                "rear_left", "rear_right"
            ])

            for reading in sensor_readings:
                writer.writerow([
                    reading.get("timestamp"),
                    reading.get("front_left"),
                    reading.get("front_right"),
                    reading.get("rear_left"),
                    reading.get("rear_right")
                ])

        print(f"Saved pressure data for vehicle {vehicle_id} in {file_path}")

    print("CSV file generation complete.")

# Define Paths
data_dir = "tyre_pressure_vehicle_csvs"
output_dir = "Predicted_TPvehicle_csvs"
os.makedirs(output_dir, exist_ok=True)

features = ['Tyre_Pressure_PSI', 'isWeekend', 'isRushHour',
            'hour_sin', 'hour_cos', 'day_sin', 'day_cos',
            'month_sin', 'month_cos', 'tp_lag_24h',
            'tp_rolling_avg_3d']
target = 'Tyre_Pressure_PSI'

def create_features(df):
    """Creates features required for tire pressure prediction after filtering zero values in all columns."""
    # Drop rows where any tire pressure is 0
    df = df[(df["front_left"] > 0) &
            (df["front_right"] > 0) &
            (df["rear_left"] > 0) &
            (df["rear_right"] > 0)]

    if df.empty:
        print("Warning: After removing zeros, no data remains!")
        return {}

    df_features = {}

    for column in ["front_left", "front_right", "rear_left", "rear_right"]:
        df_column = df[[column]].copy()
        df_column.rename(columns={column: "Tyre_Pressure_PSI"}, inplace=True)
        df_column["Hour"] = df_column.index.hour
        df_column["DayOfWeek"] = df_column.index.dayofweek
        df_column["Month"] = df_column.index.month
        df_column["isWeekend"] = df_column["DayOfWeek"].apply(lambda x: 1 if x >= 5 else 0)
        df_column["isRushHour"] = df_column["Hour"].apply(lambda x: 1 if 7 <= x <= 9 or 17 <= x <= 19 else 0)

        # Cyclical encoding
        df_column['hour_sin'] = np.sin(2 * np.pi * df_column['Hour'] / 24)
        df_column['hour_cos'] = np.cos(2 * np.pi * df_column['Hour'] / 24)
        df_column['day_sin'] = np.sin(2 * np.pi * df_column['DayOfWeek'] / 7)
        df_column['day_cos'] = np.cos(2 * np.pi * df_column['DayOfWeek'] / 7)
        df_column['month_sin'] = np.sin(2 * np.pi * (df_column['Month'] - 1) / 12)
        df_column['month_cos'] = np.cos(2 * np.pi * (df_column['Month'] - 1) / 12)

        # Lag features
        df_column['tp_lag_24h'] = df_column['Tyre_Pressure_PSI'].shift(24)
        df_column['tp_rolling_avg_3d'] = df_column['Tyre_Pressure_PSI'].rolling(window=72).mean()

        df_column.drop(['Hour', 'DayOfWeek', 'Month'], axis=1, inplace=True)
        df_column.dropna(inplace=True)

        df_features[column] = df_column

    return df_features

def inverse_scale_predictions(scaled_predictions, scaler, feature_index=0):
    """Inverse transforms predictions back to original scale."""
    n_samples, n_steps = scaled_predictions.shape
    dummy = np.zeros((n_samples * n_steps, len(features)))
    dummy[:, feature_index] = scaled_predictions.flatten()
    inverse_scaled = scaler.inverse_transform(dummy)
    return inverse_scaled[:, feature_index].reshape(n_samples, n_steps)

# Loop through all CSV files
for file in os.listdir(data_dir):
    if file.endswith(".csv"):
        file_path = os.path.join(data_dir, file)
        print(f"Processing {file_path}...")
        df = pd.read_csv(file_path, parse_dates=['datetime'], index_col='datetime')

        predictions_dict = {}
        feature_dfs = create_features(df)

        if not feature_dfs:
            print(f"Skipping {file}, all values were zero or insufficient data.")
            continue

        for column, df_column in feature_dfs.items():
            if df_column.shape[0] < 168:
                print(f"Warning: {column} in {file} has only {df_column.shape[0]} records. Padding.")
                pad_count = 168 - df_column.shape[0]
                pad_df = pd.concat([df_column.iloc[:1]] * pad_count)
                df_column = pd.concat([pad_df, df_column]).iloc[-56:]

            latest_data = df_column[features].iloc[-168:]
            latest_scaled = scaler_PT.transform(latest_data)
            latest_scaled = np.expand_dims(latest_scaled, axis=0)

            predictions_scaled = model_PT.predict(latest_scaled)
            predictions = inverse_scale_predictions(predictions_scaled, scaler_PT)

            # Create fixed future timestamps starting from next full hour (00:00)
            base_date = pd.Timestamp.today().normalize()
            future_timestamps = pd.date_range(start=base_date, periods=8, freq='3H')

            predictions_df = pd.DataFrame({'datetime': future_timestamps, column: predictions.flatten()})
            predictions_dict[column] = predictions_df.set_index('datetime')

        if predictions_dict:
            final_predictions_df = pd.concat(predictions_dict.values(), axis=1)
            output_file = os.path.join(output_dir, f"predicted_{file}")
            final_predictions_df.to_csv(output_file)
            print(f"Predictions saved: {output_file}")

print("All predictions completed!")

"""# Tire Temp"""


# Webhook URLs
vehicle_webhook = "https://swift-cloud.ephlux.com/api-swift/ned/workflow/LQDFyK106u?SWIFT_API_KEY=" + os.environ["SWIFT_KEY_VEHICLES"]
sensor_webhook = "https://swift-cloud.ephlux.com/api-swift/ned/integration/OY5sSM4POU?SWIFT_API_KEY=" + os.environ["SWIFT_KEY_SENSOR_READINGS"]

def fetch_vehicle_data():
    try:
        response = requests.post(vehicle_webhook, json={})
        response.raise_for_status()
        vehicles = response.json().get("actions", [{}])[0].get("obj", [])
        return {
            v["vehicle_id"]: {
                "vehicle_id": v["vehicle_id"],
                "status": v.get("status", "Unknown"),
                "sensor_readings": []
            } for v in vehicles
        }
    except requests.exceptions.RequestException as e:
        print(f"Error fetching vehicle data: {e}")
        return {}

def fetch_sensor_data():
    try:
        response = requests.post(sensor_webhook, json={})
        response.raise_for_status()
        sensors = response.json().get("response", {}).get("obj", [])
        return [
            {
                "vehicle_id": s["vehicle_id"],
                "timestamp": s.get("timestamp", ""),
                "front_left": s.get("value", {}).get("front_left", {}).get("temperature", 0),
                "front_right": s.get("value", {}).get("front_right", {}).get("temperature", 0),
                "rear_left": s.get("value", {}).get("rear_left", {}).get("temperature", 0),
                "rear_right": s.get("value", {}).get("rear_right", {}).get("temperature", 0),
            }
            for s in sensors
        ]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching sensor data: {e}")
        return []

def merge_vehicle_sensor_data():
    vehicles = fetch_vehicle_data()
    sensors = fetch_sensor_data()
    one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)

    for sensor in sensors:
        try:
            sensor_time = datetime.strptime(sensor["timestamp"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
            if sensor_time >= one_week_ago:
                vehicle_id = str(sensor["vehicle_id"])
                if vehicle_id in vehicles:
                    vehicles[vehicle_id]["sensor_readings"].append(sensor)
        except ValueError:
            continue

    return list(vehicles.values())

if __name__ == "__main__":
    combined_data = merge_vehicle_sensor_data()
    output_dir = "tyre_temp_vehicle_csvs"
    os.makedirs(output_dir, exist_ok=True)

    for vehicle in combined_data:
        vehicle_id = vehicle.get("vehicle_id")
        sensor_readings = vehicle.get("sensor_readings", [])

        if not sensor_readings:
            print(f"Skipping vehicle {vehicle_id} as it has no sensor readings.")
            continue

        file_name = f"vehicle_{vehicle_id}.csv"
        file_path = os.path.join(output_dir, file_name)

        print(f"Processing vehicle {vehicle_id} with {len(sensor_readings)} records...")

        with open(file_path, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([
                "datetime",
                "front_left", "front_right",
                "rear_left", "rear_right"
            ])

            for reading in sensor_readings:
                writer.writerow([
                    reading.get("timestamp"),
                    reading.get("front_left"),
                    reading.get("front_right"),
                    reading.get("rear_left"),
                    reading.get("rear_right")
                ])

        print(f"Saved tyre temperature data for vehicle {vehicle_id} in {file_path}")

    print("CSV file generation complete.")

custom_objects = {"mse": tensorflow.keras.losses.MeanSquaredError()}

model = load_model('/root/FYP-Python-Script/model_scaler/Final_Tyre_Temp_Prediction_Model.h5', custom_objects=custom_objects)

with open('/root/FYP-Python-Script/model_scaler/scaler_TTemp.pkl', 'rb') as f:
    scaler = pickle.load(f)



def create_features(df):
    df.columns = df.columns.str.strip()

    if 'Tyre_Temperature_C' not in df.columns:
        raise KeyError("'Tyre_Temperature_C' column is missing in the input data.")

    df["Hour"] = df.index.hour
    df["DayOfWeek"] = df.index.dayofweek
    df["Month"] = df.index.month

    df["isWeekend"] = df["DayOfWeek"].apply(lambda x: 1 if x >= 5 else 0)
    df["isRushHour"] = df["Hour"].apply(lambda x: 1 if 7 <= x <= 9 or 17 <= x <= 19 else 0)

    df['hour_sin'] = np.sin(2 * np.pi * df['Hour'] / 24)
    df['hour_cos'] = np.cos(2 * np.pi * df['Hour'] / 24)
    df['day_sin'] = np.sin(2 * np.pi * df['DayOfWeek'] / 7)
    df['day_cos'] = np.cos(2 * np.pi * df['DayOfWeek'] / 7)
    df['month_sin'] = np.sin(2 * np.pi * (df['Month'] - 1) / 12)
    df['month_cos'] = np.cos(2 * np.pi * (df['Month'] - 1) / 12)

    df['tp_lag_24h'] = df['Tyre_Temperature_C'].shift(24)
    df['tp_rolling_avg_3d'] = df['Tyre_Temperature_C'].rolling(window=72).mean()

    df.drop(['Hour', 'DayOfWeek', 'Month'], axis=1, inplace=True)
    df.dropna(inplace=True)

    return df

def inverse_scale_predictions(scaled_predictions, scaler, feature_index=0):
    n_samples, n_steps = scaled_predictions.shape
    dummy = np.zeros((n_samples * n_steps, scaler.n_features_in_))
    dummy[:, feature_index] = scaled_predictions.flatten()
    inverse_scaled = scaler.inverse_transform(dummy)
    return inverse_scaled[:, feature_index].reshape(n_samples, n_steps)

def process_vehicle_data(vehicle_file, scaler, model, output_dir):
    df = pd.read_csv(vehicle_file, parse_dates=['datetime'], index_col='datetime')
    df.columns = df.columns.str.strip()

    tyre_columns = ['front_left', 'front_right', 'rear_left', 'rear_right']
    vehicle_id = os.path.basename(vehicle_file).split('_')[1].split('.')[0]

    all_preds = []

    for tyre in tyre_columns:
        if tyre not in df.columns:
            print(f"{tyre} not found in {vehicle_file}, skipping.")
            continue

        df_tyre = df[[tyre]].copy()
        df_tyre.rename(columns={tyre: 'Tyre_Temperature_C'}, inplace=True)

        df_tyre = df_tyre[df_tyre['Tyre_Temperature_C'] != 0]
        df_tyre.index.name = 'datetime'

        if df_tyre.shape[0] < 72:
            print(f"Not enough data for {tyre} in {vehicle_file}, skipping...")
            continue

        df_tyre = create_features(df_tyre)

        features = ['Tyre_Temperature_C', 'isWeekend', 'isRushHour',
                    'hour_sin', 'hour_cos', 'day_sin', 'day_cos',
                    'month_sin', 'month_cos', 'tp_lag_24h',
                    'tp_rolling_avg_3d']

        if df_tyre.shape[0] < 56:
            print(f"Not enough feature data for {tyre} in {vehicle_file}, skipping...")
            continue

        latest_data = df_tyre[features].iloc[-56:]
        latest_scaled = scaler.transform(latest_data)
        latest_scaled = np.expand_dims(latest_scaled, axis=0)

        predictions_scaled = model.predict(latest_scaled)
        predictions = inverse_scale_predictions(predictions_scaled, scaler)

        # Generate timestamps only once
        if not all_preds:
            last_time = df_tyre.index[-1]
            next_day_midnight = (last_time + pd.Timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            future_timestamps = pd.date_range(start=next_day_midnight, periods=8, freq='3H')
            formatted_timestamps = future_timestamps.strftime("%d/%m/%Y %H:%M")
            all_preds.append(pd.DataFrame({'datetime': formatted_timestamps}))

        # Add predictions for this tyre
        all_preds.append(pd.DataFrame({tyre: predictions.flatten()}))

        print(f"Predicted {tyre} for vehicle {vehicle_id}")

    if len(all_preds) > 1:
        result_df = pd.concat(all_preds, axis=1)
        result_df = result_df.loc[:, ~result_df.columns.duplicated()]
        output_file = os.path.join(output_dir, f"predicted_vehicle_{vehicle_id}.csv")
        #output_file = os.path.join(output_dir, f"predicted_{file}")
        result_df.to_csv(output_file, index=False)
        print(f"Saved predictions for vehicle {vehicle_id} to {output_file}")
    else:
        print(f"No predictions saved for vehicle {vehicle_id}.")

if __name__ == "__main__":

    input_dir = "tyre_temp_vehicle_csvs"
    output_dir = "pred_tyre_temp"
    os.makedirs(output_dir, exist_ok=True)

    vehicle_files = [os.path.join(input_dir, f) for f in os.listdir(input_dir) if f.endswith('.csv')]
    for vehicle_file in vehicle_files:
        process_vehicle_data(vehicle_file, scaler, model, output_dir)

    print("All vehicle predictions complete.")

"""# Make Json

"""



# Define input directories
tp_dir = "Predicted_TPvehicle_csvs"
tt_dir = "pred_tyre_temp"
et_dir = "engine_temp_vehicle_predictions"
output_dir = "vehicle_combined_jsons"
os.makedirs(output_dir, exist_ok=True)

# Get list of vehicle IDs from tyre pressure folder (assuming consistent filenames)
vehicle_ids = [f.split("_")[2].split(".")[0] for f in os.listdir(tp_dir) if f.endswith(".csv")]

# Tyre positions
tyres = ['rear_left', 'rear_right', 'front_left', 'front_right']

for vid in vehicle_ids:
    # File paths
    tyre_pressure_file = os.path.join(tp_dir, f"predicted_vehicle_{vid}.csv")
    tyre_temp_file = os.path.join(tt_dir, f"predicted_vehicle_{vid}.csv")
    engine_temp_file = os.path.join(et_dir, f"predicted_vehicle_{vid}.csv")

    # Load data
    df_tp = pd.read_csv(tyre_pressure_file, parse_dates=['datetime'])
    df_tt = pd.read_csv(tyre_temp_file, parse_dates=['datetime'])
    df_et = pd.read_csv(engine_temp_file, parse_dates=['datetime'])

    # Metadata
    metadata = {
        "date": str(df_tp['datetime'].min().date()),
        "vehicle_id": vid
    }

    # Summary
    summary = {
        "max_tyre_temperature_c": {tyre: round(df_tt[tyre].max(), 2) for tyre in tyres},
        "min_tyre_pressure_psi": {tyre: round(df_tp[tyre].min(), 2) for tyre in tyres},
        "max_engine_temperature_c": round(df_et["Predicted_Engine_Temperature"].max(), 2)
    }

    # Predictions - Tyre Temperature
    tyre_temp_preds = {tyre: [] for tyre in tyres}
    for _, row in df_tt.iterrows():
        timestamp = row["datetime"].isoformat()
        for tyre in tyres:
            tyre_temp_preds[tyre].append({
                "timestamp": timestamp,
                "value": round(row[tyre], 2)
            })

    # Predictions - Tyre Pressure
    tyre_pressure_preds = {tyre: [] for tyre in tyres}
    for _, row in df_tp.iterrows():
        timestamp = row["datetime"].isoformat()
        for tyre in tyres:
            tyre_pressure_preds[tyre].append({
                "timestamp": timestamp,
                "value": round(row[tyre], 2)
            })

    # Predictions - Engine Temperature
    engine_temp_preds = []
    for _, row in df_et.iterrows():
        engine_temp_preds.append({
            "timestamp": row["datetime"].isoformat(),
            "value": round(row["Predicted_Engine_Temperature"], 2)
        })

    # Combine JSON
    combined_json = {
        "metadata": metadata,
        "summary": summary,
        "predictions": {
            "tyre_temperature_c": tyre_temp_preds,
            "tyre_pressure_psi": tyre_pressure_preds,
            "engine_temperature_c": engine_temp_preds
        }
    }

    # Save to file
    output_path = os.path.join(output_dir, f"vehicle_{vid}_data.json")
    with open(output_path, "w") as json_file:
        json.dump(combined_json, json_file, indent=4)

    print(f"✅ Saved JSON for vehicle {vid} to: {output_path}")

print("🎉 All JSON files created successfully!")

"""# Sent Data to Swift"""



Delete_pred_webhook='https://swift-cloud.ephlux.com/api-swift/ned/workflow/5N3ei2rugN?SWIFT_API_KEY=' + os.environ["SWIFT_KEY_DELETE_PREDICTIONS"]

response = requests.post(Delete_pred_webhook)
response_text = response.text
print(response_text)

import os
import json
import requests

# Webhook URL
webhook_url = "https://swift-cloud.ephlux.com/api-swift/ned/workflow/QUc_x0zye9?SWIFT_API_KEY=" + os.environ["SWIFT_KEY_POST_PREDICTIONS"]

# Directory where JSON files are stored
json_dir = "vehicle_combined_jsons"

# Get all JSON files in the directory
json_files = sorted(os.listdir(json_dir))  # Sorting ensures vehicle order consistency

# Process each JSON file one by one
for json_file in json_files:
    file_path = os.path.join(json_dir, json_file)

    with open(file_path, 'r') as f:
        data = json.load(f)

    # Make POST request for the full JSON data
    response = requests.post(webhook_url, json=data)
    response_text = response.text

    # Get vehicle ID from JSON for logging
    vehicle_id = data.get("metadata", {}).get("vehicle_id", "Unknown")

    # Print response status and content
    if response.status_code in [200, 201]:
        print(f"✅ Successfully sent data for vehicle {vehicle_id}")
    else:
        print(f"❌ Failed to send data for vehicle {vehicle_id}. Error: {response_text}")

    print(f"📡 Webhook Response: {response_text}")

print("🚀 All vehicle data has been sent to the webhook!")

