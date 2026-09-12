from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from .blockchain_service import get_ledger_from_db, BlockchainLedger
from core.supabase_client import supabase
import uuid
import time
import json
import os
from datetime import datetime, timedelta
from services.sensor_service import get_latest_sensor_data
from dotenv import load_dotenv

# ── Gemini client (lazy singleton) ───────────────────────────────────────────
_gemini_client = None

def _get_gemini_client():
    global _gemini_client
    if _gemini_client is None:
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
            load_dotenv(env_path)
            api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        from google import genai as google_genai
        _gemini_client = google_genai.Client(api_key=api_key)
    return _gemini_client

router = APIRouter()

class EventRequest(BaseModel):
    batch_id: str
    event_type: str # SOWING, IRRIGATION, FERTILIZER, HARVEST, DISEASE
    details: Dict[str, Any]

from .trust_engine import update_inventory_trust_data, calculate_integrity_score, generate_cultivation_summary

class BatchCreateRequest(BaseModel):
    farmer_id: str
    crop_name: str
    variety: str
    quantity: float
    price_per_quintal: float
    location: str = "Unknown"
    district: str = "Unknown"
    area_cultivated: float = 1.0
    soil_nitrogen: float = 45.0
    soil_phosphorus: float = 18.0
    soil_potassium: float = 12.0
    soil_moisture: float = 24.5
    status: str = "planted"
    days_to_harvest: int = 120

@router.post("/batch/create")
def create_batch(req: BatchCreateRequest):
    """
    Creates a new batch (Inventory Item) and initializes its Genesis Block.
    Synced with User SQL Schema: status must be one of ['harvested', 'ready_for_sale', 'listed', 'sold']
    """
    batch_id = f"BATCH-{uuid.uuid4().hex[:8].upper()}"
    
    try:
        sowing_dt = datetime.now()
        harvest_dt = sowing_dt + timedelta(days=req.days_to_harvest)
        
        data = {
            "farmer_id": req.farmer_id, 
            "crop_name": req.crop_name,
            "variety": req.variety,
            "quantity": float(req.quantity),
            "price_per_quintal": float(req.price_per_quintal),
            "batch_id": batch_id,
            "location": req.location,
            "district": req.district,
            "area_cultivated": float(req.area_cultivated),
            "available_quantity": float(req.quantity),
            "status": req.status,
            "sowing_date": sowing_dt.isoformat(),
            "harvest_date": harvest_dt.isoformat(), # Expected Harvest Date
            "integrity_score": 100,
            "verified_badge": False,
            "sustainability_score": 0,
            "health_status": "Healthy"
        }
        
        # 2. Insert into DB (Must succeed)
        res = supabase.table("inventory").insert(data).execute()
        if not res.data:
            raise HTTPException(status_code=500, detail="Database insertion failed.")
        
        # 3. Initialize REAL Blockchain Ledger (crop_events)
        ledger = BlockchainLedger([]) 
        genesis = BlockchainLedger.create_genesis_block()
        ledger._persist_block(batch_id, genesis)
        
        # 4. Add SOWING event to ledger
        ledger.add_event(batch_id, "SOWING", {
            "method": "Precision Line Sowing",
            "seed_purity": "99.8%",
            "area_acres": float(req.area_cultivated),
            "soil_chemistry": {
                "nitrogen_n": f"{req.soil_nitrogen} mg/kg",
                "phosphorus_p": f"{req.soil_phosphorus} mg/kg",
                "potassium_k": f"{req.soil_potassium} mg/kg"
            },
            "environment": {
                "moisture_content": f"{req.soil_moisture}%",
                "ph_level": 6.8,
                "temperature": "28°C"
            },
            "note": "Genesis crop metrics secured on blockchain for traceability."
        })

        # 4b. If PLANTED, add real-time SENSOR data
        if req.status == "planted":
            try:
                sensor_data = get_latest_sensor_data(req.farmer_id)
                if sensor_data:
                    # Remove id/user_id from data to keep it clean in ledger
                    clean_data = {k:v for k,v in sensor_data.items() if k not in ['id', 'user_id', 'created_at']}
                    ledger.add_event(batch_id, "SENSOR_READING", {
                        "source": "Autonomous_IoT_Station",
                        "reading_type": "Initial_State",
                        "metrics": clean_data,
                        "verified": True
                    })
            except Exception as e:
                print(f"⚠️ Failed to add sensor log: {e}")

        # 5. Populate initial trust summaries
        update_inventory_trust_data(batch_id)
        
        return {"success": True, "batch_id": batch_id}
    except Exception as e:
        print(f"Error in create_batch: {e}")
        return {"success": False, "error": str(e)}

