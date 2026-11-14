#!/usr/bin/env python3
import os
import pygame
import random
import math
from pygame import Rect

# ------------------------------
# Environment Setup
# ------------------------------
os.environ.setdefault("SDL_VIDEODRIVER", "kmsdrm")
os.environ.setdefault("SDL_AUDIODRIVER", "alsa")

pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.mouse.set_visible(False)
WIDTH, HEIGHT = screen.get_size()
clock = pygame.time.Clock()
FPS = 60

# ------------------------------
# Colors
# ------------------------------
BG = (0, 0, 0)
LIGHT_GREEN = (96, 234, 236)
RED = (255, 50, 50)
LINE_THICKNESS = 10

# ------------------------------
# Face Layout
# ------------------------------
face_w, face_h = int(WIDTH * 0.75), int(HEIGHT * 0.75)
face_y = (HEIGHT - face_h) // 3

eye_size = int(min(face_w, face_h) * 0.3)
eye_gap = int(eye_size * 1.7)
eye_y = face_y + int(face_h * 0.25)

left_x = WIDTH // 2 - eye_gap // 2 - eye_size
right_x = WIDTH // 2 + eye_gap // 2
eye_corner = max(8, eye_size // 6)

mouth_w = int(face_w * 0.25)
mouth_h = int(face_h * 0.25)
mouth_x = WIDTH // 2 - mouth_w // 2
mouth_y = eye_y + eye_size + 80

# ------------------------------
# Blink Control
# ------------------------------
is_blinking = False
blink_start = 0
blink_total_ms = 220
next_blink_time = pygame.time.get_ticks() + random.randint(1500, 4500)
talk_phase = 0


def ease_in_out(t):
    return t * t * (3 - 2 * t)


# ------------------------------
# Utility: Rotated Rect
# ------------------------------
def draw_rotated_rect(surface, color, rect, angle, border_radius=0):
    temp = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(temp, color, (0, 0, rect.width,
                     rect.height), border_radius=border_radius)
    rotated = pygame.transform.rotate(temp, angle)
    new_rect = rotated.get_rect(center=rect.center)
    surface.blit(rotated, new_rect)


# ------------------------------
# Eye Drawing
# ------------------------------
def draw_eye(x, y, size, pos, open_amount=1.0, expression="neutral", blink=False):

    eye_rect = Rect(x, y, size, size)

    # ----- Base white eye box (if needed) -----
    if expression in ["neutral", "fear", "anger", "sad", "surprise"]:
        pygame.draw.rect(screen, LIGHT_GREEN, eye_rect,
                         border_radius=eye_corner)

    # ----- Expression modifiers -----
    if expression == "fear":
        rect = pygame.Rect(
            x - size if pos == "left" else x,
            y - size * 0.7,
            size * 2,
            size
        )
        draw_rotated_rect(screen, BG, rect, 14 if pos == "left" else -14)

    elif expression == "happy":
        cx, cy = x + size // 2, y + int(size * 0.5)
        points = [
            (cx - size * 0.7, cy + size * 0.5),
            (cx, cy - size * 0.5),
            (cx + size * 0.7, cy + size * 0.5)
        ]
        pygame.draw.lines(screen, LIGHT_GREEN, False, points, LINE_THICKNESS)

    elif expression == "anger":
        pygame.draw.circle(
            screen, BG,
            (x + size // 2 + (size * 0.3 if pos == "left" else -size * 0.3),
             y - size * 1.5),
            size * 2
        )

    elif expression == "sad":
        pygame.draw.circle(
            screen, BG,
            (x + size // 2 + (size * 0.2 if pos == "left" else -size * 0.2),
             y + size * 1.6),
            size * 1.2
        )

    elif expression == "surprise":
        rect = pygame.Rect(
            x,
            (y - size * 0.5) if pos == "left" else (y - size * 0.3),
            size,
            10
        )
        draw_rotated_rect(screen, LIGHT_GREEN, rect,
                          14 if pos == "left" else -12)

    elif expression == "sleep":
        screen.fill(BG)
        mid = eye_y + eye_size // 2
        pygame.draw.line(screen, LIGHT_GREEN, (left_x, mid),
                         (left_x + eye_size, mid), 4)
        pygame.draw.line(screen, LIGHT_GREEN, (right_x, mid),
                         (right_x + eye_size, mid), 4)
        pygame.draw.line(screen, LIGHT_GREEN, (mouth_x, mouth_y + mouth_h // 2),
                         (mouth_x + mouth_w, mouth_y + mouth_h // 2), 4)
        pygame.display.flip()

    # ----- Blinking lids -----
    if blink and expression != "sleep" and expression != "happy":
        lid_height = int(size * (1.0 - open_amount))
        if lid_height > 0:
            # Top lid
            pygame.draw.rect(screen, BG, (x, y, size, lid_height))
            # Bottom lid
            pygame.draw.rect(screen, BG, (x, y + size -
                             lid_height, size, lid_height))


# ------------------------------
# Mouth Drawing
# ------------------------------
# def draw_mouth(x, y, w, h, expression="neutral"):

#     if expression in ["neutral", "happy"]:
#         pygame.draw.ellipse(screen, LIGHT_GREEN, (x, y, w, h))
#         pygame.draw.rect(screen, BG, (x, y, w, h // 2))

#     elif expression == "sad":
#         pygame.draw.ellipse(screen, LIGHT_GREEN, (x, y, w, h))
#         pygame.draw.rect(screen, BG, (x, y + h // 2, w, h // 2))

#     elif expression == "anger":
#         pygame.draw.rect(screen, LIGHT_GREEN, (x, y + h // 2, w, h // 6))

#     elif expression == "fear":
#         pygame.draw.line(screen, LIGHT_GREEN, (x, y + h // 2),
#                          (x + w, y + h // 3), LINE_THICKNESS)

#     elif expression == "surprise":
#         pygame.draw.ellipse(screen, LIGHT_GREEN, (x, y, w, h))

def draw_mouth(x, y, w, h, expression="neutral", talking=False, movement=0):
    """
    Draw mouth with optional talking animation for all expressions.
    """
    # Compute dynamic height if talking
    move_h = h
    if talking:
        move_h = int(h * (0.3 + 0.7 * movement))  # min 30%, max 100%

    if expression in ["neutral", "happy"]:
        pygame.draw.ellipse(screen, LIGHT_GREEN, (x, y, w, move_h))
        pygame.draw.rect(screen, BG, (x, y, w, h // 2))

    elif expression == "sad":
        pygame.draw.ellipse(screen, LIGHT_GREEN,
                            (x, y-move_h*0.2 if talking else y, w, h*1.1))
        pygame.draw.rect(screen, BG, (x, y + h // 2, w, h))

    elif expression == "anger":
        # Anger is usually a line, but we can make it move slightly
        pygame.draw.rect(screen, LIGHT_GREEN,
                         (x, y + h // 2, w, move_h // 6))  # good

    elif expression == "fear":
        pygame.draw.line(screen, LIGHT_GREEN, (x, y + h // 2),
                         (x + w, y + h // 3), LINE_THICKNESS + (move_h // 3) if talking else LINE_THICKNESS)

    elif expression == "surprise":
        pygame.draw.ellipse(screen, LIGHT_GREEN, (x, y, w, move_h))


# ------------------------------
# Rendering with blinking
# ------------------------------


def render_face(expression="neutral", talking=True, talk_speed=0.1):
    global is_blinking, blink_start, next_blink_time, talk_phase

    now = pygame.time.get_ticks()

    # Trigger blink
    if not is_blinking and now >= next_blink_time:
        is_blinking = True
        blink_start = now
        next_blink_time = now + random.randint(1500, 4500)

    # Lids animation
    open_amount = 1.0
    if is_blinking:
        elapsed = now - blink_start
        if elapsed >= blink_total_ms:
            is_blinking = False
        else:
            half = blink_total_ms / 2
            if elapsed <= half:
                open_amount = 1.0 - ease_in_out(elapsed / half)
            else:
                open_amount = ease_in_out((elapsed - half) / half)

    mouth_movement = 0
    if talking:
        # increment phase
        talk_phase += talk_speed
        # simple oscillation between 0 and 1
        mouth_movement = (math.sin(talk_phase) + 1) / 2

    # Draw face
    screen.fill(BG)
    draw_eye(left_x, eye_y, eye_size, "left", open_amount, expression, True)
    draw_eye(right_x, eye_y, eye_size, "right", open_amount, expression, True)
    draw_mouth(mouth_x, mouth_y, mouth_w, mouth_h,
               expression, talking, mouth_movement)

    pygame.display.flip()
