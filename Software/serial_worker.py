import serial
import serial.tools.list_ports
import json
import time
from PyQt6.QtCore import QThread, pyqtSignal

class SerialWorker(QThread):
    data_received = pyqtSignal(dict)
    connection_status = pyqtSignal(bool, str)
    
    def __init__(self):
        super().__init__()
        self.serial_port = None
        self.is_running = False
        
    def get_available_ports(self):
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]
        
    def connect_port(self, port_name, baudrate=115200):
        try:
            self.serial_port = serial.Serial(port_name, baudrate, timeout=1)
            self.connection_status.emit(True, f"Connected to {port_name}")
            self.start()
            return True
        except Exception as e:
            self.connection_status.emit(False, str(e))
            return False
            
    def disconnect_port(self):
        self.is_running = False
        self.wait() # Wait for thread to exit
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.connection_status.emit(False, "Disconnected")
        
    def send_command(self, cmd_dict):
        if self.serial_port and self.serial_port.is_open:
            try:
                cmd_str = json.dumps(cmd_dict) + '\n'
                self.serial_port.write(cmd_str.encode('utf-8'))
            except Exception as e:
                print(f"Error sending command: {e}")
                
    def run(self):
        self.is_running = True
        # Readline blocking loop in a separate thread
        while self.is_running:
            if self.serial_port and self.serial_port.is_open:
                try:
                    if self.serial_port.in_waiting > 0:
                        line = self.serial_port.readline().decode('utf-8').strip()
                        if line:
                            data = json.loads(line)
                            self.data_received.emit(data)
                except Exception as e:
                    # Ignore JSON decode errors or temporary drops
                    pass
            time.sleep(0.01)
