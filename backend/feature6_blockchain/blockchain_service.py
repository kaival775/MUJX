import hashlib
import json
import time
from typing import List, Optional
from core.supabase_client import supabase

class CropBlock:
    def __init__(self, index, previous_hash, timestamp, data, event_type, block_hash=None):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.data = data
        self.event_type = event_type
        # If hash is provided (loading from DB), use it. Otherwise calculate.
        self.hash = block_hash if block_hash else self.calculate_hash()

    def calculate_hash(self):
        block_string = json.dumps({
            "index": self.index,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "data": self.data,
            "event_type": self.event_type
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

class BlockchainLedger:
    def __init__(self, chain: List[CropBlock]):
        self.chain = chain

    @staticmethod
    def create_genesis_block():
        return CropBlock(0, "0", int(time.time()), {"message": "Genesis Block - Annadata Saathi"}, "GENESIS")

    def get_latest_block(self):
        return self.chain[-1] if self.chain else self.create_genesis_block()

    def _persist_block(self, batch_id: str, block: CropBlock):
        try:
            supabase.table("crop_events").insert({
                "batch_id": batch_id,
                "event_type": block.event_type,
                "event_data": block.data,
                "timestamp": block.timestamp,
                "previous_hash": block.previous_hash,
                "block_hash": block.hash,
                "block_index": block.index
            }).execute()
        except Exception as e:
            print(f"Error saving block to DB: {e}")

    def add_event(self, batch_id: str, event_type: str, data: dict):
        latest_block = self.get_latest_block()
        
        # If the latest block is a memory-only Genesis block (index 0) 
        # and not in DB, we should persist it first if it hasn't been.
        # But a better way is to ensure create_batch handles this.
        
        new_block = CropBlock(
            index=latest_block.index + 1,
            previous_hash=latest_block.hash,
            timestamp=int(time.time()),
            data=data,
            event_type=event_type
        )
        self.chain.append(new_block)
        self._persist_block(batch_id, new_block)
        return new_block

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i-1]

            # 1. Recalculate hash to check for data tampering
            if current.hash != current.calculate_hash():
                print(f"Hash mismatch at index {current.index}")
                return False
                
            # 2. Check link to previous block
            if current.previous_hash != previous.hash:
                print(f"Link broken at index {current.index}")
                return False
        return True

    def get_chain_dict(self):
        return [
            {
                "index": block.index,
                "timestamp": block.timestamp,
                "event": block.event_type,
                "data": block.data,
                "hash": block.hash,
                "previous_hash": block.previous_hash
            }
            for block in self.chain
        ]

def get_ledger_from_db(batch_id: str) -> BlockchainLedger:
    # Fetch events sorted by index
    response = supabase.table("crop_events")\
        .select("*")\
        .eq("batch_id", batch_id)\
        .order("block_index", desc=False)\
        .execute()

    blocks = []
    
    # If no blocks found, return empty ledger (so it can create Genesis)
    if not response.data:
        # Implicitly, the first block added will link to Genesis, 
        # but usually we want to persist Genesis too. 
        # For simplicity, we assume if empty, we start fresh.
        # Ideally, we should insert Genesis on batch creation.
        # Here we just initialize with Genesis in memory.
        return BlockchainLedger([BlockchainLedger.create_genesis_block()])

    for row in response.data:
        blocks.append(CropBlock(
            index=row['block_index'],
            previous_hash=row['previous_hash'],
            timestamp=row['timestamp'],
            data=row['event_data'],
            event_type=row['event_type'],
            block_hash=row['block_hash']
        ))
    
    return BlockchainLedger(blocks)
