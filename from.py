import cv2
import sys
import re
import numpy

if len(sys.argv) != 2:
    print("Bitte gib eine Datei an.")
    sys.exit()

img = sys.argv[1]

with open(img, "r") as file:
    lines = file.readlines()

h = len(lines)
first_line_matches = re.findall(r'\((\d+,\d+,\d+(?:,\d+)?)\)', lines[0])
w = len(first_line_matches)

sample_pixel = first_line_matches[0].split(',')
channels = len(sample_pixel)

img_data = numpy.zeros((h, w, channels), dtype=numpy.uint8)

for y, line in enumerate(lines):
    matches = re.findall(r'\((\d+,\d+,\d+(?:,\d+)?)\)', line)
    for x, match in enumerate(matches):
        pixel = list(map(int, match.split(',')))
        r, g, b = pixel[0], pixel[1], pixel[2]
        
        if channels == 4:
            a = pixel[3]
            img_data[y, x] = [b, g, r, a]
        else:
            img_data[y, x] = [b, g, r]
        
    print(f"{y}/{len(lines)}, {y/len(lines)*100}%")

output_path = f"{img.rsplit('.', 1)[0]}.png"
cv2.imwrite(output_path, img_data)