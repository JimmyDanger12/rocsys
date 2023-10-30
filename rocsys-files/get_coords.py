import subprocess
import math
import csv

AMOUNT_TIMES = 1

DOCKER_COMMAND = "docker exec -it vision-vision-1 bash -c 'rocsys-vision-client DETECT_SOCKET_FAST'"

RES_NO_SUCCESS = 0
RES_SUCCESS = 1
RES_UNRELIABLE = 2

def convert_coords(coords):
    converted_coords = list()
    converted_coords[0:2] = [x*1000 for x in coords[0:3]]
    converted_coords[3:5] = [math.degrees(rad) for rad in coords[3:6]]
    return converted_coords

def extract_coords(text=str):
    coords_str = text.split('Pose: ')[1].split('\n')[0]
    coords = eval(coords_str)
    coords = convert_coords(coords)
    return coords
    
def take_image(amount):
    results = list()
    coords_list = list()
    for i in range(amount):
        try:
            docker_output = subprocess.check_output(DOCKER_COMMAND, shell=True, text=True, stderr=subprocess.STDOUT).strip()
        except subprocess.CalledProcessError as e:
            docker_output = e.output

        if "not running" in docker_output:
            print(docker_output)
        else:
            print("image taken")
        result = None
        
        if "success" in docker_output:        
            result = RES_SUCCESS
            coords = extract_coords(docker_output)
            coords_list.append(coords)
        elif "No socket detected" in docker_output or "unreliable" in docker_output:
            result = RES_NO_SUCCESS if "No socket detected" in docker_output else RES_UNRELIABLE
            coords = []
        
        results.append(result)
    return results, coords_list

file_path = "coord.csv"
results, coord_list = take_image(AMOUNT_TIMES)


print(coord_list)

if coord_list:
    av = []
    for i in range(6):
        i_total = 0
        for coord in coord_list:
            i_total += coord[i]
        av.append(i_total/len(coord_list))
        
    with open(file_path, mode="a", newline="") as file:
        writer = csv.writer(file)
            
        writer.writerow(av)
    
print(f"Taken {AMOUNT_TIMES} images: results: {results}")
if sum(results) == 0:
    print(f"No successful picture taken!")
    