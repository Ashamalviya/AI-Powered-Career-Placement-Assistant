import os
import sqlite3
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)

app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "development-secret-key-change-later"
)

DATABASE = os.path.join("database", "career.db")


# ---------------- DATABASE ----------------

def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_database():

    os.makedirs("database", exist_ok=True)

    connection = get_db()

    connection.executescript("""
    
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        education TEXT DEFAULT '',
        skills TEXT DEFAULT '',
        target_role TEXT DEFAULT ''
    );

    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        company TEXT NOT NULL,
        location TEXT NOT NULL,
        skills TEXT NOT NULL,
        description TEXT
    );

    CREATE TABLE IF NOT EXISTS quiz_questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT NOT NULL,
        option_a TEXT NOT NULL,
        option_b TEXT NOT NULL,
        option_c TEXT NOT NULL,
        option_d TEXT NOT NULL,
        answer TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS quiz_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        score INTEGER NOT NULL,
        total INTEGER NOT NULL
    );

    """)

    # Add sample jobs only once
    job_count = connection.execute(
        "SELECT COUNT(*) FROM jobs"
    ).fetchone()[0]

    if job_count == 0:

        jobs = [
            (
                "Python Developer",
                "Tech Solutions",
                "Indore / Remote",
                "Python,SQL,Flask,Git",
                "Develop backend applications using Python."
            ),
            (
                "Frontend Developer",
                "WebWorks",
                "Remote",
                "HTML,CSS,JavaScript,React",
                "Create responsive web applications."
            ),
            (
                "Java Developer",
                "Software Labs",
                "Bangalore",
                "Java,SQL,OOP,Spring",
                "Develop Java-based software applications."
            ),
            (
                "QA Engineer",
                "QualityTech",
                "Pune / Remote",
                "Testing,SQL,Java,Automation",
                "Test applications and find software defects."
            ),
            (
                "Business Analyst",
                "Digital Systems",
                "Gurgaon",
                "SQL,Excel,Communication,Analysis",
                "Analyze business requirements and data."
            )
        ]

        connection.executemany(
            """
            INSERT INTO jobs
            (title, company, location, skills, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            jobs
        )

    # Add quiz questions only once
    question_count = connection.execute(
        "SELECT COUNT(*) FROM quiz_questions"
    ).fetchone()[0]

    if question_count == 0:

        questions = [
            (
                "Which language is mainly used with Flask?",
                "Python",
                "Java",
                "C++",
                "PHP",
                "A"
            ),
            (
                "Which SQL command retrieves data?",
                "INSERT",
                "SELECT",
                "DELETE",
                "UPDATE",
                "B"
            ),
            (
                "Which HTML tag creates a hyperlink?",
                "<p>",
                "<h1>",
                "<a>",
                "<img>",
                "C"
            ),
            (
                "Which data structure follows LIFO?",
                "Queue",
                "Stack",
                "Array",
                "Tree",
                "B"
            ),
            (
                "Which keyword defines a function in Python?",
                "function",
                "def",
                "fun",
                "define",
                "B"
            ),
            (
                "What does CSS primarily control?",
                "Database",
                "Webpage styling",
                "Server hardware",
                "Passwords",
                "B"
            ),
            (
                "Which one is a relational database?",
                "MySQL",
                "Git",
                "Flask",
                "HTML",
                "A"
            ),
            (
                "What does OOP stand for?",
                "Object Oriented Programming",
                "Open Online Protocol",
                "Object Output Process",
                "Order Of Programs",
                "A"
            ),
            (
                "Which Git command uploads commits?",
                "git pull",
                "git clone",
                "git push",
                "git init",
                "C"
            ),
            (
                "Which HTTP status means Not Found?",
                "200",
                "301",
                "404",
                "500",
                "C"
            )
        ]

        connection.executemany(
            """
            INSERT INTO quiz_questions
            (
                question,
                option_a,
                option_b,
                option_c,
                option_d,
                answer
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            questions
        )

    connection.commit()
    connection.close()


# ---------------- LOGIN CHECK ----------------

def login_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            flash("Please login first.", "warning")
            return redirect(url_for("login"))

        return function(*args, **kwargs)

    return wrapper


# ---------------- HOME ----------------

@app.route("/")
def index():
    return render_template("index.html")


# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:

            flash("All fields are required.", "danger")
            return render_template("register.html")

        if len(password) < 6:

            flash(
                "Password must contain at least 6 characters.",
                "danger"
            )

            return render_template("register.html")

        connection = get_db()

        try:

            hashed_password = generate_password_hash(password)

            connection.execute(
                """
                INSERT INTO users
                (name, email, password)
                VALUES (?, ?, ?)
                """,
                (name, email, hashed_password)
            )

            connection.commit()

            flash(
                "Registration successful. Please login.",
                "success"
            )

            return redirect(url_for("login"))

        except sqlite3.IntegrityError:

            flash(
                "This email is already registered.",
                "danger"
            )

        finally:
            connection.close()

    return render_template("register.html")


# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        connection = get_db()

        user = connection.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        connection.close()

        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]

            flash(
                "Login successful!",
                "success"
            )

            return redirect(url_for("dashboard"))

        flash(
            "Invalid email or password.",
            "danger"
        )

    return render_template("login.html")


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "You have been logged out.",
        "success"
    )

    return redirect(url_for("index"))


# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
@login_required
def dashboard():

    connection = get_db()

    user = connection.execute(
        """
        SELECT *
        FROM users
        WHERE id = ?
        """,
        (session["user_id"],)
    ).fetchone()

    results = connection.execute(
        """
        SELECT *
        FROM quiz_results
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 5
        """,
        (session["user_id"],)
    ).fetchall()

    job_count = connection.execute(
        "SELECT COUNT(*) FROM jobs"
    ).fetchone()[0]

    connection.close()

    return render_template(
        "dashboard.html",
        user=user,
        results=results,
        job_count=job_count
    )


# ---------------- PROFILE ----------------

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():

    connection = get_db()

    if request.method == "POST":

        education = request.form.get(
            "education",
            ""
        ).strip()

        skills = request.form.get(
            "skills",
            ""
        ).strip()

        target_role = request.form.get(
            "target_role",
            ""
        ).strip()

        connection.execute(
            """
            UPDATE users

            SET education = ?,
                skills = ?,
                target_role = ?

            WHERE id = ?
            """,
            (
                education,
                skills,
                target_role,
                session["user_id"]
            )
        )

        connection.commit()

        flash(
            "Profile updated successfully.",
            "success"
        )

    user = connection.execute(
        """
        SELECT *
        FROM users
        WHERE id = ?
        """,
        (session["user_id"],)
    ).fetchone()

    connection.close()

    return render_template(
        "profile.html",
        user=user
    )


# ---------------- JOBS ----------------

@app.route("/jobs")
@login_required
def jobs():

    connection = get_db()

    jobs_data = connection.execute(
        """
        SELECT *
        FROM jobs
        ORDER BY id DESC
        """
    ).fetchall()

    connection.close()

    return render_template(
        "jobs.html",
        jobs=jobs_data
    )


# ---------------- RECOMMENDATIONS ----------------

@app.route("/recommendations")
@login_required
def recommendations():

    connection = get_db()

    user = connection.execute(
        """
        SELECT skills, target_role
        FROM users
        WHERE id = ?
        """,
        (session["user_id"],)
    ).fetchone()

    jobs_data = connection.execute(
        "SELECT * FROM jobs"
    ).fetchall()

    connection.close()

    student_skills = {
        skill.strip().lower()
        for skill in (user["skills"] or "").split(",")
        if skill.strip()
    }

    target_role = (
        user["target_role"] or ""
    ).lower()

    recommendations_data = []

    for job in jobs_data:

        required_skills = {
            skill.strip().lower()
            for skill in job["skills"].split(",")
            if skill.strip()
        }

        matched_skills = (
            student_skills.intersection(
                required_skills
            )
        )

        if required_skills:

            score = round(
                len(matched_skills)
                / len(required_skills)
                * 100
            )

        else:

            score = 0

        if target_role and (
            target_role in job["title"].lower()
        ):

            score = min(
                score + 20,
                100
            )

        recommendations_data.append({
            "title": job["title"],
            "company": job["company"],
            "location": job["location"],
            "skills": job["skills"],
            "description": job["description"],
            "score": score
        })

    recommendations_data.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return render_template(
        "recommendations.html",
        recommendations=recommendations_data
    )


# ---------------- QUIZ ----------------

@app.route("/quiz", methods=["GET", "POST"])
@login_required
def quiz():

    connection = get_db()

    questions = connection.execute(
        """
        SELECT *
        FROM quiz_questions
        ORDER BY id
        """
    ).fetchall()

    if request.method == "POST":

        score = 0

        for question in questions:

            selected_answer = request.form.get(
                f"q{question['id']}"
            )

            if selected_answer == question["answer"]:
                score += 1

        connection.execute(
            """
            INSERT INTO quiz_results
            (user_id, score, total)
            VALUES (?, ?, ?)
            """,
            (
                session["user_id"],
                score,
                len(questions)
            )
        )

        connection.commit()
        connection.close()

        return render_template(
            "quiz_result.html",
            score=score,
            total=len(questions)
        )

    connection.close()

    return render_template(
        "quiz.html",
        questions=questions
    )


# ---------------- RUN ----------------

if __name__ == "__main__":

    init_database()

    app.run(
        debug=True
    )
