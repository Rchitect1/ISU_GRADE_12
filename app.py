####################################################################################
######## Project: Peer Tutoring Management System
######## Aim: This is a system to facilitate the peer tutoring management in schools
######## Authors: Koosha Shamdani, Reza Homayounmehr, Patrick Wei
######## Course: ICS4U
######## Date: June 17, 2024
####################################################################################


####################################################################################
######## Initialization
####################################################################################

# Import all of the important packages for the program to function properly
from flask import Flask, render_template, request, session, redirect, url_for
from flask_session import Session
import sqlite3
import smtplib
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
import hashlib
from email.mime.multipart import MIMEMultipart

# Initialize Flask
app = Flask(__name__)

# Initialize Flask-session for login system
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


####################################################################################
######## Main Functions of Program
####################################################################################

# The function for Main Page functionality
@app.route("/")
def index():
    # Create the Main Page
    return render_template("index.html")

# The function to sign out the guidance staff
@app.route("/signout")
def signout():
    # Remove any cookies associated with that guidance staff
    session["school-code"] = None
    session["code"] = None
    # Redirect to Main Page
    return redirect("/")

# The function to login the guidance staff into the website (Login Page functionality)
@app.route("/login", methods=["GET", "POST"])
def login():
    # If the guidance staff input some data to login save those data for the future access to Matches Page
    if request.method == "POST":
            session["school-code"] = request.form.get("school-code")
            session["code"] = request.form.get("code")
            # Redirect to the Matches Page
            return redirect("/matches")
    # If the guidance staff wants to login, create the Login Page
    return render_template("login.html")

# The function for Matches Page Functionality 
@app.route("/matches")
def matches():  
        # If the guidance staff do not have session, then they should login
        if not session.get("school-code"):
            # Redirect to Login Page
            return redirect("/login")

        # Open the database to read in the matches
        con = sqlite3.connect("records.db")
        cur = con.cursor()

        # Get the codes that the guidance staff input in Loging Page
        school_code = session["school-code"]
        code = session["code"]

        # Hash the school code
        hashed = hashlib.md5(school_code.encode()).hexdigest()

        # Read in all of the schools from the database
        sclcd_List = cur.execute("select code FROM schools;").fetchall()
        new_lst = []
        for i in range(len(sclcd_List)):
            new_lst.append(sclcd_List[i][0])

        # If the codes are the same with one of the schools, show all of the matches associated with that school in the Matches Page and close the database
        if  hashed in new_lst and code == "220244":
            schl_id =  cur.execute("select id from schools where code = ?;", (hashed,)).fetchone()
            res = cur.execute("select students.id, students.name, students.grade, students.phone, students.email, tutors.name, tutors.grade, tutors.phone, tutors.email, students.subject, students.period from students, tutors where students.id = tutors.match and students.school = ?;", schl_id).fetchall()
            con.close()
            return render_template("matches.html", matches_list=res)
        # If the codes are not matching with a school return an error to the guidance staff and remove the session data
        else:
            con.close()
            session["school-code"] = None
            session["code"] = None
            return redirect(url_for("login", showModal='true', message="Invalid code"))

# The function to remove a student from a match using its button in the Matches Page
@app.route("/remove_s/<student_id>")
def remove_s(student_id): 
    # Open the database to read in data
    con = sqlite3.connect("records.db")
    cur = con.cursor()

    # Find the tutor that becomes available and the student that is removed from the match
    tutor = cur.execute("SELECT id, name, grade, subject, type, period, phone, email, match, school, crossed FROM tutors WHERE match = ?;", student_id).fetchone()
    crossed_student = cur.execute("SELECT name, subject, email, school, crossed FROM students WHERE id = ?;", student_id).fetchone()
    crossed = tutor[10]+crossed_student[0]+crossed_student[1]+crossed_student[2]+f"{crossed_student[3]}"
    
    # Remove the match between the tutor and the student
    cur.execute("UPDATE tutors SET match = NULL, crossed = ? WHERE match = ?;", (crossed,student_id))

    # DELETE the student
    cur.execute("DELETE FROM students WHERE id = ?;", student_id)
    con.commit()
    
    # Rematch the tutor if there is a possible match
    for student in cur.execute("SELECT id, name, grade, subject, type, period, phone, email, match, school, crossed FROM students WHERE match IS NULL ORDER BY id;").fetchall():
        checkPossibilityMatching(student, tutor) #pair up 

    # close the database
    con.close()
    # Redirect to the Matches Page
    return redirect("/matches")

