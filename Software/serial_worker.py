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
        self.port_name = ""
        self.baudrate = 115200
        self.is_running = False
        self._disconnect_requested = False
        
    def get_available_ports(self):
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]
        
    def connect_port(self, port_name, baudrate=115200):
        if self.is_running:
            return False
        self.port_name = port_name
        self.baudrate = baudrate
        self._disconnect_requested = False
        self.start() # Starts run() in a background thread
        return True
        
    def disconnect_port(self):
        self._disconnect_requested = True
        self.is_running = False
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.close()
            except Exception:
                pass
        self.wait() # Wait for thread to finish
        self.connection_status.emit(False, "Disconnected")
        
    def send_command(self, cmd_dict):
        if self.serial_port and self.serial_port.is_open:
            try:
                cmd_str = json.dumps(cmd_dict) + '\n'
                self.serial_port.write(cmd_str.encode('utf-8'))
            except Exception as e:
                print(f"Error sending command: {e}")
                
    def run(self):
        try:
            # Open serial port in background thread to prevent freezing UI
            self.serial_port = serial.Serial(self.port_name, self.baudrate, timeout=1)
            self.connection_status.emit(True, f"Connected to {self.port_name}")
            self.is_running = True
        except Exception as e:
            self.connection_status.emit(False, f"Failed to connect: {str(e)}")
            self.is_running = False
            return
            
        while self.is_running:
            try:
                if self.serial_port and self.serial_port.is_open:
                    if self.serial_port.in_waiting > 0:
                        line = self.serial_port.readline().decode('utf-8').strip()
                        if line:
                            data = json.loads(line)
                            self.data_received.emit(data)
            except Exception as e:
                if self._disconnect_requested:
                    break
                self.connection_status.emit(False, f"Connection lost: {str(e)}")
                break
            time.sleep(0.01)
            
        # Ensure clean up
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.close()
            except Exception:
                pass
        self.is_running = False
