
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, SelectField, IntegerField, BooleanField, TextAreaField
from wtforms.validators import (
    DataRequired,
    Email,
    Length,
    EqualTo,
    Regexp,
    Optional,
    NumberRange,
    ValidationError
)
from app.models import User

class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=50),
        Regexp(r'^[a-zA-Z0-9_]+$', message='Username can only contain letters, numbers, and underscores')
    ])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    role = SelectField('Role', choices=[
        ('student', 'Student'),
        ('lecturer', 'Lecturer')
    ], validators=[DataRequired()])
    
    # Student-specific fields
    matric_number = StringField('Matric Number', validators=[
        Optional(),
        Length(max=20)
    ])
    level = IntegerField('Level', validators=[Optional(), NumberRange(min=100, max=500)])
    program = StringField('Program', validators=[Optional(), Length(max=100)])
    
    # Lecturer-specific fields
    staff_id = StringField('Staff ID', validators=[
        Optional(),
        Length(max=20)
    ])
    specialization = StringField('Specialization', validators=[Optional(), Length(max=100)])
    
    def validate_role(self, field):
        if field.data == "student" and not self.matric_number.data:
            raise ValidationError("Matric Number is required for students")

        if field.data == "lecturer" and not self.staff_id.data:
            raise ValidationError("Staff ID is required for lecturers")


class AssignmentForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description')
    instructions = TextAreaField('Instructions')
    due_date = StringField('Due Date', validators=[DataRequired()])
    max_score = IntegerField('Max Score', validators=[DataRequired(), NumberRange(min=1, max=100)])
    course_id = SelectField('Course', validators=[DataRequired()], coerce=int)