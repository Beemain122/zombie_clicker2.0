from kivy.app import App
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.core.window import Window
from kivy.uix.image import Image
from kivy.properties import NumericProperty, ObjectProperty
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
        self.manager.current = "shop"

    def go_settings(self):
        self.manager.transition.direction = "up"
        self.manager.current = "settings"

    def exit_app(self):
        App.get_running_app().stop()


class Settings(Screen):
    def go_menu(self):
        self.manager.transition.direction = "down"
        self.manager.current = "menu"

    def apply_volume(self, text):
        App.get_running_app().set_volume_from_input(text)

    def toggle_music(self):
        App.get_running_app().toggle_music()


class Shop(Screen):
    def buy(self, weapon_id):
        App.get_running_app().buy_weapon(weapon_id)


class RotatedImage(Image):
    angle = NumericProperty(0)


class Fish(RotatedImage):
    hp_current = 0
    anim_play = False
    interaction_block = True

    def new_enemy(self):
        app = App.get_running_app()

        if app.stage < 2:
            enemy = app.ENEMIES[app.stage]
        else:
            enemy = app.ENEMIES[2] if app.round == 1 else app.ENEMIES[3]

        self.source = enemy["source"]
        self.hp_current = enemy["hp"]
        self.opacity = 1
        self.interaction_block = False

    def defeated(self):
        self.interaction_block = True
        Animation(opacity=0, duration=0.4).start(self)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False

        app = App.get_running_app()

        if not app.weapon_selected or self.interaction_block or self.anim_play:
            return False

        self.hp_current -= app.weapon_selected["damage"]

        if app.sounds.get("hit"):
            app.sounds["hit"].play()

        if self.hp_current <= 0:
            self.defeated()
            app.coins += 15

            if app.stage < 2:
                app.stage += 1
                if app.stage == 2:
                    Clock.schedule_once(
                        lambda dt: setattr(app.root, "current", "shop"), 0.8
                    )
                else:
                    Clock.schedule_once(lambda dt: self.new_enemy(), 0.8)
            else:
                if app.round == 1:
                    app.round = 2
                    app.stage = 0
                    Clock.schedule_once(
                        lambda dt: setattr(app.root, "current", "shop"), 0.8
                    )
                else:
                    app.game_finished = True
                    self.source = "assets/images/game_over.png"

        return True


class Game(Screen):
    def on_enter(self):
        app = App.get_running_app()

        if app.game_finished:
            return

        if not app.weapon_selected:
            self.manager.current = "shop"
            return

        self.ids.fish.new_enemy()

    def go_home(self):
        self.manager.transition.direction = "right"
        self.manager.current = "menu"




class ClickerApp(App):
    coins = NumericProperty(0)
    weapon_selected = ObjectProperty(None)

    round = NumericProperty(1)
    stage = NumericProperty(0)
    game_finished = False

    # ===== НАСТРОЙКИ ЗВУКА =====
    master_volume = NumericProperty(0.5)  # 0.0 – 1.0
    music_enabled = True

    WEAPONS = [
        {"name": "Stick", "price": 0,  "damage": 1, "img": "assets/images/weapon_1.png"},
        {"name": "Knife", "price": 40, "damage": 2, "img": "assets/images/weapon_2.png"},
        {"name": "Sword", "price": 70, "damage": 3, "img": "assets/images/weapon_3.png"},
    ]

    ENEMIES = [
        {"source": "assets/images/fish_01.png", "hp": 8},
        {"source": "assets/images/fish_01.png", "hp": 12},
        {"source": "assets/images/fish_02.png", "hp": 30},
        {"source": "assets/images/fish_03.png", "hp": 35},
    ]

    sounds = {}
    music = None

    def build(self):
        self.load_audio()
        sm = ScreenManager()
        sm.add_widget(Menu(name="menu"))
        sm.add_widget(Game(name="game"))
        sm.add_widget(Settings(name="settings"))
        sm.add_widget(Shop(name="shop"))
        return sm

    def buy_weapon(self, weapon_id):
        weapon = self.WEAPONS[weapon_id]
        if self.coins < weapon["price"]:
            return
        self.weapon_selected = weapon
        self.root.current = "game"



    def load_audio(self):
        self.sounds["hit"] = SoundLoader.load(
            rpath("assets", "audios", "bubble01.mp3")
        )
        self.music = SoundLoader.load(
            rpath("assets", "audios", "Black_Swan_part.mp3")
        )

        self.apply_volume()

        if self.music and self.music_enabled:
            self.music.loop = True
            self.music.play()

    def apply_volume(self):
        if self.music:
            self.music.volume = self.master_volume if self.music_enabled else 0

        for s in self.sounds.values():
            if s:
                s.volume = self.master_volume

    def set_volume_from_input(self, text):
        try:
            value = float(text)
            value = max(0, min(100, value))
            self.master_volume = value / 100
            self.apply_volume()
        except ValueError:
            pass

    def toggle_music(self):
        self.music_enabled = not self.music_enabled

        if not self.music_enabled:
            if self.music:
                self.music.stop()
        else:
            if self.music:
                self.music.play()
                self.music.volume = self.master_volume



if __name__ == "__main__":
    if os.name != "posix":
        Window.size = (450, 900)
    ClickerApp().run()
