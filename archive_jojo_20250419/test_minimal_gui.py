import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel

print("Starting minimal GUI test...")

try:
    # 1. 創建 QApplication 實例
    print("Creating QApplication...")
    qapp = QApplication(sys.argv)
    print("QApplication created.")

    # 2. 創建一個簡單的主視窗
    print("Creating QMainWindow...")
    main_window = QMainWindow()
    main_window.setWindowTitle("Minimal GUI Test")
    main_window.setGeometry(200, 200, 300, 100) # 設定位置和大小
    print("QMainWindow created.")

    # 3. 在視窗中添加一個標籤
    label = QLabel("如果看到此視窗，表示 PyQt6 基本功能正常。", parent=main_window)
    label.setWordWrap(True)
    main_window.setCentralWidget(label) # 將標籤設為中心部件
    print("Label added.")

    # 4. 顯示視窗
    print("Showing main window...")
    main_window.show()
    print("main_window.show() called.")

    # 5. 啟動事件循環
    print("Starting event loop (qapp.exec())...")
    exit_code = qapp.exec()
    print(f"Event loop finished with exit code: {exit_code}")
    sys.exit(exit_code)

except Exception as e:
    print(f"An error occurred: {e}")
    import traceback
    traceback.print_exc()
    input("Press Enter to exit...") # 錯誤時暫停，方便查看
