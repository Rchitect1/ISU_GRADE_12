from flask import Flask, render_template, request, session, redirect, url_for
from flask_session import Session
import sqlite3
from bs4 import BeautifulSoup

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/matches")
def matches():
    con = sqlite3.connect("records.db")
    cur = con.cursor()
    res = cur.execute("select students.id, students.name, students.grade, tutors.name, tutors.grade, students.subject from students, tutors where students.id = tutors.match;")
    lst = res.fetchall()
    con.close()
    return render_template("matches.html", matches_list=lst)

@app.route("/remove_s/<student_id>")
def remove_s(student_id):
    con = sqlite3.connect("records.db")
    cur = con.cursor()
    cur.execute("DELETE FROM students WHERE id = ?;", student_id)
    con.commit()
    con.close()
    return redirect("/matches")

@app.route("/remove_t/<student_id>")
def remove_t(student_id):
    con = sqlite3.connect("records.db")
    cur = con.cursor()
    cur.execute("DELETE FROM tutors WHERE match = ?;", student_id)
    con.commit()
    con.close()
    return redirect("/matches")

@app.route("/remove_m/<student_id>")
def remove_m(student_id):
    con = sqlite3.connect("records.db")
    cur = con.cursor()
    cur.execute("UPDATE students SET match = NULL WHERE id = ?;", student_id)
    cur.execute("UPDATE tutors SET match = NULL WHERE match = ?;", student_id)
    con.commit()
    con.close()
    return redirect("/matches")

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
    return render_template("index.html")


@app.route("/submit_login", methods=["POST"])
def submit_login():

    school_code = request.form["school-code"]
    code = request.form["code"]

    if code == "123456" and school_code == "654321":

        #nHsmarket1824-4202#ptsklcd
        #891742
        return redirect("/matches")
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

    return redirect("/thank")

app.route("/submit_student_form", methods=["POST"])
def submit_tutor_form():
    name = request.form["full-name"]
    email = request.form["email"]
    phone = request.form["phone"]
    grade = request.form["grade"]
    period = request.form["period"]
    course = request.form["subject"]

    matchMacking([name, email, phone, grade, course, period], "Student")

    return redirect("/thank")

def matchMacking(data, form):
    conn = sqlite3.connect("records.db")
    c = conn.cursor()

    name = data[0]
    email = data[1]
    phone = data[2]
    grade = data[3]
    course = data[4]
    period = data[5]
    match = None

    sId = 0 #student ID
    for row in c.execute:
        sId += 1

    if(form == "Student"): # if form is student
        t = c.execute("SELECT name FROM sqlite_master WHERE name='tutors'")
        for row in c.execute("SELECT id, grade, subject, match, type, period FROM tutors ORDER BY id WHERE match == None"): #if no match value, might be null? i dont know
          
            if(row[1] > grade and row[2] == course and row[8] == period ): #if grade bigger, same subject and period
                if (match != None):
                    match = row[5] #student match= tutor ID
                else:
                    match = None

        insert = [sId, name, email, grade, course, match, "university", phone, period] #i need to find out how to do course type, its missing from here
        c.executemany("INSERT INTO students VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)", insert)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    app.run(debug=True)


# def doMatchmaking():
#     return null

