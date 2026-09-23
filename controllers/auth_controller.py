#####auth_controller.py#####

import bcrypt
import time
import random

from logger import logger
from models.database import DB_PATH, get_connection, DatabaseError
from models.schemas import UserRegisterSchema
from pydantic import ValidationError


class AuthController:

    def __init__(self, db_name=DB_PATH):
        self.db_name = db_name

    def register_user(self, username, email, password, role):
        try:
            validated = UserRegisterSchema(
                username=username,
                email=email,
                password=password,
                role=role
            )

        except ValidationError as e:
            msg = e.errors()[0]["msg"]
            logger.warning(
                f"Registration validation failed: {msg}"
            )
            return False, f"Validation Error: {msg}"

        hashed_pw = bcrypt.hashpw(
            validated.password.encode("utf-8"),
            bcrypt.gensalt()
        )

        verification_code = str(
            random.randint(100000, 999999)
        )
        print(f"\n[DEBUG] Verification code for {username}: {verification_code}\n")

        try:
            conn = get_connection(self.db_name)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id
                FROM users
                WHERE LOWER(username) = LOWER(?)
                """,
                (validated.username,)
            )

            if cursor.fetchone():
                conn.close()
                return False, "Username already taken."

            cursor.execute(
                """
                SELECT id
                FROM users
                WHERE LOWER(email) = LOWER(?)
                """,
                (validated.email,)
            )

            if cursor.fetchone():
                conn.close()
                return False, "Email address already registered."

            cursor.execute(
                """
                INSERT INTO users
                (
                    username,
                    email,
                    password_hash,
                    role,
                    failed_attempts,
                    locked_until,
                    is_verified,
                    verification_code
                )
                VALUES (?, ?, ?, ?, 0, 0, 0, ?)
                """,
                (
                    validated.username,
                    validated.email,
                    hashed_pw.decode("utf-8"),
                    validated.role,
                    verification_code
                )
            )

            conn.commit()
            conn.close()

            logger.info(
                f"Account created: '{validated.username}' as {validated.role}"
            )

            return (
                True,
                f"Registration successful.\n\n"
                f"Your verification code is: {verification_code}\n\n"
                f"Please verify your account before logging in."
            )

        except DatabaseError as e:
            logger.error(
                f"Registration database error: {e}"
            )
            return False, "Registration failed due to a database error."

    def verify_account(self, username, code):
        if not username or not code:
            return False, "Username and verification code are required."

        try:
            conn = get_connection(self.db_name)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT verification_code, is_verified
                FROM users
                WHERE LOWER(username) = LOWER(?)
                """,
                (username,)
            )

            row = cursor.fetchone()

            if not row:
                conn.close()
                return False, "Account not found."

            verification_code = row[0]
            is_verified = row[1]

            if is_verified:
                conn.close()
                return True, "Account is already verified."

            if str(code).strip() != str(verification_code).strip():
                conn.close()
                return False, "Invalid verification code."

            cursor.execute(
                """
                UPDATE users
                SET is_verified = 1,
                    verification_code = NULL
                WHERE LOWER(username) = LOWER(?)
                """,
                (username,)
            )

            conn.commit()
            conn.close()

            logger.info(
                f"Account verified: '{username}'."
            )

            return True, "Account verified successfully."

        except DatabaseError as e:
            logger.error(
                f"Verification error: {e}"
            )
            return False, "Account verification failed."

    def login_user(self, username, password):
        if not username or not password:
            return False, "Please enter both username and password.", False, None

        try:
            conn = get_connection(self.db_name)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    password_hash,
                    failed_attempts,
                    locked_until,
                    role,
                    is_verified
                FROM users
                WHERE LOWER(username) = LOWER(?)
                """,
                (username,)
            )

            row = cursor.fetchone()

            if not row:
                conn.close()

                logger.warning(
                    f"Failed login attempt for username '{username}'."
                )

                return (
                    False,
                    "Invalid username or password.",
                    False,
                    None
                )

            password_hash = row[0]
            failed_attempts = row[1] or 0
            locked_until = row[2] or 0
            role = row[3] or "user"
            is_verified = row[4]

            if not is_verified:
                conn.close()

                return (
                    False,
                    "Account is not verified. Please verify your account first.",
                    False,
                    role
                )

            current_time = time.time()

            if current_time < locked_until:
                conn.close()

                return (
                    False,
                    "Account is locked. Please use Reset / Unlock Password.",
                    True,
                    role
                )

            if bcrypt.checkpw(
                password.encode("utf-8"),
                password_hash.encode("utf-8")
            ):
                cursor.execute(
                    """
                    UPDATE users
                    SET failed_attempts = 0,
                        locked_until = 0
                    WHERE LOWER(username) = LOWER(?)
                    """,
                    (username,)
                )

                conn.commit()
                conn.close()

                logger.info(
                    f"User '{username}' logged in successfully as {role}."
                )

                return (
                    True,
                    "Login successful!",
                    False,
                    role
                )

            failed_attempts += 1

            if failed_attempts >= 3:
                cursor.execute(
                    """
                    UPDATE users
                    SET failed_attempts = 0,
                        locked_until = ?
                    WHERE LOWER(username) = LOWER(?)
                    """,
                    (
                        current_time + 3600,
                        username
                    )
                )

                conn.commit()
                conn.close()

                logger.warning(
                    f"Account '{username}' locked after 3 failed attempts."
                )

                return (
                    False,
                    "Account locked after 3 failed attempts.",
                    True,
                    role
                )

            cursor.execute(
                """
                UPDATE users
                SET failed_attempts = ?
                WHERE LOWER(username) = LOWER(?)
                """,
                (
                    failed_attempts,
                    username
                )
            )

            conn.commit()
            conn.close()

            remaining = 3 - failed_attempts

            return (
                False,
                f"Invalid username or password.\n"
                f"{remaining} attempt(s) remaining.",
                False,
                role
            )

        except DatabaseError as e:
            logger.error(
                f"Login database error: {e}"
            )

            return (
                False,
                "Login database error.",
                False,
                None
            )

    def request_password_reset(self, email, new_password):
        try:
            validated = UserRegisterSchema(
                username="ResetUser",
                email=email,
                password=new_password,
                role="user"
            )

        except ValidationError as e:
            msg = e.errors()[0]["msg"]
            return False, f"Validation Error: {msg}"

        hashed_pw = bcrypt.hashpw(
            validated.password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        try:
            conn = get_connection(self.db_name)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id, username
                FROM users
                WHERE LOWER(email) = LOWER(?)
                """,
                (email,)
            )

            user = cursor.fetchone()

            if not user:
                conn.close()
                return False, "No account was found using that email."

            cursor.execute(
                """
                SELECT id
                FROM password_reset_requests
                WHERE user_id = ?
                AND status = 'Pending'
                """,
                (user[0],)
            )

            if cursor.fetchone():
                conn.close()

                return (
                    False,
                    "A password-reset request is already pending."
                )

            cursor.execute(
                """
                INSERT INTO password_reset_requests
                (
                    user_id,
                    email,
                    new_password_hash,
                    status
                )
                VALUES (?, ?, ?, 'Pending')
                """,
                (
                    user[0],
                    email,
                    hashed_pw
                )
            )

            conn.commit()
            conn.close()

            logger.info(
                f"Password reset requested for '{user[1]}'."
            )

            return (
                True,
                "Password-reset request submitted."
            )

        except DatabaseError as e:
            logger.error(
                f"Password reset request error: {e}"
            )

            return (
                False,
                "Password-reset request failed."
            )

    def change_password(
        self,
        username,
        old_password,
        new_password
    ):
        try:
            validated = UserRegisterSchema(
                username=username,
                email="change@example.com",
                password=new_password,
                role="user"
            )

        except ValidationError as e:
            msg = e.errors()[0]["msg"]

            return (
                False,
                f"Validation Error: {msg}"
            )

        try:
            conn = get_connection(self.db_name)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT password_hash
                FROM users
                WHERE LOWER(username) = LOWER(?)
                """,
                (username,)
            )

            row = cursor.fetchone()

            if not row:
                conn.close()
                return False, "Account not found."

            if not bcrypt.checkpw(
                old_password.encode("utf-8"),
                row[0].encode("utf-8")
            ):
                conn.close()
                return False, "Current password is incorrect."

            hashed = bcrypt.hashpw(
                new_password.encode("utf-8"),
                bcrypt.gensalt()
            ).decode("utf-8")

            cursor.execute(
                """
                UPDATE users
                SET password_hash = ?
                WHERE LOWER(username) = LOWER(?)
                """,
                (
                    hashed,
                    username
                )
            )

            conn.commit()
            conn.close()

            logger.info(
                f"Password changed for '{username}'."
            )

            return (
                True,
                "Password changed successfully."
            )

        except DatabaseError as e:
            logger.error(
                f"Password change error: {e}"
            )

            return (
                False,
                "Password change failed."
            )

    def get_profile(self, username):
        try:
            conn = get_connection(self.db_name)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT username, email, role, is_verified
                FROM users
                WHERE LOWER(username) = LOWER(?)
                """,
                (username,)
            )

            row = cursor.fetchone()
            conn.close()

            return row

        except DatabaseError as e:
            logger.error(
                f"Failed to get profile: {e}"
            )

            return None

    def get_reset_requests(self):
        try:
            conn = get_connection(self.db_name)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    r.id,
                    u.username,
                    r.email,
                    r.status
                FROM password_reset_requests r
                JOIN users u
                    ON r.user_id = u.id
                ORDER BY r.id DESC
                """
            )

            rows = cursor.fetchall()
            conn.close()

            return rows

        except DatabaseError as e:
            logger.error(
                f"Failed to get reset requests: {e}"
            )

            return []

    def process_reset_request(
        self,
        request_id,
        approve
    ):
        try:
            conn = get_connection(self.db_name)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    user_id,
                    new_password_hash
                FROM password_reset_requests
                WHERE id = ?
                AND status = 'Pending'
                """,
                (request_id,)
            )

            row = cursor.fetchone()

            if not row:
                conn.close()

                return (
                    False,
                    "Request not found or already processed."
                )

            user_id = row[0]
            new_password_hash = row[1]

            if approve:
                cursor.execute(
                    """
                    UPDATE users
                    SET password_hash = ?,
                        failed_attempts = 0,
                        locked_until = 0
                    WHERE id = ?
                    """,
                    (
                        new_password_hash,
                        user_id
                    )
                )

                status = "Approved"

            else:
                status = "Rejected"

            cursor.execute(
                """
                UPDATE password_reset_requests
                SET status = ?
                WHERE id = ?
                """,
                (
                    status,
                    request_id
                )
            )

            conn.commit()
            conn.close()

            logger.info(
                f"Password reset request {request_id}: {status}."
            )

            return (
                True,
                f"Request {status.lower()}."
            )

        except DatabaseError as e:
            logger.error(
                f"Reset approval error: {e}"
            )

            return (
                False,
                "Failed to process request."
            )

