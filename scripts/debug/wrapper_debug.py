
import sys
import traceback
import os

print("Starting debug runner...")
try:
    print("Attempting to import test module...")
    # Add current dir to path
    sys.path.insert(0, os.getcwd())
    
    import tests.unit.ui.stage4_ui_test
    print("Import successful.")
    
    # Run tests manually
    import unittest
    
    with open('test_output.log', 'w', encoding='utf-8') as f:
        runner = unittest.TextTestRunner(stream=f, verbosity=2)
        suite = unittest.TestLoader().loadTestsFromModule(tests.unit.ui.stage4_ui_test)
        result = runner.run(suite)
        
    print(f"Tests finished. Failures: {len(result.failures)}, Errors: {len(result.errors)}")
    
except Exception:
    print("Exception during import:")
    traceback.print_exc()
except SystemExit as e:
    print(f"SystemExit detected: {e}")
except:
    print("Unknown error detected.")
    traceback.print_exc()
