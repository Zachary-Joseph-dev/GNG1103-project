# AI Ball Sorting System (STEM Workshop Project)

## Overview
This project was developed as part of a university assignment to create an interactive AI workshop for high school students. The goal was to demonstrate real-world applications of machine learning and computer vision through a hands-on system that sorts balls based on color.

The system uses a trained AI model running on a laptop to classify objects, and communicates predictions to an embedded device (ESP32-CAM) over Wi-Fi.

## Features
- Real-time image capture using ESP32-CAM  
- Color classification using a TensorFlow-based model  
- Computer vision pipeline built with OpenCV  
- GUI interface using Tkinter  
- Multithreaded architecture for improved performance  
- Wireless communication between devices  

## System Architecture
- **ESP32-CAM (C)**  
  Captures images and sends them to a local server over Wi-Fi  

- **Python Application (Laptop)**  
  - Receives image data  
  - Processes images using OpenCV  
  - Runs inference using TensorFlow  
  - Sends classification results back to ESP32  

## Technologies Used
- Python  
- TensorFlow  
- OpenCV  
- Tkinter  
- C (ESP32)  
- Multithreading  
- Wi-Fi communication  

## My Contributions
- Solely responsible for all software development for the project  
- Designed and implemented the Python-based AI system  
- Built the computer vision and inference pipeline using TensorFlow and OpenCV  
- Developed multithreaded architecture for real-time performance  
- Programmed ESP32 communication for image transfer over Wi-Fi  
- Contributed to workshop design and delivery for students  

## Educational Purpose
This project was specifically designed to:
- Introduce students to AI and computer vision  
- Demonstrate real-time machine learning applications  
- Provide an interactive and engaging STEM learning experience  

## Future Improvements
- Support for more object categories  
- Improved model accuracy  
- Faster image transmission  
- Hardware-based actuation for physical sorting  

## Notes
This project was built for educational purposes and prioritizes clarity and demonstration over production-level optimization.
