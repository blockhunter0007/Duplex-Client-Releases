import threading
import tkinter as tk
from tkinter import ttk, messagebox, colorchooser, simpledialog
import colorsys
import urllib.request
import urllib.error
import json
import keyboard
import time
import os
import pathlib
import sys
import datetime

# =====================================================================
# LOGGING
# ====================================================================
logs = []
current_path = sys.path[0]
class LOG_COLORS:
    INFO = "\033[94m"
    SUCCESS = "\033[92m"
    WARNING = "\033[93m"
    ERROR = "\033[91m"
    FATAL = "\033[95m"
    log_colors = {
        "INFO": INFO,
        "WARNING": WARNING,
        "ERROR": ERROR,
        "FATAL": FATAL,
        "SUCCESS": SUCCESS
    }

DEBUG = True

def log(message: str, level: str = "INFO"):
    global logs

    time_stamp = datetime.datetime.now().strftime("%H:%M:%S")
    if DEBUG:
        print(f"{LOG_COLORS.log_colors.get(level, '')}[{level}] {time_stamp} {message}\033[0m")
    logs.append({"level": level, "timestamp": time_stamp, "message": message})
    if level == "FATAL":
        str_to_save = "".join([f"[{log['level']}] {time_stamp} {log['message']}\n" for log in logs])
        with open(f"{current_path}/crashlog.log", "a", encoding="utf-8") as f:
            f.write(str_to_save)
        sys.exit(1)
    if len(logs) > 1000:
        logs.pop(0)
# =====================================================================


CLIENT_VERSION = "1.0.11"


# =====================================================================
# CONFIGURATION & THEME
# =====================================================================
configs = {}
config = {}
settings = {
    "theme": "default",
    "alpha": 0.80,
    "hide_uninjected": "hide",
    "windows": {},
    "config": "default"
}
API_BASE = "http://127.0.0.1:65534"
CLIENT_NAME = "Duplex Lab"
THEMES = {
    "default": {
        "bg": "#1e1e1e",
        "fg": "#ffffff",
        "accent": "#ff5555",
        "header_bg": "#2e2e2e",
        "module_bg": "#2e2e2e",
        "active_fg": "#50fa7b",
        "active_bg": "#2e2e2e",
        "disabled_fg": "#888888"
    },
}
CURRENT_THEME = list(THEMES.keys())[0]
script_dir = pathlib.Path(__file__).parent.resolve()
if not os.path.exists(script_dir / "data"):
    os.makedirs(script_dir / "data")
if not os.path.exists(script_dir / "data" / "configs"):
    os.makedirs(script_dir / "data" / "configs")
if not os.path.exists(script_dir / "data" / "configs" / f"{settings['config']}.config"):
    with open(script_dir / "data" / "configs" / f"{settings['config']}.config", "w") as f:
        json.dump(config, f, indent=4)
if not os.path.exists(script_dir / "data" / "themes"):
    os.makedirs(script_dir / "data" / "themes")
if not os.path.exists(script_dir / "data" / "settings.json"):
    with open(script_dir / "data" / "settings.json", "w") as f:
        json.dump(settings, f, indent=4)
try:
    with open(script_dir / "data" / "settings.json", "r") as f:
        settings = json.load(f)
except (FileNotFoundError, json.JSONDecodeError) as e:
    log(f"Error loading settings: {e}", "ERROR")
try:
    with open(script_dir / "data" / "configs" / f"{settings['config']}.config", "r") as f:
        config = json.load(f)
except (FileNotFoundError, json.JSONDecodeError) as e:
    log(f"Error loading config {settings['config']}: {e}", "ERROR")
    settings["config"] = "default"
    config = {}
theme_files = [f.name for f in pathlib.Path(script_dir / "data" / "themes").iterdir() if f.is_file()]
for theme_file in theme_files:
    try:
        with open(script_dir / "data" / "themes" / theme_file, "r") as f:
            theme_data = json.load(f)
            for theme_name, theme_values in theme_data.items():
                if theme_name not in THEMES:
                    THEMES[theme_name] = theme_values
                else:
                    log(f"Theme {theme_name} from {theme_file} already exists. Skipping.", "WARNING")
    except Exception as e:
        log(f"Error loading theme {theme_file}: {e}", "ERROR")
config_files = [f.name for f in pathlib.Path(script_dir / "data" / "configs").iterdir() if f.is_file()]
for config_file in config_files:
    try:
        with open(script_dir / "data" / "configs" / config_file, "r") as f:
            config_data = json.load(f)
            if config_file not in configs or config_file == "New Config":
                configs[config_file.split(".config")[0]] = config_data
    except Exception as e:
        log(f"Error loading config {config_file}: {e}", "ERROR")
