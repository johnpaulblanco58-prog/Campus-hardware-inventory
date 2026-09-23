########login_view.py######

import tkinter as tk
from tkinter import messagebox

from controllers.auth_controller import AuthController


class LoginWindow:

    def __init__(
        self,
        root,
        on_login_success
    ):
        self.root = root
        self.on_login_success = on_login_success
        self.auth = AuthController()
        self.register_mode = False

        self.root.title(
            "Engineering Laboratory System - Login"
        )

        self.root.geometry(
            "420x400"
        )

        self.root.resizable(
            False,
            False
        )

        self.title_label = tk.Label(
            root,
            text="User Authentication",
            font=("Arial", 14, "bold")
        )

        self.title_label.pack(
            pady=15
        )

        tk.Label(
            root,
            text="Username:"
        ).pack()

        self.entry_user = tk.Entry(
            root,
            width=32
        )

        self.entry_user.pack(
            pady=(0, 10)
        )

        self.email_label = tk.Label(
            root,
            text="Email Address:"
        )

        self.entry_email = tk.Entry(
            root,
            width=32
        )

        self.role_label = tk.Label(
            root,
            text="Role:"
        )

        self.role = tk.StringVar(
            value="User"
        )

        self.role_menu = tk.OptionMenu(
            root,
            self.role,
            "User",
            "Admin"
        )

        tk.Label(
            root,
            text="Password:"
        ).pack()

        self.entry_pass = tk.Entry(
            root,
            show="*",
            width=32
        )

        self.entry_pass.pack(
            pady=(0, 5)
        )

        self.show_password = tk.BooleanVar(
            value=False
        )

        tk.Checkbutton(
            root,
            text="Show Password",
            variable=self.show_password,
            command=self.toggle_password
        ).pack(
            pady=(0, 15)
        )

        btn_frame = tk.Frame(root)
        btn_frame.pack()

        self.login_button = tk.Button(
            btn_frame,
            text="Login",
            command=self.handle_login,
            bg="#4CAF50",
            fg="white",
            width=12
        )

        self.login_button.pack(
            side="left",
            padx=5
        )

        self.register_button = tk.Button(
            btn_frame,
            text="Register",
            command=self.toggle_register,
            bg="#2196F3",
            fg="white",
            width=12
        )

        self.register_button.pack(
            side="right",
            padx=5
        )

        self.verify_button = tk.Button(
            root,
            text="Verify Account",
            command=self.verify_account
        )

        self.verify_button.pack(
            pady=8
        )

        self.reset_button = tk.Button(
            root,
            text="Reset / Unlock Password",
            command=self.reset_password
        )

        self.reset_button.pack(
            pady=5
        )

    def toggle_password(self):
        if self.show_password.get():
            self.entry_pass.config(show="")
        else:
            self.entry_pass.config(show="*")

    def toggle_register(self):
        if self.register_mode:
            self.show_login()
        else:
            self.show_register()

    def show_register(self):
        self.register_mode = True

        self.root.geometry(
            "420x500"
        )

        self.title_label.config(
            text="User Registration"
        )

        self.email_label.pack(
            after=self.entry_user
        )

        self.entry_email.pack(
            after=self.email_label,
            pady=(0, 10)
        )

        self.role_label.pack(
            after=self.entry_email
        )

        self.role_menu.pack(
            after=self.role_label,
            pady=(0, 10)
        )

        self.login_button.config(
            text="Back to Login",
            command=self.show_login
        )

        self.register_button.config(
            text="Create Account",
            command=self.register_account
        )

        self.verify_button.pack_forget()
        self.reset_button.pack_forget()

    def show_login(self):
        self.register_mode = False

        self.root.geometry(
            "420x400"
        )

        self.title_label.config(
            text="User Authentication"
        )

        self.email_label.pack_forget()
        self.entry_email.pack_forget()

        self.role_label.pack_forget()
        self.role_menu.pack_forget()

        self.login_button.config(
            text="Login",
            command=self.handle_login
        )

        self.register_button.config(
            text="Register",
            command=self.toggle_register
        )

        self.verify_button.pack(
            pady=8
        )

        self.reset_button.pack(
            pady=5
        )

    def handle_login(self):
        username = self.entry_user.get().strip()
        password = self.entry_pass.get().strip()

        success, msg, locked, role = self.auth.login_user(
            username,
            password
        )

        if success:
            messagebox.showinfo(
                "Success",
                msg
            )

            self.on_login_success(
                username,
                role
            )

        elif locked:
            messagebox.showwarning(
                "Account Locked",
                msg
            )

        else:
            messagebox.showerror(
                "Authentication Failed",
                msg
            )

    def register_account(self):
        username = self.entry_user.get().strip()
        email = self.entry_email.get().strip()
        password = self.entry_pass.get().strip()
        role = self.role.get().lower()

        success, msg = self.auth.register_user(
            username,
            email,
            password,
            role
        )

        if success:
            messagebox.showinfo(
                "Registration",
                msg
            )

            self.clear_fields()
            self.show_login()

        else:
            messagebox.showwarning(
                "Registration Alert",
                msg
            )

    def verify_account(self):
        window = tk.Toplevel(
            self.root
        )

        window.title(
            "Account Verification"
        )

        window.geometry(
            "350x250"
        )

        window.resizable(
            False,
            False
        )

        window.transient(
            self.root
        )

        window.grab_set()

        tk.Label(
            window,
            text="Verify Account",
            font=("Arial", 13, "bold")
        ).pack(pady=15)

        tk.Label(
            window,
            text="Username:"
        ).pack()

        username_entry = tk.Entry(
            window,
            width=30
        )

        username_entry.pack(
            pady=5
        )

        tk.Label(
            window,
            text="Verification Code:"
        ).pack()

        code_entry = tk.Entry(
            window,
            width=30
        )

        code_entry.pack(
            pady=5
        )

        def submit():
            success, msg = self.auth.verify_account(
                username_entry.get().strip(),
                code_entry.get().strip()
            )

            if success:
                messagebox.showinfo(
                    "Verification",
                    msg,
                    parent=window
                )

                window.destroy()

            else:
                messagebox.showerror(
                    "Verification",
                    msg,
                    parent=window
                )

        tk.Button(
            window,
            text="Verify",
            command=submit,
            bg="#4CAF50",
            fg="white",
            width=15
        ).pack(
            pady=15
        )

    def reset_password(self):
        window = tk.Toplevel(
            self.root
        )

        window.title(
            "Reset / Unlock Password"
        )

        window.geometry(
            "350x260"
        )

        window.resizable(
            False,
            False
        )

        window.transient(
            self.root
        )

        window.grab_set()

        tk.Label(
            window,
            text="Password Reset Request",
            font=("Arial", 13, "bold")
        ).pack(
            pady=15
        )

        tk.Label(
            window,
            text="Registered Email:"
        ).pack()

        email_entry = tk.Entry(
            window,
            width=32
        )

        email_entry.pack(
            pady=5
        )

        tk.Label(
            window,
            text="New Password:"
        ).pack()

        password_entry = tk.Entry(
            window,
            show="*",
            width=32
        )

        password_entry.pack(
            pady=5
        )

        def submit():
            success, msg = self.auth.request_password_reset(
                email_entry.get().strip(),
                password_entry.get().strip()
            )

            if success:
                messagebox.showinfo(
                    "Request Submitted",
                    msg,
                    parent=window
                )

                window.destroy()

            else:
                messagebox.showwarning(
                    "Reset Request",
                    msg,
                    parent=window
                )

        tk.Button(
            window,
            text="Submit Request",
            command=submit,
            bg="#2196F3",
            fg="white",
            width=18
        ).pack(
            pady=15
        )

    def clear_fields(self):
        self.entry_user.delete(
            0,
            tk.END
        )

        self.entry_email.delete(
            0,
            tk.END
        )

        self.entry_pass.delete(
            0,
            tk.END
        )

        self.show_password.set(
            False
        )

        self.entry_pass.config(
            show="*"
        )

