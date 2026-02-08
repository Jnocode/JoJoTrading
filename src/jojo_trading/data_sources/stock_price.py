
import yfinance as yf
import pandas as pd
import time
import logging
from typing import List, Dict, Optional

# Configure logging
logger = logging.getLogger(__name__)

class StockPriceFetcher:
    """
    Fetches real-time stock prices using yfinance with caching.
    """
    _cache = {}
    _cache_expiry = {}
    _name_cache = {} # Persistent cache for names (rarely changes)
    CACHE_DURATION = 60  # Cache for 60 seconds to avoid prolonged API blocking

    def __init__(self):
        pass

    def get_prices(self, tickers: List[str]) -> Dict[str, Dict]:
        """
        Fetch prices for a list of tickers.
        Returns: {Ticker: {'price': 100.0, 'change_pct': 2.5}}
        """
        results = {}
        to_fetch = []
        current_time = time.time()

        # Check Cache
        for t in tickers:
            t = t.upper().strip()
            if t in self._cache and current_time < self._cache_expiry.get(t, 0):
                results[t] = self._cache[t]
            else:
                to_fetch.append(t)

        if not to_fetch:
            return results

        # Fetch batch
        try:
            # yfinance batch download is efficient
            # Tickers string: "TSLA AAPL 2330.TW"
            tickers_str = " ".join(to_fetch)
            if not tickers_str:
                return results

            logger.info(f"Fetching prices for: {tickers_str}")
            # period='1d' is enough to get current price and prev close
            data = yf.download(tickers_str, period="1d", interval="1m", progress=False)

            # Handle single ticker vs multiple tickers structure
            # If multiple, columns are MultiIndex (Price, Ticker)
            # If single, columns are Index (Price)
            
            for t in to_fetch:
                try:
                    price = None
                    prev_close = None
                    
                    # Extract Data
                    if len(to_fetch) == 1:
                        # Single Ticker DataFrame
                        if not data.empty:
                            price = data['Close'].iloc[-1]
                            # Prev close is tricky in 1d 1m data, let's use 'Open' of today or calculate from change?
                            # Better: use Ticker object for detail if needed, but download is faster for batch.
                            # Actually, efficient way for simple Current Price + Change %:
                            # Use Ticker().fast_info or just accept delay.
                            # Let's try to extract from 'Close' (latest) and 'Open' (start of day) as proxy for simple intraday change.
                            # OR better: fetch "5d" to get yesterday's close accurately.
                            pass
                    else:
                        # Multi-level columns
                         if not data.empty:
                            # Logic for multi-index extraction... yfinance structure can be complex.
                            pass
                    
                    # Alternative: Use Ticker module loop for reliability over speed if batch structure is messy
                    # For < 20 tickers, looping Ticker().info or fast_info is acceptable.
                    ticker_obj = yf.Ticker(t)
                    # fast_info is much faster than .info
                    price = ticker_obj.fast_info.last_price
                    prev_close = ticker_obj.fast_info.previous_close
                    
                    if price and prev_close:
                        change_val = price - prev_close
                        change_pct = (change_val / prev_close) * 100
                        
                        # Fetch Name (Lazy Load)
                        valid_name = self._name_cache.get(t)
                        if not valid_name:
                            try:
                                # accessing .info triggers request
                                info = ticker_obj.info 
                                valid_name = info.get('shortName') or info.get('longName') or classes
                                self._name_cache[t] = valid_name
                            except:
                                self._name_cache[t] = t # Fallback to ticker
                                valid_name = t
                        
                        data_dict = {
                            'price': round(price, 2),
                            'change_pct': round(change_pct, 2),
                            'currency': ticker_obj.fast_info.currency,
                            'name': valid_name
                        }
                        
                        # Update Cache
                        self._cache[t] = data_dict
                        self._cache_expiry[t] = current_time + self.CACHE_DURATION
                        results[t] = data_dict
                    else:
                        results[t] = {'price': float('nan'), 'change_pct': 0.0, 'name': t}

                except Exception as e:
                    logger.warning(f"Failed to fetch {t}: {e}")
                    results[t] = {'price': float('nan'), 'change_pct': 0.0}

        except Exception as e:
            logger.error(f"Batch fetch failed: {e}")

        return results
