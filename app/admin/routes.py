from flask import render_template, redirect, url_for, flash, current_app, send_file
from flask_login import login_required, current_user
from app.admin import admin_bp
from app.models import (
    User,
    Student,
    Lecturer,
    Assignment,
    Submission,
    Notification,
    Course,
    SystemLog,
    SuspiciousSubmission,
)
import os


@admin_bp.route("/dashboard")
@login_required
def dashboard():

    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("auth.login"))

    total_submissions = Submission.query.count()
    flagged = SuspiciousSubmission.query.count()

    stats = {
        "total_users": User.query.count(),
        "students": Student.query.count(),
        "lecturers": Lecturer.query.count(),
        "courses": Course.query.count(),
        "assignments": Assignment.query.count(),
        "submissions": total_submissions,
        "total_submissions": total_submissions,
        "flagged_percent": round(
            (flagged / total_submissions * 100), 1
        ) if total_submissions else 0,
    }

    recent_users = (
        User.query.order_by(User.created_at.desc())
        .limit(5)
        .all()
    )

    notifications = (
        Notification.query.filter_by(user_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(5)
        .all()
    )

    system_logs = (
        SystemLog.query.order_by(SystemLog.created_at.desc())
        .limit(10)
        .all()
    )

    # Temporary settings until you create a Settings model
    settings = {
        "plagiarism_threshold": 60,
        "ai_threshold": 60,
        "max_file_size": 10,
        "allow_resubmission": True,
    }

    return render_template(
        "admin/dashboard.html",
        stats=stats,
        system_stats=stats,
        recent_users=recent_users,
        notifications=notifications,
        settings=settings,
        system_logs=system_logs,
    )


@admin_bp.route("/users")
@login_required
def users():

    if current_user.role != "admin":
        flash("Access denied", "danger")
        return redirect(url_for("auth.login"))


    users = User.query.order_by(
        User.created_at.desc()
    ).all()


    return render_template(
        "admin/users.html",
        users=users
    )

@admin_bp.route("/settings")
@login_required
def settings():
    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("auth.login"))

    return render_template("admin/settings.html")


# ==========================================
# STUDENTS
# ==========================================

@admin_bp.route("/students")
@login_required
def students():

    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("auth.login"))

    students = Student.query.order_by(Student.id.desc()).all()

    return render_template(
        "admin/students.html",
        students=students
    )


# ==========================================
# LECTURERS
# ==========================================

@admin_bp.route("/lecturers")
@login_required
def lecturers():

    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("auth.login"))

    lecturers = Lecturer.query.order_by(Lecturer.id.desc()).all()

    return render_template(
        "admin/lecturers.html",
        lecturers=lecturers
    )


# ==========================================
# COURSES
# ==========================================

@admin_bp.route("/courses")
@login_required
def courses():

    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("auth.login"))

    courses = (
        Course.query
        .order_by(Course.created_at.desc())
        .all()
    )

    return render_template(
        "admin/courses.html",
        courses=courses
    )


# ==========================================
# ASSIGNMENTS
# ==========================================

@admin_bp.route("/assignments")
@login_required
def assignments():

    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("auth.login"))

    assignments = (
        Assignment.query
        .order_by(Assignment.created_at.desc())
        .all()
    )

    return render_template(
        "admin/assignments.html",
        assignments=assignments
    )


# ==========================================
# SUBMISSIONS
# ==========================================

@admin_bp.route("/submissions")
@login_required
def submissions():

    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("auth.login"))

    submissions = (
        Submission.query
        .order_by(Submission.submitted_at.desc())
        .all()
    )

    return render_template(
        "admin/submissions.html",
        submissions=submissions
    )


@admin_bp.route('/submission/<int:id>')
@login_required
def view_submission(id):
    submission = Submission.query.get_or_404(id)
    
    
    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("auth.login"))

    
    return render_template('admin/view_submission.html', submission=submission)



# ==========================================
# FLAGGED SUBMISSIONS
# ==========================================

@admin_bp.route("/flagged-submissions")
@login_required
def flagged_submissions():

    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("auth.login"))

    flagged = (
        SuspiciousSubmission.query
        .order_by(SuspiciousSubmission.created_at.desc())
        .all()
    )

    return render_template(
        "admin/flagged_submissions.html",
        flagged_submissions=flagged
    )


# ==========================================
# SYSTEM LOGS
# ==========================================

@admin_bp.route("/logs")
@login_required
def logs():

    if current_user.role != "admin":
        flash("Access denied.", "danger")
        return redirect(url_for("auth.login"))

    logs = (
        SystemLog.query
        .order_by(SystemLog.created_at.desc())
        .all()
    )

    return render_template(
        "admin/logs.html",
        logs=logs
    )


@admin_bp.route("/submissions/<int:id>/download")
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