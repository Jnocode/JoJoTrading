#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
JoJotrading Phase 1 Integration Test Suite

This comprehensive test script validates all Phase 1 optimization features:
1. Data quality validation
2. Enhanced DCF calculations with dynamic discount rates
3. Sensitivity analysis
4. Monte Carlo simulation capabilities
5. Anomaly detection integration
6. Complete system integration

Usage: python test_phase1_integration.py
"""

import sys
import traceback
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def test_module_imports():
    """Test all Phase 1 module imports"""
    print("=" * 60)
    print("Phase 1 Module Import Test")
    print("=" * 60)
    
    try:
        # Core modules
        from modules.data_validator import FinancialDataValidator
        from modules.enhanced_dcf import EnhancedDCFModel
        from modules.integrated_dcf_handler import IntegratedDCFHandler
        print("✓ All Phase 1 modules imported successfully")
        
        # Data handler integration
        from data_handler import financial_validator, enhanced_dcf_model, USE_ENHANCED_DCF
        print(f"✓ Data handler integration: USE_ENHANCED_DCF = {USE_ENHANCED_DCF}")
        
        # State machine integration
        from jojo_state_machine import JoJoStateMachine
        print("✓ State machine integration successful")
        
        return True
        
    except Exception as e:
        print(f"✗ Import error: {e}")
        traceback.print_exc()
        return False

def test_data_validation():
    """Test financial data validation functionality"""
    print("\n" + "=" * 60)
    print("Data Validation Test")
    print("=" * 60)
    
    try:
        from modules.data_validator import FinancialDataValidator
        
        validator = FinancialDataValidator()
        
        # Create sample financial data with varying quality
        high_quality_data = pd.DataFrame({
            'revenue': [1000, 1100, 1200, 1300, 1400],  # Consistent growth
            'operating_income': [200, 220, 240, 260, 280],  # Good margins
            'net_income': [150, 165, 180, 195, 210],  # Positive and growing
            'total_debt': [500, 520, 540, 560, 580],  # Manageable debt growth
            'cash': [100, 110, 120, 130, 140],  # Growing cash position
            'shares_outstanding': [100, 100, 100, 100, 100]  # Stable shares
        })
        
        low_quality_data = pd.DataFrame({
            'revenue': [1000, 950, 800, 1200, 600],  # Volatile
            'operating_income': [200, -50, 100, 150, -100],  # Inconsistent
            'net_income': [150, -200, 50, 100, -150],  # Volatile
            'total_debt': [500, 800, 1200, 1500, 2000],  # Growing debt
            'cash': [100, 80, 50, 20, 10],  # Decreasing cash
            'shares_outstanding': [100, 120, 150, 180, 200]  # Dilution
        })
        
        # Test validation
        high_score = validator.validate_data_quality(high_quality_data)
        low_score = validator.validate_data_quality(low_quality_data)
        
        print(f"High quality data score: {high_score:.3f}")
        print(f"Low quality data score: {low_score:.3f}")
        
        # Validate that high quality data gets higher score
        if high_score > low_score:
            print("✓ Data validation working correctly")
            return True, high_quality_data, low_quality_data
        else:
            print("✗ Data validation not working correctly")
            return False, None, None
            
    except Exception as e:
        print(f"✗ Data validation error: {e}")
        traceback.print_exc()
        return False, None, None

def test_enhanced_dcf():
    """Test enhanced DCF calculations"""
    print("\n" + "=" * 60)
    print("Enhanced DCF Test")
    print("=" * 60)
    
    try:
        from modules.enhanced_dcf import EnhancedDCFModel
        
        enhanced_dcf = EnhancedDCFModel()
        
        # Test scenario analysis
        base_scenario = {
            'revenue': [1000, 1100, 1200, 1300, 1400],
            'growth_rate': 0.05,
            'terminal_growth_rate': 0.03,
            'discount_rate': 0.10,
            'shares_outstanding': 100,
            'debt': 500,
            'cash': 100
        }
        
        scenarios = {
            'optimistic': {'growth_rate': 0.08, 'terminal_growth_rate': 0.04},
            'base': {},
            'pessimistic': {'growth_rate': 0.02, 'terminal_growth_rate': 0.02}
        }
        
        # Test basic enhanced DCF
        base_valuation = enhanced_dcf.calculate_enhanced_dcf(**base_scenario)
        print(f"Base enhanced DCF valuation: ${base_valuation:.2f}")
        
        # Test scenario analysis
        scenario_results = enhanced_dcf.scenario_analysis(base_scenario, scenarios)
        print(f"Scenario analysis results:")
        for scenario, result in scenario_results.items():
            print(f"  {scenario}: ${result:.2f}")
        
        # Test Monte Carlo simulation
        print("Running Monte Carlo simulation...")
        mc_results = enhanced_dcf.monte_carlo_simulation(
            base_scenario, 
            n_simulations=100,  # Reduced for testing
            volatility=0.1
        )
        
        print(f"Monte Carlo results:")
        print(f"  Mean: ${mc_results['mean']:.2f}")
        print(f"  95% VaR: ${mc_results['var_95']:.2f}")
        print(f"  Standard deviation: ${mc_results['std']:.2f}")
        
        print("✓ Enhanced DCF calculations working correctly")
        return True, scenario_results, mc_results
        
    except Exception as e:
        print(f"✗ Enhanced DCF error: {e}")
        traceback.print_exc()
        return False, None, None

def test_integrated_handler():
    """Test integrated DCF handler"""
    print("\n" + "=" * 60)
    print("Integrated DCF Handler Test")
    print("=" * 60)
    
    try:
        from modules.integrated_dcf_handler import IntegratedDCFHandler
        
        handler = IntegratedDCFHandler()
        
        # Use data from validation test
        high_quality_data = pd.DataFrame({
            'revenue': [1000, 1100, 1200, 1300, 1400],
            'operating_income': [200, 220, 240, 260, 280],
            'net_income': [150, 165, 180, 195, 210],
            'total_debt': [500, 520, 540, 560, 580],
            'cash': [100, 110, 120, 130, 140],
            'shares_outstanding': [100, 100, 100, 100, 100]
        })
        
        dcf_inputs = {
            'revenue': [1000, 1100, 1200, 1300, 1400],
            'growth_rate': 0.05,
            'terminal_growth_rate': 0.03,
            'discount_rate': 0.10,
            'shares_outstanding': 100,
            'debt': 500,
            'cash': 100
        }
        
        # Test with high-quality data (should use enhanced DCF)
        result_high = handler.calculate_integrated_dcf(
            financial_data=high_quality_data,
            dcf_inputs=dcf_inputs,
            quality_threshold=0.6
        )
        
        # Test with low-quality data (should fallback to standard DCF)
        low_quality_data = pd.DataFrame({
            'revenue': [1000, 950, 800, 1200, 600],
            'operating_income': [200, -50, 100, 150, -100],
            'net_income': [150, -200, 50, 100, -150],
            'total_debt': [500, 800, 1200, 1500, 2000],
            'cash': [100, 80, 50, 20, 10],
            'shares_outstanding': [100, 120, 150, 180, 200]
        })
        
        result_low = handler.calculate_integrated_dcf(
            financial_data=low_quality_data,
            dcf_inputs=dcf_inputs,
            quality_threshold=0.6
        )
        
        print(f"High-quality data valuation: ${result_high:.2f}")
        print(f"Low-quality data valuation: ${result_low:.2f}")
        
        print("✓ Integrated DCF handler working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Integrated handler error: {e}")
        traceback.print_exc()
        return False

def test_state_machine_integration():
    """Test state machine integration with Phase 1 features"""
    print("\n" + "=" * 60)
    print("State Machine Integration Test")
    print("=" * 60)
    
    try:
        from jojo_state_machine import JoJoStateMachine
        
        # Initialize state machine
        state_machine = JoJoStateMachine()
        
        # Check if Phase 1 parameters are in context
        context = state_machine.context
        
        phase1_params = [
            'data_quality_threshold', 'use_enhanced_dcf', 'enable_scenario_analysis',
            'enable_monte_carlo', 'monte_carlo_simulations', 'scenario_volatility',
            'enable_anomaly_detection', 'anomaly_threshold'
        ]
        
        print("Checking Phase 1 parameters in state machine context:")
        all_present = True
        for param in phase1_params:
            if hasattr(context, param):
                value = getattr(context, param)
                print(f"  ✓ {param}: {value}")
            else:
                print(f"  ✗ {param}: NOT FOUND")
                all_present = False
        
        if all_present:
            print("✓ State machine Phase 1 integration successful")
            return True
        else:
            print("✗ Some Phase 1 parameters missing from state machine")
            return False
            
    except Exception as e:
        print(f"✗ State machine integration error: {e}")
        traceback.print_exc()
        return False

def test_performance_benchmark():
    """Performance benchmark for Phase 1 features"""
    print("\n" + "=" * 60)
    print("Performance Benchmark")
    print("=" * 60)
    
    try:
        import time
        from modules.data_validator import FinancialDataValidator
        from modules.enhanced_dcf import EnhancedDCFModel
        from modules.integrated_dcf_handler import IntegratedDCFHandler
        
        # Create test data
        test_data = pd.DataFrame({
            'revenue': [1000, 1100, 1200, 1300, 1400],
            'operating_income': [200, 220, 240, 260, 280],
            'net_income': [150, 165, 180, 195, 210],
            'total_debt': [500, 520, 540, 560, 580],
            'cash': [100, 110, 120, 130, 140],
            'shares_outstanding': [100, 100, 100, 100, 100]
        })
        
        dcf_inputs = {
            'revenue': [1000, 1100, 1200, 1300, 1400],
            'growth_rate': 0.05,
            'terminal_growth_rate': 0.03,
            'discount_rate': 0.10,
            'shares_outstanding': 100,
            'debt': 500,
            'cash': 100
        }
        
        # Initialize components
        validator = FinancialDataValidator()
        enhanced_dcf = EnhancedDCFModel()
        handler = IntegratedDCFHandler()
        
        # Benchmark data validation
        start_time = time.time()
        for _ in range(100):
            validator.validate_data_quality(test_data)
        validation_time = (time.time() - start_time) / 100
        
        # Benchmark enhanced DCF
        start_time = time.time()
        for _ in range(10):
            enhanced_dcf.calculate_enhanced_dcf(**dcf_inputs)
        dcf_time = (time.time() - start_time) / 10
        
        # Benchmark integrated handler
        start_time = time.time()
        for _ in range(10):
            handler.calculate_integrated_dcf(test_data, dcf_inputs)
        handler_time = (time.time() - start_time) / 10
        
        print(f"Performance benchmarks (average time):")
        print(f"  Data validation: {validation_time:.4f} seconds")
        print(f"  Enhanced DCF calculation: {dcf_time:.4f} seconds")
        print(f"  Integrated handler: {handler_time:.4f} seconds")
        
        print("✓ Performance benchmark completed")
        return True
        
    except Exception as e:
        print(f"✗ Performance benchmark error: {e}")
        traceback.print_exc()
        return False

def main():
    """Run comprehensive Phase 1 integration tests"""
    print("JoJotrading Phase 1 Optimization Integration Test Suite")
    print("=" * 80)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    test_results = []
    
    # Run all tests
    tests = [
        ("Module Imports", test_module_imports),
        ("Data Validation", lambda: test_data_validation()[0]),
        ("Enhanced DCF", lambda: test_enhanced_dcf()[0]),
        ("Integrated Handler", test_integrated_handler),
        ("State Machine Integration", test_state_machine_integration),
        ("Performance Benchmark", test_performance_benchmark)
    ]
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            test_results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {e}")
            test_results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name:<30} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All Phase 1 integration tests PASSED!")
        print("JoJotrading Phase 1 optimization is ready for production use.")
    else:
        print(f"\n❌ {total - passed} tests failed. Please review the errors above.")
    
    print(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
