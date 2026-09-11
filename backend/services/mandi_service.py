import httpx
import asyncio
import logging
from typing import Dict, List, Optional
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# OGD India MaSndi API Config
# Resource: Real-time Market Prices for Various Commodities (Mandi)
MANDI_API_URL = "https://api.data.gov.in/resource/35985678-0d79-46b4-9ed6-6f13308a1d24"
# Using the market api key from .env
MANDI_API_KEY = os.environ.get("MARKET_API_KEY", "579b464db66ec23bdd0000013582fdc531c242434618e379466b6e86")
# MANDI_API_URL = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
# Use MARKET_API_KEY from .env (falls back to old key for backwards compat)
MANDI_API_KEY = (
    os.environ.get("MARKET_API_KEY")
    or os.environ.get("MANDI_API_KEY")
)

# ── Curated fallback prices (₹/quintal, modal) — used when live API is unavailable ──
_FALLBACK_PRICES: Dict[str, Dict] = {
    "potato":      {"min": 700,  "max": 1400, "modal": 1050, "trend": "down",     "unit": "Quintal"},
    "onion":       {"min": 600,  "max": 1800, "modal": 1100, "trend": "up",       "unit": "Quintal"},
    "tomato":      {"min": 500,  "max": 2500, "modal": 1200, "trend": "volatile", "unit": "Quintal"},
    "wheat":       {"min": 2100, "max": 2500, "modal": 2275, "trend": "stable",   "unit": "Quintal"},
    "rice":        {"min": 1800, "max": 2800, "modal": 2200, "trend": "stable",   "unit": "Quintal"},
    "maize":       {"min": 1500, "max": 2000, "modal": 1800, "trend": "up",       "unit": "Quintal"},
    "soybean":     {"min": 3800, "max": 4800, "modal": 4300, "trend": "stable",   "unit": "Quintal"},
    "cotton":      {"min": 5500, "max": 6800, "modal": 6200, "trend": "up",       "unit": "Quintal"},
    "sugarcane":   {"min": 280,  "max": 340,  "modal": 315,  "trend": "stable",   "unit": "Tonne"},
    "mango":       {"min": 1500, "max": 5000, "modal": 2800, "trend": "up",       "unit": "Quintal"},
    "banana":      {"min": 800,  "max": 1500, "modal": 1100, "trend": "stable",   "unit": "Quintal"},
    "chilli":      {"min": 4000, "max": 8000, "modal": 6000, "trend": "up",       "unit": "Quintal"},
    "garlic":      {"min": 2000, "max": 8000, "modal": 4500, "trend": "volatile", "unit": "Quintal"},
    "carrot":      {"min": 600,  "max": 1400, "modal": 900,  "trend": "down",     "unit": "Quintal"},
    "spinach":     {"min": 500,  "max": 1200, "modal": 700,  "trend": "stable",   "unit": "Quintal"},
    "brinjal":     {"min": 400,  "max": 1200, "modal": 700,  "trend": "stable",   "unit": "Quintal"},
    "okra":        {"min": 600,  "max": 1800, "modal": 1100, "trend": "up",       "unit": "Quintal"},
    "cauliflower": {"min": 500,  "max": 1500, "modal": 900,  "trend": "stable",   "unit": "Quintal"},
    "groundnut":   {"min": 4500, "max": 6500, "modal": 5500, "trend": "stable",   "unit": "Quintal"},
    "turmeric":    {"min": 7000, "max": 12000,"modal": 9500, "trend": "up",       "unit": "Quintal"},
    "ginger":      {"min": 2000, "max": 6000, "modal": 3500, "trend": "volatile", "unit": "Quintal"},
    "jowar":       {"min": 2000, "max": 3000, "modal": 2500, "trend": "stable",   "unit": "Quintal"},
    "bajra":       {"min": 1800, "max": 2500, "modal": 2200, "trend": "stable",   "unit": "Quintal"},
    "gram":        {"min": 4000, "max": 5500, "modal": 4800, "trend": "stable",   "unit": "Quintal"},
    "urea fertilizer": {"min": 260, "max": 270, "modal": 267, "trend": "stable",  "unit": "Bag (50kg)"},
    "dap fertilizer":  {"min": 1350,"max": 1400,"modal": 1375,"trend": "stable",  "unit": "Bag (50kg)"},
    "seeds":       {"min": 200,  "max": 1500, "modal": 600,  "trend": "stable",   "unit": "kg"},
}


def _normalize(name: str) -> str:
    return name.strip().lower()


def get_fallback_price(commodity: str) -> Optional[Dict]:
    """Return curated fallback price record for a commodity name."""
    key = _normalize(commodity)
    if key in _FALLBACK_PRICES:
        rec = dict(_FALLBACK_PRICES[key])
        rec["commodity"] = commodity
        rec["source"] = "fallback"
        rec["state"] = "National Average"
        rec["market"] = "—"
        rec["arrival_date"] = "Current"
        return rec
    # Fuzzy: check if any key starts with the query word
    for k, v in _FALLBACK_PRICES.items():
        if k.startswith(key[:4]) or key.startswith(k[:4]):
            rec = dict(v)
            rec["commodity"] = commodity
            rec["source"] = "fallback"
            rec["state"] = "National Average"
            rec["market"] = "—"
            rec["arrival_date"] = "Current"
            return rec
    return None


