from flask import Blueprint, render_template, request, jsonify, abort
from flask_login import login_required, current_user
from models import db
from models.jogging import Jogging
import json

jogging_bp = Blueprint("jogging", __name__)

@jogging_bp.route("/jogging/start")
@login_required
def start_jogging():
    if current_user.role not in ["player", "coach"]:
        abort(403)
    return render_template("jogging/start_jogging.html")

@jogging_bp.route("/jogging/save", methods=["POST"])
@login_required
def save_jogging():
    data = request.json

    jog = Jogging(
        user_id=current_user.id,
        role=current_user.role,
        distance_km=data["distance"],
        duration_min=data["duration"],
        avg_speed=data["speed"],
        calories=data["calories"],
        path=json.dumps(data["path"])
    )

    db.session.add(jog)
    db.session.commit()

    return jsonify({
        "status": "saved",
        "role": current_user.role
    })

@jogging_bp.route("/jogging/history/player")
@login_required
def jogging_history_player():
    if current_user.role != "player":
        abort(403)

    runs = Jogging.query.filter_by(
        user_id=current_user.id
    ).order_by(Jogging.created_at.desc()).all()

    return render_template(
        "jogging/jogging_history.html",
        runs=runs,
        role="player"
    )

@jogging_bp.route("/jogging/history/coach")
@login_required
def jogging_history_coach():
    if current_user.role != "coach":
        abort(403)

    runs = Jogging.query.filter_by(
        user_id=current_user.id
    ).order_by(Jogging.created_at.desc()).all()

    return render_template(
        "jogging/jogging_history.html",
        runs=runs,
        role="coach"
    )
