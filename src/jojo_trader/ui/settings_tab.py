
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QSpinBox, QCheckBox, QGroupBox, 
                             QPushButton, QMessageBox, QSpacerItem, QSizePolicy, QLineEdit)
from PySide6.QtCore import Qt
try:
    from jojo_trading.core.stock_database import StockDatabase
except ImportError:
    StockDatabase = None

try:
    from jojo_trading.data_sources.news_cache import NewsCacheManager
except ImportError:
    NewsCacheManager = None

class GeneralSettingsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = StockDatabase() if StockDatabase else None
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # --- Appearance ---
        grp_appearance = QGroupBox("🎨 外觀與顯示 (Appearance)")
        grp_appearance.setStyleSheet("QGroupBox { border: 1px solid #555; border-radius: 5px; margin-top: 20px; font-weight: bold; color: #4CAF50; } QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 3px; }")
        layout_app = QVBoxLayout(grp_appearance)
        
        # Font Size
        row_font = QHBoxLayout()
        row_font.addWidget(QLabel("字體大小 (Font Size):"))
        self.combo_font = QComboBox()
        self.combo_font.addItems(["10 (Small)", "12 (Medium)", "14 (Large)", "16 (Extra Large)"])
        row_font.addWidget(self.combo_font)
        row_font.addStretch()
        layout_app.addLayout(row_font)
        
        # Theme
        row_theme = QHBoxLayout()
        row_theme.addWidget(QLabel("主題顏色 (Theme):"))
        self.combo_theme = QComboBox()
        self.combo_theme.addItems(["Dark (預設)", "Light (開發中)"])
        row_theme.addWidget(self.combo_theme)
        row_theme.addStretch()
        layout_app.addLayout(row_theme)
        
        grp_appearance.setLayout(layout_app)
        layout.addWidget(grp_appearance)
        
        # --- Trading & Data ---
        grp_trading = QGroupBox("📈 交易與數據 (Trading & Data)")
        grp_trading.setStyleSheet("QGroupBox { border: 1px solid #555; border-radius: 5px; margin-top: 20px; font-weight: bold; color: #2196F3; } QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 3px; }")
        layout_trade = QVBoxLayout(grp_trading)
        
        # Default Qty
        row_qty = QHBoxLayout()
        row_qty.addWidget(QLabel("預設下單口數 (Default Qty):"))
        self.spin_qty = QSpinBox()
        self.spin_qty.setRange(1, 100)
        row_qty.addWidget(self.spin_qty)
        row_qty.addStretch()
        layout_trade.addLayout(row_qty)
        
        # Update Rate
        row_rate = QHBoxLayout()
        row_rate.addWidget(QLabel("行情更新頻率 (Update Rate):"))
        self.combo_rate = QComboBox()
        self.combo_rate.addItems(["Realtime (不限制)", "Fast (0.5s)", "Normal (1.0s)", "Slow (2.0s)"])
        row_rate.addWidget(self.combo_rate)
        row_rate.addStretch()
        layout_trade.addLayout(row_rate)
        
        grp_trading.setLayout(layout_trade)
        layout.addWidget(grp_trading)
        
        # --- System & Notifications ---
        grp_sys = QGroupBox("🔔 系統通知 (System)")
        grp_sys.setStyleSheet("QGroupBox { border: 1px solid #555; border-radius: 5px; margin-top: 20px; font-weight: bold; color: #FF9800; } QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 3px; }")
        layout_sys = QVBoxLayout(grp_sys)
        
        self.chk_sound = QCheckBox("啟用成交音效 (Enable Trade Sound)")
        self.chk_autoconnect = QCheckBox("啟動時自動連線 (Auto Connect on Launch)")
        
        layout_sys.addWidget(self.chk_sound)
        layout_sys.addWidget(self.chk_autoconnect)
        
        grp_sys.setLayout(layout_sys)
        layout.addWidget(grp_sys)
        
        # AI Settings Layout
        grp_ai = QGroupBox("🤖 AI 引擎 (AI Engine)")
        grp_ai.setStyleSheet("QGroupBox { border: 1px solid #555; border-radius: 5px; margin-top: 20px; font-weight: bold; color: #E91E63; } QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 3px; }")
        layout_ai = QVBoxLayout(grp_ai)
        
        row_ai = QHBoxLayout()
        row_ai.addWidget(QLabel("AI 分析引擎 (Provider):"))
        self.combo_ai = QComboBox()
        self.combo_ai.addItems([
            "Gemini (免費雲端)",
            "Groq (極速雲端)",
            "Ollama (本機離線)",
        ])
        self.combo_ai.currentIndexChanged.connect(self._on_ai_provider_changed)
        row_ai.addWidget(self.combo_ai)
        row_ai.addStretch()
        layout_ai.addLayout(row_ai)

        # --- Cloud API Keys ---
        # Gemini API Key
        row_gemini_key = QHBoxLayout()
        self.lbl_gemini = QLabel("Gemini API Key:")
        row_gemini_key.addWidget(self.lbl_gemini)
        self.input_gemini_key = QLineEdit()
        self.input_gemini_key.setPlaceholderText("留空則使用 .env 預設金鑰 (免費: aistudio.google.com)")
        self.input_gemini_key.setEchoMode(QLineEdit.Password)
        row_gemini_key.addWidget(self.input_gemini_key)
        layout_ai.addLayout(row_gemini_key)

        # Groq API Key
        row_groq_key = QHBoxLayout()
        self.lbl_groq = QLabel("Groq API Key:")
        row_groq_key.addWidget(self.lbl_groq)
        self.input_groq_key = QLineEdit()
        self.input_groq_key.setPlaceholderText("留空則使用 .env 預設金鑰 (免費: console.groq.com)")
        self.input_groq_key.setEchoMode(QLineEdit.Password)
        row_groq_key.addWidget(self.input_groq_key)
        layout_ai.addLayout(row_groq_key)

        # --- Ollama Local Settings ---
        row_ollama_url = QHBoxLayout()
        self.lbl_ollama_url = QLabel("Ollama URL:")
        row_ollama_url.addWidget(self.lbl_ollama_url)
        self.input_ollama_url = QLineEdit()
        self.input_ollama_url.setPlaceholderText("http://localhost:11434")
        self.input_ollama_url.setText("http://localhost:11434")
        row_ollama_url.addWidget(self.input_ollama_url)
        layout_ai.addLayout(row_ollama_url)

        row_ollama_model = QHBoxLayout()
        self.lbl_ollama_model = QLabel("Ollama Model:")
        row_ollama_model.addWidget(self.lbl_ollama_model)
        self.input_ollama_model = QComboBox()
        self.input_ollama_model.setEditable(True)
        self.input_ollama_model.setPlaceholderText("gemma3:4b (建議 4B+ 模型)")
        self.input_ollama_model.setCurrentText("gemma3:4b")
        self.input_ollama_model.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        row_ollama_model.addWidget(self.input_ollama_model)
        
        self.btn_refresh_ollama = QPushButton("🔄")
        self.btn_refresh_ollama.setToolTip("取得本機模型清單")
        self.btn_refresh_ollama.setFixedSize(30, 24)
        self.btn_refresh_ollama.clicked.connect(self._refresh_ollama_models)
        row_ollama_model.addWidget(self.btn_refresh_ollama)
        
        layout_ai.addLayout(row_ollama_model)

        # Test Connection Button
        row_test = QHBoxLayout()
        row_test.addStretch()
        self.btn_test_ai = QPushButton("🔗 測試 AI 連線 (Test Connection)")
        self.btn_test_ai.setMinimumHeight(32)
        self.btn_test_ai.setStyleSheet("background-color: #2196F3; font-weight: bold;")
        self.btn_test_ai.clicked.connect(self._test_ai_connection)
        row_test.addWidget(self.btn_test_ai)
        layout_ai.addLayout(row_test)
        
        grp_ai.setLayout(layout_ai)
        layout.addWidget(grp_ai)
        
        # --- News Dashboard Settings ---
        grp_news = QGroupBox("📰 新聞儀表板 (News Dashboard)")
        grp_news.setStyleSheet("QGroupBox { border: 1px solid #555; border-radius: 5px; margin-top: 20px; font-weight: bold; color: #00BCD4; } QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 3px; }")
        layout_news = QVBoxLayout(grp_news)
        
        # Scope Type
        row_scope = QHBoxLayout()
        row_scope.addWidget(QLabel("自動抓取範圍單位 (Scope Type):"))
        self.cmb_news_scope_type = QComboBox()
        self.cmb_news_scope_type.addItems(["則 (Items)", "小時 (Hours)", "天 (Days)"])
        row_scope.addWidget(self.cmb_news_scope_type)
        row_scope.addStretch()
        layout_news.addLayout(row_scope)
        
        # Scope Value
        row_scope_val = QHBoxLayout()
        row_scope_val.addWidget(QLabel("自動抓取數值 (Scope Value):"))
        self.spin_news_scope_value = QSpinBox()
        self.spin_news_scope_value.setRange(1, 1000)
        self.spin_news_scope_value.setValue(20)
        row_scope_val.addWidget(self.spin_news_scope_value)
        row_scope_val.addStretch()
        layout_news.addLayout(row_scope_val)
        
        # Load Amount
        row_load = QHBoxLayout()
        row_load.addWidget(QLabel("單次載入更多數量 (Load Amount):"))
        self.spin_news_load_amount = QSpinBox()
        self.spin_news_load_amount.setRange(3, 20)
        self.spin_news_load_amount.setValue(5)
        row_load.addWidget(self.spin_news_load_amount)
        row_load.addStretch()
        layout_news.addLayout(row_load)
        
        # Auto Refresh Interval
        row_refresh = QHBoxLayout()
        row_refresh.addWidget(QLabel("自動刷新頻率(秒) (Auto Refresh Sec):"))
        self.spin_news_auto_refresh = QSpinBox()
        self.spin_news_auto_refresh.setRange(10, 600)
        self.spin_news_auto_refresh.setValue(60)
        row_refresh.addWidget(self.spin_news_auto_refresh)
        row_refresh.addStretch()
        layout_news.addLayout(row_refresh)
        
        # Clear Cache Button
        row_cache = QHBoxLayout()
        self.btn_clear_cache = QPushButton("🗑️ 清除 AI 分析快取")
        self.btn_clear_cache.setMinimumHeight(32)
        self.btn_clear_cache.setStyleSheet("background-color: #D32F2F; font-weight: bold;")
        self.btn_clear_cache.clicked.connect(self._clear_news_cache)
        row_cache.addWidget(self.btn_clear_cache)
        self.lbl_cache_count = QLabel("")
        self.lbl_cache_count.setStyleSheet("color: #888; font-size: 11px;")
        row_cache.addWidget(self.lbl_cache_count)
        row_cache.addStretch()
        layout_news.addLayout(row_cache)
        
        grp_news.setLayout(layout_news)
        layout.addWidget(grp_news)
        
        layout.addStretch()
        
        # --- Action Buttons ---
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("💾 儲存設定 (Save Settings)")
        btn_save.setMinimumHeight(40)
        btn_save.setStyleSheet("background-color: #4CAF50; font-weight: bold; font-size: 14px;")
        btn_save.clicked.connect(self.save_settings)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_save)
        
        layout.addLayout(btn_layout)

    def load_settings(self):
        if not self.db: return
        
        # Font
        font_size = self.db.get_setting("font_size", "10")
        index = self.combo_font.findText(f"{font_size} ", Qt.MatchStartsWith)
        if index >= 0: self.combo_font.setCurrentIndex(index)
        
        # Theme
        theme = self.db.get_setting("theme", "Dark")
        index = self.combo_theme.findText(theme, Qt.MatchStartsWith)
        if index >= 0: self.combo_theme.setCurrentIndex(index)
        
        # Qty
        qty = self.db.get_setting("default_qty", "1")
        self.spin_qty.setValue(int(qty))
        
        # Rate
        rate = self.db.get_setting("update_rate", "Fast")
        index = self.combo_rate.findText(rate, Qt.MatchStartsWith)
        if index >= 0: self.combo_rate.setCurrentIndex(index)
        
        # Bools
        sound = self.db.get_setting("enable_sound", "True") == "True"
        self.chk_sound.setChecked(sound)
        
        auto = self.db.get_setting("auto_connect", "True") == "True"
        self.chk_autoconnect.setChecked(auto)
        
        # AI Provider
        provider = self.db.get_setting("ai_provider", "Gemini")
        index = self.combo_ai.findText(provider, Qt.MatchStartsWith)
        if index >= 0: self.combo_ai.setCurrentIndex(index)
        
        # API Keys
        gemini_key = self.db.get_setting("gemini_api_key", "")
        self.input_gemini_key.setText(gemini_key)
        
        groq_key = self.db.get_setting("groq_api_key", "")
        self.input_groq_key.setText(groq_key)

        # Ollama Settings
        ollama_url = self.db.get_setting("ollama_url", "http://localhost:11434")
        self.input_ollama_url.setText(ollama_url)
        
        ollama_model = self.db.get_setting("ollama_model", "gemma3:4b")
        self.input_ollama_model.setCurrentText(ollama_model)

        # News Dashboard Settings
        news_scope_type = self.db.get_setting("news_scope_type", "則 (Items)")
        idx = self.cmb_news_scope_type.findText(news_scope_type, Qt.MatchStartsWith)
        if idx >= 0: self.cmb_news_scope_type.setCurrentIndex(idx)
        
        news_scope_value = self.db.get_setting("news_scope_value", "20")
        self.spin_news_scope_value.setValue(int(news_scope_value))
        
        news_load_amount = self.db.get_setting("news_load_amount", "5")
        self.spin_news_load_amount.setValue(int(news_load_amount))

        news_auto_refresh = self.db.get_setting("news_auto_refresh", "60")
        self.spin_news_auto_refresh.setValue(int(news_auto_refresh))

        # Update cache count label
        self._update_cache_count()

        # Trigger visibility update
        self._on_ai_provider_changed()

    def save_settings(self):
        if not self.db: return
        
        try:
            # Font: Extract number "10" from "10 (Small)"
            font_txt = self.combo_font.currentText()
            font_val = font_txt.split()[0]
            self.db.set_setting("font_size", font_val)
            
            # Theme
            theme_txt = self.combo_theme.currentText()
            theme_val = theme_txt.split()[0]
            self.db.set_setting("theme", theme_val)
            
            # Qty
            self.db.set_setting("default_qty", str(self.spin_qty.value()))
            
            # Rate
            rate_txt = self.combo_rate.currentText()
            rate_val = rate_txt.split()[0] # Store "Fast", "Realtime" etc. or maybe store full string
            # Let's store full string or first word. Store first word is cleaner for logic.
            # Actually, let's store the whole thing or a key?
            # Storing "Fast" is fine if we match it later.
            # But "Fast (0.5s)" is what we loaded.
            # Let's simple store what is loaded to match next time.
            # But for logic, "Fast" is better.
            # We implemented `findText(rate, MatchStartsWith)` so storing "Fast" works.
            self.db.set_setting("update_rate", rate_txt.split()[0]) 
            
            self.db.set_setting("enable_sound", str(self.chk_sound.isChecked()))
            self.db.set_setting("auto_connect", str(self.chk_autoconnect.isChecked()))
            
            # AI Provider
            ai_txt = self.combo_ai.currentText()
            ai_val = ai_txt.split()[0]
            self.db.set_setting("ai_provider", ai_val)
            
            # API Keys
            self.db.set_setting("gemini_api_key", self.input_gemini_key.text().strip())
            self.db.set_setting("groq_api_key", self.input_groq_key.text().strip())

            # Ollama Settings
            self.db.set_setting("ollama_url", self.input_ollama_url.text().strip() or "http://localhost:11434")
            self.db.set_setting("ollama_model", self.input_ollama_model.currentText().strip() or "gemma3:4b")
            
            # News Dashboard Settings
            scope_type_txt = self.cmb_news_scope_type.currentText().split()[0]
            self.db.set_setting("news_scope_type", scope_type_txt)
            self.db.set_setting("news_scope_value", str(self.spin_news_scope_value.value()))
            self.db.set_setting("news_load_amount", str(self.spin_news_load_amount.value()))
            self.db.set_setting("news_auto_refresh", str(self.spin_news_auto_refresh.value()))
            
            QMessageBox.information(self, "Success", "設定已儲存！\nAI 引擎與新聞設定將在下次分析/抓取時立即生效。")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"儲存失敗: {e}")

    def _on_ai_provider_changed(self):
        """根據選擇的 Provider 顯示/隱藏對應的設定欄位"""
        provider = self.combo_ai.currentText().split()[0]
        
        is_gemini = (provider == "Gemini")
        is_groq = (provider == "Groq")
        is_ollama = (provider == "Ollama")
        
        # Cloud keys
        self.lbl_gemini.setVisible(is_gemini)
        self.input_gemini_key.setVisible(is_gemini)
        self.lbl_groq.setVisible(is_groq)
        self.input_groq_key.setVisible(is_groq)
        
        # Ollama fields
        self.lbl_ollama_url.setVisible(is_ollama)
        self.input_ollama_url.setVisible(is_ollama)
        self.lbl_ollama_model.setVisible(is_ollama)
        self.input_ollama_model.setVisible(is_ollama)
        self.btn_refresh_ollama.setVisible(is_ollama)

    def _refresh_ollama_models(self):
        """從 Ollama URL 取得本機已安裝的模型清單"""
        url = self.input_ollama_url.text().strip() or "http://localhost:11434"
        try:
            import requests as req
            resp = req.get(f"{url}/api/tags", timeout=3)
            if resp.status_code == 200:
                models = [m.get("name") for m in resp.json().get("models", [])]
                if models:
                    current = self.input_ollama_model.currentText()
                    self.input_ollama_model.clear()
                    self.input_ollama_model.addItems(models)
                    if current in models:
                        self.input_ollama_model.setCurrentText(current)
                    else:
                        self.input_ollama_model.setCurrentText(models[0])
                    QMessageBox.information(self, "成功", f"已更新模型清單，共找到 {len(models)} 個模型。")
                else:
                    QMessageBox.warning(self, "警告", "連線成功但找不到任何模型。")
            else:
                QMessageBox.warning(self, "錯誤", f"取得模型失敗，狀態碼: {resp.status_code}")
        except Exception as e:
            QMessageBox.critical(self, "連線錯誤", f"無法連接到 Ollama:\n{e}")

    def _test_ai_connection(self):
        """測試當前選擇的 AI Provider 是否可以連線"""
        provider = self.combo_ai.currentText().split()[0]
        
        try:
            import requests as req
            
            if provider == "Gemini":
                key = self.input_gemini_key.text().strip() or os.environ.get("GOOGLE_API_KEY", "")
                if not key:
                    QMessageBox.warning(self, "Missing Key", "請先輸入 Gemini API Key。\n免費申請: https://aistudio.google.com/apikey")
                    return
                key = key.strip("'\"")
                url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
                r = req.get(url, timeout=10)
                if r.status_code == 200:
                    models = [m['name'].split('/')[-1] for m in r.json().get('models', []) if 'generateContent' in str(m.get('supportedGenerationMethods', []))]
                    top_models = ', '.join(models[:5])
                    QMessageBox.information(self, "✅ Gemini 連線成功", f"API Key 有效！\n可用模型: {top_models}...")
                else:
                    QMessageBox.critical(self, "❌ 連線失敗", f"HTTP {r.status_code}: {r.text[:200]}")

            elif provider == "Groq":
                key = self.input_groq_key.text().strip() or os.environ.get("GROQ_API_KEY", "")
                if not key:
                    QMessageBox.warning(self, "Missing Key", "請先輸入 Groq API Key。\n免費申請: https://console.groq.com")
                    return
                key = key.strip("'\"")
                url = "https://api.groq.com/openai/v1/models"
                r = req.get(url, headers={"Authorization": f"Bearer {key}"}, timeout=10)
                if r.status_code == 200:
                    QMessageBox.information(self, "✅ Groq 連線成功", "API Key 有效！")
                else:
                    QMessageBox.critical(self, "❌ 連線失敗", f"HTTP {r.status_code}: {r.text[:200]}")

            elif provider == "Ollama":
                url = self.input_ollama_url.text().strip() or "http://localhost:11434"
                model = self.input_ollama_model.currentText().strip() or "gemma3:4b"
                r = req.get(f"{url}/api/tags", timeout=5)
                if r.status_code == 200:
                    available = [m['name'] for m in r.json().get('models', [])]
                    if model in available or any(model in m for m in available):
                        QMessageBox.information(self, "✅ Ollama 連線成功", f"模型 '{model}' 已就緒！\n所有模型: {', '.join(available[:8])}")
                    else:
                        QMessageBox.warning(self, "⚠️ Ollama 已連線但模型未安裝", f"'{model}' 未找到。\n已安裝模型: {', '.join(available) if available else '(無)'}\n\n請執行: ollama pull {model}")
                else:
                    QMessageBox.critical(self, "❌ 連線失敗", f"Ollama HTTP {r.status_code}")

        except req.exceptions.ConnectionError:
            if provider == "Ollama":
                QMessageBox.critical(self, "❌ 無法連線 Ollama", "請確認 Ollama 已啟動。\n下載: https://ollama.com")
            else:
                QMessageBox.critical(self, "❌ 網路錯誤", "無法連線到 AI 服務，請檢查網路。")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"測試失敗: {e}")

    def _update_cache_count(self):
        """Update the cache count label."""
        try:
            if NewsCacheManager:
                mgr = NewsCacheManager()
                count = mgr.get_count()
                self.lbl_cache_count.setText(f"目前 {count} 筆快取")
        except Exception:
            self.lbl_cache_count.setText("")

    def _clear_news_cache(self):
        """Clear all AI analysis cache with confirmation."""
        if not NewsCacheManager:
            QMessageBox.warning(self, "提示", "快取管理器未載入。")
            return
        reply = QMessageBox.question(
            self, "確認清除",
            "確定要清除所有 AI 分析快取嗎？\n下次抓取新聞時，所有項目都將需要重新 AI 分析。",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            mgr = NewsCacheManager()
            cleared = mgr.clear_all()
            self._update_cache_count()
            QMessageBox.information(self, "完成", f"已清除 {cleared} 筆 AI 分析快取。")
