from flask import Flask, render_template, redirect, request, session, url_for, g, send_from_directory, after_this_request
from flask_session import Session
from database import get_db, close_db
from forms import CheckGrades, Login, RegistrationForm, Upload, NewAssignment, NewAnnouncement, UpdateGrade, NewStudent, NewLecturer, DeleteForm, AccountType, ModuleFilter
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import date
import os

#admin account/password: dgb, 123
#sample student account/password: ST01, 123
#sample lecturer account/password: L03, 123
#i have other entries that don't really contain information, so you can test the delete route

app = Flask(__name__)
app.config["SECRET_KEY"] = "key"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['UPLOAD_FOLDER'] = 'static/files/'
Session(app)
app.teardown_appcontext(close_db)

@app.before_request
def load_logged_in_user():
    g.user = session.get("user_id", None)
    if g.user:
        g.type = session.get("user_type", None)

def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            return redirect(url_for("login", next=request.url))
        return view(*args, **kwargs)
    return wrapped_view

#function that validates file by only allowing pdf and unique filenames
def validateFile (filename, dst):
    ext = filename.split(".")[1]
    if ext == "pdf":
        list = os.listdir(app.config['UPLOAD_FOLDER']+dst)
        if list != []:
            for file in list:
                if file == filename:
                    if session["user_type"] == "staff":
                        error = "Filename already exists"
                        break
                    elif session["user_type"] == "stdnt":
                        error = "Filename already exists. Add ID no. at the end to make it unique" 
                        break
                else:
                    error = ""
                    break
        else:
            error = ""
        return error
    else:
        error = "Only PDFs are accepted"
        return error

@app.route("/") #checks after request if g.user and then g.user_type exists then sends to respective homepage
def home_page():
    @after_this_request
    def check_user(response):
        if g.user:
            if g.type == "admin":
                return redirect(url_for("admin"))
            elif g.type == "staff":
                return redirect(url_for("staff"))
            elif g.type == "stdnt":
                return redirect(url_for("student"))
        return response
    return render_template("index.html")

@app.route("/login", methods=["GET","POST"]) #sends users to a different homepage depending on their user type
def login():
    form = Login()
    if form.validate_on_submit():
        id = form.id.data
        password = form.password.data
        db = get_db()
        user =  db.execute("""SELECT * FROM users WHERE id=?""", (id,)).fetchone()
        if user is None:
            form.id.errors.append("No such username")
        elif not check_password_hash(user["password"], password):
            form.password.errors.append("Passwords don't match")
        else:
            if user["type"] == "admin":
                session.clear()
                session["user_id"] = id
                session["user_type"] = user["type"]
                return redirect(url_for("admin"))
            elif user["type"] == "staff":
                session.clear()
                session["user_id"] = id
                session["user_type"] = user["type"]
                return redirect(url_for("staff"))
            elif user["type"] == "stdnt":
                session.clear()
                session["user_id"] = id
                session["user_type"] = user["type"]
                return redirect(url_for("student"))
    return render_template("login.html", form=form)
    
@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect(url_for("home_page"))

#admin
@app.route("/admin") 
@login_required
def admin():
    return render_template("admin.html")

@app.route ("/all_students")
@login_required
def all_students():
    db = get_db()
    students = db.execute("""SELECT * FROM students;""").fetchall()
    return render_template("all_students.html", students=students, caption="All Students")

@app.route ("/all_lecturers")
@login_required
def all_lecturers():
    db = get_db()
    lecturers = db.execute("""SELECT * FROM lecturers;""").fetchall()
    return render_template("all_lecturers.html", lecturers=lecturers, caption="All Lecturers")

@app.route("/register", methods=(["GET", "POST"]))
@login_required
def register(): 
    form = RegistrationForm() 
    if form.validate_on_submit(): 
        id = form.id.data
        password = form.password.data 
        password2 = form.password2.data 
        type = form.type.data
        db = get_db() 
        conflict_user = db.execute( """SELECT * 
                                   FROM users WHERE id = ?;""", (id,)).fetchone() 
        if conflict_user is not None: 
            form.id.errors.append("User name already taken") 
        else:
            db.execute(""" INSERT INTO users (id, password, type) 
                       VALUES (?, ?, ?);""", (id, generate_password_hash(password), type)) 
            db.commit()
            return redirect("/admin")
    return render_template("register.html", form=form) 

