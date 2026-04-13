Ok so because bulletpoints don't work here: Claude made us a beatiful little template. Un

mentorship_platform/
├── app.py                      # Main Flask application with all routes
├── helpers.py                  # Helper functions (login_required decorator)
├── setup_db.py                 # Database initialization script
├── mentorship.db               # SQLite database
├── requirements.txt            # Python dependencies
├── static/
│   └── styles.css             # Custom CSS styling
└── templates/
    ├── layout.html            # Base template
    ├── index.html             # Landing page
    ├── register_hs.html       # High school registration
    ├── register_college.html  # College registration with profile
    ├── login.html             # Login page
    ├── hs_home.html           # High school dashboard
    ├── hs_browse.html         # Browse mentors page
    ├── hs_view_profile.html   # View mentor profile
    ├── hs_request.html        # Send request page
    ├── hs_past_meetings.html  # Past meetings page
    ├── college_home.html      # College dashboard
    ├── college_requests.html  # Manage requests page
    ├── college_meetings.html  # Upcoming meetings page
    ├── college_past_meetings.html  # Past meetings page
    └── 404.html               

DATABASES:
Setup.db.py created all my databases. I have learned that making a python file and instructing it to do a one time creation is the norm amoung web developers. 
It’s REALLY important to know this because all of the features HEAVILY rely on SQL. THis is a SQL heavy project.

Here’s a copy of all the tables:
### users - 
`id`: Primary key - 
`email`: Unique email address - 
`password_hash`: Hashed password - 
`user_type`: 'highschool' or 'college' -
`username`: Display name (high school students only) - 
`created_at`: Timestamp 


college profiles is a seperate things from the users database because college students really need this for profiles; high school student only have the high school usernames which is chill. 
###college_profiles - 
`user_id`: Foreign key to users - 
`first_name`, `last_name`: Name - `
university`: College name -
`hometown`: Optional hometown - 
`help_areas`: Comma-separated list of expertise - 
`academic_interests`: Comma-separated list - 
`gender`, `race`, `religion`: Optional demographics - 
`is_international`, `is_athlete`, `is_lgbtq`: Boolean flags 


### requests - 
`id`: Primary key - 
`from_user_id`: Foreign key to users (high school student) - 
`to_user_id`: Foreign key to users (college student) -
 `message`: Request message -
 `meet_link`: Google Meet link - 
`status`: 'pending', 'accepted', or 'rejected' - 
`created_at`: Timestamp ### meetings - 
`id`: Primary key - 
`request_id`: Foreign key to requests- 
`meeting_date`: Scheduled date/time - 
`is_completed`: Boolean


Helpers.py:
Take a lot of inspiration from CS50's finance pset, becuase I believe that's the norm for coders 

.HTML pages:
Because I plan to actually implement my project in my own highschool by January 2026, and it is pretty ambitious project to do without partners, a lot of the HTML pages are using a lot of AI because it’s a lot of design focus things and involves a lot of intricacies that we haven’t learned in CS5. But generally for my AI prompts and for my small little tweaks to the HTML page outside of AI, I was looking for a clean design that is very appealing to students where students can clearly see a button and they can click on it. That’s why all the buttons are really bright and blue and in your face. And also I want a clean, respectable sort of platform so that it could be seen as professional to high school administration and to teachers and staff. The design also incorporates lotta blue because a lot of people love the color blue and hey, I made a disagree with them but it’s a cool color.

I will mainly talk about app.py because that is where most of the critical thinking and my orginality came into play. 
Everything under here is app.py:

BROWSER:
The browser filter is really interesting because it operates like a dynamic sequel command where we’re adding on different layers as the sequel carries the code progresses. This is really cool. It goes outside the scope of the course of it but if you use “query +=” you can dynamically add on to the query. 
This is how we filter and filter and filter out the profiles overtime so for example, the first query is 
SELECT college_profiles.*, user.email
FROM college_profiles
JOIN users ON college_profile.user_id = user.id
WHERE users.user_type = ‘college’
This query makes us look specifically at college profiles. Now that we’ve got that down, we can then look at the search filter which adds another query using a the “like” feature in the first name AND in the last name.
query += " AND (college_profiles.first_name LIKE ? OR college_profiles.last_name LIKE ?)"
As you can see here, use the query += to make the logic dynamic. And this process continues. We add another query to get a help filter and then we have another query to get an interest filter and they have another query for gender, race, etc.
This is how the browser filter operates.


REQUESTS:
For the request, we verify the meeting link by just verifying that it’s a link so we only look at the beginning to make sure it begins with HTTPS or HTTP which isn’t the most efficient way but it’s the one that’s the most familiar to us CS50. For this, we also use this different function in Python called start (insert_name)startswith(). I realize this function too late and when I realize this, this is so much better.
The request is also a whole new page with a bunch of different forms 
Also, this is need explaining but the college student rec receiving the request is going to be their college student because they match up with their user ID so it’s very simple and it’s like as if someone was sending a text message one time but the updates will happen on the like request ID and that is how it becomes really dynamic in a way
TO PREVENT SPAM: There is an existing request pending boolean function at the bottom of app.py that returns true if there is an existing request and false if there is not. This function is used within to the request function for the highschoolers above. 


SQL HEAVY FUNCTIONS:
Imma keep it real everything in “college student end” is all sql queries that you can highkey just use AI to generate once you give them the lists of tables. 
For college students “request page” and “upcoming meetings” in the home page and for the “college request page” also use a lot of sequel curries. They’re pretty simple but for both the high school and for the college level they use queries. Sometimes we join different tables to get all the information we want. For example in the past meeting page we join past meetings table with the users table to get the high schoolers username who request a specific meeting and the meeting’s date.
This is also true for high school students in the pending requests and upcoming meeting (filtering with meeting have the status of pending and upcoming), and their “past meeting” as well. All of these functions really all come from the same sort of style of doing one or two SQL clauses so that’s why I grouped them in and don’t explain them as much because it’s pretty intuitive.
For college students to recently see who viewed them within the past day for the recent request page. We just use the sequels automatic date time and then we just say now minus a day so it’s really simple. One of the tfs talked about sql automatic timer
With the SQL clause, I also have to do something new that I haven’t learned in CS 50 called fetchall that basically gives me all the results of the SQL clauses: using select isn’t enough of itself because I actually need to return the results of my prompt and that’s what that fetchall does and you can see it use a lot of my code. Sometimes I also use fetchone and fetchone basically gives me one value and not all the possible values.

LOGIN & REGISTER:
For highschool students this is very similar to CS 50s finance pieces in terms of design so it doesn’t require too much explanation. That’s very little difference. For college students, it’s a bit more complex story. This is because they need to fill out their profile, so on the HTML file for the college student registration page there are a lot of forms for all the demographic information. The results of this demographic information gets placed into the SQL table. 
The Harvard email verification for college students and the Philadelphian email verification for high school students are used in the exact same way that we used for verification and CS5 finance.
The login page is really interesting because the login page is the same login page for both high school students and for college students, but depending on what button you click at first for the login it writes you to your accurate homepage so if I’m a college student and a college student first it would route me to the college student homepage when I click login. This is an ingenious design because the login pages if they would be made separately would be really similar if not almost identical that is why we just make it all one login page. However, there is one caveat: if a college student decides to login but presses the high school button we don’t want college to do an accessing the high school page that wouldn’t make any sense. That’s why before you render all of the templates for high school we ensure that the user that’s logging in is actually a high school student by checking their user ID and using a sequel command. This is also applied to vice versa for the college students. 
To summarize, this is a genius level coding that I have done and I feel really smart. Nicole give me my flowers. 


