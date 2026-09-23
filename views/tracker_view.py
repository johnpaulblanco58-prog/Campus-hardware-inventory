#####tracker_view.py######

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from logger import logger

from controllers.tracker_controller import TrackerController
from controllers.auth_controller import AuthController
from controllers.reservation_controller import ReservationController

from views.reservation_view import ReservationWindow


class TrackerWindow:

    def __init__(
        self,
        root,
        username,
        role,
        on_logout
    ):
        self.root = root
        self.username = username
        self.role = role.lower()
        self.on_logout = on_logout

        self.controller = TrackerController()
        self.auth = AuthController()
        self.reservation_controller = ReservationController()

        self.root.title(
            "Engineering Laboratory Asset Tracking System"
        )

        self.root.geometry(
            "1100x720"
        )

        self.root.resizable(
            True,
            True
        )

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.handle_close
        )

        self.build_header()
        self.build_search()
        self.build_admin_form()
        self.build_inventory()
        self.build_actions()

        if self.role != "admin":
            if hasattr(self, "frame_form"):
                self.frame_form.pack_forget()

            if hasattr(self, "frame_update"):
                self.frame_update.pack_forget()

        self.load_data()

    # =========================================================
    # HEADER
    # =========================================================

    def build_header(self):

        header = tk.Frame(
            self.root,
            padx=10,
            pady=10
        )

        header.pack(
            fill="x"
        )

        tk.Label(
            header,
            text="Engineering Laboratory Inventory",
            font=("Arial", 17, "bold")
        ).pack(
            side="left"
        )

        tk.Label(
            header,
            text=f"{self.username} ({self.role.upper()})",
            font=("Arial", 10)
        ).pack(
            side="right",
            padx=10
        )

        self.total_label = tk.Label(
            header,
            text="Inventory",
            font=("Arial", 11, "bold")
        )

        self.total_label.pack(
            side="right",
            padx=20
        )

    # =========================================================
    # SEARCH
    # =========================================================

    def build_search(self):

        frame = tk.Frame(
            self.root,
            padx=10,
            pady=5
        )

        frame.pack(
            fill="x"
        )

        tk.Label(
            frame,
            text="Search:"
        ).pack(
            side="left"
        )

        self.search_entry = tk.Entry(
            frame,
            width=30
        )

        self.search_entry.pack(
            side="left",
            padx=5
        )

        tk.Button(
            frame,
            text="Search",
            command=self.search_items
        ).pack(
            side="left"
        )

        tk.Button(
            frame,
            text="Clear",
            command=self.clear_search
        ).pack(
            side="left",
            padx=5
        )

        tk.Label(
            frame,
            text="Category:"
        ).pack(
            side="left",
            padx=(20, 5)
        )

        self.category_var = tk.StringVar(
            value="All Categories"
        )

        self.category_combo = ttk.Combobox(
            frame,
            textvariable=self.category_var,
            state="readonly",
            width=20
        )

        self.category_combo.pack(
            side="left"
        )

        self.category_combo.bind(
            "<<ComboboxSelected>>",
            lambda event: self.load_data()
        )

    # =========================================================
    # ADMIN ADD FORM
    # =========================================================

    def build_admin_form(self):

        self.frame_form = tk.LabelFrame(
            self.root,
            text="Add New Inventory Item",
            padx=10,
            pady=8
        )

        self.frame_form.pack(
            fill="x",
            padx=10,
            pady=5
        )

        tk.Label(
            self.frame_form,
            text="Item Name"
        ).grid(
            row=0,
            column=0,
            padx=5,
            pady=5
        )

        self.entry_name = tk.Entry(
            self.frame_form,
            width=25
        )

        self.entry_name.grid(
            row=0,
            column=1,
            padx=5
        )

        tk.Label(
            self.frame_form,
            text="Category"
        ).grid(
            row=0,
            column=2,
            padx=5
        )

        self.entry_category = tk.Entry(
            self.frame_form,
            width=20
        )

        self.entry_category.grid(
            row=0,
            column=3,
            padx=5
        )

        tk.Label(
            self.frame_form,
            text="Quantity"
        ).grid(
            row=1,
            column=0,
            padx=5
        )

        self.entry_quantity = tk.Entry(
            self.frame_form,
            width=15
        )

        self.entry_quantity.grid(
            row=1,
            column=1,
            padx=5
        )

        tk.Label(
            self.frame_form,
            text="Unit Price"
        ).grid(
            row=1,
            column=2,
            padx=5
        )

        self.entry_price = tk.Entry(
            self.frame_form,
            width=15
        )

        self.entry_price.grid(
            row=1,
            column=3,
            padx=5
        )

        tk.Button(
            self.frame_form,
            text="Add Item",
            command=self.add_item,
            bg="#4CAF50",
            fg="white"
        ).grid(
            row=2,
            column=0,
            columnspan=4,
            sticky="ew",
            pady=8
        )

    # =========================================================
    # INVENTORY TABLE
    # =========================================================

    def build_inventory(self):

        frame = tk.LabelFrame(
            self.root,
            text="Inventory",
            padx=5,
            pady=5
        )

        frame.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=5
        )

        scrollbar = ttk.Scrollbar(
            frame,
            orient="vertical"
        )

        self.tree = ttk.Treeview(
            frame,
            columns=(
                "ID",
                "Name",
                "Category",
                "Total",
                "Available",
                "Price",
                "Status"
            ),
            show="headings",
            selectmode="browse",
            yscrollcommand=scrollbar.set
        )

        scrollbar.config(
            command=self.tree.yview
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        columns = (
            "ID",
            "Name",
            "Category",
            "Total",
            "Available",
            "Price",
            "Status"
        )

        for column in columns:
            self.tree.heading(
                column,
                text=column
            )

        self.tree.column(
            "ID",
            width=50,
            anchor="center"
        )

        self.tree.column(
            "Name",
            width=220
        )

        self.tree.column(
            "Category",
            width=150
        )

        self.tree.column(
            "Total",
            width=80,
            anchor="center"
        )

        self.tree.column(
            "Available",
            width=90,
            anchor="center"
        )

        self.tree.column(
            "Price",
            width=100,
            anchor="center"
        )

        self.tree.column(
            "Status",
            width=120,
            anchor="center"
        )

        self.tree.tag_configure(
            "out",
            background="#ffcccc"
        )

        self.tree.tag_configure(
            "low",
            background="#fff2a8"
        )

        self.tree.tag_configure(
            "in",
            background="#ccffcc"
        )

        self.tree.pack(
            fill="both",
            expand=True
        )

        if self.role != "admin":

            self.tree.bind(
                "<Double-1>",
                lambda event: self.proceed_reservation()
            )

    # =========================================================
    # UPDATE
    # =========================================================

    def build_actions(self):

        self.frame_update = tk.LabelFrame(
            self.root,
            text="Update Selected Inventory",
            padx=10,
            pady=5
        )

        self.frame_update.pack(
            fill="x",
            padx=10,
            pady=5
        )

        tk.Label(
            self.frame_update,
            text="New Quantity"
        ).grid(
            row=0,
            column=0,
            padx=5
        )

        self.entry_update_quantity = tk.Entry(
            self.frame_update,
            width=15
        )

        self.entry_update_quantity.grid(
            row=0,
            column=1
        )

        tk.Label(
            self.frame_update,
            text="New Unit Price"
        ).grid(
            row=0,
            column=2,
            padx=5
        )

        self.entry_update_price = tk.Entry(
            self.frame_update,
            width=15
        )

        self.entry_update_price.grid(
            row=0,
            column=3
        )

        tk.Button(
            self.frame_update,
            text="Update Item",
            command=self.update_item,
            bg="#2196F3",
            fg="white"
        ).grid(
            row=0,
            column=4,
            padx=10
        )

        action_frame = tk.Frame(
            self.root,
            padx=10,
            pady=5
        )

        action_frame.pack(
            fill="x"
        )

        if self.role != "admin":

            tk.Button(
                action_frame,
                text="Proceed to Reservation",
                command=self.proceed_reservation,
                bg="#2196F3",
                fg="white"
            ).pack(
                side="left",
                fill="x",
                expand=True,
                padx=2
            )

            tk.Button(
                action_frame,
                text="My Reservations",
                command=self.user_reservations
            ).pack(
                side="left",
                fill="x",
                expand=True,
                padx=2
            )

        else:

            tk.Button(
                action_frame,
                text="Reservation Management",
                command=self.admin_reservations,
                bg="#FF9800",
                fg="white"
            ).pack(
                side="left",
                fill="x",
                expand=True,
                padx=2
            )

            tk.Button(
                action_frame,
                text="Password Reset Requests",
                command=self.password_reset_requests
            ).pack(
                side="left",
                fill="x",
                expand=True,
                padx=2
            )

            tk.Button(
                action_frame,
                text="Delete Selected Item",
                command=self.delete_item,
                bg="#F44336",
                fg="white"
            ).pack(
                side="left",
                fill="x",
                expand=True,
                padx=2
            )

        tk.Button(
            action_frame,
            text="Export Inventory to CSV Report",
            command=self.export_csv,
            bg="#795548",
            fg="white"
        ).pack(
            side="left",
            fill="x",
            expand=True,
            padx=2
        )

        tk.Button(
            action_frame,
            text="My Profile & Security",
            command=self.profile_security
        ).pack(
            side="left",
            fill="x",
            expand=True,
            padx=2
        )

        tk.Button(
            action_frame,
            text="Logout",
            command=self.logout,
            bg="#9C27B0",
            fg="white"
        ).pack(
            side="left",
            fill="x",
            expand=True,
            padx=2
        )

    # =========================================================
    # INVENTORY
    # =========================================================

    def load_data(self):

        for row in self.tree.get_children():
            self.tree.delete(row)

        search = self.search_entry.get().strip()
        category = self.category_var.get()

        rows = self.controller.fetch_all_items(
            search,
            category
        )

        for row in rows:

            available = row[6]

            if available <= 0:
                tag = "out"
            elif available <= 5:
                tag = "low"
            else:
                tag = "in"

            self.tree.insert(
                "",
                tk.END,
                values=(
                    row[0],
                    row[1],
                    row[2],
                    row[3],
                    available,
                    f"{row[4]:.2f}",
                    "Unavailable"
                    if available <= 0
                    else "Available"
                ),
                tags=(tag,)
            )

        self.refresh_categories()
        self.update_total_value()

    def refresh_categories(self):

        categories = self.controller.get_categories()

        values = [
            "All Categories"
        ] + categories

        current = self.category_var.get()

        self.category_combo["values"] = values

        if current not in values:
            self.category_var.set(
                "All Categories"
            )

    def update_total_value(self):

        total = self.controller.get_total_value()

        if self.role == "admin":
            self.total_label.config(
                text=f"Total Asset Value: ${total:,.2f}"
            )
        else:
            self.total_label.config(
                text="User Inventory"
            )

    def search_items(self):
        self.load_data()

    def clear_search(self):

        self.search_entry.delete(
            0,
            tk.END
        )

        self.category_var.set(
            "All Categories"
        )

        self.load_data()

    # =========================================================
    # ADD
    # =========================================================

    def add_item(self):

        if self.role != "admin":
            return

        success, msg = self.controller.add_item(
            self.entry_name.get().strip(),
            self.entry_category.get().strip(),
            self.entry_quantity.get().strip(),
            self.entry_price.get().strip()
        )

        if success:

            messagebox.showinfo(
                "Success",
                msg
            )

            for entry in (
                self.entry_name,
                self.entry_category,
                self.entry_quantity,
                self.entry_price
            ):
                entry.delete(
                    0,
                    tk.END
                )

            self.load_data()

        else:
            messagebox.showerror(
                "Error",
                msg
            )

    # =========================================================
    # UPDATE
    # =========================================================

    def update_item(self):

        selected = self.tree.selection()

        if not selected:
            messagebox.showwarning(
                "Selection",
                "Please select an inventory item."
            )

            return

        item_id = self.tree.item(
            selected[0],
            "values"
        )[0]

        success, msg = self.controller.update_item(
            item_id,
            self.entry_update_quantity.get().strip(),
            self.entry_update_price.get().strip()
        )

        if success:

            messagebox.showinfo(
                "Update",
                msg
            )

            self.entry_update_quantity.delete(
                0,
                tk.END
            )

            self.entry_update_price.delete(
                0,
                tk.END
            )

            self.load_data()

        else:
            messagebox.showerror(
                "Update Error",
                msg
            )

    # =========================================================
    # DELETE
    # =========================================================

    def delete_item(self):

        selected = self.tree.selection()

        if not selected:
            messagebox.showwarning(
                "Selection",
                "Please select an inventory item."
            )

            return

        item_id = self.tree.item(
            selected[0],
            "values"
        )[0]

        if not messagebox.askyesno(
            "Delete Item",
            f"Delete inventory item ID {item_id}?"
        ):
            return

        success, msg = self.controller.delete_item(
            item_id
        )

        if success:

            messagebox.showinfo(
                "Deleted",
                msg
            )

            self.load_data()

        else:
            messagebox.showerror(
                "Delete Error",
                msg
            )

    # =========================================================
    # USER RESERVATION
    # =========================================================

    def proceed_reservation(self):

        selected = self.tree.selection()

        if not selected:
            messagebox.showwarning(
                "Select Item",
                "Please select an inventory item first."
            )

            return

        values = self.tree.item(
            selected[0],
            "values"
        )

        available = int(
            values[4]
        )

        if available <= 0:
            messagebox.showwarning(
                "Unavailable",
                "This item is currently unavailable."
            )

            return

        item_id = int(
            values[0]
        )

        item = self.controller.get_item(
            item_id
        )

        if not item:
            messagebox.showerror(
                "Error",
                "The selected inventory item no longer exists."
            )

            self.load_data()

            return

        ReservationWindow(
            self.root,
            self.username,
            item,
            on_success=self.load_data
        )

    # =========================================================
    # USER RESERVATIONS
    # =========================================================

    def user_reservations(self):

        window = tk.Toplevel(
            self.root
        )

        window.title(
            "My Reservations"
        )

        window.geometry(
            "850x400"
        )

        columns = (
            "ID",
            "Item",
            "Qty",
            "Date",
            "Start",
            "End",
            "Purpose",
            "Status"
        )

        tree = ttk.Treeview(
            window,
            columns=columns,
            show="headings"
        )

        for column in columns:
            tree.heading(
                column,
                text=column
            )

        tree.column(
            "ID",
            width=50
        )

        tree.column(
            "Item",
            width=150
        )

        tree.column(
            "Qty",
            width=50
        )

        tree.column(
            "Date",
            width=100
        )

        tree.column(
            "Start",
            width=70
        )

        tree.column(
            "End",
            width=70
        )

        tree.column(
            "Purpose",
            width=180
        )

        tree.column(
            "Status",
            width=100
        )

        tree.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        for row in self.reservation_controller.get_user_reservations(
            self.username
        ):
            tree.insert(
                "",
                tk.END,
                values=row
            )

    # =========================================================
    # ADMIN RESERVATION MANAGEMENT
    # =========================================================

    def admin_reservations(self):

        if self.role != "admin":
            return

        window = tk.Toplevel(
            self.root
        )

        window.title(
            "Reservation Management"
        )

        window.geometry(
            "1100x500"
        )

        columns = (
            "ID",
            "User",
            "Item",
            "Category",
            "Qty",
            "Date",
            "Start",
            "End",
            "Purpose",
            "Status"
        )

        tree = ttk.Treeview(
            window,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        for column in columns:
            tree.heading(
                column,
                text=column
            )

        widths = {
            "ID": 50,
            "User": 100,
            "Item": 130,
            "Category": 100,
            "Qty": 50,
            "Date": 100,
            "Start": 70,
            "End": 70,
            "Purpose": 180,
            "Status": 90
        }

        for column, width in widths.items():
            tree.column(
                column,
                width=width
            )

        tree.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        def load():

            for child in tree.get_children():
                tree.delete(child)

            rows = self.reservation_controller.get_all_reservations()

            for row in rows:
                tree.insert(
                    "",
                    tk.END,
                    values=row
                )

        def process(approve):

            selected = tree.selection()

            if not selected:
                messagebox.showwarning(
                    "Selection",
                    "Please select a reservation.",
                    parent=window
                )

                return

            reservation_id = int(
                tree.item(
                    selected[0],
                    "values"
                )[0]
            )

            success, msg = self.reservation_controller.process_reservation(
                reservation_id,
                approve
            )

            if success:

                messagebox.showinfo(
                    "Reservation",
                    msg,
                    parent=window
                )

                load()
                self.load_data()

            else:
                messagebox.showerror(
                    "Reservation",
                    msg,
                    parent=window
                )

        def borrow():

            selected = tree.selection()

            if not selected:
                messagebox.showwarning(
                    "Selection",
                    "Please select an approved reservation.",
                    parent=window
                )

                return

            values = tree.item(
                selected[0],
                "values"
            )

            reservation_id = int(
                values[0]
            )

            status = values[9]

            if status != "Approved":
                messagebox.showwarning(
                    "Borrow",
                    "Only approved reservations can be borrowed.",
                    parent=window
                )

                return

            self.open_borrow_window(
                reservation_id,
                window,
                load
            )

        def return_item():

            selected = tree.selection()

            if not selected:
                messagebox.showwarning(
                    "Selection",
                    "Please select a borrowed reservation.",
                    parent=window
                )

                return

            values = tree.item(
                selected[0],
                "values"
            )

            reservation_id = int(
                values[0]
            )

            status = values[9]

            if status != "Borrowed":
                messagebox.showwarning(
                    "Return",
                    "Only borrowed equipment can be returned.",
                    parent=window
                )

                return

            self.open_return_window(
                reservation_id,
                window,
                load
            )

        buttons = tk.Frame(
            window
        )

        buttons.pack(
            pady=5
        )

        tk.Button(
            buttons,
            text="Approve",
            command=lambda: process(True),
            bg="#4CAF50",
            fg="white",
            width=12
        ).pack(
            side="left",
            padx=5
        )

        tk.Button(
            buttons,
            text="Deny",
            command=lambda: process(False),
            bg="#F44336",
            fg="white",
            width=12
        ).pack(
            side="left",
            padx=5
        )

        tk.Button(
            buttons,
            text="Mark as Borrowed",
            command=borrow,
            bg="#2196F3",
            fg="white",
            width=16
        ).pack(
            side="left",
            padx=5
        )

        tk.Button(
            buttons,
            text="Process Return",
            command=return_item,
            bg="#795548",
            fg="white",
            width=16
        ).pack(
            side="left",
            padx=5
        )

        load()

    # =========================================================
    # BORROW WINDOW
    # =========================================================

    def open_borrow_window(
        self,
        reservation_id,
        parent,
        refresh
    ):

        window = tk.Toplevel(
            parent
        )

        window.title(
            "Borrow Equipment"
        )

        window.geometry(
            "350x200"
        )

        tk.Label(
            window,
            text="Expected Return Date",
            font=("Arial", 11, "bold")
        ).pack(
            pady=15
        )

        entry = tk.Entry(
            window,
            width=25
        )

        entry.pack()

        tk.Label(
            window,
            text="Format: YYYY-MM-DD"
        ).pack(
            pady=5
        )

        def submit():

            success, msg = self.reservation_controller.mark_borrowed(
                reservation_id,
                entry.get().strip()
            )

            if success:

                messagebox.showinfo(
                    "Borrowing",
                    msg,
                    parent=window
                )

                window.destroy()
                refresh()
                self.load_data()

            else:
                messagebox.showerror(
                    "Borrowing",
                    msg,
                    parent=window
                )

        tk.Button(
            window,
            text="Confirm Borrowing",
            command=submit,
            bg="#2196F3",
            fg="white"
        ).pack(
            pady=15
        )

    # =========================================================
    # RETURN WINDOW
    # =========================================================

    def open_return_window(
        self,
        reservation_id,
        parent,
        refresh
    ):

        window = tk.Toplevel(
            parent
        )

        window.title(
            "Process Return"
        )

        window.geometry(
            "400x300"
        )

        tk.Label(
            window,
            text="Equipment Condition",
            font=("Arial", 11, "bold")
        ).pack(
            pady=15
        )

        condition = ttk.Combobox(
            window,
            values=[
                "Good",
                "Damaged",
                "Missing Components"
            ],
            state="readonly",
            width=25
        )

        condition.set(
            "Good"
        )

        condition.pack()

        tk.Label(
            window,
            text="Remarks"
        ).pack(
            pady=(15, 5)
        )

        remarks = tk.Text(
            window,
            width=35,
            height=5
        )

        remarks.pack()

        def submit():

            success, msg = self.reservation_controller.return_item(
                reservation_id,
                condition.get(),
                remarks.get(
                    "1.0",
                    tk.END
                ).strip()
            )

            if success:

                messagebox.showinfo(
                    "Return",
                    msg,
                    parent=window
                )

                window.destroy()
                refresh()
                self.load_data()

            else:
                messagebox.showerror(
                    "Return",
                    msg,
                    parent=window
                )

        tk.Button(
            window,
            text="Confirm Return",
            command=submit,
            bg="#795548",
            fg="white"
        ).pack(
            pady=15
        )

    # =========================================================
    # CSV
    # =========================================================

    def export_csv(self):

        filename = filedialog.asksaveasfilename(
            parent=self.root,
            title="Export Inventory Report",
            defaultextension=".csv",
            filetypes=[
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ],
            initialfile="inventory_report.csv"
        )

        if not filename:
            return

        success, msg = self.controller.export_csv(
            filename=filename,
            search=self.search_entry.get().strip(),
            category=self.category_var.get()
        )

        if success:

            messagebox.showinfo(
                "CSV Report",
                msg
            )

        else:

            messagebox.showerror(
                "Export Error",
                msg
            )

    # =========================================================
    # PROFILE & SECURITY
    # =========================================================

    def profile_security(self):

        profile = self.auth.get_profile(
            self.username
        )

        window = tk.Toplevel(
            self.root
        )

        window.title(
            "My Profile & Security"
        )

        window.geometry(
            "420x500"
        )

        window.resizable(
            False,
            False
        )

        tk.Label(
            window,
            text="My Profile",
            font=("Arial", 15, "bold")
        ).pack(
            pady=15
        )

        if profile:

            tk.Label(
                window,
                text=f"Username: {profile[0]}"
            ).pack(
                pady=5
            )

            tk.Label(
                window,
                text=f"Email: {profile[1]}"
            ).pack(
                pady=5
            )

            tk.Label(
                window,
                text=f"Role: {profile[2].upper()}"
            ).pack(
                pady=5
            )

            verification = (
                "Verified"
                if profile[3]
                else "Not Verified"
            )

            tk.Label(
                window,
                text=f"Account Status: {verification}"
            ).pack(
                pady=5
            )

        ttk.Separator(
            window,
            orient="horizontal"
        ).pack(
            fill="x",
            padx=20,
            pady=15
        )

        tk.Label(
            window,
            text="Security",
            font=("Arial", 13, "bold")
        ).pack(
            pady=5
        )

        tk.Label(
            window,
            text="Current Password:"
        ).pack()

        old_entry = tk.Entry(
            window,
            show="*",
            width=30
        )

        old_entry.pack(
            pady=5
        )

        tk.Label(
            window,
            text="New Password:"
        ).pack()

        new_entry = tk.Entry(
            window,
            show="*",
            width=30
        )

        new_entry.pack(
            pady=5
        )

        tk.Label(
            window,
            text="New password requires 8+ characters, "
                 "uppercase, number and special character.",
            fg="#666666"
        ).pack(
            pady=5
        )

        def change_password():

            success, msg = self.auth.change_password(
                self.username,
                old_entry.get(),
                new_entry.get()
            )

            if success:

                messagebox.showinfo(
                    "Security",
                    msg,
                    parent=window
                )

                window.destroy()

            else:

                messagebox.showwarning(
                    "Security",
                    msg,
                    parent=window
                )

        tk.Button(
            window,
            text="Change Password",
            command=change_password,
            bg="#2196F3",
            fg="white",
            width=18
        ).pack(
            pady=15
        )

    # =========================================================
    # PASSWORD RESET REQUESTS
    # =========================================================

    def password_reset_requests(self):

        window = tk.Toplevel(
            self.root
        )

        window.title(
            "Password Reset Requests"
        )

        window.geometry(
            "650x400"
        )

        tree = ttk.Treeview(
            window,
            columns=(
                "ID",
                "Username",
                "Email",
                "Status"
            ),
            show="headings"
        )

        for column in (
            "ID",
            "Username",
            "Email",
            "Status"
        ):
            tree.heading(
                column,
                text=column
            )

        tree.column(
            "ID",
            width=50
        )

        tree.column(
            "Username",
            width=120
        )

        tree.column(
            "Email",
            width=250
        )

        tree.column(
            "Status",
            width=100
        )

        tree.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

        def load():

            for child in tree.get_children():
                tree.delete(child)

            for row in self.auth.get_reset_requests():

                tree.insert(
                    "",
                    tk.END,
                    values=row
                )

        def process(approve):

            selected = tree.selection()

            if not selected:

                messagebox.showwarning(
                    "Selection",
                    "Please select a request.",
                    parent=window
                )

                return

            request_id = int(
                tree.item(
                    selected[0],
                    "values"
                )[0]
            )

            success, msg = self.auth.process_reset_request(
                request_id,
                approve
            )

            if success:

                messagebox.showinfo(
                    "Password Reset",
                    msg,
                    parent=window
                )

                load()

            else:

                messagebox.showerror(
                    "Error",
                    msg,
                    parent=window
                )

        button_frame = tk.Frame(
            window
        )

        button_frame.pack(
            pady=5
        )

        tk.Button(
            button_frame,
            text="Approve",
            command=lambda: process(True),
            bg="#4CAF50",
            fg="white",
            width=12
        ).pack(
            side="left",
            padx=5
        )

        tk.Button(
            button_frame,
            text="Reject",
            command=lambda: process(False),
            bg="#F44336",
            fg="white",
            width=12
        ).pack(
            side="left",
            padx=5
        )

        load()

    # =========================================================
    # LOGOUT
    # =========================================================

    def logout(self):

        logger.info(
            f"User '{self.username}' logged out."
        )

        self.on_logout()

    def handle_close(self):

        logger.info(
            f"User '{self.username}' exited the application."
        )

        self.root.destroy()