configs["New Config"] = {}
MOCK_MODULES = {
    'airjump': {'toggle': True, 'value': False, 'category': 'movement', 'min_value': None, 'max_value': None},
    'see_entities': {'toggle': True, 'value': False, 'category': 'visual', 'min_value': None, 'max_value': None},
    'phasefly': {'toggle': True, 'value': False, 'category': 'movement', 'min_value': None, 'max_value': None},
    'noweb': {'toggle': True, 'value': False, 'category': 'movement', 'min_value': None, 'max_value': None},
    'zoom': {'toggle': True, 'value': False, 'category': 'visual', 'min_value': None, 'max_value': None},
    'smooth_swing': {'toggle': True, 'value': False, 'category': 'visual', 'min_value': None, 'max_value': None},
    'speed': {'toggle': True, 'value': True, 'category': 'movement', 'min_value': 0.15, 'max_value': 1.0},
    'nofall': {'toggle': True, 'value': False, 'category': 'movement', 'min_value': None, 'max_value': None},
    'hitbox': {'toggle': True, 'value': True, 'category': 'combat', 'min_value': 0.6, 'max_value': 3.0},
    'reach': {'toggle': True, 'value': True, 'category': 'combat', 'min_value': 3.0, 'max_value': 6.0}
}
CONNECTED = True

# =====================================================================
# API CALL HELPERS
# =====================================================================
def unload_config(config):
    working_modules = api_request("/get_working")
    if working_modules is None:
        working_modules = list(MOCK_MODULES.keys())
    for module_name in list(config.keys()):
        if module_name in working_modules:
            api_request(f"/toggle_module/{module_name}/False")
def load_config(config):
    working_modules = api_request("/get_working")
    if working_modules is None:
        working_modules = list(MOCK_MODULES.keys())
    for module_name, module_data in config.items():
        if module_name in working_modules:
            api_request(f"/toggle_module/{module_name}/{module_data.get('active', False)}")
            if "value" in module_data:
                api_request(f"/set_module_value/{module_name}/{module_data['value']}")
def api_request(endpoint, method="GET", bypass = False, show_log=True):
    if not CONNECTED and not bypass:
        if show_log:
            log(f"API request to {endpoint} skipped: Not connected to server.", "WARNING")
        return None
    try:
        req = urllib.request.Request(f"{API_BASE}{endpoint}")
        req.add_header("Content-Type", "application/json")
        response = urllib.request.urlopen(req, timeout=99.0)
        if response.getcode() == 200:
            return json.loads(response.read().decode())
    except urllib.error.URLError as e:
        if show_log:
            log(f"API request to {endpoint} failed: {e}", "ERROR")
    return {}
def save_config():
    try:
        with open(script_dir / "data" / "configs" / f"{settings['config']}.config", "w") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        log(f"Failed to save configuration: {e}", "ERROR")
    save_settings()
def save_settings():
    try:
        with open(script_dir / "data" / "settings.json", "w") as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        log(f"Failed to save settings: {e}", "ERROR")
def check_thread():
    while True:
        time.sleep(30)
        response = api_request("/", bypass=True, show_log=False)
        if response and response.get("success"):
            log(f"Server is running. Injection status: {response.get('injected')}, Injection time: {response.get('injection_time')}")
            if not response.get("injected"):
                log("Attempting to inject...")
                inject_response = api_request("/inject")
                if inject_response and "message" in inject_response:
                    log(inject_response["message"])
            break
threading.Thread(target=check_thread, daemon=True).start()
class keyboard_listener:
    def __init__(self):
        keyboard.on_press(self.handle_key_press)
        self.keys = {}
    def remove_key(self, key, callback):
        key = key.lower()
        if key in self.keys:
            self.keys[key].remove(callback)
            if not self.keys[key]:
                del self.keys[key]
    def add_key(self, key, callback):
        key = key.lower()
        if key not in self.keys:
            self.keys[key] = []
        self.keys[key].append(callback)
    def handle_key_press(self, event):
        #log(f"Key pressed: {event.name}", "INFO")
        if event.name.lower() in self.keys:
            for callback in self.keys[event.name.lower()]:
                callback()
keyboard_manager = keyboard_listener()
# =====================================================================
# COMPONENT CLASSES
# =====================================================================
HAS_RGB = False
SINK = True
class rainbow_loop:
    def __init__(self, root, widget, speed=0.01, bg=False, fg=True):
        self.root = root
        self.widget = widget
        self.speed = speed
        self.bg = bg
        self.fg = fg
        self.hue = 0.0
        self.running = True
    def update_color(self):
        if not self.running or not self.widget.winfo_exists():
            return
        self.hue += self.speed
        if self.hue >= 1:
            self.hue = 0.0
        r, g, b = [int(x * 255) for x in colorsys.hsv_to_rgb(self.hue, 1.0, 1.0)]
        color = f"#{r:02x}{g:02x}{b:02x}"
        r, g, b = [int(x * 255) for x in colorsys.hsv_to_rgb((1-self.hue), 1.0, 1.0)]
        inverted = f"#{r:02x}{g:02x}{b:02x}"
        if self.fg:
            self.widget.config(fg=color)
        if self.bg:
            self.widget.config(bg=color)
            #self.widget.config(fg=inverted)
        self.root.after(50, self.update_color)
    def start(self):
        self.running = True
        self.update_color()
    def stop(self):
        self.running = False
