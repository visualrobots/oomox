import os
import random
import subprocess
import json
from collections import defaultdict
from itertools import groupby
from gi.repository import Gdk, Gtk, Gio


script_dir = os.path.dirname(os.path.realpath(__file__))
oomox_root_dir = os.path.join(script_dir, "../")
user_config_dir = os.path.join(
    os.environ.get(
        "XDG_CONFIG_HOME",
        os.path.join(os.environ.get("HOME"), ".config/")
    ),
    "oomox/"
)
user_theme_dir = os.path.join(user_config_dir, "colors/")
colors_dir = os.path.join(oomox_root_dir, "colors/")
user_palette_path = os.path.join(user_config_dir, "recent_palette.json")

THEME_KEYS = [
    {
        'key': 'BG',
        'type': 'color',
        'display_name': 'Background'
    },
    {
        'key': 'FG',
        'type': 'color',
        'display_name': 'Foreground/text'
    },
    {
        'key': 'MENU_BG',
        'type': 'color',
        'display_name': 'Menu/toolbar background'
    },
    {
        'key': 'MENU_FG',
        'type': 'color',
        'display_name': 'Menu/toolbar text'
    },
    {
        'key': 'SEL_BG',
        'type': 'color',
        'display_name': 'Selection highlight'
    },
    {
        'key': 'SEL_FG',
        'type': 'color',
        'display_name': 'Selection text'
    },
    {
        'key': 'TXT_BG',
        'type': 'color',
        'display_name': 'Textbox background'
    },
    {
        'key': 'TXT_FG',
        'type': 'color',
        'display_name': 'Textbox text'
    },
    {
        'key': 'BTN_BG',
        'type': 'color',
        'display_name': 'Button background'
    },
    {
        'key': 'BTN_FG',
        'type': 'color',
        'display_name': 'Button text'
    },
    {
        'key': 'HDR_BTN_BG',
        'fallback_key': 'BTN_BG',
        'type': 'color',
        'display_name': 'Header button background'
    },
    {
        'key': 'HDR_BTN_FG',
        'fallback_key': 'BTN_FG',
        'type': 'color',
        'display_name': 'Header button text'
    },

    {
        'type': 'separator',
        'display_name': 'Options'
    },

    {
        'key': 'ROUNDNESS',
        'type': 'int',
        'fallback_value': 2,
        'display_name': 'Roundness'
    },
    {
        'key': 'SPACING',
        'type': 'int',
        'fallback_value': 3,
        'display_name': '(GTK3) Spacing'
    },
    {
        'key': 'GRADIENT',
        'type': 'float',
        'fallback_value': 0.0,
        'display_name': '(GTK3) Gradient'
    },
    {
        'key': 'GTK3_GENERATE_DARK',
        'type': 'bool',
        'fallback_value': True,
        'display_name': '(GTK3) Add dark variant'
    },
    {
        'key': 'GTK2_HIDPI',
        'type': 'bool',
        'fallback_value': False,
        'display_name': '(GTK2) HiDPI'
    },

    {
        'type': 'separator',
        'display_name': 'Iconset'
    },

    {
        'key': 'ICONS_LIGHT_FOLDER',
        'type': 'color',
        'fallback_key': 'SEL_BG',
        'display_name': 'Light base (folders)'
    },
    {
        'key': 'ICONS_LIGHT',
        'fallback_key': 'SEL_BG',
        'type': 'color',
        'display_name': 'Light base'
    },
    {
        'key': 'ICONS_MEDIUM',
        'type': 'color',
        'fallback_key': 'BTN_BG',
        'display_name': 'Medium base'
    },
    {
        'key': 'ICONS_DARK',
        'type': 'color',
        'fallback_key': 'BTN_FG',
        'display_name': 'Dark stroke'
    },
]


def mkdir_p(dir):
    if os.path.isdir(dir):
        return
    os.makedirs(dir)


def ls_r(path):
    return [
        os.path.join(files[0], file)
        for files in os.walk(path)
        for file in files[2]
    ]


