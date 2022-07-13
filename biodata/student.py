
import os
from flask import Blueprint, flash, g, redirect, render_template, request, send_from_directory, url_for
from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename


from .auth import login_required
from .db import get_db
# from . import app

basedir = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(basedir, 'static/uploads')
ALLOWED_EXTENSIONS = set(["png", "jpg", "jpeg"])

bp = Blueprint("student", __name__, url_prefix="/student")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route("/upload", methods=("GET", "POST"))
@login_required
def upload_biodata():
    """Create a new record for the user in the student table for the current user."""
    if request.method == "POST":
        # handle file save to directory
        # check if the post request has the file part
        if 'passport' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['passport']
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
        # passport_url = +filename

        # handle form data
        names = request.form["names"]        
        error = None
        if not names:
            error = "Names is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "INSERT INTO uploads (user_id, names, passport_url) VALUES (?, ?, ?)",
                (g.user["id"], names, passport_url),
            )
            db.commit()
            # return redirect(url_for("index"))
            return redirect(url_for('download_file', name=filename))

    return render_template("student/upload.html")