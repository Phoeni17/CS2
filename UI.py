import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import serial
import serial.tools.list_ports
import threading
import time
import os

USER_FILE = "users.txt"
WINDOW_W = 1280
WINDOW_H = 720

serial_port = None
running = False
moisture_value = None
moisture_status = None

# -----------------------------
# USER STORAGE
# -----------------------------
def load_users():
    if not os.path.exists(USER_FILE):
        return {}
    users = {}
    with open(USER_FILE, "r") as f:
        for line in f:
            if ":" in line:
                name, pw = line.strip().split(":", 1)
                users[name] = pw
    return users

def save_user(username, password):
    with open(USER_FILE, "a") as f:
        f.write(f"{username}:{password}\n")

# -----------------------------
# WINDOW FACTORY
# -----------------------------
def create_window(title, is_root=False):
    if is_root:
        win = root
    else:
        win = tk.Toplevel()
    win.title(title)
    win.geometry(f"{WINDOW_W}x{WINDOW_H}")
    win.resizable(False, False)
    img = Image.open("fieldd.jpg")
    img = img.resize((WINDOW_W, WINDOW_H))
    bg = ImageTk.PhotoImage(img)
    bg_label = tk.Label(win, image=bg)
    bg_label.image = bg
    bg_label.place(x=0, y=0, relwidth=1, relheight=1)
    return win

# -----------------------------
# SERIAL AUTO CONNECT
# -----------------------------
def detect_arduino_port():
    ports = serial.tools.list_ports.comports()
    for p in ports:
        name = p.device.lower()
        desc = p.description.lower()
        if ("arduino" in desc or "ch340" in desc or "usbserial" in name or "usbmodem" in name):
            return p.device
    return None

def auto_connect():
    global serial_port, running
    port = detect_arduino_port()
    if not port:
        status_label.config(text="Arduino Not Found", fg="red")
        return
    try:
        serial_port = serial.Serial(port, 115200, timeout=1)
        running = True
        status_label.config(text=f"Connected on {port}", fg="green")
    except Exception as e:
        status_label.config(text="Connection Failed", fg="red")
        messagebox.showerror("Serial Error", str(e))

def send_cmd(cmd):
    if serial_port and serial_port.is_open:
        serial_port.write(cmd.encode())

# -----------------------------
# LOGIN SCREEN
# -----------------------------
def login_screen():
    win = create_window("Login")
    users = load_users()
    tk.Label(win, text="Hello", font=("Arial", 50), bg="white", fg="black").pack(pady=50)
    tk.Label(win, text="Username:", font=("Arial", 20), bg="white", fg="black").pack()
    user_entry = tk.Entry(win, font=("Arial", 20))
    user_entry.pack()
    tk.Label(win, text="Password:", font=("Arial", 20), bg="white", fg="black").pack()
    pass_entry = tk.Entry(win, font=("Arial", 20), show="*")
    pass_entry.pack()

    def login():
        username = user_entry.get()
        pw = pass_entry.get()
        if username in users and users[username] == pw:
            messagebox.showinfo("Welcome", f"Hello {username}!")
            win.withdraw()
            dashboard(win)
        else:
            messagebox.showerror("Error", "Invalid Login")

    tk.Button(win, text="Login", font=("Arial", 18), width=15, command=login).pack(pady=15)
    tk.Button(win, text="Sign Up", font=("Arial", 14), command=lambda: (win.destroy(), signup_screen())).pack()

# -----------------------------
# SIGN UP SCREEN
# -----------------------------
def signup_screen():
    win = create_window("Sign Up")
    tk.Label(win, text="Create Account", font=("Arial", 40), bg="white", fg="black").pack(pady=40)
    tk.Label(win, text="New Username:", font=("Arial", 18), bg="white", fg="black").pack()
    new_user = tk.Entry(win, font=("Arial", 18))
    new_user.pack()
    tk.Label(win, text="New Password:", font=("Arial", 18), bg="white", fg="black").pack()
    new_pass = tk.Entry(win, font=("Arial", 18), show="*")
    new_pass.pack()

    def create():
        user = new_user.get()
        pw = new_pass.get()
        users = load_users()
        if not user or not pw:
            messagebox.showerror("Error", "Fields required")
        elif user in users:
            messagebox.showerror("Error", "User exists")
        else:
            save_user(user, pw)
            messagebox.showinfo("OK", "User created!")
            win.destroy()
            login_screen()

    tk.Button(win, text="Register", font=("Arial", 18), width=15, command=create).pack(pady=20)
    tk.Button(win, text="Back to Login", font=("Arial", 14), command=lambda: (win.destroy(), login_screen())).pack()

