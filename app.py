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

@app.route("/matches", methods=["POST"])
def matches():
    if request.method == "POST":   
        con = sqlite3.connect("records.db")
        cur = con.cursor()
        print(request.form)

        school_code = request.form["school-code"]
        code = request.form["code"]

        sclcd_List = cur.execute("select code FROM schools;").fetchall()
        new_lst = []
        for i in range(len(sclcd_List)):
            new_lst.append(sclcd_List[i][0])

        if  school_code in new_lst and code == "978659":
            schl_id =  cur.execute("select id from schools where code = ?;", (school_code,)).fetchone()
            res = cur.execute("select students.id, students.name, students.grade, tutors.name, tutors.grade, students.subject from students, tutors, schools where students.id = tutors.match and students.school = ?;", schl_id).fetchall()
            con.close()
            return render_template("matches.html", matches_list=res)
        else:
            con.close()
            return redirect(url_for("login", showModal='true', message="Invalid code"))
    else:
        return redirect("/login")

@app.route("/remove_s/<student_id>")
def remove_s(student_id):
    con = sqlite3.connect("records.db")
    cur = con.cursor()
    cur.execute("DELETE FROM students WHERE id = ?;", student_id)
    cur.execute("UPDATE tutors SET match = NULL WHERE match = ?;", student_id)
    con.commit()
    con.close()

    #matchMaking(data)
    return redirect("/login")

@app.route("/remove_t/<student_id>")
def remove_t(student_id):
    con = sqlite3.connect("records.db")
    cur = con.cursor()
    cur.execute("DELETE FROM tutors WHERE match = ?;", student_id)
    cur.execute("UPDATE students SET match = NULL WHERE id = ?;", student_id)
    con.commit()
    con.close()
    #matchMaking(data)
    return redirect("/login")

@app.route("/remove_m/<student_id>")
def remove_m(student_id):
    con = sqlite3.connect("records.db")
    cur = con.cursor()
    cur.execute("UPDATE students SET match = NULL WHERE id = ?;", student_id)
    cur.execute("UPDATE tutors SET match = NULL WHERE match = ?;", student_id)
    con.commit()
    con.close()
    #matchMaking(data)
    return redirect("/login")

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

@app.route("/submit_tutor_form", methods=["POST"])
def submit_tutor_form():
    name = request.form["full_name"]
    email = request.form["email"]
    phone = request.form["phone"]
    school = request.form["school"]
    grade = request.form["grade"]
    period = request.form["period"]
    subject = request.form["subject"]
    
    type = subject[len(subject)-1]

    matchMacking([name, grade, subject, type, period, phone, email, school], "Tutor")

    return redirect("/thank")

@app.route("/submit_student_form", methods=["POST"])
def submit_student_form():
    name = request.form["full_name"]
    email = request.form["email"]
    phone = request.form["phone"]
    school = request.form["school"]
    grade = request.form["grade"]
    period = request.form["period"]
    subject = request.form["subject"]
    type = None
    
    type = subject[len(subject)-1]
        
    matchMacking([name, grade, subject, type, period, phone, email, school], "Student")

    return redirect("/thank")

def matchMacking(data, form):
    conn = sqlite3.connect("records.db")
    c = conn.cursor()

    name = data[0]
    grade = data[1]
    subject = data[2]
    type = data[3]
    period = data[4]
    phone = data[5]
    email = data[6]
    school = data[7]
    match = None

    schl_id = c.execute("SELECT id FROM schools WHERE school = ?;", (school,)).fetchone()[0]

    if(form == "Student"): # if form is student
        insert = [name, grade, subject, type, period, phone, email, match, int(schl_id)] #i need to find out how to do course type, its missing from here
        c.execute("INSERT INTO students(name, grade, subject, type, period, phone, email, match, school) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?);", insert)
        conn.commit()
        conn.close()

        conn = sqlite3.connect("records.db")
        c = conn.cursor()
        st_id = c.execute("SELECT MAX(id) from students;").fetchone()[0]
        row = None
        for row in c.execute("SELECT id, name, grade, subject, type, period, phone, email, match, school FROM tutors WHERE match IS NULL ORDER BY id;").fetchall(): #if no match value, might be null? i dont know         
            if(row[2] >= int(grade) and row[3] == subject and row[5] == period and row[9] == schl_id): #if grade bigger, same subject and period
                c.execute("UPDATE tutors SET match = ? WHERE id = ?;", (st_id, row[0]))
                c.execute("UPDATE students SET match = ? WHERE id = ?;", (row[0], st_id))
                

        
        
    if(form == "Tutor"): # if form is tutor
        insert = [name, grade, subject, type, period, phone, email, match, int(schl_id)] #i need to find out how to do course type, its missing from here
        c.execute("INSERT INTO tutors(name, grade, subject, type, period, phone, email, match, school) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?);", insert)
        conn.commit()
        conn.close()

        conn = sqlite3.connect("records.db")
        c = conn.cursor()
        tr_id = c.execute("SELECT MAX(id) from tutors;").fetchone()[0]
        row = None
        for row in c.execute("SELECT id, name, grade, subject, type, period, phone, email, match, school FROM students WHERE match IS NULL ORDER BY id;").fetchall(): #if no match value, might be null? i dont know         
            if(row[2] <= int(grade) and row[3] == subject and row[5] == period and row[9] == schl_id): #if grade smaller, same subject and period
                c.execute("UPDATE students SET match = ? WHERE id = ?;", (tr_id, row[0]))
                c.execute("UPDATE tutors SET match = ? WHERE id = ?;", (row[0], tr_id))

    conn.commit()
    conn.close()
    
    
if __name__ == "__main__":
    app.run(debug=True)


# def doMatchmaking():
#     return null

