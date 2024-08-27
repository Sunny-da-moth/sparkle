import os
import sys
import tkinter as tk
from json import load as json_load
from random import randint
from webbrowser import open_new_tab

from PIL import Image, ImageTk
from pygame import mixer
from pynput.keyboard import Controller as KeyboardController
from pynput.mouse import Listener as MouseListener, Button as MouseButton
from pystray import MenuItem as Item, Icon
from requests import request
from win32api import RGB
from win32con import WS_EX_TRANSPARENT, WS_EX_LAYERED, LWA_COLORKEY, GWL_EXSTYLE
from win32gui import SetWindowLong, SetLayeredWindowAttributes


class Game:
    def __init__(self, taskbar_height_):
        self.root = tk.Tk()
        self.sprites: list[Sprite] = []
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        self.root.geometry(f"{self.screen_width}x{self.screen_height - taskbar_height_}")
        self.root.overrideredirect(True)
        self.root.configure(bg=trans)
        self.canvas = tk.Canvas(self.root, bg=trans, width=self.screen_width,
                                height=self.screen_height - taskbar_height_, border=-2, borderwidth=-2)
        self.canvas.pack()
        try:
            hwnd = self.canvas.winfo_id()
            r, g, b = tuple(int(trans[i:i + 2], 16) for i in (1, 3, 5))
            styles = WS_EX_LAYERED | WS_EX_TRANSPARENT
            SetWindowLong(hwnd, GWL_EXSTYLE, styles)
            SetLayeredWindowAttributes(hwnd, RGB(r, g, b), 255, LWA_COLORKEY)
        except Exception as e:
            print(e)
        self.root.attributes("-topmost", True, "-transparentcolor", trans)
        self._update_loop()

    def _update_loop(self):
        for sprite in self.sprites:
            if sprite.enabled:
                sprite.update(sprite)
        self.root.after(15, self._update_loop)


class Sprite:
    """A basic blank sprite without any visual handling"""
    def __init__(self, sunny: Game, xy: tuple[int, int], image: ImageTk.PhotoImage,
                 origin: tuple[float, float] = (0.5, 0.5)):
        self.sunny = sunny
        self.canvas: tk.Canvas = sunny.canvas
        self.image = image
        self.width, self.height = self.image.width(), self.image.height()
        self.id = sunny.canvas.create_image(xy[0], xy[1], image=self.image)
        self.sunny.sprites.append(self)
        self.update = lambda _: None
        self.origin = origin
        self.enabled = True
        self.hidden = False

    def update_image(self, image: ImageTk.PhotoImage | None = None):
        """Update the sprite's image and refresh it on the canvas."""
        self.image = image
        self.width, self.height = self.image.width(), self.image.height()
        self.sunny.canvas.itemconfig(self.id, image=self.image)

    def hide(self):
        if not self.hidden:
            self.canvas.itemconfigure(self.id, state="hidden")
            self.hidden = True

    def show(self):
        if self.hidden:
            self.canvas.itemconfigure(self.id, state="normal")
            self.hidden = False

    def move_to(self, x, y):
        self.canvas.moveto(self.id, -self.width * self.origin[0] + x, -self.height * self.origin[1] + y)

    def move(self, x, y):
        self.canvas.move(self.id, x, y)

    def on_update(self, func):
        self.update = func
        return func

    def init_attr(self, attr, value=None):
        if not hasattr(self, attr):
            setattr(self, attr, value)

    def delete(self):
        """Remove the sprite from the canvas and the Sunny instance's sprite list."""
        self.canvas.delete(self.id)
        if self in self.sunny.sprites:
            self.sunny.sprites.remove(self)

    def enable(self):
        if not self.enabled:
            self.enabled = True

    def disable(self):
        self.enabled = False

    def __del__(self):
        self.delete()


def get_asset_path(filename):
    """Get the path to an asset, whether running as a script or as a bundled executable."""
    if hasattr(sys, '_MEIPASS'):
        return str(os.path.join(sys._MEIPASS, 'assets', filename))
    return str(os.path.join('assets', filename))


