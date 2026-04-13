from flask import Flask, render_template, request, redirect, session, flash
from flask_session import Session

#password security library
from werkzeug.security import check_password_hash, generate_password_hash

import sqlite3
from datetime import datetime
from helpers import login_required

# Configure application
app = Flask(__name__)
# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Jinja filter: format SQLite timestamps for templates
def datetime_format(value):
    """Format a timestamp string from the database for display in templates."""
    if not value:
        return ""
    s = str(value)
    # try common SQLite timestamp formats
    fmts = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"]
    for fmt in fmts:
        try:
            dt = datetime.strptime(s, fmt)
            return dt.strftime('%b %d, %Y %I:%M %p')
        except ValueError:
            continue
    # fallback: return original value
    return s

# register filter with Jinja
app.jinja_env.filters['datetime_format'] = datetime_format

#Database helper function
    #RLY IMPORTANT ADD MORE EXPLAINATION
def get_db():
    """Connect to the database"""
    conn = sqlite3.connect('mentorship.db')
    conn.row_factory = sqlite3.Row
    return conn

#I HAVE NO IDEA WHAT THIS DOES SO LOOK BAD ON IT
@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Similiar to CS50 Finance
# EVERYTHING ABOVE THIS IS THE SET UP IN FINANCE

#How to access the homepage
@app.route("/")
def index():
    """Landing page with two columns"""
    return render_template("index.html")

#HERE IS VERY SIMILIAR TO CS50 FINANCE - login and regrister. So I won't explain it too much
@app.route("/register_hs", methods=["GET", "POST"])
def register_hs():
    """Register high school student"""
    if request.method == "POST":
        email = request.form.get("email")
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        
        # Validate input
        if not email or not username or not password or not confirmation:
            flash("All fields are required", "danger")
            return render_template("register_hs.html")
        
        # Little function I saw that ensures the email is valid. It is the same for the college with harvard. I really just don't want to use java lol
        if not email.endswith("@philasd.org"):
            flash("Must use a @philasd.org email address", "danger")
            return render_template("register_hs.html")
        
        # Check passwords match
        if password != confirmation:
            flash("Passwords do not match", "danger")
            return render_template("register_hs.html")
        
        # Hash password
        password_hash = generate_password_hash(password)
        
        # Insert into database
        try:
            db = get_db()
            db.execute(
                "INSERT INTO users (email, password_hash, user_type, username) VALUES (?, ?, ?, ?)",
                (email, password_hash, "highschool", username)
            )
            db.commit()
            db.close()
            
            flash("Registration successful! Please login.", "success")
            return redirect("/login?type=highschool")
            
        except sqlite3.IntegrityError: 
            flash("Email already registered", "danger")
            return render_template("register_hs.html")
    
    return render_template("register_hs.html")

