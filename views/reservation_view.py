#####reservation_view.py######

import tkinter as tk
from tkinter import messagebox

from controllers.reservation_controller import ReservationController


class ReservationWindow:

    def __init__(
        self,
        parent,
        username,
        item,
        on_success=None
    ):
        self.parent = parent
        self.username = username
        self.item = item
        self.on_success = on_success

        self.controller = ReservationController()

        self.window = tk.Toplevel(parent)

        self.window.title("Equipment Reservation")
        self.window.geometry("500x600")
        self.window.resizable(False, False)

        self.window.transient(parent)
        self.window.grab_set()

        self.build_ui()

    def build_ui(self):

        tk.Label(
            self.window,
            text="Equipment Reservation",
            font=("Arial", 16, "bold")
        ).pack(pady=15)

        info = tk.LabelFrame(
            self.window,
            text="Selected Inventory Item",
            padx=15,
            pady=10
        )

        info.pack(
            fill="x",
            padx=20,
            pady=5
        )

        tk.Label(
            info,
            text=f"ID: {self.item[0]}"
        ).pack(anchor="w")

        tk.Label(
            info,
            text=f"Item Name: {self.item[1]}"
        ).pack(anchor="w")

        tk.Label(
            info,
            text=f"Category: {self.item[2]}"
        ).pack(anchor="w")

        tk.Label(
            info,
            text=f"Total Quantity: {self.item[3]}"
        ).pack(anchor="w")

        form = tk.LabelFrame(
            self.window,
            text="Reservation Details",
            padx=15,
            pady=10
        )

        form.pack(
            fill="x",
            padx=20,
            pady=10
        )

        tk.Label(
            form,
            text="Quantity:"
        ).grid(
            row=0,
            column=0,
            sticky="w",
            pady=5
        )

        self.quantity_var = tk.StringVar(
            value="1"
        )

        self.quantity_spin = tk.Spinbox(
            form,
            from_=1,
            to=max(1, self.item[3]),
            textvariable=self.quantity_var,
            width=10
        )

        self.quantity_spin.grid(
            row=0,
            column=1,
            sticky="w",
            pady=5
        )

        tk.Label(
            form,
            text="Date (YYYY-MM-DD):"
        ).grid(
            row=1,
            column=0,
            sticky="w",
            pady=5
        )

        self.date_entry = tk.Entry(
            form,
            width=20
        )

        self.date_entry.grid(
            row=1,
            column=1,
            sticky="w",
            pady=5
        )

        tk.Label(
            form,
            text="Start Time (HH:MM):"
        ).grid(
            row=2,
            column=0,
            sticky="w",
            pady=5
        )

        self.start_entry = tk.Entry(
            form,
            width=20
        )

        self.start_entry.grid(
            row=2,
            column=1,
            sticky="w",
            pady=5
        )

        tk.Label(
            form,
            text="End Time (HH:MM):"
        ).grid(
            row=3,
            column=0,
            sticky="w",
            pady=5
        )

        self.end_entry = tk.Entry(
            form,
            width=20
        )

        self.end_entry.grid(
            row=3,
            column=1,
            sticky="w",
            pady=5
        )

        tk.Label(
            form,
            text="Purpose:"
        ).grid(
            row=4,
            column=0,
            sticky="nw",
            pady=5
        )

        self.purpose_text = tk.Text(
            form,
            width=28,
            height=4
        )

        self.purpose_text.grid(
            row=4,
            column=1,
            pady=5
        )

        tk.Label(
            form,
            text="Remarks:"
        ).grid(
            row=5,
            column=0,
            sticky="nw",
            pady=5
        )

        self.remarks_text = tk.Text(
            form,
            width=28,
            height=3
        )

        self.remarks_text.grid(
            row=5,
            column=1,
            pady=5
        )

        tk.Label(
            self.window,
            text=(
                "Your request will be reviewed by the laboratory administrator."
            ),
            fg="#555555"
        ).pack(pady=5)

        tk.Button(
            self.window,
            text="Submit Reservation Request",
            command=self.submit,
            bg="#2196F3",
            fg="white",
            width=28
        ).pack(pady=15)

    def submit(self):

        quantity = self.quantity_var.get().strip()
        date = self.date_entry.get().strip()
        start = self.start_entry.get().strip()
        end = self.end_entry.get().strip()

        purpose = self.purpose_text.get(
            "1.0",
            tk.END
        ).strip()

        remarks = self.remarks_text.get(
            "1.0",
            tk.END
        ).strip()

        success, msg = self.controller.create_reservation(
            username=self.username,
            asset_id=self.item[0],
            quantity=quantity,
            reservation_date=date,
            start_time=start,
            end_time=end,
            purpose=purpose,
            remarks=remarks
        )

        if success:
            messagebox.showinfo(
                "Reservation",
                msg,
                parent=self.window
            )

            if self.on_success:
                self.on_success()

            self.window.destroy()

        else:
            messagebox.showerror(
                "Reservation Error",
                msg,
                parent=self.window
            )
