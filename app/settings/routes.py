from flask import Blueprint, render_template
from flask_login import login_required, current_user

from app.settings import settings_bp

@settings_bp.route("/")
@login_required
def index():

    return render_template(
        "settings/index.html",
        user=current_user
    )