class ModuleRow(tk.Frame):
    def __init__(self, parent, name, data, is_working, app_instance, callback=None):
        global config
        super().__init__(parent)
        self.name = name
        self.data = data
        self.is_working = is_working
        self.app = app_instance
        self.callback = callback
        self.colors = THEMES.get(settings.get("theme", CURRENT_THEME), THEMES[CURRENT_THEME])
        if self.name not in config["modules"]:
            config["modules"][self.name] = {}
        self.is_active = False
        self.is_expanded = False
        self.keybind = config["modules"][self.name].get("keybind", None)
        if self.keybind and self.keybind not in ["None", "", None]:
            keyboard_manager.add_key(self.keybind, self.toggle_active)
        self.binding_mode = False
        self.configure(bg=self.colors["module_bg"], bd=1, relief="groove")
        self.lbl_name = tk.Label(
            self, text=self.name, bg=self.colors["module_bg"], 
            fg=self.colors["fg"], font=("Courier", 10, "bold"), anchor="w"
        )
        self.lbl_name.pack(fill="x", padx=0, pady=0)
        self.lbl_name.bind("<Button-1>", self.toggle_active)
        self.lbl_name.bind("<Button-3>", self.toggle_expand)
        self.options_frame = tk.Frame(self, bg=self.colors["module_bg"])
        self.btn_bind = tk.Button(
            self.options_frame, text=f"Bind: {self.keybind}", font=("Courier", 8),
            bg=self.colors["header_bg"], fg=self.colors["fg"], bd=0, command=self.start_binding
        )
        self.btn_bind.pack(fill="x", padx=10, pady=2)
        if self.data.get("value") and self.data.get("min_value") is not None:
            self.val_var = tk.DoubleVar(value=config["modules"][self.name].get("value", self.data.get("min_value", 0)))
            self.slider = tk.Scale(
                self.options_frame, from_=self.data["min_value"], to=self.data["max_value"],
                resolution=0.05, orient="horizontal", variable=self.val_var,
                bg=self.colors["module_bg"], fg=self.colors["fg"], 
                highlightthickness=0, font=("Courier", 8), command=self.on_slider_change
            )
            self.slider.pack(fill="x", padx=10, pady=2)
            if config["modules"][self.name].get("value") is not None:
                self.val_var.set(config["modules"][self.name]["value"])
        self.custom_btns = []
        self.custom_cbs = []
        if self.data.get("btn"):
            for btn_info in self.data["btn"]:
                self.custom_btn = tk.Button(
                    self.options_frame, text=btn_info["text"], font=("Courier", 8),
                    bg=self.colors["header_bg"], fg=self.colors["fg"], bd=0, command=btn_info["command"]
                )
                self.custom_btn.pack(fill="x", padx=10, pady=2)
                self.custom_btns.append(self.custom_btn)
        if self.data.get("cb"):
            for cb_info in self.data["cb"]:
                self.custom_cb_var = tk.BooleanVar(value=config["modules"][self.name].get("rgb", False))
                self.custom_cb = tk.Checkbutton(
                    self.options_frame, text=cb_info["text"], font=("Courier", 8),
                    bg=self.colors["module_bg"], fg=self.colors["fg"], selectcolor=self.colors["header_bg"],
                    variable=self.custom_cb_var, command=lambda: cb_info["command"](self.custom_cb_var.get())
                )
                self.custom_cb.pack(fill="x", padx=10, pady=2)
                self.custom_cbs.append(self.custom_cb)
        if config["modules"][self.name].get("active", False):
            self.is_active = True
        if HAS_RGB:
            self.rgb = rainbow_loop(self.app.root, self.lbl_name, bg=True, fg=False)
        save_config()
        self.update_status()

    def toggle_active(self, event=None, state=None):
        if not self.is_working and self.app.hide_uninjected.get() == "grey":
            return

        self.is_active = not self.is_active if state is None else state
        if self.callback:
            self.callback(event, self.is_active)
        else:
            threading.Thread(target=api_request, args=(f"/toggle_module/{self.name}/{self.is_active}",), daemon=True).start()
        self.update_status()

    def toggle_expand(self, event=None):
        if self.is_expanded:
            self.options_frame.pack_forget()
        else:
            self.options_frame.pack(fill="x", pady=5)
        self.is_expanded = not self.is_expanded

    def start_binding(self):
        self.btn_bind.config(text="Press any key...")
        self.binding_mode = True
        self.focus_set()
        self.bind("<Key>", self.set_keybind)

    def set_keybind(self, event):
        if self.binding_mode:
            if self.keybind not in ["None", "", None]:
                keyboard_manager.remove_key(self.keybind, self.toggle_active)
            self.keybind = event.keysym.upper()
            self.btn_bind.config(text=f"Bind: {self.keybind}")
            self.unbind("<Key>")
            self.binding_mode = False
            keyboard_manager.add_key(self.keybind, self.toggle_active)
            global config
            config["modules"][self.name]["keybind"] = self.keybind
            save_config()

    def on_slider_change(self, val):
        global config
        if self.data.get("value_command"):
            self.data["value_command"](val)
            return
        config["modules"][self.name]["value"] = val
        save_config()
        threading.Thread(target=api_request, args=(f"/set_module_value/{self.name}/{val}",), daemon=True).start()

    def update_status(self):
        if not self.is_working:
            if self.app.hide_uninjected.get() == "grey":
                self.lbl_name.config(fg=self.colors["disabled_fg"])
                return
        config["modules"][self.name]["active"] = self.is_active
        if self.is_active:
            self.lbl_name.config(fg=self.colors["active_fg"], bg=self.colors["active_bg"])
            if HAS_RGB:
                self.rgb.start()
        else:
            self.lbl_name.config(fg=self.colors["fg"], bg=self.colors["module_bg"])
            if HAS_RGB:
                self.rgb.stop()

    def refresh_theme(self):
        self.colors = THEMES[settings["theme"]]
        self.configure(bg=self.colors["module_bg"])
        self.options_frame.config(bg=self.colors["module_bg"])
        self.btn_bind.config(bg=self.colors["header_bg"], fg=self.colors["fg"])
        if hasattr(self, 'slider'):
            self.slider.config(bg=self.colors["module_bg"], fg=self.colors["fg"])
        for btn in self.custom_btns:
            btn.config(bg=self.colors["header_bg"], fg=self.colors["fg"])
        for cb in self.custom_cbs:
            cb.config(bg=self.colors["module_bg"], fg=self.colors["fg"], selectcolor=self.colors["header_bg"])
        self.update_status()
    def reload_cfg(self):
        global config
        if not self.name in config["modules"]:
            config["modules"][self.name] = {"active": False, "keybind": "None", "value": 0}
        self.toggle_active(state=config["modules"][self.name].get("active", False))
        if hasattr(self, 'slider'):
            self.slider.set(config["modules"][self.name].get("value", self.data.get("min_value", 0))) if hasattr(self, 'slider') else None


