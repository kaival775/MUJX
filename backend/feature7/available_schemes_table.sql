-- Create Available Schemes Table
CREATE TABLE IF NOT EXISTS public.available_schemes (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    scheme_name text NOT NULL,
    description text NOT NULL,
    subsidy_percentage numeric DEFAULT 0,
    max_amount numeric DEFAULT 0,
    eligibility jsonb DEFAULT '[]'::jsonb,
    applicable_equipment jsonb DEFAULT '[]'::jsonb,
    source text NOT NULL,
    application_url text,
    state text, -- 'Maharashtra' or NULL for Central
    category text DEFAULT 'General'::text,
    valid_until date,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT available_schemes_pkey PRIMARY KEY (id)
);

-- Index for faster filtering
CREATE INDEX IF NOT EXISTS idx_available_schemes_state ON available_schemes(state);
CREATE INDEX IF NOT EXISTS idx_available_schemes_category ON available_schemes(category);
CREATE INDEX IF NOT EXISTS idx_available_schemes_name ON available_schemes(scheme_name);
