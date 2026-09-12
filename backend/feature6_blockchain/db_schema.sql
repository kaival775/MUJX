-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- 1. Inventory Table (Stock Management)
create table public.inventory (
  id uuid default uuid_generate_v4() primary key,
  farmer_id uuid not null, -- Links to auth.users if needed, or just a string for MVP
  crop_name text not null,
  variety text,
  quantity numeric not null, -- In Quintals
  price_per_quintal numeric not null,
  status text check (status in ('harvested', 'ready_for_sale', 'listed', 'sold')) default 'harvested',
  harvest_date timestamp with time zone default now(),
  quality_grade text,
  batch_id text unique not null, -- The key for Blockchain tracking
  image_url text,
  created_at timestamp with time zone default now()
);

-- 2. Orders Table (Commerce)
create table public.orders (
  id uuid default uuid_generate_v4() primary key,
  buyer_id uuid, -- Can be null for guest checkout
  inventory_id uuid references public.inventory(id),
  quantity numeric not null,
  total_price numeric not null,
  status text check (status in ('pending', 'confirmed', 'shipped', 'delivered', 'cancelled')) default 'pending',
  order_date timestamp with time zone default now()
);

-- 3. Blockchain Ledger Table (Immutable Events)
-- This stores the "blocks" of our crop history
create table public.crop_events (
  id uuid default uuid_generate_v4() primary key,
  batch_id text references public.inventory(batch_id),
  event_type text not null, -- SEEDING, IRRIGATION, FERTILIZER, HARVEST
  event_data jsonb not null, -- Flexible details (e.g. fertilizer name, water amount)
  timestamp bigint not null, -- Unix timestamp for hashing
  previous_hash text not null,
  block_hash text not null,
  block_index integer not null,
  created_at timestamp with time zone default now()
);

-- Indexes for performance
create index idx_inventory_farmer on public.inventory(farmer_id);
create index idx_crop_events_batch on public.crop_events(batch_id);

-- RLS Policies (Simple for MVP: Enable all access, secure later)
alter table public.inventory enable row level security;
create policy "Public Access" on public.inventory for all using (true);

alter table public.orders enable row level security;
create policy "Public Access" on public.orders for all using (true);

alter table public.crop_events enable row level security;
create policy "Public Access" on public.crop_events for all using (true);