# -----------------------------
# DASHBOARD
# -----------------------------
def dashboard(prev_win):
    prev_win.withdraw()
    win = create_window("Dashboard")
    tk.Label(win, text="Dashboard", font=("Arial", 50), bg="white", fg='black').pack(pady=50)

    tk.Button(win, text="Moisture check", font=("Arial", 22), width=20, command=lambda: moisture_window(win)).pack(pady=20)
    tk.Button(win, text="Watering", font=("Arial", 22), width=20, command=lambda: watering_window(win)).pack(pady=20)
    tk.Button(win, text="Roof Control", font=("Arial", 22), width=20, command=lambda: doors_window(win)).pack(pady=20)

    global status_label
    status_label = tk.Label(win, text="Disconnected", font=("Arial", 18), bg="white", fg="black")
    status_label.place(x=10, y=WINDOW_H - 50)

    logout_btn = tk.Button(win, text="Logout", font=("Arial", 18), width=15, command=lambda: (win.destroy(), login_screen()))
    logout_btn.place(x=10, y=WINDOW_H - 100)

# -----------------------------
# MOISTURE WINDOW
# -----------------------------
def moisture_window(prev_win):
    global moisture_value, moisture_status
    moisture_value = tk.StringVar(value="---")
    moisture_status = tk.StringVar(value="---")
    win = create_window("Moisture Sensor")
    prev_win.withdraw()

    tk.Label(win, text="Moisture Sensor", font=("Arial", 40), bg="white", fg="black").pack(pady=20)
    tk.Label(win, textvariable=moisture_value, font=("Arial", 50), bg="white", fg="black").pack(pady=10)
    status_label_widget = tk.Label(win, textvariable=moisture_status, font=("Arial", 36), bg="white")
    status_label_widget.pack(pady=10)
    tk.Button(win, text="Back", font=("Arial", 18), command=lambda: (win.destroy(), prev_win.deiconify())).pack(pady=30)

    auto_connect()

    def update_moisture():
        try:
            if serial_port and serial_port.in_waiting > 0:
                line = serial_port.readline().decode(errors="ignore").strip()
                if line.startswith("MOISTURE:"):
                    try:
                        val = int(line.split(":")[1].strip())
                        moisture_value.set(val)
                        if val <= 80:
                            moisture_status.set("Dry")
                            status_label_widget.config(fg="red")
                        elif val <= 120:
                            moisture_status.set("Normal")
                            status_label_widget.config(fg="green")
                        else:
                            moisture_status.set("Wet")
                            status_label_widget.config(fg="blue")
                    except:
                        pass
        except:
            pass
        win.after(300, update_moisture)

    update_moisture()

# -----------------------------
# WATERING WINDOW
# -----------------------------
def watering_window(prev_win):
    win = create_window("Watering System")
    prev_win.withdraw()
    tk.Label(win, text="Watering System", font=("Arial", 40), bg="white", fg="black").pack(pady=30)
    tk.Button(win, text="Start Watering", font=("Arial", 22), width=18, command=lambda: send_cmd("W")).pack(pady=20)
    tk.Button(win, text="Stop Watering", font=("Arial", 22), width=18, command=lambda: send_cmd("X")).pack(pady=20)
    tk.Button(win, text="Back", font=("Arial", 18), width=15, command=lambda: (win.destroy(), prev_win.deiconify())).pack(pady=30)

# -----------------------------
# ROOF CONTROL WINDOW
# -----------------------------
def doors_window(prev_win):
    win = create_window("Roof Control")
    prev_win.withdraw()
    tk.Label(win, text="Roof Control", font=("Arial", 40), bg="white", fg="black").pack(pady=20)
    status_label = tk.Label(win, text="Roof Stopped", font=("Arial", 24), bg="white", fg="black")
    status_label.pack(pady=20)

    def update_status(txt):
        status_label.config(text=f"Roof {txt}")

    tk.Button(win, text="Open", font=("Arial", 18), width=12, command=lambda: [send_cmd("O"), update_status("Opening")]).pack(side="left", padx=20)
    tk.Button(win, text="Close", font=("Arial", 18), width=12, command=lambda: [send_cmd("C"), update_status("Closing")]).pack(side="left", padx=20)
    tk.Button(win, text="Stop", font=("Arial", 18), width=12, command=lambda: [send_cmd("S"), update_status("Stopped")]).pack(side="left", padx=20)
    tk.Button(win, text="Back", font=("Arial", 18), width=12, command=lambda: (win.destroy(), prev_win.deiconify())).pack(pady=30)

# -----------------------------
# MAIN
# -----------------------------
root = tk.Tk()
root.withdraw()
root = create_window("System", is_root=True)
login_screen()
root.mainloop()
