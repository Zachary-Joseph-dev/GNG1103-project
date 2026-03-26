import tkinter as tk
from tkinter import filedialog,messagebox
from tkinter import ttk
import tensorflow as tf
from keras.layers import TFSMLayer
import numpy as np
import cv2
import requests
import threading
import socket
from PIL import Image, ImageTk

ESP_IP = "192.168.4.1"
stream_url = "http://192.168.4.1/stream"
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

cap = None
after_id = None
latest_frame = None

classes = []
stream_started=False
Loading=False
frame_height=244
frame_width=244
display_width=0
display_height=0

progress_bars = {}
confidence_labels = {}

def sendPrediction(prediction):
    prediction=classes[prediction].lower()
    msg=prediction.encode()
    sock.sendto(msg, (ESP_IP, 5000))

def readStream():
    global latest_frame

    while True:
        try:
            bytes_data = b''
            stream = requests.get(stream_url, stream=True)

            for chunk in stream.iter_content(chunk_size=4096):
                bytes_data += chunk

                start = bytes_data.find(b'\xff\xd8')
                end = bytes_data.find(b'\xff\xd9')

                if start != -1 and end != -1 and end > start:
                    jpg = bytes_data[start:end+2]
                    bytes_data = bytes_data[end+2:]

                    frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                    if frame is not None:
                        latest_frame = frame
        except Exception as e:
            print("Stream error, reconnecting...", e)


def setClasses(filepath):
    classes.clear()
    with open(filepath,"r") as f:
        lines = f.readlines()
        for line in lines:
            classes.append(line[2:].strip())

def resizeWithAspectRatio(image, max_width, max_height):
    h, w, _ = image.shape
    scale = min(max_width / w, max_height / h)
    new_w = int(w * scale)
    new_h = int(h * scale)
    return cv2.resize(image, (new_w, new_h))
def createLoadingScreen():
    global Loading
    select_button.destroy()
    label.config(text = "Loading...",font=("Segoe UI", 20, "bold"))
    root.update()
    Loading=True
def createNewUI():
    global display_height,display_width,Loading
    for widget in confidence_frame.winfo_children():
        widget.destroy()

    progress_bars.clear()
    confidence_labels.clear()

    select_button.destroy()
    label.destroy()

    root.config(bg="#dee2e3")
    root.geometry("1054x629")

    left_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
    right_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
    bottom_frame.grid(row=2, column=0,columnspan=2, sticky="nsew", padx=10, pady=10)

    left_frame.update_idletasks()
    display_width = max(300, left_frame.winfo_width())
    display_height = max(300, left_frame.winfo_height())

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
    prediction_label.config(text=f"Prediction: {classes[class_index]} ({preds[class_index]*100:.2f}%)")
    for i, class_string in enumerate(classes):

        pred = preds[i]

        progress_bars[class_string]["value"] = pred * 100
        confidence_labels[class_string].config(text=f"{pred:.2f}")

        if class_string == classes[class_index]:
            confidence_labels[class_string].config(font=("Segoe UI", 10, "bold"))
        else:
            confidence_labels[class_string].config(font=("Segoe UI", 10))


def runModel():
    global latest_frame,after_id,Loading

    if latest_frame is None:
        root.after(50, runModel)
        return

    frame = latest_frame.copy()
    # Convert BGR -> RGB for Tkinter & model 
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) 
    # Resize & normalize for your model 
    resized = cv2.resize(frame_rgb, (frame_height, frame_width)) 
    normalized = resized / 255.0 
    input_data = np.expand_dims(normalized, axis=0) 
    # Run model 
    prediction = model(input_data) 

    prediction = list(prediction.values())[0].numpy()
   
    class_index = np.argmax(prediction)  
    # Send prediction to ESP32 
    #requests.get(f"http://{ESP_IP}/push?prediction=blue") 
    #Update GUI 
    frame_rgb = resizeWithAspectRatio(frame_rgb,display_width,display_height)
    updateChart(prediction[0], class_index) 
    img = Image.fromarray(frame_rgb) 
    imgtk = ImageTk.PhotoImage(image=img) 
    display_image.imgtk = imgtk 
    display_image.configure(image=imgtk)
    after_id = root.after(50, runModel)
    

def selectFile():
    global model, after_id, stream_started
    folder_path = filedialog.askdirectory(title="Select Folder")
    setClasses(f"{folder_path}/labels.txt")
    folder_path+="/model.savedmodel"

    if after_id is not None:
        root.after_cancel(after_id)

    if folder_path:
        if stream_started==False: 
            threading.Thread(target=readStream, daemon=True).start()
            stream_started=True
        createNewUI()
        model = TFSMLayer(folder_path, call_endpoint="serving_default")
        runModel()
    else:
        messagebox.showwarning("No Selection", "No folder selected!")

root = tk.Tk()
root.title("AI hopper sorter")
root.geometry("450x300")
root.configure(bg="#2c3e50")
root.rowconfigure(1, weight=1)
root.columnconfigure(0, weight=3)
root.columnconfigure(1, weight=1)

left_frame = tk.Frame(root, bg="#1e1e1e")

right_frame = tk.Frame(root, bg="#f5f5f5")

bottom_frame=tk.Frame(root,bg="#2c3e50",)


title = tk.Label(root,text="AI Hopper Sorter",font=("Segoe UI", 22, "bold"),bg="#2c3e50",fg="white",pady=10)

label = tk.Label(root, text="Select a Teachable Machine saved model", font=("Segoe UI", 16, "bold"), bg="#2c3e50", fg="white", pady=20, padx=10)
label.pack(pady=(50, 20))

display_image=tk.Label(left_frame,bg="black")

prediction_label = tk.Label(right_frame,text="",font=("Segoe UI", 18, "bold"))

confidence_frame = tk.Frame(right_frame)

select_button = tk.Button( root, text="Select Model", font=("Segoe UI", 14, "bold"), bg="#3498db", fg="white", activebackground="#2980b9", relief="flat", width=20, height=2, command=selectFile)
select_button.pack()

change_model_button = tk.Button(bottom_frame, text="Change Model", bg="#3498db", fg="white", activebackground="#2980b9", relief="flat", width=20, height=2, command=selectFile)


root.mainloop()