@app.route("/new_student", methods=["GET","POST"]) #adds new student into students table
@login_required
def new_student():
    form = NewStudent()
    message = ""
    if form.validate_on_submit():
        db = get_db()
        id = form.id.data
        fName = form.first_name.data
        lName = form.last_name.data
        course = form.course.data
        year = form.year.data
        modules = form.modules.data
        db.execute("""INSERT INTO students
                    VALUES (?, ?, ?, ?, ?)""", (id,fName,lName,course,year))
        db.commit()
        for module in modules:
            db.execute("""INSERT INTO enrollment
                          VALUES (?, ?)""", (id, module))
            db.commit()
        message = "Student added"
    return render_template("new_student.html", form=form, message=message)

@app.route("/new_lecturer", methods=["GET","POST"]) #adds new lecturer to lecturers table
@login_required
def new_lecturer():
    form = NewLecturer()
    message = ""
    if form.validate_on_submit():
        db = get_db()
        id = form.id.data
        fName = form.first_name.data
        lName = form.last_name.data
        modules = form.modules.data
        print(modules)
        db.execute("""INSERT INTO lecturers
                      VALUES (?, ?, ?)""", (id,fName,lName))
        db.commit()
        for module in modules:
            db.execute("""INSERT INTO teaches
                          VALUES (?, ?)""", (id, module))
            db.commit()
        message = "Lecturer added"
    return render_template("new_lecturer.html", form=form, message=message)

@app.route("/delete", methods=["GET", "POST"]) #deletes selected ID from the users table and students or lecturers depending on type
@login_required
def delete_user():
    form1 = AccountType()
    form2 = DeleteForm()
    g.second_form = False
    if form1.validate_on_submit():
        account = form1.account.data
        db = get_db()
        ids = db.execute("""SELECT * FROM users WHERE type=?;""",(account,)).fetchall()
        for id in ids:
            form2.id.choices.append(id["id"])
        g.second_form = True
        if form2.validate_on_submit():
            id = form2.id.data
            db.execute("""DELETE FROM users WHERE id=?""",(id,))
            db.commit()
            if account == "stdnt":
                db.execute("""DELETE FROM students WHERE id=?""",(id,))
                db.commit()
                return redirect(url_for("admin"))
            elif account == "staff":
                db.execute("""DELETE FROM lecturers WHERE id=?""",(id,))
                db.commit()
                return redirect(url_for("admin"))
    return render_template("delete_user.html", form1=form1, form2=form2)

#student
@app.route("/student", methods=["GET", "POST"]) #retrieves all the dbs related to student and compares todays date with the due date of assignment (to check if overdue)
@login_required
def student():
    module = '%'
    db = get_db()
    announcements=db.execute("""SELECT * 
                                    FROM announcements 
                                    WHERE module IN (SELECT modules 
                                                    FROM enrollment 
                                                    WHERE std_id=?)""", (session["user_id"],)).fetchall()
    modules = db.execute("""SELECT * FROM enrollment WHERE std_id=?""", (session["user_id"],)).fetchall()
    g.date = date.today()
    due = db.execute("""SELECT module_id, name, due_date
                        FROM assignments_due
                        WHERE id NOT IN (SELECT id 
                                         FROM assignments_submitted 
                                         WHERE std_id=?);""", (session["user_id"],)).fetchall()
    form = ModuleFilter()
    for module in modules:
        form.module.choices.append((module["modules"]))
    if form.validate_on_submit():
        module = form.module.data
        announcements = db.execute("""SELECT * 
                                    FROM announcements 
                                    WHERE module IN (SELECT modules 
                                                    FROM enrollment 
                                                    WHERE std_id=? AND module LIKE ?)""", (session["user_id"],module)).fetchall()
    return render_template("student_page.html", form=form, modules=modules, due=due, announcements=announcements)

@app.route("/grades/<module>") 
@login_required
def grades(module):
    db = get_db()
    grades = db.execute("""SELECT type, semester, grade FROM grades WHERE grade!='U' AND module=? AND std_id=?""", (module,session["user_id"])).fetchall()
    return render_template("grades.html", grades=grades, module=module)

@app.route("/assignments/<module>", methods=["GET", "POST"]) 
@login_required
def assignment(module):
    db = get_db()
    assignments = db.execute("SELECT * FROM assignments_due WHERE module_id=?", (module,)).fetchall()
    return render_template("assignment.html", module=module, assignments=assignments)

@app.route('/download/<path:name>') #
@login_required
def download(name):
    dst = "assignments_due/"
    return send_from_directory(directory=app.config['UPLOAD_FOLDER']+dst, path=name, as_attachment=True)

