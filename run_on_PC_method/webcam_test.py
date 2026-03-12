import tkinter as tk
from tkinter import filedialog,messagebox
from tkinter import ttk
import tensorflow as tf
from keras.layers import TFSMLayer
import numpy as np
import cv2
import requests
import time
from PIL import Image, ImageTk



classes = []
show_feed=False
frame_height=244
frame_width=244


progress_bars = {}
confidence_labels = {}

def setClasses(filepath):
    with open(filepath,"r") as f:
        lines = f.readlines()
        for line in lines:
            classes.append(line[2:].strip())


def createNewUI():
    select_button.pack_forget()
    label.pack_forget()

    left_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
    right_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
    bottom_frame.grid(row=2, column=0,columnspan=2, sticky="nsew", padx=10, pady=10)

    title.grid(row=0,column=0,columnspan=2)
    display_image.pack()
    prediction_label.pack(pady=10)
    confidence_frame.pack(fill="x", padx=10)
    change_model_button.pack()
    

    for class_string in classes:

        row = tk.Frame(confidence_frame)
        row.pack(fill="x", pady=5)

        name_label = tk.Label(row, text=class_string, width=12, anchor="w")
        name_label.pack(side="left")

        bar = ttk.Progressbar(row, length=150, maximum=100)
        bar.pack(side="left", padx=5)

        conf_label = tk.Label(row, text="0.00")
        conf_label.pack(side="left")

        progress_bars[class_string] = bar
        confidence_labels[class_string] = conf_label

def updateChart(preds,class_index):
    prediction_label.config(text=f"Prediction: {classes[class_index]}:({preds[class_index]*100:.2f}%)")
    for i, class_string in enumerate(classes):

        pred = preds[i]

        progress_bars[class_string]["value"] = pred * 100
        confidence_labels[class_string].config(text=f"{pred:.2f}")

        if class_string == classes[class_index]:
            confidence_labels[class_string].config(font=("Segoe UI", 10, "bold"))
        else:
            confidence_labels[class_string].config(font=("Segoe UI", 10))


def runModel(model,cap,previous_time):

    ret, frame = cap.read()
    if not ret:
        messagebox.showwarning("cannot connect to sorting machine!")

    """current_time=time.time()
    delta_time=current_time-previous_time
    previous_time=time.time()
    with open("data.csv", "a") as f:
        f.write(f"{delta_time},{1/delta_time}\n")"""

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    resized = cv2.resize(frame_rgb, (frame_height, frame_width))  
    normalized = resized / 255.0
    input_data = np.expand_dims(normalized, axis=0)
    
    prediction = model(input_data)

    for x in prediction:
        prediction = prediction[x].numpy()
   
    class_index = np.argmax(prediction)

    confidence = float(np.max(prediction))

    updateChart(prediction[0],class_index)
 
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    img = Image.fromarray(frame_rgb)
    imgtk = ImageTk.PhotoImage(image=img)

    display_image.imgtk = imgtk
    display_image.configure(image=imgtk)

    root.after(30, lambda: runModel(model, cap,previous_time))


def selectFile():
   
    folder_path = filedialog.askdirectory(title="Select Folder")
    setClasses(f"{folder_path}/labels.txt")
    folder_path+="/model.savedmodel"


    if folder_path: 
        createNewUI()
        model = TFSMLayer(folder_path, call_endpoint="serving_default")
        cap = cv2.VideoCapture(0)
        #previous_time=time.time()
        runModel(model,cap,0)
    else:
        messagebox.showwarning("No Selection", "No folder selected!")


root = tk.Tk()
root.title("AI hopper sorter")
root.rowconfigure(1, weight=1)

root.columnconfigure(0, weight=3)
root.columnconfigure(1, weight=1)

left_frame = tk.Frame(root, bg="#1e1e1e")

right_frame = tk.Frame(root, bg="#f5f5f5")

bottom_frame=tk.Frame(root,bg="#2c3e50",)


title = tk.Label(root,text="AI Hopper Sorter",font=("Segoe UI", 22, "bold"),bg="#2c3e50",fg="white",pady=10)

label = tk.Label(root, text="Select a Teachable Machine saved model", pady=20)
label.pack()

display_image=tk.Label(left_frame,bg="black")

prediction_label = tk.Label(right_frame,text="",font=("Segoe UI", 18, "bold"))

confidence_frame = tk.Frame(right_frame)

select_button = tk.Button(root, text="Select Model", width=20, height=2, command=selectFile)
select_button.pack()

change_model_button = tk.Button(bottom_frame, text="Change Model", bg="#3498db", fg="white", activebackground="#2980b9", relief="flat", width=20, height=2, command=selectFile)
#poopoo

root.mainloop()