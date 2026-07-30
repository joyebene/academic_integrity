from flask import render_template, redirect, url_for, flash, request, send_file, current_app
from flask_login import login_required, current_user

from app import db
from app.lecturers import lecturers_bp
from app.models import Assignment, Course, Notification, Report, Submission
from app.forms.lecturer import AssignmentForm
from app.models import AIAnalysis, SuspiciousSubmission
from app.forms.course import CourseForm
from app.forms.common import DeleteForm
from app.forms.lecturer import ReviewSubmissionForm
import os

@lecturers_bp.route("/dashboard")
@login_required
def dashboard():

    if current_user.role != "lecturer":
        flash("Access denied.", "danger")
        return redirect(url_for("auth.login"))

    lecturer = current_user.lecturer_profile

    assignments = Assignment.query.all()

    submissions = Submission.query.order_by(
        Submission.submitted_at.desc()
    ).limit(10).all()

    stats = {
        "assignments": Assignment.query.count(),
        "submissions": Submission.query.count(),
        "processing": Submission.query.filter_by(status="processing").count(),
    }

    analytics = {
        "high_plagiarism": AIAnalysis.query.filter(
            AIAnalysis.plagiarism_score >= 50
        ).count(),

        "high_ai": AIAnalysis.query.filter(
            AIAnalysis.ai_generated_score >= 50
        ).count(),

        "flagged": SuspiciousSubmission.query.count(),
}

    notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Notification.created_at.desc()
    ).limit(5).all()

    return render_template(
        "lecturers/dashboard.html",
        lecturer=lecturer,
        assignments=assignments,
        submissions=submissions,
        stats=stats,
        analytics=analytics,
        notifications=notifications,
    )


# ===============================
# Assignment Pages
# ===============================

@lecturers_bp.route("/assignments")
@login_required
def assignments():

    assignments = Assignment.query.join(Course).filter(
        Course.lecturer_id == current_user.lecturer_profile.id
    ).all()

    stats = {
        "total_assignments": len(assignments),
        "active_assignments": sum(1 for a in assignments if a.is_active),
        "inactive_assignments": sum(1 for a in assignments if not a.is_active),
    }


    return render_template(
        "lecturers/assignments.html",
        assignments=assignments,
        stats=stats,

    )


@lecturers_bp.route("/assignments/create", methods=["GET", "POST"])
@login_required
def create_assignment():

    form = AssignmentForm()

    # Load only this lecturer's courses
    form.course_id.choices = [
        (course.id, f"{course.code} - {course.title}")
        for course in Course.query.filter_by(
            lecturer_id=current_user.lecturer_profile.id
        ).all()
    ]

    if form.validate_on_submit():

        assignment = Assignment(
            title=form.title.data,
            description=form.description.data,
            due_date=form.due_date.data,
            course_id=form.course_id.data,
            is_active=True
        )

        db.session.add(assignment)
        db.session.commit()

        flash("Assignment created successfully.", "success")

        return redirect(url_for("lecturers.assignments"))

    return render_template(
        "lecturers/create_assignment.html",
        form=form
    )


@lecturers_bp.route("/assignments/<int:id>")
@login_required
def view_assignment(id):

    assignment = Assignment.query.get_or_404(id)

    return render_template(
        "lecturers/view_assignment.html",
        assignment=assignment
    )


@lecturers_bp.route("/assignments/<int:id>/edit",
                     methods=["GET", "POST"])
@login_required
def edit_assignment(id):

    assignment = Assignment.query.get_or_404(id)

    form = AssignmentForm(obj=assignment)

    if form.validate_on_submit():

        assignment.title = form.title.data
        assignment.description = form.description.data
        assignment.due_date = form.due_date.data

        db.session.commit()

        flash("Assignment updated successfully.", "success")

        return redirect(
            url_for(
                "lecturers.view_assignment",
                id=assignment.id
            )
        )

    return render_template(
        "lecturers/edit_assignment.html",
        form=form,
        assignment=assignment
    )


@lecturers_bp.route("/assignments/<int:id>/delete",
                     methods=["POST"])
@login_required
def delete_assignment(id):

    assignment = Assignment.query.get_or_404(id)

    db.session.delete(assignment)
    db.session.commit()

    flash("Assignment deleted successfully.", "success")

    return redirect(url_for("lecturers.assignments"))

@lecturers_bp.route("/submissions")
@login_required
def submissions():

    if current_user.role != "lecturer":
        flash("Access denied.", "danger")
        return redirect(url_for("auth.login"))

    submissions = Submission.query.order_by(
        Submission.submitted_at.desc()
    ).all()

    return render_template(
        "lecturers/submissions.html",
        submissions=submissions
    )

