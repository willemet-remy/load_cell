import csv
import os
import json
import time

class DataLogger:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        
        self.is_logging = False
        self.experiment_name = ""
        self.log_interval = 30 # seconds (customizable)
        self.last_log_time = 0
        
    def start_logging(self, name, interval):
        self.experiment_name = name if name else "Experiment"
        self.log_interval = interval
        self.is_logging = True
        self.last_log_time = time.time()
        
        file_path = os.path.join(self.data_dir, f"{self.experiment_name}.csv")
        # Write header if new file
        if not os.path.exists(file_path):
            with open(file_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp", 
                    "raw_0", "raw_1", "raw_2", "raw_3",
                    "weight_0", "weight_1", "weight_2", "weight_3"
                ])
                
    def stop_logging(self):
        self.is_logging = False
        
    def process_data(self, data_dict):
        if not self.is_logging:
            return
            
        current_time = time.time()
        if current_time - self.last_log_time >= self.log_interval:
            self.last_log_time = current_time
            file_path = os.path.join(self.data_dir, f"{self.experiment_name}.csv")
            with open(file_path, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    current_time,
                    data_dict['raw'][0], data_dict['raw'][1], data_dict['raw'][2], data_dict['raw'][3],
                    data_dict['weight'][0], data_dict['weight'][1], data_dict['weight'][2], data_dict['weight'][3]
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
