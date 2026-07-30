from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import TextAreaField, SubmitField
from wtforms.validators import Optional

class SubmissionForm(FlaskForm):
    comments = TextAreaField("Comments", validators=[Optional()])
    file = FileField(
        "Assignment File",
        validators=[
            FileRequired(),
            FileAllowed(["pdf", "doc", "docx", "zip"], "Unsupported file type."),
        ],
    )
    submit = SubmitField("Submit Assignment")