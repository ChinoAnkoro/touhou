import pyxel
import math
import random
import os
from pathlib import Path

# Pyxelの画面サイズ
SCREEN_WIDTH = 256
SCREEN_HEIGHT = 256

# 元のゲームのキャンバスサイズ
ORIGINAL_CANVAS_WIDTH = 800
ORIGINAL_CANVAS_HEIGHT = 600

# スケールファクター (元のサイズをPyxelの画面サイズに合わせるため)
# 幅と高さで異なるスケールになるが、ここでは統一して0.35を使用
SCALE_FACTOR = 0.35



def scale_x(val):
    return int(val * (SCREEN_WIDTH / ORIGINAL_CANVAS_WIDTH))

def scale_y(val):
    return int(val * (SCREEN_HEIGHT / ORIGINAL_CANVAS_HEIGHT))

def scale_val(val):
    return int(val * SCALE_FACTOR)

class Player:
    def __init__(self):
        self.w = scale_val(50)
        self.h = scale_val(50)
        self.x = SCREEN_WIDTH / 2 - self.w / 2
        self.y = SCREEN_HEIGHT - self.h - scale_val(10) # 画面下部に配置
        self.speed = scale_val(10)
        self.life = 3
        self.max_life = 5
        self.shot_type = 'normal'
        self.bullet_power = 1
        self.bullet_size = scale_val(5)
        self.has_barrier = False
        self.special_attack_stock = 2

        self.is_hammering = False
        self.hammer_cooldown = 10
        self.hammer_timer = 0

        self.invincible_timer = 0 # 無敵時間

        self.shot_cooldown = 5 # ショットのクールダウン (フレーム数)
        self.shot_timer = 0 # ショットタイマー

    def update(self):
        if pyxel.btn(pyxel.KEY_UP):
            self.y -= self.speed
        if pyxel.btn(pyxel.KEY_DOWN):
            self.y += self.speed
        if pyxel.btn(pyxel.KEY_LEFT):
            self.x -= self.speed
        if pyxel.btn(pyxel.KEY_RIGHT):
            self.x += self.speed

        # 画面端での制限
        self.x = max(0, min(self.x, SCREEN_WIDTH - self.w))
        self.y = max(0, min(self.y, SCREEN_HEIGHT - self.h))

        # ハンマー攻撃のクールダウン
        if self.hammer_timer > 0:
            self.hammer_timer -= 1
        else:
            self.is_hammering = False

        # 無敵時間の更新
        if self.invincible_timer > 0:
            self.invincible_timer -= 1

    def draw(self):
        # 無敵時間中は点滅
        if self.invincible_timer > 0 and pyxel.frame_count % 4 < 2:
            return

        # バリアの描画
        if self.has_barrier:
            pyxel.circ(self.x + self.w / 2, self.y + self.h / 2, self.w / 2, 8) # Pyxel color 8 (light blue)

        # プレイヤー本体 (シンプルな人型)
        # 頭
        pyxel.circ(self.x + self.w / 2, self.y + self.h / 4, self.w / 4, 6) # Pink
        # 体
        pyxel.rect(self.x + self.w / 4, self.y + self.h / 2, self.w / 2, self.h / 2, 6) # Pink
        # 腕
        pyxel.rect(self.x, self.y + self.h / 2, self.w / 4, self.h / 4, 6) # Pink
        pyxel.rect(self.x + self.w * 3 / 4, self.y + self.h / 2, self.w / 4, self.h / 4, 6) # Pink

        # ハンマーの描画
        if self.is_hammering:
            hammer_w = scale_val(70)
            hammer_h = scale_val(70)
            pyxel.rect(
                self.x + self.w / 2 - hammer_w / 2,
                self.y - hammer_h / 2,
                hammer_w,
                hammer_h,
                10 # Pyxel color 10 (light yellow)
            )

class Bullet:
    def __init__(self, x, y, dx, power, size, color):
        self.x = x
        self.y = y
        self.w = size
        self.h = size * 2
        self.speed = scale_val(40) # 弾の速度を半分にする
        self.power = power
        self.color = color
        self.dx = dx

    def update(self):
        self.y -= self.speed
        self.x += self.dx * (self.speed / 2)

    def draw(self):
        pyxel.rect(self.x, self.y, self.w, self.h, self.color)

