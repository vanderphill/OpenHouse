import os
import requests
import urllib.parse
import datetime
from flask import redirect, render_template, request, session
from functools import wraps




def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def datetimenow():
    now = datetime.datetime.now()
    offset = datetime.timedelta(hours=6)
    t = now-offset
    datetim = str(datetime.date.today())+ " " +str(t.hour)+ ":" +str(t.minute)+ ":" + str(t.second)
    return datetim