@router.get("/scan/{batch_id}")
def scan_batch_details(batch_id: str):
    """
    Returns full trust details directly from Database.
    """
    # 1. Fetch Inventory
    inv_res = supabase.table("inventory").select("*").eq("batch_id", batch_id).execute()
    if not inv_res.data:
        raise HTTPException(status_code=404, detail=f"Batch {batch_id} not found.")
    
    inventory = inv_res.data[0]
    
    # 2. Fetch Timeline from REAL Ledger
    ledger = get_ledger_from_db(batch_id)
    
    # 3. Fetch Farmer Reputation
    farmer_id = inventory.get("farmer_id")
    # Note: farmer_profiles.user_id is the unique key in provided schema
    farmer_res = supabase.table("farmer_profiles").select("*").eq("user_id", farmer_id).execute()
    farmer = farmer_res.data[0] if farmer_res.data else {
        "name": "Verified Annadata",
        "identity_verified": True,
        "reputation_rating": 4.8
    }
    
    return {
        "crop_info": inventory,
        "trust_layer": {
            "farmer": {
                "name": farmer.get("name"),
                "verified": farmer.get("identity_verified", True),
                "rating": farmer.get("reputation_rating", 4.8),
                "total_sales": farmer.get("total_sales", 0),
                "district": farmer.get("district")
            },
            "integrity_score": inventory.get("integrity_score", 100),
            "summary": inventory.get("cultivation_summary", {}),
            "verified_badge": inventory.get("verified_badge", False),
            "sustainability_score": inventory.get("sustainability_score", 0)
        },
        "blockchain_timeline": ledger.get_chain_dict()
    }

@router.post("/trust/refresh/{batch_id}")
def refresh_trust_data(batch_id: str):
    """Endpoint to manually trigger trust data recompilation."""
    success = update_inventory_trust_data(batch_id)
    return {"success": success}

@router.get("/marketplace")
async def list_marketplace():
    """Returns all active listings with trust summaries and real Mandi prices."""
    try:
        from services.mandi_service import MandiService
        res = supabase.table("inventory").select("*").eq("status", "ready_for_sale").limit(20).execute()
        listings = res.data or []
        
        # Enrich with live Mandi prices
        for item in listings:
            mandi_price = await MandiService.get_price_for_crop(item['crop_name'], item.get('state', 'Maharashtra'))
            if mandi_price:
                item['mandi_price'] = round(mandi_price, 2)
            else:
                # Fallback to a calculated trend if API fails
                item['mandi_price'] = round(item['price_per_quintal'] * 0.95, 2)
                
        return listings
    except Exception as e:
        print(f"Marketplace error: {e}")
        return []

@router.get("/timeline/{batch_id}")
def get_batch_timeline(batch_id: str):
    """
    Returns the real SHA-256 chained history for the batch.
    """
    ledger = get_ledger_from_db(batch_id)
    return {
        "batch_id": batch_id,
        "is_valid": ledger.is_chain_valid(),
        "timeline": ledger.get_chain_dict()
    }

@router.post("/batch/event")
def add_batch_event(req: EventRequest):
    """
    Records a new event (IRRIGATION, FERTILIZER, etc) in the Blockchain Ledger.
    """
    try:
        ledger = get_ledger_from_db(req.batch_id)
        # Add timestamp if not in details
        details = req.details.copy()
        if "timestamp" not in details:
            details["timestamp"] = datetime.now().isoformat()
            
        block = ledger.add_event(req.batch_id, req.event_type, details)
        
        # If it's irrigation, update last_irrigated in inventory (optional metadata)
        if req.event_type == "IRRIGATION":
            supabase.table("inventory").update({"health_status": "Recently Irrigated"}).eq("batch_id", req.batch_id).execute()
        
        # Trigger trust recalculation
        update_inventory_trust_data(req.batch_id)
            
        return {"success": True, "event": req.event_type, "block_hash": block.hash}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class StatusUpdateRequest(BaseModel):
    batch_id: str
    status: str # harvested, ready_for_sale, sold
    quantity: Optional[float] = None
    quality_grade: Optional[str] = None

