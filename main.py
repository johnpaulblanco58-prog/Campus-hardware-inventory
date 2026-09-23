#main.py#

import sys
import os
import tkinter as tk

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from logger import logger
from models.database import init_db
from views.login_view import LoginWindow
from views.tracker_view import TrackerWindow


def clear_window():
    for widget in root.winfo_children():
        widget.destroy()


def launch_main_app(username, role):
    clear_window()

    TrackerWindow(
        root,
        username=username,
        role=role,
        on_logout=show_login
    )


def show_login():
    clear_window()

    LoginWindow(
        root,
        on_login_success=launch_main_app
    )


if __name__ == "__main__":
    init_db()

    root = tk.Tk()

    logger.info("Application started.")

    show_login()

    root.mainloop()