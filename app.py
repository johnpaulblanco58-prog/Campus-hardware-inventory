

import os
import re
import random
import smtplib
import requests

from email.mime.text import MIMEText
from dotenv import load_dotenv

from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    send_file
)

from logger import logger

from models.database import init_db

from controllers.auth_controller import AuthController
from controllers.tracker_controller import TrackerController
from controllers.reservation_controller import ReservationController


# =========================================================
# PROJECT DIRECTORY
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

load_dotenv(
    os.path.join(BASE_DIR, ".env")
)

SMTP_SERVER = os.getenv(
    "SMTP_SERVER",
    "smtp-relay.brevo.com"
)

SMTP_PORT = int(
    os.getenv(
        "SMTP_PORT",
        "587"
    )
)

SMTP_LOGIN = os.getenv(
    "SMTP_LOGIN"
)

SMTP_PASSWORD = os.getenv(
    "SMTP_PASSWORD"
)

BREVO_SENDER_EMAIL = os.getenv(
    "BREVO_SENDER_EMAIL"
)

BREVO_API_KEY = os.getenv("BREVO_API_KEY")

def send_otp_email(receiver_email, otp, intent="Account Verification"):

    message_data = {
        "sender": {
            "name": "Laboratory System",
            "email": BREVO_SENDER_EMAIL
        },
        "to": [
            {
                "email": receiver_email
            }
        ],
        "subject": f"Laboratory System - {intent} OTP",
        "textContent": f"""Hello,

Your One-Time Password (OTP) for the Laboratory System is:

{otp}

This code is for {intent}.

Please do not share this code with anyone.

Thank you,
Laboratory System"""
    }

    try:

        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "accept": "application/json",
                "api-key": BREVO_API_KEY,
                "content-type": "application/json"
            },
            json=message_data,
            timeout=15
        )

        if response.status_code in (200, 201, 202):

            logger.info(
                f"OTP email sent successfully to {receiver_email}."
            )

            return True

        logger.error(
            f"Brevo API error: {response.status_code} - {response.text}"
        )

        return False

    except Exception as e:

        logger.error(
            f"OTP email error: {e}"
        )

        return False
# =========================================================
# FLASK APPLICATION
# =========================================================

app = Flask(__name__)

app.secret_key = os.getenv(
    "SECRET_KEY",
    "development-only-secret"
)


# =========================================================
# CONTROLLERS
# =========================================================

auth_controller = AuthController()

tracker_controller = TrackerController()

reservation_controller = ReservationController()


# =========================================================
# LOGIN REQUIRED
# =========================================================

def login_required(view):

    @wraps(view)

    def wrapped(*args, **kwargs):

        if "username" not in session:

            flash(
                "Please log in first.",
                "danger"
            )

            return redirect(
                url_for("login")
            )

        return view(*args, **kwargs)

    return wrapped


# =========================================================
# ADMIN REQUIRED
# =========================================================

def admin_required(view):

    @wraps(view)

    def wrapped(*args, **kwargs):

        role = session.get(
            "role",
            ""
        ).lower()

        if role != "admin":

            flash(
                "Administrator access required.",
                "danger"
            )

            return redirect(
                url_for("dashboard")
            )

        return view(*args, **kwargs)

    return wrapped


# =========================================================
# HOME
# =========================================================

@app.route("/")
def index():

    if "username" in session:

        return redirect(
            url_for("dashboard")
        )

    return redirect(
        url_for("login")
    )


# =========================================================
# LOGIN
# =========================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if "username" in session:

        return redirect(
            url_for("dashboard")
        )

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        success, message, is_locked, role = (
            auth_controller.login_user(
                username,
                password
            )
        )

        if success:

            session.clear()

            session["username"] = username

            session["role"] = role.lower()

            flash(
                message,
                "success"
            )

            return redirect(
                url_for("dashboard")
            )

        if is_locked:

            flash(
                message,
                "danger"
            )

            return redirect(
                url_for("reset")
            )

        flash(
            message,
            "danger"
        )

        return redirect(
            url_for("login")
        )

    # IMPORTANT:
    # This must be outside the POST condition.
    # It displays the login page for GET requests.

    return render_template(
        "login.html"
    )


