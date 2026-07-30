from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired


class CourseForm(FlaskForm):
    code = StringField(
        "Course Code",
        validators=[DataRequired()]
    )

    title = StringField(
        "Course Title",
        validators=[DataRequired()]
    )

    description = TextAreaField(
        "Description"
    )