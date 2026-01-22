
import base64
import os
from jojo_trading.core.stock_database import StockDatabase


class BrokerProfileManager:
    """
    Manages Shioaji Broker Profiles.
    Handles simple obfuscation of API keys/Secrets.
    """
    
    @staticmethod
    def _obfuscate(text: str) -> str:
        """Simple obfuscation (Base64). Not military grade encryption."""
        if not text: return ""
        return base64.b64encode(text.encode('utf-8')).decode('utf-8')

    @staticmethod
    def _deobfuscate(text: str) -> str:
        """De-obfuscate"""
        if not text: return ""
        try:
            return base64.b64decode(text.encode('utf-8')).decode('utf-8')
        except:
            return text

    @classmethod
    def save_profile(cls, name, api_key, secret_key, person_id, cert_path, cert_pass="", is_sim=False, save_cert_pass=False, allowed_ip="", vpn_user="", vpn_pass=""):
        """
        Save a profile. Encrypts sensitive data.
        If save_cert_pass is False, cert_pass is ignored/cleared.
        """
        enc_api = cls._obfuscate(api_key)
        enc_secret = cls._obfuscate(secret_key)
        enc_pass = cls._obfuscate(cert_pass) if save_cert_pass and cert_pass else ""
        enc_vpn_pass = cls._obfuscate(vpn_pass) if vpn_pass else ""
        
        db = StockDatabase()
        return db.create_broker_profile(name, enc_api, enc_secret, person_id, cert_path, enc_pass, is_sim, allowed_ip, vpn_user, enc_vpn_pass)

    @classmethod
    def get_profiles(cls):
        """Get list of profiles (decrypted for usage, or keep encrypted?)"""
        db = StockDatabase()
        profiles = db.get_broker_profiles()
        return profiles

    @classmethod
    def get_decrypted_profile(cls, name):
        """Get specific profile with decrypted credentials for connection"""
        db = StockDatabase()
        profiles = db.get_broker_profiles()
        target = next((p for p in profiles if p['profile_name'] == name), None)
        
        if target:
            target['api_key'] = cls._deobfuscate(target['api_key'])
            target['secret_key'] = cls._deobfuscate(target['secret_key'])
            target['cert_pass'] = cls._deobfuscate(target['cert_pass'])
            # Fix: Decrypt VPN password too!
            if 'vpn_pass' in target:
                target['vpn_pass'] = cls._deobfuscate(target['vpn_pass'])
            return target
        return None

    @classmethod
    def delete_profile(cls, name):
        db = StockDatabase()
        db.delete_broker_profile(name)

    @classmethod
    def import_from_env(cls, env_path):
        """Parse .env file and create a profile"""
        if not os.path.exists(env_path):
            return False, "File not found"
        
        try:
            env_vars = {}
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'): continue
                    if '=' in line:
                        k, v = line.split('=', 1)
                        # Remove quotes
                        v = v.strip().strip("'").strip('"')
                        env_vars[k.strip()] = v
            
            # Map keys
            name = "Imported_Env"
            api_key = env_vars.get('SHIOAJI_API_KEY', '')
            secret_key = env_vars.get('SHIOAJI_SECRET_KEY', '')
            person_id = env_vars.get('SHIOAJI_PERSON_ID', '')
            cert_path = env_vars.get('SHIOAJI_CERT_PATH', '')
            cert_pass = env_vars.get('SHIOAJI_CERT_PASS', '')
            is_sim = env_vars.get('SHIOAJI_SIMULATION', 'False').lower() == 'true'
            safe_ip = env_vars.get('SAFE_IP', '') # Map SAFE_IP to allowed_ip
            vpn_user = env_vars.get('VPN_USER', '')
            vpn_pass = env_vars.get('VPN_PASS', '')

            if not api_key:
                return False, "No SHIOAJI_API_KEY found in .env"

            res = cls.save_profile(name, api_key, secret_key, person_id, cert_path, cert_pass, 
                                 is_sim=is_sim, save_cert_pass=True, allowed_ip=safe_ip, 
                                 vpn_user=vpn_user, vpn_pass=vpn_pass)
            if res:
                return True, f"Profile '{name}' imported successfully!"
            else:
                return False, "Failed to save profile to DB."

        except Exception as e:
            return False, f"Import Error: {e}"

    @classmethod
    def export_to_json(cls, file_path):
        """Export all profiles to JSON (Encrypted)"""
        import json
        profiles = cls.get_profiles()
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(profiles, f, ensure_ascii=False, indent=2)
            return True, f"Exported {len(profiles)} profiles."
        except Exception as e:
            return False, str(e)

    @classmethod
    def import_from_json(cls, file_path):
        """Import profiles from JSON"""
        import json
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                return False, "Invalid JSON format (Expected list)"
            
            db = StockDatabase()
            count = 0
            for p in data:
                # Direct SQL insert might be risky if schema changed, but using DB method is safer if args match.
                # Since 'p' has encrypted data, we should pass it directly if we had a method, 
                # OR we decrypt and re-encrypt (redundant).
                # Better: direct DB insert or specialized method.
                # Let's use create_broker_profile but assuming inputs are ALREADY encrypted?
                # No, create_broker_profile expects Plain Text usually if we call save_profile?
                # Wait, save_profile calls _obfuscate.
                # If JSON contains ALREADY encrypted data (from get_profiles), we should NOT encrypt again.
                # We need a method to insert RAW record.
                
                # Check if keys exist
                name = p.get('profile_name')
                if not name: continue
                
                # We reuse calls but need to handle encryption status.
                # Let's assume JSON export/import is for backup, so it keeps encryption.
                # We need a direct insert method in StockDatabase or use raw SQL here?
                # Using Database method is cleaner.
                
                # However, StockDatabase.create_broker_profile takes arguments and inserts them.
                # It doesn't encrypt inside StockDatabase. 
                # BrokerManager.save_profile does encryption.
                # So if we pass data from JSON (already encrypted) to db.create_broker_profile, it works!
                # We just need to ensure we map fields correctly.
                
                db.create_broker_profile(
                    profile_name=name,
                    api_key=p.get('api_key', ''),
                    secret_key=p.get('secret_key', ''),
                    person_id=p.get('person_id', ''),
                    cert_path=p.get('cert_path', ''),
                    cert_pass=p.get('cert_pass', ''),
                    is_simulation=p.get('is_simulation', False),
                    allowed_ip=p.get('allowed_ip', ''),
                    vpn_user=p.get('vpn_user', ''),
                    vpn_pass=p.get('vpn_pass', '')
                )
                count += 1
            
            return True, f"Imported {count} profiles."
            
        except Exception as e:
            return False, str(e)