class Enemy:
    def __init__(self, type, x, y, w, h, speed, color, health):
        self.type = type
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.speed = speed
        self.color = color
        self.health = health
        self.dx = (random.random() - 0.5) * scale_val(5) # 横方向の速度を上げる

    def update(self):
        self.y += self.speed
        self.x += self.dx

        # 画面端で跳ね返る
        if self.x < 0 or self.x + self.w > SCREEN_WIDTH:
            self.dx *= -1

    def draw(self):
        # 胴体
        pyxel.rect(self.x, self.y + self.h / 4, self.w, self.h / 2, self.color)
        # 頭
        pyxel.tri(self.x + self.w / 4, self.y, self.x + self.w * 3 / 4, self.y, self.x + self.w / 2, self.y + self.h / 4, self.color)
        # 左翼
        pyxel.tri(self.x - self.w / 4, self.y + self.h / 4, self.x, self.y + self.h / 2, self.x, self.y + self.h / 4, 10)
        # 右翼
        pyxel.tri(self.x + self.w, self.y + self.h / 4, self.x + self.w * 5 / 4, self.y + self.h / 2, self.x + self.w, self.y + self.h / 4, 10)
        # 尻尾
        pyxel.tri(self.x + self.w / 2, self.y + self.h / 2, self.x + self.w * 3 / 4, self.y + self.h, self.x + self.w / 4, self.y + self.h, self.color)

class EnemyBullet:
    def __init__(self, x, y, dx, dy, w, h, speed, color):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.speed = speed
        self.color = color
        self.dx = dx
        self.dy = dy

    def update(self):
        self.x += self.dx
        self.y += self.dy

    def draw(self):
        pyxel.rect(self.x, self.y, self.w, self.h, self.color)

class Item:
    def __init__(self, x, y, w, h, speed, type_index):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.speed = speed
        self.type_index = type_index
        self.item_types = [
            {'name': 'score', 'color': 10}, # yellow
            {'name': 'speed', 'color': 12}, # blue
            {'name': 'power', 'color': 13}, # grey
            {'name': '3way', 'color': 14},  # purple
            {'name': 'barrier', 'color': 6},# pink
            {'name': 'bomb', 'color': 7}    # white (for flashing)
        ]
        self.is_bouncing = False
        self.bounce_speed = scale_val(5)
        self.initial_bounce_y = 0
        self.bounce_height = scale_val(30)

    @property
    def type(self):
        return self.item_types[self.type_index]

    def update(self):
        if self.is_bouncing:
            self.y -= self.bounce_speed
            if self.y <= self.initial_bounce_y - self.bounce_height:
                self.is_bouncing = False
                self.y = self.initial_bounce_y - self.bounce_height # Ensure it stops at the peak
        else:
            self.y += self.speed

    def draw(self):
        if self.type['name'] == 'bomb':
            # 点滅表現
            if pyxel.frame_count % 10 < 5:
                pyxel.rect(self.x, self.y, self.w, self.h, self.type['color'])
        else:
            pyxel.rect(self.x, self.y, self.w, self.h, self.type['color'])

class Explosion:
    def __init__(self, x, y, size, color, duration):
        self.x = x
        self.y = y
        self.size = size
        self.color = color
        self.duration = duration
        self.timer = duration

    def update(self):
        self.timer -= 1

    def draw(self):
        if self.timer > 0:
            pyxel.rect(self.x - self.size / 2, self.y - self.size / 2, self.size, self.size, self.color)

class BombEffect:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 0
        self.max_radius = SCREEN_WIDTH
        self.speed = 8
        self.is_alive = True
        self.color = 7 # White

    def update(self):
        self.radius += self.speed
        if self.radius > self.max_radius:
            self.is_alive = False

    def draw(self):
        # 複数の円を時間差で描画して波紋のようなエフェクトにする
        for i in range(3):
            r = self.radius - i * 20
            if r > 0:
                # 中空の円を描画
                pyxel.circb(self.x, self.y, r, self.color)

class HealItem:
    def __init__(self, x, y, w, h, speed, color):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.speed = speed
        self.color = color

    def update(self):
        self.y += self.speed

    def draw(self):
        pyxel.rect(self.x, self.y, self.w, self.h, self.color)

class Cloud:
    def __init__(self, x, y, w, h, speed, is_background_cloud=False):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.speed = speed
        self.dropped_item = False

    def update(self):
        self.y += self.speed # Move downwards

    def draw(self):
        # Pyxelには楕円描画がないので、rectで代用するか、後で画像を使う
        pyxel.rect(self.x, self.y, self.w, self.h, 7) # White for cloud

