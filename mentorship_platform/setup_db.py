# EXPLANATION: This creates the database with updated schema for Philadelphia School District
# Changes from previous version:
# - Added athletic_interests field
# - Added hbcu and ib boolean fields
# - Removed is_international field
# - Updated to support custom gender input
# Run this to create fresh database: python3 setup_db.py

import sqlite3

# Connect to database (creates mentorship.db if it doesn't exist)
# EXPLANATION: If you deleted the old .db file, this creates a brand new one
conn = sqlite3.connect('mentorship.db')
cursor = conn.cursor()

# ============================================================
# Table 1: users
# ============================================================
# EXPLANATION: Main authentication table - unchanged from before
# Stores login credentials for both high school and college students
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    user_type TEXT NOT NULL CHECK(user_type IN ('highschool', 'college')),
    username TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# ============================================================
# Table 2: college_profiles
# ============================================================
# EXPLANATION: Extended profile for college students
# CHANGES FROM PREVIOUS VERSION:
# - hometown → high_school (text field)
# - academic_interests (expanded list)
# - athletic_interests (NEW field)
# - gender (now supports custom input)
# - Added hbcu (boolean)
# - Added ib (boolean) 
# - Removed is_international
cursor.execute('''
CREATE TABLE IF NOT EXISTS college_profiles (
    user_id INTEGER PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    university TEXT NOT NULL,
    high_school TEXT,
    help_areas TEXT,
    availability TEXT,
    academic_interests TEXT,
    athletic_interests TEXT,
    gender TEXT,
    gender_custom TEXT,
    race TEXT,
    hbcu INTEGER,
    ib INTEGER,
    university_outside_us INTEGER,
    is_athlete INTEGER,
    is_lgbtq INTEGER,
    religion TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
''')
# EXPLANATION of new/changed fields:
# - high_school: Which Philadelphia high school they attended (replaces hometown)
# - athletic_interests: Comma-separated list of sports/activities
# - gender_custom: Custom gender text if they select "Another gender identity"
# - hbcu: 1 if attended HBCU, 0 if not (NULL if prefer not to say)
# - ib: 1 if did IB program, 0 if not (NULL if prefer not to say)
# - Removed is_international (not relevant for Philadelphia alumni)

# ============================================================
# Table 3: requests
# ============================================================
# EXPLANATION: Unchanged - stores mentorship requests
cursor.execute('''
CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_user_id INTEGER NOT NULL,
    to_user_id INTEGER NOT NULL,
    message TEXT NOT NULL,
    meet_link TEXT NOT NULL,
    availability TEXT,
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'accepted', 'rejected')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (from_user_id) REFERENCES users(id),
    FOREIGN KEY (to_user_id) REFERENCES users(id)
)
''')

# ============================================================
# Table 4: meetings
# ============================================================
# EXPLANATION: Unchanged - stores scheduled meetings
cursor.execute('''
CREATE TABLE IF NOT EXISTS meetings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id INTEGER NOT NULL,
    meeting_date TIMESTAMP,
    is_completed INTEGER DEFAULT 0,
    FOREIGN KEY (request_id) REFERENCES requests(id)
)
''')

# Save all changes
conn.commit()
conn.close()

print("✅ Database created successfully with updated schema!")
print("📊 New fields added: high_school, athletic_interests, hbcu, ib")
print("🗑️  Removed fields: is_international, hometown")