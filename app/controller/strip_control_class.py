import neopixel
import time
import random
import json
"""
data = json.load(open("led_configs.json"))

temp = {
    "current mode": data["start mode"],

    "brightness": 10,
    '1': {
        "color": 0,
        "add on tick": data['1']["add on tick"],  # 10000 colors
    },
    '2': {
        "r": data["2"]["r"],
        "colors": data["2"]["colors"],
        "color": 0,
        "add on tick": data["2"]["add on tick"],  # 10000 colors
    },
    '3': {
        "color": [255, 0, 0],
        "d": 5,
        "r": 10,
        "run": 0,
    },
    '10': {
        "current color": 0,
        "colors": data['10']["colors"]
    },
    '21': {
        "color": [57, 255, 20]
    }
}
"""


class LedStrip(neopixel.NeoPixel):
    def __init__(self, pin, leds):
        self.leds = leds
        super().__init__(pin, leds)
        # self.fill_all((57, 255, 20))
        # self.fill_all((200, 50, 0))
        self._mods_association = {
            1: self._effect1,
            2: self._effect2,
            3: self._effect3,
            10: self._effect_rgb,
            21: self._effect_21,
        }
        self._load_temp()

    def _load_temp(self):
        data = json.load(open("led_configs.json"))

        self.temp = {
                "current mode": data["start mode"],

                "brightness": 10,
                '1': {
                    "color": 0,
                    "add on tick": data['1']["add on tick"],  # 10000 colors
                },
                '2': {
                    "r": data["2"]["r"],
                    "colors": data["2"]["colors"],
                    "color": 0,
                    "add on tick": data["2"]["add on tick"],  # 10000 colors
                },
                '3': {
                    "color": [255, 0, 0],
                    "d": 5,
                    "r": 10,
                    "run": 0,
                },
                '10': {
                    "current color": 0,
                    "colors": data['10']["colors"]
                },
                '21': {
                    "color": [57, 255, 20]
                }
            }

    @staticmethod
    def hsv_to_rgb(h, s, v):
        if s == 0.0: v *= 255; return (v, v, v)
        i = int(h * 6.)  # XXX assume int() truncates!
        f = (h * 6.) - i;
        p, q, t = int(255 * (v * (1. - s))), int(255 * (v * (1. - s * f))), int(255 * (v * (1. - s * (1. - f))));
        v *= 255;
        i %= 6
        if i == 0: return (v, t, p)
        if i == 1: return (q, v, p)
        if i == 2: return (p, v, t)
        if i == 3: return (p, q, v)
        if i == 4: return (t, p, v)
        if i == 5: return (v, p, q)

    @staticmethod
    def hsv_to_rgb_fix_for_np(h, s, v):
        if s == 0.0: v *= 255; return (v, v, v)
        i = int(h * 6.)  # XXX assume int() truncates!
        f = (h * 6.) - i;
        p, q, t = int(255 * (v * (1. - s))), int(255 * (v * (1. - s * f))), int(255 * (v * (1. - s * (1. - f))));
        v *= 255;
        i %= 6
        if i == 0: return (t, v, p)
        if i == 1: return (v, q, p)
        if i == 2: return (v, p, t)
        if i == 3: return (q, p, v)
        if i == 4: return (p, t, v)
        if i == 5: return (p, v, q)

    def set_led(self, color, n):
        color = list(map(lambda x: int(x * self.temp["brightness"] / 100), color))
        self[n] = (color[1], color[0], color[2])
        self.write()

    def fill_all(self, color):
        """
        заливает всю ленту цветом, преобразуя яркость
        :param color:
        :return:
        """
        color = list(map(lambda x: int(x*self.temp["brightness"]/100), color))
        self.fill((color[1], color[0], color[2]))
        self.write()

    def fill_all_clr(self, color):
        """
        заливает всю ленту выбранным цветом без изменений!!!
        :param color:
        :return:
        """
        self.fill((color[1], color[0], color[2]))
        self.write()

    def set_brig(self, num: int):
        self.temp["brightness"] = num

    def _effect_rgb(self):
        lst = self.temp['10']["colors"]
        self.fill_all(lst[self.temp['10']["current color"]])

    def _effect1(self):
        self.fill_all(self.hsv_to_rgb(self.temp['1']["color"]/10000, 1, 1))
        self.temp['1']["color"] += self.temp['1']["add on tick"]
        if self.temp['1']["color"] >= 10000:
            self.temp['1']["color"] = 1

    def _effect2(self):
        t = time.time_ns()
        t2 = time.time()
        col = self.temp['2']["color"]
        x = self.temp['2']["r"]/self.leds
        for i in range(1, self.leds):
            col = (col + x) % 1000
            self[i] = list(map(lambda x: int(x * self.temp["brightness"] / 100), self.hsv_to_rgb_fix_for_np(col/self.temp['2']["colors"], 1, 1)))
            # print(self[i])
        self.write()
        # print(time.time_ns()-t, t2 - time.time())
        self.temp['2']["color"] += self.temp['2']["add on tick"]
        if self.temp['2']["color"] >= 1000:
            self.temp['2']["color"] = 0

    def _effect3(self):
        color = self.temp['3']["color"][0]
        color += (random.getrandbits(2) - (random.getrandbits(1)+1))
        color2 = self.temp['3']["color"][1]
        r = random.getrandbits(1)
        if r == 0:
            r = -1
        color2 += r
        if color > 255:
            color = 250
        elif color < 150:
            color = 155
        if color2 > 15:
            color2 = 15
        elif color2 < 0:
            color2 = 0
        self.temp['3']["color"] = [color, color2, 0]
        # print((random.getrandbits(2)))
        # print(self.temp['3']["color"])
        self.fill_all(self.temp['3']["color"])

    def _effect_21(self):
        # print(self.temp['21']["color"])
        self.fill_all(self.temp['21']["color"])

    def nothing(self):
        pass

    def run(self):
        self._mods_association[self.temp["current mode"]]()

    def switch_effect(self, arg: str, *args):
        if arg.isdigit():
            n = int(arg)
            # print(n)
            if (n >= 10) and (n <= 20):
                self.temp["current mode"] = 10
                self.temp['10']["current color"] = n - 10
            elif n == 21:
                # print(*args)
                self.temp["current mode"] = 21
                self.temp['21']["color"] = list(map(int, args[-1].split("_")))
            else:
                if str(n) in self.temp.keys():
                    self.temp["current mode"] = n

        print("current mode", self.temp["current mode"])

    def set_temp_json_from_string(self, json_string: str):
        self.temp = json.loads(json_string)

