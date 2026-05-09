import pygame
import sys
import os
import re
import cv2
import numpy

pygame.init()

pygame.display.set_caption("Image Converter")

screen = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)

font = pygame.font.Font(None, 50)

running = True
while running:
    screen.fill((255, 255, 255))
    text = font.render("Bitte ziehe eine Datei in das Fenster.", True, (0, 0, 0))
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.DROPFILE:
            file = event.file
            if file.endswith(".tho"):
                img = file
                with open(img, "r") as imgfile:
                    lines = imgfile.readlines()

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
                    
                    screen.fill((255, 255, 255))
                    text = font.render(f"{round(y/len(lines)*100, 1)}% ({y}/{len(lines)})", True, (0, 0, 0))
                    screen.blit(text, (screen.get_width() // 2 - text.get_width() // 2, screen.get_height() // 2 - text.get_height() // 2))
                    pygame.display.flip()

                output_path = f"{file.rsplit('.', 1)[0]}.png"
                cv2.imwrite(output_path, img_data)

            else:
                img = cv2.imread(file, cv2.IMREAD_UNCHANGED)

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

                    screen.fill((255, 255, 255))
                    text = font.render(f"{round(y/height*100, 1)}% ({y}/{height})", True, (0, 0, 0))
                    screen.blit(text, (screen.get_width() // 2 - text.get_width() // 2, screen.get_height() // 2 - text.get_height() // 2))
                    pygame.display.flip()

                with open(f"{file.rsplit(".", 1)[0]}.tho", "w") as thofile:
                    thofile.write("\n".join(output))
    
    screen.blit(text, (screen.get_width() // 2 - text.get_width() // 2, screen.get_height() // 2 - text.get_height() // 2))
    pygame.display.flip()
pygame.quit()