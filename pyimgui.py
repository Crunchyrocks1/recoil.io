import glfw
import imgui
from imgui.integrations.glfw import GlfwRenderer
import moderngl
import time
import numpy as np
import ctypes
import os
import keyboard            
import threading
import pydirectinput       

GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
SetWindowLong = ctypes.windll.user32.SetWindowLongW
GetWindowLong = ctypes.windll.user32.GetWindowLongW

settings = {
    "activation_key": "shift",         # Activation key for recoil control (e.g., "shift", "f1", etc.)
    "reaction_speed": 5,               # ms between recoil steps
    "vertical_strength": 4,            # Vertical recoil strength
    "horizontal_strength": 1,          # Horizontal recoil strength
    "horizontal_direction": 1,         # 1 = right, -1 = left
    "vertical_end": 1,                 # Vertical end multiplier
    "vertical_transition_time": 2000,  # Vertical transition time
    "horizontal_start_delay": 2000,    # Horizontal start delay
    "reset_delay": 4000,               # Recoil reset delay
    "shake_x_min": -1,                 # Min shake on X-axis
    "shake_x_max": 1,                  # Max shake on X-axis
    "shake_y_min": -1,                 # Min shake on Y-axis
    "shake_y_max": 1,                  # Max shake on Y-axis
    "recoil_enabled": False,           # Toggle recoil compensation
    "max_recoil_distance": 10,         # Maximum recoil distance
    "recoil_speed": 1,                 # Speed of recoil compensation
    "shake_intensity": 0.5,            # Intensity of shake (randomness)
    "smooth_recoil": False,            # Enable smooth recoil (interpolated)
    "recoil_smoothness_factor": 5      # Factor for smooth recoil effect (higher = slower smoothness)
}

def set_custom_style():
    style = imgui.get_style()
    colors = style.colors
    style.window_rounding = 10
    style.frame_rounding = 8
    style.grab_rounding = 12
    style.scrollbar_rounding = 8
    style.item_spacing = (12, 10)
    style.window_padding = (15, 15)
    style.frame_padding = (10, 6)

    colors[imgui.COLOR_WINDOW_BACKGROUND] = (0.15, 0.15, 0.05, 0.9)  # Dark gold background
    colors[imgui.COLOR_FRAME_BACKGROUND] = (0.25, 0.20, 0.10, 0.9)  # Lighter gold frame background
    colors[imgui.COLOR_FRAME_BACKGROUND_HOVERED] = (0.30, 0.25, 0.15, 0.9)  # Hovered frame background
    colors[imgui.COLOR_FRAME_BACKGROUND_ACTIVE] = (0.40, 0.35, 0.20, 0.9)  # Active frame background
    colors[imgui.COLOR_BUTTON] = (0.30, 0.25, 0.15, 0.8)  # Gold button color
    colors[imgui.COLOR_BUTTON_HOVERED] = (0.45, 0.40, 0.25, 0.8)  # Hovered button color
    colors[imgui.COLOR_BUTTON_ACTIVE] = (0.50, 0.45, 0.30, 0.8)  # Active button color
    colors[imgui.COLOR_SLIDER_GRAB] = (0.70, 0.60, 0.30, 1.0)  # Gold slider grab
    colors[imgui.COLOR_SLIDER_GRAB_ACTIVE] = (0.85, 0.70, 0.35, 1.0)  # Active gold slider grab
    colors[imgui.COLOR_TEXT] = (1, 1, 1, 1)  

    colors[imgui.COLOR_CHECK_MARK] = (1.0, 0.84, 0.0, 1.0)  # Gold checkmark color (RGB: 255, 215, 0)


def set_click_through(window, enable):
    hwnd = glfw.get_win32_window(window)
    ex_style = GetWindowLong(hwnd, GWL_EXSTYLE)
    if enable:
        SetWindowLong(hwnd, GWL_EXSTYLE, ex_style | WS_EX_LAYERED | WS_EX_TRANSPARENT)
    else:
        SetWindowLong(hwnd, GWL_EXSTYLE, ex_style & ~WS_EX_TRANSPARENT)

def window_focus_callback(window, focused):
    global visible
    if not focused:
        visible = False  
    else:
        if fade_alpha > 0.01:
            visible = True  

def apply_recoil():
    dx = -settings["horizontal_strength"] * settings["horizontal_direction"]
    dy = settings["vertical_strength"] * settings["vertical_end"]  

    if settings["smooth_recoil"]:
        dx /= settings["recoil_smoothness_factor"]
        dy /= settings["recoil_smoothness_factor"]

    dx = np.clip(dx, -settings["max_recoil_distance"], settings["max_recoil_distance"])
    dy = np.clip(dy, -settings["max_recoil_distance"], settings["max_recoil_distance"])

    dx += np.random.uniform(-settings["shake_x_min"], settings["shake_x_max"]) * settings["shake_intensity"]
    dy += np.random.uniform(-settings["shake_y_min"], settings["shake_y_max"]) * settings["shake_intensity"]

    dx = int(dx)
    dy = int(dy)

    pydirectinput.moveRel(dx, dy)