# The function to remove a tutor from a match using its button in the Matches Page
@app.route("/remove_t/<student_id>")
def remove_t(student_id): 
    # Open the database to read in data
    con = sqlite3.connect("records.db")
    cur = con.cursor()

    # Find the student that becomes available and the tutor that is removed from the match
    student = cur.execute("SELECT id, name, grade, subject, type, period, phone, email, match, school, crossed FROM students WHERE id = ?;", student_id).fetchone()
    crossed_tutor = cur.execute("SELECT name, subject, email, school, crossed FROM tutors WHERE id = ?;", student_id).fetchone()
    crossed = student[10]+crossed_tutor[0]+crossed_tutor[1]+crossed_tutor[2]+f"{crossed_tutor[3]}"
    
    # Remove the match between the tutor and the student
    cur.execute("UPDATE students SET match = NULL, crossed = ? WHERE id = ?;", (crossed, student_id))

    # DELETE the tutor
    cur.execute("DELETE FROM tutors WHERE match = ?;", student_id)
    con.commit()

    # Rematch the student if there is a possible match
    for tutor in cur.execute("SELECT id, name, grade, subject, type, period, phone, email, match, school, crossed FROM tutors WHERE match IS NULL ORDER BY id;").fetchall():
        checkPossibilityMatching(student, tutor) #pair up 

    # close the database
    con.close()
    # Redirect to the Matches Page
    return redirect("/matches")

# The function to remove both tutor and student of a match using its button in the Matches Page
@app.route("/remove_b/<student_id>")
def remove_b(student_id): 
    # Open the database to read in data
    con = sqlite3.connect("records.db")
    cur = con.cursor()

    # DELETE both the tutor and the student
    cur.execute("DELETE FROM students WHERE id = ?;", student_id)
    cur.execute("DELETE FROM tutors WHERE match = ?;", student_id)
    con.commit()

    # close the database
    con.close()
    # Redirect to the Matches Page
    return redirect("/matches")

# The function to remove the match between a tutor and a student using its button in the Matches Page
@app.route("/remove_m/<student_id>")
def remove_m(student_id):
    # Open the database to read in data
    con = sqlite3.connect("records.db")
    cur = con.cursor()

    # Find the student and the tutor that become available 
    student = cur.execute("SELECT id, name, grade, subject, type, period, phone, email, match, school, crossed FROM students WHERE id = ?;", student_id).fetchone()
    tutor = cur.execute("SELECT id, name, grade, subject, type, period, phone, email, match, school, crossed FROM tutors WHERE match IS ?;", student_id).fetchone()
    crossed_student = tutor[10]+student[1]+student[3]+student[7]+f"{student[9]}"
    crossed_tutor = student[10]+tutor[1]+tutor[3]+tutor[7]+f"{tutor[9]}"

    # Remove the match between the tutor and the student
    cur.execute("UPDATE students SET match = NULL, crossed = ? WHERE id = ?;", (crossed_tutor, student_id))
    cur.execute("UPDATE tutors SET match = NULL, crossed = ? WHERE match = ?;", (crossed_student, student_id))
    con.commit()

    # Rematch the student if there is a possible match
    for t in cur.execute("SELECT id, name, grade, subject, type, period, phone, email, match, school, crossed FROM tutors WHERE match IS NULL ORDER BY id;").fetchall():
        checkPossibilityMatching(student, t) #pair up

    # Rematch the tutor if there is a possible match
    for s in cur.execute("SELECT id, name, grade, subject, type, period, phone, email, match, school, crossed FROM students WHERE match IS NULL ORDER BY id;").fetchall():
        checkPossibilityMatching(s, tutor) #pair up 
    
    # close the database
    con.close()
    # Redirect to the Matches Page
    return redirect("/matches")

# The function for Student Form Creation
@app.route("/student_form")
def student_form():
    # Create the form
    return render_template("student_form.html")

