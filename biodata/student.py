import functools
import os
from flask import Blueprint, flash, g, redirect, render_template, request, send_from_directory, session, url_for
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename


from .auth import login_required
from .db import get_db

basedir = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(basedir, 'static/uploads')
ALLOWED_EXTENSIONS = set(["png", "jpg", "jpeg"])

bp = Blueprint("student", __name__, url_prefix="/student")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def is_rep(view):
    """View decorator that checks if the logged in person is a class rep."""

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        # test if user has filled biodata
        db = get_db()
        user = db.execute(
            "SELECT is_rep FROM students WHERE user_id = ?", (session['user_id'],)
        ).fetchone()

        if user is None:
            error = "Error..."
            flash(error)
            return redirect(url_for("index"))

        if user['is_rep'] == 1:
            session['is_rep'] = True
        elif user['is_rep'] == 0:
            session['is_rep'] = False
            error = "You are not a class rep..."
            flash(error)
            return redirect(url_for("index"))
        
        return view(**kwargs)

    return wrapped_view


@bp.route("/dashboard", methods=("GET", "POST"))
@login_required
def dashboard():
    """View controller for the dashboard view for the current user."""
    if request.method == 'GET' and session:
        # test if user has filled biodata
        db = get_db()
        user = db.execute(
            "SELECT * FROM students WHERE user_id = ?", (session['user_id'],)
        ).fetchone()

        if user is None:
            error = "You have not filled your biodata yet. Redirected..."
            flash(error)
            return redirect(url_for("student.biodata"))
        
        # create dict to hold db row values 
        data = dict()
        for key in user.keys():
            data[key] = user[key]
        # print(data)

        return render_template("student/dashboard.html", data=data)   # render template with data
    return render_template("student/dashboard.html")                  # render template without data
    

@bp.route("/biodata", methods=("GET", "POST"))
@login_required
def biodata():
    """View controller for the biodata view for the current user."""
    if request.method == "POST":
        # handle file save to directory
        # check if the post request has the file part
        if 'passport_url' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['passport_url']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # filename should really be user_<user_id>_+filename
            filename = "user_" + str(g.user["id"]) + "_" + filename
            file.save(os.path.join(UPLOAD_FOLDER, filename))
        # passport_url should be the url to the passport image
        passport_url = url_for("download_file", name=filename)

        # handle form data
        reg_num = request.form["reg_num"]
        first_name = request.form["first_name"]
        middle_name = request.form["middle_name"]
        last_name = request.form["last_name"]
        dept = request.form["dept"]
        faculty = request.form["faculty"]
        level = request.form["level"]
        dob = request.form["dob"]
        phone = request.form["phone"]
        # checks if the is_rep is checked
        if request.form.get('is_rep'):
            is_rep = 1        # if checked, set is_rep to 1  
        else:
            is_rep = 0        # if not checked, set is_rep to 0 (though default in schema.sql is 0)

        # you may do any type of error checking here, for simplicity, I didn't
        error = None
        
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "INSERT INTO students (user_id, reg_num, first_name, middle_name, last_name, dept, faculty, level, dob, phone, is_rep, passport_url) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (g.user["id"], reg_num, first_name, middle_name, last_name, dept, faculty, level, dob, phone, is_rep, passport_url),
            )
            db.commit()
            return redirect(url_for('student.dashboard'))
    
    if request.method == "GET":
        # test if the user has filled biodata already (if they have, redirect to dashboard)
        # get the dept of logged in user and get all students in that dept
        db = get_db()
        # get the user dept (we want to also test that the user is a rep)
        user = db.execute(
            "SELECT * FROM students WHERE user_id = ?", (session['user_id'],)
        ).fetchone()

        if user:
            # user has filled biodata then redirect to edit biodata view
            return redirect(url_for("student.editbiodata"))
        else:
            # user has not filled biodata yet, render biodata template
            return render_template("student/biodata.html")


