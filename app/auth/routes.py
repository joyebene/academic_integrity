from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime

from app import db
from app.auth import auth_bp
from app.models import User, Student, Lecturer, SystemLog
from app.forms.auth import LoginForm, RegistrationForm



@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    print("STEP 1")

    if current_user.is_authenticated:
        print("STEP 2")

        if current_user.role == "student":
            return redirect(url_for("students.dashboard"))
        elif current_user.role == "lecturer":
            return redirect(url_for("lecturers.dashboard"))
        else:
            return redirect(url_for("admin.dashboard"))

    print("STEP 3")

    form = LoginForm()

    print("STEP 4")
    print(form.csrf_token)

    if form.validate_on_submit():
        print("STEP 5")

        user = User.query.filter_by(email=form.email.data).first()
        print("User found:", user)

        if user:
            print("Password correct:", user.check_password(form.password.data))
            print("Active:", user.is_active)
            print("Role:", user.role)

        if user and user.check_password(form.password.data):

            if not user.is_active:
                flash(
                    "Your account has been deactivated. Please contact administrator.",
                    "danger",
                )
                return render_template("auth/login.html", form=form)

            login_user(user, remember=form.remember_me.data)

            user.last_login = datetime.utcnow()

            log = SystemLog(
                user_id=user.id,
                action="LOGIN",
                description=f"User {user.email} logged in",
                ip_address=request.remote_addr,
                user_agent=request.headers.get("User-Agent"),
            )

            db.session.add(log)
            db.session.commit()

            flash("Login successful!", "success")

            if user.role == "student":
                return redirect(url_for("students.dashboard"))
            elif user.role == "lecturer":
                return redirect(url_for("lecturers.dashboard"))
            else:
                return redirect(url_for("admin.dashboard"))

        flash("Invalid email or password.", "danger")

    return render_template("auth/login.html", form=form)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if current_user.is_authenticated:
        if current_user.role == "student":
            return redirect(url_for("students.dashboard"))
        elif current_user.role == "lecturer":
            return redirect(url_for("lecturers.dashboard"))
        else:
            return redirect(url_for("admin.dashboard"))

    form = RegistrationForm()

    if form.validate_on_submit():
      print("Form validated")
    else:
      print("Validation failed")
      print(form.errors)

    if form.validate_on_submit():

        if User.query.filter_by(email=form.email.data).first():
            flash("Email already registered.", "danger")
            return render_template("auth/register.html", form=form)

        if User.query.filter_by(username=form.username.data).first():
            flash("Username already taken.", "danger")
            return render_template("auth/register.html", form=form)

        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            role=form.role.data,
        )

        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        if form.role.data == "student":
            student = Student(
                user_id=user.id,
                matric_number=form.matric_number.data,
                level=form.level.data,
                program=form.program.data,
            )

            db.session.add(student)

        elif form.role.data == "lecturer":
            lecturer = Lecturer(
                user_id=user.id,
                staff_id=form.staff_id.data,
                specialization=form.specialization.data,
            )

            db.session.add(lecturer)

        db.session.commit()

        flash(
            f"Registration successful! Welcome {user.first_name}!",
            "success",
        )

        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():

    log = SystemLog(
        user_id=current_user.id,
        action="LOGOUT",
        description=f"User {current_user.email} logged out",
        ip_address=request.remote_addr,
        user_agent=request.headers.get("User-Agent"),
    )

    db.session.add(log)
    db.session.commit()

    logout_user()

    flash("You have been logged out.", "info")

    return redirect(url_for("auth.login"))


@auth_bp.route("/profile")
@login_required
def profile():
    return render_template("auth/profile.html", user=current_user)


@auth_bp.route("/profile/update", methods=["POST"])
@login_required
def update_profile():

    user = current_user

    user.first_name = request.form.get("first_name", user.first_name)
    user.last_name = request.form.get("last_name", user.last_name)
    user.department = request.form.get("department", user.department)
    user.faculty = request.form.get("faculty", user.faculty)

    if request.form.get("password"):
        user.set_password(request.form.get("password"))

    db.session.commit()

    flash("Profile updated successfully!", "success")

    return redirect(url_for("auth.profile"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":

        email = request.form.get("email")
        user = User.query.filter_by(email=email).first()

        if user:
            # TODO: Implement password reset email
            flash(
                "Password reset instructions have been sent to your email.",
                "info",
            )
        else:
            flash("Email not found.", "danger")

        return redirect(url_for("auth.login"))

    return render_template("auth/forgot_password.html")