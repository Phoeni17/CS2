from tkinter import *
from tkinter.messagebox import showinfo, showerror
import tkinter as tk
from tkinter import ttk
import cv2
from PIL import Image, ImageTk

import serial
import serial.tools.list_ports
import threading
import time
import re


# ===================================
# USER SYSTEM
# ===================================
def load_users():
    users = {}
    try:
        with open("users.txt", "r") as f:
            for line in f:
                if ":" in line:
                    user, pw = line.strip().split(":", 1)
                    users[user] = pw
    except FileNotFoundError:
        pass
    return users


def save_user(username, password):
    with open("users.txt", "a") as f:
        f.write(f"{username}:{password}\n")


users = load_users()

# ===================================
# LOGIN WINDOW
# ===================================
window = Tk()
window.title("Xe nha la vuon")
window.geometry("1280x720")
window.resizable(False, False)

bg = cv2.imread("fieldd.jpg")
bg = cv2.cvtColor(bg, cv2.COLOR_BGR2RGB)
bg = cv2.resize(bg, (1280, 720))
bg_pil = Image.fromarray(bg)
bg_image = ImageTk.PhotoImage(bg_pil)

background_label = Label(window, image=bg_image)
background_label.place(x=0, y=0, relwidth=1, relheight=1)


def login(event=None):
    username = username_entry.get()
    password = password_entry.get()

    if username in users and users[username] == password:
        showinfo("Login Successful", f"Welcome, {username}!")
        window.destroy()
        open_moisture_system()
    else:
        showerror("Login Failed", "Incorrect username or password!")


def open_signup():
    signup = Toplevel(window)
    signup.title("Sign Up")
    signup.geometry("1280x720")
    signup.resizable(False, False)

    Label(signup, text="Create Account", font=("Arial", 24, "bold")).pack(pady=20)

    Label(signup, text="New Username:", font=("Arial", 14)).pack()
    new_user = Entry(signup, font=("Arial", 14))
    new_user.pack(pady=5)

    Label(signup, text="New Password:", font=("Arial", 14)).pack()
    new_pass = Entry(signup, show="*", font=("Arial", 14))
    new_pass.pack(pady=5)

    Label(signup, text="Confirm Password:", font=("Arial", 14)).pack()
    confirm_pass = Entry(signup, show="*", font=("Arial", 14))
    confirm_pass.pack(pady=5)

    def register():
        user = new_user.get()
        pw1 = new_pass.get()
        pw2 = confirm_pass.get()

        if not user or not pw1 or not pw2:
            showerror("Error", "All fields are required!")
            return

        if user in users:
            showerror("Error", "Username already exists!")
            return

        if pw1 != pw2:
            showerror("Error", "Passwords do not match!")
            return

        save_user(user, pw1)
        users[user] = pw1

        showinfo("Success", "Account created successfully!")
        signup.destroy()

    Button(signup, text="Create Account", font=("Arial", 16), command=register).pack(pady=20)


title_label = Label(window, text="HELLO", font=("Arial", 60, "bold"), fg="white", bg="black")
title_label.place(relx=0.5, rely=0.15, anchor="center")

username_label = Label(window, text="Username:", font=("Arial", 20, "bold"), fg="white", bg="black")
username_label.place(relx=0.4, rely=0.33, anchor="e")

username_entry = Entry(window, font=("Arial", 20), width=20)
username_entry.place(relx=0.41, rely=0.33, anchor="w")

password_label = Label(window, text="Password:", font=("Arial", 20, "bold"), fg="white", bg="black")
password_label.place(relx=0.4, rely=0.43, anchor="e")

password_entry = Entry(window, font=("Arial", 20), width=20, show="*")
password_entry.place(relx=0.41, rely=0.43, anchor="w")


def on_enter(e):
    login_button["background"] = "#5599ff"


def on_leave(e):
    login_button["background"] = "#3366cc"


login_button = Button(
    window, text="Login", font=("Arial", 20, "bold"),
    fg="white", bg="#3366cc", activebackground="#4477dd",
    width=12, height=1, bd=0, relief="flat", command=login
)
login_button.place(relx=0.5, rely=0.55, anchor="center")

login_button.bind("<Enter>", on_enter)
login_button.bind("<Leave>", on_leave)

signup_button = Button(
    window, text="Sign Up", font=("Arial", 14),
    fg="black", bg="white", width=10, command=open_signup
)
signup_button.place(relx=0.5, rely=0.63, anchor="center")

window.bind("<Return>", login)
username_entry.focus()

# ===================================
# MOISTURE SYSTEM WINDOW
# ===================================
serial_port = None
running = False


def detect_arduino_port():
    ports = serial.tools.list_ports.comports()

    for p in ports:
        name = p.device.lower()
        desc = p.description.lower()

        if ("arduino" in desc or
                "ch340" in desc or
                "usbserial" in name or
                "usbmodem" in name):
            return p.device

    return None


def auto_connect():
    global serial_port, running

    port = detect_arduino_port()

    if not port:
        status_label.config(text="Arduino not found", foreground="red")
        return

    try:
        serial_port = serial.Serial(port, 9600, timeout=1)
        running = True
        status_label.config(text=f"Connected on {port}", foreground="green")

        threading.Thread(target=read_serial_loop, daemon=True).start()

    except Exception as e:
        status_label.config(text="Connection failed", foreground="red")
        messagebox.showerror("Connection Failed", str(e))


def disconnect():
    global serial_port, running
    running = False
    time.sleep(0.1)

    if serial_port and serial_port.is_open:
        serial_port.close()

    status_label.config(text="Disconnected", foreground="red")


def read_serial_loop():
    global running
    while running:
        try:
            if serial_port.in_waiting > 0:
                line = serial_port.readline().decode(errors="ignore").strip()
                numbers = re.findall(r"\d+", line)
                if numbers:
                    moisture_value.set(numbers[-1])
        except:
            pass

        time.sleep(0.1)


def open_moisture_system():
    root = tk.Tk()
    root.title("Garden System")

    # Change this when you add a background image!
    root.geometry("1280x720")

    def open_window():
        root.withdraw()
        moisture_window.deiconify()
        moisture_window.after(300, auto_connect)

    welcome_label = ttk.Label(
        root, text="Welcome to the Garden", font=("Arial", 20, "bold")
    )
    welcome_label.pack(pady=40)

    moisture_btn = ttk.Button(root, text="Moisture Check", command=open_window)
    moisture_btn.pack(pady=10)

    # Moisture Window
    global moisture_value, status_label

    moisture_window = tk.Toplevel(root)
    moisture_window.title("Moisture Sensor")
    moisture_window.geometry("1280x720")
    moisture_window.withdraw()

    moisture_value = tk.StringVar(value="---")

    ttk.Label(
        moisture_window, text="Moisture Sensor Reader", font=("Arial", 14, "bold")
    ).pack(pady=5)

    ttk.Label(moisture_window, text="Value:", font=("Arial", 12)).pack(pady=10)

    moisture_label = ttk.Label(
        moisture_window, textvariable=moisture_value, font=("Arial", 28, "bold")
    )
    moisture_label.pack()

    ttk.Button(moisture_window, text="Disconnect", command=disconnect).pack(pady=10)

    status_label = ttk.Label(moisture_window, text="Waiting...", foreground="orange")
    status_label.pack(pady=10)

    root.mainloop()


window.mainloop()
