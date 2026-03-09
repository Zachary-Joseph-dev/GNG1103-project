with open ("data.csv","r") as f:
    lines=f.readlines()
    runtime_sum=0
    fps_sum=0
    i=0
    for line in lines:
        line=line.split(",")
        runtime_sum+=float(line[0])
        fps_sum+=float(line[1])
        i+=1
    avg_runtime=runtime_sum/i
    avg_fps=fps_sum/i
    print(f"{avg_runtime},{avg_fps}")