@bp.route("/editbiodata", methods=("GET", "POST"))
@login_required
def editbiodata():
    """View controller for the student to edit their biodata."""
    # test if user is logged in 
    if request.method == "GET":
        # get all details of logged in user
        db = get_db()
        user = db.execute(
            "SELECT * FROM students WHERE user_id = ?", (session['user_id'],)
        ).fetchone()

        if user is None:
            error = "You have not filled your biodata yet. Redirected..."
            flash(error)
            return redirect(url_for("student.biodata"))
            
        # create dict to hold db row values 
        data = dict()
        for key in user.keys():
            data[key] = user[key]

        return render_template("student/editbiodata.html", data=data)

    if request.method == "POST":
        # handle form data
        reg_num = request.form["reg_num"]
        first_name = request.form["first_name"]
        middle_name = request.form["middle_name"]
        last_name = request.form["last_name"]
        dept = request.form["dept"]
        faculty = request.form["faculty"]
        level = request.form["level"]
        dob = request.form["dob"]
        phone = request.form["phone"]
        # checks if the is_rep is checked
        if request.form.get('is_rep'):
            is_rep = 1        # if checked, set is_rep to 1  
        else:
            is_rep = 0        # if not checked, set is_rep to 0 (though default in schema.sql is 0)
        # handle file image
        file = request.files['passport_url']


        # handle file save to directory
        # check if the post request has the file part
        if file.filename == '':
            # user did not update their passport, so just update the biodata
            db = get_db()
            db.execute(
                "UPDATE students SET reg_num=?, first_name=?, middle_name=?, last_name=?, dept=?, faculty=?, level=?, dob=?, phone=?, is_rep=? WHERE user_id=?",
                (reg_num, first_name, middle_name, last_name, dept, faculty, level, dob, phone, is_rep, g.user["id"]),
            )
            db.commit()
            return redirect(url_for('student.dashboard'))

        # if user updated their passport, handle file save to directory
        else:
            # only treat since the file is not empty and the user wants to update their passport
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # filename should really be user_<user_id>_+filename
                filename = "user_" + str(g.user["id"]) + "_" + filename
                file.save(os.path.join(UPLOAD_FOLDER, filename))
            # passport_url should be the url to the passport image
            passport_url = url_for("download_file", name=filename)

            # you may do any type of error checking here, for simplicity, I didn't
            error = None
            
            if error is not None:
                flash(error)
            else:
                db = get_db()
                db.execute(
                    "UPDATE students SET reg_num=?, first_name=?, middle_name=?, last_name=?, dept=?, faculty=?, level=?, dob=?, phone=?, is_rep=?, passport_url=? WHERE user_id=?",
                    (reg_num, first_name, middle_name, last_name, dept, faculty, level, dob, phone, is_rep, passport_url, g.user["id"]),
                )
                db.commit()
                return redirect(url_for('student.dashboard'))


# for class reps only viewing the students biodata
@bp.route("/coursemates", methods=("GET", "POST"))
@is_rep
@login_required
def coursemates():
    """View controller for the coursemates view for the current user."""
    # test if user is logged in and session exists
    if request.method == "GET":
        # get the dept of logged in user and get all students in that dept
        db = get_db()
        rep_dept = db.execute(
            "SELECT dept FROM students WHERE user_id = ?", (session['user_id'],)
        ).fetchone()

        if rep_dept is None:
            error = "You have not filled your biodata yet. Redirected..."
            flash(error)
            return redirect(url_for("student.biodata"))

        # now select from the db all students in the same dept
        coursemates = db.execute(
            "SELECT first_name, middle_name, last_name, reg_num, phone, passport_url, u.email FROM students s JOIN user u ON u.id = s.user_id WHERE dept = ? AND u.email != ?", (rep_dept['dept'], g.user['email'])
        ).fetchall()

        return render_template("student/coursemates.html", data=coursemates)

    return render_template("student/coursemates.html")

