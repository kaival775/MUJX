# FARMER PROFILES - COMPLETE FIELD MAPPING

## 📋 **What You Need to Do**

### **Step 1: Run the Update Script**
```sql
-- File: update_farmer_profiles_for_claims.sql
-- This adds all claim-related fields to your existing farmer_profiles table
-- Safe to run - won't delete any existing data
```

---

## 🗂️ **Complete Field Mapping**

### **✅ EXISTING FIELDS (Kept as-is)**

| Field | Type | Purpose | Used In |
|-------|------|---------|---------|
| `id` | UUID | Primary key | Internal |
| `user_id` | TEXT | Unique identifier | All systems |
| `name` | TEXT | Farmer name | Marketplace |
| `phone` | TEXT | Contact number | Marketplace |
| `state` | TEXT | State location | All systems |
| `district` | TEXT | District location | All systems |
| `land_size` | NUMERIC | Farm size | All systems |
| `crops` | TEXT | Crop types | Marketplace |
| `category` | TEXT | SC/ST/OBC/General | Claims & Schemes |
| `created_at` | TIMESTAMP | Record created | Internal |
| `updated_at` | TIMESTAMP | Last updated | Internal |
| `identity_verified` | BOOLEAN | Verified status | Marketplace |
| `farm_geo_verified` | BOOLEAN | Farm verified | Marketplace |
| `active_seasons_completed` | INTEGER | Seasons | Marketplace |
| `fraud_flags` | INTEGER | Fraud tracking | Marketplace |
| `total_sales` | INTEGER | Total sales | Marketplace |
| `on_time_delivery_pct` | NUMERIC | Delivery % | Marketplace |
| `reputation_rating` | NUMERIC | Rating | Marketplace |

---

### **🆕 NEW FIELDS ADDED (For Claims)**

#### **1. Personal Details**
| Field | Type | Required for Claims | Auto-filled in Claim |
|-------|------|---------------------|---------------------|
| `full_name` | TEXT | ✅ Yes | ✅ Yes |
| `father_husband_name` | TEXT | ✅ Yes | ✅ Yes |
| `date_of_birth` | DATE | ❌ No | ❌ No |
| `gender` | TEXT | ❌ No | ❌ No |

#### **2. Contact Details**
| Field | Type | Required for Claims | Auto-filled in Claim |
|-------|------|---------------------|---------------------|
| `mobile_number` | TEXT | ✅ Yes | ✅ Yes |
| `alternate_mobile` | TEXT | ❌ No | ❌ No |
| `email` | TEXT | ❌ No | ❌ No |

#### **3. Identity Documents**
| Field | Type | Required for Claims | Auto-filled in Claim |
|-------|------|---------------------|---------------------|
| `aadhaar_number` | TEXT | ✅ Yes | ✅ Yes |
| `pan_number` | TEXT | ❌ No | ❌ No |
| `voter_id` | TEXT | ❌ No | ❌ No |

#### **4. Address Details**
| Field | Type | Required for Claims | Auto-filled in Claim |
|-------|------|---------------------|---------------------|
| `address_line1` | TEXT | ❌ No | ❌ No |
| `address_line2` | TEXT | ❌ No | ❌ No |
| `village` | TEXT | ❌ No | ❌ No |
| `pincode` | TEXT | ❌ No | ❌ No |

#### **5. Farm Details**
| Field | Type | Required for Claims | Auto-filled in Claim |
|-------|------|---------------------|---------------------|
| `land_unit` | TEXT | ❌ No | ✅ Yes (from land_size) |
| `survey_number` | TEXT | ❌ No | ❌ No |
| `land_ownership` | TEXT | ❌ No | ❌ No |

#### **6. Bank Details (For Payment)**
| Field | Type | Required for Claims | Auto-filled in Claim |
|-------|------|---------------------|---------------------|
| `bank_name` | TEXT | ⚠️ Recommended | ❌ No |
| `account_number` | TEXT | ⚠️ Recommended | ❌ No |
| `ifsc_code` | TEXT | ⚠️ Recommended | ❌ No |
| `branch_name` | TEXT | ❌ No | ❌ No |

#### **7. NDVI Analysis (KEY FOR CLAIMS)**
| Field | Type | Required for Claims | Auto-calculated |
|-------|------|---------------------|----------------|
| `last_ndvi_value` | DECIMAL(5,3) | ✅ Yes | ✅ Yes |
| `crop_loss_percentage` | DECIMAL(5,2) | ✅ Yes | ✅ Yes |
| `last_ndvi_analysis_date` | TIMESTAMP | ❌ No | ✅ Yes |

#### **8. Document URLs**
| Field | Type | Required for Claims | Uploaded Where |
|-------|------|---------------------|----------------|
| `aadhaar_doc_url` | TEXT | ✅ Yes | Profile form |
| `land_doc_url` | TEXT | ✅ Yes | Profile form |
| `bank_passbook_url` | TEXT | ⚠️ Recommended | Profile form |
| `photo_url` | TEXT | ❌ No | Profile form |

#### **9. Profile Status**
| Field | Type | Purpose |
|-------|------|---------|
| `profile_completed` | BOOLEAN | Check if profile is complete |
| `verified` | BOOLEAN | Admin verification status |

---

## 🔄 **Data Migration**

The update script automatically:

