
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QFrame, QGridLayout, 
    QSpinBox, QDoubleSpinBox, QProgressBar
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QFont

from jojo_trading.core.dcf_calculator import DCFCalculator

class DCFWorker(QThread):
    finished = Signal(dict)
    
    def __init__(self, code, params):
        super().__init__()
        self.code = code
        self.params = params
        
    def run(self):
        try:
            # Prepare financial data package
            # In a real app, we might need to fetch this if not provided
            financial_data = {
                'current_market_price': self.params.get('price', 0),
                'net_income_parent': self.params.get('net_income', 0) * 1e8, # Unit correction
                'shares_outstanding': self.params.get('shares', 0) * 1e8,
            }
            
            calc = DCFCalculator()
            # Pass user params
            result = calc.calculate_dcf(
                self.code,
                financial_data,
                discount_rate=self.params.get('discount', 0.08),
                growth_rate=self.params.get('growth_rate', 0.08),
                terminal_growth_rate=self.params.get('terminal_growth', 0.03),
                projection_years=self.params.get('years', 5)
            )
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit({'error': str(e)})

class DCFWidget(QWidget):
    """
    DCF Valuation Widget (Desktop Version)
    """
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title_lbl = QLabel("💰 DCF Valuation (估值分析)")
        title_lbl.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title_lbl.setStyleSheet("color: white; border-bottom: 1px solid #555; padding-bottom: 5px;")
        layout.addWidget(title_lbl)
        
        # --- Parameters Area ---
        param_group = QFrame()
        param_group.setStyleSheet("background-color: #2D2D2D; border-radius: 5px;")
        p_layout = QGridLayout(param_group)
        
        # Inputs
        self.spin_price = self.create_input(p_layout, "Price (股價):", 0, 0, 10000, 1)
        self.spin_net_income = self.create_input(p_layout, "Net Income (億):", 0, 2, 10000, 0.1)
        self.spin_shares = self.create_input(p_layout, "Shares (億股):", 1, 0, 500, 0.1)
        
        # Assumptions
        self.spin_discount = self.create_input(p_layout, "Discount (%):", 1, 2, 20, 0.1, 8.0)
        self.spin_growth = self.create_input(p_layout, "Growth (%):", 2, 0, 50, 0.1, 8.0)
        self.spin_terminal = self.create_input(p_layout, "Terminal (%):", 2, 2, 10, 0.1, 3.0)
        
        layout.addWidget(param_group)
        
        # Calculate Button
        self.btn_calc = QPushButton("Calculate Valuation (計算)")
        self.btn_calc.setStyleSheet("""
            QPushButton {
                background-color: #007ACC; 
                color: white; 
                padding: 8px; 
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #0098FF; }
        """)
        self.btn_calc.clicked.connect(self.run_calculation)
        layout.addWidget(self.btn_calc)
        
        # --- Result Area ---
        res_group = QFrame()
        res_group.setStyleSheet("background-color: #1E1E1E; border: 1px solid #444; border-radius: 5px; margin-top: 10px;")
        res_layout = QVBoxLayout(res_group)
        
        # Intrinsic Value
        self.lbl_value = QLabel("Intrinsic Value: ---") # e.g. $150.0
        self.lbl_value.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.lbl_value.setStyleSheet("color: #FFD700;") # Gold
        self.lbl_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        res_layout.addWidget(self.lbl_value)
        
        # Upside
        self.lbl_upside = QLabel("Upside: ---%")
        self.lbl_upside.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_upside.setFont(QFont("Segoe UI", 12))
        res_layout.addWidget(self.lbl_upside)
        
        layout.addWidget(res_group)
        layout.addStretch()
        
    def create_input(self, layout, label_text, row, col, max_val, step, default=0.0):
        lbl = QLabel(label_text)
        lbl.setStyleSheet("color: #AAA;")
        layout.addWidget(lbl, row, col)
        
        spin = QDoubleSpinBox()
        spin.setRange(0, max_val)
        spin.setSingleStep(step)
        spin.setValue(default)
        spin.setStyleSheet("background-color: #111; color: white; border: 1px solid #555;")
        layout.addWidget(spin, row, col+1)
        return spin

    def set_data(self, price, net_income=None, shares=None):
        """Pre-fill data from analysis tab"""
        if price: self.spin_price.setValue(price)
        if net_income: self.spin_net_income.setValue(net_income) # Expecting Billions
        if shares: self.spin_shares.setValue(shares) # Expecting Billions

    def run_calculation(self):
        self.btn_calc.setEnabled(False)
        self.btn_calc.setText("Calculating...")
        
        # Gather params
        params = {
            'price': self.spin_price.value(),
            'net_income': self.spin_net_income.value(),
            'shares': self.spin_shares.value(),
            'discount': self.spin_discount.value() / 100.0,
            'growth_rate': self.spin_growth.value() / 100.0,
            'terminal_growth': self.spin_terminal.value() / 100.0,
            'years': 5
        }
        
        # Run in thread
        # Note: We need 'code' but for widget generic use we can pass dummy if simple DCF
        self.worker = DCFWorker("GENERIC", params)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()
        
    def on_finished(self, result):
        self.btn_calc.setEnabled(True)
        self.btn_calc.setText("Calculate Valuation (計算)")
        
        if 'error' in result:
            self.lbl_value.setText("Error")
            self.lbl_upside.setText(result['error'])
            return
            
        val = result.get('intrinsic_value_per_share', 0)
        ret = result.get('potential_return', 0)
        
        self.lbl_value.setText(f"Intrinsic Value: ${val:,.2f}")
        
        upside_pct = ret * 100 if ret else 0
        color = "#66bb6a" if upside_pct > 0 else "#ef5350"
        self.lbl_upside.setText(f"Upside: {upside_pct:+.2f}%")
        self.lbl_upside.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: bold;")
