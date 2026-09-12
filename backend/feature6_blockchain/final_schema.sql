-- FEATURE 6: BLOCKCHAIN & INVENTORY SCHEMA
-- Run this in Supabase SQL Editor

-- 1. Inventory Table 
-- Stores the list of produce batches owned by the farmer
CREATE TABLE IF NOT EXISTS public.inventory (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  farmer_id TEXT NOT NULL, -- Simplified to TEXT to account for potential Supabase User ID or external ID
  crop_name TEXT NOT NULL,
  variety TEXT,
  quantity NUMERIC NOT NULL, -- In Quintals
  price_per_quintal NUMERIC NOT NULL,
  status TEXT DEFAULT 'growing', -- 'growing', 'harvested', 'ready_for_sale', 'listed', 'sold'
  harvest_date TIMESTAMP WITH TIME ZONE,
  quality_grade TEXT,
  batch_id TEXT UNIQUE NOT NULL, -- KEY: The unique identifier for Blockchain tracking
  image_url TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Blockchain Ledger Table
-- Stores the immutable history of events for each batch
CREATE TABLE IF NOT EXISTS public.crop_events (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  batch_id TEXT REFERENCES public.inventory(batch_id) ON DELETE CASCADE,
  event_type TEXT NOT NULL, -- SOWING, IRRIGATION, FERTILIZER, HARVEST, DISEASE_CHECK, etc.
  event_data JSONB NOT NULL, -- Flexible details (e.g., {"amount": "500L", "method": "Drip"})
  timestamp BIGINT NOT NULL, -- Unix timestamp for consistent hashing
  previous_hash TEXT NOT NULL, -- The link to the previous block
  block_hash TEXT NOT NULL, -- The hash of the current block
  block_index INTEGER NOT NULL, -- Sequence number (0, 1, 2...)
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Indexes
CREATE INDEX IF NOT EXISTS idx_inventory_farmer ON public.inventory(farmer_id);
CREATE INDEX IF NOT EXISTS idx_crop_events_batch ON public.crop_events(batch_id);

-- 4. RLS (Enable Public Access for MVP Demo)
ALTER TABLE public.inventory ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow Public Inventory Access" ON public.inventory FOR ALL USING (true);

ALTER TABLE public.crop_events ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow Public Ledger Access" ON public.crop_events FOR ALL USING (true);