class MandiService:
    _cache = {}
    _last_fetch = 0

    @staticmethod
    async def get_market_prices(commodity: Optional[str] = None, state: Optional[str] = None) -> List[Dict]:
        """
        Fetches real-time price data from Data.gov.in Mandi API with 6-hour caching.
        """
        cache_key = f"{commodity}_{state}"
        now = __import__('time').time()
        
        if cache_key in MandiService._cache:
            data, timestamp = MandiService._cache[cache_key]
            if now - timestamp < 21600: # 6 hours cache
                return data

        original_key = os.environ.get("MARKET_API_KEY") or os.environ.get("MANDI_API_KEY") or MANDI_API_KEY or "579b464db66ec23bdd0000013582fdc531c242434618e379466b6e86"
        params = {
            "api-key": original_key,
            "format": "json",
            "limit": 50
        }
        
        # Add filters if provided (Case-sensitive for new API)
        filters = {}
        if commodity:
            filters["Commodity"] = commodity
        if state:
            filters["State"] = state
            
        # OGD uses 'filters[field]=value' format
        for k, v in filters.items():
            params[f"filters[{k}]"] = v

        try:
            async with httpx.AsyncClient() as client:
                logger.info(f"Fetching Mandi prices for {commodity} in {state}...")
                response = await client.get(MANDI_API_URL, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    records = data.get("records", [])
                    
                    cleaned_records = []
                    for rec in records:
                        cleaned_records.append({
                            "state": rec.get("State"),
                            "district": rec.get("District"),
                            "market": rec.get("Market"),
                            "commodity": rec.get("Commodity"),
                            "variety": rec.get("Variety"),
                            "arrival_date": rec.get("Arrival_Date"),
                            "min_price": float(rec.get("Min_Price", 0)),
                            "max_price": float(rec.get("Max_Price", 0)),
                            "modal_price": float(rec.get("Modal_Price", 0)),
                            "unit": "Quintal",
                            "currency": "INR"
                        })
                    
                    MandiService._cache[cache_key] = (cleaned_records, now)
                    return cleaned_records
                else:
                    logger.error(f"Mandi API Error: {response.status_code} - {response.text}")
                    return []
        except Exception as e:
            logger.error(f"Failed to fetch Mandi prices: {e}")
            return []

    @staticmethod
    async def get_price_for_crop(crop_name: str, state: str = "Maharashtra") -> Optional[float]:
        """
        Helper to get the average modal price for a specific crop.
        """
        records = await MandiService.get_market_prices(commodity=crop_name, state=state)
        
        if not records:
            # Try without state filter if no results
            records = await MandiService.get_market_prices(commodity=crop_name)
            
        if records:
            # Return mean of modal prices
            prices = [r["modal_price"] for r in records if r["modal_price"] > 0]
            if prices:
                return sum(prices) / len(prices)
        
        return None

    @staticmethod
    async def get_prices_for_inventory(inventory: List[Dict], state: Optional[str] = "Maharashtra") -> List[Dict]:
        """
        Enhances inventory items with live or fallback market prices.
        """
        enriched = []
        for item in inventory:
            crop_name = item.get("crop_name", item.get("commodity", ""))
            if not crop_name:
                enriched.append(item)
                continue
            
            # Fetch live prices
            records = await MandiService.get_market_prices(commodity=crop_name, state=state)
            if not records:
                records = await MandiService.get_market_prices(commodity=crop_name)
            
            current_price = None
            price_source = "none"
            
            if records:
                prices = [r["modal_price"] for r in records if r["modal_price"] > 0]
                if prices:
                    current_price = sum(prices) / len(prices)
                    price_source = "live"
            
            if not current_price:
                fb = get_fallback_price(crop_name)
                if fb:
                    current_price = fb["modal"]
                    price_source = "fallback"
            
            item_copy = dict(item)
            if current_price:
                item_copy["current_market_price"] = round(current_price, 2)
                item_copy["price_source"] = price_source
                item_copy["currency"] = "INR"
                item_copy["unit"] = "Quintal"
            enriched.append(item_copy)
            
        return enriched

    @staticmethod
    async def get_board(state: Optional[str] = None) -> List[Dict]:
        """
        Returns a board of all available prices for major crops.
        """
        board = []
        major_crops = ["wheat", "rice", "maize", "soybean", "cotton", "potato", "onion", "tomato"]
        for crop in major_crops:
            records = await MandiService.get_market_prices(commodity=crop, state=state)
            if not records:
                records = await MandiService.get_market_prices(commodity=crop)
                
            if records:
                # get latest record or average
                prices = [r["modal_price"] for r in records if r["modal_price"] > 0]
                if prices:
                    avg_price = sum(prices) / len(prices)
                    board.append({
                        "commodity": crop.capitalize(),
                        "modal_price": round(avg_price, 2),
                        "unit": "Quintal",
                        "trend": "stable",
                        "source": "live"
                    })
            else:
                fb = get_fallback_price(crop)
                if fb:
                    board.append({
                        "commodity": fb["commodity"].capitalize(),
                        "modal_price": fb["modal"],
                        "unit": fb["unit"],
                        "trend": fb.get("trend", "stable"),
                        "source": "fallback"
                    })
        return board
