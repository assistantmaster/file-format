import pygame
import sys
import re
import struct
import numpy

pygame.init()
pygame.display.set_caption("Image Viewer")

if len(sys.argv) != 2:
    print("Bitte gib eine Datei an.")
    sys.exit()

path = sys.argv[1]

PIX_DEC = re.compile(r'\((\d+,\d+,\d+(?:,\d+)?)\)')
PIX_HEX_OLD = re.compile(r'\(([0-9A-Fa-f]+(?:,[0-9A-Fa-f]+){2,3})\)')
RLE_PAT = re.compile(r'(\d+):\(([^)]+)\)')


def parse_tho(path):
    with open(path, "rb") as f:
        magic = f.read(4)

    # Binärformat
    if magic == b"THO\x02":
        with open(path, "rb") as f:
            f.read(4)
            width, height, channels, flags = struct.unpack(">IIIB", f.read(13))
            rle = bool(flags & 1)
            data = f.read()
        if rle:
            flat = []
            i = 0
            while i < len(data):
                count = data[i]
                flat.extend([list(data[i+1:i+1+channels])] * count)
                i += 1 + channels
            arr = numpy.array(flat, dtype=numpy.uint8).reshape((height, width, channels))
        else:
            arr = numpy.frombuffer(data, dtype=numpy.uint8).reshape((height, width, channels))
        # OpenCV speichert BGR → RGB für pygame
        if channels == 4:
            arr = arr[:, :, [2,1,0,3]]
        else:
            arr = arr[:, :, ::-1]
        return arr

    # Textformat
    with open(path, "r") as f:
        lines = f.readlines()

    hex_mode = False
    rle_mode = False
    if lines[0].startswith("#THO"):
        hex_mode = "hex=1" in lines[0]
        rle_mode = "rle=1" in lines[0]
        lines = lines[1:]

    h = len(lines)
    first = lines[0].strip()

    if rle_mode:
        if hex_mode:
            parts = [p for p in first.split(";") if p.strip()]
            w = sum(int(p.split(":")[0]) for p in parts)
            sample = parts[0].split(":", 1)[1].strip()
            channels = 4 if len(sample) == 8 else 3
            legacy_hex = False
        else:
            m = RLE_PAT.findall(first)
            w = sum(int(c) for c, _ in m)
            channels = len(m[0][1].split(",")) if m else 3
            legacy_hex = False
    else:
        if hex_mode:
            parts = [p.strip() for p in first.split(";") if p.strip()]
            if parts and parts[0].startswith("("):
                legacy_hex = True
                found = PIX_HEX_OLD.findall(first)
                w = len(found)
                channels = len(found[0].split(",")) if found else 3
            else:
                legacy_hex = False
                w = len(parts)
                channels = 4 if parts and len(parts[0]) == 8 else 3
        else:
            legacy_hex = False
            found = PIX_DEC.findall(first)
            w = len(found)
            channels = len(found[0].split(",")) if found else 3

    arr = numpy.zeros((h, w, channels), dtype=numpy.uint8)

    for y, line in enumerate(lines):
        line = line.strip()
        if rle_mode:
            if hex_mode and not legacy_hex:
                x = 0
                for part in line.split(";"):
                    if not part.strip(): continue
                    cnt_s, hex_s = part.split(":", 1)
                    count, s = int(cnt_s), hex_s.strip()
                    r, g, b = int(s[0:2],16), int(s[2:4],16), int(s[4:6],16)
                    pixel = [r,g,b, int(s[6:8],16)] if channels==4 else [r,g,b]
                    for _ in range(count):
                        if x < w: arr[y, x] = pixel; x += 1
            else:
                x = 0
                for cnt_s, vals_s in RLE_PAT.findall(line):
                    count = int(cnt_s)
                    vals = [int(v,16) if legacy_hex else int(v) for v in vals_s.split(",")]
                    pixel = vals[:4] if channels==4 else vals[:3]
                    for _ in range(count):
                        if x < w: arr[y, x] = pixel; x += 1
        else:
            if hex_mode and not legacy_hex:
                for x, s in enumerate(p.strip() for p in line.split(";") if p.strip()):
                    r, g, b = int(s[0:2],16), int(s[2:4],16), int(s[4:6],16)
                    arr[y, x] = [r,g,b, int(s[6:8],16)] if channels==4 else [r,g,b]
            elif legacy_hex:
                for x, m in enumerate(PIX_HEX_OLD.findall(line)):
                    vals = [int(v,16) for v in m.split(",")]
                    arr[y, x] = vals[:4] if channels==4 else vals[:3]
            else:
                for x, m in enumerate(PIX_DEC.findall(line)):
                    vals = [int(v) for v in m.split(",")]
                    arr[y, x] = vals[:4] if channels==4 else vals[:3]

    return arr


arr = parse_tho(path)
h, w = arr.shape[:2]
channels = arr.shape[2] if len(arr.shape) > 2 else 1

screen = pygame.display.set_mode((w, h))
flag = pygame.SRCALPHA if channels == 4 else 0
surface = pygame.Surface((w, h), flag)
pygame.surfarray.blit_array(surface, arr.swapaxes(0, 1)[:, :, :3] if channels == 3 else arr.swapaxes(0, 1))

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    screen.fill((30, 30, 30))
    screen.blit(surface, (0, 0))
    pygame.display.flip()

pygame.quit()