from typing import Dict, Any, List
import numpy as np
import time
from datetime import datetime
from core.supabase_client import supabase

def get_batch_events(batch_id: str) -> List[Dict[str, Any]]:
    """Helper to fetch events for a batch."""
    try:
        res = supabase.table("crop_events").select("*").eq("batch_id", batch_id).order("timestamp").execute()
        return res.data or []
    except:
        return []

def calculate_integrity_score(batch_id: str, events: List[Dict[str, Any]] = None) -> int:
    """
    Calculates Integrity Score dynamically based on lifecycle stage.
    """
    if events is None:
        events = get_batch_events(batch_id)
        
    print(f"CALCULATING INTEGRITY for {batch_id}: Found {len(events)} events")
    
    if not events:
        return 0
        
    # 1. Base Score - Logic changes based on what the farmer SHOULD have done by now
    score = 100
    event_types = [e["event_type"] for e in events]
    
    # 2. Lifecycle Context (Dynamic Expectation)
    try:
        inv_res = supabase.table("inventory").select("status", "created_at").eq("batch_id", batch_id).execute()
        status = inv_res.data[0]["status"] if inv_res.data else "growing"
    except:
        status = "growing"

    # 3. Dynamic Evidence Checks
    # a) Mandatory Evidence
    if "GENESIS" not in event_types: score -= 20
    if "SOWING" not in event_types: score -= 30
    
    # b) Cadence Check (Predictive: Are they logging regularly?)
    if len(events) > 1:
        # Check gap between events. If 0 blocks for 60 days, integrity drops.
        timestamps = sorted([e["timestamp"] for e in events])
        if (int(time.time()) - timestamps[-1]) > (21 * 24 * 3600): # +21 days since last log
            score -= 15 # "Cold Lead" penalty for not updating logs
            print(f"Integrity Drop: No recent activity for {batch_id}")

    # c) Fulfillment Check (Based on Status)
    if status == "ready_for_sale":
        if "HARVEST" not in event_types: score -= 40 # Can't be ready for sale without harvest log
        if "IRRIGATION" not in event_types: score -= 20
        if "FERTILIZER" not in event_types: score -= 10
    
    # d) Logic & Fraud Check (Predictive)
    sowing_e = next((e for e in events if e["event_type"] == "SOWING"), None)
    harvest_e = next((e for e in events if e["event_type"] == "HARVEST"), None)
    
    if sowing_e and harvest_e:
        duration_days = (harvest_e["timestamp"] - sowing_e["timestamp"]) / (24 * 3600)
        if duration_days < 70: # Standard growing period for most Grains/Oilseeds
             score -= 25 # Unrealistic yield timeline flag
             print(f"Integrity Drop: Unrealistic timeline ({duration_days} days)")

    # 4. Final Output
    final_score = max(5, min(100, score)) # Minimum 5 for on-chain identity
    print(f"FINAL SCORE for {batch_id}: {final_score}")
    return final_score

def generate_cultivation_summary(batch_id: str, events: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Generates dynamic AI-ready summaries of verified events.
    """
    if events is None:
        events = get_batch_events(batch_id)
        
    summary = {
        "irrigation": {"total_cycles": 0, "source": "Not Logged", "last_event": "N/A"},
        "fertilizer": {"types": [], "safety": "Verified Safe", "total_logs": 0},
        "disease": {"history": "None Detected", "last_check": "N/A", "alerts": 0},
        "blockchain": {"blocks": len(events), "status": "Immutable", "last_sync": datetime.now().isoformat()}
    }
    
    for event in events:
        e_type = event["event_type"]
        data = event.get("event_data", {})
        ts = event.get("timestamp")
        
        if e_type == "IRRIGATION":
            summary["irrigation"]["total_cycles"] += 1
            summary["irrigation"]["source"] = data.get("source", "Well/Borewell")
            summary["irrigation"]["last_event"] = datetime.fromtimestamp(ts).strftime('%d %b %Y') if ts else "N/A"
                
        elif e_type == "FERTILIZER":
            summary["fertilizer"]["total_logs"] += 1
            f_type = data.get("type", "Standard NPK")
            if f_type not in summary["fertilizer"]["types"]:
                summary["fertilizer"]["types"].append(f_type)
            if "chemical" in f_type.lower() or "synthetic" in f_type.lower():
                summary["fertilizer"]["safety"] = "Commercial Grade"
        
        elif e_type == "DISEASE_CHECK":
            summary["disease"]["last_check"] = datetime.fromtimestamp(ts).strftime('%d %b %Y') if ts else "N/A"
            if data.get("issue_detected") == "Yes":
                summary["disease"]["history"] = f"Detected: {data.get('details', 'Unknown')}"
                summary["disease"]["alerts"] += 1
                
    return summary

def update_inventory_trust_data(batch_id: str):
    """
    Utility to update inventory record with calculated scores/summaries.
    """
    events = get_batch_events(batch_id)
    score = calculate_integrity_score(batch_id, events)
    summary = generate_cultivation_summary(batch_id, events)
    
    try:
        supabase.table("inventory").update({
            "integrity_score": score,
            "cultivation_summary": summary,
            "verified_badge": score > 85
        }).eq("batch_id", batch_id).execute()
        return True
    except:
        return False
