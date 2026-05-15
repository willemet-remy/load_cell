import sys
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QLineEdit, QComboBox, QGroupBox, QSpinBox,
                             QGridLayout, QDoubleSpinBox)
from PyQt6.QtCore import pyqtSlot
import pyqtgraph as pg

from serial_worker import SerialWorker
from data_logger import DataLogger

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Load Cell Monitor")
        self.resize(1200, 800)
        
        self.logger = DataLogger()
        self.serial_worker = SerialWorker()
        self.serial_worker.data_received.connect(self.on_data_received)
        self.serial_worker.connection_status.connect(self.on_connection_status)
        
        # Data buffers for plotting
        self.start_time = time.time()
        self.time_data = []
        self.weight_data = [[], [], [], []]
        self.curves = []
        
        self.init_ui()
        self.refresh_ports()
        
    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        
        # Left Panel (Controls)
        left_panel = QVBoxLayout()
        
        # Connection Group
        conn_group = QGroupBox("Connection")
        conn_layout = QVBoxLayout()
        self.port_combo = QComboBox()
        self.btn_refresh = QPushButton("Refresh Ports")
        self.btn_refresh.clicked.connect(self.refresh_ports)
        self.btn_connect = QPushButton("Connect")
        self.btn_connect.clicked.connect(self.toggle_connection)
        self.lbl_status = QLabel("Disconnected")
        
        conn_layout.addWidget(self.port_combo)
        conn_layout.addWidget(self.btn_refresh)
        conn_layout.addWidget(self.btn_connect)
        conn_layout.addWidget(self.lbl_status)
        conn_group.setLayout(conn_layout)
        left_panel.addWidget(conn_group)
        
        # Measurement Group
        meas_group = QGroupBox("Measurement Logging")
        meas_layout = QVBoxLayout()
        
        self.le_meas_name = QLineEdit()
        self.le_meas_name.setPlaceholderText("Measurement Name")
        
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Interval (sec):"))
        self.sb_interval = QSpinBox()
        self.sb_interval.setRange(1, 3600)
        self.sb_interval.setValue(30)
        interval_layout.addWidget(self.sb_interval)
        
        self.btn_start_stop = QPushButton("Start Logging")
        self.btn_start_stop.clicked.connect(self.toggle_logging)
        
        meas_layout.addWidget(QLabel("Name:"))
        meas_layout.addWidget(self.le_meas_name)
        meas_layout.addLayout(interval_layout)
        meas_layout.addWidget(self.btn_start_stop)
        meas_group.setLayout(meas_layout)
        left_panel.addWidget(meas_group)
        
        # Calibration Groups
        self.calib_spins = []
        for i in range(4):
            cal_group = QGroupBox(f"Scale {i}")
            cal_layout = QGridLayout()
            
            btn_tare = QPushButton("Tare")
            btn_tare.clicked.connect(lambda checked, idx=i: self.tare_scale(idx))
            
            spin_cal = QDoubleSpinBox()
            spin_cal.setRange(0.1, 5000.0)
            spin_cal.setValue(500.0)
            self.calib_spins.append(spin_cal)
            
            btn_cal = QPushButton("Calibrate")
            btn_cal.clicked.connect(lambda checked, idx=i: self.calibrate_scale(idx))
            
            cal_layout.addWidget(btn_tare, 0, 0, 1, 2)
            cal_layout.addWidget(QLabel("Known Weight (g):"), 1, 0)
            cal_layout.addWidget(spin_cal, 1, 1)
            cal_layout.addWidget(btn_cal, 2, 0, 1, 2)
            
            cal_group.setLayout(cal_layout)
            left_panel.addWidget(cal_group)
            
        left_panel.addStretch()
        main_layout.addLayout(left_panel, 1)
        
        # Right Panel (Plots)
        plot_layout = QGridLayout()
        self.plots = []
        for i in range(4):
            plot = pg.PlotWidget(title=f"Beaker {i} Weight")
            plot.setLabel('left', 'Weight (g)')
            plot.setLabel('bottom', 'Time (s)')
            plot.showGrid(x=True, y=True)
            # Use different colors for plots
            colors = [(255,0,0), (0,255,0), (0,0,255), (255,255,0)]
            curve = plot.plot(pen=pg.mkPen(color=colors[i], width=2))
            self.plots.append(plot)
            self.curves.append(curve)
            
            row = i // 2
            col = i % 2
            plot_layout.addWidget(plot, row, col)
            
        main_layout.addLayout(plot_layout, 4)
        
    def refresh_ports(self):
        self.port_combo.clear()
        ports = self.serial_worker.get_available_ports()
        self.port_combo.addItems(ports)
        
    def toggle_connection(self):
        if self.serial_worker.is_running:
            self.serial_worker.disconnect_port()
            self.btn_connect.setText("Connect")
        else:
            port = self.port_combo.currentText()
            if port:
                self.serial_worker.connect_port(port)
                self.btn_connect.setText("Disconnect")
                
    @pyqtSlot(bool, str)
    def on_connection_status(self, connected, msg):
        self.lbl_status.setText(msg)
        if not connected:
            self.btn_connect.setText("Connect")
            
    @pyqtSlot(dict)
    def on_data_received(self, data):
        if 'type' in data and data['type'] == 'DATA':
            # Update logger
            self.logger.process_data(data)
            
            # Update plots
            current_t = time.time() - self.start_time
            self.time_data.append(current_t)
            
            for i in range(4):
                self.weight_data[i].append(data['weight'][i])
            
            # Keep only last 100 points for smooth scrolling
            if len(self.time_data) > 100:
                self.time_data.pop(0)
                for i in range(4):
                    self.weight_data[i].pop(0)
                    
            for i in range(4):
                self.curves[i].setData(self.time_data, self.weight_data[i])
                
        elif 'status' in data:
            print(f"Status update from MCU: {data}")
            # If calibration was done, we could save the factors to calibration.json
            # and send them on next boot. For now, it lives in RAM on the ESP32.

    def toggle_logging(self):
        if self.logger.is_logging:
            self.logger.stop_logging()
            self.btn_start_stop.setText("Start Logging")
            self.le_meas_name.setEnabled(True)
            self.sb_interval.setEnabled(True)
        else:
            name = self.le_meas_name.text()
            interval = self.sb_interval.value()
            self.logger.start_logging(name, interval)
            self.btn_start_stop.setText("Stop Logging")
            self.le_meas_name.setEnabled(False)
            self.sb_interval.setEnabled(False)
            
    def tare_scale(self, scale_idx):
        self.serial_worker.send_command({"cmd": "TARE", "scale": scale_idx})
        
    def calibrate_scale(self, scale_idx):
        weight = self.calib_spins[scale_idx].value()
        self.serial_worker.send_command({"cmd": "CALIBRATE", "scale": scale_idx, "weight": weight})

    def closeEvent(self, event):
        self.serial_worker.disconnect_port()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