# =========================================================
# REGISTER
# =========================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        # New web registrations are normal users
        role = "user"

        success, message = (
            auth_controller.register_user(
                username,
                email,
                password,
                role
            )
        )

        if success:

            session["verify_username"] = username

            code_match = re.search(
                r"verification code is:\s*(\d{6})",
                message,
                re.IGNORECASE
            )

            if code_match:

                verification_code = code_match.group(1)

                if send_otp_email(
                    email,
                    verification_code,
                    intent="Account Verification"
                ):

            # Do NOT store the OTP in the session anymore.
            # The user must get it from their email.

                    flash(
                        "Account created successfully. A 6-digit verification code has been sent to your email.",
                        "success"
                    )

                    return redirect(
                        url_for("verify")
                    )

                else:

                    flash(
                        "Account was created, but the verification email could not be sent. Please try again.",
                        "danger"
                    )

                    return redirect(
                        url_for("register")
                    )

            flash(
                "Account created, but no verification code was generated.",
                "danger"
            )

            return redirect(
                url_for("register")
            )

        flash(
            message,
            "danger"
        )

        return redirect(
            url_for("register")
        )

    return render_template(
        "register.html"
    )


# =========================================================
# VERIFY ACCOUNT
# =========================================================

@app.route(
    "/verify",
    methods=["GET", "POST"]
)
def verify():

    username = session.get(
        "verify_username",
        ""
    )

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        code = request.form.get(
            "verification_code",
            ""
        ).strip()

        success, message = (
            auth_controller.verify_account(
                username,
                code
            )
        )

        if success:

            session.pop(
                "verify_username",
                None
            )
            session.pop(
                "verification_code",
                None
            )

            flash(
                message,
                "success"
            )

            return redirect(
                url_for("login")
            )

        flash(
            message,
            "danger"
        )

    verification_code = session.get(
        "verification_code",
        ""
    )

    return render_template(
        "otp_verify.html",
        username=username,
        verification_code=verification_code
    )


# =========================================================
# PASSWORD RESET
# =========================================================

