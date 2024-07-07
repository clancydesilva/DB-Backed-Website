from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, DateField, PasswordField, SelectField, FileField, TextAreaField, SelectMultipleField
from wtforms.validators import InputRequired, EqualTo, Length

class CheckGrades (FlaskForm):
    id = StringField("Type in an ID: ")
    name = StringField("Type in a Name: ")
    module = SelectField("Module:", choices=[])
    grade = SelectField("Grade:", choices=["_", "U","A", "B", "C", "D", "E", "F"], default="_")
    semester = SelectField("Semester: ", choices=["_","1","2"], default="_")
    type = SelectField("Type: ", choices=["_","Mid-term", "Quiz", "Finals"], default="_")
    submit = SubmitField("Submit")

class Login (FlaskForm):
    id = StringField("Enter your user ID:", validators=[InputRequired()])
    password = PasswordField("Enter your password:", validators=[InputRequired()])
    submit = SubmitField("Submit")

class RegistrationForm(FlaskForm):
    id = StringField("Enter a username:", validators=[InputRequired()])
    password = PasswordField("Enter a password:", validators=[InputRequired()])
    password2 = PasswordField("Enter the same password again", validators=[EqualTo("password"), InputRequired()])
    type = SelectField("Choose account type:", choices=["admin", "staff", "stdnt"], validators=[InputRequired()])
    submit = SubmitField("Submit")

class Upload (FlaskForm):
    file = FileField("Upload File")
    submit = SubmitField("Upload")

class NewAssignment (FlaskForm):
    name = StringField("Name of Assignment:", validators=[InputRequired()])
    module = SelectField ("Select Module:", choices=[])
    date = DateField("Due Date:")
    file = FileField("Choose File:")
    submit = SubmitField("Submit")

class NewAnnouncement(FlaskForm):
    module = SelectField ("Select Module:", choices=[])
    message = TextAreaField("Enter Announcement:", validators=[InputRequired()])
    submit = SubmitField("Submit")

class UpdateGrade(FlaskForm):
    new_grade = SelectField("New Grade:", choices=["U","A", "B", "C", "D", "E", "F"])
    submit = SubmitField("Submit")

class NewStudent (FlaskForm):
    id = StringField("Enter ID Number: ", validators=[InputRequired()])
    first_name = StringField("First Name: ", validators=[InputRequired()])
    last_name = StringField("Last Name: ")
    course = StringField("Course: ",validators=[InputRequired()])
    year = StringField("Year: ", validators=[Length(1,1), InputRequired()]) 
    modules = SelectMultipleField("Select Module Taught: ", choices=["CC001", "CC002", "CC003", "CC004", "CC005", "CC006"])
    submit = SubmitField("Submit")

class NewLecturer (FlaskForm):
    id = StringField("Enter ID Number: ", validators=[InputRequired()])
    first_name = StringField("First Name: ", validators=[InputRequired()])
    last_name = StringField("Last Name: ")
    modules = SelectMultipleField("Select Module Taught: ", choices=["CC001", "CC002", "CC003", "CC004", "CC005", "CC006"])
    submit = SubmitField("Submit")

class AccountType (FlaskForm):
    account = SelectField("Select Account Type: ", choices=["stdnt", "staff"])
    submit = SubmitField("Submit")

class DeleteForm (FlaskForm):
    id = SelectField("Select ID: ", choices=[])
    submit = SubmitField("Delete")

class ModuleFilter(FlaskForm):
    module = SelectField("Filter by Module: ", choices=[])
    submit = SubmitField("Submit")