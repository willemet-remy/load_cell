import time
import numpy as np
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QDoubleSpinBox, QTableWidget, QTableWidgetItem, QHeaderView,
                             QMessageBox, QGroupBox)
from PyQt6.QtCore import pyqtSlot, QTimer, Qt
import pyqtgraph as pg

class CalibrationDialog(QDialog):
    def __init__(self, scale_idx, parent=None, initial_calib_data=None):
        super().__init__(parent)
        self.scale_idx = scale_idx
        self.setWindowTitle(f"Calibration - Scale {scale_idx + 1}")
        self.resize(800, 600)
        
        # Data
        self.current_raw = 0
        self.points = [] # list of dicts: {'raw': float, 'weight': float}
        self.factor = 1.0
        self.offset = 0
        
        # Averaging state
        self.is_averaging = False
        self.averaging_samples = []
        self.averaging_timer = QTimer()
        self.averaging_timer.timeout.connect(self.finish_averaging)
        
        if initial_calib_data and 'points' in initial_calib_data:
            self.points = initial_calib_data['points']
            
        self.init_ui()
        self.update_table()
        self.update_plot()
        
    def init_ui(self):
        main_layout = QHBoxLayout(self)
        
        # Left Panel (Controls)
        left_layout = QVBoxLayout()
        
        # Live Data Group
        live_group = QGroupBox("Live Data")
        live_layout = QVBoxLayout()
        self.lbl_raw = QLabel("Current Raw: 0")
        self.lbl_raw.setStyleSheet("color: #10b981; font-size: 16px; font-weight: bold;")
        live_layout.addWidget(self.lbl_raw)
        live_group.setLayout(live_layout)
        left_layout.addWidget(live_group)
        
        # Add Point Group
        add_group = QGroupBox("Add Point")
        add_layout = QVBoxLayout()
        
        h_wt = QHBoxLayout()
        h_wt.addWidget(QLabel("Known Weight (g):"))
        self.spin_weight = QDoubleSpinBox()
        self.spin_weight.setRange(0, 50000.0)
        self.spin_weight.setValue(0.0)
        h_wt.addWidget(self.spin_weight)
        add_layout.addLayout(h_wt)
        
        self.btn_add = QPushButton("Add Point (2s Avg)")
        self.btn_add.setProperty("theme", "info")
        self.btn_add.clicked.connect(self.start_averaging)
        add_layout.addWidget(self.btn_add)
        
        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("color: #06b6d4; font-weight: bold;")
        add_layout.addWidget(self.lbl_status)
        
        add_group.setLayout(add_layout)
        left_layout.addWidget(add_group)
        
        # Points Table
        table_group = QGroupBox("Calibration Points")
        table_layout = QVBoxLayout()
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Raw", "Weight (g)"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table_layout.addWidget(self.table)
        
        self.btn_remove = QPushButton("Remove Selected Point")
        self.btn_remove.setProperty("theme", "secondary")
        self.btn_remove.clicked.connect(self.remove_point)
        table_layout.addWidget(self.btn_remove)
        table_group.setLayout(table_layout)
        left_layout.addWidget(table_group)
        
        # Save / Close
        self.btn_apply = QPushButton("Apply & Save")
        self.btn_apply.setProperty("theme", "success")
        self.btn_apply.clicked.connect(self.accept) # Triggers QDialog.accept()
        left_layout.addWidget(self.btn_apply)
        
        main_layout.addLayout(left_layout, 1)
        
        # Right Panel (Plot)
        right_layout = QVBoxLayout()
        
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('#1e1e24')
        self.plot_widget.getAxis('left').setPen(pg.mkPen(color='#888888', width=1))
        self.plot_widget.getAxis('bottom').setPen(pg.mkPen(color='#888888', width=1))
        self.plot_widget.showGrid(x=True, y=True, alpha=0.15)
        
        label_style = {'color': '#a0aec0', 'font-size': '10pt'}
        self.plot_widget.setLabel('left', 'Weight (g)', **label_style)
        self.plot_widget.setLabel('bottom', 'Raw Value (Voltage)', **label_style)
        
        self.scatter = pg.ScatterPlotItem(size=10, pen=pg.mkPen(None), brush=pg.mkBrush(244, 63, 94, 255))
        self.plot_widget.addItem(self.scatter)
        self.fit_line = pg.PlotCurveItem(pen=pg.mkPen(color=(6, 182, 212), width=2))
        self.plot_widget.addItem(self.fit_line)
        right_layout.addWidget(self.plot_widget, 4)
        
        self.lbl_eq = QLabel("Equation: N/A\nR² = N/A")
        self.lbl_eq.setStyleSheet("font-size: 13px; font-weight: bold; color: #e2e8f0;")
        right_layout.addWidget(self.lbl_eq)
        
        main_layout.addLayout(right_layout, 2)
        
    @pyqtSlot(int, float)
    def update_live_data(self, scale_idx, raw_val):
        if scale_idx != self.scale_idx:
            return
        self.current_raw = raw_val
        self.lbl_raw.setText(f"Current Raw: {raw_val}")
        
        if self.is_averaging:
            self.averaging_samples.append(raw_val)
            
    def start_averaging(self):
        self.is_averaging = True
        self.averaging_samples = []
        self.btn_add.setEnabled(False)
        self.lbl_status.setText("Averaging... Please wait 2s")
        self.averaging_timer.setSingleShot(True)
        self.averaging_timer.start(2000) # 2 seconds
        
    def finish_averaging(self):
        self.is_averaging = False
        self.btn_add.setEnabled(True)
        
        if not self.averaging_samples:
            self.lbl_status.setText("Error: No data received!")
            return
            
        avg_raw = sum(self.averaging_samples) / len(self.averaging_samples)
        weight = self.spin_weight.value()
        
        self.points.append({'raw': avg_raw, 'weight': weight})
        self.lbl_status.setText(f"Added: {weight}g at {avg_raw:.1f} raw")
        
        self.update_table()
        self.update_plot()
        
    def remove_point(self):
        selected = self.table.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        del self.points[row]
        self.update_table()
        self.update_plot()
        
    def update_table(self):
        self.table.setRowCount(len(self.points))
        for row, pt in enumerate(self.points):
            self.table.setItem(row, 0, QTableWidgetItem(f"{pt['raw']:.1f}"))
            self.table.setItem(row, 1, QTableWidgetItem(f"{pt['weight']:.1f}"))
            
    def update_plot(self):
        raws = [p['raw'] for p in self.points]
        weights = [p['weight'] for p in self.points]
        
        self.scatter.setData(raws, weights)
        self.fit_line.setData([], [])
        self.lbl_eq.setText("Equation: N/A\nR² = N/A")
        self.factor = 1.0
        self.offset = 0
        
        if len(self.points) < 2:
            return
            
        # Linear Regression: Weight = m * Raw + c
        # numpy polyfit degree 1
        x = np.array(raws)
        y = np.array(weights)
        m, c = np.polyfit(x, y, 1)
        
        # Calculate R^2
        p = np.poly1d([m, c])
        yhat = p(x)
        ybar = np.sum(y)/len(y)
        ssreg = np.sum((yhat - ybar)**2)
        sstot = np.sum((y - ybar)**2)
        r_squared = ssreg / sstot if sstot != 0 else 1.0
        
        # Plot line extending beyond min/max points slightly
        x_min, x_max = min(x), max(x)
        span = x_max - x_min if x_max != x_min else 100
        x_line = np.array([x_min - span*0.1, x_max + span*0.1])
        y_line = m * x_line + c
        self.fit_line.setData(x_line, y_line)
        
        # HX711 translation
        # Weight = (Raw - offset) / factor
        # Raw = factor * Weight + offset
        # Weight = m * Raw + c  =>  Raw = (1/m) * Weight - c/m
        if m != 0:
            self.factor = 1.0 / m
            self.offset = int(-c / m)
        
        self.lbl_eq.setText(f"Weight = {m:.5f} * Raw {c:+.2f}\nR² = {r_squared:.4f}\n(MCU Factor: {self.factor:.2f}, Offset: {self.offset})")
        
    def get_calibration_data(self):
        return {
            'points': self.points,
            'factor': self.factor,
            'offset': self.offset
        }
