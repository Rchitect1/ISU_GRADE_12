from flask import Flask, render_template, request, session, redirect, url_for
from flask_session import Session
import sqlite3
import smtplib
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
import hashlib
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/signout")
def signout():
    session["school-code"] = None
    session["code"] = None
    return redirect("/")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
            session["school-code"] = request.form.get("school-code")
            session["code"] = request.form.get("code")
            return redirect("/matches")
    return render_template("login.html")

@app.route("/matches")
def matches():  
        if not session.get("school-code"):
            return redirect("/login")

        con = sqlite3.connect("records.db")
        cur = con.cursor()

        school_code = session["school-code"]
        code = session["code"]

        hashed = hashlib.md5(school_code.encode()).hexdigest()

        sclcd_List = cur.execute("select code FROM schools;").fetchall()
        new_lst = []
        for i in range(len(sclcd_List)):
            new_lst.append(sclcd_List[i][0])

        if  hashed in new_lst and code == "220244":
            schl_id =  cur.execute("select id from schools where code = ?;", (hashed,)).fetchone()
            res = cur.execute("select students.id, students.name, students.grade, students.phone, students.email, tutors.name, tutors.grade, tutors.phone, tutors.email, students.subject, students.period from students, tutors where students.id = tutors.match and students.school = ?;", schl_id).fetchall()
            con.close()
            return render_template("matches.html", matches_list=res)
        else:
            con.close()
            return redirect(url_for("login", showModal='true', message="Invalid code"))

@app.route("/remove_s/<student_id>")
def remove_s(student_id): #remove student
    con = sqlite3.connect("records.db")
    cur = con.cursor()

    tutor = cur.execute("SELECT id, name, grade, subject, type, period, phone, email, match, school, crossed FROM tutors WHERE match = ?;", student_id).fetchone()
    crossed_student = cur.execute("SELECT name, subject, email, school, crossed FROM students WHERE id = ?;", student_id).fetchone()
    crossed = tutor[10]+crossed_student[0]+crossed_student[1]+crossed_student[2]+f"{crossed_student[3]}"
    
    #remove tutor match
    cur.execute("UPDATE tutors SET match = NULL, crossed = ? WHERE match = ?;", (crossed,student_id))

    #DELETE the student
    cur.execute("DELETE FROM students WHERE id = ?;", student_id)
    con.commit()
    
    #re-match tutor
    for student in cur.execute("SELECT id, name, grade, subject, type, period, phone, email, match, school, crossed FROM students WHERE match IS NULL ORDER BY id;").fetchall():
        matchAvailable(student, tutor) #pair up 

    
    con.close()
    return redirect("/matches")

@app.route("/remove_t/<student_id>")
def remove_t(student_id): #remove tutor
    con = sqlite3.connect("records.db")
    cur = con.cursor()

    student = cur.execute("SELECT id, name, grade, subject, type, period, phone, email, match, school, crossed FROM students WHERE id = ?;", student_id).fetchone()
    crossed_tutor = cur.execute("SELECT name, subject, email, school, crossed FROM tutors WHERE id = ?;", student_id).fetchone()
    crossed = student[10]+crossed_tutor[0]+crossed_tutor[1]+crossed_tutor[2]+f"{crossed_tutor[3]}"
    
    #remove student match
    cur.execute("UPDATE students SET match = NULL, crossed = ? WHERE id = ?;", (crossed, student_id))

    #DELETE the tutor
    cur.execute("DELETE FROM tutors WHERE match = ?;", student_id)
    con.commit()

    #re-match student
    for tutor in cur.execute("SELECT id, name, grade, subject, type, period, phone, email, match, school, crossed FROM tutors WHERE match IS NULL ORDER BY id;").fetchall():
        matchAvailable(student, tutor) #pair up 

    con.close()
    return redirect("/matches")

@app.route("/remove_b/<student_id>")
def remove_b(student_id): #remove tutor
    con = sqlite3.connect("records.db")
    cur = con.cursor()

    #DELETE the tutor
    cur.execute("DELETE FROM students WHERE id = ?;", student_id)
    cur.execute("DELETE FROM tutors WHERE match = ?;", student_id)
    con.commit()

    con.close()
    return redirect("/matches")