class Boss:
    def __init__(self):
        self.w = scale_val(200)
        self.h = scale_val(200)
        self.x = SCREEN_WIDTH / 2 - self.w / 2
        self.y = -self.h # 画面外から出現
        self.speed = scale_val(1)
        self.dx = 1
        self.health = 500
        self.max_health = 500
        self.color = 14 # Purple
        self.attack_pattern = 'descend'
        self.attack_timer = 0

    def update(self):
        if self.attack_pattern == 'descend':
            self.y += self.speed
            if self.y >= scale_val(50):
                self.attack_pattern = 'barrage'
        elif self.attack_pattern == 'barrage':
            self.x += self.dx * self.speed
            if self.x <= 0 or self.x + self.w >= SCREEN_WIDTH:
                self.dx *= -1
            self.attack_timer += 1

    def draw(self):
        pyxel.rect(self.x, self.y, self.w, self.h, self.color)
        # Health bar
        pyxel.rect(self.x, self.y - scale_val(10), self.w, scale_val(5), 8) # Background (blue)
        pyxel.rect(self.x, self.y - scale_val(10), self.w * (self.health / self.max_health), scale_val(5), 11) # Health (green)


class App:
    # Inner class for the hammer hitbox to fix the scope issue
    class HammerHitbox:
        def __init__(self, x, y, w, h):
            self.x = x
            self.y = y
            self.w = w
            self.h = h
            
    def __init__(self):
        pyxel.init(SCREEN_WIDTH, SCREEN_HEIGHT)
        pyxel.title("Pyxel Danmaku Game")

        # ハイスコアファイルのパス
        self.SAVE_DIR = Path(pyxel.user_data_dir("PyxelDanmakuGame", "HighScores"))
        self.HIGH_SCORE_FILE = self.SAVE_DIR / "highscore.txt"

        self.reset_game()
        pyxel.run(self.update, self.draw)

    def load_high_score(self):
        if not self.HIGH_SCORE_FILE.exists():
            return 0
        try:
            with open(self.HIGH_SCORE_FILE, "r") as f:
                return int(f.read())
        except (ValueError, IOError):
            return 0

    def save_high_score(self, score):
        self.SAVE_DIR.mkdir(parents=True, exist_ok=True)
        with open(self.HIGH_SCORE_FILE, "w") as f:
            f.write(str(score))

    def reset_game(self):
        self.player = Player()
        self.bullets = []
        self.enemies = []
        self.enemy_bullets = []
        self.clouds = []
        self.items = []
        self.heal_items = []
        self.boss = None
        self.explosions = [] # 爆発エフェクトのリスト
        self.bomb_effects = [] # ボムエフェクトのリスト

        # サウンド定義
        pyxel.sound(0).set(notes="c1", tones="n", volumes="2", effects="q", speed=5) # Shot
        pyxel.sound(1).set(notes="c1", tones="n", volumes="7", effects="f", speed=15) # Hit/Explosion
        pyxel.sound(2).set(notes="c1", tones="n", volumes="7", effects="f", speed=30) # Player Hit

        # BGMの定義
        # メロディ (ch0)
        pyxel.sound(10).set("c3e3g3c4 g3e3c3r", "t", "7", "n", 10)
        # ベース (ch1)
        pyxel.sound(11).set("c2g1c2g1 c2g1c2g1", "s", "5", "n", 10)
        # アルペジオ (ch2)
        pyxel.sound(12).set("c2e2g2c3e3g3c4e4", "t", "3", "f", 15)
        pyxel.music(0).set([10], [11], [12], [])

        # BGMの定義 (ボスステージ - 派手なBGM)
        # メロディ (ch0)
        pyxel.sound(13).set("c3g3e3c4g3e3c3r", "t", "7", "n", 8) # Faster, higher pitch
        # ベース (ch1)
        pyxel.sound(14).set("c3g2c3g2 c3g2c3g2", "s", "5", "n", 8) # Faster, higher pitch
        # ドラム (ch2)
        pyxel.sound(15).set("rrrrrrc1rrrrrr", "n", "5", "f", 4) # Percussive
        pyxel.music(1).set([13], [14], [15], [])

        # BGMの再生
        pyxel.playm(0, loop=True)

        self.score = 0
        self.high_score = self.load_high_score() # ハイスコアを読み込む
        self.game_phase = 'playing' # playing, gameover, clear
        self.boss_intro_timer = 0 # ボス導入タイマーを初期化

        self.enemy_spawn_timer = 0
        self.cloud_spawn_timer = 0

        # 初期雲を10個生成
        for _ in range(10):
            w = scale_val(120)
            h = scale_val(60)
            x = random.random() * (SCREEN_WIDTH - w)
            y = random.uniform(-h * 2, -h) # 画面上部の異なる高さから出現
            speed = scale_val(7) # 落下速度を速くする
            self.clouds.append(Cloud(x, y, w, h, speed))

    def update(self):
        if self.game_phase == 'gameover' or self.game_phase == 'clear':
            if pyxel.btnp(pyxel.KEY_R): # Rキーでリスタート
                self.reset_game() # ゲームをリセット
            return

        self.player.update() # Player update always runs

        # 雲の更新 (常に実行)
        for cloud in self.clouds:
            cloud.update()
            if not cloud.dropped_item and abs(cloud.x + cloud.w / 2 - SCREEN_WIDTH / 2) < scale_val(20):
                cloud.dropped_item = True
                self.create_item(cloud)
        self.clouds = [c for c in self.clouds if c.y < SCREEN_HEIGHT]

        # Player input handling (shooting, hammer, special attack)
        if self.player.shot_timer > 0:
            self.player.shot_timer -= 1

        if pyxel.btn(pyxel.KEY_SPACE) and self.player.shot_timer <= 0:
            self.create_bullet()
            pyxel.play(0, 0) # ショット音
            self.player.shot_timer = self.player.shot_cooldown

        # ハンマー攻撃 (Zキー)
        if pyxel.btnp(pyxel.KEY_Z):
            if self.player.hammer_timer <= 0:
                self.player.is_hammering = True
                self.player.hammer_timer = self.player.hammer_cooldown

        # 特殊攻撃
        if pyxel.btnp(pyxel.KEY_X) and self.player.special_attack_stock > 0:
            self.player.special_attack_stock -= 1
            self.enemy_bullets.clear() # 敵の弾を消去
            for enemy in self.enemies:
                enemy.health -= 10 # 敵にダメージ
            if self.boss:
                self.boss.health -= 50 # ボスにダメージ
            # ボムエフェクトを生成
            self.bomb_effects.append(BombEffect(self.player.x + self.player.w / 2, self.player.y + self.player.h / 2))

        # ゲームフェーズの移行
        if self.score >= 100000 and self.boss is None: # スコア閾値を100000に調整し、ボスがまだ出現していない場合
            self.game_phase = 'boss_intro' # ボス導入フェーズに移行
            self.enemies.clear() # 残っている敵をクリア
            self.boss_intro_timer = 0
            # ボス登場前の雲を10個生成
            for _ in range(10):
                w = scale_val(120)
                h = scale_val(60)
                x = random.random() * (SCREEN_WIDTH - w)
                y = random.uniform(-h * 2, -h) # 画面上部の異なる高さから出現
                speed = random.uniform(scale_val(2), scale_val(5))
                self.clouds.append(Cloud(x, y, w, h, speed))
            pyxel.playm(-1) # 現在のBGMを停止

        if self.game_phase == 'boss_intro': # ボス導入フェーズ中
            self.boss_intro_timer += 1
            if self.boss_intro_timer >= 420: # 7秒経過 (60フレーム/秒 * 7秒)
                self.game_phase = 'boss'
                self.boss = Boss()
                pyxel.playm(1, loop=True) # ボスBGMを再生

        # 弾の更新
        for bullet in self.bullets:
            bullet.update()
        self.bullets = [b for b in self.bullets if b.y > -b.h and b.y < SCREEN_HEIGHT + b.h and b.x > -b.w and b.x < SCREEN_WIDTH + b.w]

        # アイテムの更新
        for item in self.items:
            item.update()
        self.items = [i for i in self.items if i.y < SCREEN_HEIGHT]

        # 回復アイテムの更新
        for item in self.heal_items:
            item.update()
        self.heal_items = [i for i in self.heal_items if i.y < SCREEN_HEIGHT]

        # 敵の出現 (ランダム)
        if self.boss is None and self.game_phase != 'boss_intro': # ボスが出現していない、かつボス導入フェーズ中でない場合のみ敵を出現させる
            self.enemy_spawn_timer += 1
            if self.enemy_spawn_timer >= 3: # 0.05秒に1回敵を出現させる (10倍)
                self.spawn_enemy()
                self.enemy_spawn_timer = 0

            # 雲の出現
            self.cloud_spawn_timer += 1
            if self.cloud_spawn_timer >= 240: # 4秒に1回 (240フレーム)
                self.spawn_cloud() # アイテムドロップ用の雲
                self.cloud_spawn_timer = 0

            # 敵の更新
            for enemy in self.enemies:
                enemy.update()
                # シューター敵の弾発射
                if enemy.type == 'shooter' and random.random() < 0.01: # 確率を調整
                    self.create_enemy_bullet(enemy, math.pi / 2) # 真下
            self.enemies = [e for e in self.enemies if e.y < SCREEN_HEIGHT]

        elif self.game_phase == 'boss':
            if self.boss:
                self.boss.update()
                # ボスの弾幕パターン
                if self.boss.attack_pattern == 'barrage' and self.boss.attack_timer % 5 == 0: # 頻度をさらに上げる
                    for i in range(16): # 弾の数を増やす
                        angle = (math.pi * 2 / 16) * i + (self.boss.attack_timer / 20) # 弾の角度を調整
                        self.create_enemy_bullet(self.boss, angle)
                if self.boss.health <= 0:
                    self.game_clear()

        # 敵の弾の更新
        for bullet in self.enemy_bullets:
            bullet.update()
        self.enemy_bullets = [b for b in self.enemy_bullets if b.y > -b.h and b.y < SCREEN_HEIGHT + b.h and b.x > -b.w and b.x < SCREEN_WIDTH + b.w]

        # 爆発エフェクトの更新
        for explosion in self.explosions:
            explosion.update()
        self.explosions = [e for e in self.explosions if e.timer > 0]

        # ボムエフェクトの更新
        for effect in self.bomb_effects:
            effect.update()
        self.bomb_effects = [e for e in self.bomb_effects if e.is_alive]

        self.check_collisions()

    def draw(self):
        # Background drawing based on score
        if self.score < 1000:
            # Sea background
            for y in range(SCREEN_HEIGHT):
                if y < SCREEN_HEIGHT * 0.2: # Top 20% (lighter blue)
                    pyxel.rect(0, y, SCREEN_WIDTH, 1, 12) # Light blue
                elif y < SCREEN_HEIGHT * 0.5: # Middle 30% (medium blue)
                    pyxel.rect(0, y, SCREEN_WIDTH, 1, 1) # Dark blue
                else: # Bottom 50% (darker blue) 
                    pyxel.rect(0, y, SCREEN_WIDTH, 1, 1) # Dark blue
        elif self.score < 2000:
            # Sky background with clouds
            pyxel.cls(12) # Light blue for sky
            for cloud in self.clouds:
                cloud.draw()
        else:
            # Space background with Earth
            pyxel.cls(0) # Black for space
            # Draw stars (simple random pixels)
            for _ in range(100):
                star_x = random.randint(0, SCREEN_WIDTH - 1)
                star_y = random.randint(0, SCREEN_HEIGHT - 1)
                pyxel.pset(star_x, star_y, 7) # White stars
            
            # Draw Earth (simple circle with blue and green)
            earth_radius = scale_val(50)
            earth_x = SCREEN_WIDTH / 2
            earth_y = SCREEN_HEIGHT / 4 * 3 # Near bottom
            pyxel.circ(earth_x, earth_y, earth_radius, 1) # Blue ocean
            pyxel.circ(earth_x + earth_radius / 3, earth_y - earth_radius / 3, earth_radius / 2, 3) # Green land
            pyxel.circ(earth_x - earth_radius / 2, earth_y + earth_radius / 4, earth_radius / 4, 3) # Green land

        self.player.draw()

        for bullet in self.bullets:
            bullet.draw()

        for enemy in self.enemies:
            enemy.draw()

        for bullet in self.enemy_bullets:
            bullet.draw()

        for cloud in self.clouds:
            cloud.draw()

        for item in self.items:
            item.draw()

        for item in self.heal_items:
            item.draw()

        if self.boss:
            self.boss.draw()

        # 爆発エフェクトの描画
        for explosion in self.explosions:
            explosion.draw()

        # ボムエフェクトの描画
        for effect in self.bomb_effects:
            effect.draw()

        self.draw_ui()

        if self.game_phase == 'gameover':
            pyxel.rect(0, SCREEN_HEIGHT / 2 - 20, SCREEN_WIDTH, 40, 0) # 黒い帯
            pyxel.text(SCREEN_WIDTH / 2 - len("GAME OVER") * 4 / 2, SCREEN_HEIGHT / 2 - 10, "GAME OVER", 7)
            pyxel.text(SCREEN_WIDTH / 2 - len("PRESS R TO RESTART") * 4 / 2, SCREEN_HEIGHT / 2 + 5, "PRESS R TO RESTART", 7)
        elif self.game_phase == 'clear':
            pyxel.rect(0, SCREEN_HEIGHT / 2 - 20, SCREEN_WIDTH, 40, 0) # 黒い帯
            pyxel.text(SCREEN_WIDTH / 2 - pyxel.width("GAME CLEAR") / 2, SCREEN_HEIGHT / 2 - 10, "GAME CLEAR", 10)
            pyxel.text(SCREEN_WIDTH / 2 - pyxel.width("PRESS R TO RESTART") / 2, SCREEN_HEIGHT / 2 + 5, "PRESS R TO RESTART", 7)

    def create_bullet(self):
        bullet_props = {
            'y': self.player.y,
            'w': self.player.bullet_size,
            'h': self.player.bullet_size * 2,
            'power': self.player.bullet_power,
            'color': 10 # Yellow
        }

        if self.player.shot_type == '3way':
            # 5-way shot
            for i in range(-2, 3):
                angle_offset = i * (math.pi / 12) # 角度を調整
                self.bullets.append(Bullet(self.player.x + self.player.w / 2 - bullet_props['w'] / 2, bullet_props['y'], math.tan(angle_offset), bullet_props['power'], bullet_props['w'], bullet_props['color']))
        else:
            self.bullets.append(Bullet(self.player.x + self.player.w / 2 - bullet_props['w'] / 2, bullet_props['y'], 0, bullet_props['power'], bullet_props['w'], bullet_props['color']))

    def spawn_enemy(self):
        type_roll = random.random()
        if type_roll < 0.6:
            enemy_type = 'shooter'
        elif type_roll < 0.85:
            enemy_type = 'swarmer'
        else:
            enemy_type = 'armored'
        
        size = scale_val(40)
        if enemy_type == 'shooter':
            color = 8 # Red
            health = 2
        elif enemy_type == 'swarmer':
            size = scale_val(20)
            color = 9 # Orange
            health = 1
        else: # armored
            size = scale_val(50)
            color = 13 # Grey
            health = 5
        
        x = random.random() * (SCREEN_WIDTH - size)
        y = -size
        speed = scale_val(2) if enemy_type != 'swarmer' else scale_val(4)
        self.enemies.append(Enemy(enemy_type, x, y, size, size, speed, color, health))

    def create_enemy_bullet(self, source, angle):
        bullet_w = scale_val(10)
        bullet_h = scale_val(20)
        bullet_speed = scale_val(4)
        dx = math.cos(angle) * bullet_speed
        dy = math.sin(angle) * bullet_speed
        self.enemy_bullets.append(EnemyBullet(source.x + source.w / 2 - bullet_w / 2, source.y + source.h / 2, dx, dy, bullet_w, bullet_h, bullet_speed, 6)) # Pink

    def spawn_cloud(self):
        w = random.randint(scale_val(50), scale_val(150))
        h = random.randint(scale_val(20), scale_val(70))
        x = random.random() * (SCREEN_WIDTH - w)
        y = random.uniform(-h * 2, -h) # 画面上部の異なる高さから出現
        speed = scale_val(7) # 落下速度を速くする
        self.clouds.append(Cloud(x, y, w, h, speed))

    def create_item(self, cloud):
        item_w = scale_val(20)
        item_h = scale_val(20)
        item_speed = scale_val(5) # アイテムの落下速度を速くする
        self.items.append(Item(cloud.x + cloud.w / 2 - item_w / 2, cloud.y + cloud.h, item_w, item_h, item_speed, 0)) # Start with score item

    def create_heal_item(self, enemy):
        item_w = scale_val(20)
        item_h = scale_val(20)
        item_speed = scale_val(2)
        self.heal_items.append(HealItem(enemy.x + enemy.w / 2 - item_w / 2, enemy.y + enemy.h / 2 - item_h / 2, item_w, item_h, item_speed, 3)) # Lime green

    def check_collisions(self):
        # Define hammer hitbox once if active, to be used for enemies and boss
        hammer_hitbox = None
        if self.player.is_hammering:
            hammer_w = scale_val(70)
            hammer_h = scale_val(70)
            hammer_hitbox = self.HammerHitbox(
                self.player.x + self.player.w / 2 - hammer_w / 2,
                self.player.y - hammer_h / 2,
                hammer_w,
                hammer_h
            )

        # プレイヤーの弾 vs 敵
        for i in range(len(self.bullets) - 1, -1, -1):
            for j in range(len(self.enemies) - 1, -1, -1):
                bullet = self.bullets[i]
                enemy = self.enemies[j]
                if self.is_colliding(bullet, enemy):
                    if enemy.type == 'armored':
                        self.bullets.pop(i)
                        break # 次の弾へ
                    enemy.health -= bullet.power
                    self.bullets.pop(i)
                    if enemy.health <= 0:
                        self.enemies.pop(j)
                        self.score += 100
                        self.explosions.append(Explosion(enemy.x + enemy.w / 2, enemy.y + enemy.h / 2, scale_val(30), 7, 10)) # 白い爆発
                        pyxel.play(1, 1) # 爆発音
                        if random.random() < 0.1:
                            self.create_heal_item(enemy)
                    break # 弾が当たったら次の弾へ

        # プレイヤーの弾 vs 雲
        for i in range(len(self.bullets) - 1, -1, -1):
            for j in range(len(self.clouds) - 1, -1, -1):
                bullet = self.bullets[i]
                cloud = self.clouds[j]
                if self.is_colliding(bullet, cloud):
                    self.bullets.pop(i)
                    if not cloud.dropped_item: # 既にドロップ済みでなければ
                        cloud.dropped_item = True
                        self.create_item(cloud)
                    break # 弾が当たったら次の弾へ

        # ハンマー vs 敵
        if hammer_hitbox:
            for j in range(len(self.enemies) - 1, -1, -1):
                enemy = self.enemies[j]
                if self.is_colliding(hammer_hitbox, enemy):
                    enemy.health -= scale_val(5) # ハンマーダメージ
                    if enemy.health <= 0:
                        self.enemies.pop(j)
                        self.score += 150
                        self.explosions.append(Explosion(enemy.x + enemy.w / 2, enemy.y + enemy.h / 2, scale_val(40), 7, 15)) # 白い爆発
                        pyxel.play(1, 1) # 爆発音
                        if random.random() < 0.1:
                            self.create_heal_item(enemy)

        # プレイヤーの弾 vs アイテム (アイテムの種類変更)
        for i in range(len(self.bullets) - 1, -1, -1):
            for j in range(len(self.items) - 1, -1, -1):
                bullet = self.bullets[i]
                item = self.items[j]
                if self.is_colliding(bullet, item):
                    self.bullets.pop(i)
                    item.type_index = (item.type_index + 1) % len(item.item_types)
                    item.is_bouncing = True
                    item.initial_bounce_y = item.y
                    break

        # プレイヤー vs アイテム (アイテム取得)
        for i in range(len(self.items) - 1, -1, -1):
            item = self.items[i]
            if self.is_colliding(self.player, item):
                self.apply_item_effect(item.type)
                self.items.pop(i)

        # プレイヤー vs 回復アイテム
        for i in range(len(self.heal_items) - 1, -1, -1):
            item = self.heal_items[i]
            if self.is_colliding(self.player, item):
                self.player.life = min(self.player.life + 1, self.player.max_life)
                self.heal_items.pop(i)

        # プレイヤー vs 敵
        for i in range(len(self.enemies) - 1, -1, -1):
            enemy = self.enemies[i]
            if self.is_colliding(self.player, enemy):
                if self.player.invincible_timer == 0: # 無敵時間中でない場合のみダメージ
                    self.enemies.pop(i)
                    if self.player.has_barrier:
                        self.player.has_barrier = False
                    else:
                        self.player.life -= 1
                        pyxel.play(0, 2) # プレイヤー被弾音
                        self.player.invincible_timer = 60 # 1秒間の無敵時間 (60フレーム)
                        if self.player.life <= 0:
                            self.game_over()
                    return # プレイヤーがダメージを受けたら、他の敵との衝突はチェックしない

        # 敵の弾 vs プレイヤー
        for i in range(len(self.enemy_bullets) - 1, -1, -1):
            bullet = self.enemy_bullets[i]
            if self.is_colliding(bullet, self.player):
                if self.player.invincible_timer == 0: # 無敵時間中でない場合のみダメージ
                    self.enemy_bullets.pop(i)
                    if self.player.has_barrier:
                        self.player.has_barrier = False
                    else:
                        self.player.life -= 1
                        pyxel.play(0, 2) # プレイヤー被弾音
                        self.player.invincible_timer = 60 # 1秒間の無敵時間 (60フレーム)
                        if self.player.life <= 0:
                            self.game_over()
                    return # プレイヤーがダメージを受けたら、他の弾との衝突はチェックしない

        # ボスとの衝突
        if self.boss:
            # プレイヤーの弾 vs ボス
            for i in range(len(self.bullets) - 1, -1, -1):
                bullet = self.bullets[i]
                if self.is_colliding(bullet, self.boss):
                    self.boss.health -= bullet.power
                    self.bullets.pop(i)
                    if self.boss.health <= 0:
                        self.explosions.append(Explosion(self.boss.x + self.boss.w / 2, self.boss.y + self.boss.h / 2, scale_val(100), 7, 30)) # ボス破壊時の大きな爆発
                        pyxel.play(1, 1) # 爆発音
                        self.game_clear()
                    break

            # ハンマー vs ボス
            if hammer_hitbox and self.is_colliding(hammer_hitbox, self.boss):
                self.boss.health -= scale_val(5) # ハンマーダメージ
                if self.boss.health <= 0:
                    self.explosions.append(Explosion(self.boss.x + self.boss.w / 2, self.boss.y + self.boss.h / 2, scale_val(100), 7, 30)) # ボス破壊時の大きな爆発
                    pyxel.play(1, 1) # 爆発音
                    self.game_clear()

    def apply_item_effect(self, item_type):
        if item_type['name'] == 'score':
            self.score += 1000
        elif item_type['name'] == 'speed':
            self.player.speed = min(self.player.speed + scale_val(1), scale_val(10))
        elif item_type['name'] == 'power':
            self.player.shot_type = 'normal'
            self.player.bullet_power = min(self.player.bullet_power + 1, 5)
            self.player.bullet_size = min(self.player.bullet_size + scale_val(5), scale_val(25)) # 弾のサイズをより大きくする
        elif item_type['name'] == '3way':
            self.player.shot_type = '3way'
            self.player.bullet_power = 1
            self.player.bullet_size = scale_val(5)
        elif item_type['name'] == 'barrier':
            self.player.has_barrier = True
        elif item_type['name'] == 'bomb':
            self.player.special_attack_stock = min(self.player.special_attack_stock + 1, 5)

    def is_colliding(self, a, b):
        # Pyxelのrectは(x, y, w, h)なので、それに合わせる
        return a.x < b.x + b.w and a.x + a.w > b.x and a.y < b.y + b.h and a.y + a.h > b.y

    def draw_ui(self):
        # HPバーの背景
        pyxel.rect(5, 5, 100, 5, 1) # Dark blue
        # HPバー本体
        hp_width = (self.player.life / self.player.max_life) * 100
        pyxel.rect(5, 5, hp_width, 5, 11) # Green

        pyxel.text(5, 15, f"SCORE: {self.score}", 7) # White
        pyxel.text(5, 25, f"HIGH SCORE: {self.high_score}", 7)
        pyxel.text(5, 35, f"BOMB: {self.player.special_attack_stock}", 7)

        # Add controls
        pyxel.text(5, SCREEN_HEIGHT - 40, "MOVE: ARROWS", 7)
        pyxel.text(5, SCREEN_HEIGHT - 30, "SHOT: SPACE", 7)
        pyxel.text(5, SCREEN_HEIGHT - 20, "HAMMER: Z", 7)
        pyxel.text(5, SCREEN_HEIGHT - 10, "BOMB: X", 7)

    def game_over(self):
        self.game_phase = 'gameover'
        if self.score > self.high_score:
            self.save_high_score(self.score)

    def game_clear(self):
        self.game_phase = 'clear'
        if self.score > self.high_score:
            self.save_high_score(self.score)

App()
