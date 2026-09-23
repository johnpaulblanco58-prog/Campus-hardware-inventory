#reservation_controller.py#

from datetime import datetime

from logger import logger
from models.database import DB_PATH, get_connection, DatabaseError


class ReservationController:

    def __init__(self, db_name=DB_PATH):
        self.db_name = db_name


    # =========================================================
    # CHECK RESERVATION CONFLICT
    # =========================================================

    def check_conflict(
        self,
        asset_id,
        quantity,
        reservation_date,
        start_time,
        end_time
    ):

        try:

            requested_start = datetime.strptime(
                f"{reservation_date} {start_time}",
                "%Y-%m-%d %H:%M"
            )

            requested_end = datetime.strptime(
                f"{reservation_date} {end_time}",
                "%Y-%m-%d %H:%M"
            )

            if requested_end <= requested_start:

                return (
                    False,
                    "End time must be later than start time."
                )

        except ValueError:

            return (
                False,
                "Invalid date or time format."
            )

        try:

            conn = get_connection(self.db_name)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT quantity
                FROM hardware
                WHERE item_id = ?
                """,
                (asset_id,)
            )

            item = cursor.fetchone()

            if not item:

                conn.close()

                return (
                    False,
                    "Selected inventory item was not found."
                )

            total_quantity = item[0]

            cursor.execute(
                """
                SELECT COALESCE(SUM(r.quantity), 0)
                FROM reservations r
                WHERE r.asset_id = ?
                AND r.status IN ('Approved', 'Borrowed')
                AND r.reservation_date = ?
                AND r.start_time < ?
                AND r.end_time > ?
                """,
                (
                    asset_id,
                    reservation_date,
                    end_time,
                    start_time
                )
            )

            conflicting_quantity = cursor.fetchone()[0]

            conn.close()

            available = total_quantity - conflicting_quantity

            if quantity > available:

                return (
                    False,
                    f"Resource conflict detected.\n\n"
                    f"Total quantity: {total_quantity}\n"
                    f"Already allocated: {conflicting_quantity}\n"
                    f"Available: {available}"
                )

            return (
                True,
                "No resource conflict."
            )

        except DatabaseError as e:

            logger.error(
                f"Conflict check failed: {e}"
            )

            return (
                False,
                "Unable to check resource availability."
            )


    # =========================================================
    # CREATE RESERVATION
    # =========================================================

    def create_reservation(
        self,
        username,
        asset_id,
        quantity,
        reservation_date,
        start_time,
        end_time,
        purpose,
        remarks
    ):

        try:

            quantity = int(quantity)

            if quantity <= 0:

                return (
                    False,
                    "Quantity must be greater than zero."
                )

        except ValueError:

            return (
                False,
                "Quantity must be a whole number."
            )

        if not purpose.strip():

            return (
                False,
                "Purpose is required."
            )

        try:

            date_obj = datetime.strptime(
                reservation_date,
                "%Y-%m-%d"
            )

            start_obj = datetime.strptime(
                start_time,
                "%H:%M"
            )

            end_obj = datetime.strptime(
                end_time,
                "%H:%M"
            )

            if date_obj.date() < datetime.now().date():

                return (
                    False,
                    "Reservation date cannot be in the past."
                )

            if end_obj <= start_obj:

                return (
                    False,
                    "End time must be later than start time."
                )

        except ValueError:

            return (
                False,
                "Use valid date/time formats."
            )

        conflict, message = self.check_conflict(
            asset_id,
            quantity,
            reservation_date,
            start_time,
            end_time
        )

        if not conflict:

            return False, message

        try:

            conn = get_connection(self.db_name)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id
                FROM users
                WHERE LOWER(username) = LOWER(?)
                """,
                (username,)
            )

            user = cursor.fetchone()

            if not user:

                conn.close()

                return (
                    False,
                    "User account was not found."
                )

            cursor.execute(
                """
                SELECT item_id
                FROM hardware
                WHERE item_id = ?
                """,
                (asset_id,)
            )

            if not cursor.fetchone():

                conn.close()

                return (
                    False,
                    "Inventory item was not found."
                )

            # IMPORTANT:
            # New reservation always starts as Pending

            cursor.execute(
                """
                INSERT INTO reservations
                (
                    user_id,
                    asset_id,
                    quantity,
                    reservation_date,
                    start_time,
                    end_time,
                    purpose,
                    remarks,
                    status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Pending')
                """,
                (
                    user[0],
                    asset_id,
                    quantity,
                    reservation_date,
                    start_time,
                    end_time,
                    purpose.strip(),
                    remarks.strip()
                )
            )

            conn.commit()
            conn.close()

            logger.info(
                f"Reservation submitted by "
                f"'{username}' for item {asset_id}."
            )

            return (
                True,
                "Reservation request submitted successfully. "
                "Waiting for administrator approval."
            )

        except DatabaseError as e:

            logger.error(
                f"Reservation creation failed: {e}"
            )

            return (
                False,
                "Failed to create reservation."
            )


    # =========================================================
    # GET USER RESERVATIONS
    # =========================================================

    def get_user_reservations(self, username):

        try:

            conn = get_connection(self.db_name)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    r.reservation_id,
                    h.item_name,
                    r.quantity,
                    r.reservation_date,
                    r.start_time,
                    r.end_time,
                    r.purpose,
                    r.status
                FROM reservations r

                JOIN users u
                    ON r.user_id = u.id

                JOIN hardware h
                    ON r.asset_id = h.item_id

                WHERE LOWER(u.username) = LOWER(?)

                ORDER BY r.reservation_id DESC
                """,
                (username,)
            )

            rows = cursor.fetchall()

            conn.close()

            return rows

        except DatabaseError as e:

            logger.error(
                f"Failed to fetch user reservations: {e}"
            )

            return []


    # =========================================================
    # GET ALL RESERVATIONS FOR ADMIN
    # =========================================================

    def get_all_reservations(self):

        try:

            conn = get_connection(self.db_name)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    r.reservation_id,
                    u.username,
                    h.item_name,
                    h.category,
                    r.quantity,
                    r.reservation_date,
                    r.start_time,
                    r.end_time,
                    r.purpose,
                    r.status

                FROM reservations r

                JOIN users u
                    ON r.user_id = u.id

                JOIN hardware h
                    ON r.asset_id = h.item_id

                ORDER BY r.reservation_id DESC
                """
            )

            rows = cursor.fetchall()

            conn.close()

            return rows

        except DatabaseError as e:

            logger.error(
                f"Failed to fetch reservations: {e}"
            )

            return []


    # =========================================================
    # APPROVE OR REJECT RESERVATION
    # =========================================================

    def process_reservation(
        self,
        reservation_id,
        approve
    ):

        try:

            conn = get_connection(self.db_name)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    asset_id,
                    quantity,
                    reservation_date,
                    start_time,
                    end_time,
                    status

                FROM reservations

                WHERE reservation_id = ?
                """,
                (reservation_id,)
            )

            row = cursor.fetchone()

            if not row:

                conn.close()

                return (
                    False,
                    "Reservation not found."
                )

            asset_id = row[0]
            quantity = row[1]
            reservation_date = row[2]
            start_time = row[3]
            end_time = row[4]
            current_status = row[5]

            if current_status != "Pending":

                conn.close()

                return (
                    False,
                    "This reservation has already been processed."
                )

            conn.close()


            # =================================================
            # REJECT
            # =================================================

            if not approve:

                conn = get_connection(self.db_name)
                cursor = conn.cursor()

                cursor.execute(
                    """
                    UPDATE reservations

                    SET status = 'Rejected'

                    WHERE reservation_id = ?
                    """,
                    (reservation_id,)
                )

                conn.commit()
                conn.close()

                logger.info(
                    f"Reservation {reservation_id} rejected."
                )

                return (
                    True,
                    "Reservation request rejected."
                )


            # =================================================
            # APPROVE
            # =================================================

            conflict, message = self.check_conflict(
                asset_id,
                quantity,
                reservation_date,
                start_time,
                end_time
            )

            if not conflict:

                return (
                    False,
                    f"Cannot approve reservation.\n\n{message}"
                )

            conn = get_connection(self.db_name)
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE reservations

                SET status = 'Approved'

                WHERE reservation_id = ?
                """,
                (reservation_id,)
            )

            conn.commit()
            conn.close()

            logger.info(
                f"Reservation {reservation_id} approved."
            )

            return (
                True,
                "Reservation approved successfully."
            )

        except DatabaseError as e:

            logger.error(
                f"Reservation processing error: {e}"
            )

            return (
                False,
                "Failed to process reservation."
            )


    # =========================================================
    # GET APPROVED RESERVATIONS
    # =========================================================

    def get_approved_reservations(self):

        try:

            conn = get_connection(self.db_name)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    r.reservation_id,
                    u.username,
                    h.item_name,
                    r.quantity,
                    r.reservation_date,
                    r.start_time,
                    r.end_time,
                    r.status

                FROM reservations r

                JOIN users u
                    ON r.user_id = u.id

                JOIN hardware h
                    ON r.asset_id = h.item_id

                WHERE r.status = 'Approved'

                ORDER BY r.reservation_date ASC
                """
            )

            rows = cursor.fetchall()

            conn.close()

            return rows

        except DatabaseError as e:

            logger.error(
                f"Failed to fetch approved reservations: {e}"
            )

            return []


    # =========================================================
    # MARK EQUIPMENT AS BORROWED
    # =========================================================

    def mark_borrowed(
        self,
        reservation_id,
        expected_return
    ):

        try:

            conn = get_connection(self.db_name)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    status,
                    asset_id,
                    quantity

                FROM reservations

                WHERE reservation_id = ?
                """,
                (reservation_id,)
            )

            row = cursor.fetchone()

            if not row:

                conn.close()

                return (
                    False,
                    "Reservation not found."
                )

            if row[0] != "Approved":

                conn.close()

                return (
                    False,
                    "Only approved reservations can be marked as borrowed."
                )


            # Check if already borrowed

            cursor.execute(
                """
                SELECT borrowing_id

                FROM borrowings

                WHERE reservation_id = ?
                """,
                (reservation_id,)
            )

            existing = cursor.fetchone()

            if existing:

                conn.close()

                return (
                    False,
                    "This reservation already has a borrowing record."
                )


            # Create borrowing record

            cursor.execute(
                """
                INSERT INTO borrowings
                (
                    reservation_id,
                    borrow_date,
                    expected_return,
                    status
                )

                VALUES
                (
                    ?,
                    CURRENT_TIMESTAMP,
                    ?,
                    'Borrowed'
                )
                """,
                (
                    reservation_id,
                    expected_return
                )
            )


            # Update reservation

            cursor.execute(
                """
                UPDATE reservations

                SET status = 'Borrowed'

                WHERE reservation_id = ?
                """,
                (reservation_id,)
            )

            conn.commit()
            conn.close()

            logger.info(
                f"Reservation {reservation_id} marked as borrowed."
            )

            return (
                True,
                "Equipment successfully marked as borrowed."
            )

        except DatabaseError as e:

            logger.error(
                f"Borrowing error: {e}"
            )

            return (
                False,
                "Failed to mark equipment as borrowed."
            )


    # =========================================================
    # GET BORROWED ITEMS
    # =========================================================

    def get_borrowed_items(self):

        try:

            conn = get_connection(self.db_name)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    r.reservation_id,
                    u.username,
                    h.item_name,
                    r.quantity,
                    b.borrow_date,
                    b.expected_return,
                    b.status

                FROM borrowings b

                JOIN reservations r
                    ON b.reservation_id =
                    r.reservation_id

                JOIN users u
                    ON r.user_id = u.id

                JOIN hardware h
                    ON r.asset_id = h.item_id

                WHERE b.status = 'Borrowed'

                ORDER BY b.borrow_date DESC
                """
            )

            rows = cursor.fetchall()

            conn.close()

            return rows

        except DatabaseError as e:

            logger.error(
                f"Failed to fetch borrowed items: {e}"
            )

            return []


    # =========================================================
    # RETURN EQUIPMENT
    # =========================================================

    def return_item(
        self,
        reservation_id,
        condition,
        remarks
    ):

        try:

            conn = get_connection(self.db_name)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT status

                FROM reservations

                WHERE reservation_id = ?
                """,
                (reservation_id,)
            )

            row = cursor.fetchone()

            if not row:

                conn.close()

                return (
                    False,
                    "Reservation not found."
                )

            if row[0] != "Borrowed":

                conn.close()

                return (
                    False,
                    "This equipment is not currently borrowed."
                )


            # Update borrowing record

            cursor.execute(
                """
                UPDATE borrowings

                SET
                    actual_return = CURRENT_TIMESTAMP,
                    condition_on_return = ?,
                    remarks = ?,
                    status = 'Returned'

                WHERE reservation_id = ?

                AND status = 'Borrowed'
                """,
                (
                    condition,
                    remarks,
                    reservation_id
                )
            )


            # Update reservation

            cursor.execute(
                """
                UPDATE reservations

                SET status = 'Returned'

                WHERE reservation_id = ?
                """,
                (reservation_id,)
            )

            conn.commit()
            conn.close()

            logger.info(
                f"Reservation {reservation_id} returned."
            )

            return (
                True,
                "Equipment returned successfully."
            )

        except DatabaseError as e:

            logger.error(
                f"Return processing error: {e}"
            )

            return (
                False,
                "Failed to process return."
            )
