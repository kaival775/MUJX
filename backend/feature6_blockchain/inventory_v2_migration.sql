-- ============================================================
-- Inventory V2 Migration
-- Adds category, unit, and item_name columns to inventory table
-- Run this once against your Supabase project SQL editor
-- ============================================================

-- 1. Category: produce | inputs | assets | financials
ALTER TABLE public.inventory
    ADD COLUMN IF NOT EXISTS category TEXT DEFAULT 'produce'
    CHECK (category IN ('produce', 'inputs', 'assets', 'financials'));

-- 2. Unit of measurement (kg, litre, bags, pieces, quintal, tonne, etc.)
ALTER TABLE public.inventory
    ADD COLUMN IF NOT EXISTS unit TEXT DEFAULT 'kg';

-- 3. Display name for the item (mirrors crop_name for produce; used for non-crop items)
ALTER TABLE public.inventory
    ADD COLUMN IF NOT EXISTS item_name TEXT;

-- 4. Original quantity at time of addition (used to compute relative stock %)
ALTER TABLE public.inventory
    ADD COLUMN IF NOT EXISTS original_quantity NUMERIC DEFAULT NULL;

-- 4. Backfill item_name from crop_name for all existing rows
UPDATE public.inventory SET item_name = crop_name WHERE item_name IS NULL;

-- Done
