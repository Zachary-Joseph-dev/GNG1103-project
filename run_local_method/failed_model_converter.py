import tkinter as tk
from tkinter import filedialog,messagebox
import tensorflow as tf
import numpy as np
import cv2
import glob
import sys

#load calibration data
def representative_data_gen():
    #creates a list of images
    image_paths = glob.glob("calibration_data/*.jpg")
    #loops through list
    for path in image_paths:
        #loads list into memory
        img = cv2.imread(path)
        #resizes image
        img = cv2.resize(img, (224, 224))
        #converts rgb values into values between 0 and 1 (neural networks work with probabilities so it is just easier this way)
        img = img.astype(np.float32) / 255.0
        #before img=(r,g,b) now img=(1,r,g,b) the 1 tell TensorFlow how many images it is working with 
        img = np.expand_dims(img, axis=0)
        yield [img]


#compresses data 
def convert_model(model_path):
    try:

        #loads full model into RAM
        model = tf.keras.models.load_model(model_path)

        #converts the data into TFlite format
        converter = tf.lite.TFLiteConverter.from_keras_model(model)
        #built-in optimazations so that accuracy doesn't go down that much
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        #tests the model against calibration data to fine tune variables
        converter.representative_dataset = representative_data_gen
        #converts all weight and bias to integers to save processing power
        converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
        converter.inference_input_type = tf.int8
        converter.inference_output_type = tf.int8

        #final conversion step
        tflite_model = converter.convert()

        #create a new file name 
        OUTPUT_PATH = model_path.replace(".h5", "_quant.tflite")

        #write to the file path so the model is now saved used wb so that it writes in binary
        with open(OUTPUT_PATH, "wb") as f:
            f.write(tflite_model)

        messagebox.showinfo("Success", f"Model converted!\nSaved as:\n{output_path}")
    
    except Exception as e:
        messagebox.showerror("Error", str(e))


def select_file():
    #simple file selection
    file_path = tk.filedialog.askopenfilename(
        title = "select Keras Model",
        filetypes=[('Keras model',"*.h5")]
    )
    if file_path:
        convert_model(file_path)

#simple UI
root = tk.Tk()
root.title("Teachable Machine → ESP32 Converter")
root.geometry("400x200")

label = tk.Label(root, text="Select a Teachable Machine .h5 model", pady=20)
label.pack()

button = tk.Button(root, text="Select Model", command=select_file, width=20, height=2)
button.pack()

root.mainloop()