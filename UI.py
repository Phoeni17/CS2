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
        serial_port = serial.Serial(port, 9600, timeout=1)
        running = True
        status_label.config(text=f"Connected on {port}", fg="green")
        threading.Thread(target=read_serial_loop, daemon=True).start()
    except Exception as e:
        status_label.config(text="Connection Failed", fg="red")
        messagebox.showerror("Serial Error", str(e))

def disconnect():
    global running, serial_port
    running = False
    if serial_port and serial_port.is_open:
        serial_port.close()
    status_label.config(text="Disconnected", fg="red")

def read_serial_loop():
    global running
    while running:
        try:
            if serial_port.in_waiting > 0:
                line = serial_port.readline().decode(errors="ignore").strip()
                if line.isdigit():
                    moisture_value.set(line)
        except:
            pass
        time.sleep(0.1)

# -----------------------------
# LOGIN SCREEN
# -----------------------------
def login_screen():
    win = create_window("Login")

    users = load_users()

    tk.Label(win, text="Hello", font=("Arial", 50), bg="white").pack(pady=50)

    tk.Label(win, text="Username:", font=("Arial", 20), bg="white").pack()
    user_entry = tk.Entry(win, font=("Arial", 20))
    user_entry.pack()

    tk.Label(win, text="Password:", font=("Arial", 20), bg="white").pack()
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
    tk.Button(win, text="Sign Up", font=("Arial", 14), command=signup_screen).pack()

# -----------------------------
# SIGN UP SCREEN
# -----------------------------
def signup_screen():
    win = create_window("Sign Up")

    users = load_users()

    tk.Label(win, text="Create Account", font=("Arial", 40), bg="white").pack(pady=40)

    tk.Label(win, text="New Username:", font=("Arial", 18), bg="white").pack()
    new_user = tk.Entry(win, font=("Arial", 18))
    new_user.pack()

    tk.Label(win, text="New Password:", font=("Arial", 18), bg="white").pack()
    new_pass = tk.Entry(win, font=("Arial", 18), show="*")
    new_pass.pack()

    def create():
        user = new_user.get()
        pw = new_pass.get()

        if not user or not pw:
            messagebox.showerror("Error", "Fields required")
        elif user in users:
            messagebox.showerror("Error", "User exists")
        else:
            save_user(user, pw)
            messagebox.showinfo("OK", "User created!")
            win.withdraw()
            login_screen(win)

    tk.Button(win, text="Register", font=("Arial", 18), width=15, command=create).pack(pady=20)

# -----------------------------
# DASHBOARD
# -----------------------------
def dashboard(previous_window):
    previous_window.withdraw()
    win = create_window("Dashboard")

    tk.Label(win, text="Dashboard", font=("Arial", 50), bg="white").pack(pady=50)

    # Moisture button
    tk.Button(
        win,
        text="Moisture Window",
        font=("Arial", 22),
        width=20,
        command=lambda: moisture_window(win)
    ).pack(pady=20)

    # Doors button
    tk.Button(
        win,
        text="Doors",
        font=("Arial", 22),
        width=20,
        command=lambda: doors_window(win)
    ).pack(pady=20)

    # Logout button at bottom-left using x and y
    logout_btn = tk.Button(
        win,
        text="Logout",
        font=("Arial", 18),
        width=15,
        command=lambda: (win.destroy(), login_screen())
    )
    # Position: 10 px from left, 20 px from bottom
    logout_btn.place(x=10, y=WINDOW_H - 50)

# -----------------------------
# MOISTURE WINDOW
# -----------------------------
def moisture_window(prev_win):
    global moisture_value, status_label

    moisture_value = tk.StringVar(value="---")
    status_text = tk.StringVar(value="---")  # For Dry/Normal/Wet
    win = create_window("Moisture Sensor")
    prev_win.withdraw()  # hide dashboard

    tk.Label(win, text="Moisture Sensor", font=("Arial", 40), bg="white").pack(pady=20)

    # Frame to hold value + status side by side
    frame = tk.Frame(win, bg="white")
    frame.pack(pady=10)

    # Moisture numeric value
    val_label = tk.Label(frame, textvariable=moisture_value, font=("Arial", 50), bg="white")
    val_label.pack(side="left", padx=20)

    # Moisture status
    status_label_local = tk.Label(frame, textvariable=status_text, font=("Arial", 40), bg="white")
    status_label_local.pack(side="left", padx=20)

    # Status logic updater
    def update_status(*args):
        try:
            val = int(moisture_value.get())
        except:
            status_text.set("---")
            status_label_local.config(fg="black")
            return

        if 0 <= val <= 80:
            status_text.set("Dry")
            status_label_local.config(fg="red")
        elif 81 <= val <= 120:
            status_text.set("Normal")
            status_label_local.config(fg="green")
        elif val >= 121:
            status_text.set("Wet")
            status_label_local.config(fg="blue")
        else:
            status_text.set("---")
            status_label_local.config(fg="black")

    # Trigger whenever moisture_value changes
    moisture_value.trace_add("write", update_status)

    # Arduino connection status
    status_label = tk.Label(win, text="Connecting...", font=("Arial", 18), bg="white")
    status_label.pack(pady=15)

    tk.Button(win, text="Disconnect", font=("Arial", 18), command=disconnect).pack(pady=15)

    tk.Button(
        win, text="Back", font=("Arial", 18),
        command=lambda: (disconnect(), win.destroy(), prev_win.deiconify())
    ).pack(pady=10)

    win.after(300, auto_connect)

# -----------------------------
# DOORS WINDOW
# -----------------------------
def doors_window(prev_win):
    win = create_window("Doors Control")
    prev_win.withdraw()  # hide dashboard

    tk.Label(win, text="Doors Control", font=("Arial", 40), bg="white").pack(pady=20)

    # Frame for radio buttons
    radio_frame = tk.Frame(win, bg="white")
    radio_frame.pack(pady=10)

    selected = tk.StringVar(value="roof")  # default selection

    tk.Radiobutton(radio_frame, text="Roof", variable=selected, value="roof", font=("Arial", 20), bg="white").pack(side="left", padx=20)
    tk.Radiobutton(radio_frame, text="Door", variable=selected, value="door", font=("Arial", 20), bg="white").pack(side="left", padx=20)

    # Indicator for open/close status
    status_dict = {"roof": "Closed", "door": "Closed"}  # initial state
    status_label = tk.Label(win, text=f"{selected.get().capitalize()} is {status_dict[selected.get()]}", font=("Arial", 24), bg="white")
    status_label.pack(pady=20)

    # Function to update indicator
    def update_status():
        status_label.config(text=f"{selected.get().capitalize()} is {status_dict[selected.get()]}")

    # Open/Close functions
    def open_item():
        item = selected.get()
        status_dict[item] = "Open"
        update_status()
        # Here you could add actual hardware control code

    def close_item():
        item = selected.get()
        status_dict[item] = "Closed"
        update_status()
        # Here you could add actual hardware control code

    # Buttons
    btn_frame = tk.Frame(win, bg="white")
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="Open", font=("Arial", 18), width=10, command=open_item).pack(side="left", padx=20)
    tk.Button(btn_frame, text="Close", font=("Arial", 18), width=10, command=close_item).pack(side="left", padx=20)

    # Back button
    tk.Button(win, text="Back", font=("Arial", 18), command=lambda: (win.destroy(), prev_win.deiconify())).pack(pady=30)



# -----------------------------
# MAIN
# -----------------------------
root = tk.Tk()
root.withdraw()

root = create_window("System", is_root=True)
login_screen()

root.mainloop()