@app.route(
    "/reset",
    methods=["GET", "POST"]
)
def reset():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip()

        new_password = request.form.get(
            "new_password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        if new_password != confirm_password:

            flash(
                "Passwords do not match.",
                "danger"
            )

            return redirect(
                url_for("reset")
            )

        success, message = (
            auth_controller.request_password_reset(
                email,
                new_password
            )
        )

        flash(
            message,
            "success" if success else "danger"
        )

        if success:

            return redirect(
                url_for("login")
            )

        return redirect(
            url_for("reset")
        )

    return render_template(
        "reset.html"
    )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
@login_required
def dashboard():

    username = session.get(
        "username"
    )

    role = session.get(
        "role",
        "user"
    ).lower()

    search = request.args.get(
        "search",
        ""
    ).strip()

    category = request.args.get(
        "category",
        "All Categories"
    )

    # =====================================================
    # INVENTORY
    # =====================================================

    items = tracker_controller.fetch_all_items(
        search,
        category
    )

    categories = (
        tracker_controller.get_categories()
    )

    # =====================================================
    # TOTAL STOCKS
    # =====================================================

    all_items = (
        tracker_controller.fetch_all_items()
    )

    total_stocks = sum(
        item[3]
        for item in all_items
    )

    # =====================================================
    # USER RESERVATIONS
    # =====================================================

    user_reservations = (
        reservation_controller.get_user_reservations(
            username
        )
    )

    # =====================================================
    # BORROWED ITEMS
    # =====================================================

    borrowed_items = [
        reservation
        for reservation in user_reservations
        if reservation[7] == "Borrowed"
    ]

    # =====================================================
    # PENDING REQUESTS
    # =====================================================

    pending_requests = [
        reservation
        for reservation in user_reservations
        if reservation[7] == "Pending"
    ]

    # =====================================================
    # APPROVED RESERVATIONS
    # =====================================================

    approved_reservations = [
        reservation
        for reservation in user_reservations
        if reservation[7] == "Approved"
    ]

    # =====================================================
    # ADMIN DATA
    # =====================================================

    all_reservations = []

    reset_requests = []

    admin_pending_count = 0
    admin_approved_count = 0
    admin_borrowed_count = 0

    if role == "admin":

        all_reservations = (
            reservation_controller.get_all_reservations()
        )

        admin_pending_count = sum(
            1 for reservation in all_reservations
            if reservation[9] == "Pending"
        )

        admin_approved_count = sum(
            1 for reservation in all_reservations
            if reservation[9] == "Approved"
        )

        admin_borrowed_count = sum(
            1 for reservation in all_reservations
            if reservation[9] == "Borrowed"
        )

        reset_requests = (
            auth_controller.get_reset_requests()
        )

    return render_template(
        "dashboard.html",

        username=username,

        role=role,

        items=items,

        categories=categories,

        search=search,

        selected_category=category,

        total_stocks=total_stocks,

        user_reservations=user_reservations,

        borrowed_items=borrowed_items,

        pending_requests=pending_requests,

        approved_reservations=approved_reservations,

        all_reservations=all_reservations,

        admin_pending_count=admin_pending_count,

        admin_approved_count=admin_approved_count,

        admin_borrowed_count=admin_borrowed_count,

        reset_requests=reset_requests
    )


# =========================================================
# CREATE RESERVATION
# =========================================================

@app.route(
    "/reserve/<int:item_id>",
    methods=["POST"]
)
@login_required
def reserve_item(item_id):

    username = session.get(
        "username"
    )

    quantity = request.form.get(
        "quantity",
        "1"
    )

    reservation_date = request.form.get(
        "reservation_date",
        ""
    )

    start_time = request.form.get(
        "start_time",
        ""
    )

    end_time = request.form.get(
        "end_time",
        ""
    )

    purpose = request.form.get(
        "purpose",
        ""
    )

    remarks = request.form.get(
        "remarks",
        ""
    )

    success, message = (
        reservation_controller.create_reservation(
            username=username,
            asset_id=item_id,
            quantity=quantity,
            reservation_date=reservation_date,
            start_time=start_time,
            end_time=end_time,
            purpose=purpose,
            remarks=remarks
        )
    )

    flash(
        message,
        "success" if success else "danger"
    )

    return redirect(
        url_for("dashboard")
    )


# =========================================================
# ADMIN PROCESS RESERVATION
# =========================================================

@app.route(
    "/admin/reservation/<int:reservation_id>",
    methods=["POST"]
)
@admin_required
def process_reservation(reservation_id):

    action = request.form.get(
        "action"
    )

    approve = (
        action == "approve"
    )

    success, message = (
        reservation_controller.process_reservation(
            reservation_id,
            approve
        )
    )

    flash(
        message,
        "success" if success else "danger"
    )

    return redirect(
        url_for("dashboard")
    )


# =========================================================
# ADMIN MARK AS BORROWED
# =========================================================

@app.route(
    "/admin/borrow/<int:reservation_id>",
    methods=["POST"]
)
@admin_required
def mark_borrowed(reservation_id):

    expected_return = request.form.get(
        "expected_return",
        ""
    )

    success, message = (
        reservation_controller.mark_borrowed(
            reservation_id,
            expected_return
        )
    )

    flash(
        message,
        "success" if success else "danger"
    )

    return redirect(
        url_for("dashboard")
    )


# =========================================================
# ADMIN RETURN ITEM
# =========================================================

@app.route(
    "/admin/return/<int:reservation_id>",
    methods=["POST"]
)
@admin_required
def return_item(reservation_id):

    condition = request.form.get(
        "condition",
        ""
    )

    remarks = request.form.get(
        "remarks",
        ""
    )

    success, message = (
        reservation_controller.return_item(
            reservation_id,
            condition,
            remarks
        )
    )

    flash(
        message,
        "success" if success else "danger"
    )

    return redirect(
        url_for("dashboard")
    )


# =========================================================
# ADMIN ADD ITEM
# =========================================================

@app.route(
    "/admin/add-item",
    methods=["POST"]
)
@admin_required
def add_item():

    item_name = request.form.get(
        "item_name",
        ""
    ).strip()

    category = request.form.get(
        "category",
        ""
    ).strip()

    quantity = request.form.get(
        "quantity",
        ""
    )

    unit_price = request.form.get(
        "unit_price",
        ""
    )

    success, message = (
        tracker_controller.add_item(
            item_name,
            category,
            quantity,
            unit_price
        )
    )

    flash(
        message,
        "success" if success else "danger"
    )

    return redirect(
        url_for("dashboard")
    )


# =========================================================
# ADMIN UPDATE ITEM
# =========================================================

@app.route(
    "/admin/update-item/<int:item_id>",
    methods=["POST"]
)
@admin_required
def update_item(item_id):

    quantity = request.form.get(
        "quantity",
        ""
    )

    unit_price = request.form.get(
        "unit_price",
        ""
    )

    success, message = (
        tracker_controller.update_item(
            item_id,
            quantity,
            unit_price
        )
    )

    flash(
        message,
        "success" if success else "danger"
    )

    return redirect(
        url_for("dashboard")
    )


# =========================================================
# ADMIN DELETE ITEM
# =========================================================

@app.route(
    "/admin/delete-item/<int:item_id>",
    methods=["POST"]
)
@admin_required
def delete_item(item_id):

    success, message = (
        tracker_controller.delete_item(
            item_id
        )
    )

    flash(
        message,
        "success" if success else "danger"
    )

    return redirect(
        url_for("dashboard")
    )


# =========================================================
# ADMIN PASSWORD RESET REQUEST
# =========================================================

@app.route(
    "/admin/reset-request/<int:request_id>",
    methods=["POST"]
)
@admin_required
def process_reset_request(request_id):

    action = request.form.get(
        "action"
    )

    approve = (
        action == "approve"
    )

    success, message = (
        auth_controller.process_reset_request(
            request_id,
            approve
        )
    )

    flash(
        message,
        "success" if success else "danger"
    )

    return redirect(
        url_for("dashboard")
    )


# =========================================================
# EXPORT CSV
# =========================================================

@app.route("/export")
@login_required
def export():

    filename = os.path.join(
        BASE_DIR,
        "inventory_report.csv"
    )

    success, message = (
        tracker_controller.export_csv(
            filename
        )
    )

    if not success:

        flash(
            message,
            "danger"
        )

        return redirect(
            url_for("dashboard")
        )

    return send_file(
        filename,
        as_attachment=True,
        download_name="inventory_report.csv"
    )

# =========================================================
# MY PROFILE
# =========================================================

@app.route(
    "/profile",
    methods=["GET", "POST"]
)
@login_required
def profile():

    username = session.get(
        "username"
    )

    if request.method == "POST":

        old_password = request.form.get(
            "old_password",
            ""
        )

        new_password = request.form.get(
            "new_password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        # Check password confirmation
        if new_password != confirm_password:

            flash(
                "New passwords do not match.",
                "danger"
            )

            return redirect(
                url_for("profile")
            )

        # Change password
        success, message = (
            auth_controller.change_password(
                username,
                old_password,
                new_password
            )
        )

        flash(
            message,
            "success" if success else "danger"
        )

        if success:
            return redirect(
                url_for("profile")
            )

    profile_data = (
        auth_controller.get_profile(
            username
        )
    )

    return render_template(
        "profile.html",
        username=username,
        profile=profile_data
    )

# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "You have been logged out.",
        "success"
    )

    return redirect(
        url_for("login")
    )


# =========================================================
# START WEB APPLICATION
# =========================================================

if __name__ == "__main__":

    init_db()

    print()
    print("=" * 55)
    print("ENGINEERING LABORATORY SYSTEM")
    print("WEB APPLICATION")
    print("=" * 55)
    print()
    print("Open:")
    print("http://127.0.0.1:5000")
    print()

    app.run(
        debug=True
    )

