from flask import Flask, render_template, request, redirect, session
import mysql.connector
import os

app = Flask(__name__)
app.secret_key = "secret123"

# =========================
# DATABASE CONNECTION
# =========================
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="ott_db"
)
cursor = db.cursor(dictionary=True)

# =========================
# UPLOAD PATHS
# =========================
UPLOAD_IMAGE = "static/images"
UPLOAD_VIDEO = "static/videos"

os.makedirs(UPLOAD_IMAGE, exist_ok=True)
os.makedirs(UPLOAD_VIDEO, exist_ok=True)

# =========================
# LANDING PAGE
# =========================
@app.route("/")
def landing():
    if "user" in session:
        return redirect("/home")
    return render_template("landing.html")

# =========================
# HOME PAGE
# =========================
@app.route("/home")
def home():
    if "user" not in session:
        return render_template("login_required.html")

    cursor.execute("SELECT * FROM movies ORDER BY id ASC")
    movies = cursor.fetchall()

    return render_template("index.html", movies=movies, user=session["user"])

# =========================
# WATCH PAGE
# =========================
@app.route("/watch/<video>")
def watch(video):
    if "user" not in session:
        return render_template("login_required.html")

    return render_template("watch.html", video=video)

# =========================
# LOGIN
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"].strip()

        cursor.execute(
            "SELECT * FROM users WHERE email=%s AND password=%s",
            (email, password)
        )
        user = cursor.fetchone()

        if user:
            session["user"] = user["first_name"]
            return redirect("/home")
        else:
            error = "Invalid email or password"

    return render_template("login.html", error=error)

# =========================
# SIGNUP
# =========================
@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = None
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip()
        password = request.form["password"].strip()

        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            error = "Email already exists"
            return render_template("signup.html", error=error)

        cursor.execute(
            "INSERT INTO users (first_name, email, password) VALUES (%s,%s,%s)",
            (name, email, password)
        )
        db.commit()

        return redirect("/login")

    return render_template("signup.html", error=error)

# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# =========================
# ADMIN LOGIN
# =========================
@app.route("/admin", methods=["GET", "POST"])
def admin():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":
            session["admin"] = True
            return redirect("/dashboard")
        else:
            error = "Invalid credentials"

    return render_template("admin_login.html", error=error)

# =========================
# DASHBOARD
# =========================
@app.route("/dashboard")
def dashboard():
    if "admin" not in session:
        return redirect("/admin")

    cursor.execute("SELECT * FROM movies ORDER BY id ASC")
    movies = cursor.fetchall()

    return render_template("dashboard.html", movies=movies)

# =========================
# ADD MOVIE (with description)
# =========================
@app.route("/add", methods=["POST"])
def add_movie():
    if "admin" not in session:
        return redirect("/admin")

    title = request.form["title"]
    description = request.form.get("description", "").strip()
    image = request.files["image"]
    video = request.files["video"]

    image_path = os.path.join(UPLOAD_IMAGE, image.filename)
    video_path = os.path.join(UPLOAD_VIDEO, video.filename)

    image.save(image_path)
    video.save(video_path)

    cursor.execute(
        "INSERT INTO movies (title, image, video, description) VALUES (%s,%s,%s,%s)",
        (title, "images/" + image.filename, "videos/" + video.filename, description)
    )
    db.commit()

    return redirect("/dashboard")

# =========================
# EDIT MOVIE (NEW)
# =========================
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_movie(id):
    if "admin" not in session:
        return redirect("/admin")

    if request.method == "POST":
        title = request.form["title"]
        description = request.form.get("description", "").strip()
        image_file = request.files.get("image")
        video_file = request.files.get("video")

        cursor.execute("SELECT image, video FROM movies WHERE id=%s", (id,))
        current = cursor.fetchone()
        if not current:
            return redirect("/dashboard")

        image_db = current["image"]
        video_db = current["video"]

        if image_file and image_file.filename:
            image_path = os.path.join(UPLOAD_IMAGE, image_file.filename)
            image_file.save(image_path)
            image_db = "images/" + image_file.filename

        if video_file and video_file.filename:
            video_path = os.path.join(UPLOAD_VIDEO, video_file.filename)
            video_file.save(video_path)
            video_db = "videos/" + video_file.filename

        cursor.execute(
            "UPDATE movies SET title=%s, image=%s, video=%s, description=%s WHERE id=%s",
            (title, image_db, video_db, description, id)
        )
        db.commit()
        return redirect("/dashboard")

    # GET request - show edit form
    cursor.execute("SELECT * FROM movies WHERE id=%s", (id,))
    movie = cursor.fetchone()
    if not movie:
        return redirect("/dashboard")

    return render_template("edit.html", movie=movie)

# =========================
# DELETE MOVIE
# =========================
@app.route("/delete/<int:id>")
def delete_movie(id):
    if "admin" not in session:
        return redirect("/admin")

    cursor.execute("DELETE FROM movies WHERE id=%s", (id,))
    db.commit()

    return redirect("/dashboard")

# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    app.run(debug=True)