class CategoryWindow(tk.Toplevel):
    def __init__(self, parent, title, x, y):
        global settings
        super().__init__(parent)
        self.title_text = title
        self.colors = THEMES.get(settings.get("theme", CURRENT_THEME), THEMES[CURRENT_THEME])
        if title in settings["windows"]:
            x = settings["windows"][title]["x"]
            y = settings["windows"][title]["y"]
        else:
            settings["windows"][title] = {"x": x, "y": y, "minimized": False}
        self.overrideredirect(True)
        self.geometry(f"200x350+{x}+{y}")
        self.configure(bg="#624949")#self.colors["bg"])
        self.attributes("-topmost", True)
        self.attributes("-alpha", settings["alpha"])
        self.header = tk.Label(
            self, text=self.title_text.upper(), bg=self.colors["accent"], 
            fg=self.colors["bg"], font=("Courier", 11, "bold"), cursor="fleur"
        )
        self.header.pack(fill="x")
        self.header.bind("<Button-1>", self.start_drag)
        self.header.bind("<ButtonRelease-1>", self.click)
        self.header.bind("<B1-Motion>", self.do_drag)
        self.container = tk.Frame(self, bg=self.colors["bg"])
        self.container.pack(fill="x", expand=False)
        self.wm_attributes("-transparentcolor", "#624949")
        self.minimized = False
        self.start_time = 0
        self.modules = []
        if settings["windows"][title]["minimized"]:
            self.click(None, state=True)
    def click(self, event, state=None):
        global settings
        if time.time() - self.start_time < 0.2 or state is not None:
            self.minimized = not self.minimized if state is None else state
            settings["windows"][self.title_text]["minimized"] = self.minimized
            if self.minimized:
                self.container.pack_forget()
            else:
                self.container.pack(fill="x", expand=False)
            save_config()
        self._drag_x = None
        self._drag_y = None
    def start_drag(self, event):
        self.start_time = time.time()
        self._drag_x = event.x
        self._drag_y = event.y

    def do_drag(self, event):
        global settings
        x = self.winfo_x() + event.x - self._drag_x
        y = self.winfo_y() + event.y - self._drag_y
        self.geometry(f"+{x}+{y}")
        settings["windows"][self.title_text] = {"x": x, "y": y, "minimized": self.minimized}
        save_config()

    def refresh_theme(self):
        self.colors = THEMES[settings["theme"]]
        self.header.config(bg=self.colors["accent"], fg=self.colors["bg"])
        self.container.config(bg=self.colors["bg"])
        for mod in self.modules:
            mod.refresh_theme()
    def update_alpha(self):
        self.attributes("-alpha", settings["alpha"])
    def reload_cfg(self):
        for mod in self.modules:
            mod.reload_cfg()

