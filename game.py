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


class GameObject:
    def __init__(self, canvas, item):
        self.canvas = canvas
        self.item = item

    def get_position(self):
        return self.canvas.coords(self.item)

    def move(self, x, y):
        self.canvas.move(self.item, x, y)

    def delete(self):
        self.canvas.delete(self.item)


class Ball(GameObject):
    def __init__(self, canvas, x, y, speed):
        self.radius = 7
        self.speed = speed
        self.dx = 0.0
        self.dy = 0.0
        item = canvas.create_oval(x - self.radius, y - self.radius,
                                  x + self.radius, y + self.radius,
                                  fill='#ffffff', outline='#00e5ff', width=2)
        super().__init__(canvas, item)

    def launch(self):
        angle = math.radians(random.uniform(-35, 35))
        self.set_angle(angle)

    def set_speed(self, speed):
        """Ubah kecepatan tanpa mengubah arah."""
        if self.speed and (self.dx or self.dy):
            k = speed / self.speed
            self.dx *= k
            self.dy *= k
        self.speed = speed

    def set_angle(self, angle):
        """Angle dalam radian, 0 = lurus ke atas."""
        self.dx = self.speed * math.sin(angle)
        self.dy = -self.speed * math.cos(angle)

    def current_angle(self):
        return math.atan2(self.dx, -self.dy)

    def center(self):
        x1, y1, x2, y2 = self.get_position()
        return (x1 + x2) / 2, (y1 + y2) / 2

    def update(self):
        x1, y1, x2, y2 = self.get_position()
        if (x1 <= 0 and self.dx < 0) or (x2 >= WIDTH and self.dx > 0):
            self.dx = -self.dx
        if y1 <= TOP and self.dy < 0:
            self.dy = -self.dy
        self.move(self.dx, self.dy)

    def bounce_paddle(self, paddle):
        # Sudut pantulan tergantung di bagian paddle mana bola mengenai
        px1, _, px2, _ = paddle.get_position()
        cx, _ = self.center()
        half = (px2 - px1) / 2
        rel = max(-1.0, min(1.0, (cx - (px1 + px2) / 2) / half))
        self.set_angle(math.radians(rel * 60))

    def bounce_brick(self, brick):
        # Pantulkan sesuai sisi yang tertabrak (horizontal / vertikal)
        x1, y1, x2, y2 = self.get_position()
        bx1, by1, bx2, by2 = brick.get_position()
        overlap_x = min(x2, bx2) - max(x1, bx1)
        overlap_y = min(y2, by2) - max(y1, by1)
        if overlap_x < overlap_y:
            self.dx = -self.dx
        else:
            self.dy = -self.dy


class Paddle(GameObject):
    def __init__(self, canvas, x, y):
        self.width = PADDLE_WIDTH
        self.height = 12
        self.speed = 9
        item = canvas.create_rectangle(x - self.width / 2, y - self.height / 2,
                                       x + self.width / 2, y + self.height / 2,
                                       fill='#ffd54f', outline='#fff59d', width=2)
        super().__init__(canvas, item)

    def move_by(self, offset):
        x1, _, x2, _ = self.get_position()
        offset = max(-x1, min(WIDTH - x2, offset))
        self.move(offset, 0)

    def move_to(self, x):
        x1, _, x2, _ = self.get_position()
        self.move_by(x - (x1 + x2) / 2)

    def set_width(self, new_width):
        """Ubah lebar paddle dengan titik tengah tetap, tetap di dalam layar."""
        x1, y1, x2, y2 = self.get_position()
        new_x1 = (x1 + x2) / 2 - new_width / 2
        new_x1 = max(0, min(WIDTH - new_width, new_x1))
        self.canvas.coords(self.item, new_x1, y1, new_x1 + new_width, y2)
        self.width = new_width


class Brick(GameObject):
    COLORS = {1: '#ef5350', 2: '#42a5f5', 3: '#ab47bc'}
    OUTLINES = {1: '#ff8a80', 2: '#90caf9', 3: '#ce93d8'}
    POINTS = {1: 5, 2: 10, 3: 15}

    def __init__(self, canvas, x, y, width, height, hits):
        self.hits = hits
        item = canvas.create_rectangle(x, y, x + width, y + height,
                                       fill=Brick.COLORS[hits],
                                       outline=Brick.OUTLINES[hits])
        super().__init__(canvas, item)

    def hit(self):
        """Kurangi nyawa balok. Return True kalau balok hancur."""
        self.hits -= 1
        if self.hits <= 0:
            self.delete()
            return True
        self.canvas.itemconfig(self.item, fill=Brick.COLORS[self.hits],
                               outline=Brick.OUTLINES[self.hits])
        return False


class PowerUp(GameObject):
    """Kapsul yang jatuh. Jenis:
    - 'multi': hijau '+'  -> setiap bola berlipat ganda
    - 'wide' : oranye '<>' -> paddle jadi lebih panjang (sementara)"""
    FALL_SPEED = 3
    STYLE = {'multi': ('#66bb6a', '+'), 'wide': ('#ff9800', '<>')}

    def __init__(self, canvas, x, y, kind):
        self.kind = kind
        color, text = PowerUp.STYLE[kind]
        item = canvas.create_oval(x - 16, y - 10, x + 16, y + 10,
                                  fill=color, outline='#ffffff', width=2)
        self.label = canvas.create_text(x, y, text=text, fill='white',
                                        font=('Arial', 11, 'bold'))
        super().__init__(canvas, item)

    def move(self, x, y):
        super().move(x, y)
        self.canvas.move(self.label, x, y)

    def delete(self):
        super().delete()
        self.canvas.delete(self.label)

    def update(self):
        self.move(0, PowerUp.FALL_SPEED)