def load_palette():
    try:
        with open(user_palette_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def save_palette(palette):
    with open(user_palette_path, 'w') as f:
        return json.dump(palette, f)


def get_presets():
    file_paths = [
        {
            "name": "".join(
                path.startswith(colors_dir) and path.rsplit(colors_dir) or
                path.rsplit(user_theme_dir)
            ),
            "path": path,
        }
        for path in ls_r(user_theme_dir) + ls_r(colors_dir)
    ]
    result = defaultdict(list)
    for key, group in groupby(file_paths, lambda x: x['name'].split('/')[0]):
        group = sorted(list(group), key=lambda x: x['name'])
        display_name = group[0]['name']
        if display_name in result:
            display_name = display_name + " (default)"
        result[display_name] = group
    return dict(result)


def get_random_gdk_color():
    return Gdk.RGBA(random.random(), random.random(), random.random(), 1)


def convert_theme_color_to_gdk(theme_color):
    gdk_color = Gdk.RGBA()
    gdk_color.parse("#" + theme_color)
    return gdk_color


def convert_gdk_to_theme_color(gdk_color):
    return "".join([
        "{0:02x}".format(int(n * 255))
        for n in (gdk_color.red, gdk_color.green, gdk_color.blue)
    ])


def resolve_color_links(colorscheme):
    # @TODO: rename it
    for key_obj in THEME_KEYS:
        key = key_obj.get('key')
        if not key:
            continue
        fallback_key = key_obj.get('fallback_key')
        fallback_value = key_obj.get('fallback_value')
        value = colorscheme.get(key)
        if value is None and (fallback_key or fallback_value is not None):
            if fallback_value is not None:
                value = colorscheme[key] = fallback_value
            else:
                value = colorscheme[key] = colorscheme[fallback_key]
        if value is None:
            colorscheme[key] = "ff3333"
        elif isinstance(value, str) and value.startswith("$"):
            try:
                colorscheme[key] = colorscheme[value.lstrip("$")]
            except KeyError:
                colorscheme[key] = "ff3333"
        if key_obj['type'] == 'bool':
            if isinstance(value, str):
                colorscheme[key] = value.lower() == 'true'
        elif key_obj['type'] == 'int':
            colorscheme[key] = int(value)
        elif key_obj['type'] == 'float':
            colorscheme[key] = float(value)
    return colorscheme


def bash_preprocess(preset_path):
    colorscheme = {"NOGUI": True}
    process = subprocess.run(
        [
            "bash", "-c",
            "source " + preset_path + " ; " +
            "".join(
                "echo ${{{}-None}} ;".format(obj['key'])
                for obj in THEME_KEYS
                if obj.get('key')
            )
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    if process.stderr:
        raise(Exception(
            "Pre-processing failed:\nstdout:\n{}\nstderr:\n{}".format(
                process.stdout, process.stderr
            )))

    lines = process.stdout.decode("UTF-8").split()
    i = 0
    for obj in THEME_KEYS:
        if not obj.get('key'):
            continue
        value = lines[i]
        if value == 'None':
            value = None
        colorscheme[obj['key']] = value
        i += 1

    return colorscheme


def read_colorscheme_from_path(preset_path):
    # @TODO: remove legacy stuff
    colorscheme = {}
    with open(preset_path) as f:
        for line in f.readlines():
            parsed_line = line.strip().split('=')
            # migration workaround:
            try:
                if not parsed_line[0].startswith("#"):
                    colorscheme[parsed_line[0]] = parsed_line[1]
            except IndexError:
                pass
    # migration workaround #2:
    if 'NOGUI' in colorscheme:
        colorscheme = bash_preprocess(preset_path)
    colorscheme = resolve_color_links(colorscheme)
    return colorscheme


def read_colorscheme_from_preset(preset_name):
    return read_colorscheme_from_path(os.path.join(colors_dir, preset_name))


def save_colorscheme(preset_name, colorscheme):
    path = os.path.join(user_theme_dir, preset_name)
    try:
        with open(path, 'w') as f:
            if 'NAME' not in colorscheme:
                f.write("NAME={}\n".format(preset_name))
            for key in sorted(colorscheme.keys()):
                f.write("{}={}\n".format(
                    key, colorscheme[key]
                ))
    except FileNotFoundError:
        mkdir_p(os.path.dirname(path))
        return save_colorscheme(preset_name, colorscheme)
    return path


class CenterLabel(Gtk.Label):

    def __init__(self, text):
        super().__init__(text)
        self.set_justify(Gtk.Justification.CENTER)
        self.set_alignment(0.5, 0.5)
        self.set_margin_left(6)
        self.set_margin_right(6)
        self.set_margin_top(6)
        self.set_margin_bottom(6)


class ImageButton(Gtk.Button):

    icon = None
    image = None

    def __init__(self, icon_name, tooltip_text=None):
        super().__init__()
        self.icon = Gio.ThemedIcon(name=icon_name)
        self.image = Gtk.Image.new_from_gicon(self.icon, Gtk.IconSize.BUTTON)
        self.add(self.image)
        if tooltip_text:
            self.set_tooltip_text(tooltip_text)
