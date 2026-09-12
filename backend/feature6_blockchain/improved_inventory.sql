-- IMPROVED INVENTORY & TRUST LAYER SCHEMA
-- Run this in Supabase SQL Editor

-- 1. Extend Inventory Table
ALTER TABLE public.inventory ADD COLUMN IF NOT EXISTS location TEXT DEFAULT 'Unknown';
ALTER TABLE public.inventory ADD COLUMN IF NOT EXISTS district TEXT DEFAULT 'Unknown';
ALTER TABLE public.inventory ADD COLUMN IF NOT EXISTS area_cultivated NUMERIC;
ALTER TABLE public.inventory ADD COLUMN IF NOT EXISTS sowing_date TIMESTAMPTZ;
ALTER TABLE public.inventory ADD COLUMN IF NOT EXISTS available_quantity NUMERIC;
ALTER TABLE public.inventory ADD COLUMN IF NOT EXISTS cultivation_summary JSONB DEFAULT '{}';
ALTER TABLE public.inventory ADD COLUMN IF NOT EXISTS integrity_score NUMERIC DEFAULT 100;
ALTER TABLE public.inventory ADD COLUMN IF NOT EXISTS verified_badge BOOLEAN DEFAULT FALSE;
ALTER TABLE public.inventory ADD COLUMN IF NOT EXISTS sustainability_score NUMERIC DEFAULT 0;
ALTER TABLE public.inventory ADD COLUMN IF NOT EXISTS health_status TEXT DEFAULT 'Healthy';
ALTER TABLE public.inventory ADD COLUMN IF NOT EXISTS ndvi_history JSONB DEFAULT '[]';

-- Update available_quantity for existing records
UPDATE public.inventory SET available_quantity = quantity WHERE available_quantity IS NULL;

-- 2. Extend Farmer Profiles for Reputation
ALTER TABLE public.farmer_profiles ADD COLUMN IF NOT EXISTS identity_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE public.farmer_profiles ADD COLUMN IF NOT EXISTS farm_geo_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE public.farmer_profiles ADD COLUMN IF NOT EXISTS active_seasons_completed INTEGER DEFAULT 0;
ALTER TABLE public.farmer_profiles ADD COLUMN IF NOT EXISTS fraud_flags INTEGER DEFAULT 0;
ALTER TABLE public.farmer_profiles ADD COLUMN IF NOT EXISTS total_sales INTEGER DEFAULT 0;
ALTER TABLE public.farmer_profiles ADD COLUMN IF NOT EXISTS on_time_delivery_pct NUMERIC DEFAULT 100;
ALTER TABLE public.farmer_profiles ADD COLUMN IF NOT EXISTS reputation_rating NUMERIC DEFAULT 5.0;

-- 3. Create Marketplace Listing View (or table)
-- We use a table so we can store status independently
CREATE TABLE IF NOT EXISTS public.marketplace_listings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    batch_id TEXT UNIQUE REFERENCES public.inventory(batch_id) ON DELETE CASCADE,
    farmer_id TEXT REFERENCES public.farmer_profiles(user_id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS for marketplace
ALTER TABLE public.marketplace_listings ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow Public Marketplace Access" ON public.marketplace_listings FOR SELECT USING (true);
CREATE POLICY "Allow Farmers to manage listings" ON public.marketplace_listings FOR ALL USING (true);
