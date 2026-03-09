import sys
import json
import random

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, Rectangle, Ellipse, Triangle
from kivy.uix.widget import Widget

Window.size = (480, 800)

DATA_FILE = "save_data.json"

def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return {"coins": 0, "high_score": 0, "levels": [1], "upgrades": {}, "ship": 1}

def save_data(d):
    with open(DATA_FILE, 'w') as f:
        json.dump(d, f, indent=2)

COLOR_BG = [0, 0, 0.2, 1]
COLOR_WHITE = [1, 1, 1, 1]
COLOR_RED = [1, 0, 0, 1]
COLOR_GREEN = [0, 1, 0, 1]
COLOR_BLUE = [0, 0, 1, 1]
COLOR_CYAN = [0, 1, 1, 1]
COLOR_ORANGE = [1, 0.5, 0, 1]
COLOR_GOLD = [1, 0.84, 0, 1]

LEVELS = [
    {"waves": 3, "types": ["low"]},
    {"waves": 5, "types": ["low", "medium"]},
    {"waves": 7, "types": ["medium", "high"]},
    {"waves": 10, "types": ["medium", "high"]},
    {"waves": 12, "types": ["high"]},
    {"waves": 15, "types": ["low", "medium", "high"]},
]

class Star:
    def __init__(self):
        self.x = random.uniform(0, 480)
        self.y = random.uniform(0, 800)
        self.s = random.uniform(1, 3)
        self.v = random.uniform(0.5, 2)
    
    def move(self, dt):
        self.y += self.v * dt * 60
        if self.y > 800:
            self.y = 0
            self.x = random.uniform(0, 480)

class Player:
    def __init__(self, upg, lvl):
        self.upg = upg
        self.lvl = lvl
        self.max_hp = 100 + upg.get('hp', 0) * 20
        self.hp = self.max_hp
        self.dmg = 1 + upg.get('dmg', 0) * 0.2 + (lvl - 1) * 0.3
        self.x = 240
        self.y = 150
        self.cool = 0
    
    def update(self, dt, tx):
        if tx:
            self.x = tx
        self.x = max(30, min(450, self.x))
        if self.cool > 0:
            self.cool -= dt * 60
    
    def shoot(self):
        if self.cool <= 0:
            self.cool = max(15, 30 - self.upg.get('fr', 0) * 2)
            b = [{'x': self.x, 'y': self.y - 20, 'dy': -600, 'd': self.dmg, 'c': COLOR_CYAN}]
            if self.lvl >= 2:
                b.append({'x': self.x - 10, 'y': self.y - 10, 'dy': -560, 'd': self.dmg * 0.8, 'c': COLOR_BLUE})
                b.append({'x': self.x + 10, 'y': self.y - 10, 'dy': -560, 'd': self.dmg * 0.8, 'c': COLOR_BLUE})
            return b
        return []

class Enemy:
    def __init__(self, t, lv):
        self.x = random.uniform(50, 430)
        self.y = 850
        self.t = t
        if t == "low":
            self.hp = 20 + lv * 5
            self.spd = 100
            self.c = [0.6, 0.2, 0.2, 1]
            self.coins = 1
        elif t == "medium":
            self.hp = 40 + lv * 10
            self.spd = 75
            self.c = [0.7, 0.3, 0.3, 1]
            self.coins = 2
        else:
            self.hp = 80 + lv * 20
            self.spd = 50
            self.c = [0.9, 0.4, 0.4, 1]
            self.coins = 3
        self.max_hp = self.hp
        self.dir = random.choice([-1, 1])
        self.cd = random.randint(60, 180)
    
    def update(self, dt):
        self.y -= self.spd * dt
        self.x += self.dir * 30 * dt
        if self.x < 50 or self.x > 430:
            self.dir *= -1
        self.cd -= 1
        if self.cd <= 0:
            self.cd = random.randint(60, 180)
            return [{'x': self.x, 'y': self.y + 20, 'dy': 320, 'd': 10, 'c': COLOR_RED}]
        return []

