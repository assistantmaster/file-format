import pygame
import re
import cv2
import numpy
import struct

pygame.init()
pygame.display.set_caption("Image Converter")
screen = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
font = pygame.font.Font(None, 50)

use_hex = True
use_rle = True
use_bin = True

RLE_PAT = re.compile(r'(\d+):\(([^)]+)\)')
PIX_DEC = re.compile(r'\((\d+,\d+,\d+(?:,\d+)?)\)')
PIX_HEX = re.compile(r'\(([0-9A-Fa-f]+(?:,[0-9A-Fa-f]+){2,3})\)')


def show_progress(y, total):
    screen.fill((255, 255, 255))
    t = font.render(f"{round(y / total * 100, 1)}% ({y}/{total})", True, (0, 0, 0))
    screen.blit(t, (screen.get_width() // 2 - t.get_width() // 2,
                    screen.get_height() // 2 - t.get_height() // 2))
    pygame.display.flip()


def px_str(r, g, b, a, hex_mode):
    if hex_mode:
        return f"{r:02X}{g:02X}{b:02X}{a:02X}" if a is not None else f"{r:02X}{g:02X}{b:02X}"
    return f"({r},{g},{b},{a})" if a is not None else f"({r},{g},{b})"


def write_tho(path, img, hex_mode, rle_mode, bin_mode):
    height, width = img.shape[:2]
    channels = img.shape[2] if len(img.shape) > 2 else 1

    if bin_mode:
        flags = 1 if rle_mode else 0
        with open(path, "wb") as f:
            f.write(b"THO\x02")
            f.write(struct.pack(">IIIB", width, height, channels, flags))
            pixels = img.reshape(-1, channels)
            total = len(pixels)
            if rle_mode:
                buf = bytearray()
                i, last_y = 0, -1
                while i < total:
                    cur = bytes(pixels[i])
                    count = 1
                    while i + count < total and bytes(pixels[i + count]) == cur and count < 255:
                        count += 1
                    buf.append(count)
                    buf.extend(cur)
                    i += count
                    cur_y = i // width
                    if cur_y != last_y:
                        show_progress(cur_y, height)
                        last_y = cur_y
                f.write(bytes(buf))
            else:
                f.write(img.tobytes())
    else:
        with open(path, "w") as f:
            f.write(f"#THO hex={1 if hex_mode else 0} rle={1 if rle_mode else 0}\n")
            for y in range(height):
                row = img[y]
                parts = []
                if rle_mode:
                    x = 0
                    while x < width:
                        count = 1
                        while x + count < width and numpy.array_equal(row[x + count], row[x]) and count < 255:
                            count += 1
                        px = row[x]
                        r, g, b = int(px[2]), int(px[1]), int(px[0])
                        a = int(px[3]) if channels == 4 else None
                        parts.append(f"{count}:{px_str(r, g, b, a, hex_mode)}")
                        x += count
                else:
                    for px in row:
                        r, g, b = int(px[2]), int(px[1]), int(px[0])
                        a = int(px[3]) if channels == 4 else None
                        parts.append(px_str(r, g, b, a, hex_mode))
                f.write(";".join(parts) + "\n")
                show_progress(y, height)


def read_tho(path):
    with open(path, "rb") as f:
        magic = f.read(4)

    if magic == b"THO\x02":
        with open(path, "rb") as f:
            f.read(4)
            width, height, channels, flags = struct.unpack(">IIIB", f.read(13))
            rle_mode = bool(flags & 1)
            data = f.read()
        if rle_mode:
            flat = []
            i = 0
            while i < len(data):
                count = data[i]
                pixel = list(data[i + 1:i + 1 + channels])
                flat.extend([pixel] * count)
                i += 1 + channels
            return numpy.array(flat, dtype=numpy.uint8).reshape((height, width, channels))
        return numpy.frombuffer(data, dtype=numpy.uint8).reshape((height, width, channels))

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

    # Breite & Kanäle bestimmen
    legacy_hex = False
    if rle_mode:
        if hex_mode:
            parts = [p for p in first.split(";") if p.strip()]
            w = sum(int(p.split(":")[0]) for p in parts)
            sample = parts[0].split(":", 1)[1].strip()
            channels = 4 if len(sample) == 8 else 3
        else:
            m = RLE_PAT.findall(first)
            w = sum(int(c) for c, _ in m)
            channels = len(m[0][1].split(",")) if m else 3
    else:
        if hex_mode:
            parts = [p.strip() for p in first.split(";") if p.strip()]
            if parts and parts[0].startswith("("):
                legacy_hex = True
                found = PIX_HEX.findall(first)
                w = len(found)
                channels = len(found[0].split(",")) if found else 3
            else:
                w = len(parts)
                channels = 4 if parts and len(parts[0]) == 8 else 3
        else:
            found = PIX_DEC.findall(first)
            w = len(found)
            channels = len(found[0].split(",")) if found else 3

    img_data = numpy.zeros((h, w, channels), dtype=numpy.uint8)

    for y, line in enumerate(lines):
        line = line.strip()
        if rle_mode:
            if hex_mode and not legacy_hex:
                x = 0
                for part in line.split(";"):
                    if not part.strip():
                        continue
                    cnt_s, hex_s = part.split(":", 1)
                    count, s = int(cnt_s), hex_s.strip()
                    r, g, b = int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
                    pixel = [b, g, r, int(s[6:8], 16)] if channels == 4 else [b, g, r]
                    for _ in range(count):
                        if x < w:
                            img_data[y, x] = pixel
                            x += 1
            else:
                x = 0
                for cnt_s, vals_s in RLE_PAT.findall(line):
                    count = int(cnt_s)
                    vals = [int(v, 16) if legacy_hex else int(v) for v in vals_s.split(",")]
                    r, g, b = vals[0], vals[1], vals[2]
                    pixel = [b, g, r, vals[3]] if channels == 4 else [b, g, r]
                    for _ in range(count):
                        if x < w:
                            img_data[y, x] = pixel
                            x += 1
        else:
            if hex_mode and not legacy_hex:
                for x, s in enumerate(p.strip() for p in line.split(";") if p.strip()):
                    r, g, b = int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
                    img_data[y, x] = [b, g, r, int(s[6:8], 16)] if channels == 4 else [b, g, r]
            elif legacy_hex:
                for x, m in enumerate(PIX_HEX.findall(line)):
                    vals = [int(v, 16) for v in m.split(",")]
                    r, g, b = vals[0], vals[1], vals[2]
                    img_data[y, x] = [b, g, r, vals[3]] if channels == 4 else [b, g, r]
            else:
                for x, m in enumerate(PIX_DEC.findall(line)):
                    vals = [int(v) for v in m.split(",")]
                    r, g, b = vals[0], vals[1], vals[2]
                    img_data[y, x] = [b, g, r, vals[3]] if channels == 4 else [b, g, r]

        show_progress(y, h)

    return img_data


TOGGLE_LABELS = ["Hexadezimal-Kodierung", "RLE-Kodierung", "Binär-Kodierung"]

running = True
while running:
    screen.fill((255, 255, 255))
    text = font.render("Bitte ziehe eine Datei in das Fenster.", True, (0, 0, 0))

    states = [use_hex, use_rle, use_bin]
    for i, (label, state) in enumerate(zip(TOGGLE_LABELS, states)):
        color = (0, 180, 0) if state else (200, 0, 0)
        pygame.draw.rect(screen, color, (20, 20 + i * 70, 30, 30))
        screen.blit(font.render(label, True, (0, 0, 0)), (65, 17 + i * 70))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            mx, my = pygame.mouse.get_pos()
            if mx <= 400:
                if 20 <= my < 70:
                    use_hex = not use_hex
                elif 90 <= my < 140:
                    use_rle = not use_rle
                elif 160 <= my < 210:
                    use_bin = not use_bin

        if event.type == pygame.DROPFILE:
            file = event.file
            if file.endswith(".tho"):
                img_data = read_tho(file)
                cv2.imwrite(f"{file.rsplit('.', 1)[0]}.png", img_data)
            else:
                img = cv2.imread(file, cv2.IMREAD_UNCHANGED)
                write_tho(f"{file.rsplit('.', 1)[0]}.tho", img, use_hex, use_rle, use_bin)

    screen.blit(text, (screen.get_width() // 2 - text.get_width() // 2,
                       screen.get_height() // 2 - text.get_height() // 2))
    pygame.display.flip()

pygame.quit()