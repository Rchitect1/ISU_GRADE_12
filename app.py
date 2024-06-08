from flask import Flask, render_template, request, session, redirect, url_for
from flask_session import Session
import sqlite3
from bs4 import BeautifulSoup


email = ""
password = ""
code = ""

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
    return render_template("matches.html")

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
    email = request.form["email"]
    password = request.form["password"]
    code = request.form["code"]

    if code == "123456":
        return redirect(url_for("matches"))
    else:
        return redirect(url_for("login", showModal='true', message="Invalid code"))


if __name__ == "__main__":
    app.run(debug=True)



app.route("/submit_tutor_form", methods=["POST"])
def submit_tutor_form():
    name = request.form["full-name"]
    email = request.form["email"]
    phone = request.form["phone"]
    grade = request.form["grade"]
    period = request.form["period"]
    course = request.form["subject"]

    return render_template("thank.html")




# def doMatchmaking():
#     return null

conn.close()