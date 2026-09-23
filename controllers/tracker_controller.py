######tracker_controller.py#######

import csv

from logger import logger
from models.database import DB_PATH, get_connection, DatabaseError
from models.schemas import HardwareSchema
from pydantic import ValidationError


class TrackerController:

    def __init__(self, db_name=DB_PATH):
        self.db_name = db_name

    @staticmethod
    def get_status(quantity):
        if quantity > 5:
            return "In Stock"
        elif quantity >= 1:
            return "Low Stock"
        else:
            return "Out of Stock"

    def fetch_all_items(
        self,
        search="",
        category=""
    ):
        try:
            conn = get_connection(self.db_name)
            cursor = conn.cursor()

            query = """
                SELECT
                    h.item_id,
                    h.item_name,
                    h.category,
                    h.quantity,
                    h.unit_price,
                    h.status,
                    h.quantity -
                    COALESCE(
                        (
                            SELECT SUM(r.quantity)
                            FROM reservations r
                            WHERE r.asset_id = h.item_id
                            AND r.status IN ('Approved', 'Borrowed')
                        ),
                        0
                    ) AS available_quantity
                FROM hardware h
                WHERE 1=1
            """

            params = []

            if search:
                query += """
                    AND (
                        LOWER(h.item_name) LIKE LOWER(?)
                        OR LOWER(h.category) LIKE LOWER(?)
                    )
                """

                params.extend([
                    f"%{search}%",
                    f"%{search}%"
                ])

            if category and category != "All Categories":
                query += """
                    AND LOWER(h.category) = LOWER(?)
                """

                params.append(category)

            query += " ORDER BY h.item_id"

            cursor.execute(
                query,
                params
            )

            rows = cursor.fetchall()
            conn.close()

            return rows

        except DatabaseError as e:
            logger.error(
                f"Failed to fetch inventory records: {e}"
            )

            return []

    def get_item(self, item_id):
        try:
            conn = get_connection(self.db_name)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    item_id,
                    item_name,
                    category,
                    quantity,
                    unit_price,
                    status
                FROM hardware
                WHERE item_id = ?
                """,
                (item_id,)
            )

            row = cursor.fetchone()
            conn.close()

            return row

        except DatabaseError as e:
            logger.error(
                f"Failed to get item {item_id}: {e}"
            )

            return None

    def get_categories(self):
        try:
            conn = get_connection(self.db_name)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT DISTINCT category
                FROM hardware
                ORDER BY LOWER(category)
                """
            )

            rows = cursor.fetchall()
            conn.close()

            return [
                row[0]
                for row in rows
            ]

        except DatabaseError as e:
            logger.error(
                f"Failed to fetch categories: {e}"
            )

            return []

    def get_available_quantity(self, item_id):
        try:
            conn = get_connection(self.db_name)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    h.quantity -
                    COALESCE(
                        (
                            SELECT SUM(r.quantity)
                            FROM reservations r
                            WHERE r.asset_id = h.item_id
                            AND r.status IN ('Approved', 'Borrowed')
                        ),
                        0
                    )
                FROM hardware h
                WHERE h.item_id = ?
                """,
                (item_id,)
            )

            row = cursor.fetchone()
            conn.close()

            return max(0, int(row[0])) if row else 0

        except DatabaseError as e:
            logger.error(
                f"Failed to calculate available quantity: {e}"
            )

            return 0

    def get_total_value(self):
        try:
            conn = get_connection(self.db_name)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT COALESCE(
                    SUM(quantity * unit_price),
                    0
                )
                FROM hardware
                """
            )

            total = cursor.fetchone()[0]
            conn.close()

            return float(total or 0)

        except DatabaseError as e:
            logger.error(
                f"Failed to calculate total inventory value: {e}"
            )

            return 0.0

    def add_item(
        self,
        item_name,
        category,
        quantity,
        unit_price
    ):
        try:
            validated = HardwareSchema(
                item_name=item_name,
                category=category,
                quantity=quantity,
                unit_price=unit_price
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
                SELECT item_id
                FROM hardware
                WHERE LOWER(item_name) = LOWER(?)
                """,
                (validated.item_name,)
            )

            if cursor.fetchone():
                conn.close()

                return (
                    False,
                    f"'{validated.item_name}' already exists."
                )

            status = self.get_status(
                validated.quantity
            )

            cursor.execute(
                """
                INSERT INTO hardware
                (
                    item_name,
                    category,
                    quantity,
                    unit_price,
                    status
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    validated.item_name,
                    validated.category,
                    validated.quantity,
                    validated.unit_price,
                    status
                )
            )

            conn.commit()
            conn.close()

            logger.info(
                f"Hardware added: '{validated.item_name}'"
            )

            return (
                True,
                "Hardware item added successfully!"
            )

        except DatabaseError as e:
            logger.error(
                f"Database error adding item: {e}"
            )

            return (
                False,
                "Database insertion failed."
            )

    def update_item(
        self,
        item_id,
        quantity,
        unit_price
    ):
        try:
            quantity = int(quantity)
            unit_price = float(unit_price)

            if quantity < 0:
                return False, "Quantity cannot be negative."

            if unit_price < 0:
                return False, "Unit price cannot be negative."

        except ValueError:
            return (
                False,
                "Quantity must be an integer and Unit Price must be numeric."
            )

        try:
            conn = get_connection(self.db_name)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT COALESCE(
                    SUM(quantity),
                    0
                )
                FROM reservations
                WHERE asset_id = ?
                AND status IN ('Approved', 'Borrowed')
                """,
                (item_id,)
            )

            reserved = cursor.fetchone()[0]

            if quantity < reserved:
                conn.close()

                return (
                    False,
                    f"Quantity cannot be less than "
                    f"the currently allocated quantity ({reserved})."
                )

            status = self.get_status(quantity)

            cursor.execute(
                """
                UPDATE hardware
                SET quantity = ?,
                    unit_price = ?,
                    status = ?
                WHERE item_id = ?
                """,
                (
                    quantity,
                    unit_price,
                    status,
                    item_id
                )
            )

            if cursor.rowcount == 0:
                conn.close()

                return False, "Item not found."

            conn.commit()
            conn.close()

            logger.info(
                f"Inventory item ID {item_id} updated."
            )

            return (
                True,
                "Item updated successfully."
            )

        except DatabaseError as e:
            logger.error(
                f"Error updating item ID {item_id}: {e}"
            )

            return (
                False,
                "Failed to update item."
            )

    def delete_item(self, item_id):
        try:
            conn = get_connection(self.db_name)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM reservations
                WHERE asset_id = ?
                AND status IN (
                    'Pending',
                    'Approved',
                    'Borrowed'
                )
                """,
                (item_id,)
            )

            active = cursor.fetchone()[0]

            if active > 0:
                conn.close()

                return (
                    False,
                    "This item cannot be deleted because "
                    "it has an active reservation or borrowing record."
                )

            cursor.execute(
                """
                DELETE FROM hardware
                WHERE item_id = ?
                """,
                (item_id,)
            )

            if cursor.rowcount == 0:
                conn.close()

                return False, "Item not found."

            conn.commit()
            conn.close()

            logger.info(
                f"Inventory item ID {item_id} deleted."
            )

            return (
                True,
                "Item deleted successfully."
            )

        except DatabaseError as e:
            logger.error(
                f"Error deleting item ID {item_id}: {e}"
            )

            return (
                False,
                "Failed to delete item."
            )

    def export_csv(
        self,
        filename="inventory_report.csv",
        search="",
        category=""
    ):
        try:
            rows = self.fetch_all_items(
                search,
                category
            )

            with open(
                filename,
                "w",
                newline="",
                encoding="utf-8"
            ) as file:

                writer = csv.writer(file)

                writer.writerow(
                    [
                        "ID",
                        "Name",
                        "Category",
                        "Total Qty",
                        "Available Qty",
                        "Price ($)",
                        "Status"
                    ]
                )

                for row in rows:
                    writer.writerow(
                        [
                            row[0],
                            row[1],
                            row[2],
                            row[3],
                            row[6],
                            f"{row[4]:.2f}",
                            row[5]
                        ]
                    )

            logger.info(
                f"Inventory CSV report generated: {filename}"
            )

            return (
                True,
                f"Inventory report exported successfully:\n{filename}"
            )

        except OSError as e:
            logger.error(
                f"Inventory report generation failed: {e}"
            )

            return (
                False,
                "Failed to generate inventory report."
            )