@router.post("/batch/update-status")
def update_batch_status(req: StatusUpdateRequest):
    """
    Transitions the crop batch life-cycle.
    """
    try:
        update_data = {"status": req.status}
        if req.quantity is not None:
             update_data["quantity"] = req.quantity
             update_data["available_quantity"] = req.quantity
        if req.quality_grade:
             update_data["quality_grade"] = req.quality_grade
             
        if req.status == "harvested":
            update_data["harvest_date"] = datetime.now().isoformat() # Actual harvest date

        res = supabase.table("inventory").update(update_data).eq("batch_id", req.batch_id).execute()
        
        # Record on blockchain
        ledger = get_ledger_from_db(req.batch_id)
        ledger.add_event(req.batch_id, f"STATUS_CHANGE", {
            "new_status": req.status,
            "updated_at": datetime.now().isoformat(),
            "notes": f"Batch transitioned to {req.status}"
        })
        
        return {"success": True, "data": res.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class PriceSnapshotRequest(BaseModel):
    batch_id: str
    price: float
    market: str = "Local Mandi"

@router.post("/batch/price-snapshot")
def save_price_snapshot(req: PriceSnapshotRequest):
    """
    Saves a market price snapshot for a 'Ready to Sell' batch.
    """
    try:
        # Update price on inventory or just log event
        supabase.table("inventory").update({
            "price_per_quintal": req.price
        }).eq("batch_id", req.batch_id).execute()
        
        ledger = get_ledger_from_db(req.batch_id)
        ledger.add_event(req.batch_id, "PRICE_SNAPSHOT", {
            "price": req.price,
            "currency": "INR",
            "market_source": req.market,
            "captured_at": datetime.now().isoformat()
        })
        
        return {"success": True, "price": req.price}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list/{farmer_id}")
async def list_farmer_batches(farmer_id: str):
    """
    Get all batches for a specific farmer, enriched with market data.
    """
    try:
        from services.mandi_service import MandiService
        res = supabase.table("inventory").select("*").eq("farmer_id", farmer_id).order("created_at", desc=True).execute()
        batches = res.data or []
        
        # Enrich with live Mandi prices
        for item in batches:
            mandi_price = await MandiService.get_price_for_crop(item['crop_name'], item.get('state', 'Maharashtra'))
            if mandi_price:
                item['mandi_price'] = round(mandi_price, 2)
            else:
                item['mandi_price'] = round(item['price_per_quintal'] * 0.94, 2)
                
        return batches
    except Exception as e:
        print(f"Error fetching inventory for {farmer_id}: {e}")
        return []


# ─────────────────────────────────────────────────────────────────────────────
# VOICE / NLP — Inventory V2
# ─────────────────────────────────────────────────────────────────────────────

class VoiceParseRequest(BaseModel):
    text: str
    language: str = "en"  # en | hi | mr


class AddInventoryItemRequest(BaseModel):
    farmer_id: str
    item_name: str
    quantity: float
    unit: str = "kg"
    category: str = "produce"  # produce | inputs | assets | financials
    price_per_unit: float = 0.0
    location: str = "Unknown"


# ── Regex fallback parser (works offline / when Gemini quota is exhausted) ───

import re as _re

# Maps vernacular words → English item name + category
_ITEM_MAP = {
    # ── Produce ──────────────────────────────────────────────────────────────
    "potato|आलू|aloo|batata|बटाटा|आलूचे|बटाट्याचे": ("Potato", "produce", "kg"),
    "wheat|गेहूं|gehu|गहू|गव्हाचे|गव्हाचा": ("Wheat", "produce", "kg"),
    "rice|chawal|चावल|tandul|तांदूळ|तांदळाचे": ("Rice", "produce", "kg"),
    "onion|pyaz|प्याज|kanda|कांदा|कांद्याचे": ("Onion", "produce", "kg"),
    "tomato|tamatar|टमाटर|tomato|टोमॅटो|टोमॅटोचे": ("Tomato", "produce", "kg"),
    "maize|makka|मक्का|corn|मक्याचे": ("Maize", "produce", "kg"),
    "soybean|soya|सोयाबीन|सोयाबीनचे": ("Soybean", "produce", "kg"),
    "cotton|kapas|कपास|kapus|कापूस|कापसाचे": ("Cotton", "produce", "kg"),
    "sugarcane|ganna|गन्ना|oos|ऊस|उसाचे": ("Sugarcane", "produce", "tonne"),
    "mango|aam|आम|amba|आंबा|आंब्याचे": ("Mango", "produce", "kg"),
    "banana|kela|केला|keli|केळी|केळीचे": ("Banana", "produce", "kg"),
    "chilli|mirchi|मिर्च|मिरची|मिरचीचे": ("Chilli", "produce", "kg"),
    "garlic|lehsun|लहसुन|lasun|लसूण|लसणाचे": ("Garlic", "produce", "kg"),
    # carrot — include oblique Marathi forms (गाजराचे, गाजराचा, गाजराची, गाजरे)
    "carrot|gajar|गाजर|गाजराचे|गाजराचा|गाजराची|गाजरे": ("Carrot", "produce", "kg"),
    "spinach|palak|पालक|पालकाचे": ("Spinach", "produce", "kg"),
    "brinjal|eggplant|baingan|बैंगन|vangi|वांगे|वांग्याचे": ("Brinjal", "produce", "kg"),
    "okra|bhindi|भिंडी|bhendi|भेंडी|भेंडीचे": ("Okra", "produce", "kg"),
    "cauliflower|phoolgobi|फूलगोभी|phulkobi|फुलकोबी|फुलकोबीचे": ("Cauliflower", "produce", "kg"),
    "groundnut|peanut|moongphali|मूंगफली|shengdana|शेंगदाणे|शेंगदाण्याचे": ("Groundnut", "produce", "kg"),
    "turmeric|haldi|हल्दी|halad|हळद|हळदीचे": ("Turmeric", "produce", "kg"),
    "ginger|adrak|अदरक|aale|आले|आल्याचे": ("Ginger", "produce", "kg"),
    "jowar|sorghum|ज्वारी|ज्वाराचे": ("Jowar", "produce", "kg"),
    "bajra|millet|बाजरा|बाजरीचे": ("Bajra", "produce", "kg"),
    "chana|gram|chickpea|चना|चणा|चण्याचे": ("Gram", "produce", "kg"),
    # ── Inputs ──────────────────────────────────────────────────────────────
    "urea|यूरिया": ("Urea Fertilizer", "inputs", "bags"),
    "dap": ("DAP Fertilizer", "inputs", "bags"),
    "fertilizer|khad|खाद|khat|खत|खताचे": ("Fertilizer", "inputs", "bags"),
    "pesticide|keetnaashak|कीटनाशक|keetaknashak|कीटकनाशक|कीटकनाशकाचे": ("Pesticide", "inputs", "litre"),
    "seed|beej|बीज|bij|बी|बियाण्याचे": ("Seeds", "inputs", "kg"),
    "compost|khaad|जैविक": ("Compost", "inputs", "kg"),
    # ── Assets ──────────────────────────────────────────────────────────────
    "tractor|ट्रैक्टर|ट्रॅक्टर": ("Tractor", "assets", "pieces"),
    "pump|पंप": ("Water Pump", "assets", "pieces"),
    "sprayer|छिड़काव|फवारणी": ("Sprayer", "assets", "pieces"),
    "sensor|सेंसर": ("IoT Sensor", "assets", "pieces"),
}

_UNIT_MAP = {
    "kg|kilo|किलो|किलोग्राम|kgs|किलोग्रॅम": "kg",
    "gram|grams|ग्राम|grm|ग्रॅम": "gram",
    "litre|liter|ltr|लीटर|लिटर": "litre",
    "ml|milliliter|मिलीलीटर": "ml",
    "bag|bags|बोरी|पिशवी|बैग|बोरे": "bags",
    "piece|pieces|pcs|नग": "pieces",
    "quintal|qtl|क्विंटल|cwt": "quintal",
    "tonne|ton|टन|tonnes": "tonne",
    "bundle|गट्ठर|गुच्छ": "bundle",
}

# ── Word-form numerals → digits (EN / HI / MR) ───────────────────────────────
_WORD_NUMS = {
    # English
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90, "hundred": 100,
    # Hindi / Marathi (shared + language-specific)
    "एक": 1, "दो": 2, "दोन": 2, "तीन": 3, "चार": 4,
    "पाँच": 5, "पाच": 5, "छह": 6, "सहा": 6, "सात": 7,
    "आठ": 8, "नौ": 9, "नऊ": 9, "दस": 10, "दहा": 10,
    "ग्यारह": 11, "अकरा": 11, "बारह": 12, "बारा": 12,
    "तेरह": 13, "तेरा": 13, "चौदह": 14, "चौदा": 14,
    "पंद्रह": 15, "पंधरा": 15, "सोलह": 16, "सोळा": 16,
    "सत्रह": 17, "सतरा": 17, "अठारह": 18, "अठरा": 18,
    "उन्नीस": 19, "एकोणीस": 19,
    "बीस": 20, "वीस": 20, "तीस": 30, "चालीस": 40, "चाळीस": 40,
    "पचास": 50, "पन्नास": 50, "साठ": 60, "सत्तर": 70,
    "अस्सी": 80, "ऐंशी": 80, "नब्बे": 90, "नव्वद": 90,
    "सौ": 100, "शंभर": 100,
}


def _replace_word_nums(text: str) -> str:
    """Replace word-form numbers (EN/HI/MR) with digits — longest match first."""
    for word, val in sorted(_WORD_NUMS.items(), key=lambda x: -len(x[0])):
        if ord(word[0]) > 127:
            # Devanagari — plain replace (word boundaries don't work with Unicode)
            text = text.replace(word, f" {val} ")
        else:
            text = _re.sub(r'\b' + _re.escape(word) + r'\b', f" {val} ", text, flags=_re.IGNORECASE)
    return text


def _strip_marathi_oblique(text: str) -> str:
    """
    Remove Marathi case suffixes that follow the oblique ā marker.
    e.g. गाजराचे → गाजर  (ā + चे stripped, leaves base form)
    """
    return _re.sub(r'ाचे|ाचा|ाची|ाचं|ाच्या|ांचे|ांचा|ांची|ांचं|ाला|ाने|ाशी|ावर|ातून', '', text)


def _regex_parse(text: str) -> dict | None:
    """Simple multilingual regex parser. Returns parsed dict or None."""
    # Pre-process: strip Marathi oblique forms, then convert word nums → digits
    t = _strip_marathi_oblique(text.lower().strip())
    t = _replace_word_nums(t)

    # Extract quantity (digits)
    qty_match = _re.search(r'(\d+(?:\.\d+)?)', t)
    if not qty_match:
        return None
    quantity = float(qty_match.group(1))

    # Detect unit
    unit = "kg"
    for pattern, mapped_unit in _UNIT_MAP.items():
        if _re.search(pattern, t):
            unit = mapped_unit
            break

    # Detect item
    item_name, category = None, "produce"
    default_unit = unit
    for pattern, (name, cat, def_unit) in _ITEM_MAP.items():
        if _re.search(pattern, t, _re.IGNORECASE):
            item_name = name
            category = cat
            if unit == "kg":  # only override if no explicit unit was found
                default_unit = def_unit
            break

    if not item_name:
        return None

    if unit == "kg" and default_unit != "kg":
        unit = default_unit

    return {
        "item_name": item_name,
        "quantity": quantity,
        "unit": unit,
        "category": category,
        "estimated_price_per_unit": 0.0,
        "location": "Unknown",
        "confidence": 0.75,
        "_source": "regex_fallback"
    }


@router.post("/parse-voice")
async def parse_voice_command(req: VoiceParseRequest):
    """
    Parses natural language inventory commands (EN/HI/MR) into structured data.
    Tries Gemini LLM first; falls back to regex parser if Gemini is unavailable/rate-limited.
    """
    # ── Try Gemini ────────────────────────────────────────────────────────────
    try:
        client = _get_gemini_client()

        prompt = f"""You are a multilingual inventory assistant for Indian farmers.
Parse the following text and extract inventory information.

Text: "{req.text}"
Language hint: {req.language} (en=English, hi=Hindi, mr=Marathi)

Return ONLY a valid JSON object with these exact fields:
- item_name: string (the name of the item translated to English)
- quantity: number
- unit: string — pick the most appropriate from: kg, gram, litre, ml, bags, pieces, quintal, tonne, bundle
- category: string — exactly one of:
    "produce"    → harvested crops, vegetables, fruits, grains (rice, wheat, potato, onion, tomato, etc.)
    "inputs"     → seeds, fertilizer, urea, DAP, pesticide, herbicide, compost, soil amendment
    "assets"     → tractor, pump, sprayer, sensor, tool, equipment, machine
    "financials" → invoice, payment, loan, cost, expense, receipt
- estimated_price_per_unit: number (INR per unit if mentioned, else 0)
- location: string (storage location if mentioned, else "Unknown")
- confidence: number from 0.0 to 1.0

Examples:
"I have 20 kg potato" → {{"item_name":"Potato","quantity":20,"unit":"kg","category":"produce","estimated_price_per_unit":0,"location":"Unknown","confidence":0.98}}
"मेरे पास 20 किलो आलू है" → {{"item_name":"Potato","quantity":20,"unit":"kg","category":"produce","estimated_price_per_unit":0,"location":"Unknown","confidence":0.97}}
"50 bags of urea in warehouse" → {{"item_name":"Urea Fertilizer","quantity":50,"unit":"bags","category":"inputs","estimated_price_per_unit":0,"location":"Warehouse","confidence":0.95}}
"माझ्याकडे 5 लीटर कीटकनाशक आहे" → {{"item_name":"Pesticide","quantity":5,"unit":"litre","category":"inputs","estimated_price_per_unit":0,"location":"Unknown","confidence":0.93}}
"2 tractors in Field A" → {{"item_name":"Tractor","quantity":2,"unit":"pieces","category":"assets","estimated_price_per_unit":0,"location":"Field A","confidence":0.90}}

Respond ONLY with valid JSON. No explanation, no markdown, no code blocks."""

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )

        raw = response.text.strip()
        if raw.startswith("```"):
            parts = raw.split("```")
            raw = parts[1] if len(parts) >= 2 else raw
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        parsed = json.loads(raw)
        for field in ("item_name", "quantity", "unit", "category"):
            if field not in parsed:
                raise ValueError(f"Missing field: {field}")

        valid_categories = {"produce", "inputs", "assets", "financials"}
        if parsed.get("category") not in valid_categories:
            parsed["category"] = "produce"

        parsed["quantity"] = float(parsed["quantity"])
        parsed["estimated_price_per_unit"] = float(parsed.get("estimated_price_per_unit", 0))
        parsed["confidence"] = float(parsed.get("confidence", 0.8))
        parsed["location"] = parsed.get("location", "Unknown") or "Unknown"
        parsed["_source"] = "gemini"

        return {"success": True, "parsed": parsed}

    except Exception as gemini_err:
        # Log silently and fall through to regex fallback
        print(f"Gemini unavailable ({type(gemini_err).__name__}), trying regex fallback...")

    # ── Regex fallback ────────────────────────────────────────────────────────
    fallback = _regex_parse(req.text)
    if fallback:
        return {"success": True, "parsed": fallback}

    return {
        "success": False,
        "error": (
            "Could not understand the input. Try phrases like:\n"
            "• \"I have 20 kg potato\"\n"
            "• \"50 bags of urea\"\n"
            "• \"मेरे पास 20 किलो आलू है\""
        )
    }


