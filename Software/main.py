import sys
import time
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QLineEdit, QComboBox, QGroupBox, QSpinBox,
                             QGridLayout, QDoubleSpinBox, QFrame)
from PyQt6.QtCore import pyqtSlot, QTimer, Qt
from PyQt6.QtGui import QIcon
import pyqtgraph as pg

from serial_worker import SerialWorker
from data_logger import DataLogger
from calibration_dialog import CalibrationDialog

THEME_QSS = """
QMainWindow {
    background-color: #121214;
}

QDialog {
    background-color: #121214;
}

QWidget {
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
    color: #e2e8f0;
}

QGroupBox {
    background-color: #1e1e24;
    border: 1px solid #2e2e38;
    border-radius: 8px;
    margin-top: 12px;
    font-weight: bold;
    font-size: 13px;
    padding: 10px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 5px;
    color: #06b6d4;
}

/* Form Inputs */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #2d2d38;
    border: 1px solid #3f3f4c;
    border-radius: 6px;
    padding: 6px 10px;
    color: #e2e8f0;
    font-size: 12px;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border: 1px solid #06b6d4;
    background-color: #343442;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 20px;
    border-left-width: 0px;
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
}

/* Buttons */
QPushButton {
    background-color: #2d2d38;
    border: 1px solid #3f3f4c;
    border-radius: 6px;
    padding: 8px 12px;
    font-weight: bold;
    font-size: 12px;
    color: #e2e8f0;
}

QPushButton:hover {
    background-color: #3f3f50;
    border-color: #06b6d4;
}

QPushButton:pressed {
    background-color: #23232b;
}

QPushButton:disabled {
    background-color: #1a1a20;
    color: #64748b;
    border-color: #2a2a32;
}

/* Themes */
QPushButton[theme="primary"] {
    background-color: #0284c7;
    border: 1px solid #0369a1;
    color: white;
}
QPushButton[theme="primary"]:hover {
    background-color: #0369a1;
}

QPushButton[theme="accent"] {
    background-color: #ea580c;
    border: 1px solid #c2410c;
    color: white;
}
QPushButton[theme="accent"]:hover {
    background-color: #c2410c;
}

QPushButton[theme="info"] {
    background-color: #0891b2;
    border: 1px solid #0e7490;
    color: white;
}
QPushButton[theme="info"]:hover {
    background-color: #0e7490;
}

QPushButton[theme="success"] {
    background-color: #059669;
    border: 1px solid #047857;
    color: white;
}
QPushButton[theme="success"]:hover {
    background-color: #047857;
}

QPushButton[theme="danger"] {
    background-color: #e11d48;
    border: 1px solid #be123c;
    color: white;
}
QPushButton[theme="danger"]:hover {
    background-color: #be123c;
}

QPushButton[theme="secondary"] {
    background-color: #374151;
    border: 1px solid #4b5563;
    color: #f3f4f6;
}
QPushButton[theme="secondary"]:hover {
    background-color: #4b5563;
}

/* Status styling */
QLabel[status="connected"] {
    color: #10b981;
    font-weight: bold;
}
QLabel[status="connecting"] {
    color: #f59e0b;
    font-weight: bold;
}
QLabel[status="disconnected"] {
    color: #ef4444;
    font-weight: bold;
}

/* Table Widget styling */
QTableWidget {
    background-color: #1e1e24;
    border: 1px solid #2e2e38;
    gridline-color: #2e2e38;
    border-radius: 6px;
    color: #e2e8f0;
}

QTableWidget::item {
    padding: 5px;
}

QTableWidget::item:selected {
    background-color: #06b6d4;
    color: white;
}

QHeaderView::section {
    background-color: #2d2d38;
    color: #e2e8f0;
    padding: 6px;
    border: 1px solid #2e2e38;
    font-weight: bold;
}

QScrollBar:vertical {
    border: none;
    background: #121214;
    width: 8px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #3f3f4c;
    min-height: 20px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #06b6d4;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}

QFrame#plot_container {
    background-color: #1e1e24;
    border: 1px solid #2e2e38;
    border-radius: 8px;
}
"""

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Load Cell Monitor")
        self.resize(1200, 800)
        
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
        self.logger = DataLogger()
        self.calibration_data = self.logger.load_calibration() or {}
        self.active_calib_dialogs = [None] * 4
        self.serial_worker = SerialWorker()
        self.serial_worker.data_received.connect(self.on_data_received)
        self.serial_worker.connection_status.connect(self.on_connection_status)
        
        # Data buffers for plotting
        self.start_times = [time.time()] * 4
        self.time_data = [[], [], [], []]
        self.weight_data = [[], [], [], []]
        self.curves = []
        
        self.scale_controls = []
        self.logging_start_times = [None] * 4
        
        # Setup UI update timer for elapsed logging time
        self.ui_timer = QTimer(self)
        self.ui_timer.timeout.connect(self.update_logging_timers)
        self.ui_timer.start(1000)
        
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
        self.btn_refresh.setProperty("theme", "secondary")
        self.btn_refresh.clicked.connect(self.refresh_ports)
        self.btn_connect = QPushButton("Connect")
        self.btn_connect.setProperty("theme", "primary")
        self.btn_connect.clicked.connect(self.toggle_connection)
        
        self.lbl_status = QLabel("Disconnected")
        self.lbl_status.setObjectName("lbl_status")
        self.lbl_status.setProperty("status", "disconnected")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        conn_layout.addWidget(self.port_combo)
        conn_layout.addWidget(self.btn_refresh)
        conn_layout.addWidget(self.btn_connect)
        conn_layout.addWidget(self.lbl_status)
        conn_group.setLayout(conn_layout)
        left_panel.addWidget(conn_group)
        
        # Scale Controls Group
        scales_layout = QVBoxLayout()
        
        for i in range(4):
            cal_group = QGroupBox(f"Scale {i+1}")
            cal_layout = QGridLayout()
            
            # Tare / Calibrate
            btn_tare = QPushButton("Tare")
            btn_tare.setProperty("theme", "accent")
            btn_tare.clicked.connect(lambda checked, idx=i: self.tare_scale(idx))
            
            btn_cal = QPushButton("Open Calibration")
            btn_cal.setProperty("theme", "info")
            btn_cal.clicked.connect(lambda checked, idx=i: self.open_calibration(idx))
            
            # Measurement Logging
            le_meas_name = QLineEdit()
            le_meas_name.setPlaceholderText("Measurement Name")
            
            cb_interval = QComboBox()
            cb_interval.addItems(["5", "10", "15", "30", "60", "120"])
            cb_interval.setCurrentText("30")
            
            btn_start_stop = QPushButton("Start Logging")
            btn_start_stop.setProperty("theme", "success")
            btn_start_stop.clicked.connect(lambda checked, idx=i: self.toggle_logging(idx))
            
            lbl_timer = QLabel("00:00:00")
            lbl_timer.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_timer.setStyleSheet("font-family: monospace; font-size: 13px; color: #888888; font-weight: bold;")
            
            # Layout logic
            cal_layout.addWidget(btn_tare, 0, 0)
            cal_layout.addWidget(btn_cal, 0, 1)
            
            # Add a separator line
            line = QWidget()
            line.setFixedHeight(2)
            line.setStyleSheet("background-color: #3f3f4c;")
            cal_layout.addWidget(line, 1, 0, 1, 2)
            
            cal_layout.addWidget(QLabel("Name:"), 2, 0)
            cal_layout.addWidget(le_meas_name, 2, 1)
            cal_layout.addWidget(QLabel("Interval (s):"), 3, 0)
            cal_layout.addWidget(cb_interval, 3, 1)
            cal_layout.addWidget(btn_start_stop, 4, 0)
            cal_layout.addWidget(lbl_timer, 4, 1)
            
            self.scale_controls.append({
                'le_name': le_meas_name,
                'cb_interval': cb_interval,
                'btn_start_stop': btn_start_stop,
                'lbl_timer': lbl_timer
            })
            
            cal_group.setLayout(cal_layout)
            scales_layout.addWidget(cal_group)
            
        left_panel.addLayout(scales_layout)
        left_panel.addStretch()
        
        # Version Label
        lbl_version = QLabel("Rémy Willemet — Load Cell Monitor v2.0.0")
        lbl_version.setStyleSheet("color: #64748b; font-size: 10px; font-weight: bold; padding: 4px;")
        left_panel.addWidget(lbl_version)
        
        main_layout.addLayout(left_panel, 1)
        
        # Right Panel (Plots)
        plot_layout = QGridLayout()
        self.plots = []
        self.curves = []
        self.plot_calib_labels = []
        
        for i in range(4):
            # Create QFrame container for the plot card
            plot_container = QFrame()
            plot_container.setObjectName("plot_container")
            container_layout = QVBoxLayout(plot_container)
            container_layout.setContentsMargins(10, 10, 10, 10)
            container_layout.setSpacing(5)
            
            # Header
            header_layout = QHBoxLayout()
            lbl_title = QLabel(f"Scale {i+1}")
            lbl_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #06b6d4;")
            
            lbl_calib = QLabel("")
            lbl_calib.setStyleSheet("font-size: 11px; color: #a0aec0; font-style: italic; font-weight: normal;")
            
            btn_clear = QPushButton("Clear")
            btn_clear.setProperty("theme", "secondary")
            btn_clear.setFixedWidth(60)
            btn_clear.setFixedHeight(24)
            btn_clear.setStyleSheet("font-size: 10px; padding: 2px 5px;")
            btn_clear.clicked.connect(lambda checked, idx=i: self.clear_scale_graph(idx))
            
            header_layout.addWidget(lbl_title)
            header_layout.addWidget(lbl_calib)
            header_layout.addStretch()
            header_layout.addWidget(btn_clear)
            container_layout.addLayout(header_layout)
            
            # Plot Widget
            plot = pg.PlotWidget()
            plot.setBackground('#1e1e24')
            plot.getAxis('left').setPen(pg.mkPen(color='#888888', width=1))
            plot.getAxis('bottom').setPen(pg.mkPen(color='#888888', width=1))
            plot.showGrid(x=True, y=True, alpha=0.15)
            plot.setXRange(0, 60, padding=0)
            
            label_style = {'color': '#a0aec0', 'font-size': '10pt'}
            plot.setLabel('left', 'Weight (g)', **label_style)
            plot.setLabel('bottom', 'Time (s)', **label_style)
            
            # Neon palette
            colors = [
                (6, 182, 212),   # Cyan
                (217, 70, 239),  # Magenta/Purple
                (16, 185, 129),  # Emerald
                (245, 158, 11)   # Orange
            ]
            curve = plot.plot(pen=pg.mkPen(color=colors[i], width=2))
            
            container_layout.addWidget(plot)
            
            self.plots.append(plot)
            self.curves.append(curve)
            self.plot_calib_labels.append(lbl_calib)
            
            row = i // 2
            col = i % 2
            plot_layout.addWidget(plot_container, row, col)
            
        main_layout.addLayout(plot_layout, 4)
    def refresh_ports(self):
        self.port_combo.clear()
        ports = self.serial_worker.get_available_ports()
        self.port_combo.addItems(ports)
        
    def toggle_connection(self):
        if self.serial_worker.is_running:
            self.btn_connect.setEnabled(False)
            self.lbl_status.setText("Disconnecting...")
            self.lbl_status.setProperty("status", "connecting")
            self.lbl_status.style().unpolish(self.lbl_status)
            self.lbl_status.style().polish(self.lbl_status)
            self.serial_worker.disconnect_port()
        else:
            port = self.port_combo.currentText()
            if port:
                self.btn_connect.setEnabled(False)
                self.lbl_status.setText("Connecting...")
                self.lbl_status.setProperty("status", "connecting")
                self.lbl_status.style().unpolish(self.lbl_status)
                self.lbl_status.style().polish(self.lbl_status)
                self.serial_worker.connect_port(port)
                
    @pyqtSlot(bool, str)
    def on_connection_status(self, connected, msg):
        self.lbl_status.setText(msg)
        self.btn_connect.setEnabled(True)
        if connected:
            self.btn_connect.setText("Disconnect")
            self.btn_connect.setProperty("theme", "danger")
            self.lbl_status.setProperty("status", "connected")
            for scale_idx, calib in self.calibration_data.items():
                if 'factor' in calib and 'offset' in calib:
                    self.serial_worker.send_command({
                        "cmd": "SET_CALIBRATION",
                        "scale": int(scale_idx),
                        "factor": calib['factor'],
                        "offset": calib['offset']
                    })
        else:
            self.btn_connect.setText("Connect")
            self.btn_connect.setProperty("theme", "primary")
            self.lbl_status.setProperty("status", "disconnected")
            
        self.btn_connect.style().unpolish(self.btn_connect)
        self.btn_connect.style().polish(self.btn_connect)
        self.lbl_status.style().unpolish(self.lbl_status)
        self.lbl_status.style().polish(self.lbl_status)
            
    @pyqtSlot(dict)
    def on_data_received(self, data):
        if 'type' in data and data['type'] == 'DATA':
            # Update logger
            self.logger.process_data(data)
            
            # Update plots
            for i in range(4):
                current_t = time.time() - self.start_times[i]
                self.time_data[i].append(current_t)
                self.weight_data[i].append(data['weight'][i])
            
                # Keep exactly last 60 seconds of data (with 5s buffer to prevent edge cutting)
                while self.time_data[i] and (current_t - self.time_data[i][0] > 65.0):
                    self.time_data[i].pop(0)
                    self.weight_data[i].pop(0)
                    
                x_min = max(0.0, current_t - 60.0)
                x_max = max(60.0, current_t)
                
                self.curves[i].setData(self.time_data[i], self.weight_data[i])
                self.plots[i].setXRange(x_min, x_max, padding=0)
                
                if self.active_calib_dialogs[i] is not None:
                    self.active_calib_dialogs[i].update_live_data(i, data['raw'][i])

        elif 'status' in data:
            if data['status'] == 'CALIBRATED':
                self.logger.log_calibration_history(data)
            print(f"Status update from MCU: {data}")

    def clear_scale_graph(self, scale_idx):
        self.start_times[scale_idx] = time.time()
        self.time_data[scale_idx].clear()
        self.weight_data[scale_idx].clear()
        self.curves[scale_idx].setData([], [])
        self.plots[scale_idx].setXRange(0.0, 60.0, padding=0)

    def clear_graphs(self):
        for i in range(4):
            self.clear_scale_graph(i)

    def update_logging_timers(self):
        for i in range(4):
            start_time = self.logging_start_times[i]
            controls = self.scale_controls[i]
            if start_time is not None:
                elapsed = int(time.time() - start_time)
                hours, remainder = divmod(elapsed, 3600)
                minutes, seconds = divmod(remainder, 60)
                time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                controls['lbl_timer'].setText(time_str)
                controls['lbl_timer'].setStyleSheet("font-family: monospace; font-size: 13px; color: #00f5d4; font-weight: bold;")
            else:
                controls['lbl_timer'].setText("00:00:00")
                controls['lbl_timer'].setStyleSheet("font-family: monospace; font-size: 13px; color: #888888; font-weight: bold;")

    def toggle_logging(self, scale_idx):
        controls = self.scale_controls[scale_idx]
        state = self.logger.scale_states[scale_idx]
        
        if state['is_logging']:
            self.logger.stop_logging(scale_idx)
            self.logging_start_times[scale_idx] = None
            controls['btn_start_stop'].setText("Start Logging")
            controls['btn_start_stop'].setProperty("theme", "success")
            controls['le_name'].setEnabled(True)
            controls['cb_interval'].setEnabled(True)
            controls['lbl_timer'].setText("00:00:00")
            controls['lbl_timer'].setStyleSheet("font-family: monospace; font-size: 13px; color: #888888; font-weight: bold;")
            
            # Clear calibration equation text when logging stops
            self.plot_calib_labels[scale_idx].setText("")
        else:
            name = controls['le_name'].text()
            interval = int(controls['cb_interval'].currentText())
            self.logger.start_logging(scale_idx, name, interval)
            self.logging_start_times[scale_idx] = time.time()
            controls['btn_start_stop'].setText("Stop Logging")
            controls['btn_start_stop'].setProperty("theme", "danger")
            controls['le_name'].setEnabled(False)
            controls['cb_interval'].setEnabled(False)
            controls['lbl_timer'].setText("00:00:00")
            controls['lbl_timer'].setStyleSheet("font-family: monospace; font-size: 13px; color: #00f5d4; font-weight: bold;")
            
            # Show calibration curve equation when logging starts
            calib = self.calibration_data.get(str(scale_idx))
            if calib and 'factor' in calib and 'offset' in calib:
                factor = calib['factor']
                offset = calib['offset']
                if factor != 0:
                    m = 1.0 / factor
                    c = -offset / factor
                    eq_str = f"Calib: W = {m:.5f}*Raw {c:+.2f}"
                    self.plot_calib_labels[scale_idx].setText(eq_str)
            else:
                self.plot_calib_labels[scale_idx].setText("Calib: Not calibrated")
            
        controls['btn_start_stop'].style().unpolish(controls['btn_start_stop'])
        controls['btn_start_stop'].style().polish(controls['btn_start_stop'])
            
    def tare_scale(self, scale_idx):
        self.serial_worker.send_command({"cmd": "TARE", "scale": scale_idx})
        
    def open_calibration(self, scale_idx):
        if self.active_calib_dialogs[scale_idx] is not None:
            self.active_calib_dialogs[scale_idx].activateWindow()
            return
            
        initial_data = self.calibration_data.get(str(scale_idx))
        dialog = CalibrationDialog(scale_idx, self, initial_calib_data=initial_data)
        self.active_calib_dialogs[scale_idx] = dialog
        
        if dialog.exec():
            calib = dialog.get_calibration_data()
            self.calibration_data[str(scale_idx)] = calib
            self.logger.save_calibration(self.calibration_data)
            
            if self.serial_worker.is_running:
                self.serial_worker.send_command({
                    "cmd": "SET_CALIBRATION",
                    "scale": scale_idx,
                    "factor": calib['factor'],
                    "offset": calib['offset']
                })
            
        self.active_calib_dialogs[scale_idx] = None

    def closeEvent(self, event):
        self.serial_worker.disconnect_port()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(THEME_QSS)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
