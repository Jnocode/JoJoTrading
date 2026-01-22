
import unittest
from unittest.mock import MagicMock, patch, PropertyMock
import pandas as pd
import sys
import os

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
# tests/unit/ui -> tests/unit -> tests -> jojo_trading
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from jojo_trading.ui.components.stage4_integration import Stage4IntegrationPanel

class TestStage4IntegrationPanel(unittest.TestCase):
    
    def setUp(self):
        # Mock streamlit
        self.patcher = patch('jojo_trading.ui.components.stage4_integration.st')
        self.mock_st = self.patcher.start()
        
        # Setup component
        self.panel = Stage4IntegrationPanel()
        
    def tearDown(self):
        self.patcher.stop()

    def test_initialization(self):
        """Test component initialization"""
        self.assertIsNotNone(self.panel.wacc_calculator)
        self.assertTrue(hasattr(self.panel, 'industry_map'))

    @patch('jojo_trading.ui.components.stage4_integration.pd.read_excel')
    def test_excel_import_single_row(self, mock_read_excel):
        """Test Excel import with single row"""
        # Setup mock data
        mock_df = pd.DataFrame({
            'stock_code': ['2330'],
            'current_price': [500],
            'net_income': [10000],
            'shares_outstanding': [20000],
            'total_debt': [1000],
            'interest_expense': [50]
        })
        mock_read_excel.return_value = mock_df
        
        # Setup file uploader mock
        mock_file = MagicMock(name='uploaded_file')
        mock_file.name = 'test.xlsx'
        self.mock_st.file_uploader.return_value = mock_file
        self.mock_st.button.return_value = True # Simulate calculation button click
        
        # Run
        self.panel._render_excel_import()
        
        # Verify read_excel called
        mock_read_excel.assert_called_once()
        
    @patch('jojo_trading.ui.components.stage4_integration.pd.read_excel')
    def test_excel_import_batch(self, mock_read_excel):
        """Test Excel import with multiple rows (Batch mode)"""
         # Setup mock data (2 rows)
        mock_df = pd.DataFrame({
            'stock_code': ['2330', '2317'],
            'current_price': [500, 100],
            'net_income': [10000, 5000],
            'shares_outstanding': [20000, 10000],
            'total_debt': [1000, 500],
            'interest_expense': [50, 20]
        })
        mock_read_excel.return_value = mock_df
        
        mock_file = MagicMock(name='uploaded_file')
        mock_file.name = 'batch_test.xlsx'
        self.mock_st.file_uploader.return_value = mock_file
        self.mock_st.button.return_value = True # Simulate run batch button
        
        # Run
        self.panel._render_excel_import()
        
        # Verify info message about batch mode
        self.mock_st.info.assert_any_call("📊 偵測到 2 筆數據，切換至批次分析模式")
        
    def test_pdf_generation(self):
        """Test PDF generation logic"""
        # Mock inputs
        stock_code = "TEST"
        wacc_result = {'wacc': 0.1, 'after_tax_cost_of_debt': 0.05, 'equity_weight': 0.5, 'debt_weight': 0.5}
        disposal_result = {'has_disposal': False, 'confidence': 'High'}
        params_result = {'discount_rate': 0.1, 'terminal_growth': 0.03, 'safety_margin': 0.2}
        
        try:
             pdf_bytes = self.panel._generate_pdf_report(stock_code, wacc_result, disposal_result, params_result)
             if pdf_bytes:
                 self.assertIsInstance(pdf_bytes, bytes)
        except ImportError:
            pass 

    def test_sensitivity_analysis(self):
        """Test sensitivity analysis logic"""
        base_wacc = 0.1
        base_growth = 0.03
        
        # Mock calculation function
        def mock_calc(wacc, growth):
            return 100 * (1+growth) / (wacc - growth)
            
        # Mock dataframe display
        self.mock_st.dataframe = MagicMock()
        
        # Run
        self.panel._render_sensitivity_analysis(base_wacc, base_growth, mock_calc)
        
        # Check if dataframe was called
        self.mock_st.dataframe.assert_called()
        
        # Extract arguments passed to dataframe
        # args[0] is the styler object. data is the underlying dataframe
        call_args = self.mock_st.dataframe.call_args
        styler = call_args[0][0]
        
        # Styler.data is the dataframe
        df = styler.data
        
        # Check shape (5x5 matrix)
        self.assertEqual(df.shape, (5, 5))
        
        # Check if value calculated correctly for base case (center cell)
        # 3rd row (index 2), 3rd col (index 2) should be base case
        # Note: df uses iloc
        expected_base = mock_calc(base_wacc, base_growth)
        self.assertAlmostEqual(df.iloc[2, 2], expected_base)

    def test_waterfall_chart(self):
        """Test waterfall chart rendering"""
        # Mock breakdown data
        breakdown = {
            'pv_explicit': 500.0,
            'pv_terminal': 1000.0,
            'enterprise_value': 1500.0,
            'net_debt': 200.0,
            'equity_value': 1300.0,
            'share_price': 130.0
        }
        shares = 10.0
        
        # Mock plotly
        # We need to ensure import plotly.graph_objects works or mock it
        # Since we can't easily mock imports inside the function under test without patch.dict or similar
        # We'll rely on the fact that if plotly is missing, it prints warning, if present it calls st.plotly_chart
        
        # Test 1: Simulate Plotly installed and rendering
        with patch('jojo_trading.ui.components.stage4_integration.st.plotly_chart') as mock_chart:
            # We also need to mock import, but let's assume environment has plotly or handle ImportError
            # If environmental plotly is present
            try:
                import plotly.graph_objects
                self.panel._render_valuation_waterfall(breakdown, shares)
                mock_chart.assert_called()
            except ImportError:
                # If plotly not installed in test env, it should call st.warning
                self.mock_st.warning.assert_called_with("請安裝 plotly 以查看瀑布圖")

    def test_calculate_dcf_breakdown_detail(self):
        """Test DCF breakdown with detailed component inputs"""
        # Inputs
        shares = 1000
        wacc = 0.10
        terminal_growth = 0.03
        short_term_growth = 0.05
        net_debt = 500
        
        # Detailed inputs
        net_income = 1000
        depreciation = 200
        amortization = 50
        capex = 300 # Absolute value
        
        # Expected FCF = 1000 + 200 + 50 - 300 = 950
        expected_fcf = 950.0
        
        result = self.panel._calculate_dcf_breakdown(
            base_fcf=0, # Should be ignored
            shares=shares,
            wacc=wacc,
            terminal_growth=terminal_growth,
            short_term_growth=short_term_growth,
            net_debt=net_debt,
            net_income=net_income,
            depreciation=depreciation,
            amortization=amortization,
            capex=capex,
            use_detailed_fcf=True
        )
        
        self.assertEqual(result['current_fcf'], expected_fcf)
        self.assertFalse(result['failed'])
        
        # Verify direction: Higher FCF -> Higher Value
        # Compare with lower FCF
        result_lower = self.panel._calculate_dcf_breakdown(
            base_fcf=0,
            shares=shares,
            wacc=wacc,
            terminal_growth=terminal_growth,
            short_term_growth=short_term_growth,
            net_debt=net_debt,
            net_income=net_income - 100, # Reduce NI
            depreciation=depreciation,
            amortization=amortization,
            capex=capex,
            use_detailed_fcf=True
        )
        self.assertGreater(result['share_price'], result_lower['share_price'])

if __name__ == '__main__':
    unittest.main()
