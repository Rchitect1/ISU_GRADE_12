from flask import Flask, render_template, request, session
from flask_session import Session
import sqlite3

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

    @app.route("/student_form")
def student_form():
    return render_template("student_form.html")

# def doMatchmaking():
#     return null

conn.close()