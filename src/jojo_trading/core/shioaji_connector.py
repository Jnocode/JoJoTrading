import os
import shioaji as sj
from shioaji import Exchange
import pandas as pd
from typing import Dict, Optional, Any, List
from dotenv import load_dotenv
from datetime import datetime

# Load env variables
load_dotenv()

class ShioajiConnector:
    """
    Shioaji API Connector for Real-time Data
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ShioajiConnector, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        # Initialize as disconnected first
        self.api = None
        self.is_connected = False
        self._initialized = True
        
        # Determine if simulation from env (fallback)
        self.is_simulation = os.getenv('SHIOAJI_SIMULATION', 'False').lower() == 'true'

    def connect(self, api_key=None, secret_key=None, person_id=None, cert_path=None, cert_pass=None, allowed_ip=None, vpn_user=None, vpn_pass=None, is_simulation=False):
        """
        Connect to Shioaji API using provided credentials or fallback to env vars
        allowed_ip: Optional white-listed IP to enforce verification
        """
        if self.is_connected:
            print("⚠️ Already Connected")
            return {"status": "success", "msg": "Already Connected"}

        # 0. Network Safe Check (if allowed_ip is set)
        if allowed_ip:
            try:
                from jojo_trading.core.network_manager import NetworkManager
                nm = NetworkManager(safe_ip=allowed_ip, vpn_user=vpn_user, vpn_pass=vpn_pass)
                print(f"🔄 Verifying Network IP: {allowed_ip}...")
                is_safe, msg = nm.check_safety()
                
                if not is_safe:
                    print(f"⚠️ {msg} - Attempting Auto-Connect...")
                    success, log = nm.auto_connect()
                    
                    # CRITICAL: Re-verify IP after auto-connect with Retry
                    import time
                    is_safe_now = False
                    msg_now = ""
                    
                    print("🔄 Waiting for network switch...", end="", flush=True)
                    for i in range(10): # Up to 30 seconds
                        time.sleep(3)
                        print(f".{i+1}", end="", flush=True)
                        is_safe_now, msg_now = nm.check_safety()
                        if is_safe_now:
                            print(" OK!")
                            break
                    print("") # Newline
                            
                    if not success or not is_safe_now:
                        print(f"❌ Network Security Blocking Connection: {msg_now}")
                        return {"status": "error", "msg": f"IP Mismatch: {msg_now}"}
                        
                    print(f"✅ Network Auto-Connected & Verified: {log}")
                else:
                    print(f"✅ Network IP Verified: {msg}")
            except Exception as e:
                print(f"⚠️ Network check warning: {e}")
                return {"status": "error", "msg": f"Network Check Error: {e}"}

        # 1. Credentials Setup - Strict Mode (No Env Fallback if args provided)
        ak = api_key if api_key is not None else os.getenv('SHIOAJI_API_KEY')
        sk = secret_key if secret_key is not None else os.getenv('SHIOAJI_SECRET_KEY')
        cp = cert_path if cert_path is not None else os.getenv('SHIOAJI_CERT_PATH')
        cwp = cert_pass if cert_pass is not None else os.getenv('SHIOAJI_CERT_PASS')
        pid = person_id if person_id is not None else os.getenv('SHIOAJI_PERSON_ID')
        
        if not ak or not sk:
            return {"status": "error", "msg": "Missing API Key or Secret"}

        # 2. Login
        try:
            with open("debug.log", "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] Attempting Shioaji Login (Sim={is_simulation})...\n")

            self.api = sj.Shioaji(simulation=is_simulation)
            
            with open("debug.log", "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] Shioaji Instance Created. Calling login()...\n")

            # Increase contract timeout to 30s to prevent 'api/v1/data/contracts' error on slow connections
            self.api.login(ak, sk, contracts_timeout=30000, fetch_contract=False)
            
            with open("debug.log", "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] Login API returned. Connected.\n")

            self.is_connected = True
            self.is_simulation = is_simulation
            print(f"✅ Shioaji API Connected Successfully ({'SIM' if is_simulation else 'REAL'})")

            
            # Setup Callbacks
            try:
                # Try standard first
                if hasattr(self.api.quote, 'set_on_tick_fnk'):
                    self.api.quote.set_on_tick_fnk(self._on_tick)
                    print("DEBUG: Set callback via set_on_tick_fnk")
                elif hasattr(self.api.quote, 'set_on_tick_stk_v1_callback'):
                    self.api.quote.set_on_tick_stk_v1_callback(self._on_tick)
                    print("DEBUG: Set callback via set_on_tick_stk_v1_callback")
                else:
                    print(f"⚠️ Warning: set_on_tick_fnk not found. Available: {[x for x in dir(self.api.quote) if not x.startswith('_')]}")

                if hasattr(self.api.quote, 'set_on_bidask_fnk'):
                    self.api.quote.set_on_bidask_fnk(self._on_bidask)
                elif hasattr(self.api.quote, 'set_on_bidask_stk_v1_callback'):
                    self.api.quote.set_on_bidask_stk_v1_callback(self._on_bidask)
                
            except Exception as e:
                print(f"⚠️ Callback Setup Failed: {e}")
                
            # self.api.quote.set_on_quote_fnk(self._on_quote) # If needed for stock snapshot updates
            
            # Manually fetch contracts with error handling
            try:
                print("🔄 Fetching Contracts...")


                self.api.fetch_contracts(contract_download=True)
                print("✅ Contracts Downloaded")
            except Exception as ce:
                print(f"⚠️ Contract Download Failed (Some features may be limited): {ce}")
            
            if cert_path and cert_pass and person_id:
                self._activate_ca(cert_path, cert_pass, person_id)
            elif cert_path:
                print("ℹ️ CA info present but incomplete provided to connect()")
            
            # Cache accounts
            self.stock_account = None
            self.futures_account = None
            
            # Shioaji might have api.stock_account, but iterating is safer for all types
            # Try properties first
            try:
                self.stock_account = getattr(self.api, 'stock_account', None)
            except: pass
            
            try:
                self.futures_account = getattr(self.api, 'futures_account', None)
            except: pass
            
            # Iterate to find missing accounts (especially Futures)
            # Iterate to find best accounts
            # Priority for Stock: Type 'S' > Type 'H'
            # Priority for specific: Signed > Unsigned
            candidate_stock_accounts = []
            
            for acc in self.api.list_accounts():
                acc_type_str = str(acc.account_type)
                type_val = getattr(acc.account_type, 'value', '')
                
                # Future Selection
                if 'Future' in acc_type_str or type_val == 'F':
                    if not self.futures_account:
                        self.futures_account = acc
                    elif getattr(acc, 'signed', False) and not getattr(self.futures_account, 'signed', False):
                         # Prefer signed
                         self.futures_account = acc
                
                # Stock Selection Candidates
                if 'Stock' in acc_type_str or type_val in ['H', 'S']:
                    candidate_stock_accounts.append(acc)

            # Select Best Stock Account
            best_stock = None
            for acc in candidate_stock_accounts:
                type_val = getattr(acc.account_type, 'value', '')
                is_signed = getattr(acc, 'signed', False)
                
                if best_stock is None:
                    best_stock = acc
                    continue
                
                # Compare with current best
                best_type_val = getattr(best_stock.account_type, 'value', '')
                best_signed = getattr(best_stock, 'signed', False)
                
                # Rule 1: S > H
                if type_val == 'S' and best_type_val != 'S':
                    best_stock = acc
                    continue
                
                # Rule 2: If same type, Signed > Unsigned
                if type_val == best_type_val and is_signed and not best_signed:
                    best_stock = acc
                    continue
            
            self.stock_account = best_stock
            if self.stock_account:
                 t_val = getattr(self.stock_account.account_type, 'value', 'Unknown')
                 print(f"✅ Selected Stock Account: {self.stock_account.account_id} (Type: {t_val})")
            
            print(f"📦 Accounts Loaded - Stock: {self.stock_account is not None}, Future: {self.futures_account is not None}")
            
        except Exception as e:
            print(f"❌ Shioaji Connect Failed: {e}")
            self.is_connected = False
            # Re-raise to let UI know
            raise e

    # --- Real-time Logic ---
    def set_bridge(self, bridge):
        """Set external bridge (Qt Signal Bridge)"""
        self.bridge = bridge

    def _on_tick(self, exchange, tick):
        """Tick Callback"""
        # print(f"DEBUG: Tick Received {getattr(tick, 'code', 'Unknown')}")
        if hasattr(self, 'bridge') and self.bridge:
            self.bridge.handle_tick(tick)
        else:
             pass # print("DEBUG: Tick skipped - No Bridge")

    def _on_bidask(self, exchange, bidask):
        """BidAsk Callback (Best 5)"""
        # print(f"DEBUG: BidAsk Received {getattr(bidask, 'code', 'Unknown')}")
        if hasattr(self, 'bridge') and self.bridge:
            self.bridge.handle_bidask(bidask)
        else:
             pass # print("DEBUG: BidAsk skipped - No Bridge")

    def subscribe_contract(self, code: str, quote_type: str = 'bidask'):
        """
        Subscribe to Quote
        quote_type: 'tick', 'bidask'
        """
        if not self.is_connected: return
        
        try:
            # Try Stock first
            contract = self.api.Contracts.Stocks.get(code)
            if not contract:
                contract = self.api.Contracts.Futures.get(code)
                
            if contract:
                self.api.quote.subscribe(contract, quote_type=quote_type)
                # print(f"Subscribed {quote_type} for {code}")
            else:
                print(f"Contract {code} not found for subscription")
        except Exception as e:
            print(f"Subscribe failed: {e}")

    def unsubscribe_contract(self, code: str):
        """Unsubscribe"""
        if not self.is_connected: return
        try:
            contract = self.api.Contracts.Stocks.get(code)
            if not contract: contract = self.api.Contracts.Futures.get(code)
            if contract:
                self.api.quote.unsubscribe(contract, quote_type='tick')
                self.api.quote.unsubscribe(contract, quote_type='bidask')
        except: pass

    def _login(self):
        """Deprecated: Use connect()"""
        pass
            
    def _activate_ca(self, cert_path, cert_pass, person_id):
        """Activate Certificate for Trading/Account Data"""
        try:
            self.api.activate_ca(
                ca_path=cert_path,
                ca_passwd=cert_pass,
                person_id=person_id
            )
            print("✅ CA Certificate Activated Successfully")
        except Exception as e:
            print(f"⚠️ CA Activation Failed: {e}")
            raise e

    def get_latest_price(self, stock_code: str) -> Optional[float]:
        """
        Get real-time snapshot price for a stock.
        Returns None if failed or not connected.
        """
        if not self.is_connected:
            return None
            
        try:
            # Get contract
            contract = self.api.Contracts.Stocks[stock_code]
            if not contract:
                print(f"⚠️ Contract not found for {stock_code}")
                return None
                
            # Get snapshot
            snapshot = self.api.snapshots([contract])
            
            if snapshot and len(snapshot) > 0:
                # Snapshot object structure: snapshot[0].close 
                # Note: snapshot structure depends on API version somewhat, 
                # but generally .close is the last price.
                price = snapshot[0].close
                if price == 0: # Sometimes pre-market might be 0? Fallback to reference?
                    price = snapshot[0].reference
                    
                return float(price)
                
            return None
            
        except Exception as e:
            print(f"❌ Failed to fetch Shioaji price for {stock_code}: {e}")
            return None

    def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get current stock positions (Inventory).
        Returns list of dict: [{'code': '2330', 'qty': 1000, 'cost': 500}, ...]
        """
        if not self.is_connected:
            return []
            
        try:
            # 1. Get Accounts (Prefer Stock Account)
            accounts = self.api.list_accounts()
            stock_account = None
            for acc in accounts:
                if acc.account_type.value == 'H': # 'H' usually implies Stock/Securities? Or just pick first non-future?
                    # Shioaji AccountType: S (Stock), F (Future), H (Stock?)
                    # Let's try to find a stock account.
                    # Actually, we can just iterate accounts and aggregate positions.
                    pass
            
            # Simple approach: Use default/first stock account
            # Usually api.stock_account is a property shortcut if single account?
            # Safe way:
            stock_account = self.api.stock_account
            
            if not stock_account:
                print("⚠️ No stock account found in Shioaji.")
                return []
                
            # 2. Get Positions
            positions = self.api.list_positions(stock_account)
            
            result = []
            for pos in positions:
                qty = int(pos.quantity)
                cost = float(pos.price)
                code = pos.code
                
                # Check for available P&L and Last Price from Shioaji object
                pnl = getattr(pos, 'pnl', 0.0)
                last_price = getattr(pos, 'last_price', 0.0)
                
                # Heuristic to detect Lots vs Shares unit mismatch
                # If P&L implies shares (x1000) but qty is small, adjust qty
                # Theoretical PnL per unit = (last_price - cost)
                # If actual pnl / (per unit pnl * qty) ~ 1000, then qty is in lots
                
                final_qty = qty
                if qty < 1000 and abs(pnl) > 0 and last_price > 0:
                    diff = last_price - cost
                    if abs(diff) > 0:
                        theoretical_pnl = diff * qty
                        ratio = abs(pnl / theoretical_pnl)
                        if 900 < ratio < 1100: # Approx 1000
                            final_qty = qty * 1000
                
                # Filter out empty positions
                if final_qty > 0:
                    result.append({
                        'code': code,
                        'qty': final_qty,
                        'cost': cost,
                        'pnl': pnl,         # Direct P&L from broker
                        'last_price': last_price # Direct price from broker
                    })
            
            return result
            
        except Exception as e:
            print(f"❌ Failed to fetch positions: {e}")
            return []

    def get_kbars(self, stock_code: str, start_date: str, end_date: str = None) -> pd.DataFrame:
        """
        Fetch historical K-bars (Minute level) from Shioaji.
        :param stock_code: '2330'
        :param start_date: '2023-01-01'
        :param end_date: '2023-01-02'
        :return: DataFrame with ['date', 'open', 'high', 'low', 'close', 'volume']
        """
        if not self.is_connected:
            return pd.DataFrame()
            
        try:
            # 1. Get Contract
            contract = self.api.Contracts.Stocks.get(stock_code)
            if not contract:
                 # Try Futures lookup if not stock
                 contract = self.api.Contracts.Futures.get(stock_code)
                 
            if not contract:
                print(f"⚠️ Contract {stock_code} not found for Kbars")
                return pd.DataFrame()

            # 2. Fetch Data
            # Shioaji expects 'YYYY-MM-DD' strings
            kbars = self.api.kbars(contract, start=start_date, end=end_date)
            
            # 3. Convert to DataFrame
            df = pd.DataFrame({
                'date': pd.to_datetime(kbars.ts),
                'open': kbars.Open,
                'high': kbars.High,
                'low': kbars.Low,
                'close': kbars.Close,
                'volume': kbars.Volume
            })
            
            # Shioaji volume is usually shares, but sometimes lots depending on API version/contract
            # For Stocks, usually shares.
            
            return df
            
        except Exception as e:
            print(f"❌ Failed to fetch Shioaji Kbars: {e}")
            return pd.DataFrame()





    def get_available_futures_contracts(self, code: str = 'TXF') -> List[Dict[str, str]]:
        """List all available contracts for a category"""
        if not self.is_connected:
            return []
            
        category = getattr(self.api.Contracts.Futures, code, None)
        if not category:
            return []
            
        results = []
        for c in category:
            results.append({
                'code': c.code,
                'name': c.name,
                'date': c.delivery_date
            })
        return results

    def get_futures_snapshot(self, code: str = 'TXF', specific_code: str = None) -> Optional[Dict[str, Any]]:
        """
        Fetch Futures Snapshot.
        :param code: Category (TXF, MXF)
        :param specific_code: Specific contract code (e.g. TXFR2). If None, defaults to R1 (Near Month).
        """
        if not self.is_connected:
            return None
            
        try:
            category = getattr(self.api.Contracts.Futures, code, None)
            if not category:
                # print(f"⚠️ Futures category not found: {code}")
                return None
                
            target_contract = None
            
            # 1. Determine Target Code
            if specific_code:
                desired_code = specific_code
            else:
                desired_code = f"{code}R1" # Default to Near Month
            
            # 2. Find Contract
            for c in category:
                if c.code == desired_code:
                    target_contract = c
                    break
            
            # 3. Fallback (only if specific_code was NOT provided, revert to R1 fallbacks or first)
            if not target_contract and not specific_code:
                 # Try R1 failed? Fallback to first available
                contracts_list = list(category)
                if contracts_list:
                    target_contract = contracts_list[0]
            
            if not target_contract:
                return None
                
            # 4. Fetch Snapshot
            snap = self.api.snapshots([target_contract])
            
            if not snap:
                return None
                
            data = snap[0]
            
            # Safe attribute access
            price = getattr(data, 'close', 0)
            if price == 0: price = getattr(data, 'price', 0) # Fallback
            
            change_price = getattr(data, 'change_price', 0)
            change_rate = getattr(data, 'change_rate', 0)
            volume = getattr(data, 'total_volume', 0) # total_volume is better for index futures
            
            return {
                'code': target_contract.code,
                'name': target_contract.name,
                'price': float(price),
                'change': float(change_price),
                'pct_change': float(change_rate),
                'volume': int(volume),
                'ts': getattr(data, 'ts', 0)
            }
            
        except Exception as e:
            print(f"❌ Failed to fetch Futures {code}: {e}")
            return None

    def place_order(self, 
                    stock_code: str, 
                    action: str, 
                    quantity: int, 
                    price: float = None, 
                    price_type: str = 'LMT',
                    order_type: str = 'ROD',
                    dry_run: bool = False) -> Dict[str, Any]:
        """
        Place a Stock Order (Spot).
        """
        if not self.is_connected:
            return {'status': 'error', 'msg': 'API Not Connected'}

        try:
            # 1. Get Contract
            contract = self.api.Contracts.Stocks[stock_code]
            if not contract:
                return {'status': 'error', 'msg': f'Contract {stock_code} not found'}

            # 2. Resolve Action
            act = sj.constant.Action.Buy if action.upper() == 'BUY' else sj.constant.Action.Sell
            
            # 3. Resolve Price Type
            pt = sj.constant.StockPriceType.LMT
            if price_type == 'MKT': pt = sj.constant.StockPriceType.MKT
            elif price_type == 'MKP': pt = sj.constant.StockPriceType.MKP
            
            # 4. Resolve Order Type
            ot = sj.constant.OrderType.ROD
            if order_type == 'IOC': ot = sj.constant.OrderType.IOC
            elif order_type == 'FOK': ot = sj.constant.OrderType.FOK

            # 5. Create Order Object
            order = self.api.Order(
                price=price if price else 0,
                quantity=int(quantity),
                action=act,
                price_type=pt,
                order_type=ot,
                account=self.api.stock_account
            )
            
            if dry_run:
                return {'status': 'success', 'msg': f'[DRY] {action} {stock_code} {quantity} @ {price}'}

            # 6. Submit
            trade = self.api.place_order(contract, order)
            return {
                'status': 'success', 
                'msg': 'Order Submitted', 
                'order_id': trade.order.id, # Note: trade.order.id might fail if async?
                'raw': str(trade)
            }
            
        except Exception as e:
            print(f"❌ Order Failed: {e}")
            return {'status': 'error', 'msg': str(e)}

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """
        Cancel an existing order by ID (SeqNo).
        """
        if not self.is_connected:
            return {'status': 'error', 'msg': 'Not Connected'}
            
        try:
            self.api.update_status()
            trades = self.api.list_trades()
            
            target_trade = None
            for t in trades:
                if not getattr(t, 'order', None): continue
                seqno = getattr(t.order, 'seqno', getattr(t.order, 'id', ''))
                if str(seqno) == str(order_id):
                    target_trade = t
                    break
            
            if not target_trade:
                return {'status': 'error', 'msg': f'Order {order_id} not found.'}
                
            self.api.cancel_order(target_trade)
            return {'status': 'success', 'msg': f'Cancel submitted for {order_id}'}
            
        except Exception as e:
            return {'status': 'error', 'msg': f'Cancel failed: {e}'}

    def place_futures_order(self, 
                            contract_code: str, 
                            action: str, 
                            quantity: int, 
                            price: float = None, 
                            price_type: str = 'LMT',
                            order_type: str = 'ROD',
                            dry_run: bool = True) -> Dict[str, Any]:
        """
        Place a Futures Order.
        
        :param contract_code: Full contract code (e.g. 'TXFR1', 'MXFR1')
        :param action: 'Buy' or 'Sell'
        :param quantity: Number of contracts (Max 2 for safety)
        :param price: Limit price (Required for LMT)
        :param price_type: 'LMT', 'MKT', 'MKP' (Market w/ Range)
        :param order_type: 'ROD', 'IOC', 'FOK'
        :param dry_run: If True, only simulate request.
        """
        MAX_ORDER_QTY = 2  # Hard safety limit per order
        
        if not self.is_connected:
            return {'status': 'error', 'msg': 'API Not Connected'}
        contract = None
        # Must search across all Futures categories? Or just lookup if we know category.
        # Simplistic lookup: Check TXF then MXF.
        for cat_name in ['TXF', 'MXF', 'ZEF']:
             cat = getattr(self.api.Contracts.Futures, cat_name, [])
             for c in cat:
                 if c.code == contract_code:
                     contract = c
                     break
             if contract: break
        
        if not contract:
            return {'status': 'error', 'msg': f'Contract {contract_code} not found'}

        # 3. Resolve Action & PriceType
        try:
            act = sj.constant.Action.Buy if action.lower() == 'buy' else sj.constant.Action.Sell
            
            pt = sj.constant.FuturesPriceType.LMT
            if price_type == 'MKT': pt = sj.constant.FuturesPriceType.MKT
            elif price_type == 'MKP': pt = sj.constant.FuturesPriceType.MKP
            
            ot = sj.constant.OrderType.ROD
            if order_type == 'IOC': ot = sj.constant.OrderType.IOC
            elif order_type == 'FOK': ot = sj.constant.OrderType.FOK
        except Exception as e:
            return {'status': 'error', 'msg': f'Invalid Order Parameters: {e}'}

        # 4. Dry Run Logic
        if dry_run:
            return {
                'status': 'success', 
                'msg': f'[DRY RUN] Would {action} {quantity} x {contract.name} ({contract_code}) @ {price if price else "MKT"}',
                'order_id': 'SIMULATED_12345'
            }

            # 5. Place Real Order
            try:
                # Use cached Futures Account
                if not getattr(self, 'futures_account', None):
                    return {'status': 'error', 'msg': 'Futures account not found/loaded.'}

                order = self.api.Order(
                    action=act,
                    price=price if price else 0,
                    quantity=quantity,
                    price_type=pt,
                    order_type=ot,
                    octtype=sj.constant.FuturesOCTType.Auto,
                    account=self.futures_account # Explicitly use Futures Account
                )
                
                trade = self.api.place_order(contract, order)
                return {
                    'status': 'success',
                    'msg': 'Order Submitted',
                    'order_id': getattr(trade.order, 'id', 'N/A'),
                    'trade_object': str(trade)
                }
            except Exception as e:
                return {'status': 'error', 'msg': f'API Error: {e}'}

    def get_orders(self) -> List[Dict[str, Any]]:
        """
        Fetch recent orders.
        """
        if not self.is_connected:
            return []
            
        try:
            # Update status from server
            self.api.update_status() 
            orders = self.api.list_trades()
            
            result = []
            for trade in orders:
                # trade is a Trade object
                # It contains .order, .contract, .status
                
                # Safe access to inner Order object
                ord_obj = getattr(trade, 'order', None)
                if not ord_obj: continue
                
                # Get SeqNo (ID)
                # Some versions use .seqno, some use .id on the Order object
                seqno = getattr(ord_obj, 'seqno', getattr(ord_obj, 'id', 'N/A'))
                
                # Get Code
                code = getattr(trade.contract, 'code', 'Unknown')
                
                # Get Action
                action_enum = getattr(ord_obj, 'action', '')
                action = str(action_enum).split('.')[-1]
                
                # Get Status
                st_obj = getattr(trade, 'status', None)
                status_str = getattr(st_obj, 'status', 'Unknown')
                
                result.append({
                    'id': seqno,
                    'code': code,
                    'action': action,
                    'price': float(getattr(ord_obj, 'price', 0)),
                    'qty': int(getattr(ord_obj, 'quantity', 0)),
                    'status': str(status_str),
                    'type': str(getattr(ord_obj, 'price_type', '')).split('.')[-1]
                })
            
            return result
        except Exception as e:
            print(f"❌ Failed to fetch orders: {e}")
            return []

    def get_account_margin(self) -> Dict[str, float]:
        """
        Get Futures Account Margin Data.
        Returns dict with: equity, available_margin, initial_margin_req, maintenance_margin_req
        """
        if not self.is_connected:
            return {}

        try:
            # 1. Find Futures Account
            futures_account = None
            if getattr(self, 'futures_account', None):
                futures_account = self.futures_account
            else:
                for acc in self.api.list_accounts():
                    if 'Future' in str(acc.account_type):
                        futures_account = acc
                        break
            
            if not futures_account:
                if self.is_simulation:
                     # Mock for UI testing if no account found in Sim
                     return { 'equity': 1000000, 'available_margin': 800000, 'initial_margin': 100000, 'maintenance_margin': 80000, 'risk_ratio': 999.0 }
                return {}

            # 2. Call api.margin
            margin = self.api.margin(futures_account)
            
            return {
                'equity': float(getattr(margin, 'equity', 0)),
                'available_margin': float(getattr(margin, 'available_margin', 0) or getattr(margin, 'available', 0)),
                'initial_margin': float(getattr(margin, 'initial_margin', 0)),
                'maintenance_margin': float(getattr(margin, 'maintenance_margin', 0)),
                'risk_ratio': float(getattr(margin, 'margin_ratio', 0) or 0) # e.g. 50%
            }
        except Exception as e:
            print(f"Failed to fetch margin: {e}")
            return {}

    def get_settlements(self) -> List[Dict[str, Any]]:
        """
        Fetch Settlement (Cash) Information.
        Returns list of upcoming settlements (T+1, T+2).
        """
        if not self.is_connected:
            return []

        try:
            # 1. Get Accounts (Settlement usually requires Stock Account)
            # Use cached stock account if available
            acc = getattr(self, 'stock_account', None)
            if not acc:
                for a in self.api.list_accounts():
                    if 'Stock' in str(a.account_type) or a.account_type.value == 'H':
                        acc = a
                        break
            
            if not acc: return []

            # 2. Call api.settlements
            # Note: Method name might vary by version, usually api.settlements(account)
            settlements = self.api.settlements(acc)
            
            # 3. Parse
            # 3. Parse
            results = []
            if settlements:
                for s in settlements:
                    results.append({
                        'date': str(getattr(s, 'date', 'Unknown')), # T+1, T+2 date (Convert to str for JSON)
                        'amount': float(getattr(s, 'amount', 0)), # Positive: Receive, Negative: Pay
                        'currency': getattr(s, 'currency', 'TWD')
                    })
            
            return results
            
        except Exception as e:
            print(f"Failed to fetch settlements: {e}")
            return []