class Coin:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vy = -200
    
    def update(self, dt):
        self.vy += 8 * dt
        self.y += self.vy * dt
        return self.y < 850

class GameScreen(Widget):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.data = load_data()
        self.coins = self.data.get('coins', 0)
        self.upg = self.data.get('upgrades', {})
        self.ship_lvl = self.data.get('ship', 1)
        
        self.state = 'menu'
        self.lvl = 1
        self.score = 0
        self.lvl_coins = 0
        
        self.player = None
        self.enemies = []
        self.pbullets = []
        self.ebullets = []
        self.coins_list = []
        self.stars = [Star() for _ in range(100)]
        
        self.wave = 0
        self.killed = 0
        self.waves = 0
        self.tx = None
        
        self.build_menu()
        Clock.schedule_interval(self.update, 1/60)
    
    def build_menu(self):
        self.clear_widgets()
        self.menu_layout = BoxLayout(orientation='vertical', padding=50, spacing=20)
        
        title = Label(text='Thunder Fighter', font_size=48, color=COLOR_GOLD, size_hint_y=None, height=80)
        self.menu_layout.add_widget(title)
        
        start_btn = Button(text='Start Game', background_color=COLOR_GREEN, size_hint_y=None, height=60)
        start_btn.bind(on_press=self.start_game)
        self.menu_layout.add_widget(start_btn)
        
        level_btn = Button(text='Levels', background_color=COLOR_BLUE, size_hint_y=None, height=60)
        level_btn.bind(on_press=self.show_levels)
        self.menu_layout.add_widget(level_btn)
        
        shop_btn = Button(text='Shop', background_color=COLOR_ORANGE, size_hint_y=None, height=60)
        shop_btn.bind(on_press=self.show_shop)
        self.menu_layout.add_widget(shop_btn)
        
        coin_label = Label(text=f'Coins: {self.coins}  Best: {self.data.get("high_score", 0)}', font_size=20, color=COLOR_WHITE)
        self.menu_layout.add_widget(coin_label)
        
        quit_btn = Button(text='Quit', background_color=[0.6, 0, 0, 1], size_hint_y=None, height=50)
        quit_btn.bind(on_press=self.quit_game)
        self.menu_layout.add_widget(quit_btn)
        
        self.add_widget(self.menu_layout)
    
    def start_game(self, *args):
        self.lvl = 1
        self.reset_game()
        self.state = 'play'
        self.build_game()
    
    def reset_game(self):
        self.player = Player(self.upg, self.ship_lvl)
        self.enemies = []
        self.pbullets = []
        self.ebullets = []
        self.coins_list = []
        self.score = 0
        self.lvl_coins = 0
        self.wave = 0
        self.killed = 0
        self.waves = LEVELS[self.lvl-1]['waves']
    
    def build_game(self):
        self.clear_widgets()
        self.game_layout = BoxLayout(orientation='vertical')
        
        self.hud = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, padding=10)
        self.hud.add_widget(Label(text=f'Score: {self.score}', color=COLOR_WHITE))
        self.hud.add_widget(Label(text=f'HP: {int(self.player.hp)}', color=COLOR_RED))
        self.hud.add_widget(Label(text=f'Coins: {self.lvl_coins}', color=COLOR_GOLD))
        self.hud.add_widget(Label(text=f'Wave: {self.wave}/{self.waves}', color=COLOR_CYAN))
        self.game_layout.add_widget(self.hud)
        
        self.canvas_area = Widget(size_hint_y=1)
        self.canvas_area.bind(on_touch_down=self.on_touch)
        self.canvas_area.bind(on_touch_move=self.on_touch)
        self.canvas_area.bind(on_touch_up=self.on_touch_up)
        self.game_layout.add_widget(self.canvas_area)
        
        self.add_widget(self.game_layout)
    
    def on_touch(self, w, t):
        if self.state == 'play':
            self.tx = t.x
    
    def on_touch_up(self, w, t):
        if self.state == 'play':
            self.tx = None
    
    def show_levels(self, *args):
        self.state = 'level'
        self.clear_widgets()
        layout = BoxLayout(orientation='vertical', padding=50, spacing=15)
        layout.add_widget(Label(text='Select Level', font_size=36, color=COLOR_WHITE, size_hint_y=None, height=60))
        
        for i in range(6):
            lvl_num = i + 1
            unlocked = lvl_num in self.data['levels']
            btn = Button(text=f'Level {lvl_num}', 
                        background_color=COLOR_GREEN if unlocked else [0.3, 0.3, 0.3, 1],
                        size_hint_y=None, height=50)
            if unlocked:
                btn.bind(on_press=lambda _, x=lvl_num: self.select_level(x))
            layout.add_widget(btn)
        
        back_btn = Button(text='Back', background_color=[0.5, 0, 0, 1], size_hint_y=None, height=50)
        back_btn.bind(on_press=self.back_menu)
        layout.add_widget(back_btn)
        
        self.add_widget(layout)
    
    def select_level(self, n):
        self.lvl = n
        self.reset_game()
        self.state = 'play'
        self.build_game()
    
    def show_shop(self, *args):
        self.state = 'shop'
        self.clear_widgets()
        layout = BoxLayout(orientation='vertical', padding=30, spacing=10)
        layout.add_widget(Label(text='Upgrade Shop', font_size=32, color=COLOR_GOLD, size_hint_y=None, height=50))
        layout.add_widget(Label(text=f'Coins: {self.coins}', font_size=24, color=COLOR_WHITE, size_hint_y=None, height=40))
        
        items = [('dmg', 'Damage'), ('hp', 'Health'), ('fr', 'Fire Rate')]
        for k, name in items:
            key = k
            row = BoxLayout(size_hint_y=None, height=50, spacing=10)
            cur = self.upg.get(key, 0)
            cost = 50 + cur * 15
            row.add_widget(Label(text=f'{name} Lv{cur}', color=COLOR_WHITE, size_hint_x=2))
            btn = Button(text=f'{cost}', background_color=COLOR_BLUE if self.coins >= cost else [0.3, 0.3, 0.3, 1], size_hint_x=1)
            btn.bind(on_press=lambda _, key=key: self.buy(key))
            row.add_widget(btn)
            layout.add_widget(row)
        
        ship_row = BoxLayout(size_hint_y=None, height=50, spacing=10)
        ship_cost = self.ship_lvl * 100
        ship_row.add_widget(Label(text=f'Ship Lv{self.ship_lvl}', color=COLOR_WHITE, size_hint_x=2))
        ship_btn = Button(text=f'{ship_cost}', background_color=COLOR_ORANGE if self.coins >= ship_cost else [0.3, 0.3, 0.3, 1], size_hint_x=1)
        ship_btn.bind(on_press=self.buy_ship)
        ship_row.add_widget(ship_btn)
        layout.add_widget(ship_row)
        
        back_btn = Button(text='Back', background_color=[0.5, 0, 0, 1], size_hint_y=None, height=50)
        back_btn.bind(on_press=self.back_menu)
        layout.add_widget(back_btn)
        
        self.add_widget(layout)
    
    def buy(self, key):
        cur = self.upg.get(key, 0)
        cost = 50 + cur * 15
        if self.coins >= cost:
            self.coins -= cost
            self.upg[key] = cur + 1
            self.data['coins'] = self.coins
            self.data['upgrades'] = self.upg
            save_data(self.data)
            self.show_shop()
    
    def buy_ship(self):
        cost = self.ship_lvl * 100
        if self.coins >= cost:
            self.coins -= cost
            self.ship_lvl += 1
            self.data['coins'] = self.coins
            self.data['ship'] = self.ship_lvl
            save_data(self.data)
            self.show_shop()
    
    def back_menu(self, *args):
        self.state = 'menu'
        self.build_menu()
    
    def quit_game(self, *args):
        import sys
        sys.exit()
    
    def spawn_enemy(self):
        if self.wave >= self.waves:
            return
        if random.random() < 0.3:
            return
        t = random.choice(LEVELS[self.lvl-1]['types'])
        self.enemies.append(Enemy(t, self.lvl))
    
    def game_over(self):
        self.state = 'over'
        self.data['coins'] = self.coins + self.lvl_coins
        self.data['high_score'] = max(self.data.get('high_score', 0), self.score)
        save_data(self.data)
        self.clear_widgets()
        layout = BoxLayout(orientation='vertical', padding=50, spacing=30)
        layout.add_widget(Label(text='Game Over', font_size=48, color=COLOR_RED))
        layout.add_widget(Label(text=f'Score: {self.score}', font_size=28, color=COLOR_WHITE))
        
        retry_btn = Button(text='Retry', background_color=COLOR_GREEN, size_hint_y=None, height=60)
        retry_btn.bind(on_press=self.retry)
        layout.add_widget(retry_btn)
        
        menu_btn = Button(text='Menu', background_color=COLOR_BLUE, size_hint_y=None, height=60)
        menu_btn.bind(on_press=self.back_menu)
        layout.add_widget(menu_btn)
        
        self.add_widget(layout)
    
    def retry(self, *args):
        self.reset_game()
        self.state = 'play'
        self.build_game()
    
    def win(self):
        self.state = 'win'
        self.data['coins'] = self.coins + self.lvl_coins
        self.data['high_score'] = max(self.data.get('high_score', 0), self.score)
        if self.lvl < 6 and self.lvl + 1 not in self.data['levels']:
            self.data['levels'].append(self.lvl + 1)
        save_data(self.data)
        self.clear_widgets()
        layout = BoxLayout(orientation='vertical', padding=50, spacing=30)
        layout.add_widget(Label(text='Victory!', font_size=48, color=COLOR_GOLD))
        layout.add_widget(Label(text=f'Score: {self.score}', font_size=28, color=COLOR_WHITE))
        layout.add_widget(Label(text=f'Coins: +{self.lvl_coins}', font_size=28, color=COLOR_GOLD))
        
        retry_btn = Button(text='Retry', background_color=COLOR_GREEN, size_hint_y=None, height=60)
        retry_btn.bind(on_press=self.retry)
        layout.add_widget(retry_btn)
        
        menu_btn = Button(text='Menu', background_color=COLOR_BLUE, size_hint_y=None, height=60)
        menu_btn.bind(on_press=self.back_menu)
        layout.add_widget(menu_btn)
        
        self.add_widget(layout)
    
    def update(self, dt):
        for s in self.stars:
            s.move(dt)
        
        if self.state != 'play' or not self.player:
            return
        
        self.player.update(dt, self.tx)
        bullets = self.player.shoot()
        if bullets:
            self.pbullets.extend(bullets)
        
        for b in self.pbullets[:]:
            b['y'] += b['dy'] * dt
            if b['y'] < -50:
                self.pbullets.remove(b)
        
        for b in self.ebullets[:]:
            b['y'] += b['dy'] * dt
            if b['y'] > 850 or b['y'] < -50:
                self.ebullets.remove(b)
        
        for e in self.enemies[:]:
            self.ebullets.extend(e.update(dt))
            if e.y < -50:
                self.enemies.remove(e)
        
        for c in self.coins_list[:]:
            if c.update(dt):
                if abs(c.x - self.player.x) < 30 and abs(c.y - self.player.y) < 30:
                    self.lvl_coins += 1
                    if c in self.coins_list:
                        self.coins_list.remove(c)
            else:
                if c in self.coins_list:
                    self.coins_list.remove(c)
        
        for b in self.pbullets[:]:
            for e in self.enemies[:]:
                if abs(b['x'] - e.x) < 30 and abs(b['y'] - e.y) < 30:
                    e.hp -= b['d']
                    if b in self.pbullets:
                        self.pbullets.remove(b)
                    if e.hp <= 0:
                        if e in self.enemies:
                            self.enemies.remove(e)
                        self.killed += 1
                        self.score += 10
                        for _ in range(e.coins):
                            self.coins_list.append(Coin(e.x, e.y))
                    break
        
        for b in self.ebullets[:]:
            if abs(b['x'] - self.player.x) < 20 and abs(b['y'] - self.player.y) < 20:
                self.player.hp -= b['d']
                if b in self.ebullets:
                    self.ebullets.remove(b)
                if self.player.hp <= 0:
                    self.game_over()
                    return
        
        for e in self.enemies[:]:
            if abs(e.x - self.player.x) < 25 and abs(e.y - self.player.y) < 25:
                self.player.hp -= 20
                if e in self.enemies:
                    self.enemies.remove(e)
                if self.player.hp <= 0:
                    self.game_over()
                    return
        
        if self.killed >= (self.wave + 1) * 5:
            self.wave += 1
            if self.wave >= self.waves:
                self.win()
                return
        
        if random.random() < 0.05:
            self.spawn_enemy()
        
        self.draw_game()
    
    def draw_game(self):
        if not self.player:
            return
        
        c = self.canvas_area.canvas
        c.clear()
        
        with c:
            Color(*COLOR_BG)
            Rectangle(pos=(0, 0), size=(480, 800))
            
            Color(1, 1, 1, 0.5)
            for s in self.stars:
                Ellipse(pos=(s.x - s.s, s.y - s.s), size=(s.s*2, s.s*2))
            
            Color(0.4, 0.6, 0.8, 1)
            Triangle(self.player.x, self.player.y + 30, self.player.x - 15, self.player.y - 10, self.player.x, self.player.y - 20)
            Triangle(self.player.x, self.player.y + 30, self.player.x + 15, self.player.y - 10, self.player.x, self.player.y - 20)
            
            Color(1, 0.4, 0, 1)
            Triangle(self.player.x - 5, self.player.y + 22, self.player.x, self.player.y + 35, self.player.x + 5, self.player.y + 22)
            
            for b in self.pbullets:
                Color(*b['c'])
                Ellipse(pos=(b['x']-6, b['y']-6), size=(12, 12))
            
            for b in self.ebullets:
                Color(*b['c'])
                Ellipse(pos=(b['x']-8, b['y']-8), size=(16, 16))
            
            for e in self.enemies:
                Color(*e.c)
                Triangle(e.x, e.y + 20, e.x - 15, e.y - 10, e.x, e.y - 20)
                Triangle(e.x, e.y + 20, e.x + 15, e.y - 10, e.x, e.y - 20)
                if e.hp < e.max_hp and e.max_hp > 0:
                    Color(1, 0, 0, 1)
                    Rectangle(pos=(e.x-30, e.y+30), size=(60, 6))
                    Color(0, 1, 0, 1)
                    Rectangle(pos=(e.x-30, e.y+30), size=(60*(e.hp/e.max_hp), 6))
            
            Color(1, 0.84, 0, 1)
            for c in self.coins_list:
                Ellipse(pos=(c.x-12, c.y-12), size=(24, 24))
        
        if self.hud:
            self.hud.clear_widgets()
            self.hud.add_widget(Label(text=f'Score: {self.score}', color=COLOR_WHITE))
            self.hud.add_widget(Label(text=f'HP: {int(self.player.hp)}', color=COLOR_RED))
            self.hud.add_widget(Label(text=f'Coins: {self.lvl_coins}', color=COLOR_GOLD))
            self.hud.add_widget(Label(text=f'Wave: {self.wave}/{self.waves}', color=COLOR_CYAN))

class GameApp(App):
    def build(self):
        return GameScreen()

if __name__ == '__main__':
    GameApp().run()
