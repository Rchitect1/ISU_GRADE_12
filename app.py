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


# def doMatchmaking():
#     return null

conn.close()