import math
import random
import tkinter as tk

WIDTH, HEIGHT = 640, 480
FRAME_MS = 16          # ~60 FPS
TOP = 34               # batas atas area main (di bawah bar HUD)
MAX_BALLS = 15         # batas jumlah bola
DROP_CHANCE = 0.05     # peluang balok hancur menjatuhkan power-up (jarang)
PADDLE_WIDTH = 50      # lebar paddle normal (sempit)
PADDLE_MAX = 110       # lebar maksimal paddle
PADDLE_GROW = 15       # tambahan lebar tiap menangkap power-up
WIDE_FRAMES = 300      # lama paddle panjang (~5 detik)
LIVES = 1              # cuma satu nyawa
START_SPEED = 7        # kecepatan awal bola
MAX_SPEED = 16         # kecepatan maksimal bola
SPEED_UP = 0.08        # bola makin cepat tiap balok kena
DESCEND_FRAMES = 200   # tiap ~4 detik balok turun + baris baru muncul
ROW_STEP = 17          # jarak turun balok per langkah
POWERUPS_LOCKED = True # power-up dikunci (harus 'bayar'); False = berfungsi normal
AD_FRAMES = 240        # ganti iklan di pojok kanan bawah tiap ~4 detik
ADS = ['Ultra Paddle Pack - $4.99',
       'Unlimited Lives - $19.99',
       'Season Pass - $9.99/mo',
       'Double Score Boost - $2.99']

