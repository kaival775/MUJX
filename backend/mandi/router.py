from fastapi import APIRouter, Query
from typing import Optional, List, Dict
from services.mandi_service import MandiService, _FALLBACK_PRICES, get_fallback_price
from core.supabase_client import supabase

router = APIRouter(prefix="/mandi", tags=["Market Prices"])

@router.get("/prices")
async def get_mandi_prices(
    commodity: Optional[str] = Query(None, description="Crop name e.g. Wheat, Rice"),
    state: Optional[str] = Query(None, description="State name e.g. Maharashtra, Punjab")
):
    """Get live market prices from Government Mandis (Data.gov.in) with fallback."""
    prices = await MandiService.get_market_prices(commodity=commodity, state=state)
    if not prices and commodity:
        fb = get_fallback_price(commodity)
        if fb:
            prices = [{
                "state": state or "National Average",
                "district": "—",
                "market": "—",
                "commodity": commodity,
                "variety": "—",
                "arrival_date": "Current",
                "min_price": float(fb["min"]),
                "max_price": float(fb["max"]),
                "modal_price": float(fb["modal"]),
                "unit": fb.get("unit", "Quintal"),
                "currency": "INR",
                "source": "fallback",
                "trend": fb.get("trend", "stable"),
            }]
    return {"success": True, "count": len(prices), "data": prices}


@router.get("/suggested-price")
async def get_suggested_price(
    crop: str = Query(..., description="Crop name"),
    state: Optional[str] = Query("Maharashtra", description="State")
):
    """Returns a single recommended price based on current market averages."""
    avg_price = await MandiService.get_price_for_crop(crop, state)
    if avg_price:
        return {"success": True, "crop": crop, "suggested_price": round(avg_price, 2),
                "unit": "Quintal", "currency": "INR", "source": "Mandi API (Data.gov.in)"}
    return {"success": False, "message": f"No price data found for {crop}"}


@router.get("/board")
async def get_mandi_board(
    state: Optional[str] = Query(None, description="Filter by state")
):
    """Full market price board — live if available, curated fallback otherwise."""
    board = await MandiService.get_board(state=state)
    return {"success": True, "count": len(board), "source": board[0]["source"] if board else "none", "data": board}


@router.get("/prices-for-farmer/{farmer_id}")
async def get_prices_for_farmer(
    farmer_id: str,
    state: Optional[str] = Query("Maharashtra", description="State for price lookup")
):
    """
    Fetch farmer's inventory and annotate each produce item with live/fallback
    mandi prices. Also returns a full mandi board for context.
    """
    try:
        res = supabase.table("inventory").select("*").eq("farmer_id", farmer_id).execute()
        inventory = res.data or []
    except Exception as e:
        inventory = []

    enriched = await MandiService.get_prices_for_inventory(inventory, state=state)
    board = await MandiService.get_board(state=state)

    return {
        "success": True,
        "inventory": enriched,
        "board": board,
        "state": state,
    }