def transform(x, y):
    if offset_first:
        x += x_offset
        y += y_offset
        x *= x_scale
        y *= y_scale
        return x, y
    else:
        x *= x_scale
        y *= y_scale
        x += x_offset
        y += y_offset
        return x, y


def play(asset_name):
    assets[asset_name].play()


def make_particle(x, y, amount, life_, v: tuple[int | float, int | float] | None = None):
    global particles_enabled
    if not particles_enabled:
        return
    for _ in range(amount):
        tmp = game.sprites[randint(0, len(game.sprites)-1)]
        if hidden_spawn_only:
            while tmp.enabled:
                tmp = game.sprites[randint(0, len(game.sprites) - 1)]
        tmp.enable()
        tmp.show()
        tmp.rank = randint(1, 3)
        tmp.variant = randint(1, 2)
        tmp.move_to(x, y)
        tmp.life = life_
        if v:
            tmp.__setattr__("vx", v[0])
            tmp.__setattr__("vy", v[1])
        else:
            tmp.__setattr__("vx", randint(-delta_vx, delta_vx))
            tmp.__setattr__("vy", randint(-delta_vy, delta_vy))


def sparkle(x, y):
    play(str(randint(1, 3)))
    sparkle_.counter = 0
    sparkle_.move_to(x, y)
    sparkle_.enable()
    sparkle_.show()
    make_particle(x, y, particle_burst, life)


# load config
try:
    with open('config.json', 'r', encoding='utf-8') as config_file:
        config = json_load(config_file)
except Exception as e:
    print(e)
    config = {
        "life": 10,
        "speed": 5,
        "particle_pool": 25,
        "particle_burst": 2,
        "click_burst": 3,
        "trail_chance": 1,
        "trail_speed": 50,
        "trail_wind": 2,
        "h_drag": 0.8,
        "v_drag": 0.8,
        "delta_vx": 10,
        "delta_vy": 10,
        "delta_br": 1,
        "delta_trail": 5,
        "br_precision": 63,
        "scale": 0.6,
        "x_offset": 0,
        "y_offset": 0,
        "offset_first": False,
        "x_scale": 1.0,
        "y_scale": 1.0,
        "hidden_spawn_only": False,
        "taskbar_height": 1,
        "win32_event_filter_": [
            523,
            524
        ],
        "behaviour": {
            "x1": "keyboard.type(\"✨\");sparkle(x, y)",
            "x2": "keyboard.type(\" (d20:{})\".format(randint(1, 20)));play(\"dice\")"
        }
    }

# config variables
life = config["life"]
speed = config["speed"]
particle_pool = config["particle_pool"]
particle_burst = config["particle_burst"]
click_burst = config["click_burst"]
trail_chance = config["trail_chance"]
trail_speed = config["trail_speed"]
trail_wind = config["trail_wind"]
h_drag = config["h_drag"]
v_drag = config["v_drag"]
delta_vx = config["delta_vx"]
delta_vy = config["delta_vy"]
delta_br = config["delta_br"]
delta_trail = config["delta_trail"]
br_precision = config["br_precision"]
scale = config["scale"]
x_offset = config["x_offset"]
y_offset = config["y_offset"]
offset_first = config["offset_first"]
x_scale = config["x_scale"]
y_scale = config["y_scale"]
hidden_spawn_only = config["hidden_spawn_only"]
taskbar_height = config["taskbar_height"]
win32_event_filter_ = config["win32_event_filter_"]
behaviour = config["behaviour"]
parsed_behaviour = {}
assets = {}

trans = "#000001"
game = Game(taskbar_height)
mixer.init()

# parse parsed_behaviour
for button_, behaviour_ in behaviour.items():
    def func(x, y): pass
    exec(f"def func(x, y): {behaviour_}")
    parsed_behaviour[eval(f"MouseButton.{button_}")] = func

# load assets
path = get_asset_path('')
with os.scandir(path) as entries:
    for entry in entries:
        if entry.is_file() and entry.name.lower().endswith('.png'):
            tmp = Image.open(get_asset_path(entry.name))
            assets[entry.name] = ImageTk.PhotoImage(tmp.resize((int(tmp.width * scale),
                                                               int(tmp.height * scale)),
                                                               Image.Resampling.NEAREST))
        if entry.name.lower().endswith('.wav'):
            assets[entry.name[:-4]] = mixer.Sound(get_asset_path(entry.name))