# The function for Tutor Form Creation
@app.route("/tutor_form")
def tutor_form():
    # Create the form
    return render_template("tutor_form.html")

# The function for Thank You Page functionality 
@app.route("/thank")
def thank():
    # Create the page
    return render_template("thank.html")

# The function for Tutor Form functionality
@app.route("/submit_tutor_form", methods=["POST"])
def submit_tutor_form():
    # Get the tutor's input
    name = request.form["full_name"]
    email = request.form["email"]
    phone = request.form["phone"]
    school = request.form["school"]
    grade = request.form["grade"]
    period = request.form["period"]
    subject = request.form["subject"]
    
    type = subject[len(subject)-1]

    # Find the possible match and make a match between them
    prepareDataForMatching([name, grade, subject, type, period, phone, email, school], "Tutor")

    # Redirect to Thank You Page
    return redirect("/thank")

# The function for Student Form functionality
@app.route("/submit_student_form", methods=["POST"])
def submit_student_form():
    # Get the student's input
    name = request.form["full_name"]
    email = request.form["email"]
    phone = request.form["phone"]
    school = request.form["school"]
    grade = request.form["grade"]
    period = request.form["period"]
    subject = request.form["subject"]
    
    type = subject[len(subject)-1]
        
    # Find the possible match and make a match between them
    prepareDataForMatching([name, grade, subject, type, period, phone, email, school], "Student")

    # Redirect to Thank You Page
    return redirect("/thank")

# The function to fetch the correct data for making a match
def prepareDataForMatching(data, form):
    # Open the database to read in data
    conn = sqlite3.connect("records.db")
    c = conn.cursor()

    # Get the input data of the form (if the form is Tutor Form, the data is for the tutor and if the form is Student Form, the data is for the student)
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

    # If the input form is for student
    if(form == "Student"): 
        # Create the student
        insert = [name, grade, subject, type, period, phone, email, match, int(schl_id), crossed] 
        c.execute("INSERT INTO students(name, grade, subject, type, period, phone, email, match, school, crossed) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", insert)
        conn.commit()
        conn.close()

        # Open the database to read in data
        conn = sqlite3.connect("records.db")
        c = conn.cursor()
        # Get the data for the student
        st_id = c.execute("SELECT MAX(id) from students;").fetchone()[0]
        student_data = [st_id, name, int(grade), subject, type, period, phone, email, match, int(schl_id), crossed]
        row = None
        matched = False
        # Find the available tutors
        for row in c.execute("SELECT id, name, grade, subject, type, period, phone, email, match, school, crossed FROM tutors WHERE match IS NULL ORDER BY id;").fetchall(): 
            # Try to match them if it is possible
            if checkPossibilityMatching(student_data, row):
                matched = True
                break
        # If no match is found, send email notification
        if not matched:
            send_email(email, "Standby", f"Hi {name},\n\nThank you for using the Peer Tutoring Management System.\n\nYou have not been assigned a tutor yet. Please keep an eye on your inbox for an update.\n\nGood Luck!\nPeer Tutoring Management System")

    # If the input form is for tutor   
    if(form == "Tutor"): 
        # Create the tutor
        insert = [name, grade, subject, type, period, phone, email, match, int(schl_id), crossed] 
        c.execute("INSERT INTO tutors(name, grade, subject, type, period, phone, email, match, school, crossed) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", insert)
        conn.commit()
        conn.close()

        # Open the database to read in data
        conn = sqlite3.connect("records.db")
        c = conn.cursor()
        # Get the data for the tutor
        tr_id = c.execute("SELECT MAX(id) from tutors;").fetchone()[0]
        tutor_data = [tr_id, name, int(grade), subject, type, period, phone, email, match, int(schl_id), crossed]
        row = None
        matched = False
        # Find the available students
        for row in c.execute("SELECT id, name, grade, subject, type, period, phone, email, match, school, crossed FROM students WHERE match IS NULL ORDER BY id;").fetchall(): 
            # Try to match them if it is possible     
            if checkPossibilityMatching(row, tutor_data):
                matched = True
                break
        # If no match is found, send email notification
        if not matched:
            send_email(email, "Standby", f"Hi {name},\n\nThank you for using the Peer Tutoring Management System.\n\nYou have not been assigned a peer yet. Please keep an eye on your inbox for an update.\n\nGood Luck!\nPeer Tutoring Management System")

    # close the database
    conn.commit()
    conn.close()

