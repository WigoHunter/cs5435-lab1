from bottle import (
    get,
    post,
    redirect,
    request,
    response,
    jinja2_template as template,
)

from app.util.hash import (hash_sha256, hash_pbkdf2)
from app.models.breaches import get_breaches
from app.models.user import create_user, get_user
from app.models.session import (
    delete_session,
    create_session,
    get_session_by_username,
    logged_in,
)

def plaintext_breached(breaches, password):
    for breach in breaches:
        if (password == breach.password):
            return True
    return False

def hashed_breached(breaches, password):
    for breach in breaches:
        if (hash_sha256(password) == breach.hashed_password):
            return True
    return False

def salted_breached(breaches, password):
    for breach in breaches:
        if (hash_pbkdf2(password, breach.salt) == breach.salted_password):
            return True
    return False

@get('/login')
def login():
    return template('login')

@post('/login')
def do_login(db):
    username = request.forms.get('username')
    password = request.forms.get('password')
    error = None
    user = get_user(db, username)
    print(user)
    if (request.forms.get("login")):
        if user is None:
            response.status = 401
            error = "{} is not registered.".format(username)
        elif user.salted_password != hash_pbkdf2(password, user.salt):
            response.status = 401
            error = "Wrong password for {}.".format(username)
        else:
            pass  # Successful login
    elif (request.forms.get("register")):
        if user is not None:
            response.status = 401
            error = "{} is already taken.".format(username)
        else:
            breaches = get_breaches(db, username)
            if (plaintext_breached(breaches[0], password)
                or hashed_breached(breaches[1], password)
                or salted_breached(breaches[2], password)):
                response.status = 401
                error = "Password is already breached!"
            else:
                create_user(db, username, password)
    else:
        response.status = 400
        error = "Submission error." 
    if error is None:  # Perform login
        existing_session = get_session_by_username(db, username)
        if existing_session is not None:
            delete_session(db, existing_session)
        session = create_session(db, username)
        response.set_cookie("session", str(session.get_id()))
        return redirect("/{}".format(username))

    return template("login", error=error)

@post('/logout')
@logged_in
def do_logout(db, session):
    delete_session(db, session)
    response.delete_cookie("session")
    return redirect("/login")


