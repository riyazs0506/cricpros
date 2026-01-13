import io
import csv
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from sqlalchemy import func

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, send_file
from flask_login import login_required, current_user
from models import db, PreMatchAvailability, PreMatchResponse, User
from models.payment import MatchPayment

payments_bp = Blueprint("payments", __name__)

@payments_bp.route("/payment/<int:availability_id>")
@login_required
def payment_page(availability_id):
    availability = PreMatchAvailability.query.get_or_404(availability_id)

    PreMatchResponse.query.filter_by(
        availability_id=availability.id,
        user_id=current_user.id,
        status="available"
    ).first_or_404()

    return render_template("payment/payment_page.html", availability=availability)


@payments_bp.route("/payment/submit/<int:availability_id>", methods=["POST"])
@login_required
def submit_payment(availability_id):
    txn = request.form.get("transaction_id")
    availability = PreMatchAvailability.query.get_or_404(availability_id)

    payment = MatchPayment(
        availability_id=availability.id,
        user_id=current_user.id,
        amount=availability.amount,
        transaction_id=txn,
        payment_status="pending"
    )

    db.session.add(payment)
    db.session.commit()

    flash("Payment submitted. Waiting for coach approval.", "info")
    return redirect(url_for("payments.payment_history_player"))


@payments_bp.route("/payment/approve/<int:payment_id>")
@login_required
def approve_payment(payment_id):
    if current_user.role != "coach":
        abort(403)

    payment = MatchPayment.query.get_or_404(payment_id)
    payment.payment_status = "paid"
    db.session.commit()

    flash("Payment approved successfully", "success")
    return redirect(url_for("payments.payment_history_coach"))


@payments_bp.route("/payment/history/player")
@login_required
def payment_history_player():
    payments = MatchPayment.query.filter_by(user_id=current_user.id).all()
    return render_template("payment/payment_history_player.html", payments=payments)


@payments_bp.route("/payment/history/coach")
@login_required
def payment_history_coach():
    if current_user.role != "coach":
        abort(403)

    payments = (
        db.session.query(
            MatchPayment,
            User.username.label("player_name"),
            PreMatchAvailability.match_date
        )
        .join(User, User.id == MatchPayment.user_id)
        .join(
            PreMatchAvailability,
            PreMatchAvailability.id == MatchPayment.availability_id
        )
        .order_by(MatchPayment.created_at.desc())
        .all()
    )

    return render_template(
        "payment/payment_history_coach.html",
        payments=payments
    )

# 🔹 Match Fee List
@payments_bp.route("/payments")
@login_required
def payment_match_list():
    if current_user.role != "coach":
        abort(403)

    matches = PreMatchAvailability.query.order_by(
        PreMatchAvailability.match_date.desc()
    ).all()

    return render_template(
        "payment/payment_match_list.html",
        matches=matches
    )


@payments_bp.route("/payment/match/<int:availability_id>")
@login_required
def payment_match_detail(availability_id):
    if current_user.role != "coach":
        abort(403)

    availability = PreMatchAvailability.query.get_or_404(availability_id)

    payments = (
        db.session.query(
            MatchPayment,
            User.username.label("player_name")
        )
        .join(User, User.id == MatchPayment.user_id)
        .filter(MatchPayment.availability_id == availability.id)
        .all()
    )

    approved_total = sum(
        p.amount for p, _ in payments if p.payment_status == "paid"
    )

    return render_template(
        "payment/payment_match_detail.html",
        availability=availability,
        payments=payments,
        approved_total=approved_total
    )

@payments_bp.route("/payment/export/csv/<int:availability_id>")
@login_required
def export_payment_csv(availability_id):
    if current_user.role != "coach":
        abort(403)

    availability = PreMatchAvailability.query.get_or_404(availability_id)

    payments = (
        db.session.query(
            MatchPayment,
            User.username
        )
        .join(User, User.id == MatchPayment.user_id)
        .filter(
            MatchPayment.availability_id == availability_id,
            MatchPayment.payment_status == "paid"
        )
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)

    # HEADER
    writer.writerow([
        "Player Name",
        "Amount",
        "Transaction ID",
        "Paid Date"
    ])

    for p, username in payments:
        writer.writerow([
            username,
            float(p.amount),
            p.transaction_id,
            p.created_at.strftime("%Y-%m-%d %H:%M")
        ])

    output.seek(0)

    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"match_{availability_id}_payments.csv"
    )
@payments_bp.route("/payment/export/pdf/<int:availability_id>")
@login_required
def export_payment_pdf(availability_id):
    if current_user.role != "coach":
        abort(403)

    availability = PreMatchAvailability.query.get_or_404(availability_id)

    payments = (
        db.session.query(
            MatchPayment,
            User.username
        )
        .join(User, User.id == MatchPayment.user_id)
        .filter(
            MatchPayment.availability_id == availability_id,
            MatchPayment.payment_status == "paid"
        )
        .all()
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # TITLE
    elements.append(Paragraph(
        f"<b>Match Payment Report</b>", styles["Title"]
    ))
    elements.append(Paragraph(
        f"Match: {availability.title}", styles["Normal"]
    ))
    elements.append(Paragraph(
        f"Date: {availability.match_date}", styles["Normal"]
    ))
    elements.append(Paragraph(
        f"Venue: {availability.venue}", styles["Normal"]
    ))

    elements.append(Paragraph("<br/>", styles["Normal"]))

    # TABLE DATA
    table_data = [
        ["Player Name", "Amount", "Transaction ID", "Paid Date"]
    ]

    total_amount = 0

    for p, username in payments:
        table_data.append([
            username,
            f"₹{p.amount}",
            p.transaction_id,
            p.created_at.strftime("%Y-%m-%d %H:%M")
        ])
        total_amount += float(p.amount)

    table = Table(table_data, colWidths=[140, 80, 140, 120])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("ALIGN", (1,1), (-1,-1), "CENTER"),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
    ]))

    elements.append(table)

    elements.append(Paragraph("<br/>", styles["Normal"]))
    elements.append(Paragraph(
        f"<b>Total Approved Amount:</b> ₹{total_amount}",
        styles["Normal"]
    ))

    doc.build(elements)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"match_{availability_id}_payments.pdf",
        mimetype="application/pdf"
    )