1. ✅ **Copies** `name` → `full_name`
2. ✅ **Copies** `phone` → `mobile_number`
3. ✅ **Sets** `profile_completed` based on existing data
4. ✅ **Keeps** all existing fields intact
5. ✅ **Adds** new indexes for performance

---

## 📊 **Profile Completion Requirements**

### **Minimum for Claims:**
```sql
-- Required fields to apply for a claim:
- full_name ✅
- father_husband_name ✅
- mobile_number ✅
- aadhaar_number ✅
- state ✅
- land_size ✅
- last_ndvi_value ✅ (auto-calculated)
- crop_loss_percentage ✅ (auto-calculated)
```

### **Recommended for Claims:**
```sql
-- Recommended fields for faster claim processing:
- bank_name ⚠️
- account_number ⚠️
- ifsc_code ⚠️
- aadhaar_doc_url ⚠️
- land_doc_url ⚠️
```

---

## 🔍 **Example Profile After Update**

### **Before Update:**
```json
{
  "id": "uuid",
  "user_id": "farmer123",
  "name": "Ramesh Kumar",
  "phone": "9876543210",
  "state": "Maharashtra",
  "district": "Nagpur",
  "land_size": 5.5,
  "crops": "Wheat, Cotton",
  "category": "OBC",
  "reputation_rating": 4.8
}
```

### **After Update:**
```json
{
  // OLD FIELDS (Kept)
  "id": "uuid",
  "user_id": "farmer123",
  "name": "Ramesh Kumar",
  "phone": "9876543210",
  "state": "Maharashtra",
  "district": "Nagpur",
  "land_size": 5.5,
  "crops": "Wheat, Cotton",
  "category": "OBC",
  "reputation_rating": 4.8,
  
  // NEW FIELDS (Added)
  "full_name": "Ramesh Kumar",              // Copied from name
  "father_husband_name": "Suresh Kumar",    // To be filled by farmer
  "mobile_number": "9876543210",            // Copied from phone
  "aadhaar_number": "123456789012",         // To be filled by farmer
  "bank_name": "State Bank of India",       // To be filled by farmer
  "account_number": "1234567890",           // To be filled by farmer
  "ifsc_code": "SBIN0001234",               // To be filled by farmer
  "last_ndvi_value": 0.450,                 // Auto-calculated from satellite
  "crop_loss_percentage": 35.50,            // Auto-calculated from NDVI
  "last_ndvi_analysis_date": "2026-02-08",  // Auto-set
  "aadhaar_doc_url": "https://...",         // Uploaded by farmer
  "land_doc_url": "https://...",            // Uploaded by farmer
  "profile_completed": true,                // Auto-set
  "verified": false                         // Set by admin
}
```

---

## 🎯 **User Flow**

### **1. Farmer Completes Profile** (`/profile`)
```
Navigate to Profile Page
↓
Fill Required Fields:
✓ Full Name (auto-filled from existing name)
✓ Father/Husband Name (NEW - farmer enters)
✓ Mobile (auto-filled from existing phone)
✓ Aadhaar Number (NEW - farmer enters)
✓ Bank Details (NEW - farmer enters)
↓
Upload Documents:
✓ Aadhaar Card scan
✓ Land ownership document
✓ Bank passbook copy
↓
System Auto-Calculates:
✓ NDVI Value
✓ Crop Loss Percentage
↓
Profile Status: ✅ Complete
```

### **2. Farmer Applies for Claim** (`/apply-claim`)
```
Profile Check: ✅ Complete
↓
Auto-fill from Profile:
✓ Name: Ramesh Kumar
✓ Father: Suresh Kumar
✓ Mobile: 9876543210
✓ Aadhaar: 123456789012
✓ Land Size: 5.5 acres
✓ NDVI Loss: 35.50%
↓
Farmer Enters:
✓ Crop Name: Wheat
✓ Upload crop damage photos
↓
Auto-Calculate Claim Amount: ₹75,000
↓
Submit → Get Reference: CLM-2026-12345
```

### **3. Admin Reviews Claim** (`/admin/claims`)
```
See All Farmer Data:
✓ Full Name: Ramesh Kumar
✓ Father: Suresh Kumar
✓ Aadhaar: 123456789012
✓ Mobile: 9876543210
✓ Land: 5.5 acres
✓ NDVI Loss: 35.50%
✓ Claim: ₹75,000
✓ Documents: Aadhaar, Land docs, Crop photos
✓ Bank: SBI, Acc: 1234567890, IFSC: SBIN0001234
↓
Review → Approve → Payment
```

---

## ✅ **Action Required**

1. **Run SQL Script**:
   ```sql
   -- In Supabase SQL Editor:
   -- Run: update_farmer_profiles_for_claims.sql
   ```

2. **Verify Updates**:
   ```sql
   SELECT column_name, data_type 
   FROM information_schema.columns
   WHERE table_name = 'farmer_profiles'
   ORDER BY column_name;
   ```

3. **Test Profile Form**:
   - Navigate to `/profile`
   - Complete all required fields
   - Upload documents
   - Check `profile_completed` = true

4. **Test Claim Application**:
   - Navigate to `/apply-claim`
   - Verify auto-filled data
   - Submit claim
   - Check in `/admin/claims`

---

## 🚀 **Everything is Ready!**

Your `farmer_profiles` table will now support:
- ✅ Complete farmer profiles
- ✅ NDVI crop loss analysis
- ✅ Government claim applications
- ✅ Document management
- ✅ Bank details for payments
- ✅ All existing marketplace features (unchanged)
