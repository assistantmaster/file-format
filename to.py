import cv2
import sys

if len(sys.argv) != 2:
    print("Bitte gib eine Datei an.")
    sys.exit()
    
img = cv2.imread(sys.argv[1], cv2.IMREAD_UNCHANGED)

height, width = img.shape[:2]
channels = img.shape[2] if len(img.shape) > 2 else 1

output = []

for y in range(height):
    line = []
    for x in range(width):
        if channels == 4:
            b, g, r, a = img[y, x]
            line.append(f"({int(r)},{int(g)},{int(b)},{int(a)})")
        else:
            b, g, r = img[y, x]
            line.append(f"({int(r)},{int(g)},{int(b)})")
    output.append(";".join(line))
    print(f"{y}/{height}, {y/height*100}%")

with open(f"{sys.argv[1].rsplit(".", 1)[0]}.tho", "w") as thofile:
    thofile.write("\n".join(output))