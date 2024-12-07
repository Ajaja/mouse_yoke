from pynput import mouse, keyboard
from threading import Thread
import pydirectinput
import vgamepad as vg
import sys
import time
import ctypes


configs = {
    "center_xy_axes_key":  keyboard.KeyCode.from_char('/'),
    "rudder_mode":  keyboard.KeyCode.from_char('\\')  # keyboard.Key.ctrl_l
}

gamepad = vg.VX360Gamepad()
(screen_size_width, screen_size_height) = pydirectinput.size()

global_x = 0
global_y = 0
active = False
mainmode = True
mainmode_rudder = False
pydirectinput.FAILSAFE = False

pixelsToFloatX = 0.0
pixelsToFloatY = 0.0
last_x_position = screen_size_width / 2
last_y_position = screen_size_height / 2
last_x_position_mode = screen_size_width / 2


user32 = ctypes.WinDLL('User32.dll')


def is_capslock_on():
    return True if user32.GetKeyState(0x14) else False


def turn_capslock_off():
    if is_capslock_on():
        user32.keybd_event(0x14, 0X3a, 0X1, 0)
        user32.keybd_event(0x14, 0X3a, 0X3, 0)


def is_scrolllock_on():
    return True if user32.GetKeyState(0x91) else False


def turn_scrolllock_off():
    if is_capslock_on():
        user32.keybd_event(0x91, 0X46, 0X1, 0)
        user32.keybd_event(0x91, 0X46, 0X3, 0)


def is_numlock_on():
    return True if user32.GetKeyState(0x90) else False


def turn_numlock_off():
    if is_numlock_on():
        user32.keybd_event(0x90, 0X45, 0X1, 0)
        user32.keybd_event(0x90, 0X45, 0X3, 0)


def mouseYoke(x, y):
    global pixelsToFloatX, pixelsToFloatY
    global global_x, global_y

    global_x = x
    global_y = y

    if active:
        if x >= 0 and x <= screen_size_width:
            pixelsToFloatX = x / (screen_size_width / 2) - 1
        if y >= 0 and y <= screen_size_height:
            pixelsToFloatY = y / (screen_size_height / 2) - 1

        if mainmode:
            gamepad.left_joystick_float(x_value_float=pixelsToFloatX, y_value_float=pixelsToFloatY)
            if mainmode_rudder:
                gamepad.right_joystick_float(x_value_float=0, y_value_float=pixelsToFloatX)
        else:
            gamepad.right_joystick_float(x_value_float=0, y_value_float=pixelsToFloatX)
            if last_x_position_mode >= 0 and last_x_position_mode <= screen_size_width:
                gamepad.left_joystick_float(x_value_float=last_x_position_mode / (screen_size_width / 2) - 1, y_value_float=pixelsToFloatY)

        gamepad.update()


def onKeyPress(key):
    global mainmode
    global last_x_position_mode

    if active and mainmode and key == configs["rudder_mode"]:
        mainmode = False
        x = last_x_position_mode
        last_x_position_mode = global_x
        pydirectinput.moveTo(int(x), int(global_y))


def onKeyRelease(key):
    global active
    global mainmode, mainmode_rudder
    global last_x_position_mode
    global last_x_position, last_y_position

    if key == keyboard.Key.scroll_lock:
        active = not active
        if not active:
            last_x_position = global_x
            last_y_position = global_y
        else:
            last_x_position_mode = last_x_position
            pydirectinput.moveTo(int(last_x_position), int(last_y_position))

    elif key == keyboard.Key.caps_lock:
        mainmode_rudder = not mainmode_rudder

    elif key == configs["center_xy_axes_key"] and active:
        if mainmode:
            pydirectinput.moveTo(int(screen_size_width / 2), int(screen_size_height / 2))
        else:
            pydirectinput.moveTo(int(screen_size_width / 2), int(global_y))

    elif key == configs["rudder_mode"] and active and not mainmode:
        mainmode = True
        x = last_x_position_mode
        last_x_position_mode = global_x
        pydirectinput.moveTo(int(x), int(global_y))


def userInterface():
    global active
    global mainmode_rudder

    while (True):
        if is_capslock_on():
            mainmode_rudder = True
        else:
            mainmode_rudder = False
        if is_scrolllock_on():
            active = True
        else:
            active = False
        print("active: ", active)
        print("mainmode: ", mainmode)
        print("mainmode_rudder: ", mainmode_rudder)
        print(f"+{'':—^60}+")
        print(f"|{'Axis':^20}{'Raw input':^20}{'Conversion':^20}|")
        print(f"+{'':—^60}+")
        print(f"|{'X':^20}{global_x:^20}{'{:.2f}'.format((pixelsToFloatX + 1) * 50) + '%':^20}|")
        print(f"|{'Y':^20}{global_y:^20}{'{:.2f}'.format((pixelsToFloatY + 1) * 50) + '%':^20}|")
        print(f"+{'':—^60}+")
        time.sleep(10)


if __name__ == "__main__":

    turn_scrolllock_off()
    turn_capslock_off()

    ui = Thread(target=userInterface)
    ms = mouse.Listener(on_move=mouseYoke)
    kb = keyboard.Listener(on_release=onKeyRelease, on_press=onKeyPress)

    ms.start()
    kb.start()
    ui.start()
    ms.join()
    kb.join()
