import os

from flask import Flask, flash, g, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename

from . import db, auth, student

def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    basedir = os.path.abspath(os.path.dirname(__file__))

    app.config.from_mapping(
        # a default secret that should be overridden by instance config
        SECRET_KEY="dev",
        # store the database in the instance folder
        DATABASE=os.path.join(app.instance_path, "biodata.sqlite"),
        # UPLOAD_FOLDER="/biodata/static/uploads/",
        UPLOAD_FOLDER = os.path.join(basedir, 'static/uploads'),
        ALLOWED_EXTENSIONS = set(["png", "jpg", "jpeg"])
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.update(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.route("/hello")
    def hello():
        return "Hello, World!"

    # register the database commands
    db.init_app(app)

    # apply the blueprints to the app
    app.register_blueprint(auth.bp)
    app.register_blueprint(student.bp)

    # make url_for('index') == url_for('blog.index')
    # in another app, you might define a separate main index here with
    # app.route, while giving the blog blueprint a url_prefix, but for
    # the tutorial the blog will be the main index
    # app.add_url_rule("/", endpoint="index")

    @app.route("/")
    def index():
        """Show all the posts, most recent first."""
        
        return  "Hello, World at homepage!"

    
    # UPLOAD_FOLDER = "./static/uploads/"
    # ALLOWED_EXTENSIONS = set(["png", "jpg", "jpeg"])
    # app.config['UPLOAD_FOLDER'] = "./static/uploads/"

    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

    @app.route('/uploads', methods=['GET', 'POST'])
    @auth.login_required
    def upload_file():
        if request.method == 'POST':
            # check if the post request has the file part
            if 'file' not in request.files:
                flash('No file part')
                return redirect(request.url)
            file = request.files['file']
            # If the user does not select a file, the browser submits an
            # empty file without a filename.
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                # file.save(filename)
                return redirect(url_for('download_file', name=filename))
        return '''
            <!doctype html>
            <title>Upload new File</title>
            <h1>Upload new File</h1>
            <form method=post enctype=multipart/form-data>
            <input type=file name=file>
            <input type=submit value=Upload>
            </form>
            '''

    from flask import send_from_directory

    @app.route('/uploads/<name>')
    def download_file(name):
        return send_from_directory(app.config["UPLOAD_FOLDER"], name)

    app.add_url_rule(
        "/uploads/<name>", endpoint="download_file", build_only=True
    )

    # app.add_url_rule(
    #     "/uploads/<user_id>/<name>", endpoint="download_file", build_only=True
    # )

    return app