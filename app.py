from flask import Flask, render_template, request, session, redirect, url_for
from flask_session import Session
import sqlite3
from bs4 import BeautifulSoup




conn = sqlite3.connect("peer_tutor.db")
c = conn.cursor

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/matches")
def matches():
    con = sqlite3.connect("peer_tutor.db")
    cur = con.cursor()
    res = cur.execute("select students.name, students.grade, tutors.name, tutors.grade, students.subject from students, tutors where students.id = tutors.match_id;")
    return render_template("matches.html", matches_list=res.fetchall())

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/student_form")
def student_form():
    return render_template("student_form.html")

@app.route("/tutor_form")
def tutor_form():
    return render_template("tutor_form.html")

@app.route("/thank")
def thank():
    return render_template("thank.html")


@app.route("/signout")
def signout():
    email = ""
    password = ""
    code = ""
    return render_template("index.html")


@app.route("/submit_login", methods=["POST"])
def submit_login():

    school_code = request.form["school-code"]
    code = request.form["code"]

    if code == "123456" and school_code == "654321":

        #nHsmarket1824-4202#ptsklcd
        #891742
        return redirect(url_for("matches"))
    else:
        return redirect(url_for("login", showModal='true', message="Invalid code"))

app.route("/submit_tutor_form", methods=["POST"])
def submit_tutor_form():
    name = request.form["full-name"]
    email = request.form["email"]
    phone = request.form["phone"]
    grade = request.form["grade"]
    period = request.form["period"]
    course = request.form["subject"]

    matchMacking([name, email, phone, grade, course, period], "Tutor")

    return redirect(url_for("thank"))

app.route("/submit_student_form", methods=["POST"])
def submit_tutor_form():
    name = request.form["full-name"]
    email = request.form["email"]
    phone = request.form["phone"]
    grade = request.form["grade"]
    period = request.form["period"]
    course = request.form["subject"]

    matchMacking([name, email, phone, grade, course, period], "Student")

    return render_template("thank.html")

def matchMacking(data, form):
    data = 0
    form = 0

if __name__ == "__main__":
    app.run(debug=True)


# def doMatchmaking():
#     return null

conn.close()