@app.route("/remove_m/<student_id>")
def remove_m(student_id):
    con = sqlite3.connect("records.db")
    cur = con.cursor()

    student = cur.execute("SELECT id, name, grade, subject, type, period, phone, email, match, school, crossed FROM students WHERE id = ?;", student_id).fetchone()
    tutor = cur.execute("SELECT id, name, grade, subject, type, period, phone, email, match, school, crossed FROM tutors WHERE match IS ?;", student_id).fetchone()
    crossed_student = tutor[10]+student[1]+student[3]+student[7]+f"{student[9]}"
    crossed_tutor = student[10]+tutor[1]+tutor[3]+tutor[7]+f"{tutor[9]}"

    #empty match
    cur.execute("UPDATE students SET match = NULL, crossed = ? WHERE id = ?;", (crossed_tutor, student_id))
    cur.execute("UPDATE tutors SET match = NULL, crossed = ? WHERE match = ?;", (crossed_student, student_id))
    con.commit()

    #re-match
    for t in cur.execute("SELECT id, name, grade, subject, type, period, phone, email, match, school, crossed FROM tutors WHERE match IS NULL ORDER BY id;").fetchall():
        matchAvailable(student, t) #pair up

    for s in cur.execute("SELECT id, name, grade, subject, type, period, phone, email, match, school, crossed FROM students WHERE match IS NULL ORDER BY id;").fetchall():
        matchAvailable(s, tutor) #pair up 
    
    #close
    con.close()
    return redirect("/matches")

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
    crossed = " "

    schl_id = c.execute("SELECT id FROM schools WHERE school = ?;", (school,)).fetchone()[0]

    if(form == "Student"): # if form is student
        insert = [name, grade, subject, type, period, phone, email, match, int(schl_id), crossed] #i need to find out how to do course type, its missing from here
        c.execute("INSERT INTO students(name, grade, subject, type, period, phone, email, match, school, crossed) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", insert)
        conn.commit()
        conn.close()

        conn = sqlite3.connect("records.db")
        c = conn.cursor()
        st_id = c.execute("SELECT MAX(id) from students;").fetchone()[0]
        student_data = [st_id, name, int(grade), subject, type, period, phone, email, match, int(schl_id), crossed]
        row = None
        for row in c.execute("SELECT id, name, grade, subject, type, period, phone, email, match, school, crossed FROM tutors WHERE match IS NULL ORDER BY id;").fetchall(): #if no match value, might be null? i dont know  
            matchAvailable(student_data, row)
                           
    if(form == "Tutor"): # if form is tutor
        insert = [name, grade, subject, type, period, phone, email, match, int(schl_id), crossed] #i need to find out how to do course type, its missing from here
        c.execute("INSERT INTO tutors(name, grade, subject, type, period, phone, email, match, school, crossed) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", insert)
        conn.commit()
        conn.close()

        conn = sqlite3.connect("records.db")
        c = conn.cursor()
        tr_id = c.execute("SELECT MAX(id) from tutors;").fetchone()[0]
        tutor_data = [tr_id, name, int(grade), subject, type, period, phone, email, match, int(schl_id), crossed]
        row = None
        for row in c.execute("SELECT id, name, grade, subject, type, period, phone, email, match, school, crossed FROM students WHERE match IS NULL ORDER BY id;").fetchall(): #if no match value, might be null? i dont know      
            matchAvailable(row, tutor_data) 

    conn.commit()
    conn.close()

def matchAvailable(student, tutor): #takes 2 arrays

    conn = sqlite3.connect("records.db")
    c = conn.cursor()
    print(student, tutor)

    #read from the forbidden matches file
    if not (student[1]+student[3]+student[7]+f"{student[9]}" in tutor[10]):
        print(-1)
        if not (tutor[1]+tutor[3]+tutor[7]+f"{tutor[9]}" in student[10]):
            print(0)
        #pair up student and tutor (if eligable)
            if (student[9] == tutor[9]):
                print(1)
                if (student[5] == tutor[5]):
                    print(2)
                    if ((student[3][0] == 'S' and tutor[3][0] == 'S') or (student[3][0] == 'C' and tutor[3][0] == 'C')): #checks first letter (subject))
                        print(3)
                        if(student[3][0] == 'S' and tutor[3][0] == 'S'):
                            if ((int (student [3][-2]) <= 2 and int (tutor[3][-2]) >=2 ) or (int ((student [3][-2])) == 1 and int (tutor[3][-2]) == 1)):
                                 print(4)
                                 match(student, tutor)
                        
                        elif (student[3][1] == tutor[3][1]):
                             print(5)
                             match(student, tutor)

                    elif (student[3][0] == tutor[3][0]): #checks first letter (subject)
                        print(6)
                        if (int(student[3][-2]) < int (tutor[3][-2])): #checks second last letter (grade)
                            print(7)
                            match(student, tutor)
                            
                        elif(int(student[3][-2]) == int (tutor[3][-2])): #checks second last latter (grade)
                            print(8)
                            if ((student[3][-1]) <= tutor[3][-1]): #checks last letter (c/U)
                                print(9)
                                match(student, tutor)
                            
    conn.commit()
    conn.close()

def match(student, tutor): #STUDENT HAS TO BE FIRST
    print(10)
    
    conn = sqlite3.connect("records.db")
    c = conn.cursor()
    c.execute("UPDATE students SET match = ? WHERE id = ?;", (tutor[0], student[0]))
    c.execute("UPDATE tutors SET match = ? WHERE id = ?;", (student[0], tutor[0]))  
    conn.commit()
    conn.close()        
    send_email(student[7], "Tutor Found", f"Hi {student[1]}!\n" f"Thank you for using Peer Tutoring Management System!\n" f"Your tutor is {tutor[1]}.\n" f"You have been scheduled for {tutor[5]}.\n" f"Good Luck!")
    send_email(tutor[7], "Peer Found", f"Hi {tutor[1]}!\n"f"Thank you for using Peer Tutoring Management System!\n" f"Your peer is {student[1]}.\n" f"You have been scheduled for {tutor[5]}.\n" f"Good Luck!")

def send_email(to_address, subject, body):
    # Define email sender and receiver
    from_address = "peertutoringmanagementsystem@gmail.com"
    password = "pbym exmx znqc eqys"

    # Create the email headers and payload
    msg = MIMEMultipart()
    msg['From'] = from_address
    msg['To'] = to_address
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Connect to the Gmail SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()

        # Login to the email account
        server.login(from_address, password)

        # Send the email
        server.send_message(msg)
        print(f"Email sent to {to_address}")

    except Exception as e:
        print(f"Failed to send email: {e}")

    finally:
        # Close the connection to the server
        server.quit()


if __name__ == "__main__":
    app.run(debug=True)

