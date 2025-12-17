from kivy.app import App
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.core.window import Window
from kivy.uix.image import Image
from kivy.properties import NumericProperty
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def rpath(*parts):
    return os.path.join(BASE_DIR, *parts)


class Menu(Screen):
    def go_game(self):
        self.manager.transition.direction = "left"
        self.manager.current = "game"

    def go_settings(self):
        self.manager.transition.direction = "up"
        self.manager.current = "settings"

    def exit_app(self):
        App.get_running_app().stop()

class Settings(Screen):
    volume_level = 0.5

    def go_menu(self):
        self.manager.transition.direction = "down"
        self.manager.current = "menu"

    def toggle_music(self, state):
        app = App.get_running_app()
        if app.music:
            if state == 'down':
                app.music.stop()
            else:
                app.music.play()

    def set_volume(self, value):
        self.volume_level = value
        app = App.get_running_app()
        # Музыка
        if app.music:
            app.music.volume = value
        # Все звуки
        for snd in app.sounds.values():
            if snd:

                if snd == app.sounds.get("kill"):
                    snd.volume = min(value * 2.0, 1.0)
                else:
                    snd.volume = value

class RotatedImage(Image):
    angle = NumericProperty(0)
    ...

class Fish(RotatedImage):
    COEF_MULT = 1.5
    angle = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.anim_play = False
        self.interaction_block = True
        self.fish_current = None
        self.fish_index = 0
        self.hp_current = None
        self.GAME_SCREEN = None

    def on_kv_post(self, base_widget):
        self.GAME_SCREEN = self.parent.parent.parent
        return super().on_kv_post(base_widget)

    def new_fish(self, *args):
        app = App.get_running_app()
        self.fish_current = app.LEVELS[app.LEVEL][self.fish_index]
        self.source = app.FISHES[self.fish_current]["source"]
        self.hp_current = app.FISHES[self.fish_current]["hp"]
        self.swim()

    def swim(self):
        self.pos = (self.GAME_SCREEN.x - self.width, self.GAME_SCREEN.height / 2 - 100)
        self.opacity = 1
        swim = Animation(x=self.GAME_SCREEN.width / 2 - self.width / 2, duration=1)
        swim.start(self)
        swim.bind(on_complete=lambda *_: setattr(self, "interaction_block", False))

    def defeated(self):
        self.interaction_block = True
        app = App.get_running_app()
        s = app.sounds.get("kill")
        if s: s.play()

        anim = Animation(angle=self.angle + 360, d=1, t="in_cubic")
        old_size = self.size.copy()
        old_pos = self.pos.copy()
        new_size = (self.size[0]*self.COEF_MULT*3, self.size[1]*self.COEF_MULT*3)
        new_pos = (self.pos[0]-(new_size[0]-self.size[0])/2, self.pos[1]-(new_size[1]-self.size[1])/2)
        anim &= Animation(size=new_size, t="in_out_bounce") + Animation(size=old_size, duration=0)
        anim &= Animation(pos=new_pos, t="in_out_bounce") + Animation(pos=old_pos, duration=0)
        anim &= Animation(opacity=0)
        anim.start(self)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos) or self.anim_play or self.interaction_block:
            return False

        self.hp_current -= 1
        self.GAME_SCREEN.score += 1

        app = App.get_running_app()
        s = app.sounds.get("hit")
        if s: s.play()

        if self.hp_current > 0:
            old_size = self.size.copy()
            old_pos = self.pos.copy()
            new_size = (self.size[0]*self.COEF_MULT, self.size[1]*self.COEF_MULT)
            new_pos = (self.pos[0]-(new_size[0]-self.size[0])/2, self.pos[1]-(new_size[1]-self.size[1])/2)
            zoom_anim = Animation(size=new_size, duration=0.05) + Animation(size=old_size, duration=0.05)
            zoom_anim &= Animation(pos=new_pos, duration=0.05) + Animation(pos=old_pos, duration=0.05)
            self.anim_play = True
            zoom_anim.bind(on_complete=lambda *_: setattr(self, "anim_play", False))
            zoom_anim.start(self)
        else:
            self.defeated()
            app = App.get_running_app()
            if len(app.LEVELS[app.LEVEL]) > self.fish_index + 1:
                self.fish_index += 1
                Clock.schedule_once(self.new_fish, 1.2)
            else:
                Clock.schedule_once(self.GAME_SCREEN.level_complete, 1.2)
        return True

class Game(Screen):
    score = NumericProperty(0)

    def on_pre_enter(self, *args):
        self.score = 0
        app = App.get_running_app()
        app.LEVEL = 0
        self.ids.level_complete.opacity = 0
        self.ids.fish.fish_index = 0
        return super().on_pre_enter(*args)

    def on_enter(self, *args):
        self.start_game()
        return super().on_enter(*args)

    def start_game(self):
        self.ids.fish.new_fish()

    def level_complete(self, *args):
        self.ids.level_complete.opacity = 1
        app = App.get_running_app()
        s = app.sounds.get("lvl_completed")
        if s: s.play()

    def go_home(self):
        self.manager.transition.direction = "right"
        self.manager.current = "menu"



class ClickerApp(App):
    LEVEL = 0
    volume_level = 0.5  # <-- ставим начальное значение

    FISHES = {
        "fish1": {"source": "assets/images/fish_01.png", "hp": 10},
        "fish2": {"source": "assets/images/fish_02.png", "hp": 20},
    }

    LEVELS = [["fish1","fish1","fish2"]]

    sounds = {}
    music = None

    def build(self):
        self.load_audio()
        sm = ScreenManager()
        sm.add_widget(Menu(name="menu"))
        sm.add_widget(Game(name="game"))
        sm.add_widget(Settings(name="settings"))
        return sm

    def _load_one(self, key, filepath):
        snd = SoundLoader.load(filepath)
        if not snd:
            print(f"❌ Audio not loaded: {key} -> {filepath}")
        else:
            print(f"✅ Audio loaded: {key} -> {filepath}")
        return snd

    def load_audio(self):
        self.sounds["hit"] = self._load_one("hit", rpath("assets","audios","bubble01.mp3"))
        self.sounds["kill"] = self._load_one("kill", rpath("assets","audios","fish_def.mp3"))
        self.sounds["lvl_completed"] = self._load_one("lvl_completed", rpath("assets","audios","level_complete.mp3"))
        self.music = self._load_one("music", rpath("assets","audios","Black_Swan_part.mp3"))


        if self.sounds["kill"]:
            self.sounds["kill"].volume = min(self.volume_level * 1.5, 1.0)
        if self.music:
            self.music.loop = True
            self.music.volume = 0.5
            self.music.play()


if __name__ == "__main__":
    if os.name != "posix":
        Window.size = (450,900)
    ClickerApp().run()
