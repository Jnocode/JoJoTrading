
import subprocess
import requests
import os
from typing import Optional, Tuple

class NetworkManager:
    """網路連線管理器 - 用於資安控管與固定IP連線"""
    
    def __init__(self, safe_ip: Optional[str] = None, vpn_user: Optional[str] = None, vpn_pass: Optional[str] = None):
        self.safe_ip = safe_ip or os.getenv("SAFE_IP")
        self.connection_name = "固定IP" # Windows dial-up connection name
        self.vpn_user = vpn_user or os.getenv("VPN_USER")
        self.vpn_pass = vpn_pass or os.getenv("VPN_PASS")

    def get_current_ip(self) -> str:
        """獲取當前外部 IP"""
        try:
            response = requests.get('https://api.ipify.org', timeout=5)
            if response.status_code == 200:
                return response.text
        except Exception as e:
            print(f"Error checking IP: {e}")
        return "Unknown"

    def check_safety(self) -> Tuple[bool, str]:
        """檢查是否處於安全 IP 環境"""
        current_ip = self.get_current_ip()
        
        if not self.safe_ip:
            return True, f"未設定 SAFE_IP，目前 IP: {current_ip} (視為安全)"
            
        if current_ip == self.safe_ip:
            return True, f"IP 正確: {current_ip}"
        else:
            return False, f"IP 不符! 目前: {current_ip}, 預期: {self.safe_ip}"

    def auto_connect(self) -> Tuple[bool, str]:
        """嘗試自動連線到撥號/VPN (強制重連模式)"""
        
        # 1. Force Disconnect first
        print(f"🔄 Disconnecting '{self.connection_name}'...")
        disc_cmd = f'rasdial "{self.connection_name}" /DISCONNECT'
        subprocess.run(disc_cmd, capture_output=True, shell=True)
        import time
        time.sleep(2) # Wait for release
        
        # 2. Connect Strategy
        cmd = f'rasdial "{self.connection_name}"'
        
        if self.vpn_user and self.vpn_pass:
             # Hinet Hint Check
             if "hinet" in self.vpn_user and "@ip.hinet.net" not in self.vpn_user:
                 print(f"⚠️ Warning: VPN User '{self.vpn_user}' might need '@ip.hinet.net' for Fixed IP.")
                 
             print(f"🔑 Using Provided Credentials: User='{self.vpn_user}'")
             cmd += f' "{self.vpn_user}" "{self.vpn_pass}"'
        else:
             print(f"💾 Using Stored Windows Credentials (No specific user provided)")
             
        try:
            print(f"🔄 Dialing {self.connection_name}...")
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
            
            # Print output for debugging
            if result.stdout.strip(): print(f"📄 Dial Output: {result.stdout.strip()}")
            if result.stderr.strip(): print(f"📄 Dial Error: {result.stderr.strip()}")

            if result.returncode == 0:
                # 3. Verify if it's actually in recent connections
                check = subprocess.run("rasdial", capture_output=True, text=True, shell=True)
                if self.connection_name in check.stdout:
                    return True, "連線指令成功且已確認連線"
                else:
                    return False, "連線指令回傳成功，但連線清單中未發現 (可能秒斷)"
            
            return False, f"連線失敗 (Code {result.returncode})"
            
        except Exception as e:
            return False, f"執行錯誤: {e}"


    def render_sidebar(self, st):
        """Standardized Sidebar UI for all pages"""
        with st.sidebar.expander("🛡️ 網路安全監控", expanded=True):
            is_safe, msg = self.check_safety()
            
            # Initialize Session State for Auto-Connect
            if "network_auto_tried" not in st.session_state:
                st.session_state.network_auto_tried = 0
            
            if is_safe:
                st.success("✅ 網路環境安全")
                st.caption(f"IP: {self.get_current_ip()}")
                # Reset retry count on success
                st.session_state.network_auto_tried = 0
            else:
                st.error("⚠️ 非固定 IP 環境")
                st.caption(f"目前 IP: {self.get_current_ip()}")
                
                # Auto Connect Logic
                if st.session_state.network_auto_tried < 1: # Try once automatically
                    st.warning("🔄 偵測到異常，正在自動連線...")
                    with st.spinner("🚀 啟動自動連線中..."):
                        success, log = self.auto_connect()
                        st.session_state.network_auto_tried += 1
                        
                        if success:
                            st.success(f"連線成功！正在重整...")
                            st.rerun()
                        else:
                            st.error(f"自動連線失敗: {log}")
                else:
                    # Fallback to manual button if auto failed
                    st.warning("自動連線已嘗試與失敗。")
                    if st.button("🚀 手動重試連線", key="btn_manual_connect"):
                        st.session_state.network_auto_tried = 0 # Reset to allow retry
                        st.rerun()
