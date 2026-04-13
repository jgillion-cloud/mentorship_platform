from flask import redirect, session
from functools import wraps

#forces login in order to access the app
#VERY SIMILIAR TO CS50 FINANCE
def login_required(f):
    """
    Decorate routes to require login.
    From CS50 Finance problem set.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function