@lecturers_bp.route("/submissions/<int:id>", methods=["GET", "POST"])
@login_required
def view_submission(id):

    if current_user.role != "lecturer":
        flash("Access denied.", "danger")
        return redirect(url_for("auth.login"))

    submission = Submission.query.get_or_404(id)

    analysis = AIAnalysis.query.filter_by(
        submission_id=submission.id
    ).first()

    suspicious = SuspiciousSubmission.query.filter_by(
        submission_id=submission.id
    ).first()

    form = ReviewSubmissionForm()

    if request.method == "POST":

        action = request.form.get("action")
        feedback = request.form.get("feedback")

        # -----------------------------
        # APPROVE SUBMISSION
        # -----------------------------
        if action == "approve":

            submission.status = "approved"

            # Remove suspicious flag if it exists
            if suspicious:
                db.session.delete(suspicious)

            # Notify student
            notification = Notification(
                user_id=submission.student.user.id,
                title="Submission Approved",
                message=f'Your submission for "{submission.assignment.title}" has been approved.',
                type="success",
                link=f"/students/submission/{submission.id}"
            )

            db.session.add(notification)

            # Save report
            report = Report.query.filter_by(
                submission_id=submission.id
            ).first()

            if not report:
                report = Report(
                    submission_id=submission.id,
                    generated_by=current_user.id,
                    report_type="AI Analysis Report",
                    plagiarism_score=analysis.plagiarism_score if analysis else 0,
                    ai_score=analysis.ai_generated_score if analysis else 0,
                    report_path=""
                )
                db.session.add(report)

            db.session.commit()

            flash("Submission approved successfully.", "success")

            return redirect(
                url_for("lecturers.view_submission", id=id)
            )

        # -----------------------------
        # FLAG SUBMISSION
        # -----------------------------
        elif action == "flag":

            submission.status = "flagged"

            if not suspicious:

                suspicious = SuspiciousSubmission(
                    submission_id=submission.id,
                    reason=feedback or "Flagged by lecturer",
                    severity="high"
                )

                db.session.add(suspicious)

            # Notify student
            notification = Notification(
                user_id=submission.student.user.id,
                title="Submission Flagged",
                message=f'Your submission for "{submission.assignment.title}" has been flagged for review.',
                type="warning",
                link=f"/students/submission/{submission.id}"
            )

            db.session.add(notification)

            db.session.commit()

            flash("Submission flagged successfully.", "warning")

            return redirect(
                url_for("lecturers.view_submission", id=id)
            )

        elif action == "report":

            report = Report.query.filter_by(
                submission_id=submission.id
            ).first()

            if not report:
                report = Report(
                    submission_id=submission.id,
                    generated_by=current_user.id,
                    report_type="AI Analysis Report",
                    plagiarism_score=analysis.plagiarism_score if analysis else 0,
                    ai_score=analysis.ai_generated_score if analysis else 0,
                    report_path=""
                )

                db.session.add(report)
                db.session.commit()

            flash("Report generated successfully.", "success")

            return redirect(
                url_for("reports.index")
            )

    return render_template(
        "lecturers/view_submission.html",
        submission=submission,
        analysis=analysis,
        suspicious=suspicious,
        form=form
    )

@lecturers_bp.route("/courses")
@login_required
def courses():

    lecturer = current_user.lecturer_profile

    courses = Course.query.filter_by(
        lecturer_id=lecturer.id
    ).order_by(Course.created_at.desc()).all()

    delete_form = DeleteForm()

    return render_template(
        "lecturers/courses.html",
        courses=courses,
        delete_form=delete_form
    )

@lecturers_bp.route("/courses/create", methods=["GET", "POST"])
@login_required
def create_course():

    form = CourseForm()

    if form.validate_on_submit():

        course = Course(
            code=form.code.data.upper(),
            title=form.title.data,
            description=form.description.data,
            lecturer_id=current_user.lecturer_profile.id
        )

        db.session.add(course)
        db.session.commit()

        flash("Course created successfully.", "success")

        return redirect(url_for("lecturers.courses"))

    return render_template(
        "lecturers/create_course.html",
        form=form
    )

@lecturers_bp.route("/courses/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_course(id):

    course = Course.query.get_or_404(id)

    if course.lecturer_id != current_user.lecturer_profile.id:
        flash("Access denied.", "danger")
        return redirect(url_for("lecturers.courses"))

    form = CourseForm(obj=course)

    if form.validate_on_submit():

        course.code = form.code.data.upper()
        course.title = form.title.data
        course.description = form.description.data

        db.session.commit()

        flash("Course updated successfully.", "success")

        return redirect(url_for("lecturers.courses"))

    return render_template(
        "lecturers/edit_course.html",
        form=form,
        course=course
    )

@lecturers_bp.route("/courses/<int:id>/delete", methods=["POST"])
@login_required
def delete_course(id):

    course = Course.query.get_or_404(id)

    if course.lecturer_id != current_user.lecturer_profile.id:
        flash("Access denied.", "danger")
        return redirect(url_for("lecturers.courses"))

    db.session.delete(course)
    db.session.commit()

    flash("Course deleted successfully.", "success")

    return redirect(url_for("lecturers.courses"))


@lecturers_bp.route("/submissions/<int:id>/download")
@login_required
def download_submission(id):
    if current_user.role not in ["lecturer", "admin"]:
        flash("Access denied.", "danger")
        return redirect(url_for("auth.login"))

    submission = Submission.query.get_or_404(id)

    project_root = os.path.abspath(os.path.join(current_app.root_path, ".."))

    file_path = os.path.join(project_root, submission.file_path)

    return send_file(
        file_path,
        as_attachment=True,
        download_name=submission.original_filename,
    )


@lecturers_bp.route("/flagged-submissions")
@login_required
def flagged_submissions():

    if current_user.role != "lecturer":
        flash("Access denied.", "danger")
        return redirect(url_for("auth.login"))

    lecturer = current_user.lecturer_profile

    suspicious_submissions = (
        SuspiciousSubmission.query
        .join(Submission)
        .join(Assignment)
        .join(Course)
        .filter(Course.lecturer_id == lecturer.id)
        .order_by(SuspiciousSubmission.created_at.desc())
        .all()
    )

    return render_template(
        "lecturers/flagged_submissions.html",
        suspicious_submissions=suspicious_submissions
    )