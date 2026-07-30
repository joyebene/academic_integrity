from flask import Blueprint

lecturers_bp = Blueprint('lecturers', __name__)

from app.lecturers import routes