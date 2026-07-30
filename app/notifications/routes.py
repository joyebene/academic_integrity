from flask import render_template
from flask_login import login_required, current_user

from app.notifications import notifications_bp
from app.models import Notification


@notifications_bp.route("/")
@login_required
def index():

    notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Notification.created_at.desc()
    ).all()


    return render_template(
        "notifications/index.html",
        notifications=notifications,
    )