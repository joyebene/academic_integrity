from flask import render_template
from flask_login import login_required, current_user

from app.reports import reports_bp
from app.models import Report, Course, Submission, Assignment


@reports_bp.route("/")
@login_required
def index():


    if current_user.role == "admin":

        # Admin sees everything

        reports = Report.query.order_by(
            Report.created_at.desc()
        ).all()



    elif current_user.role == "lecturer":

        # Lecturer only sees his courses

        lecturer = current_user.lecturer_profile


        reports = Report.query.join(
            Report.submission
        ).join(
            Submission.assignment
        ).join(
            Assignment.course
        ).filter(
            Course.lecturer_id == lecturer.id
        ).order_by(
            Report.created_at.desc()
        ).all()



    else:

        # Student only sees his reports

        student = current_user.student_profile


        reports = Report.query.join(
            Report.submission
        ).filter(
            Submission.student_id == student.id
        ).order_by(
            Report.created_at.desc()
        ).all()



    return render_template(
        "reports/index.html",
        reports=reports
    )