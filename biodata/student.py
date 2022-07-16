import os
from flask import Blueprint, flash, g, redirect, render_template, request, send_from_directory, url_for
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

@bp.route("/dashboard", methods=("GET", "POST"))
@login_required
def dashboard():
    """View controller for the dashboard view for the current user."""

    return render_template("student/dashboard.html")


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
        # is_rep = request.form["is_rep"]    

        error = None
        # if not names:
        #     error = "Names is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "INSERT INTO students (user_id, reg_num, first_name, middle_name, last_name, dept, faculty, level, dob, phone,  passport_url) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (g.user["id"], reg_num, first_name, middle_name, last_name, dept, faculty, level, dob, phone, passport_url),
            )
            db.commit()
            return redirect(url_for('student.dashboard'))
    return render_template("student/biodata.html")


@bp.route("/coursemates", methods=("GET", "POST"))
@login_required
def coursemates():
    """View controller for the coursemates view for the current user."""

    return render_template("student/coursemates.html")