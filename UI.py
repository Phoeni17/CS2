from tkinter import *
from tkinter.messagebox import showinfo, showwarning

import cv2
from PIL import Image, ImageTk

window = Tk()
window.title("Xe nha la vuon")
window.geometry("1280x720")
window.resizable(False, False)

bg = cv2.imread("fieldd.jpg")
bg = cv2.cvtColor(bg, cv2.COLOR_BGR2RGB)
bg_re = cv2.resize(bg, (1280, 720))

bg_pil = Image.fromarray(bg_re)

bg_image = ImageTk.PhotoImage(bg_pil)

background_label = Label(window, image=bg_image)
background_label.image = bg_image
background_label.place(x=0, y=0, relwidth=1, relheight=1)

text_label = Label(window,text="HELLO",font=("Arial", 60, "bold"), fg="white", bg='#000000')
text_label.place(relx=0.5, rely=0.5, anchor="center")

window.mainloop()
