import pygame
import sys
import os
import re

pygame.init()

pygame.display.set_caption("Image Viewer")

if len(sys.argv) != 2:
    print("Bitte gib eine Datei an.")
    sys.exit()

with open(sys.argv[1], "r") as file:
    lines = file.readlines()

h = len(lines)
w = len(re.findall(r'\(.*?\)', lines[0]))
screen = pygame.display.set_mode((w, h))

surface = pygame.Surface((w, h), pygame.SRCALPHA)

for lineindex, line in enumerate(lines):
    matches = re.findall(r'\((\d+,\d+,\d+(?:,\d+)?)\)', line)
    line_list = [list(map(int, m.split(','))) for m in matches]

    for pixelindex, pixel in enumerate(line_list):
        x = pixelindex
        y = lineindex
        r = pixel[0]
        g = pixel[1]
        b = pixel[2]
        surface.set_at((x, y), (r, g, b))

running = True
while running:
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((30, 30, 30))
    screen.blit(surface, (0, 0))
    pygame.display.flip()

pygame.quit()