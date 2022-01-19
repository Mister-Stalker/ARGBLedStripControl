import machine
import time
import json
import network
import socket
import select
import strip_control_class

from time import sleep_ms, ticks_ms
from machine import I2C, Pin
from esp8266_i2c_lcd import I2cLcd


# debug_lcd.putstr("It Works!\nSecond Line")
configs = json.load(open("config.json"))
strip = strip_control_class.LedStrip(pin=machine.Pin(configs["strip pin"]), leds=configs["leds"])
strip.fill_all([0, 0, 0])


print(configs)
print(type(configs))
if configs["debug"]:
    try:
        DEFAULT_I2C_ADDR = 0x27
        i2c = I2C(scl=Pin(5), sda=Pin(4), freq=100000)
        debug_lcd = I2cLcd(i2c, DEFAULT_I2C_ADDR, 2, 16)
    except:
        configs["debug"] = 0
divider = 2
button = machine.Pin(13, machine.Pin.IN)
print("pin val", button.value())
##############################################
is_ap = False

if button.value():
    import gc
    gc.collect()

    ssid = 'ArgbLedStripController'
    password = '123456789'

    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(essid=ssid, password=password)
    if configs["debug"]:
        debug_lcd.putstr("ap connect")
    time.sleep(1)
    while not ap.active():
        print(".", end="")
        pass

    print('Connection successful')
    print(ap.ifconfig())
    sta_if = ap
    is_ap = True

else:

    sta_if = network.WLAN(network.STA_IF)
    # sta_if = network.WLAN(network.AP_IF)
    print('connecting to network...')
    sta_if.active(True)
    sta_if.ifconfig(tuple(configs["static_ip"]))
    for wifi in configs["wifi"]:
        sta_if.connect(wifi["ssid"], wifi["pass"])
        i = 0
        while (not sta_if.isconnected()) and i < configs["leds"]:
            strip.set_led([255, 0, 0], i)
            if configs["debug"] and not i % (configs['leds']//16):
                debug_lcd.putstr(".")

            i += 1
            time.sleep(10/configs["leds"])
        if configs["debug"]:
            debug_lcd.clear()
        if sta_if.isconnected():
            break
        else:
            time.sleep(1)
            strip.fill_all([0, 0, 0])
    print('network config:', sta_if.ifconfig())

    if not sta_if.isconnected():
        strip.fill_all([255, 0, 0])
        print("not connect")
        time.sleep(2)
        strip.fill_all([0, 0, 0])
    if sta_if.isconnected():
        print("connect")
        strip.fill_all([0, 255, 0])
        time.sleep(2)
        strip.fill_all([0, 0, 0])


#################################################


# def get_path(request: str):
#     """ Find route """
#     # print("req", type(request), request)
#     lines = request.split("\r\n")
#     method = re.search("^([A-Z]+)", lines[0]).group(1)
#     path = re.search("^[A-Z]+\\s+(/[-a-zA-Z0-9_.]*)", lines[0]).group(1)
#     # print("method, path", method, path)
#     return path


def handle_http(client, client_addr):
    print("handle_http")
    data = str(client.recv(4096), "utf-8").split()
    print("received", data)
    if len(data) < 2:
        client.send("not correct command")
        client.close()
        return
    if data[0] == "command":
        if data[1] == "mode":
            try:
                strip.switch_effect(data[2])
            except Exception as e:
                client.send("error")
                print(e)
            finally:
                client.close()
        elif data[1] == "setdiv":
            try:
                global divider
                divider = int(data[2])
                client.send(str(divider))
                print("divider=", divider)
            except Exception as e:
                client.send("error")
                print(e)
            finally:
                client.close()
        elif data[1] == "rgb":
            try:
                strip.switch_effect("21", data[2])
            except Exception as e:
                print(e)
                pass
            finally:
                client.close()
        elif data[1] == "setbrig":
            try:
                strip.set_brig(int(data[2]))
            except Exception as e:
                print(e)
                client.send("error")
            finally:
                client.close()
        else:
            client.close()
    elif data[0] == "settings":
        if data[1] == "set_temp_json":
            try:
                strip.set_temp_json_from_string(" ".join(data[2:]))
                print(strip.temp)
                client.send("Done")
            except Exception as e:
                print(e)
            finally:
                client.close()
        elif data[1] == "get_temp_json":
            try:
                client.send(json.dumps(strip.temp))
            except Exception as e:
                client.send("error")
                print(e)
            finally:
                client.close()
        elif data[1] == "get_main_json":
            try:
                client.send(json.dumps(json.load(open("config.json"))))
            except Exception as e:
                print(e)
                client.send("error")
            finally:
                client.close()
        elif data[1] == "set_main_json":
            try:
                js = json.loads(" ".join(data[2:]))
                print(js, type(js))
                json.dump(js, open('config.json', "w"))
                client.send("Done")
            except Exception as e:
                print(e)
                client.send("error")
            finally:
                client.close()


    else:
        client.send("no")
        client.close()
    if configs["debug"]:
        debug_lcd.clear()
        debug_lcd.move_to(0, 0)
        debug_lcd.putstr(sta_if.ifconfig()[0]+" "+str(strip.temp['current mode']))




def serv(port=80):
    if configs["debug"]:
        debug_lcd.clear()
        debug_lcd.move_to(0, 0)
        debug_lcd.putstr(sta_if.ifconfig()[0]+" "+str(strip.temp['current mode']))
    http = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    addr = (socket.getaddrinfo("0.0.0.0", port))[0][-1]
    http.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    http.bind(addr)
    http.listen(4)
    tics = 0
    while True:
        tics += 1
        r, w, err = select.select((http,), (), (), 0.01)
        if r:
            for readable in r:
                print(readable)
                client, client_addr = http.accept()
                handle_http(client, client_addr)
        if tics >= divider:
            tics = 0
            strip.run()

    # a cюда можно вставить обработку еще-чего-то
    # а можно вставить такую обработку по таймеру


if sta_if.isconnected() or is_ap:
    serv()
else:
    while True:
        time.sleep_ms(10*divider)
        strip.run()
