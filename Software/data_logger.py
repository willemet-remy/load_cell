import csv
import os
import json
import time
from datetime import datetime

class DataLogger:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
        # State for each scale: 0 to 3
        self.scale_states = {
            i: {'is_logging': False, 'name': "", 'interval': 30, 'last_log_time': 0, 'start_time': 0, 'file_path': ""}
            for i in range(4)
        }
        
    def start_logging(self, scale_idx, name, interval):
        state = self.scale_states[scale_idx]
        state['name'] = name if name else f"Measurement_Scale{scale_idx+1}"
        state['interval'] = interval
        state['is_logging'] = True
        state['last_log_time'] = time.time()
        state['start_time'] = state['last_log_time']
        
        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{date_str}_{state['name']}_Scale{scale_idx+1}.csv"
        state['file_path'] = os.path.join(self.data_dir, filename)
        
        # Write header
        with open(state['file_path'], 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "datetime", "elapsed_s", "raw", "weight"])
                
    def stop_logging(self, scale_idx):
        self.scale_states[scale_idx]['is_logging'] = False
        
    def process_data(self, data_dict):
        current_time = time.time()
        date_str = datetime.fromtimestamp(current_time).strftime("%Y-%m-%d %H:%M:%S")
        
        for i in range(4):
            state = self.scale_states[i]
            if state['is_logging']:
                if current_time - state['last_log_time'] >= state['interval']:
                    state['last_log_time'] = current_time
                    elapsed_s = current_time - state['start_time']
                    with open(state['file_path'], 'a', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow([
                            current_time,
                            date_str,
                            f"{elapsed_s:.1f}",
                            data_dict['raw'][i],
                            data_dict['weight'][i]
                        ])
                        
    def save_calibration(self, calib_data):
        file_path = os.path.join(self.data_dir, "calibration.json")
        with open(file_path, 'w') as f:
            json.dump(calib_data, f, indent=4)
            
    def load_calibration(self):
        file_path = os.path.join(self.data_dir, "calibration.json")
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        return None

    def log_calibration_history(self, calib_data):
        calib_dir = os.path.join(self.data_dir, "calibration_data")
        if not os.path.exists(calib_dir):
            os.makedirs(calib_dir)
            
        file_path = os.path.join(calib_dir, "calibration_history.csv")
        file_exists = os.path.exists(file_path)
        
        with open(file_path, 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["date", "sensor", "raw", "weight", "factor"])
                
            date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow([
                date_str,
                calib_data.get('scale', 0) + 1,
                calib_data.get('raw', 0),
                calib_data.get('weight', 0.0),
                calib_data.get('factor', 1.0)
            ])