# The function to check the possibility of a match between a tutor and a student
def checkPossibilityMatching(student, tutor):
    # Open the database to read in data
    conn = sqlite3.connect("records.db")
    c = conn.cursor()

    # Check if the tutor and the student were not matched before
    if not (student[1]+student[3]+student[7]+f"{student[9]}" in tutor[10]):
        if not (tutor[1]+tutor[3]+tutor[7]+f"{tutor[9]}" in student[10]):
            # Check if the tutor and the student are in the same school
            if (student[9] == tutor[9]):
                # Check if the tutor and the student are available in the same period
                if (student[5] == tutor[5]):
                    # Check if the tutor and the student are in the same field
                    if ((student[3][0] == 'S' and tutor[3][0] == 'S') or (student[3][0] == 'C' and tutor[3][0] == 'C')):
                        # Check if the tutor and the student are in the same field and they have a proper experience for previous years
                        if(student[3][0] == 'S' and tutor[3][0] == 'S'):
                            if ((int (student [3][-2]) <= 2 and int (tutor[3][-2]) >=2 ) or (int ((student [3][-2])) == 1 and int (tutor[3][-2]) == 1)):
                                 # Match them
                                 matchingStudentTutor(student, tutor)
                                 conn.commit()
                                 conn.close()
                                 return True

                            elif (student[3][1] == tutor[3][1]):
                                # Match them
                                 matchingStudentTutor(student, tutor)
                                 conn.commit()
                                 conn.close()
                                 return True

                        # Check if the tutor and the student are in the same course
                        elif (student[3][1] == tutor[3][1]):
                             # Match them
                             matchingStudentTutor(student, tutor)
                             conn.commit()
                             conn.close()
                             return True
                    # Check if the tutor and the student are in the same field
                    elif (student[3][0] == tutor[3][0]): 
                        # Check if the tutor is in higher grade than the student
                        if (int(student[3][-2]) < int (tutor[3][-2])): 
                            # Match them
                            matchingStudentTutor(student, tutor)
                            conn.commit()
                            conn.close()
                            return True
                        # Check if the tutor is in same grade as the student
                        elif(int(student[3][-2]) == int (tutor[3][-2])): 
                            # Check if the tutor is in higher or equal speciality (college/university) than the student
                            if ((student[3][-1]) <= tutor[3][-1]): 
                                # Match them
                                matchingStudentTutor(student, tutor)
                                conn.commit()
                                conn.close()
                                return True

    # close the database         
    conn.commit()
    conn.close()
    return False

# The function to make a match between a tutor and a student
def matchingStudentTutor(student, tutor): 
    # Open the database to read in data
    conn = sqlite3.connect("records.db")
    c = conn.cursor()
    # Match them
    c.execute("UPDATE students SET match = ? WHERE id = ?;", (tutor[0], student[0]))
    c.execute("UPDATE tutors SET match = ? WHERE id = ?;", (student[0], tutor[0]))  
    conn.commit()
    # close the database
    conn.close()        
    # Send proper emails to inform the student and the tutor about their match
    send_email(student[7], "Tutor Found", f"Hi {student[1]}!\n\n" f"Thank you for using Peer Tutoring Management System!\n\n" f"Your tutor is {tutor[1]}.\nThe course {tutor[1]} is going to assist you with is {student[3]}.\n" f"You have been scheduled for {tutor[5]}.\n\n" f"Good Luck!\nPeer Tutoring Management System")
    send_email(tutor[7], "Peer Found", f"Hi {tutor[1]}!\n\n"f"Thank you for using Peer Tutoring Management System!\n" f"Your peer is {student[1]}.\nThe course {student[1]} needs assistance with is {student[3]}.\n" f"You have been scheduled for {tutor[5]}.\n\n" f"Good Luck!\nPeer Tutoring Management System")

# The function to create and send an email
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

# Enabling Debug Mode
if __name__ == "__main__":
    app.run(debug=True)

####################################################################################
######## The End
####################################################################################