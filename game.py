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


class Game(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        # cursor='none' -> kursor mouse disembunyikan di area game
        self.canvas = tk.Canvas(self, bg='#101820', width=WIDTH, height=HEIGHT,
                                highlightthickness=0, cursor='none')
        self.canvas.pack()
        self.pack()
        self.draw_background()

        self.keys = set()
        self.high_score = 0
        self.deaths = 0
        self.message = None
        self.bricks = {}
        self.balls = []
        self.powerups = []
        self.wide_timer = 0
        self.toast_timer = 0
        self.ad_index = 0
        self.ad_timer = 0

        self.paddle = Paddle(self.canvas, WIDTH / 2, HEIGHT - 40)

        self.hud_score = self.canvas.create_text(
            10, 14, anchor='w', fill='white', font=('Arial', 12, 'bold'))
        self.hud_toast = self.canvas.create_text(
            WIDTH / 2, 14, fill='#ffd54f', font=('Arial', 11, 'bold'))
        self.hud_lives = self.canvas.create_text(
            WIDTH - 10, 14, anchor='e', fill='#ff8a80', font=('Arial', 12, 'bold'))

        self.hud_paddle = self.canvas.create_text(
            10, HEIGHT - 10, anchor='w', fill='#ffb74d', font=('Arial', 10, 'bold'))
        self.hud_ad = self.canvas.create_text(
            WIDTH - 10, HEIGHT - 10, anchor='e', fill='#8d99ae', font=('Arial', 9, 'italic'))

        master.bind('<KeyPress>', self.on_key_down)
        master.bind('<KeyRelease>', self.on_key_up)
        self.canvas.bind('<Motion>', lambda e: self.paddle.move_to(e.x))
        self.canvas.focus_set()

        self.new_game()
        self.game_loop()

    # ---------- setup ----------
    def draw_background(self):
        top, bottom = (0x1b, 0x25, 0x4b), (0x08, 0x0c, 0x18)
        strips = 40
        h = HEIGHT / strips
        for i in range(strips):
            t = i / (strips - 1)
            color = '#%02x%02x%02x' % tuple(int(a + (b - a) * t) for a, b in zip(top, bottom))
            self.canvas.create_rectangle(0, i * h, WIDTH, (i + 1) * h + 1,
                                         fill=color, outline='')
        self.canvas.create_rectangle(0, 0, WIDTH, TOP, fill='#0b1020', outline='')
        self.canvas.create_line(0, TOP, WIDTH, TOP, fill='#00e5ff', width=2)

    def new_game(self):
        self.score = 0
        self.lives = LIVES
        self.level = 1
        self.ball_speed = START_SPEED
        self.build_level()
        self.reset_ball()
        self.state = 'ready'
        self.show_message('Press SPACE to start')

    def add_row(self, y):
        cols, margin, gap, height = 14, 16, 3, 14
        width = (WIDTH - 2 * margin - (cols - 1) * gap) / cols
        for c in range(cols):
            # Balok kuat lebih sering muncul
            hits = random.choices([1, 2, 3], weights=[1, 2, 3])[0]
            x = margin + c * (width + gap)
            brick = Brick(self.canvas, x, y, width, height, hits)
            self.bricks[brick.item] = brick

    def build_level(self):
        for brick in self.bricks.values():
            brick.delete()
        self.bricks = {}
        for r in range(5):
            self.add_row(TOP + 22 + r * ROW_STEP)

    def push_bricks_down(self):
        for brick in self.bricks.values():
            brick.move(0, ROW_STEP)
        self.add_row(TOP + 22)
        limit = self.paddle.get_position()[1] - 14
        if any(b.get_position()[3] >= limit for b in self.bricks.values()):
            self.game_over('The bricks reached your paddle!')

    def clear_balls_and_powerups(self):
        for ball in self.balls:
            ball.delete()
        self.balls = []
        for p in self.powerups:
            p.delete()
        self.powerups = []

    def reset_ball(self):
        self.clear_balls_and_powerups()
        self.wide_timer = 0
        self.paddle.set_width(PADDLE_WIDTH)
        self.descend_timer = DESCEND_FRAMES
        self.balls = [Ball(self.canvas, WIDTH / 2, HEIGHT - 60, self.ball_speed)]
        self.stick_ball_to_paddle()

    def stick_ball_to_paddle(self):
        ball = self.balls[0]
        px1, py1, px2, _ = self.paddle.get_position()
        bx1, by1, bx2, by2 = ball.get_position()
        ball.move((px1 + px2) / 2 - (bx1 + bx2) / 2, py1 - 2 - by2)

    # ---------- UI helpers ----------
    def show_message(self, text, color='white'):
        self.clear_message()
        label = self.canvas.create_text(
            WIDTH / 2, HEIGHT / 2 + 40, text=text, fill=color,
            font=('Arial', 16, 'bold'), justify='center')
        x1, y1, x2, y2 = self.canvas.bbox(label)
        panel = self.canvas.create_rectangle(
            x1 - 26, y1 - 12, x2 + 26, y2 + 12,
            fill='#0b1020', outline=color, width=2)
        self.canvas.tag_lower(panel, label)
        self.message = (panel, label)

    def clear_message(self):
        if self.message is not None:
            for item in self.message:
                self.canvas.delete(item)
            self.message = None

    def show_toast(self, text):
        self.canvas.itemconfig(self.hud_toast, text=text)
        self.toast_timer = 150

    def update_hud(self):
        self.canvas.itemconfig(
            self.hud_score,
            text=f'Score: {self.score}   Best: {self.high_score}')
        self.canvas.itemconfig(self.hud_lives, text='♥ ' * self.lives)
        if self.toast_timer > 0:
            self.toast_timer -= 1
            if self.toast_timer == 0:
                self.canvas.itemconfig(self.hud_toast, text='')
        self.ad_timer -= 1
        if self.ad_timer <= 0:
            self.ad_timer = AD_FRAMES
            self.ad_index = (self.ad_index + 1) % len(ADS)
            self.canvas.itemconfig(self.hud_ad, text='AD: ' + ADS[self.ad_index])
        if self.wide_timer > 0:
            secs = math.ceil(self.wide_timer * FRAME_MS / 1000)
            self.canvas.itemconfig(self.hud_paddle, text=f'Long paddle: {secs}s')
        else:
            self.canvas.itemconfig(self.hud_paddle, text='')

    # ---------- input ----------
    def on_key_down(self, event):
        key = event.keysym.lower()
        if self.state == 'restarting':
            return
        self.keys.add(key)
        if key == 'space':
            if self.state == 'ready':
                self.state = 'playing'
                self.clear_message()
                self.balls[0].launch()
        elif key == 'p':
            if self.state == 'playing':
                self.state = 'paused'
                self.show_message('PAUSED - press P to resume')
            elif self.state == 'paused':
                self.state = 'playing'
                self.clear_message()
        elif key == 'b' and self.state == 'over':
            # Uang tidak cukup -> tampilkan pesan, lalu restart dari awal
            self.state = 'restarting'
            self.show_message('Not enough money!\nRestarting...', '#ff8a80')
            self.after(2000, self.full_restart)
        elif key == 'r':
            if self.state == 'over':
                self.show_message('Pay first! Press B', '#ff8a80')
            else:
                self.new_game()

    def full_restart(self):
        """Mulai dari awal: skor, skor terbaik, dan harga tagihan di-reset."""
        self.high_score = 0
        self.deaths = 0
        self.new_game()

    def on_key_up(self, event):
        self.keys.discard(event.keysym.lower())

    # ---------- game logic ----------
    def handle_paddle_keys(self):
        move = 0
        if 'left' in self.keys or 'a' in self.keys:
            move -= self.paddle.speed
        if 'right' in self.keys or 'd' in self.keys:
            move += self.paddle.speed
        if move:
            self.paddle.move_by(move)

    def check_ball_collisions(self, ball):
        overlapping = self.canvas.find_overlapping(*ball.get_position())

        if self.paddle.item in overlapping and ball.dy > 0:
            ball.bounce_paddle(self.paddle)

        for item in overlapping:
            brick = self.bricks.get(item)
            if brick is None:
                continue
            ball.bounce_brick(brick)
            self.score += Brick.POINTS[brick.hits]
            self.speed_up()
            bx1, by1, bx2, by2 = brick.get_position()
            if brick.hit():
                del self.bricks[item]
                if random.random() < DROP_CHANCE:
                    kind = random.choice(['multi', 'wide'])
                    self.powerups.append(
                        PowerUp(self.canvas, (bx1 + bx2) / 2, (by1 + by2) / 2, kind))
            break  # satu balok per bola per frame supaya pantulan tidak dobel

        self.high_score = max(self.high_score, self.score)

    def speed_up(self):
        self.ball_speed = min(MAX_SPEED, self.ball_speed + SPEED_UP)
        for b in self.balls:
            b.set_speed(self.ball_speed)

    def update_powerups(self):
        for p in self.powerups[:]:
            p.update()
            px1, py1, px2, py2 = p.get_position()
            if self.paddle.item in self.canvas.find_overlapping(px1, py1, px2, py2):
                p.delete()
                self.powerups.remove(p)
                if POWERUPS_LOCKED:
                    self.show_toast('Locked! Unlock for $0.99')
                else:
                    if p.kind == 'multi':
                        self.multiply_balls()
                    else:
                        self.widen_paddle()
                    self.score += 50
            elif py1 > HEIGHT:
                p.delete()
                self.powerups.remove(p)

    def widen_paddle(self):
        """Paddle makin panjang (maks PADDLE_MAX) dan timer di-reset."""
        self.paddle.set_width(min(PADDLE_MAX, self.paddle.width + PADDLE_GROW))
        self.wide_timer = WIDE_FRAMES

    def multiply_balls(self):
        """Setiap bola yang ada dipecah jadi 3 (bola asli + 2 bola baru)."""
        new_balls = []
        for ball in self.balls:
            cx, cy = ball.center()
            base = ball.current_angle()
            for offset in (-25, 25):
                if len(self.balls) + len(new_balls) >= MAX_BALLS:
                    break
                nb = Ball(self.canvas, cx, cy, ball.speed)
                nb.set_angle(base + math.radians(offset))
                new_balls.append(nb)
        self.balls.extend(new_balls)

    def game_over(self, reason=''):
        self.lives = 0
        self.clear_balls_and_powerups()
        self.state = 'over'
        extra = reason + '\n' if reason else ''
        self.deaths += 1
        price = 5 * self.deaths - 0.01
        self.show_message(
            f'GAME OVER  (score {self.score})\n{extra}'
            f'Pay ${price:.2f} to play again\n'
            f'or get the Mega Pack for $19.99\n'
            f'Press B to pay',
            '#ff8a80')

    def lose_life(self):
        self.lives -= 1
        if self.lives <= 0:
            self.game_over()
        else:
            self.reset_ball()
            self.state = 'ready'
            self.show_message('Ball lost! Press SPACE')

    def next_level(self):
        self.level += 1
        self.build_level()
        self.reset_ball()
        self.state = 'ready'
        self.show_message(f'Level {self.level}! Press SPACE', '#a5d6a7')

    def game_loop(self):
        self.handle_paddle_keys()

        if self.state == 'ready':
            self.stick_ball_to_paddle()
        elif self.state == 'playing':
            for ball in self.balls[:]:
                ball.update()
                self.check_ball_collisions(ball)
                if ball.get_position()[3] >= HEIGHT:
                    ball.delete()
                    self.balls.remove(ball)

            self.update_powerups()

            self.descend_timer -= 1
            if self.descend_timer <= 0:
                self.descend_timer = DESCEND_FRAMES
                self.push_bricks_down()

            if self.wide_timer > 0:
                self.wide_timer -= 1
                if self.wide_timer == 0:
                    self.paddle.set_width(PADDLE_WIDTH)

            if self.state == 'playing':
                if not self.bricks:
                    self.next_level()
                elif not self.balls:
                    self.lose_life()

        self.update_hud()
        self.after(FRAME_MS, self.game_loop)


if __name__ == '__main__':
    root = tk.Tk()
    root.title('Brick Breaker')
    root.resizable(False, False)
    Game(root)
    root.mainloop()