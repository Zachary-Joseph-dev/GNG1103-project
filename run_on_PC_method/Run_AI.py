import tkinter as tk
from tkinter import filedialog,messagebox
import tensorflow as tf
from keras.layers import TFSMLayer
import numpy as np
import cv2
import requests
from PIL import Image, ImageTk

ESP_IP = '' #need esp first
stream_url = f"http://{ESP_IP}:81/stream"
classes = [] #just the list of possible colors. must tell the students the order as well.
show_feed=False
frame_height=244
frame_width=244


bars = []
bar_width = 40
spacing = 30
chart_height = 250
baseline = 270
max_height = 200

def setClasses(filepath):
    with open(filepath,"r") as f:
        lines = f.readlines()
        for line in lines:
            classes.append(line[2:])


def createNewUI():
    select_button.grid_forget()
    label.grid_forget()
    prediction_label.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
    display_image.grid(row=0,column=0, padx=10, pady=10,sticky="ne")
    chart_canvas.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky="sw")

    i=0
    for class_text in classes:
        x0 = spacing + i*(bar_width + spacing)
        x1 = x0 + bar_width

        bar = chart_canvas.create_rectangle(x0, baseline, x1, baseline,fill="skyblue")

        chart_canvas.create_text((x0+x1)/2,baseline + 15,text=class_text)

        bars.append(bar)
        i+=1

def updateChart(preds):
    i=0
    for pred in preds:
        height = pred * max_height

        x0, _, x1, _ = chart_canvas.coords(bars[i])

        chart_canvas.coords(bars[i], x0, baseline - height, x1, baseline)
        i+=1


def runModel(model,cap):

    ret, frame = cap.read()
    if not ret:
        messagebox.showwarning("cannot connect to sorting machine!")


    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    resized = cv2.resize(frame_rgb, (frame_height, frame_width))  
    normalized = resized / 255.0
    input_data = np.expand_dims(normalized, axis=0)
    
    prediction = model(input_data)

    for x in prediction:
        prediction = prediction[x].numpy()
   
    class_index = np.argmax(prediction)

    confidence = float(np.max(prediction))

    requests.get(f"http://{ESP_IP}/cmd?prediction={classes[class_index]}")


    prediction_label.config(text=f"Prediction: {classes[class_index]}:({confidence:.2f}%)")
    updateChart(prediction[0])
    
    
 
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    img = Image.fromarray(frame_rgb)
    imgtk = ImageTk.PhotoImage(image=img)

    display_image.imgtk = imgtk
    display_image.configure(image=imgtk)

    root.after(30, lambda: runModel(model, cap))


def selectFile():
   
    folder_path = filedialog.askdirectory(title="Select Folder")
    setClasses(f"{folder_path}/labels.txt")
    folder_path+="/model.savedmodel"


    if folder_path: 
        createNewUI()
        model = TFSMLayer(folder_path, call_endpoint="serving_default")
        cap = cv2.VideoCapture(stream_url)
        runModel(model,cap)
    else:
        messagebox.showwarning("No Selection", "No folder selected!")


root = tk.Tk()
root.title("AI hopper sorter")
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)
root.grid_rowconfigure(0, weight=1)


label = tk.Label(root, text="Select a Teachable Machine saved model", pady=20)
label.grid(row=0,column=0,columnspan=2)

display_image=tk.Label(root,bg="blue")

prediction_label = tk.Label(root,text="",font=("Arial", 16),bg="skyblue",fg="blue")

chart_canvas = tk.Canvas(root, width=300, height=300, bg="white")

select_button = tk.Button(root, text="Select Model", width=20, height=2, command=selectFile)
select_button.grid(row=1,column=0,columnspan=2)

root.mainloop()