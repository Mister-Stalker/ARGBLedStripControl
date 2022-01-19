import json
import socket
import time
from kivymd.app import MDApp
from kivy.properties import ObjectProperty
from kivy.lang import Builder
from kivy.uix.button import Button
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.screen import MDScreen
from kivy.config import Config
from kivy.utils import platform
import threading
from esp_connection import EspConnection

Config.set('kivy', 'window_icon', 'icon.png')
Config.set("graphics", "height", '1000')
Config.set("graphics", "width", '500')


class ArgbLedControl(MDApp):

    def build(self):
        self.theme_cls.material_style = "M3"
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "DeepOrange"
        self.icon = 'icon.png'
        # self.screen_manager = self.root.ids.screen_manager
        # return Builder.load_file("app_interface.kv")
        self.root = Builder.load_file("app_interface.kv")
        self.root.ids.debug_label.text = "DEBUG"

        self.root.ids.screen_manager.current = "scr 2"
        self.root.ids.slider_add_on_tick_1.value = 2


class MDScreenMain(MDScreen, EspConnection):
    def __init__(self, *args, **kwargs):
        super(MDScreenMain, self).__init__(*args, **kwargs)
        super(EspConnection, self).__init__()
        self.brightness = 10
        self.esp = {
            "led_configs_mask": {
                "start mode": [1, 2, 11, 12, 13, 14, 15, 16, 17, 18, 19],
                "brightness": {
                        "max_val": 0,
                        "min_val": 100,
                    },
                "1": {
                    "add on tick": {
                        "min_val": 1,
                        "max_val": 50,
                    },
                },

                "10": {
                    "colors": [[242, 152, 17], [221, 240, 14], [18, 237, 14], [44, 14, 237], [255, 50, 0],
                               [219, 18, 55], [153, 26, 199], [145, 17, 242], [255, 255, 255], [255, 255, 0]]
                },
                "2": {
                    "r": {
                        "min_val": 100,
                        "max_val": 1000,
                    },
                    "colors": 1000,
                    "add on tick": {
                        "min_val": 1,
                        "max_val": 10,
                    }
                },
                "3": {
                    "color": [255, 0, 0],
                    "d": 5,
                    "r": 10
                }
            },
            "configs": {},
            "led_configs": {},
            "lock": False,  # блокировка при обмене данных для избежания сбоев
            "port": 80,
            "brightness": 10,
        }

    def load_config(self):

        try:

            server_address = ('192.168.0.123', 80)
            # print('Подключено к {} порт {}'.format(*server_address))
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(server_address)
            mess = "settings get_temp_json"
            message = mess.encode()
            sock.sendall(message)
            # Смотрим ответ
            amount_received = 0
            # amount_expected = len(message)
            data = sock.recv(1024).decode()
            amount_received += len(data)
            # mess = data.decode()
            print(f'Получено: {data}')
            self.esp["configs"] = json.loads(data)
            print(self.esp)
        except Exception as e:
            print(e)

    def set_lock_label(self, s: bool):
        if s:
            self.ids.lock_label.text = "LOCK"
        else:
            self.ids.lock_label.text = ""

    def set_brig(self, *arg):
        if self.ids.brightness_slider.value != self.brightness:
            self.run_command(f"setbrig {int(self.ids.brightness_slider.value)}", "-c")
            self.brightness = self.ids.brightness_slider.value

    def get_current_ip(self):
        if self.ids.ip_switch.active:
            return '192.168.4.1'
        else:
            return '192.168.0.123'

    def _run_command(self, command: str, *flags):
        if self.esp["lock"]:
            return
        self.esp["lock"] = True
        self.set_lock_label(True)
        ip = self.get_current_ip()
        r = None
        if "-c" in flags:
            r = self._send(ip, "command " + command)
        elif "-s" in flags:
            if command == "get_main_json" or command == "gmj":
                r = self._send(ip, "settings get_main_json")
                self.esp["configs"] = json.loads(r)

            elif command == "get_temp_json" or command == "gtj":
                r = self._send(ip, "settings get_temp_json")
                self.esp["led_configs"] = json.loads(r)

            elif command == "set_main_json" or command == "smj":
                r = self._send(ip, f"settings set_main_json {json.dumps(self.esp['configs'])}")

            elif command == "set_temp_json" or command == "stj":
                r = self._send(ip, f"settings set_temp_json {json.dumps(self.esp['led_configs'])}")

        self.esp["lock"] = False
        self.set_lock_label(False)

    def run_command(self, command: str, *flags):
        try:
            send_t = threading.Thread(target=self._run_command, args=(command, *flags))
            send_t.start()
        except Exception as e:
            self.ids.debug_label.text = str(e)

    def _send(self, ip, arg):

        server_address = (ip, self.esp["port"])
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(server_address)
            print('Подключено к {} порт {}'.format(*server_address))
            print(f'Отправка: {arg}')
            message = arg.encode()
            sock.sendall(message)
            amount_received = 0
            data = sock.recv(4096).decode()
            amount_received += len(data)
            print(f'Получено: {data}')
            sock.close()
        except Exception as e:
            data = "error"
            self.ids.debug_label.text = self.ids.debug_label.text + str(e)
        return data

    @staticmethod
    def get_color(arg=""):
        if arg == "panel_color":
            # return "#eeeaea"
            return "#bbbbbb"
        if arg == "selected_color_background":
            # return "#97ecf8"
            return "#97ecf8"
        return "#eeeaea"


class ContentNavigationDrawer(MDBoxLayout):
    screen_manager = ObjectProperty()
    nav_drawer = ObjectProperty()


class ModeButton(Button):
    pass


# loop = asyncio.get_event_loop()
# loop.run_until_complete(ArgbLedControl().async_run(async_lib="asyncio"))
# loop.close()
if __name__ == '__main__':
    ArgbLedControl().run()

# ['Red', 'Pink','Purple', 'DeepPurple', 'Indigo', 'Blue',
# 'LightBlue', 'Cyan', 'Teal', 'Green', 'LightGreen', 'Lime',
# 'Yellow', 'Amber', 'Orange', 'DeepOrange', 'Brown', 'Gray', 'BlueGray']
