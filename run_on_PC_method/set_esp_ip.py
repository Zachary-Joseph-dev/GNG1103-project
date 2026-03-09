text=[]
with open("Run_AI.py","r") as f:
    text=f.readlines()

IP_index=text.find("ESP_IP = ")
