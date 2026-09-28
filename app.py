from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
DB_PATH = os.path.join(BASE_DIR, "users.db")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username  TEXT UNIQUE NOT NULL,
            password  TEXT NOT NULL,
            firstname TEXT,
            lastname  TEXT,
            email     TEXT,
            address   TEXT,
            filename  TEXT,
            wordcount INTEGER
        )
        """
    )
    conn.commit()
    conn.close()

init_db()

# Routes
@app.route("/")
def index():
    return render_template("register.html")


@app.route("/register", methods=["POST"])
def register():
    # Registration
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    firstname = request.form.get("firstname", "").strip()
    lastname = request.form.get("lastname", "").strip()
    email = request.form.get("email", "").strip()
    address = request.form.get("address", "").strip()

    if not username or not password:
        return "Username and password are required. <a href='/'>Go back</a>"

    filename = None
    wordcount = 0
    uploaded_file = request.files.get("userfile")

    if uploaded_file and uploaded_file.filename:
        safe_name = secure_filename(uploaded_file.filename)
        # prefix with the username so two users can upload files with the same name
        filename = f"{username}_{safe_name}"
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        uploaded_file.save(filepath)

        # Word count
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            wordcount = len(content.split())
        except Exception:
            wordcount = 0

    conn = get_db()
    try:
        conn.execute(
            """INSERT INTO users
               (username, password, firstname, lastname, email, address, filename, wordcount)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (username, password, firstname, lastname, email, address, filename, wordcount),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return "That username is already taken. <a href='/'>Go back</a>"
    conn.close()

    return redirect(url_for("profile", username=username))


@app.route("/profile/<username>")
def profile(username):
    # Display information
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()

    if user is None:
        return "No such user. <a href='/'>Go back</a>"

    return render_template("profile.html", user=user)


@app.route("/login", methods=["GET", "POST"])
def login():
    # Re-login
    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?", (username, password)
    ).fetchone()
    conn.close()

    if user is None:
        return render_template("login.html", error="Invalid username or password.")

    return redirect(url_for("profile", username=username))


@app.route("/download/<username>")
def download(username):
    conn = get_db()
    user = conn.execute("SELECT filename FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()

    if user is None or not user["filename"]:
        return "No file on record for this user. <a href='/'>Go back</a>"

    return send_from_directory(app.config["UPLOAD_FOLDER"], user["filename"], as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
