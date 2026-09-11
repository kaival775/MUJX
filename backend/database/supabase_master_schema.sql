-- =============================================================================
-- MASTER DATABASE RESET & SCHEMA INITIALIZATION FOR LET'S GO 3.0 (SUPABASE)
-- =============================================================================
-- INSTRUCTIONS:
-- 1. Copy the ENTIRE contents of this file.
-- 2. Open your Supabase Dashboard (https://supabase.com).
-- 3. Go to the "SQL Editor" section on the left sidebar.
-- 4. Create a "New Query", paste this script, and click "Run".
-- =============================================================================

-- =============================================================================
-- PHASE 0: CLEANUP (Drop tables in reverse dependency order to avoid constraints)
-- =============================================================================
DROP TABLE IF EXISTS public.farm_actions CASCADE;
DROP TABLE IF EXISTS public.farm_data CASCADE;
DROP TABLE IF EXISTS public.admin_activity_log CASCADE;
DROP TABLE IF EXISTS public.admin_stats CASCADE;
DROP TABLE IF EXISTS public.grampanchayat_submissions CASCADE;
DROP TABLE IF EXISTS public.grampanchayat_schemes CASCADE;
DROP TABLE IF EXISTS public.grampanchayat_users CASCADE;
DROP TABLE IF EXISTS public.marketplace_listings CASCADE;
DROP TABLE IF EXISTS public.crop_events CASCADE;
DROP TABLE IF EXISTS public.inventory CASCADE;
DROP TABLE IF EXISTS public.autonomous_ledger CASCADE;
DROP TABLE IF EXISTS public.autonomous_sensors CASCADE;
DROP TABLE IF EXISTS public.land_health_logs CASCADE;
DROP TABLE IF EXISTS public.ndvi_records CASCADE;
DROP TABLE IF EXISTS public.crops CASCADE;
DROP TABLE IF EXISTS public.agronomists CASCADE;
DROP TABLE IF EXISTS public.broadcasts CASCADE;
DROP TABLE IF EXISTS public.field_officer_assignments CASCADE;
DROP TABLE IF EXISTS public.field_officers CASCADE;
DROP TABLE IF EXISTS public.claim_applications CASCADE;
DROP TABLE IF EXISTS public.claims CASCADE;
DROP TABLE IF EXISTS public.risk_events CASCADE;
DROP TABLE IF EXISTS public.scheme_applications CASCADE;
DROP TABLE IF EXISTS public.available_schemes CASCADE;
DROP TABLE IF EXISTS public.blockchain_events CASCADE;
DROP TABLE IF EXISTS public.land_documents CASCADE;
DROP TABLE IF EXISTS public.lands CASCADE;
DROP TABLE IF EXISTS public.report_logs CASCADE;
DROP TABLE IF EXISTS public.farmer_profiles CASCADE;
DROP TABLE IF EXISTS public.activity_logs CASCADE;
DROP TABLE IF EXISTS public.sessions CASCADE;
DROP TABLE IF EXISTS public.users CASCADE;

-- Drop generic trigger helper if it exists
DROP FUNCTION IF EXISTS update_updated_at_column CASCADE;

-- =============================================================================
-- PHASE 1: CORE UTILITY FUNCTIONS & TRIGGERS
-- =============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- PHASE 2: CORE IDENTITY & AUTHENTICATION
-- =============================================================================

-- 1. users Table (Core Authentication Profile)
CREATE TABLE public.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone_number VARCHAR(20) NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'farmer' CHECK (role IN ('farmer', 'user', 'admin', 'visitor')),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. sessions Table (User logins)
CREATE TABLE public.sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    user_agent TEXT NULL,
    ip_address VARCHAR(45) NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. activity_logs Table (User audit logs)
CREATE TABLE public.activity_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource VARCHAR(255) NULL,
    details JSONB NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- PHASE 3: PROFILE MANAGEMENT
-- =============================================================================

-- 4. farmer_profiles Table (Unified Profile for Marketplace, Claims & Advisory)
CREATE TABLE public.farmer_profiles (
    id UUID UNIQUE DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL PRIMARY KEY, -- Auth user UUID or local login ID
    
    -- Personal Details
    name TEXT NULL, -- Old profile support
    phone TEXT NULL, -- Old profile support
    full_name TEXT NULL,
    father_husband_name TEXT NULL,
    date_of_birth DATE NULL,
    gender TEXT NULL,
    
    -- Contact Details
    mobile_number TEXT NULL,
    alternate_mobile TEXT NULL,
    email TEXT NULL,
    
    -- Identity Documents
    aadhaar_number TEXT NULL,
    pan_number TEXT NULL,
    voter_id TEXT NULL,
    
    -- Address Details
    address_line1 TEXT NULL,
    address_line2 TEXT NULL,
    village TEXT NULL,
    district TEXT NULL,
    state TEXT NULL,
    pincode TEXT NULL,
    
    -- Farm Details
    land_size DECIMAL(10,2) NULL,
    land_unit TEXT DEFAULT 'acres',
    survey_number TEXT NULL,
    land_ownership TEXT NULL, -- Owned/Leased/Shared
    soil_type TEXT NULL,
    gps TEXT DEFAULT 'N/A',
    irrigation_status BOOLEAN DEFAULT TRUE,
    crops TEXT NULL, -- Crop types listed as comma-separated text
    
    -- Bank Details (for subsidy transfer)
    bank_name TEXT NULL,
    account_number TEXT NULL,
    ifsc_code TEXT NULL,
    branch_name TEXT NULL,
    
    -- Category & Eligibility
    category TEXT NULL, -- General/SC/ST/OBC/EWS
    farmer_type TEXT NULL, -- Marginal/Small/Medium/Large
    annual_income DECIMAL(12,2) NULL,
    
    -- NDVI Analysis & Crop Loss (Calculated from Sentinel satellite telemetry)
    last_ndvi_value DECIMAL(5,3) NULL,
    crop_loss_percentage DECIMAL(5,2) NULL,
    last_ndvi_analysis_date TIMESTAMP NULL,
    
    -- Document Upload URLs (Supabase storage references)
    aadhaar_doc_url TEXT NULL,
    land_doc_url TEXT NULL,
    bank_passbook_url TEXT NULL,
    photo_url TEXT NULL,
    
    -- Marketplace Reputation Stats
    identity_verified BOOLEAN DEFAULT FALSE,
    farm_geo_verified BOOLEAN DEFAULT FALSE,
    active_seasons_completed INTEGER DEFAULT 0,
    fraud_flags INTEGER DEFAULT 0,
    total_sales INTEGER DEFAULT 0,
    on_time_delivery_pct NUMERIC DEFAULT 100,
    reputation_rating NUMERIC DEFAULT 5.0,
    
    -- Status & Workflow
    role TEXT DEFAULT 'farmer' CHECK (role IN ('farmer', 'visitor', 'admin')),
    profile_completed BOOLEAN DEFAULT FALSE,
    verified BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. report_logs Table (Tracks generated PDF Advisory & Soil reports)
CREATE TABLE public.report_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NULL,
    farmer_name TEXT NULL,
    language TEXT DEFAULT 'en',
    soil_type TEXT NULL,
    farm_size TEXT NULL,
    sensor_snapshot JSONB NULL,
    generated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- PHASE 4: LAND REGISTRATION & BLOCKCHAIN VERIFICATION (Feature 6: Mark My Land)
-- =============================================================================

-- 6. lands Table (Registered Farm Polygon Boundaries)
CREATE TABLE public.lands (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    polygon_coordinates JSONB NOT NULL, -- Format: [{'lat':..., 'lng':...}, ...]
    area_sqm NUMERIC NULL,
    status TEXT DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'VERIFIED', 'REJECTED')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. land_documents Table (OCR Extraction details for land deeds)
CREATE TABLE public.land_documents (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    land_id UUID REFERENCES public.lands(id) ON DELETE CASCADE,
    document_url TEXT NOT NULL,
    extracted_area_sqm NUMERIC NULL,
    confidence_score NUMERIC NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 8. blockchain_events Table (Verification ledger for lands)
CREATE TABLE public.blockchain_events (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    land_id UUID REFERENCES public.lands(id) ON DELETE CASCADE,
    document_id UUID REFERENCES public.land_documents(id) ON DELETE CASCADE,
    data_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- PHASE 5: SUBSIDY SCHEMES & ENROLLMENT (Feature 5 & 7)
-- =============================================================================

-- 9. available_schemes Table (Directory of Government Schemes available)
CREATE TABLE public.available_schemes (
    id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    scheme_name TEXT NOT NULL,
    description TEXT NOT NULL,
    subsidy_percentage NUMERIC DEFAULT 0,
    max_amount NUMERIC DEFAULT 0,
    eligibility JSONB DEFAULT '[]'::jsonb, -- String array of conditions
    applicable_equipment JSONB DEFAULT '[]'::jsonb,
    source TEXT NOT NULL,
    application_url TEXT NULL,
    state TEXT NULL, -- NULL for Central schemes, state name for state schemes
    category TEXT DEFAULT 'General'::text,
    valid_until DATE NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 10. scheme_applications Table (Farmers' submissions for schemes)
CREATE TABLE public.scheme_applications (
    id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    reference_no TEXT UNIQUE NOT NULL,
    user_id TEXT NOT NULL,
    farmer_name TEXT NULL,
    farmer_phone TEXT NULL,
    scheme_name TEXT NOT NULL,
    status TEXT NULL DEFAULT 'submitted'::text, -- submitted, under_review, approved, rejected, completed
    application_details JSONB NULL, -- Flexible structure holding documents and answers
    created_at TIMESTAMP WITH TIME ZONE NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NULL DEFAULT NOW()
);

-- =============================================================================
-- PHASE 6: DISASTER ASSESSMENT, CLAIMS & INSPECTIONS (Feature 4 & 5)
-- =============================================================================

-- 11. risk_events Table (Disaster/Disease Risk triggers)
CREATE TABLE public.risk_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    risk_level TEXT NOT NULL, -- e.g. HIGH, MEDIUM, LOW
    status TEXT DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'CLAIM_INITIATED', 'RESOLVED')),
    details JSONB DEFAULT '{}'::jsonb, -- {"location": "...", "description": "..."}
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 12. claim_applications Table (Crop damage claims submitted by farmers)
CREATE TABLE public.claim_applications (
    id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    reference_no TEXT UNIQUE NOT NULL, -- e.g. CLM-2026-00001
    
    -- Identification
    user_id TEXT NOT NULL,
    farmer_name TEXT NULL,
    father_husband_name TEXT NULL,
    farmer_phone TEXT NULL,
    aadhaar_number TEXT NULL,
    
    -- Claim Details
    scheme_name TEXT NOT NULL,
    claim_type TEXT DEFAULT 'crop_loss', -- crop_loss, subsidy, insurance
    land_size DECIMAL(10,2) NULL,
    land_unit TEXT DEFAULT 'acres',
    crop_name TEXT NULL,
    
    -- AI NDVI Assessment
    ndvi_value DECIMAL(5,3) NULL,
    crop_loss_percentage DECIMAL(5,2) NULL,
    loss_assessment_date TIMESTAMP NULL,
    
    -- Financial Details
    claim_amount DECIMAL(12,2) NULL,
    approved_amount DECIMAL(12,2) NULL,
    subsidy_percentage DECIMAL(5,2) NULL,
    
    -- Status & Priority
    status TEXT NULL DEFAULT 'submitted', -- submitted, under_review, approved, rejected, completed
    priority TEXT DEFAULT 'normal', -- urgent, high, normal, low
    
    -- Flexible metadata
    application_details JSONB NULL,
    loss_details JSONB NULL,
    document_urls JSONB NULL, -- {aadhaar_doc: url, land_doc: url, crop_photos: []}
    
    -- Admin Management
    admin_notes TEXT NULL,
    reviewed_by TEXT NULL,
    reviewed_at TIMESTAMP NULL,
    approved_by TEXT NULL,
    approved_at TIMESTAMP NULL,
    
    -- Payment Details
    payment_status TEXT DEFAULT 'pending', -- pending, processed, completed
    payment_reference TEXT NULL,
    payment_date TIMESTAMP NULL,
    
    -- Field Inspection Integration (Feature 4 & 5 Extension)
    assigned_inspector_id UUID NULL,
    inspection_deadline TIMESTAMP WITH TIME ZONE NULL,
    inspection_status TEXT DEFAULT 'pending', -- pending, scheduled, completed, report_submitted
    inspection_report JSONB NULL, -- {visited_at, photos: [], loss_estimate, remarks}
    official_pdf_url TEXT NULL,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NULL DEFAULT NOW()
);

-- 13. field_officers Table (Inspectors directory)
CREATE TABLE public.field_officers (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    officer_id TEXT UNIQUE NOT NULL, -- e.g. officer-001
    name TEXT NOT NULL,
    zone TEXT NOT NULL,
    email TEXT NULL,
    phone TEXT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 14. field_officer_assignments Table (Physical site visits logs)
CREATE TABLE public.field_officer_assignments (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    claim_id UUID REFERENCES public.claim_applications(id) ON DELETE CASCADE,
    officer_name TEXT NOT NULL,
    officer_contact TEXT NULL,
    assignment_date TIMESTAMPTZ DEFAULT NOW(),
    visit_deadline TIMESTAMPTZ NULL,
    status TEXT DEFAULT 'Assigned' CHECK (status IN ('Assigned', 'Visited', 'Report Submitted')),
    
    -- Verification Report details
    report_loss_estimate NUMERIC NULL,
    report_remarks TEXT NULL,
    report_evidence_urls JSONB NULL,
    report_submitted_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 15. broadcasts Table (Admin / Grampanchayat broadcast notifications)
CREATE TABLE public.broadcasts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    sender_id UUID REFERENCES public.users(id),
    message TEXT NOT NULL,
    region TEXT NULL,
    alert_type TEXT DEFAULT 'General' CHECK (alert_type IN ('General', 'Weather', 'Emergency', 'Deadline')),
    channels JSONB NULL, -- ['SMS', 'App', 'Email']
    sent_at TIMESTAMPTZ DEFAULT NOW()
);

-- 16. claims Table (Legacy/Alternate table for backward compatibility)
CREATE TABLE public.claims (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    farmer_id UUID REFERENCES public.users(id),
    farmer_name TEXT NOT NULL,
    farm_id TEXT NULL,
    crop_type TEXT NOT NULL,
    estimated_loss_percentage NUMERIC NULL,
    claim_amount_requested NUMERIC NULL,
    submission_date TIMESTAMPTZ DEFAULT NOW(),
    ndvi_confidence_score NUMERIC NULL,
    status TEXT DEFAULT 'Pending' CHECK (status IN ('Pending', 'Needs Verification', 'Approved', 'Rejected')),
    rejection_reason TEXT NULL,
    evidence_urls JSONB NULL,
    is_signed BOOLEAN DEFAULT FALSE,
    digital_signature_hash TEXT NULL,
    signed_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- PHASE 7: ADVISORY & CONSULTATION (Feature 2)
-- =============================================================================

-- 17. agronomists Table (Directory of Agricultural experts)
CREATE TABLE public.agronomists (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL UNIQUE,
    specialization VARCHAR(255) DEFAULT 'General Agriculture',
    experience_years INTEGER DEFAULT 0,
    is_available BOOLEAN DEFAULT TRUE,
    rating DECIMAL(3,2) DEFAULT 0.00,
    total_consultations INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- =============================================================================
-- PHASE 8: SATELLITE NDVI RESILIENCE & CROP HEALTH MONITORING
-- =============================================================================

-- 18. crops Table (Tracks crops on registered lands)
CREATE TABLE public.crops (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    land_id UUID REFERENCES public.lands(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    variety TEXT NULL,
    planting_date DATE NOT NULL,
    harvest_date_est DATE NULL,
    status TEXT DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'HARVESTED', 'FAILED')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 19. ndvi_records Table (Timeseries Sentinel-2 data)
CREATE TABLE public.ndvi_records (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    land_id UUID REFERENCES public.lands(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    mean_ndvi NUMERIC NOT NULL,
    min_ndvi NUMERIC NULL,
    max_ndvi NUMERIC NULL,
    cloud_cover_percentage NUMERIC NULL,
    image_url TEXT NULL,
    source TEXT DEFAULT 'Sentinel-2',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(land_id, date)
);

-- 20. land_health_logs Table (Automatic crop health stress analysis results)
CREATE TABLE public.land_health_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    land_id UUID REFERENCES public.lands(id) ON DELETE CASCADE,
    check_date DATE DEFAULT CURRENT_DATE,
    risk_state TEXT NOT NULL CHECK (risk_state IN ('HEALTHY', 'EARLY_STRESS', 'SEVERE_STRESS', 'CROP_LOSS_LIKELY')),
    ndvi_baseline NUMERIC NULL,
    ndvi_current NUMERIC NULL,
    stress_reason TEXT NULL,
    recommendation TEXT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- PHASE 9: TELEMETRY & HARDWARE INTEGRATION (Feature 3)
-- =============================================================================

-- 21. autonomous_sensors Table (IoT sensory snapshot)
CREATE TABLE public.autonomous_sensors (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT NOT NULL,
    data JSONB NOT NULL, -- Snapshots of NPK, EC, Moisture, Temp
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 22. autonomous_ledger Table (IoT Blockchain telemetry logger)
CREATE TABLE public.autonomous_ledger (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    hash TEXT NOT NULL,
    user_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    details JSONB NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    previous_hash TEXT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- PHASE 10: INVENTORY & BLOCKCHAIN TRACEABILITY (Feature 6: Trust Layer)
-- =============================================================================

-- 23. inventory Table (Stock items of produce listed by farmers)
CREATE TABLE public.inventory (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    farmer_id TEXT NOT NULL,
    crop_name TEXT NOT NULL,
    variety TEXT NULL,
    quantity NUMERIC NOT NULL, -- Total quantity in Stock
    price_per_quintal NUMERIC NOT NULL,
    status TEXT DEFAULT 'growing', -- growing, harvested, ready_for_sale, listed, sold
    harvest_date TIMESTAMP WITH TIME ZONE NULL,
    quality_grade TEXT NULL,
    batch_id TEXT UNIQUE NOT NULL, -- Blockchain Unique Identifier
    image_url TEXT NULL,
    
    -- Improved Inventory fields
    location TEXT DEFAULT 'Unknown',
    district TEXT DEFAULT 'Unknown',
    area_cultivated NUMERIC NULL,
    sowing_date TIMESTAMPTZ NULL,
    available_quantity NUMERIC NULL,
    cultivation_summary JSONB DEFAULT '{}'::jsonb,
    integrity_score NUMERIC DEFAULT 100,
    verified_badge BOOLEAN DEFAULT FALSE,
    sustainability_score NUMERIC DEFAULT 0,
    health_status TEXT DEFAULT 'Healthy',
    ndvi_history JSONB DEFAULT '[]'::jsonb,
    
    -- Category and Units
    category TEXT DEFAULT 'produce' CHECK (category IN ('produce', 'inputs', 'assets', 'financials')),
    unit TEXT DEFAULT 'kg',
    item_name TEXT NULL,
    original_quantity NUMERIC DEFAULT NULL,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 24. crop_events Table (Blockchain Block ledger tracking changes in inventory)
CREATE TABLE public.crop_events (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  batch_id TEXT REFERENCES public.inventory(batch_id) ON DELETE CASCADE,
  event_type TEXT NOT NULL, -- SOWING, IRRIGATION, FERTILIZER, HARVEST, etc.
  event_data JSONB NOT NULL,
  timestamp BIGINT NOT NULL,
  previous_hash TEXT NOT NULL,
  block_hash TEXT NOT NULL,
  block_index INTEGER NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 25. marketplace_listings Table (Active items listed for public buying)
CREATE TABLE public.marketplace_listings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    batch_id TEXT UNIQUE REFERENCES public.inventory(batch_id) ON DELETE CASCADE,
    farmer_id TEXT REFERENCES public.farmer_profiles(user_id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- PHASE 11: GRAMPANCHAYAT PORTAL & STATE STATISTICS (Feature 7)
-- =============================================================================

-- 26. grampanchayat_users Table (Local Gram Panchayat Admins)
CREATE TABLE public.grampanchayat_users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gp_name         TEXT NOT NULL,
    district        TEXT NOT NULL,
    taluka          TEXT NOT NULL,
    state           TEXT NOT NULL DEFAULT 'Maharashtra',
    sarpanch_name   TEXT NULL,
    phone           TEXT NULL,
    email           TEXT NULL,
    password_hash   TEXT DEFAULT 'gp_secure_2024',
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 27. grampanchayat_schemes Table (Locally managed schemes and budgets)
CREATE TABLE public.grampanchayat_schemes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gp_id           UUID REFERENCES public.grampanchayat_users(id) ON DELETE CASCADE,
    scheme_name     TEXT NOT NULL,
    ministry        TEXT NULL,
    budget_allotted NUMERIC(14,2) NULL,
    budget_used     NUMERIC(14,2) DEFAULT 0,
    beneficiaries   INTEGER DEFAULT 0,
    status          TEXT DEFAULT 'active' CHECK (status IN ('active','completed','paused')),
    deadline        DATE NULL,
    description     TEXT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 28. grampanchayat_submissions Table (Requests submitted to local GPs by farmers)
CREATE TABLE public.grampanchayat_submissions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gp_id           UUID REFERENCES public.grampanchayat_users(id) ON DELETE CASCADE,
    farmer_name     TEXT NOT NULL,
    village         TEXT NULL,
    mobile          TEXT NULL,
    aadhaar_last4   TEXT NULL,
    land_size       TEXT NULL,
    soil_type       TEXT NULL,
    crop_type       TEXT NULL,
    request_type    TEXT NULL, -- scheme_enrollment, certificate, complaint, subsidy
    scheme_name     TEXT NULL,
    description     TEXT NULL,
    priority        TEXT DEFAULT 'normal' CHECK (priority IN ('low','normal','high','urgent')),
    status          TEXT DEFAULT 'pending' CHECK (status IN ('pending','under_review','approved','rejected','forwarded')),
    submitted_at    TIMESTAMPTZ DEFAULT NOW(),
    reviewed_at     TIMESTAMPTZ NULL,
    reviewer_note   TEXT NULL
);

-- 29. admin_stats Table (Cached Dashboard KPI numbers)
CREATE TABLE public.admin_stats (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name     TEXT UNIQUE NOT NULL,
    metric_value    NUMERIC NULL,
    metric_label    TEXT NULL,
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 30. admin_activity_log Table (Audit logs of Grampanchayat portal changes)
CREATE TABLE public.admin_activity_log (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor       TEXT NULL,
    action      TEXT NULL,
    target      TEXT NULL,
    details     TEXT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- PHASE 12: YIELD MODEL TRAINING DATA (Neural Network)
-- =============================================================================

-- 31. farm_data Table (Historical Telemetry variables)
CREATE TABLE public.farm_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    ndvi NUMERIC NULL,
    nitrogen NUMERIC NULL,
    phosphorus NUMERIC NULL,
    potassium NUMERIC NULL,
    moisture NUMERIC NULL,
    ec NUMERIC NULL,
    temperature NUMERIC NULL,
    rainfall NUMERIC NULL,
    humidity NUMERIC NULL,
    crop_type TEXT NULL,
    crop_stage TEXT NULL
);

-- 32. farm_actions Table (Logged inputs to correlate with NDVI yield outcomes)
CREATE TABLE public.farm_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    action_type TEXT CHECK (action_type IN ('irrigate', 'fertilize', 'none')),
    action_value NUMERIC NULL
);

-- =============================================================================
-- PHASE 13: UPDATED_AT TRIGGERS CONFIGURATION
-- =============================================================================
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON public.users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_lands_updated_at BEFORE UPDATE ON public.lands FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_farmer_profiles_updated_at BEFORE UPDATE ON public.farmer_profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_scheme_applications_updated_at BEFORE UPDATE ON public.scheme_applications FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_claim_applications_updated_at BEFORE UPDATE ON public.claim_applications FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_agronomists_updated_at BEFORE UPDATE ON public.agronomists FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_available_schemes_updated_at BEFORE UPDATE ON public.available_schemes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- PHASE 14: INDEXES FOR OPTIMAL RETRIEVAL
-- =============================================================================
CREATE INDEX IF NOT EXISTS idx_farmer_profiles_mobile ON public.farmer_profiles(mobile_number);
CREATE INDEX IF NOT EXISTS idx_farmer_profiles_aadhaar ON public.farmer_profiles(aadhaar_number);
CREATE INDEX IF NOT EXISTS idx_farmer_profiles_state ON public.farmer_profiles(state);
CREATE INDEX IF NOT EXISTS idx_report_logs_user_id ON public.report_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_report_logs_generated ON public.report_logs(generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_scheme_applications_user_id ON public.scheme_applications(user_id);
CREATE INDEX IF NOT EXISTS idx_scheme_applications_status ON public.scheme_applications(status);
CREATE INDEX IF NOT EXISTS idx_claim_applications_user_id ON public.claim_applications(user_id);
CREATE INDEX IF NOT EXISTS idx_claim_applications_status ON public.claim_applications(status);
CREATE INDEX IF NOT EXISTS idx_claim_applications_reference ON public.claim_applications(reference_no);
CREATE INDEX IF NOT EXISTS idx_claim_applications_inspector ON public.claim_applications(assigned_inspector_id);
CREATE INDEX IF NOT EXISTS idx_agronomists_phone ON public.agronomists(phone);
CREATE INDEX IF NOT EXISTS idx_agronomists_available ON public.agronomists(is_available);
CREATE INDEX IF NOT EXISTS idx_available_schemes_state ON public.available_schemes(state);
CREATE INDEX IF NOT EXISTS idx_available_schemes_category ON public.available_schemes(category);
CREATE INDEX IF NOT EXISTS idx_inventory_farmer ON public.inventory(farmer_id);
CREATE INDEX IF NOT EXISTS idx_crop_events_batch ON public.crop_events(batch_id);
CREATE INDEX IF NOT EXISTS idx_grampanchayat_submissions_gp ON public.grampanchayat_submissions(gp_id);

-- =============================================================================
-- PHASE 15: ROW LEVEL SECURITY (RLS) POLICIES
-- =============================================================================
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.lands ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.farmer_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.report_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.available_schemes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scheme_applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.claim_applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.field_officers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.field_officer_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.broadcasts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.agronomists ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.crops ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ndvi_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.land_health_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.autonomous_sensors ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.autonomous_ledger ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.inventory ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.crop_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.marketplace_listings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.grampanchayat_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.grampanchayat_schemes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.grampanchayat_submissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.admin_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.admin_activity_log ENABLE ROW LEVEL SECURITY;

-- Creating permissive Policies for ease of development/demo (Adjust in production)
CREATE POLICY "Public Users Access" ON public.users FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Public Sessions Access" ON public.sessions FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Public Lands Access" ON public.lands FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Public Profiles Access" ON public.farmer_profiles FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Public Report Logs Access" ON public.report_logs FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Public Available Schemes Access" ON public.available_schemes FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Public Scheme Applications Access" ON public.scheme_applications FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Public Claim Applications Access" ON public.claim_applications FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Public Field Officers Access" ON public.field_officers FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Public Assignments Access" ON public.field_officer_assignments FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Public Broadcasts Access" ON public.broadcasts FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Public Agronomists Access" ON public.agronomists FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Public Crops Access" ON public.crops FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Public NDVI Access" ON public.ndvi_records FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Public Health Logs Access" ON public.land_health_logs FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Public Sensors Access" ON public.autonomous_sensors FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Public Sensors Ledger Access" ON public.autonomous_ledger FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Public Inventory Access" ON public.inventory FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Public Crop Events Access" ON public.crop_events FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Public Listings Access" ON public.marketplace_listings FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Public GP Users Access" ON public.grampanchayat_users FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Public GP Schemes Access" ON public.grampanchayat_schemes FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Public GP Submissions Access" ON public.grampanchayat_submissions FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Public Admin Stats Access" ON public.admin_stats FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Public Admin Activity Access" ON public.admin_activity_log FOR ALL USING (true) WITH CHECK (true);

-- Permissions Grants
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO anon, authenticated, service_role;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated, service_role;

-- =============================================================================
-- PHASE 16: SEED DATA (Realistic Mock Data)
-- =============================================================================

-- 1. Core Users (Admin user)
-- admin@letgo.com / password: admin123
INSERT INTO public.users (email, password_hash, full_name, role, is_active)
VALUES (
    'admin@letgo.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIvAprzZ3.',
    'Admin User',
    'admin',
    true
) ON CONFLICT (email) DO NOTHING;

-- 2. Agronomists
INSERT INTO public.agronomists (name, phone, specialization, experience_years, is_available, rating) VALUES
('Dr. Megh Bari', '+919021935820', 'Crop Disease Management', 15, TRUE, 4.8),
('Dr. Dhruv Save', '+919579649407', 'Pest Control & IPM', 12, TRUE, 4.7),
('Dr. Samarth Bhirud', '+919021935821', 'Soil Health & Fertilization', 10, TRUE, 4.9),
('Dr. Neelay Joshi', '+919579649408', 'Organic Farming', 8, TRUE, 4.6)
ON CONFLICT (phone) DO NOTHING;

-- 3. Field Officers (Inspectors)
INSERT INTO public.field_officers (officer_id, name, zone, email, phone)
VALUES 
    ('officer-001', 'Amit Verma', 'Zone A', 'amit@example.com', '9876543210'),
    ('officer-002', 'Priya Sharma', 'Zone B', 'priya@example.com', '9876543211'),
    ('officer-003', 'Rohit Singh', 'Zone C', 'rohit@example.com', '9876543212')
ON CONFLICT (officer_id) DO NOTHING;

-- 4. Available Schemes Directory (Central & MH State)
INSERT INTO public.available_schemes (scheme_name, description, subsidy_percentage, max_amount, eligibility, applicable_equipment, source, state, category)
VALUES
(
    'PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)',
    'Direct income support of ₹6,000 per year for all landholding farmers across India.',
    0,
    6000,
    '["Must be a landholding farmer", "Indian citizen", "Non-income tax payer"]'::jsonb,
    '[]'::jsonb,
    'Ministry of Agriculture & Farmers Welfare',
    NULL,
    'Income Support'
),
(
    'PM-KUSUM Solar Pump (Component B)',
    'Subsidy of up to 60% for installation of standalone solar water pumps in off-grid areas.',
    60,
    200000,
    '["Individual farmers", "Water User Associations", "FPOs"]'::jsonb,
    '["Solar Pump", "Solar Panels", "Submersible Motor"]'::jsonb,
    'Ministry of New and Renewable Energy',
    NULL,
    'Solar Energy'
),
(
    'PMFBY (Pradhan Mantri Fasal Bima Yojana)',
    'Comprehensive crop insurance scheme providing financial protection against crop loss due to natural calamities.',
    98,
    0,
    '["All farmers including tenants", "Must be growing notified crops"]'::jsonb,
    '[]'::jsonb,
    'GoI Ministry of Agriculture',
    NULL,
    'Insurance'
),
(
    'MahaDBT Tractor Subsidy (Above 20HP)',
    'Financial assistance for purchasing tractors to improve farm efficiency.',
    50,
    125000,
    '["MH Farmer", "SC/ST/Small/Marginal"]'::jsonb,
    '["Tractor"]'::jsonb,
    'Maharashtra Dept of Agriculture',
    'Maharashtra',
    'Mechanization'
),
(
    'Dr. Babasaheb Ambedkar Agricultural Self-Reliance Scheme',
    'Package for SC/Nav-Bouddha farmers for new wells, well repair, and irrigation tools.',
    100,
    285000,
    '["SC category", "Annual income < 1.5 Lakhs"]'::jsonb,
    '["New Well", "Electric Motor", "PVC Pipe", "Farm Pond Lining"]'::jsonb,
    'MS Govt - Agriculture Dept',
    'Maharashtra',
    'Social Welfare'
),
(
    'Magel Tyala Shet Tale (Farm Pond On-Demand)',
    'Subsidy for farm pond construction to store rainwater for irrigation.',
    75,
    75000,
    '["All farmers", "Min 0.40 ha land"]'::jsonb,
    '["Excavation", "Lining"]'::jsonb,
    'MH State - Water Resources',
    'Maharashtra',
    'Irrigation'
);

-- 5. Grampanchayat Users
INSERT INTO public.grampanchayat_users (id, gp_name, district, taluka, state, sarpanch_name, phone, email) VALUES
  ('11111111-0000-0000-0000-000000000001', 'Dahanu Gram Panchayat',    'Palghar',   'Dahanu',     'Maharashtra', 'Leelabai Kokate',    '9881234504', 'dahanu.gp@maha.gov.in'),
  ('11111111-0000-0000-0000-000000000002', 'Vasai Virar GP',           'Palghar',   'Vasai',      'Maharashtra', 'Kashinath Mhatre',   '9881234506', 'vasai.gp@maha.gov.in'),
  ('11111111-0000-0000-0000-000000000003', 'Palghar Rural GP',         'Palghar',   'Palghar',    'Maharashtra', 'Suresh Patil',       '9881234507', 'palghar.gp@maha.gov.in'),
  ('11111111-0000-0000-0000-000000000004', 'Pingli Gram Panchayat',    'Pune',      'Purandar',   'Maharashtra', 'Ramesh Bhosale',     '9881234501', 'pingli.gp@maha.gov.in'),
  ('11111111-0000-0000-0000-000000000005', 'Vadgaon Gram Panchayat',   'Nashik',    'Niphad',     'Maharashtra', 'Sunitabai Patil',    '9881234502', 'vadgaon.gp@maha.gov.in')
ON CONFLICT (id) DO NOTHING;

-- 6. Grampanchayat Schemes
INSERT INTO public.grampanchayat_schemes (gp_id, scheme_name, ministry, budget_allotted, budget_used, beneficiaries, status, deadline, description) VALUES
('11111111-0000-0000-0000-000000000001', 'Palghar Coastal Horticulture',   'State Horticulture',        4500000, 2800000, 142, 'active',    '2025-12-31', 'Subsidy on Chikoo, Coconut, and Mango farming tools for coastal region.'),
('11111111-0000-0000-0000-000000000001', 'PM Kisan Samman Nidhi',          'Ministry of Agriculture',   1200000,  980000,  82, 'active',    '2025-03-31', 'Direct income support ₹6000/year to small & marginal farmers.'),
('11111111-0000-0000-0000-000000000001', 'Drip Irrigation Subsidy (PMKSY)','Jal Shakti Ministry',       880000,  880000,  41, 'completed', '2024-12-31', 'Subsidy on micro-irrigation systems, drip & sprinkler.'),
('11111111-0000-0000-0000-000000000002', 'Greenhouse Subsidy Yojana',      'Ministry of Agriculture',   3500000, 1290000,  45, 'active',    '2026-03-31', 'Support for floriculture and greenhouse banana farming.'),
('11111111-0000-0000-0000-000000000002', 'e-NAM (Online Agri Market)',     'Ministry of Agriculture',    350000,  170000,  38, 'active',    '2025-09-30', 'Online trading platform for agricultural commodities.'),
('11111111-0000-0000-0000-000000000002', 'Kisan Credit Card',              'Ministry of Finance',       3200000, 2100000,  74, 'active',    '2025-12-31', 'Short-term credit for agriculture up to ₹3 lakh at 4%.'),
('11111111-0000-0000-0000-000000000003', 'PMFBY Crop Insurance',           'Ministry of Finance',       1900000,  900000,  44, 'active',    '2025-12-31', 'Coverage against crop loss due to natural calamities.'),
('11111111-0000-0000-0000-000000000003', 'Paramparagat Krishi Vikas Yojana','Ministry of Agriculture',   620000,  410000,  28, 'active',    '2025-08-31', 'Organic farming promotion and certification support.');

-- 7. Grampanchayat Submissions
INSERT INTO public.grampanchayat_submissions 
  (gp_id, farmer_name, village, mobile, aadhaar_last4, land_size, soil_type, crop_type, request_type, scheme_name, description, priority, status, submitted_at)
VALUES
('11111111-0000-0000-0000-000000000001', 'Tukaram Bari',        'Bordi',       '9765008001', '8821', '4.5 Acres', 'Coastal Alluvial','Chikoo, Coconut',   'scheme_enrollment', 'Palghar Coastal Horticulture','Need subsidy for new Chikoo saplings after storm damage.',              'urgent', 'pending',     NOW() - INTERVAL '1 day'),
('11111111-0000-0000-0000-000000000001', 'Sunita Machhi',       'Gholvad',     '9765008002', '4492', '1.8 Acres', 'Alluvial',        'Vegetables',        'subsidy',           'Drip Irrigation Subsidy',     'Apply for drip irrigation. Water scarce in summer.',                     'high',   'under_review', NOW() - INTERVAL '5 days'),
('11111111-0000-0000-0000-000000000002', 'Anandi Vartak',       'Arnala',      '9765008004', '5567', '2.0 Acres', 'Alluvial',        'Banana, Vegetables','scheme_enrollment','Greenhouse Subsidy Yojana',        'Building polyhouse for export quality banana.',                          'high',   'under_review',     NOW() - INTERVAL '4 days');

-- 8. Admin Stats
INSERT INTO public.admin_stats (metric_name, metric_value, metric_label) VALUES
  ('total_farmers',           14284, 'Registered Farmers'),
  ('active_gp_portals',          42, 'Active GPs'),
  ('total_scheme_beneficiaries', 4843,'Scheme Beneficiaries'),
  ('reports_generated',         840, 'Soil Reports Generated'),
  ('pending_submissions',        21, 'Pending Farmer Requests'),
  ('total_budget_disbursed',  84000000,'Budget Disbursed (₹)'),
  ('soil_tests_done',          1203, 'Soil Tests Completed'),
  ('schemes_active',            18,  'Active Schemes')
ON CONFLICT (metric_name) DO UPDATE SET
  metric_value = EXCLUDED.metric_value,
  metric_label = EXCLUDED.metric_label,
  updated_at   = NOW();

-- 9. Seed Farmer Profiles
INSERT INTO public.farmer_profiles 
  (user_id, name, land_size, district, village, state, crops, identity_verified, farm_geo_verified, reputation_rating)
VALUES
  ('FARM-PLG-001', 'Tukaram Bari',      4.5,  'Palghar', 'Bordi', 'Maharashtra', 'Chikoo, Coconut', true, true, 4.8),
  ('FARM-PLG-002', 'Anandi Vartak',     2.0,  'Palghar', 'Arnala', 'Maharashtra', 'Banana, Vegetables', true, false, 4.2),
  ('FARM-PLG-003', 'Navnath Save',      5.2,  'Palghar', 'Kelve', 'Maharashtra', 'Paddy, Betelnut', false, false, 4.0),
  ('FARM-PLG-004', 'Samir Koli',        1.5,  'Palghar', 'Nalasopara', 'Maharashtra', 'Onion, Garlic', true, true, 4.9)
ON CONFLICT (user_id) DO NOTHING;

-- 10. Seed Report Logs
INSERT INTO public.report_logs (user_id, farmer_name, language, soil_type, farm_size, sensor_snapshot, generated_at) VALUES
  ('FARM-PLG-001', 'Tukaram Bari',      'mr', 'Coastal Alluvial', '4.5',
   '{"ph":7.1,"nitrogen":220,"phosphorus":24,"potassium":110,"conductivity":480,"soil_moisture":45,"soil_temperature":28}',
   NOW() - INTERVAL '1 days'),
  ('FARM-PLG-002', 'Anandi Vartak',     'mr', 'Alluvial',         '2.0',
   '{"ph":6.8,"nitrogen":280,"phosphorus":32,"potassium":140,"conductivity":380,"soil_moisture":55,"soil_temperature":24}',
   NOW() - INTERVAL '2 days');

-- =============================================================================
-- SCHEMAS RESET COMPLETE!
-- =============================================================================