# =====================================================================
# MAIN APPLICATION CORE
# =====================================================================
class ClickGUIApp:
    def __init__(self):
        global config
        global settings
        self.root = tk.Tk()
        if "alpha" not in settings:
            settings["alpha"] = 0.80
        if "theme" not in settings:
            settings["theme"] = CURRENT_THEME
        if "modules" not in config:
            config["modules"] = {}
        if "windows" not in settings:
            settings["windows"] = {}
        if "main" not in settings["windows"]:
            settings["windows"]["main"] = {"x": self.root.winfo_x(), "y": self.root.winfo_y(), "minimized": False}
        if "watermark" not  in config["modules"]:
            config["modules"]["watermark"] = {"active": False, "keybind": "None", "text_color": "#FFFFFF", "rgb": False, "position": {"x": 100, "y": 100}, "font_size": 20}
        if "clickgui" not in config["modules"]:
            config["modules"]["clickgui"] = {"active": True, "keybind": "INSERT"}
        self.root.title(CLIENT_NAME)
        self.root.geometry("340x200")
        self.root.geometry(f"+{settings['windows']['main']['x']}+{settings['windows']['main']['y']}")
        self.colors = THEMES.get(settings.get("theme", CURRENT_THEME), THEMES[CURRENT_THEME])
        self.root.configure(bg=self.colors["bg"])
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", settings["alpha"])
        self.root.overrideredirect(True)
        self.root.bind("<Escape>", lambda e: self.toggle_windows(state=False))
        self.root.wm_attributes("-transparentcolor", "#624949")
        self.hide_uninjected = tk.StringVar(value="hide")
        self.windows = {}
        self.show_windows = True
        self.minimized = settings["windows"]["main"]["minimized"]
        self.start_time = 0
        self.show_watermark = config["modules"]["watermark"]["active"]
        self.watermark_window = WatermarkWindow(self.root, title=CLIENT_NAME, text_color=config["modules"]["watermark"]["text_color"], rgb=config["modules"]["watermark"]["rgb"], font_size=config["modules"]["watermark"]["font_size"])
        if config["modules"]["watermark"]["active"]:
            self.watermark_window.deiconify()
        else:
            self.watermark_window.withdraw()
        self.setup_launcher_ui()
        if self.minimized:
            self.on_release(None, state=True)
        self.initialize_backend()
    def on_release(self, event, state=None):
        global settings
        if time.time() - self.start_time < 0.2 or state is not None:
            self.minimized = not self.minimized if state is None else state
            if self.minimized:
                self.title_lbl.pack_forget()
                self.frame_controls.pack_forget()
                self.rb_hide.pack_forget()
                self.rb_grey.pack_forget()
                self.theme_menu.pack_forget()
                self.config_menu.pack_forget()
                self.lbl_status.pack_forget()
                self.root.configure(bg="#624949")
                settings["windows"]["main"]["minimized"] = True
            else:
                self.title_lbl.pack(pady=10)
                self.frame_controls.pack(pady=5)
                self.rb_hide.pack(side="left", padx=5)
                self.rb_grey.pack(side="left", padx=5)
                self.theme_menu.pack(pady=5)
                self.config_menu.pack(pady=5)
                self.lbl_status.pack(side="bottom", fill="x")
                self.root.configure(bg=self.colors["bg"])
                settings["windows"]["main"]["minimized"] = False
            save_config()

    def on_click(self, event):
        self.start_time = time.time()
        self._drag_x = event.x
        self._drag_y = event.y
    def on_drag(self, event):
        global settings
        x = self.root.winfo_x() + event.x - self._drag_x
        y = self.root.winfo_y() + event.y - self._drag_y
        self.root.geometry(f"+{x}+{y}")
        settings["windows"]["main"] = {"x": x, "y": y, "minimized": self.minimized}
    def close(self):
        if not messagebox.askyesno("Leave Injection", "Do you want to keep the injection active after closing the GUI?"): 
            api_request("/eject")
        self.root.destroy()
        save_config()
    def setup_launcher_ui(self):
        self.top_bar = tk.Frame(self.root, bg=self.colors["accent"], height=30)
        self.top_bar.pack(fill="x")
        self.top_bar.bind("<Button-1>", self.on_click)
        self.top_bar.bind("<B1-Motion>", self.on_drag)
        self.top_bar.bind("<ButtonRelease-1>", self.on_release)
        self.top_bar.grid_columnconfigure(0, weight=1)
        self.top_bar.grid_columnconfigure(1, weight=0)
        self.top_bar.grid_columnconfigure(2, weight=1)
        self.top_bar.grid_columnconfigure(3, weight=0)
        self.top_title = tk.Label(self.top_bar, text=f"{CLIENT_NAME} Settings", bg=self.colors["accent"], fg=self.colors["bg"], font=("Courier", 10, "bold"))
        self.top_title.grid(row=0, column=1, pady=5)
        self.top_title.bind("<Button-1>", self.on_click)
        self.top_title.bind("<B1-Motion>", self.on_drag)
        self.top_title.bind("<ButtonRelease-1>", self.on_release)
        self.close_btn = tk.Button(self.top_bar, text="✕", command=self.close, bg=self.colors["accent"], fg=self.colors["bg"], bd=0)
        self.close_btn.grid(row=0, column=3, padx=5, pady=5)
        self.title_lbl = tk.Label(self.root, text=CLIENT_NAME, font=("Courier", 14, "bold"), bg=self.colors["bg"], fg=self.colors["accent"])
        self.title_lbl.pack(pady=10)

        self.frame_controls = tk.Frame(self.root, bg=self.colors["bg"])
        self.frame_controls.pack(pady=5)
        self.rb_hide = tk.Radiobutton(self.frame_controls, text="Hide Failed", variable=self.hide_uninjected, value="hide", 
                                 bg=self.colors["bg"], fg=self.colors["fg"], selectcolor=self.colors["header_bg"], command=self.reload_ui_visibility)
        self.rb_hide.pack(side="left", padx=5)
        self.rb_grey = tk.Radiobutton(self.frame_controls, text="Grey out Failed", variable=self.hide_uninjected, value="grey", 
                                 bg=self.colors["bg"], fg=self.colors["fg"], selectcolor=self.colors["header_bg"], command=self.reload_ui_visibility)
        self.rb_grey.pack(side="left", padx=5)


        self.theme_var = tk.StringVar(value=settings["theme"])
        self.theme_menu = tk.OptionMenu(self.root, self.theme_var, *list(THEMES.keys()))
        self.theme_menu.config(bg=self.colors["bg"], fg=self.colors["fg"], highlightthickness=0, bd=0)
        self.theme_menu.pack(pady=5)
        self.theme_var.trace("w", self.change_theme)
        self.config_var = tk.StringVar(value=settings["config"])
        self.config_menu = tk.OptionMenu(self.root, self.config_var, *list(configs.keys()))
        self.config_menu.config(bg=self.colors["bg"], fg=self.colors["fg"], highlightthickness=0, bd=0)
        self.config_menu.pack(pady=5)
        self.config_var.trace("w", self.change_config)
        self.lbl_status = tk.Label(self.root, text="Checking backend server status...", font=("Courier", 9), bg=self.colors["bg"], fg="orange")
        self.lbl_status.pack(side="bottom", fill="x")
    def change_config(self, event=None, *args):
        global config
        global settings
        selected_config = self.config_var.get()
        if selected_config in configs and not selected_config == "New Config":
            unload_config(config)
            config = configs[selected_config]
            load_config(config)
            settings["config"] = selected_config
            save_config()
            self.reload_ui_visibility()
        elif selected_config == "New Config":
            new_config_name = simpledialog.askstring("New Config", "Enter new config name:")
            new_config_name = new_config_name + ".config"
            if new_config_name in configs or new_config_name in ["New Config", "default.config", "", None]:
                messagebox.showerror("Error", "Invalid or duplicate config name.")
                self.config_var.set(settings["config"])
                return
            configs.pop("New Config", None)
            configs[new_config_name] = {}
            config = configs[new_config_name]
            settings["config"] = new_config_name
            if "modules" not in config:
                config["modules"] = {}
            if "watermark" not  in config["modules"]:
                config["modules"]["watermark"] = {"active": False, "keybind": "None", "text_color": "#FFFFFF", "rgb": False, "position": {"x": 100, "y": 100}, "font_size": 20}
            if "clickgui" not in config["modules"]:
                config["modules"]["clickgui"] = {"active": True, "keybind": "INSERT"}
            self.config_menu['menu'].delete(0, 'end')
            self.config_menu['menu'].add_command(label=new_config_name, command=tk._setit(self.config_var, new_config_name))
            self.config_menu['menu'].add_command(label="New Config", command=tk._setit(self.config_var, "New Config"))
            self.reload_ui_visibility()
            save_config()
    def initialize_backend(self):
        res = api_request("/")
        if not res:
            messagebox.showwarning("Server Offline", f"Could not reach server at {API_BASE}.\nRunning in Offline/Mock dataset mode.")
            self.lbl_status.config(text="Status: Mock Dataset Mode (Offline)", fg="yellow")
            self.build_gui(MOCK_MODULES, list(MOCK_MODULES.keys())[len(MOCK_MODULES.keys())//2:])  # Simulate half working modules
            global CONNECTED
            CONNECTED = False
            return
        self.lbl_status.config(text="Status: Server up, checking injection status...", fg="orange")
        if not res.get("injected"):
            self.lbl_status.config(text="Status: Injecting core module...", fg="orange")
            api_request("/inject")
        all_modules = api_request("/get_all_modules")["all_modules"] or MOCK_MODULES
        working_modules = api_request("/get_working") or list(MOCK_MODULES.keys())
        res = api_request("/get_injection_time")
        self.lbl_status.config(text=f"Status: Injected & Fully Hooked took {res.get('injection_time', 0):.2f} seconds", fg="#50fa7b")
        self.build_gui(all_modules, working_modules)

    def build_gui(self, all_modules, working_modules):
        global config
        categories = set(info['category'] for info in all_modules.values())
        categories.add("client")
        start_x, start_y = 100, 150
        for idx, cat in enumerate(sorted(categories)):
            win = CategoryWindow(self.root, cat, start_x + (idx * 220), start_y)
            self.windows[cat] = win
            for mod_name, mod_data in all_modules.items():
                if mod_data['category'] == cat:
                    is_working = mod_name in working_modules

                    row = ModuleRow(win.container, mod_name, mod_data, is_working, self)
                    if config.get("modules", {}).get(mod_name, {}).get("active", False):
                        row.toggle_active()
                    win.modules.append(row)

                    if is_working or self.hide_uninjected.get() == "grey":
                        row.pack(fill="x", pady=2)
        for mod_name, mod_data in {
            "clickgui": {
                "toggle": True, "value": False, "category": "client", "min_value": None, "max_value": None
                },
            "watermark": {
                "toggle": True, "value": True, "category": "client", "min_value": 10, "max_value": 40, "value_command": self.watermark_font_size_update, "default": float(config["modules"]["watermark"]["font_size"]),
                "btn": [{"text": "Colors", "command": self.watermark_color_piker, "default": config["modules"]["watermark"]["text_color"]}],
                "cb": [{"text": "RGB", "command": self.watermark_rgb_toggle, "default": config["modules"]["watermark"]["rgb"]}],
            },
            "alpha": {
                "toggle": False, "value": True, "category": "client", "min_value": 0.0, "max_value": 1.0, "value_command": self.update_alpha, "default": settings["alpha"]
            }
        }.items():
            if mod_data['category'] == "client":
                if mod_name == "clickgui":
                    row = ModuleRow(self.windows["client"].container, mod_name, mod_data, True, self, callback=self.toggle_windows)
                    row.toggle_active(state=config["modules"]["clickgui"]["active"])
                elif mod_name == "watermark":
                    row = ModuleRow(self.windows["client"].container, mod_name, mod_data, True, self, callback=self.watermark_toggle)
                    row.toggle_active(state=config["modules"]["watermark"]["active"])
                else:
                    row = ModuleRow(self.windows["client"].container, mod_name, mod_data, True, self)
                row.pack(fill="x", pady=2)
                self.windows["client"].modules.append(row)
        save_config()
    def watermark_font_size_update(self, size):
        global config
        config["modules"]["watermark"]["font_size"] = int(float(size))
        save_config()
        self.watermark_window.update_font(font=("Arial", config["modules"]["watermark"]["font_size"]))
    def update_alpha(self, alpha):
        global settings
        settings["alpha"] = alpha
        save_config()
        self.root.attributes("-alpha", alpha)
        for win in self.windows.values():
            win.update_alpha()
    def toggle_windows(self, event=None, state=None):
        global config
        self.show_windows = not self.show_windows if state is None else state
        config["modules"]["clickgui"]["active"] = self.show_windows
        for cat, win in self.windows.items():
            if self.show_windows:
                win.deiconify()
            else:
                win.withdraw()
        if self.show_windows:
            self.root.deiconify()
        else:
            self.root.withdraw()
        save_config()
    def watermark_color_piker(self):
        color_code = colorchooser.askcolor(title="Choose Watermark Color", initialcolor=config["modules"]["watermark"]["text_color"])
        if color_code[1]:
            self.watermark_update(text_color=color_code[1])
    def watermark_rgb_toggle(self, state):
        self.watermark_update(rgb=state)
    def watermark_toggle(self, event=None, state=None):
        global config
        config["modules"]["watermark"]["active"] = state if state is not None else not config["modules"]["watermark"]["active"]
        self.show_watermark = config["modules"]["watermark"]["active"]
        if self.show_watermark:
            self.watermark_window.deiconify()
        else:
            self.watermark_window.withdraw()
        save_config()
    def watermark_update(self, text_color=None, rgb=None):
        global config
        if text_color is not None:
            config["modules"]["watermark"]["text_color"] = text_color
        if rgb is not None:
            config["modules"]["watermark"]["rgb"] = rgb
        save_config()
        self.watermark_window.update_color(color=config["modules"]["watermark"]["text_color"], rgb=config["modules"]["watermark"]["rgb"])

    def reload_ui_visibility(self):
        for cat, win in self.windows.items():
            for row in win.modules:
                row.pack_forget()
                if row.is_working or self.hide_uninjected.get() == "grey":
                    row.pack(fill="x", pady=2)
                row.update_status()

    def change_theme(self, event, *args):
        global config
        global CURRENT_THEME
        settings["theme"] = self.theme_var.get()
        CURRENT_THEME = settings["theme"]
        self.colors = THEMES[CURRENT_THEME]
        self.top_bar.config(bg=self.colors["accent"])
        self.close_btn.config(bg=self.colors["accent"], fg=self.colors["bg"])
        self.top_title.config(bg=self.colors["accent"], fg=self.colors["bg"])
        self.title_lbl.config(bg=self.colors["bg"], fg=self.colors["accent"])
        self.frame_controls.config(bg=self.colors["bg"])
        self.rb_grey.config(bg=self.colors["bg"], fg=self.colors["fg"], selectcolor=self.colors["header_bg"])
        self.rb_hide.config(bg=self.colors["bg"], fg=self.colors["fg"], selectcolor=self.colors["header_bg"])
        self.theme_menu.config(bg=self.colors["bg"], fg=self.colors["fg"])
        self.config_menu.config(bg=self.colors["bg"], fg=self.colors["fg"])
        self.lbl_status.config(bg=self.colors["bg"], fg=self.colors["fg"])
        if not self.minimized:
            self.root.configure(bg=self.colors["bg"])
        for win in self.windows.values():
            win.refresh_theme()
        save_config()

    def run(self):
        self.root.mainloop()

class WatermarkWindow(tk.Toplevel):
    def __init__(self, parent, title="Watermark", text_color="#FFFFFF", rgb = False, font_size=20):
        super().__init__(parent)
        self.text_color = text_color
        self.rgb = rgb
        self.font_size = font_size
        self.overrideredirect(True)
        self.text_color
        self.hue = 0.0
        self.geometry(f"{200+len(title)*config['modules']['watermark']['font_size']//2}x{50+config['modules']['watermark']['font_size']}")
        self.wm_attributes("-topmost", True)
        self.wm_attributes("-transparentcolor", "#624949")
        self.configure(bg="#624949")
        self.label = tk.Label(self, text=title, font=("Arial", config["modules"]["watermark"]["font_size"]), fg=self.text_color, bg="#624949")
        self.label.pack(expand=True)
        if self.rgb:
            self.rgb_cycle()
        self.label.bind("<Button-1>", self.start_drag)
        self.label.bind("<B1-Motion>", self.drag_window)
    def start_drag(self, event):
        self._drag_x = event.x
        self._drag_y = event.y
    def drag_window(self, event):
        global config
        x = self.winfo_x() + event.x - self._drag_x
        y = self.winfo_y() + event.y - self._drag_y
        self.geometry(f"+{x}+{y}")
        config["modules"]["watermark"]["position"] = {"x": x, "y": y}
        save_config()
    def update_watermark(self, text):
        self.label.config(text=text)
        self.geometry(f"{200+len(text)*config['modules']['watermark']['font_size']//2}x{50+config['modules']['watermark']['font_size']}")
    def update_color(self, color=None, rgb=None):
        if color is not None:
            self.label.config(fg=color)
        if rgb is not None:
            self.rgb = rgb
            if self.rgb:
                self.rgb_cycle()
    def rgb_cycle(self):
        if self.rgb:
            r, g, b = [int(x * 255) for x in colorsys.hsv_to_rgb(self.hue, 1.0, 1.0)]
            new_color = f"#{r:02x}{g:02x}{b:02x}"
            self.update_color(new_color)
            self.hue += 0.01 
            if self.hue > 1.0:
                self.hue = 0.0
            self.after(50, self.rgb_cycle)
    def update_font(self, font):
        self.label.config(font=font)
        self.geometry(f"{200+len(self.label.cget('text'))*font[1]//2}x{50+font[1]}")
if __name__ == "__main__":
    #watermark_window = WatermarkWindow(None, text_color="#FFFFFF", rgb=True)
    #watermark_window.mainloop()
    app = ClickGUIApp()
    app.run()