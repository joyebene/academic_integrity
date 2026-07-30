from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField, SelectField, SubmitField
from wtforms.validators import DataRequired


class AssignmentForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    description = TextAreaField("Description", validators=[DataRequired()])
    due_date = DateField("Due Date", validators=[DataRequired()])
    course_id = SelectField("Course", coerce=int,validators=[DataRequired()])


class ReviewSubmissionForm(FlaskForm):
    feedback = TextAreaField("Feedback")
    approve = SubmitField("Approve")