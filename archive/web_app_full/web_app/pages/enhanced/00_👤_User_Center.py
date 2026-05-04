"""
🌟 JoJo Trading 用戶管理系統
Phase 5: 商業化產品發布 - 用戶註冊與登入界面

核心功能:
- 用戶註冊與登入
- 訂閱方案選擇
- 功能權限管理
- 使用量監控
"""

import streamlit as st
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
import sys

# 添加專案路徑
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root / "src"))

class UserAuthSystem:
    """用戶認證系統"""
    
    def __init__(self):
        self.users_file = project_root / "user_configs" / "users.json"
        self.users_file.parent.mkdir(exist_ok=True)
        self.users = self.load_users()
        
        # 訂閱方案定義
        self.plans = {
            "free": {
                "name": "免費版",
                "price": 0,
                "features": [
                    "基礎 DCF 計算 (10 股票/月)",
                    "基本技術指標",
                    "台股數據",
                    "社群支援"
                ],
                "limits": {
                    "dcf_calculations": 10,
                    "api_calls": 0,
                    "reports": 1
                },
                "color": "#E3F2FD"
            },
            "professional": {
                "name": "專業版",
                "price": 29,
                "features": [
                    "無限制 DCF 計算",
                    "完整技術指標套件",
                    "AI 智能分析",
                    "多市場數據 (美股、港股)",
                    "高級圖表與報告",
                    "基礎 API 存取 (1000 calls/月)",
                    "電子郵件支援"
                ],
                "limits": {
                    "dcf_calculations": -1,  # 無限制
                    "api_calls": 1000,
                    "reports": 10
                },
                "color": "#E8F5E8"
            },
            "enterprise": {
                "name": "企業版",
                "price": 99,
                "features": [
                    "所有專業版功能",
                    "完整 API 存取 (無限制)",
                    "自定義報告",
                    "批量數據匯出",
                    "優先客服支援",
                    "白標解決方案",
                    "多用戶管理",
                    "SSO 整合"
                ],
                "limits": {
                    "dcf_calculations": -1,
                    "api_calls": -1,
                    "reports": -1
                },
                "color": "#FFF3E0"
            }
        }
        
    def load_users(self) -> dict:
        """載入用戶數據"""
        if self.users_file.exists():
            with open(self.users_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
        
    def save_users(self):
        """保存用戶數據"""
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(self.users, f, ensure_ascii=False, indent=2)
            
    def hash_password(self, password: str) -> str:
        """密碼雜湊"""
        return hashlib.sha256(password.encode()).hexdigest()
        
    def register_user(self, email: str, password: str, name: str, plan: str = "free") -> bool:
        """用戶註冊"""
        if email in self.users:
            return False
            
        user_data = {
            "email": email,
            "password": self.hash_password(password),
            "name": name,
            "plan": plan,
            "created_at": datetime.now().isoformat(),
            "last_login": None,
            "usage": {
                "dcf_calculations": 0,
                "api_calls": 0,
                "reports_generated": 0
            },
            "subscription_end": None
        }
        
        # 如果是付費方案，設定訂閱結束時間
        if plan != "free":
            user_data["subscription_end"] = (datetime.now() + timedelta(days=30)).isoformat()
            
        self.users[email] = user_data
        self.save_users()
        return True
        
    def authenticate_user(self, email: str, password: str) -> bool:
        """用戶認證"""
        if email not in self.users:
            return False
            
        stored_password = self.users[email]["password"]
        return stored_password == self.hash_password(password)
        
    def login_user(self, email: str):
        """用戶登入"""
        self.users[email]["last_login"] = datetime.now().isoformat()
        self.save_users()
        st.session_state["logged_in"] = True
        st.session_state["user_email"] = email
        st.session_state["user_data"] = self.users[email]
        
    def logout_user(self):
        """用戶登出"""
        for key in ["logged_in", "user_email", "user_data"]:
            if key in st.session_state:
                del st.session_state[key]
                
    def get_user_plan_info(self, email: str) -> dict:
        """獲取用戶方案資訊"""
        if email not in self.users:
            return self.plans["free"]
            
        user_plan = self.users[email]["plan"]
        return self.plans.get(user_plan, self.plans["free"])
        
    def check_feature_access(self, email: str, feature: str, amount: int = 1) -> bool:
        """檢查功能存取權限"""
        if email not in self.users:
            return False
            
        user_data = self.users[email]
        plan_info = self.get_user_plan_info(email)
        
        # 檢查功能限制
        if feature in plan_info["limits"]:
            limit = plan_info["limits"][feature]
            if limit == -1:  # 無限制
                return True
            elif limit == 0:  # 不允許
                return False
            else:
                current_usage = user_data["usage"].get(feature, 0)
                return current_usage + amount <= limit
                
        return True
        
    def record_usage(self, email: str, feature: str, amount: int = 1):
        """記錄使用量"""
        if email in self.users:
            if feature not in self.users[email]["usage"]:
                self.users[email]["usage"][feature] = 0
            self.users[email]["usage"][feature] += amount
            self.save_users()

def render_login_page():
    """渲染登入頁面"""
    st.title("🔐 用戶登入")
    
    with st.form("login_form"):
        email = st.text_input("📧 電子郵件", placeholder="your.email@example.com")
        password = st.text_input("🔒 密碼", type="password")
        submitted = st.form_submit_button("🚀 登入", use_container_width=True)
        
        if submitted:
            if not email or not password:
                st.error("❌ 請填寫所有欄位")
                return
                
            auth_system = UserAuthSystem()
            if auth_system.authenticate_user(email, password):
                auth_system.login_user(email)
                st.success("✅ 登入成功！")
                st.rerun()
            else:
                st.error("❌ 電子郵件或密碼錯誤")

def render_register_page():
    """渲染註冊頁面"""
    st.title("📝 用戶註冊")
    
    # 顯示訂閱方案比較
    auth_system = UserAuthSystem()
    st.subheader("💎 選擇您的方案")
    
    cols = st.columns(3)
    selected_plan = "free"
    
    for i, (plan_id, plan_info) in enumerate(auth_system.plans.items()):
        with cols[i]:
            with st.container():
                st.markdown(f"""
                <div style="background-color: {plan_info['color']}; padding: 20px; border-radius: 10px; margin: 10px 0;">
                    <h3 style="text-align: center; margin: 0;">{plan_info['name']}</h3>
                    <h2 style="text-align: center; color: #1f77b4;">${plan_info['price']}/月</h2>
                </div>
                """, unsafe_allow_html=True)
                
                for feature in plan_info['features']:
                    st.write(f"✅ {feature}")
                    
                if st.button(f"選擇 {plan_info['name']}", key=f"select_{plan_id}", use_container_width=True):
                    selected_plan = plan_id
                    st.session_state["selected_plan"] = plan_id
    
    # 註冊表單
    st.subheader("📋 註冊資訊")
    selected_plan = st.session_state.get("selected_plan", "free")
    
    with st.form("register_form"):
        name = st.text_input("👤 姓名", placeholder="請輸入您的姓名")
        email = st.text_input("📧 電子郵件", placeholder="your.email@example.com")
        password = st.text_input("🔒 密碼", type="password", placeholder="至少 8 個字符")
        confirm_password = st.text_input("🔒 確認密碼", type="password")
        
        agree_terms = st.checkbox("我同意服務條款和隱私政策")
        
        submitted = st.form_submit_button("🎯 立即註冊", use_container_width=True)
        
        if submitted:
            # 驗證表單
            if not all([name, email, password, confirm_password]):
                st.error("❌ 請填寫所有欄位")
                return
                
            if password != confirm_password:
                st.error("❌ 密碼不一致")
                return
                
            if len(password) < 8:
                st.error("❌ 密碼至少需要 8 個字符")
                return
                
            if not agree_terms:
                st.error("❌ 請同意服務條款")
                return
                
            # 執行註冊
            if auth_system.register_user(email, password, name, selected_plan):
                st.success(f"✅ 註冊成功！歡迎加入 JoJo Trading，已選擇 {auth_system.plans[selected_plan]['name']}")
                auth_system.login_user(email)
                st.rerun()
            else:
                st.error("❌ 該電子郵件已註冊")

def render_user_dashboard():
    """渲染用戶儀表板"""
    user_data = st.session_state["user_data"]
    auth_system = UserAuthSystem()
    plan_info = auth_system.get_user_plan_info(user_data["email"])
    
    st.title(f"👋 歡迎回來，{user_data['name']}！")
    
    # 用戶資訊卡片
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📊 當前方案", plan_info["name"])
    
    with col2:
        if user_data["subscription_end"]:
            end_date = datetime.fromisoformat(user_data["subscription_end"])
            days_left = (end_date - datetime.now()).days
            st.metric("⏰ 剩餘天數", f"{days_left} 天")
        else:
            st.metric("⏰ 方案狀態", "永久免費")
    
    with col3:
        last_login = user_data.get("last_login")
        if last_login:
            login_date = datetime.fromisoformat(last_login).strftime("%Y-%m-%d")
            st.metric("🕐 上次登入", login_date)
    
    # 使用量統計
    st.subheader("📈 使用量統計")
    
    usage_cols = st.columns(3)
    usage = user_data["usage"]
    limits = plan_info["limits"]
    
    with usage_cols[0]:
        dcf_used = usage.get("dcf_calculations", 0)
        dcf_limit = limits.get("dcf_calculations", 0)
        if dcf_limit == -1:
            st.metric("📊 DCF 計算", f"{dcf_used}", "無限制")
        else:
            st.metric("📊 DCF 計算", f"{dcf_used}/{dcf_limit}")
            if dcf_limit > 0:
                st.progress(min(dcf_used / dcf_limit, 1.0))
    
    with usage_cols[1]:
        api_used = usage.get("api_calls", 0)
        api_limit = limits.get("api_calls", 0)
        if api_limit == -1:
            st.metric("🔌 API 調用", f"{api_used}", "無限制")
        elif api_limit == 0:
            st.metric("🔌 API 調用", "不可用")
        else:
            st.metric("🔌 API 調用", f"{api_used}/{api_limit}")
            st.progress(min(api_used / api_limit, 1.0))
    
    with usage_cols[2]:
        reports_used = usage.get("reports_generated", 0)
        reports_limit = limits.get("reports", 1)
        if reports_limit == -1:
            st.metric("📋 報告生成", f"{reports_used}", "無限制")
        else:
            st.metric("📋 報告生成", f"{reports_used}/{reports_limit}")
            if reports_limit > 0:
                st.progress(min(reports_used / reports_limit, 1.0))
    
    # 功能快捷入口
    st.subheader("🚀 功能快捷入口")
    
    feature_cols = st.columns(4)
    
    with feature_cols[0]:
        if st.button("📊 DCF 估值計算", use_container_width=True):
            st.switch_page("pages/enhanced/02_📊_DCF_Calculator.py")
    
    with feature_cols[1]:
        if st.button("📈 技術分析", use_container_width=True):
            st.switch_page("pages/enhanced/03_📈_Technical_Analysis.py")
    
    with feature_cols[2]:
        if st.button("💼 投資組合", use_container_width=True):
            st.switch_page("pages/enhanced/04_💼_Portfolio_Manager.py")
    
    with feature_cols[3]:
        if "professional" in user_data["plan"] or "enterprise" in user_data["plan"]:
            if st.button("🤖 AI 分析", use_container_width=True):
                st.switch_page("pages/enhanced/advanced/05_📈_Advanced_Technical_Analysis.py")
        else:
            st.button("🔒 AI 分析 (需升級)", disabled=True, use_container_width=True)
    
    # 方案升級提示
    if user_data["plan"] == "free":
        st.subheader("⭐ 升級到專業版")
        st.info("升級到專業版可享受 AI 智能分析、多市場數據、無限 DCF 計算等強大功能！")
        if st.button("🚀 立即升級", use_container_width=True):
            st.info("💳 付費功能開發中，敬請期待！")
    
    # 登出按鈕
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 登出", use_container_width=True):
        auth_system.logout_user()
        st.rerun()

def main():
    """主應用"""
    st.set_page_config(
        page_title="JoJo Trading - 用戶中心",
        page_icon="👤",
        layout="wide"
    )
    
    # 檢查登入狀態
    if st.session_state.get("logged_in", False):
        render_user_dashboard()
    else:
        # 登入/註冊選項
        tab1, tab2 = st.tabs(["🔐 登入", "📝 註冊"])
        
        with tab1:
            render_login_page()
        
        with tab2:
            render_register_page()

if __name__ == "__main__":
    main()