# Register for college is a lot more complicated because of the profile: there are SOOO many forms the users has to fill out for demographics
@app.route("/register_college", methods=["GET", "POST"])
def register_college():
    """
    Register college student with full profile
    
    EXPLANATION: This processes the new registration form with:
    - .edu email validation (any college, not just Harvard)
    - Athletic interests (NEW)
    - High school instead of hometown (CHANGED)
    - Multiple gender selections with custom option (CHANGED)
    - HBCU and IB flags (NEW)
    - Removed is_international (REMOVED)
    """
    if request.method == "POST":
        # Get basic authentication info
        email = request.form.get("email")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        
        # Get required profile info
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        university = request.form.get("university")
        high_school = request.form.get("high_school")  # CHANGED: was "hometown"
        
        # Get multiple choice fields (checkboxes return lists)
        help_areas = request.form.getlist("help_areas")
        academic_interests = request.form.getlist("academic_interests")
        athletic_interests = request.form.getlist("athletic_interests")  # NEW
        race = request.form.getlist("race")
        gender = request.form.getlist("gender")  # CHANGED: now a list (multiple selections)
        
        # Get custom gender text if they selected "Other"
        # EXPLANATION: This field is only filled if user checks "Other" and types something
        gender_custom = request.form.get("gender_custom")
        
        # Get single choice field
        religion = request.form.get("religion")
        
        # Get boolean fields (checkboxes)
        # EXPLANATION: Convert checkbox to 1 (checked) or 0 (unchecked)
        # If "Prefer not to say" selected, we'll handle that separately
        hbcu = 1 if request.form.get("hbcu") else 0  # NEW
        ib = 1 if request.form.get("ib") else 0  # NEW
        is_athlete = 1 if request.form.get("is_athlete") else 0
        university_outside_us = 1 if request.form.get("university_outside_us") else 0  # ADD THIS
        is_lgbtq = 1 if request.form.get("is_lgbtq") else 0
        # Removed: is_international (no longer needed for Philadelphia alumni)
        
        # Validate required fields
        if not email or not password or not confirmation or not first_name or not last_name or not university:
            flash("Required fields: email, password, first name, last name, university", "danger")
            return render_template("register_college.html")
        
        # Check email domain - CHANGED to accept any .edu
        # EXPLANATION: endswith(".edu") accepts upenn.edu, temple.edu, drexel.edu, etc.
        # More flexible than hardcoding @college.harvard.edu
        if not email.endswith(".edu"):
            flash("Must use a .edu email address", "danger")
            return render_template("register_college.html")
        
        # Check passwords match
        if password != confirmation:
            flash("Passwords do not match", "danger")
            return render_template("register_college.html")
        
        # Hash password for security
        password_hash = generate_password_hash(password)
        
        # Convert lists to comma-separated strings for database storage
        # EXPLANATION: Database stores TEXT, not arrays
        # ["Essay", "Financial Aid"] becomes "Essay,Financial Aid"
        help_areas_str = ",".join(help_areas) if help_areas else None
        academic_interests_str = ",".join(academic_interests) if academic_interests else None
        athletic_interests_str = ",".join(athletic_interests) if athletic_interests else None  # NEW
        
        # Handle race - if "Prefer not to say" is selected, store None
        # EXPLANATION: We don't want to show race on profile if they prefer not to say
        if "Prefer not to say" in race:
            race_str = None
        else:
            race_str = ",".join(race) if race else None
        
        # Handle gender - if "Prefer not to say" is selected, store None
        # EXPLANATION: Similar to race - respect privacy preferences
        if "Prefer not to say" in gender:
            gender_str = None
            gender_custom = None
        else:
            gender_str = ",".join(gender) if gender else None
        
        # If religion is empty string (default dropdown), set to None
        # EXPLANATION: Empty string vs None distinction matters for database
        if not religion:
            religion = None
        
        # Insert into database (two tables!)
        try:
            db = get_db()
            
            # Step 1: Insert user account
            cursor = db.execute(
                "INSERT INTO users (email, password_hash, user_type) VALUES (?, ?, ?)",
                (email, password_hash, "college")
            )
            
            # Step 2: Get the auto-generated user ID
            user_id = cursor.lastrowid
            
            # Step 3: Insert profile with NEW schema
            db.execute('''
                INSERT INTO college_profiles 
                (user_id, first_name, last_name, university, high_school, help_areas, 
                academic_interests, athletic_interests, gender, gender_custom, race, 
                hbcu, ib, university_outside_us, is_athlete, is_lgbtq, religion)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, first_name, last_name, university, high_school, help_areas_str,
                academic_interests_str, athletic_interests_str, gender_str, gender_custom, race_str,
                hbcu, ib, university_outside_us, is_athlete, is_lgbtq, religion))
            
            db.commit()
            db.close()
            
            flash("Registration successful! Please login.", "success")
            return redirect("/login?type=college")
            
        except sqlite3.IntegrityError:
            flash("Email already registered", "danger")
            return render_template("register_college.html")
    
    # GET request - show the registration form
    return render_template("register_college.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""
    # Clear any existing session
    session.clear()
    
    # Get user type from URL parameter
    user_type = request.args.get("type", "highschool")
    
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        # Validate input
        if not email or not password:
            flash("Must provide email and password", "danger")
            return render_template("login.html", user_type=user_type)
        
        # Query database for user
        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()
        db.close()
        
        # Check if user exists and password is correct
        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Invalid email and/or password", "danger")
            return render_template("login.html", user_type=user_type)
        
        # Check if user type matches
        if user["user_type"] != user_type:
            flash(f"This email is registered as a {user['user_type']} student", "danger")
            return render_template("login.html", user_type=user_type)
        
        # Remember which user has logged in
        session["user_id"] = user["id"]
        session["user_type"] = user["user_type"]
        
        # Redirect to home page
        if user_type == "highschool":
            return redirect("/hs_home")
        else:
            return redirect("/college_home")
    
    return render_template("login.html", user_type=user_type)


@app.route("/logout")
def logout():
    """Log user out"""
    session.clear()
    flash("You have been logged out", "info")
    return redirect("/")

@app.route("/hs_home")
@login_required
def hs_home():
    """High school student home page with dashboard"""
    #Verify the logged-in user is actually a high school student
    #This prevents college students from accessing HS pages: since the login page is the same for both
    if session.get("user_type") != "highschool":
        return redirect("/")
    
    # Connect to database
    db = get_db()
    
    # Get the high school student's username
    # session["user_id"] contains the ID we stored when they logged in
    user = db.execute(
        "SELECT username FROM users WHERE id = ?", 
        (session["user_id"],)
    ).fetchone()
    
    # Get upcoming meetings
    # This SQL query does several things:
    # 1st Looks in the meetings table for meetings that haven't happened then 
    # 2nd JOINs to find people IN the meetings
    # 3rd Filters to only THIS student's meetings (from_user_id = their ID)
    # 4th Only shows meetings that are in the future (ehhh) AND not completed
    upcoming_meetings = db.execute('''
        SELECT meetings.meeting_date, 
               college_profiles.first_name || ' ' || college_profiles.last_name as mentor_name,
               requests.meet_link
        FROM meetings
        JOIN requests ON meetings.request_id = requests.id
        JOIN college_profiles ON requests.to_user_id = college_profiles.user_id
        WHERE requests.from_user_id = ?
        AND meetings.is_completed = 0
        AND meetings.meeting_date >= datetime('now')
        ORDER BY meetings.meeting_date ASC
    ''', (session["user_id"],)).fetchall()
    
    # EXPLANATION: || is the SQL concatenation operator
    # It combines strings together. So first_name || ' ' || last_name
    # turns "John" and "Doe" into "John Doe"
    # This is like doing f"{first_name} {last_name}" in Python
    
    # Get pending requests (requests that haven't been accepted or rejected yet)
    # We JOIN with college_profiles to get the mentor's name
    pending_requests = db.execute('''
        SELECT requests.id, requests.created_at,
               college_profiles.first_name || ' ' || college_profiles.last_name as mentor_name
        FROM requests
        JOIN college_profiles ON requests.to_user_id = college_profiles.user_id
        WHERE requests.from_user_id = ?
        AND requests.status = 'pending'
        ORDER BY requests.created_at DESC
    ''', (session["user_id"],)).fetchall()
    
    db.close()
    
    # Pass all the data to the template
    # The template can now use: username, upcoming_meetings, pending_requests
    return render_template("hs_home.html", 
                         username=user["username"],
                         upcoming_meetings=upcoming_meetings,
                         pending_requests=pending_requests)

@app.route("/hs_browse")
@login_required
def hs_browse():
    """Browse all college mentors with filtering"""
    if session.get("user_type") != "highschool":
        return redirect("/")
    
    db = get_db()
    
    # EXPLANATION OF request.args:
    # request.args contains URL parameters (the stuff after ? in URLs)
    # For example: /hs_browse?search=John&gender=Woman
    # request.args.get("search") would return "John"
    # request.args.get("gender") would return "Woman"
    # This is how we get filter data from the form
    
    # Get filter parameters from URL
    search_name = request.args.get("search", "")  # Default to empty string
    help_filter = request.args.get("help_area", "")
    interest_filter = request.args.get("interest", "")
    gender_filter = request.args.get("gender", "")
    athletic_filter = request.args.get("athletic", "")  # CHANGED: athletic instead of race

    # Start building the SQL query
    # We'll add WHERE conditions based on what filters are active
    query = '''
        SELECT college_profiles.*, users.email
        FROM college_profiles
        JOIN users ON college_profiles.user_id = users.id
        WHERE users.user_type = 'college'
    '''
    
    #DYNAMIC SQL QUERIES:
    #We're building the SQL query as we go, adding filters only if needed
    # making use of something called query += " AND condition" to add more conditions
    # params is a list that will hold our filter values
    params = []
    
    # Add search filter if name was provided
    # LIKE is a SQL operator for pattern matching
    # % is a wildcard that matches any characters
    # So '%John%' matches "John", "Johnny", "John Smith", etc.
    if search_name: # IF there is a name in search bar
        query += " AND (college_profiles.first_name LIKE ? OR college_profiles.last_name LIKE ?)"
        # We add % around the search term for partial matching
        params.extend([f"%{search_name}%", f"%{search_name}%"])
    
    # EXPLANATION OF LIKE operator:
    # In SQL, LIKE is used for pattern matching with wildcards
    # % means "match any number of characters"
    # Examples:
    #   'John%' matches anything starting with John
    #   '%Smith' matches anything ending with Smith
    #   '%son%' matches anything containing son
    
    # Add help area filter
    if help_filter:
        query += " AND college_profiles.help_areas LIKE ?"
        params.append(f"%{help_filter}%")
    
    # Add academic interest filter
    if interest_filter:
        query += " AND college_profiles.academic_interests LIKE ?"
        params.append(f"%{interest_filter}%")
    
    # Add gender filter (exact match, not LIKE)
    if gender_filter:
        query += " AND college_profiles.gender = ?"
        params.append(gender_filter)
    
    # Add race filter
    if athletic_filter:
        query += " AND college_profiles.athletic_interests LIKE ?"
        params.append(f"%{athletic_filter}%")
    
    # Execute the query with all the parameters
    # The ? placeholders get replaced with values from params list
    # This is called "parameterized queries" and prevents SQL injection
    mentors = db.execute(query, params).fetchall()
    
    # EXPLANATION OF SQL INJECTION PREVENTION:
    # We use ? placeholders instead of f-strings to prevent SQL injection
    # BAD:  f"SELECT * FROM users WHERE name = '{user_input}'"
    #       A hacker could input: Robert'); DROP TABLE users; --
    # GOOD: execute("SELECT * FROM users WHERE name = ?", (user_input,))
    #       The database safely handles the input
    
    db.close()
    
    # Pass mentors and current filter values to template
    # We pass the filter values back so the form can show what's selected
    return render_template("hs_browse.html", 
                         mentors=mentors,
                         search_name=search_name,
                         help_filter=help_filter,
                         interest_filter=interest_filter,
                         gender_filter=gender_filter,
                         athletic_filter=athletic_filter)

# When a student clicks "Send Request", they go to a page to write their message.
@app.route("/hs_request/<int:mentor_id>", methods=["GET", "POST"])
@login_required
def hs_request(mentor_id):
    """Send a request to a specific mentor"""
    if session.get("user_type") != "highschool":
        return redirect("/")
    
    # EXPLANATION OF <int:mentor_id>:
    # This is called a "dynamic route" or "URL parameter"
    # <int:mentor_id> captures a number from the URL
    # Example: /hs_request/5 sets mentor_id = 5
    # The 'int:' part ensures it's a number (converts string to int)
    # Flask automatically puts this into  the function
    
    db = get_db()
    
    # Get the mentor's information to display on the page
    mentor = db.execute('''
        SELECT college_profiles.*, users.email
        FROM college_profiles
        JOIN users ON college_profiles.user_id = users.id
        WHERE college_profiles.user_id = ?
    ''', (mentor_id,)).fetchone()
    
    # If mentor doesn't exist, show error
    if not mentor:
        flash("Mentor not found", "danger")
        db.close()
        return redirect("/hs_browse")
    
    # If form was submitted (POST request)
    if request.method == "POST":
               #Check if student already has a pending request to this mentor
               #^THERE is a FUNCTION at the bottom of this doc
        # EXPLANATION: This prevents spam - students can't send multiple requests
        # to the same mentor until the first one is resolved
        existing_request = db.execute('''
            SELECT id FROM requests 
            WHERE from_user_id = ? 
            AND to_user_id = ? 
            AND status = 'pending'
        ''', (session["user_id"], mentor_id)).fetchone()
        
        #If there is an existing request, a flash message will appear and redirect you
        #The existing request returns a true or false boolean
        if existing_request:
            flash(f"You already have a pending request to {mentor['first_name']} {mentor['last_name']}", "warning")
            db.close()
            return redirect("/hs_browse")
        
        message = request.form.get("message")
        meet_link = request.form.get("meet_link")
        availability = request.form.get("availability")  # ADD THIS
        
        # Validate that all fields were filled out
        # EXPLANATION: Now checking availability too
        if not message or not meet_link or not availability:
            flash("Please provide message, meeting link, and availability", "danger")
            db.close()
            return render_template("hs_request.html", mentor=mentor)
        
        # EXPLANATION OF URL VALIDATION:
        #We check if meet_link starts with http:// or https://
        #^this is the best thing we could do to ensure it's a valid link
        #Without this, someone could enter "google" which isn't a link
        if not meet_link.startswith(('http://', 'https://')):
            flash("Please provide a valid meeting link (must start with http:// or https://)", "danger")
            db.close()
            return render_template("hs_request.html", mentor=mentor)
        
        #Insert the request into the database
        #from_user_id = the high school student (logged in user)
        #to_user_id = the college mentor they're requesting
        #status defaults to 'pending'
        db.execute('''
            INSERT INTO requests (from_user_id, to_user_id, message, meet_link, availability)
            VALUES (?, ?, ?, ?, ?)
        ''', (session["user_id"], mentor_id, message, meet_link, availability))
        
        db.commit()
        db.close()
        
        flash(f"Request sent to {mentor['first_name']} {mentor['last_name']}!", "success")
        return redirect("/hs_home")
    
    #If GET request, just show the form
    db.close()
    return render_template("hs_request.html", mentor=mentor)


@app.route("/hs_past_meetings")
@login_required
def hs_past_meetings():
    """View past meetings for high school student"""
    if session.get("user_type") != "highschool":
        return redirect("/")
    
    db = get_db()
    
    # Get meetings that have either:
    # 1. Been marked as completed
    # 2. OR their date has passed
    past_meetings = db.execute('''
        SELECT meetings.meeting_date,
               college_profiles.first_name || ' ' || college_profiles.last_name as mentor_name,
               requests.message
        FROM meetings
        JOIN requests ON meetings.request_id = requests.id
        JOIN college_profiles ON requests.to_user_id = college_profiles.user_id
        WHERE requests.from_user_id = ?
        AND (meetings.is_completed = 1 OR meetings.meeting_date < datetime('now'))
        ORDER BY meetings.meeting_date DESC
    ''', (session["user_id"],)).fetchall()
    
    db.close()
    
    return render_template("hs_past_meetings.html", meetings=past_meetings)



@app.route("/college_home")
@login_required
def college_home():
    """College student home page with recent activity"""
    # Check that the logged-in user is a college student
    # session.get() retrieves data we stored when they logged in
    if session.get("user_type") != "college":
        return redirect("/")
    
    # Connect to our database
    db = get_db()
    
    # Get the college student's profile information
    # We use a JOIN to combine data from users and college_profiles tables
    # This is like saying: "Give me the profile for THIS specific user"
    profile = db.execute(
        "SELECT first_name FROM college_profiles WHERE user_id = ?", 
        (session["user_id"],)  # session["user_id"] is the logged-in user's ID
    ).fetchone()
    
    # Get recent requests (from the last 24 hours)
    # datetime('now', '-1 day') means "24 hours ago"
    # We JOIN with users table to get the high school student's username
    # We also JOIN with college_profiles to make sure requests are for THIS tutor
    recent_requests = db.execute('''
        SELECT requests.id, requests.message, requests.created_at, requests.availability,
            users.username as from_username
        FROM requests
        JOIN users ON requests.from_user_id = users.id
        WHERE requests.to_user_id = ?
        AND requests.status = 'pending'
        AND requests.created_at >= datetime('now', '-1 day')
        ORDER BY requests.created_at DESC
    ''', (session["user_id"],)).fetchall()
    
    # Get upcoming meetings (meetings that haven't happened yet)
    # We need to JOIN multiple tables:
    # - meetings table (has meeting dates)
    # - requests table (connects meetings to people)
    # - users table (to get the high school student's name)
    upcoming_meetings = db.execute('''
        SELECT meetings.meeting_date, users.username as student_name,
               requests.meet_link
        FROM meetings
        JOIN requests ON meetings.request_id = requests.id
        JOIN users ON requests.from_user_id = users.id
        WHERE requests.to_user_id = ?
        AND meetings.is_completed = 0
        AND meetings.meeting_date >= datetime('now')
        ORDER BY meetings.meeting_date ASC
        LIMIT 5
    ''', (session["user_id"],)).fetchall()
    
    db.close()
    
    # Pass all this data to the template so it can display it
    # The template will use these variables: first_name, recent_requests, upcoming_meetings
    return render_template("college_home.html", 
                         first_name=profile["first_name"],
                         recent_requests=recent_requests,
                         upcoming_meetings=upcoming_meetings)

@app.route("/college_requests")
@login_required
def college_requests():
    """View all pending requests for college student"""
    # Make sure only college students can access this page
    if session.get("user_type") != "college":
        return redirect("/")
    
    db = get_db()
    
    # Get ALL pending requests (not just last 24 hours)
    # SELECT: Choose which columns to get
    # FROM: Which table to get data from
    # JOIN: Combine data from multiple tables
    # WHERE: Filter to only get requests for THIS tutor that are still pending
    # ORDER BY: Show newest requests first (DESC = descending order)
    requests_list = db.execute('''
        SELECT requests.id, requests.message, requests.meet_link, requests.availability,
            requests.created_at, users.username as from_username
        FROM requests
        JOIN users ON requests.from_user_id = users.id
        WHERE requests.to_user_id = ?
        AND requests.status = 'pending'
        ORDER BY requests.created_at DESC
    ''', (session["user_id"],)).fetchall()
    
    db.close()
    
    # Pass the list of requests to the template
    return render_template("college_requests.html", requests=requests_list)

@app.route("/accept_request/<int:request_id>", methods=["POST"])
@login_required
def accept_request(request_id):
    """Accept a request and create a meeting"""
    # Make sure user is a college student
    if session.get("user_type") != "college":
        return redirect("/")
    
    # Get the meeting date from the form
    # request.form.get() retrieves data from HTML forms
    meeting_date = request.form.get("meeting_date")
    
    # Validate that they provided a date
    if not meeting_date:
        flash("Please provide a meeting date", "danger")
        return redirect("/college_requests")
    
    db = get_db()
    
    # First, verify this request is actually for THIS tutor
    # This prevents someone from accepting someone else's requests
    req = db.execute(
        "SELECT * FROM requests WHERE id = ? AND to_user_id = ?",
        (request_id, session["user_id"])
    ).fetchone()
    
    # If request doesn't exist or isn't for this user
    if not req:
        flash("Request not found", "danger")
        db.close()
        return redirect("/college_requests")
    
    # Update the request status to 'accepted'
    # UPDATE: Modify existing data in a table
    # SET: Which columns to change
    # WHERE: Which row to update
    db.execute(
        "UPDATE requests SET status = 'accepted' WHERE id = ?",
        (request_id,)
    )
    
    # Create a new meeting in the meetings table
    # INSERT INTO: Add a new row to a table
    db.execute(
        "INSERT INTO meetings (request_id, meeting_date, is_completed) VALUES (?, ?, ?)",
        (request_id, meeting_date, 0)  # 0 means not completed yet
    )
    
    # Commit = save all changes to database
    # Without commit(), changes are lost!
    db.commit()
    db.close()
    
    # Show success message
    flash("Request accepted! Meeting scheduled.", "success")
    return redirect("/college_requests")


@app.route("/reject_request/<int:request_id>", methods=["POST"])
@login_required
def reject_request(request_id):
    """Reject a request"""
    # Make sure user is a college student
    if session.get("user_type") != "college":
        return redirect("/")
    
    db = get_db()
    
    # Verify this request belongs to this tutor
    req = db.execute(
        "SELECT * FROM requests WHERE id = ? AND to_user_id = ?",
        (request_id, session["user_id"])
    ).fetchone()
    
    if not req:
        flash("Request not found", "danger")
        db.close()
        return redirect("/college_requests")
    
    # Update status to 'rejected'
    db.execute(
        "UPDATE requests SET status = 'rejected' WHERE id = ?",
        (request_id,)
    )
    
    db.commit()
    db.close()
    
    flash("Request rejected", "info")
    return redirect("/college_requests")

@app.route("/college_meetings")
@login_required
def college_meetings():
    """View all upcoming meetings for college student"""
    if session.get("user_type") != "college":
        return redirect("/")
    
    db = get_db()
    
    # Get ALL future meetings (not just next 5), this makes it different from the home page
    # We JOIN multiple the to get all relevant info
    # meeting_date >= datetime('now') = it's in the future (lowkey this part doesn't work as well so I just made a request button)
    meetings = db.execute('''
        SELECT meetings.id, meetings.meeting_date, meetings.request_id,
               users.username as student_name, requests.meet_link, requests.message
        FROM meetings
        JOIN requests ON meetings.request_id = requests.id
        JOIN users ON requests.from_user_id = users.id
        WHERE requests.to_user_id = ?
        AND meetings.is_completed = 0
        AND meetings.meeting_date >= datetime('now')
        ORDER BY meetings.meeting_date ASC
    ''', (session["user_id"],)).fetchall()
    
    db.close()
    
    return render_template("college_meetings.html", meetings=meetings)

@app.route("/complete_meeting/<int:meeting_id>", methods=["POST"])
@login_required
def complete_meeting(meeting_id):
    """Mark a meeting as completed"""
    if session.get("user_type") != "college":
        return redirect("/")
    
    # EXPLANATION: Connect to database
    db = get_db()
    
    # Verify this meeting belongs to this tutor
    # EXPLANATION: We JOIN tables to check ownership
    # This prevents users from marking OTHER people's meetings as complete
    meeting = db.execute('''
        SELECT meetings.* FROM meetings
        JOIN requests ON meetings.request_id = requests.id
        WHERE meetings.id = ?
        AND requests.to_user_id = ?
    ''', (meeting_id, session["user_id"])).fetchone()
    
    # If meeting doesn't exist or doesn't belong to this user
    if not meeting:
        flash("Meeting not found", "danger")
        db.close()
        return redirect("/college_meetings")
    
    # Mark as completed
    # EXPLANATION: UPDATE changes existing data
    # SET is_completed = 1 means mark it as done
    # WHERE ensures we only update this specific meeting
    db.execute(
        "UPDATE meetings SET is_completed = 1 WHERE id = ?",
        (meeting_id,)
    )
    
    db.commit()
    db.close()
    
    flash("Meeting marked as complete!", "success")
    return redirect("/college_meetings")

@app.route("/college_past_meetings")
@login_required
def college_past_meetings():
    """View past meetings for college student"""
    if session.get("user_type") != "college":
        return redirect("/")
    
    db = get_db()
    
    #Goal of the SQL query to get meeting with these criteria
    #1. marked as completed (is_completed = 1)
    #2. OR their date has passed (meeting_date < now) (IDK why but something is off about this)
    #DESC = descending order (most recent first)
    past_meetings = db.execute('''
        SELECT meetings.meeting_date, users.username as student_name,
                requests.message
        FROM meetings
        JOIN requests ON meetings.request_id = requests.id
        JOIN users ON requests.from_user_id = users.id
        WHERE requests.to_user_id = ?
        AND (
            meetings.is_completed = 1 
            OR meetings.meeting_date < datetime('now', 'localtime')
        )
        ORDER BY meetings.meeting_date DESC
    ''', (session["user_id"],)).fetchall()
    
    db.close()
    
    return render_template("college_past_meetings.html", meetings=past_meetings)


@app.route("/hs_view_profile/<int:mentor_id>")
@login_required
def hs_view_profile(mentor_id):
    """View detailed mentor profile"""
    if session.get("user_type") != "highschool":
        return redirect("/")
    
    db = get_db()
    
    # Get full mentor profile with all information
    mentor = db.execute('''
        SELECT college_profiles.*, users.email
        FROM college_profiles
        JOIN users ON college_profiles.user_id = users.id
        WHERE college_profiles.user_id = ?
    ''', (mentor_id,)).fetchone()
    
    if not mentor:
        flash("Mentor not found", "danger")
        db.close()
        return redirect("/hs_browse")
    
    #Check if student already has a pending request to this mentor
    #This will disable the request button if they already requested; this prevent SPAMMMM
    has_pending_request = db.execute('''
        SELECT id FROM requests 
        WHERE from_user_id = ? 
        AND to_user_id = ? 
        AND status = 'pending'
    ''', (session["user_id"], mentor_id)).fetchone()
    
    db.close()
    
    # EXPLANATION OF bool():
    # Converts value to True/False
    # If has_pending_request is None (no request), bool(None) = False
    # If has_pending_request has data, bool(data) = True
    return render_template("hs_view_profile.html", 
                         mentor=mentor,
                         has_pending=bool(has_pending_request))


# EXPLANATION OF ERROR HANDLERS:
# Flask can catch errors and show custom pages
# @app.errorhandler() is a decorator that catches specific HTTP errors
# 404 = "Not Found" error (page doesn't exist)
@app.errorhandler(404)
def page_not_found(e):
    """Custom 404 error page"""
    # e is the error object, we don't use it but Flask requires the parameter
    return render_template("404.html"), 404
    # The ", 404" tells Flask to return HTTP status code 404
    # Without it, Flask would return 200 (success) which is misleading

if __name__ == '__main__':
    # EXPLANATION: In production, we want different settings
    # debug=False for security (don't show error details to users)
    # host='0.0.0.0' allows external connections (not just localhost)
    # port from environment variable (Render sets this automatically)
    import os
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=False, host='0.0.0.0', port=port)