def recoil_loop():
    """Background thread: watches activation key and applies recoil when enabled."""
    while True:
        if settings["recoil_enabled"] and keyboard.is_pressed(settings["activation_key"]):
            apply_recoil()
            time.sleep(settings["reaction_speed"] / 1000.0)
        else:
            time.sleep(0.005)

def main():
    global fade_alpha, visible

    fade_alpha = 0.0
    visible = False

    t = threading.Thread(target=recoil_loop, daemon=True)
    t.start()

    if not glfw.init():
        raise Exception("GLFW init failed")

    mon = glfw.get_primary_monitor()
    mode = glfw.get_video_mode(mon)
    sw, sh = mode.size.width, mode.size.height
    taskbar_height = 40
    ah = sh - taskbar_height

    glfw.window_hint(glfw.DECORATED, glfw.FALSE)
    glfw.window_hint(glfw.FLOATING, glfw.TRUE)
    glfw.window_hint(glfw.TRANSPARENT_FRAMEBUFFER, glfw.TRUE)
    glfw.window_hint(glfw.RESIZABLE, glfw.FALSE)

    window = glfw.create_window(sw, ah, "", None, None)
    glfw.set_window_pos(window, 0, 0)
    glfw.make_context_current(window)
    glfw.set_window_focus_callback(window, window_focus_callback)

    imgui.create_context()
    io = imgui.get_io()
    font_path = "C:/Windows/Fonts/consola.ttf"
    if os.path.exists(font_path):
        io.fonts.add_font_from_file_ttf(font_path, 18)

    impl = GlfwRenderer(window)
    ctx = moderngl.create_context()
    set_custom_style()

    target_fps = 144
    last_time = time.time()

    set_click_through(window, True)

    while not glfw.window_should_close(window):
        glfw.poll_events()

        if keyboard.is_pressed('insert'):
            visible = not visible
            fade_target = 1.0 if visible else 0.0
            if visible:
                set_click_through(window, False)
            else:
                set_click_through(window, True)
            time.sleep(0.2)

        fade_target = 1.0 if visible else 0.0
        if abs(fade_alpha - fade_target) > 0.01:
            fade_alpha += (fade_target - fade_alpha) * 0.08
        else:
            fade_alpha = fade_target

        if fade_alpha < 0.01:
            ctx.clear(0, 0, 0, 0)
            glfw.swap_buffers(window)
            continue

        now = time.time()
        dt = now - last_time
        if dt < 1 / target_fps:
            time.sleep((1 / target_fps) - dt)
        last_time = now

        impl.process_inputs()
        ctx.clear(0, 0, 0, fade_alpha * 0.78)
        imgui.new_frame()
        imgui.push_style_var(imgui.STYLE_ALPHA, fade_alpha)

        win_w, win_h = 650, 600
        imgui.set_next_window_position((sw - win_w) // 2, (ah - win_h) // 2)
        imgui.set_next_window_size(win_w, win_h)
        imgui.begin("Nexus Recoil Controller",
                    flags=imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_COLLAPSE | imgui.WINDOW_NO_TITLE_BAR)

        imgui.text_colored("Nexus Recoil Controller", 1.0, 0.84, 0.0, 1.0)
        imgui.separator()

        _, settings["activation_key"] = imgui.input_text("Activation Key", settings["activation_key"], 32)
        _, settings["reaction_speed"] = imgui.slider_int("Reaction Speed (ms)", settings["reaction_speed"], 0, 50)
        _, settings["vertical_strength"] = imgui.slider_int("Vertical Strength", settings["vertical_strength"], 0, 20)
        _, settings["horizontal_strength"] = imgui.slider_int("Horizontal Strength", settings["horizontal_strength"], 0, 20)
        _, settings["horizontal_direction"] = imgui.slider_int("Horz. Dir", settings["horizontal_direction"], -1, 1)
        _, settings["vertical_end"] = imgui.slider_int("Vertical End Mult.", settings["vertical_end"], 0, 5)
        _, settings["max_recoil_distance"] = imgui.slider_int("Max Recoil Distance", settings["max_recoil_distance"], 0, 50)
        _, settings["recoil_speed"] = imgui.slider_int("Recoil Speed", settings["recoil_speed"], 1, 10)
        _, settings["shake_intensity"] = imgui.slider_float("Shake Intensity", settings["shake_intensity"], 0.0, 2.0)
        _, settings["recoil_smoothness_factor"] = imgui.slider_int("Smoothness Factor", settings["recoil_smoothness_factor"], 1, 20)

        _, settings["recoil_enabled"] = imgui.checkbox("Recoil Comp.", settings["recoil_enabled"])
        _, settings["smooth_recoil"] = imgui.checkbox("Smooth Recoil", settings["smooth_recoil"])

        imgui.end()
        imgui.pop_style_var()

        imgui.render()
        impl.render(imgui.get_draw_data())
        glfw.swap_buffers(window)

    impl.shutdown()
    glfw.terminate()

if __name__ == "__main__":
    main()