@app.route('/upload/<id>', methods=["GET", "POST"]) #uploads assignment 
@login_required
def upload_file(id):
    message = ""
    error = ""
    form = Upload()
    db = get_db()
    if form.validate_on_submit():
        file = request.files['file']
        dst = "assignments_submitted/"
        error = validateFile(secure_filename(file.filename), dst)
        if error == "":
            file_path = os.path.join(app.config['UPLOAD_FOLDER']+dst,secure_filename(file.filename))
            file.save(file_path)
            db.execute("""INSERT INTO assignments_submitted VALUES (?, ?, ?)""", (session["user_id"], id, secure_filename(file.filename)))
            db.commit()
            message = "File uploaded"
    return render_template("upload.html", form=form, error=error, id=id, message=message)

#staff
@app.route("/staff")
@login_required
def staff():
    return render_template("staff_page.html")

@app.route("/check_grades", methods=["GET", "POST"]) #
@login_required
def check_grades():
    form = CheckGrades()
    students = None
    db = get_db()
    modules = db.execute("""SELECT * FROM teaches WHERE lec_id=?""", (session["user_id"],)).fetchall()
    for module in modules:
        form.module.choices.append((module["module"]))
    if form.validate_on_submit():
        id = form.id.data
        if not id:
            id = '%'
        name = form.name.data
        if not name:
            name = '%'
        else:
            name.capitalize()
        module = form.module.data
        grade = form.grade.data
        semester = form.semester.data
        type = form.type.data
        if type == '_':
            type = '%'
        students = db.execute("""SELECT s.*, g.semester, g.module, g.type, g.grade
                                 FROM students AS s JOIN grades AS g
                                 ON s.id = g.std_id
                                 WHERE g.module=? AND g.grade LIKE ? AND g.semester LIKE ? 
                                       AND g.type LIKE ? AND s.id LIKE ? 
                                       AND (s.first_name LIKE ? OR s.last_name LIKE ?);""", (module,grade,semester,type,id,name,name)).fetchall()
    return render_template("check_grades.html", form=form, students=students, caption="Students enrolled in %s" % module)

@app.route("/add_assignment", methods=["GET", "POST"]) #
@login_required
def new_assignment():
    error = ""
    message = ""
    form = NewAssignment()
    db = get_db()
    modules = db.execute("""SELECT * FROM teaches WHERE lec_id=?""", (session["user_id"],)).fetchall()
    for module in modules:
        form.module.choices.append((module["module"]))
    if form.validate_on_submit():
        file = request.files['file']
        name = form.name.data
        module = form.module.data
        date = form.date.data
        dst = "assignments_due/"
        error = validateFile(secure_filename(file.filename), dst)
        if error == "":
            file_path = os.path.join(app.config['UPLOAD_FOLDER']+dst,secure_filename(file.filename))
            file.save(file_path)
            db.execute("""INSERT INTO assignments_due (module_id, name, due_date, file_path) VALUES (?, ?, ?, ?)""", (module,name,date,secure_filename(file.filename)))
            db.commit()
            message = "Assignment Added"
    return render_template("add_assignment.html", form=form, message=message, error=error)

@app.route("/add_announcements", methods=["GET", "POST"]) #adds new announcement, appears in the student dashboard if student takes that module
@login_required
def new_announcement():
    message = ""
    form = NewAnnouncement()
    db = get_db()
    modules = db.execute("""SELECT * FROM teaches WHERE lec_id=?""", (session["user_id"],)).fetchall()
    for module in modules:
        form.module.choices.append((module["module"]))
    if form.validate_on_submit():
        module = form.module.data
        text = form.message.data
        db.execute("""INSERT INTO announcements (module, message, date)
                      VALUES (?, ?, ?)""", (module, text, date.today()))
        db.commit()
        message = "Announcement added"
    return render_template("add_announcement.html", form=form, message=message)
    

@app.route("/update/<id>/<semester>/<type>", methods=["GET", "POST"]) #updates the grade of the row selected
@login_required
def update_grades(id, semester, type):
    form = UpdateGrade()
    message = ""
    if form.validate_on_submit():
        db = get_db()
        newGrade = form.new_grade.data
        db.execute("""UPDATE grades
                    SET grade=?
                    WHERE std_id=? AND semester=? AND type=?""",(newGrade,id,semester,type))
        db.commit()
        message = "Grade has been updated"
    return render_template("update_grade.html", form=form, message=message)
