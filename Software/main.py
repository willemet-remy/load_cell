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
        
        self.scale_controls = []
        
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
        
        # Scale Controls Group
        scales_layout = QGridLayout()
        
        for i in range(4):
            cal_group = QGroupBox(f"Scale {i+1}")
            cal_layout = QGridLayout()
            
            # Tare / Calibrate
            btn_tare = QPushButton("Tare")
            btn_tare.clicked.connect(lambda checked, idx=i: self.tare_scale(idx))
            
            spin_cal = QDoubleSpinBox()
            spin_cal.setRange(0.1, 5000.0)
            spin_cal.setValue(500.0)
            
            btn_cal = QPushButton("Calibrate")
            btn_cal.clicked.connect(lambda checked, idx=i: self.calibrate_scale(idx))
            
            # Measurement Logging
            le_meas_name = QLineEdit()
            le_meas_name.setPlaceholderText("Measurement Name")
            
            sb_interval = QSpinBox()
            sb_interval.setRange(1, 3600)
            sb_interval.setValue(30)
            
            btn_start_stop = QPushButton("Start Logging")
            btn_start_stop.clicked.connect(lambda checked, idx=i: self.toggle_logging(idx))
            
            # Layout logic
            cal_layout.addWidget(btn_tare, 0, 0, 1, 2)
            cal_layout.addWidget(QLabel("Known Wt (g):"), 1, 0)
            cal_layout.addWidget(spin_cal, 1, 1)
            cal_layout.addWidget(btn_cal, 2, 0, 1, 2)
            
            # Add a separator line
            line = QWidget()
            line.setFixedHeight(2)
            line.setStyleSheet("background-color: #c0c0c0;")
            cal_layout.addWidget(line, 3, 0, 1, 2)
            
            cal_layout.addWidget(QLabel("Name:"), 4, 0)
            cal_layout.addWidget(le_meas_name, 4, 1)
            cal_layout.addWidget(QLabel("Interval(s):"), 5, 0)
            cal_layout.addWidget(sb_interval, 5, 1)
            cal_layout.addWidget(btn_start_stop, 6, 0, 1, 2)
            
            self.scale_controls.append({
                'spin_cal': spin_cal,
                'le_name': le_meas_name,
                'sb_interval': sb_interval,
                'btn_start_stop': btn_start_stop
            })
            
            cal_group.setLayout(cal_layout)
            # Add to a 2x2 grid in the sidebar
            row = i // 2
            col = i % 2
            scales_layout.addWidget(cal_group, row, col)
            
        left_panel.addLayout(scales_layout)
        left_panel.addStretch()
        
        # Version Label
        lbl_version = QLabel("Rémy Willemet - v1.0.0")
        lbl_version.setStyleSheet("color: gray; font-size: 10px;")
        left_panel.addWidget(lbl_version)
        
        main_layout.addLayout(left_panel, 1)
        
        # Right Panel (Plots)
        plot_layout = QGridLayout()
        self.plots = []
        for i in range(4):
            plot = pg.PlotWidget(title=f"Scale {i+1}")
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

    def toggle_logging(self, scale_idx):
        controls = self.scale_controls[scale_idx]
        state = self.logger.scale_states[scale_idx]
        
        if state['is_logging']:
            self.logger.stop_logging(scale_idx)
            controls['btn_start_stop'].setText("Start Logging")
            controls['le_name'].setEnabled(True)
            controls['sb_interval'].setEnabled(True)
        else:
            name = controls['le_name'].text()
            interval = controls['sb_interval'].value()
            self.logger.start_logging(scale_idx, name, interval)
            controls['btn_start_stop'].setText("Stop Logging")
            controls['le_name'].setEnabled(False)
            controls['sb_interval'].setEnabled(False)
            
    def tare_scale(self, scale_idx):
        self.serial_worker.send_command({"cmd": "TARE", "scale": scale_idx})
        
    def calibrate_scale(self, scale_idx):
        weight = self.scale_controls[scale_idx]['spin_cal'].value()
        self.serial_worker.send_command({"cmd": "CALIBRATE", "scale": scale_idx, "weight": weight})

    def closeEvent(self, event):
        self.serial_worker.disconnect_port()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