# load particles into the pool
for _ in range(particle_pool):
    tmp = Sprite(game, (0, 0), assets["9.png"])
    tmp.hide()
    tmp.disable()
    tmp.init_attr("variant", randint(1, 2))
    tmp.init_attr("shimmer", randint(0, 1))
    tmp.init_attr("rank", 0)
    tmp.init_attr("counter", 0)
    tmp.init_attr("life", 10)
    tmp.init_attr("vx", 0)
    tmp.init_attr("vy", 0)

    @tmp.on_update
    def update(self):
        if self.rank:
            if self.counter == speed:
                self.shimmer = 1 - self.shimmer
                self.counter = 0
                if randint(1, self.life) == 1:
                    if self.rank > 0:
                        self.variant = randint(1, 2)
                        self.rank -= 1
                    if self.rank == 0:
                        self.hide()
                        self.disable()
                        return
            self.counter += 1
            self.move(self.vx, self.vy)
            self.vx *= h_drag
            self.vx += randint(-delta_br * br_precision, delta_br * br_precision) / br_precision
            self.vy *= v_drag
            self.vy += randint(-delta_br * br_precision, delta_br * br_precision) / br_precision
            if self.rank != 0:
                self.update_image(assets[f"{self.variant}{self.rank}{self.shimmer + 1}.png"])

sparkle_ = Sprite(game, (100, 100), assets['9.png'])


# slash-like sparkly animation
@sparkle_.on_update
def update2(self):
    global speed
    self.init_attr("counter", speed * 9)
    if self.counter // speed == 9:
        self.hide()
        self.disable()
        return
    self.update_image(assets[str(self.counter // speed + 1)+'.png'])
    self.counter += 1


# prevent default behavior of extra buttons
def win32_event_filter(msg, data):
    listener._suppress = False
    if msg in win32_event_filter_:
        listener._suppress = True


old_x, old_y = 0, 0
vx, vy = 0, 0


# mouse trail :3
def on_move(x, y):
    global old_x, old_y, vx, vy
    vx, vy = x - old_x, y - old_y
    distance = ((vx ** 2) + (vy ** 2)) ** 0.5
    old_x, old_y = x, y
    if randint(1, trail_chance) != 1 or randint(1, 100) > round(min(distance / trail_speed, 1) * 100):
        return
    x, y = transform(x, y)
    make_particle(x, y, 1, life, (vx / trail_wind + randint(-delta_trail, delta_trail),
                                  vy / trail_wind + randint(-delta_trail, delta_trail)))


# custom behavior for extra buttons
def on_click(x, y, button, pressed):
    x, y = transform(x, y)
    if pressed:
        make_particle(x, y, click_burst, life)
        if button in parsed_behaviour.keys():
            parsed_behaviour[button](x, y)


# tray icon
def kill_particles(icon, item):
    for sprite in game.sprites[1:]:
        sprite.hide()
        sprite.disable()


def toggle_particles(icon, item):
    global particles_enabled
    particles_enabled = not particles_enabled


def focus(icon, item):
    global focused
    focused = not focused
    game.root.attributes("-topmost", focused)


def quit_app(icon, item):
    icon.stop()
    listener.stop()
    game.root.quit()


def about(icon, item):
    try:
        request('get', "http://sunnyuwu.rf.gd/")
    except Exception as e:
        print(e)
        open_new_tab("https://sunnyuwu.rf.gd/")


focused = True
particles_enabled = True
icon_image = Image.open(get_asset_path("sparkle.ico"))
tray_icon = Icon("Sparkle App", icon_image, menu=[
    Item('Kill Particles', kill_particles),
    Item('Enable/Disable Particles', toggle_particles),
    Item('Spray it with water', focus),
    Item('Quit', quit_app),
    Item('Made by Sunny', about),
])
tray_icon.run_detached()

keyboard = KeyboardController()
listener = MouseListener(on_click=on_click, on_move=on_move, win32_event_filter=win32_event_filter)
listener.start()

game.root.mainloop()