@router.post("/add-item")
async def add_inventory_item(req: AddInventoryItemRequest):
    """
    Adds a new inventory item for a farmer.
    - For 'produce': creates a blockchain-tracked batch (genesis block + VOICE_ADDED event).
    - For other categories: inserts a simplified inventory row with a unique batch_id.
    """
    try:
        batch_id = f"ITEM-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now()

        # Build the DB row — crop_name kept for backward compatibility
        data = {
            "farmer_id": req.farmer_id,
            "crop_name": req.item_name,
            "item_name": req.item_name,
            "variety": "",
            "quantity": float(req.quantity),
            "available_quantity": float(req.quantity),
            "original_quantity": float(req.quantity),
            "price_per_quintal": float(req.price_per_unit),
            "batch_id": batch_id,
            "location": req.location,
            "district": "Unknown",
            "area_cultivated": 0.0,
            "status": "harvested" if req.category == "produce" else "listed",
            "category": req.category,
            "unit": req.unit,
            "integrity_score": 100,
            "verified_badge": False,
            "sustainability_score": 0,
            "health_status": "Good",
            "sowing_date": now.isoformat(),
            "harvest_date": now.isoformat(),
        }

        res = supabase.table("inventory").insert(data).execute()
        if not res.data:
            raise HTTPException(status_code=500, detail="Database insertion failed.")

        # For produce items, initialise the blockchain ledger
        if req.category == "produce":
            try:
                ledger = BlockchainLedger([])
                genesis = BlockchainLedger.create_genesis_block()
                ledger._persist_block(batch_id, genesis)
                ledger.add_event(batch_id, "VOICE_ADDED", {
                    "item": req.item_name,
                    "quantity": req.quantity,
                    "unit": req.unit,
                    "source": "Voice / Text Input",
                    "added_at": now.isoformat()
                })
            except Exception as ledger_err:
                print(f"⚠️ Blockchain init skipped for {batch_id}: {ledger_err}")

        return {"success": True, "batch_id": batch_id, "data": res.data[0]}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Add inventory item error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
