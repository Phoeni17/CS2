import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports
import threading
import time
import re

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


root = tk.Tk()
root.title("Garden System")
root.geometry("400x300")

moisture_window = tk.Toplevel(root)
moisture_window.title("Moisture Sensor")
moisture_window.geometry("350x300")
moisture_window.withdraw()


def open_moisture_window():
    root.withdraw()
    moisture_window.deiconify()

    moisture_window.after(300, auto_connect)


welcome_label = ttk.Label(
    root,
    text="Welcome to the Garden",
    font=("Arial", 20, "bold")
)
welcome_label.pack(pady=40)

moisture_btn = ttk.Button(
    root, text="Moisture Check", command=open_moisture_window
)
moisture_btn.pack(pady=10)


moisture_value = tk.StringVar(value="---")

ttk.Label(
    moisture_window, text="Moisture Sensor Reader",
    font=("Arial", 14, "bold")
).pack(pady=5)

ttk.Label(
    moisture_window, text="Value:", font=("Arial", 12)
).pack(pady=10)

moisture_label = ttk.Label(
    moisture_window,
    textvariable=moisture_value,
    font=("Arial", 28, "bold")
)
moisture_label.pack()

ttk.Button(
    moisture_window, text="Disconnect", command=disconnect
).pack(pady=10)

status_label = ttk.Label(
    moisture_window, text="Waiting...", foreground="orange"
)
status_label.pack(pady=10)


root.mainloop()
