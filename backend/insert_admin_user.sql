-- Manual SQL script to create an admin user
-- Run this in Supabase SQL Editor if the Python script doesn't work

-- This creates an admin user with:
-- Email: admin@letgo.com
-- Password: admin123
-- The password hash is pre-computed using bcrypt

INSERT INTO users (email, password_hash, full_name, role, is_active)
VALUES (
    'admin@letgo.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIvAprzZ3.',  -- Password: admin123
    'Admin User',
    'admin',
    true
)
ON CONFLICT (email) DO NOTHING;

-- Verify the user was created
SELECT id, email, full_name, role, created_at 
FROM users 
WHERE email = 'admin@letgo.com';

-- If you want to create a different admin user, use this template:
-- You'll need to hash the password using bcrypt first
-- Or use the Python script: python backend/create_admin.py
