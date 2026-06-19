# BO3 Weapon CSV Editor - edit level_common_weapon.csv for Black Ops III modding by TxmEXE222.

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font as tkfont
import csv
import copy
import io
import os
import sys
from typing import Optional, Dict, List, Set, Tuple

VERSION = "Pre-Release 1.0"
APP_NAME = "BO3 Weapon CSV Editor"
UNDO_LIMIT = 50

def _resolve_app_dir() -> str:
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


APP_DIR = _resolve_app_dir()

WINDOW_WIDTH = 785
WINDOW_HEIGHT = 680

DRAGDROP_MAX_HEIGHT = 140
DRAGDROP_MAX_WIDTH = 0

UI_BG = "#18181b"
UI_BG_ELEVATED = "#222226"
UI_BG_BAR = "#27272a"
UI_SURFACE = "#2f2f35"
UI_SURFACE_HOVER = "#3a3a42"
UI_BORDER = "#3f3f48"
UI_ACCENT = "#0ea5e9"
UI_ACCENT_DIM = "#0c4a6e"
UI_FG = "#f4f4f5"
UI_FG_MUTED = "#71717a"
UI_FG_LABEL = "#a1a1aa"

UI_BTN = "#3f3f46"
UI_BTN_HOVER = "#52525b"
UI_BTN_ACTIVE = "#35353b"
UI_BTN_PRIMARY = "#0284c7"
UI_BTN_PRIMARY_HOVER = "#0ea5e9"
UI_BTN_PRIMARY_ACTIVE = "#0369a1"

PREVIEW_FONT = ("Cascadia Code", 10)
PREVIEW_BG = "#141417"
PREVIEW_GUTTER_BG = "#1c1c21"
PREVIEW_CHANGED_BG = "#422006"
PREVIEW_SELECT = "#1e3a5f"

UI_FONT = "Segoe UI"
UI_FONT_SM = (UI_FONT, 9)
UI_FONT_LG = (UI_FONT, 11, "bold")
UI_FONT_LABEL = (UI_FONT, 9, "bold")

CREDIT_LINE = (
    "BO3 Weapon CSV Editor By TxmEXE222 - Inspired by WeaponCSV (MakeCentsGaming)"
)


def _entry_kwargs(**extra) -> dict:
    opts = dict(
        bg=UI_SURFACE,
        fg=UI_FG,
        insertbackground=UI_FG,
        relief=tk.FLAT,
        highlightthickness=1,
        highlightbackground=UI_BORDER,
        highlightcolor=UI_ACCENT,
        bd=0,
        font=UI_FONT_SM,
    )
    opts.update(extra)
    return opts


def _field_label(text: str) -> str:
    return text.replace("_", " ")


BOOL_OPTIONS = ["", "TRUE", "FALSE"]

WEAPON_VO_OPTS = [
    "", "pistol", "rifle", "lmg", "smg", "shotgun", "sniper",
    "grenade", "special", "betty", "launcher", "ball",
    "wpck_ray", "wpck_bowie", "wpck_thundergun", "ray2", "ray3",
    "tesla", "monkey", "octobomb", "quantum", "gersh_device", "dolls",
    "dual", "shrink_ray", "microwavegun", "energy_pistol", "katana",
]

CLASS_OPTIONS = [
    "", "pistol", "rifle", "smg", "lmg", "shotgun",
    "sniper", "grenade", "special", "launcher", "ball",
]

EDITOR_LAYOUT = [
    ("weapon_name",       0, 0, 1, "entry"),
    ("in_box",            0, 1, 1, "bool"),
    ("is_limited",        0, 2, 1, "bool"),
    ("upgrade_name",      1, 0, 1, "entry"),
    ("upgrade_in_box",    1, 1, 1, "bool"),
    ("limit",             1, 2, 1, "entry"),
    ("upgrade_limit",     1, 3, 1, "entry"),
    ("cost",              2, 0, 1, "entry"),
    ("ammo_cost",         2, 1, 1, "entry"),
    ("create_vox",        2, 2, 1, "entry"),
    ("weaponVO",          3, 0, 1, "weaponvo"),
    ("weaponVOresp",      3, 1, 1, "entry"),
    ("hint",              3, 2, 1, "entry"),
    ("class",             4, 0, 1, "class"),
    ("is_wonder_weapon",  4, 1, 1, "bool"),
    ("is_aat_exempt",     4, 2, 1, "bool"),
    ("wallbuy_autospawn", 5, 0, 1, "bool"),
    ("obsolete_false",    5, 1, 1, "bool"),
    ("obsolete2_false",   5, 2, 1, "bool"),
    ("force_attachments", 6, 0, 4, "entry"),
]

COL_WIDTHS: Dict[str, int] = {
    "weapon_name":      140,
    "upgrade_name":     140,
    "cost":              55,
    "ammo_cost":         70,
    "limit":             55,
    "upgrade_limit":     85,
    "weaponVO":          80,
    "weaponVOresp":      95,
    "hint":              80,
    "create_vox":        80,
    "in_box":            60,
    "is_limited":        75,
    "upgrade_in_box":    95,
    "is_wonder_weapon":  120,
    "wallbuy_autospawn": 120,
    "obsolete_false":    95,
    "obsolete2_false":   95,
    "is_aat_exempt":     95,
    "class":             65,
    "force_attachments": 140,
}

COL_WIDTH_PAD = 20
COL_WIDTH_MAX = 420

def _editor_widget_width(field: str, wtype: str,
                         weaponvo_values: List[str],
                         class_values: List[str]) -> int:
    if wtype == "bool":
        return 12
    if wtype == "weaponvo":
        longest = max((len(v) for v in weaponvo_values), default=0)
        return max(14, longest + 1)
    if wtype == "class":
        longest = max((len(v) for v in class_values), default=0)
        return max(10, longest + 1)
    if field == "force_attachments":
        return 48
    px = COL_WIDTHS.get(field, 90)
    return max(8, (px + 6) // 7)


def _editor_column_minsizes() -> List[int]:
    label_font = tkfont.Font(font=UI_FONT_LABEL)
    widget_font = tkfont.Font(font=UI_FONT_SM)
    mins = [76, 76, 76, 76]

    for field, _row, col, span, wtype in EDITOR_LAYOUT:
        label_px = label_font.measure(field) + 14
        widget_px = widget_font.measure("0" * _editor_widget_width(
            field, wtype, WEAPON_VO_OPTS, CLASS_OPTIONS,
        )) + 24
        need = max(label_px, widget_px)

        if span == 1:
            mins[col] = max(mins[col], need)
        else:
            share = max(need // span, 76)
            for offset in range(span):
                mins[col + offset] = max(mins[col + offset], share)

    return mins


def _is_blank_csv_line(line: List[str]) -> bool:
    return not line or not any(cell.strip() for cell in line)


def _hex_to_rgb(hex_color: str) -> tuple:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


class ToolTip:

    def __init__(self, widget: tk.Misc, text: str) -> None:
        self._widget = widget
        self._text = text
        self._tip: Optional[tk.Toplevel] = None
        widget.bind("<Enter>", self._show, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress-1>", self._hide, add="+")

    def _show(self, _event: Optional[tk.Event] = None) -> None:
        if self._tip is not None:
            return

        self._widget.update_idletasks()
        x = self._widget.winfo_rootx() + (self._widget.winfo_width() // 2)
        y = self._widget.winfo_rooty() + self._widget.winfo_height() + 8

        tip = tk.Toplevel(self._widget)
        tip.wm_overrideredirect(True)
        tip.wm_attributes("-topmost", True)
        tip.configure(bg=UI_SURFACE)

        tk.Label(
            tip,
            text=self._text,
            bg=UI_SURFACE,
            fg=UI_FG,
            font=UI_FONT_SM,
            justify="center",
            padx=10,
            pady=6,
            relief=tk.FLAT,
            bd=0,
        ).pack()

        tip.update_idletasks()
        tip_w = tip.winfo_width()
        tip.geometry(f"+{x - tip_w // 2}+{y}")
        self._tip = tip

    def _hide(self, _event: Optional[tk.Event] = None) -> None:
        if self._tip is not None:
            self._tip.destroy()
            self._tip = None


class RoundedButton(tk.Canvas):

    _FONT_SIZE = 9
    _pil_font_cache = None

    def __init__(self, parent: tk.Misc, *, text: str, command,
                 bg: str = UI_BG, padx: int = 16, pady: int = 8,
                 radius: int = 8, variant: str = "default") -> None:
        self._command = command
        self._text = text
        self._bg = bg
        self._radius = radius
        self._text_fg = UI_FG
        if variant == "primary":
            self._fill = UI_BTN_PRIMARY
            self._fill_hover = UI_BTN_PRIMARY_HOVER
            self._fill_active = UI_BTN_PRIMARY_ACTIVE
            self._outline = UI_BTN_PRIMARY
        else:
            self._fill = UI_BTN
            self._fill_hover = UI_BTN_HOVER
            self._fill_active = UI_BTN_ACTIVE
            self._outline = UI_BORDER
        self._pressed = False
        self._photo: Optional[tk.PhotoImage] = None

        measure = tkfont.Font(font=UI_FONT_SM)
        tw = measure.measure(text)
        th = measure.metrics("linespace")
        self._width = tw + padx * 2
        self._height = th + pady * 2

        super().__init__(
            parent, width=self._width, height=self._height,
            highlightthickness=0, bd=0, bg=bg, cursor="hand2",
        )
        self._draw(self._fill)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

    @classmethod
    def _pil_font(cls):
        if cls._pil_font_cache is not None:
            return cls._pil_font_cache
        from PIL import ImageFont
        for path in (
            os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", "segoeui.ttf"),
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ):
            if os.path.isfile(path):
                try:
                    cls._pil_font_cache = ImageFont.truetype(path, cls._FONT_SIZE)
                    return cls._pil_font_cache
                except OSError:
                    pass
        cls._pil_font_cache = ImageFont.load_default()
        return cls._pil_font_cache

    def _render_with_pil(self, fill: str) -> tk.PhotoImage:
        from PIL import Image, ImageDraw, ImageTk

        w, h = self._width, self._height
        r = min(self._radius, h // 2, w // 2)
        img = Image.new("RGBA", (w, h), _hex_to_rgb(self._bg) + (255,))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle(
            [1, 1, w - 2, h - 2],
            radius=r,
            fill=_hex_to_rgb(fill) + (255,),
            outline=_hex_to_rgb(self._outline) + (255,),
            width=1,
        )
        draw.text(
            (w / 2, h / 2), self._text,
            fill=_hex_to_rgb(self._text_fg) + (255,),
            font=self._pil_font(),
            anchor="mm",
        )
        photo = ImageTk.PhotoImage(img)
        self._photo = photo
        return photo

    def _draw(self, fill: str) -> None:
        photo = self._render_with_pil(fill)
        self.delete("all")
        self._photo = photo
        self.create_image(0, 0, image=photo, anchor="nw")

    def _on_enter(self, _event: tk.Event) -> None:
        if not self._pressed:
            self._draw(self._fill_hover)

    def _on_leave(self, _event: tk.Event) -> None:
        self._pressed = False
        self._draw(self._fill)

    def _on_press(self, _event: tk.Event) -> None:
        self._pressed = True
        self._draw(self._fill_active)

    def _on_release(self, event: tk.Event) -> None:
        inside = (0 <= event.x <= self.winfo_width()
                  and 0 <= event.y <= self.winfo_height())
        self._pressed = False
        self._draw(self._fill_hover if inside else self._fill)
        if inside and self._command:
            self._command()


class BO3CSVEditor:

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(APP_NAME)
        self.root.configure(bg=UI_BG)

        self.filepath: Optional[str] = None
        self.headers: List[str] = []
        self.rows: List[dict] = []
        self.cur_idx: Optional[int] = None
        self._dirty = False
        self._suppress_events = False
        self._sort_col: Optional[str] = None
        self._sort_reverse = False
        self._tree_col_ids: List[str] = []
        self._tree_keep_idx: Optional[int] = None
        self._preview_baseline = ""
        self._undo_stack: List[List[dict]] = []
        self._redo_stack: List[List[dict]] = []
        self._dragdrop_last_size: Optional[Tuple[int, int]] = None

        self.fvars: Dict[str, tk.StringVar] = {}
        self.fwidgets: Dict[str, tk.Widget] = {}
        self._weaponvo_values = list(WEAPON_VO_OPTS)
        self._class_values = list(CLASS_OPTIONS)
        self._image_refs: List[tk.PhotoImage] = []

        self._dragdrop_img: Optional[tk.PhotoImage] = None
        self._dragdrop_raw: Optional[tk.PhotoImage] = None
        self._preview_built = False

        self._build_ui()
        self._bind_menu()
        self._setup_drag_and_drop()
        self.root.after_idle(self._deferred_startup)

    def _asset_path(self, filename: str) -> str:
        return os.path.join(APP_DIR, filename)

    def _load_photo(self, filename: str) -> Optional[tk.PhotoImage]:
        path = self._asset_path(filename)
        if not os.path.isfile(path):
            return None
        try:
            photo = tk.PhotoImage(file=path)
            photo._bo3_source_path = path
            self._image_refs.append(photo)
            return photo
        except tk.TclError:
            return None

    def _set_window_icon(self) -> None:
        ico = self._asset_path("CSVEdit.ico")
        if os.path.isfile(ico):
            try:
                self.root.iconbitmap(ico)
                return
            except tk.TclError:
                pass

        icon = self._load_photo("CSVEdit.png")
        if icon is not None:
            try:
                self.root.iconphoto(True, icon)
                self.root._bo3_icon = icon
            except tk.TclError:
                pass

    def _scale_photo(self, photo: tk.PhotoImage,
                     max_width: int, max_height: int,
                     *, retain_ref: bool = True) -> tk.PhotoImage:
        max_width = max(1, max_width)
        max_height = max(1, max_height)
        iw, ih = photo.width(), photo.height()
        if iw <= 0 or ih <= 0:
            return photo

        scale = min(max_width / iw, max_height / ih, 1.0)
        tw = max(1, int(iw * scale))
        th = max(1, int(ih * scale))

        path_hint = getattr(photo, "_bo3_source_path", None)
        if path_hint and os.path.isfile(path_hint):
            try:
                from PIL import Image, ImageTk
                img = Image.open(path_hint).resize(
                    (tw, th), Image.Resampling.LANCZOS,
                )
                scaled = ImageTk.PhotoImage(img)
                if retain_ref:
                    self._image_refs.append(scaled)
                return scaled
            except Exception:
                pass

        if iw > tw or ih > th:
            step = max((iw + tw - 1) // tw, (ih + th - 1) // th, 1)
            scaled = photo.subsample(step, step)
        else:
            scaled = photo

        if retain_ref:
            self._image_refs.append(scaled)
        return scaled

    def _build_ui(self) -> None:
        self._build_topbar()
        self._build_notebook()

    def _build_topbar(self) -> None:
        bar = tk.Frame(self.root, bg=UI_BG_BAR, bd=0, highlightthickness=0)
        bar.pack(fill=tk.X, padx=0, pady=0)

        title_frame = tk.Frame(bar, bg=UI_BG_BAR)
        title_frame.pack(side=tk.LEFT, padx=(12, 8), pady=8)

        tk.Label(
            title_frame, text="●", bg=UI_BG_BAR, fg=UI_ACCENT,
            font=(UI_FONT, 10),
        ).pack(side=tk.LEFT, padx=(0, 6))

        tk.Label(
            title_frame, text=APP_NAME, bg=UI_BG_BAR, fg=UI_FG,
            font=UI_FONT_LG,
        ).pack(side=tk.LEFT)

        path_frame = tk.Frame(bar, bg=UI_BG_BAR)
        path_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=8)

        self._path_var = tk.StringVar(value="No file open")
        tk.Entry(
            path_frame, textvariable=self._path_var, state="readonly",
            readonlybackground=UI_BG_ELEVATED, **_entry_kwargs(),
        ).pack(fill=tk.X, expand=True)

        right = tk.Frame(bar, bg=UI_BG_BAR)
        right.pack(side=tk.RIGHT, padx=(8, 12), pady=8)

        tk.Label(
            right, text=f"v{VERSION}", bg=UI_BG_ELEVATED, fg=UI_FG_MUTED,
            font=UI_FONT_SM, padx=8, pady=2,
        ).pack(side=tk.LEFT, padx=(0, 10))

        RoundedButton(
            right, text="Open", command=self._open_file,
            bg=UI_BG_BAR, variant="primary", padx=14,
        ).pack(side=tk.LEFT)

    def _build_notebook(self) -> None:
        self._nb = ttk.Notebook(self.root, style="Modern.TNotebook")
        self._nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=(6, 10))

        editor_frame = tk.Frame(self._nb, bg=UI_BG, padx=2, pady=6)
        sheet_frame = tk.Frame(self._nb, bg=UI_BG, padx=2, pady=6)
        preview_frame = tk.Frame(self._nb, bg=UI_BG, padx=2, pady=6)
        self._nb.add(editor_frame, text="Editor")
        self._nb.add(sheet_frame, text="Spreadsheet")
        self._nb.add(preview_frame, text="Preview")

        self._build_editor(editor_frame)
        self._build_spreadsheet(sheet_frame)
        self._preview_frame = preview_frame
        self._nb.bind("<<NotebookTabChanged>>", self._on_tab_change)

    def _deferred_startup(self) -> None:
        self._set_window_icon()
        self._dragdrop_raw = self._load_photo("dragdrop.png")
        if self._dragdrop_raw is not None and self._dragdrop_panel is not None:
            self._update_dragdrop_hint()

    def _build_editor(self, parent: tk.Frame) -> None:
        nav = tk.Frame(parent, bg=UI_BG_ELEVATED, bd=0, highlightthickness=0)
        nav.pack(fill=tk.X, padx=0, pady=(0, 8))

        tk.Label(nav, text="Weapon", bg=UI_BG_ELEVATED, fg=UI_FG_LABEL,
                 font=UI_FONT_LABEL).pack(side=tk.LEFT, padx=(12, 4), pady=8)

        self._goto_var = tk.StringVar()
        self._goto_cb = ttk.Combobox(
            nav, textvariable=self._goto_var,
            state="readonly", width=28, style="Modern.TCombobox",
        )
        self._goto_cb.pack(side=tk.LEFT, padx=2, pady=8)
        self._goto_cb.bind("<<ComboboxSelected>>", self._on_goto_weapon)

        self._row_status_var = tk.StringVar(value="No row selected")
        tk.Label(nav, textvariable=self._row_status_var, bg=UI_BG_ELEVATED,
                 font=UI_FONT_SM, fg=UI_FG_MUTED).pack(
                     side=tk.RIGHT, padx=12, pady=8)

        editor_area = tk.Frame(parent, bd=0, highlightthickness=0, bg=UI_BG)
        editor_area.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        form_card = tk.Frame(
            editor_area, bg=UI_BG_ELEVATED, bd=0,
            highlightthickness=1, highlightbackground=UI_BORDER,
        )
        form_card.pack(fill=tk.X, anchor="nw", padx=0, pady=(0, 4))

        form = tk.Frame(form_card, bd=0, highlightthickness=0,
                        padx=12, pady=10, bg=UI_BG_ELEVATED)
        form.pack(fill=tk.X, anchor="nw")

        col_mins = _editor_column_minsizes()
        for c in range(4):
            form.columnconfigure(c, weight=1, minsize=col_mins[c])

        for (field, row, col, span, wtype) in EDITOR_LAYOUT:
            tk.Label(form, text=_field_label(field),
                     font=UI_FONT_LABEL, anchor="w", bd=0,
                     bg=UI_BG_ELEVATED, fg=UI_FG_LABEL).grid(
                         row=row * 2, column=col, columnspan=span,
                         sticky="nw", padx=(4, 2), pady=(8, 2))

            var = tk.StringVar()
            self.fvars[field] = var
            var.trace_add("write", lambda *_a: self._on_field_changed())

            width = _editor_widget_width(
                field, wtype, self._weaponvo_values, self._class_values,
            )

            if wtype == "bool":
                w = ttk.Combobox(form, textvariable=var,
                                 values=BOOL_OPTIONS, state="readonly",
                                 width=width, font=UI_FONT_SM,
                                 style="Modern.TCombobox")
            elif wtype == "weaponvo":
                w = ttk.Combobox(form, textvariable=var,
                                 values=self._weaponvo_values,
                                 state="readonly", width=width,
                                 font=UI_FONT_SM,
                                 style="Modern.TCombobox")
            elif wtype == "class":
                w = ttk.Combobox(form, textvariable=var,
                                 values=self._class_values,
                                 state="readonly", width=width,
                                 font=UI_FONT_SM,
                                 style="Modern.TCombobox")
            else:
                w = tk.Entry(form, textvariable=var, width=width, **_entry_kwargs())

            w.grid(row=row * 2 + 1, column=col, columnspan=span,
                   sticky="ew", padx=(4, 2), pady=(0, 4))
            self.fwidgets[field] = w

        self._dragdrop_panel: Optional[tk.Frame] = None
        self._dragdrop_label: Optional[tk.Label] = None
        self._dragdrop_text_label: Optional[tk.Label] = None
        self._dragdrop_panel = tk.Frame(form, bg=UI_BG_ELEVATED, bd=0)
        self._dragdrop_panel.grid(
            row=4, column=3, rowspan=8,
            sticky="nsew", padx=(8, 4), pady=0,
        )

        self._dragdrop_label = tk.Label(
            self._dragdrop_panel, bg=UI_BG_ELEVATED, bd=0, anchor="center",
        )
        self._dragdrop_label.pack(side=tk.TOP, fill=tk.X)

        self._dragdrop_text_label = tk.Label(
            self._dragdrop_panel,
            text="Drag and Drop your .CSV to edit!",
            bg=UI_BG_ELEVATED,
            fg=UI_FG_MUTED,
            font=UI_FONT_SM,
            anchor="center",
            justify="center",
        )
        self._dragdrop_text_label.pack(side=tk.TOP, pady=(6, 0))

        form.bind("<Configure>", self._on_editor_form_resize)

        tk.Frame(editor_area, bg=UI_BORDER, height=1).pack(
            fill=tk.X, side=tk.BOTTOM, pady=(8, 4))

        tk.Label(
            editor_area,
            text=CREDIT_LINE,
            bg=UI_BG,
            fg=UI_FG_MUTED,
            font=UI_FONT_SM,
            anchor="center",
        ).pack(fill=tk.X, side=tk.BOTTOM, pady=(0, 4))

        btn_bar = tk.Frame(parent, bg=UI_BG, bd=0, highlightthickness=0)
        btn_bar.pack(fill=tk.X, side=tk.BOTTOM, padx=0, pady=(4, 0))

        btn_group = tk.Frame(btn_bar, bg=UI_BG)
        btn_group.pack(anchor="center")

        for label, cmd, tip, variant in [
            ("New", self._editor_new, "Clear form", "default"),
            ("Apply", self._apply_editor, "Apply to row", "default"),
            ("Section Break", self._insert_break_above,
             "Blank line above row", "default"),
            ("Comment Out", self._toggle_comment, "Toggle //", "default"),
            ("Delete", self._delete_row, None, "default"),
            ("Add", self._add_row, "New row from form", "default"),
            ("Copy", self._copy_row, "Duplicate row", "default"),
            ("Save", self._save_file, None, "primary"),
        ]:
            btn = RoundedButton(
                btn_group, text=label, command=cmd, bg=UI_BG,
                variant=variant, padx=12,
            )
            btn.pack(side=tk.LEFT, padx=4, pady=6)
            if tip:
                ToolTip(btn, tip)

    def _on_editor_form_resize(self, _event: tk.Event) -> None:
        self._update_dragdrop_hint()

    def _update_dragdrop_hint(self) -> None:
        if (self._dragdrop_raw is None or self._dragdrop_label is None
                or self._dragdrop_panel is None
                or self._dragdrop_text_label is None):
            return
        try:
            self._dragdrop_panel.update_idletasks()
            pw = max(self._dragdrop_panel.winfo_width(), 1)
            ph = max(self._dragdrop_panel.winfo_height(), 1)

            wrap = max(80, pw - 8)
            self._dragdrop_text_label.config(wraplength=wrap)
            self._dragdrop_text_label.update_idletasks()
            text_h = self._dragdrop_text_label.winfo_reqheight()

            img_w = pw
            img_h = max(1, ph - text_h - 4)
            if DRAGDROP_MAX_WIDTH > 0:
                img_w = min(img_w, DRAGDROP_MAX_WIDTH)
            if DRAGDROP_MAX_HEIGHT > 0:
                img_h = min(img_h, DRAGDROP_MAX_HEIGHT)

            size = (img_w, img_h)
            if size == self._dragdrop_last_size and self._dragdrop_img is not None:
                return

            self._dragdrop_img = self._scale_photo(
                self._dragdrop_raw, img_w, img_h, retain_ref=False,
            )
            self._dragdrop_last_size = size
            self._dragdrop_label.config(image=self._dragdrop_img)
        except tk.TclError:
            pass

    def _build_spreadsheet(self, parent: tk.Frame) -> None:
        filter_bar = tk.Frame(
            parent, bg=UI_BG_ELEVATED, bd=0,
            highlightthickness=1, highlightbackground=UI_BORDER,
        )
        filter_bar.pack(fill=tk.X, pady=(0, 8))

        tk.Label(filter_bar, text="Search", bg=UI_BG_ELEVATED, fg=UI_FG_LABEL,
                 font=UI_FONT_LABEL).pack(side=tk.LEFT, padx=(12, 6), pady=8)

        self._filter_var = tk.StringVar()
        filter_entry = tk.Entry(
            filter_bar, textvariable=self._filter_var, **_entry_kwargs(),
        )
        filter_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 12), pady=8)
        self._filter_var.trace_add("write", lambda *_a: self._on_filter_changed())

        frame = tk.Frame(
            parent, bg=UI_BG_ELEVATED, bd=0,
            highlightthickness=1, highlightbackground=UI_BORDER,
        )
        frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        vsb = ttk.Scrollbar(frame, orient=tk.VERTICAL, style="Modern.Vertical.TScrollbar")
        hsb = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, style="Modern.Horizontal.TScrollbar")

        self.tree = ttk.Treeview(
            frame, selectmode="browse", style="Modern.Treeview",
            yscrollcommand=vsb.set, xscrollcommand=hsb.set,
        )
        self.tree.tag_configure("stripe", background=UI_BG_ELEVATED)
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)

        vsb.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 1), pady=1)
        hsb.pack(side=tk.BOTTOM, fill=tk.X, padx=1, pady=(0, 1))
        self.tree.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.tree.bind("<Double-1>", self._on_tree_double_click)

    def _build_preview(self, parent: tk.Frame) -> None:
        outer = tk.Frame(parent, bg=UI_BG)
        outer.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        header = tk.Frame(
            outer, bg=UI_BG_ELEVATED, bd=0,
            highlightthickness=1, highlightbackground=UI_BORDER,
        )
        header.pack(fill=tk.X, pady=(0, 8))

        tk.Label(
            header,
            text="CSV Preview",
            bg=UI_BG_ELEVATED,
            fg=UI_FG,
            font=UI_FONT_LABEL,
            anchor="w",
        ).pack(side=tk.LEFT, padx=12, pady=8)

        tk.Label(
            header,
            text="read-only (as saved to disk)",
            bg=UI_BG_ELEVATED,
            fg=UI_FG_MUTED,
            font=UI_FONT_SM,
            anchor="w",
        ).pack(side=tk.LEFT, padx=(0, 8), pady=8)

        self._preview_status_var = tk.StringVar(value="")
        tk.Label(
            header,
            textvariable=self._preview_status_var,
            bg=UI_BG_ELEVATED,
            fg=UI_ACCENT,
            font=UI_FONT_SM,
            anchor="e",
        ).pack(side=tk.RIGHT, padx=12, pady=8)

        body = tk.Frame(
            outer, bg=UI_BG_ELEVATED, bd=0,
            highlightthickness=1, highlightbackground=UI_BORDER,
        )
        body.pack(fill=tk.BOTH, expand=True)

        vsb = ttk.Scrollbar(body, orient=tk.VERTICAL, style="Modern.Vertical.TScrollbar")
        hsb = ttk.Scrollbar(body, orient=tk.HORIZONTAL, style="Modern.Horizontal.TScrollbar")

        text_opts = dict(
            wrap=tk.NONE,
            font=PREVIEW_FONT,
            relief=tk.FLAT,
            borderwidth=0,
            highlightthickness=0,
            insertwidth=0,
            selectbackground=PREVIEW_SELECT,
            selectforeground=UI_FG,
            inactiveselectbackground=PREVIEW_SELECT,
            cursor="arrow",
            exportselection=False,
        )

        self._preview_gutter = tk.Text(
            body,
            width=5,
            padx=6,
            pady=4,
            bg=PREVIEW_GUTTER_BG,
            fg=UI_FG_MUTED,
            state=tk.DISABLED,
            **text_opts,
        )
        self._preview_text = tk.Text(
            body,
            bg=PREVIEW_BG,
            fg=UI_FG,
            state=tk.DISABLED,
            xscrollcommand=hsb.set,
            **text_opts,
        )
        self._preview_text.tag_configure("changed", background=PREVIEW_CHANGED_BG,
                                         foreground="#fcd34d")

        def _on_preview_yscroll(first, last) -> None:
            self._preview_gutter.yview_moveto(first)
            vsb.set(first, last)

        self._preview_text.configure(yscrollcommand=_on_preview_yscroll)
        vsb.config(command=self._preview_text.yview)
        hsb.config(command=self._preview_text.xview)

        self._preview_gutter.pack(side=tk.LEFT, fill=tk.Y)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self._preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _bind_menu(self) -> None:
        menubar = tk.Menu(
            self.root, tearoff=0,
            bg=UI_BG_BAR, fg=UI_FG,
            activebackground=UI_ACCENT, activeforeground=UI_FG,
            borderwidth=0,
        )

        file_menu = tk.Menu(
            menubar, tearoff=0,
            bg=UI_BG_BAR, fg=UI_FG,
            activebackground=UI_ACCENT, activeforeground=UI_FG,
        )
        file_menu.add_command(label="Open…", command=self._open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self._save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As…", command=self._save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_exit)
        menubar.add_cascade(label="File", menu=file_menu)

        edit_menu = tk.Menu(
            menubar, tearoff=0,
            bg=UI_BG_BAR, fg=UI_FG,
            activebackground=UI_ACCENT, activeforeground=UI_FG,
        )
        edit_menu.add_command(label="New Row", command=self._editor_new)
        edit_menu.add_command(label="Apply Changes", command=self._apply_editor)
        edit_menu.add_command(label="Insert Section Break Above", command=self._insert_break_above)
        edit_menu.add_command(label="Add Row", command=self._add_row)
        edit_menu.add_command(label="Copy Row", command=self._copy_row)
        edit_menu.add_command(label="Delete Row", command=self._delete_row)
        edit_menu.add_command(label="Comment Out", command=self._toggle_comment)
        edit_menu.add_separator()
        edit_menu.add_command(label="Undo", command=self._undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self._redo, accelerator="Ctrl+Y")
        menubar.add_cascade(label="Edit", menu=edit_menu)

        self.root.config(menu=menubar)
        self.root.bind_all("<Control-o>", lambda _e: self._open_file())
        self.root.bind_all("<Control-s>", lambda _e: self._save_file())
        self.root.bind_all("<Control-z>", lambda _e: self._undo())
        self.root.bind_all("<Control-y>", lambda _e: self._redo())
        self.root.protocol("WM_DELETE_WINDOW", self._on_exit)

    def _setup_drag_and_drop(self) -> None:
        try:
            from tkinterdnd2 import DND_FILES
        except ImportError:
            return

        def on_drop(event) -> None:
            raw = event.data.strip()
            if raw.startswith("{") and raw.endswith("}"):
                raw = raw[1:-1]
            path = raw.split()[0] if raw else ""
            if not path.lower().endswith(".csv"):
                return
            if not self._confirm_discard_unsaved():
                return
            self._load_file(path)

        try:
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind("<<Drop>>", on_drop)
        except Exception:
            pass

    def _set_dirty(self, dirty: bool) -> None:
        self._dirty = dirty
        base = APP_NAME
        if self.filepath:
            base += f" - {os.path.basename(self.filepath)}"
        if dirty:
            base += " *"
        self.root.title(base)

    def _on_field_changed(self) -> None:
        if self._suppress_events:
            return
        if self.cur_idx is not None or any(v.get() for v in self.fvars.values()):
            self._set_dirty(True)

    def _update_row_status(self) -> None:
        if self.cur_idx is None:
            self._row_status_var.set("New row (not saved yet)")
        else:
            name = self.rows[self.cur_idx].get("weapon_name", "")
            blanks = self.rows[self.cur_idx].get("__blanks_before__", 0)
            extra = f", {blanks} blank line(s) above" if blanks else ""
            self._row_status_var.set(f"Editing row {self.cur_idx + 1}: {name}{extra}")

    def _merge_enum_values_from_data(self) -> None:
        vo: Set[str] = set(self._weaponvo_values)
        cls: Set[str] = set(self._class_values)
        for row in self.rows:
            v = row.get("weaponVO", "").strip()
            if v:
                vo.add(v)
            c = row.get("class", "").strip()
            if c:
                cls.add(c)
        self._weaponvo_values = [""] + sorted(x for x in vo if x)
        self._class_values = [""] + sorted(x for x in cls if x)

        wvo = self.fwidgets.get("weaponVO")
        if isinstance(wvo, ttk.Combobox):
            wvo["values"] = self._weaponvo_values
        cw = self.fwidgets.get("class")
        if isinstance(cw, ttk.Combobox):
            cw["values"] = self._class_values

    def _push_undo(self) -> None:
        self._undo_stack.append(copy.deepcopy(self.rows))
        if len(self._undo_stack) > UNDO_LIMIT:
            self._undo_stack.pop(0)
        self._redo_stack.clear()

    def _restore_rows(self, rows: List[dict]) -> None:
        keep_name = ""
        if self.cur_idx is not None and 0 <= self.cur_idx < len(self.rows):
            keep_name = self.rows[self.cur_idx].get("weapon_name", "").strip()

        self.rows = rows
        self._merge_enum_values_from_data()
        self.cur_idx = None
        if keep_name:
            for i, row in enumerate(self.rows):
                if row.get("weapon_name", "").strip() == keep_name:
                    self.cur_idx = i
                    break
        if self.cur_idx is None and self.rows:
            self.cur_idx = 0

        if self.cur_idx is not None:
            self._load_row_to_editor(self.cur_idx)
        else:
            self._editor_new()
        self._refresh_goto_dropdown()
        self._refresh_tree(keep_idx=self.cur_idx)
        self._set_dirty(self._render_csv_text() != self._preview_baseline)
        if self._preview_active():
            self._refresh_preview()

    def _undo(self) -> None:
        if not self._undo_stack:
            return
        if self.cur_idx is not None:
            self._apply_editor_to_row_silent(self.cur_idx)
        self._redo_stack.append(copy.deepcopy(self.rows))
        self._restore_rows(self._undo_stack.pop())

    def _redo(self) -> None:
        if not self._redo_stack:
            return
        if self.cur_idx is not None:
            self._apply_editor_to_row_silent(self.cur_idx)
        self._undo_stack.append(copy.deepcopy(self.rows))
        self._restore_rows(self._redo_stack.pop())

    def _on_filter_changed(self) -> None:
        self._refresh_tree(keep_idx=self.cur_idx)

    def _row_matches_filter(self, row: dict, query: str) -> bool:
        if not query:
            return True
        for hdr in self.headers:
            if query in str(row.get(hdr, "")).lower():
                return True
        return False

    def _spreadsheet_active(self) -> bool:
        try:
            return self._nb.index(self._nb.select()) == 1
        except tk.TclError:
            return False

    def _tree_font(self) -> tkfont.Font:
        try:
            font_spec = ttk.Style().lookup("Modern.Treeview", "font")
            if font_spec:
                return tkfont.Font(font=font_spec)
        except tk.TclError:
            pass
        return tkfont.Font(family=UI_FONT, size=9)

    def _auto_column_widths(self) -> Dict[str, int]:
        font = self._tree_font()
        widths: Dict[str, int] = {}

        for hdr in self.headers:
            texts = [hdr, hdr.replace("_", " ")]
            for row in self.rows:
                val = str(row.get(hdr, "")).strip()
                if val:
                    texts.append(val)

            content_px = max(font.measure(text) for text in texts)
            floor = COL_WIDTHS.get(hdr, font.measure(hdr.replace("_", " ")) + COL_WIDTH_PAD)
            width = min(max(floor, content_px + COL_WIDTH_PAD), COL_WIDTH_MAX)
            widths[hdr] = width

        return widths

    def _setup_tree_columns(self) -> None:
        self._tree_col_ids = [f"col{i}" for i in range(len(self.headers))]
        self.tree["columns"] = self._tree_col_ids
        self.tree["show"] = "headings"
        widths = self._auto_column_widths()

        for i, hdr in enumerate(self.headers):
            cid = self._tree_col_ids[i]
            col_w = widths[hdr]
            self.tree.heading(
                cid, text=hdr.replace("_", " "),
                command=lambda c=hdr: self._sort_rows(c, False),
            )
            self.tree.column(
                cid, width=col_w, minwidth=col_w, stretch=False,
            )

    def _refresh_tree(self, keep_idx: Optional[int] = None) -> None:
        self._tree_keep_idx = keep_idx
        if self._spreadsheet_active():
            self.root.after_idle(self._refresh_tree_now)

    def _refresh_tree_now(self) -> None:
        if not self.headers or not self._tree_col_ids:
            return

        sel = self._tree_keep_idx if self._tree_keep_idx is not None else self.cur_idx

        children = self.tree.get_children()
        if children:
            self.tree.delete(*children)

        self._suppress_events = True
        try:
            query = self._filter_var.get().strip().lower()
            visible = 0
            for i, row in enumerate(self.rows):
                if not self._row_matches_filter(row, query):
                    continue
                values = [str(row.get(c, "")) for c in self.headers]
                tags = ("stripe",) if visible % 2 else ()
                visible += 1
                self.tree.insert("", tk.END, iid=str(i), values=values, tags=tags)

            if sel is not None and 0 <= sel < len(self.rows):
                iid = str(sel)
                if self.tree.exists(iid):
                    self.tree.selection_set(iid)
                    try:
                        self.tree.see(iid)
                    except tk.TclError:
                        pass
        except tk.TclError as exc:
            messagebox.showerror(
                "Spreadsheet Error",
                f"Could not refresh the spreadsheet view:\n{exc}",
            )
        finally:
            self._suppress_events = False

    def _refresh_goto_dropdown(self) -> None:
        names = [r.get("weapon_name", "") for r in self.rows]
        self._suppress_events = True
        try:
            self._goto_cb["values"] = names
            if self.cur_idx is not None and 0 <= self.cur_idx < len(names):
                self._goto_var.set(names[self.cur_idx])
            else:
                self._goto_var.set("")
        finally:
            self._suppress_events = False

    def _load_row_to_editor(self, idx: int) -> None:
        if not (0 <= idx < len(self.rows)):
            return

        self._suppress_events = True
        try:
            self.cur_idx = idx
            row = self.rows[idx]
            for field, var in self.fvars.items():
                var.set(row.get(field, ""))
            self._goto_var.set(row.get("weapon_name", ""))
            self._update_row_status()
        finally:
            self._suppress_events = False

    def _apply_editor_to_row_silent(self, idx: int) -> None:
        if not (0 <= idx < len(self.rows)):
            return

        new_name = self.fvars["weapon_name"].get().strip()
        if not new_name:
            return

        for i, row in enumerate(self.rows):
            if i != idx and row.get("weapon_name", "").strip() == new_name:
                return

        row = self.rows[idx]
        for field, var in self.fvars.items():
            row[field] = var.get().strip() if field == "weapon_name" else var.get()

    def _write_editor_to_row_data(self, idx: int) -> bool:
        if not (0 <= idx < len(self.rows)):
            return False

        new_name = self.fvars["weapon_name"].get().strip()
        if not new_name:
            messagebox.showwarning("Missing Name", "weapon_name cannot be empty.")
            return False

        for i, row in enumerate(self.rows):
            if i != idx and row.get("weapon_name", "").strip() == new_name:
                messagebox.showwarning(
                    "Duplicate Name",
                    f"'{new_name}' already exists on row {i + 1}.",
                )
                return False

        self._apply_editor_to_row_silent(idx)
        return True

    def _save_editor_to_row(self, idx: int) -> bool:
        if not self._write_editor_to_row_data(idx):
            return False

        self._refresh_goto_dropdown()
        self._refresh_tree(keep_idx=idx)
        self._update_row_status()
        return True

    def _commit_editor(self) -> bool:
        if self.cur_idx is None:
            return False
        self._push_undo()
        if self._save_editor_to_row(self.cur_idx):
            self._set_dirty(True)
            return True
        self._undo_stack.pop()
        return False

    def _new_row_dict(self) -> dict:
        row: dict = {"__commented__": False, "__blanks_before__": 0}
        for h in self.headers:
            row.setdefault(h, "")
        return row

    def _open_file(self) -> None:
        if not self._confirm_discard_unsaved():
            return
        path = filedialog.askopenfilename(
            title="Open level_common_weapon.csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if path:
            self._load_file(path)

    def _load_file(self, path: str) -> None:
        try:
            with open(path, newline="", encoding="utf-8-sig") as fh:
                lines = list(csv.reader(fh))
        except Exception as exc:
            messagebox.showerror("Open Error", str(exc))
            return

        if not lines:
            messagebox.showwarning("Empty File", "The file contains no data.")
            return

        self.headers = lines[0]
        self.rows = []
        self._sort_col = None
        self._sort_reverse = False
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._filter_var.set("")

        blanks_before = 0
        for line in lines[1:]:
            if _is_blank_csv_line(line):
                blanks_before += 1
                continue

            commented = bool(line and line[0].startswith("//"))
            if commented:
                line = [line[0][2:]] + list(line[1:])
            while len(line) < len(self.headers):
                line.append("")
            line = line[: len(self.headers)]

            row = dict(zip(self.headers, line))
            row["__commented__"] = commented
            row["__blanks_before__"] = blanks_before
            blanks_before = 0
            self.rows.append(row)

        self.filepath = path
        self.cur_idx = None
        self._path_var.set(path)
        self._set_dirty(False)

        self._merge_enum_values_from_data()
        self._setup_tree_columns()
        self._refresh_goto_dropdown()

        if self.rows:
            self._load_row_to_editor(0)

        self._preview_baseline = self._render_csv_text()

    def _render_csv_text(self) -> str:
        if not self.headers:
            return ""

        buf = io.StringIO()
        writer = csv.writer(buf, lineterminator="\n")
        writer.writerow(self.headers)
        for row in self.rows:
            for _ in range(row.get("__blanks_before__", 0)):
                writer.writerow([])
            vals = [row.get(h, "") for h in self.headers]
            if row.get("__commented__"):
                vals[0] = "//" + vals[0]
            writer.writerow(vals)

        text = buf.getvalue()
        if text and not text.endswith("\n"):
            text += "\n"
        return text

    def _ensure_preview_built(self) -> None:
        if self._preview_built:
            return
        self._build_preview(self._preview_frame)
        self._preview_built = True

    def _preview_active(self) -> bool:
        try:
            return self._nb.index(self._nb.select()) == 2
        except tk.TclError:
            return False

    def _changed_preview_lines(self, current: str, baseline: str) -> Set[int]:
        current_lines = current.splitlines()
        baseline_lines = baseline.splitlines()
        changed: Set[int] = set()
        total = max(len(current_lines), len(baseline_lines))
        for i in range(total):
            cur = current_lines[i] if i < len(current_lines) else ""
            base = baseline_lines[i] if i < len(baseline_lines) else ""
            if cur != base:
                changed.add(i + 1)
        return changed

    def _refresh_preview(self) -> None:
        if not self._preview_built:
            return

        current = self._render_csv_text()
        if not self.headers:
            display = "No CSV loaded.\n\nOpen a file to preview its contents here."
            changed_lines: Set[int] = set()
            status = ""
        else:
            display = current if current else "(empty file)\n"
            changed_lines = (
                self._changed_preview_lines(current, self._preview_baseline)
                if self._dirty else set()
            )
            if self._dirty and changed_lines:
                status = (
                    f"{len(changed_lines)} line(s) changed since last save"
                )
            elif self._dirty:
                status = "Unsaved changes"
            else:
                status = "Matches last saved version"

        lines = display.splitlines(keepends=True)
        if not lines and display:
            lines = [display]

        gutter = self._preview_gutter
        body = self._preview_text

        gutter.config(state=tk.NORMAL)
        body.config(state=tk.NORMAL)
        gutter.delete("1.0", tk.END)
        body.delete("1.0", tk.END)

        for i, chunk in enumerate(lines, start=1):
            gutter.insert(tk.END, f"{i:>4}\n")
            if i in changed_lines:
                body.insert(tk.END, chunk, "changed")
            else:
                body.insert(tk.END, chunk)

        gutter.config(state=tk.DISABLED)
        body.config(state=tk.DISABLED)
        self._preview_status_var.set(status)

    def _enter_preview_tab(self) -> None:
        if not self._preview_active():
            return
        self._ensure_preview_built()
        if self.cur_idx is not None:
            self._apply_editor_to_row_silent(self.cur_idx)
        self._refresh_preview()

    def _save_file(self) -> None:
        if self.cur_idx is not None:
            if not self._save_editor_to_row(self.cur_idx):
                return
        elif any(v.get().strip() for v in self.fvars.values()):
            messagebox.showwarning(
                "Unsaved New Row",
                "Form has data but no row is selected.\nClick Add first.",
            )
            return

        if not self.filepath:
            self._save_file_as()
            return

        self._write_csv(self.filepath)

    def _save_file_as(self) -> None:
        if self.cur_idx is not None:
            if not self._save_editor_to_row(self.cur_idx):
                return
        elif any(v.get().strip() for v in self.fvars.values()):
            messagebox.showwarning(
                "Unsaved New Row",
                "Form has data but no row is selected.",
            )
            return

        path = filedialog.asksaveasfilename(
            title="Save CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not path:
            return
        self.filepath = path
        self._path_var.set(path)
        self._write_csv(path)

    def _write_csv(self, path: str) -> None:
        try:
            text = self._render_csv_text()
            with open(path, "w", newline="", encoding="utf-8") as fh:
                fh.write(text)
            self._preview_baseline = text
            self._set_dirty(False)
            if self._preview_active():
                self._refresh_preview()
            messagebox.showinfo("Saved", f"File saved:\n{path}")
        except Exception as exc:
            messagebox.showerror("Save Error", str(exc))

    def _confirm_discard_unsaved(self) -> bool:
        if not self._dirty:
            return True
        return messagebox.askyesno(
            "Unsaved Changes",
            "Discard unsaved changes?",
            icon="warning",
        )

    def _on_exit(self) -> None:
        if self._confirm_discard_unsaved():
            self.root.destroy()

    def _editor_new(self) -> None:
        if self.cur_idx is not None:
            self._save_editor_to_row(self.cur_idx)
        self._suppress_events = True
        try:
            for var in self.fvars.values():
                var.set("")
            self.cur_idx = None
            self._goto_var.set("")
            self._update_row_status()
        finally:
            self._suppress_events = False

    def _apply_editor(self) -> None:
        if self.cur_idx is None:
            messagebox.showinfo("New Row", "No row selected.")
            return
        self._commit_editor()

    def _insert_break_above(self) -> None:
        if self.cur_idx is None:
            messagebox.showwarning("No Selection", "Select a weapon first.")
            return
        if not self._save_editor_to_row(self.cur_idx):
            return
        self._push_undo()
        row = self.rows[self.cur_idx]
        row["__blanks_before__"] = row.get("__blanks_before__", 0) + 1
        self._set_dirty(True)
        self._refresh_tree(keep_idx=self.cur_idx)
        self._update_row_status()

    def _on_goto_weapon(self, _event=None) -> None:
        if self._suppress_events:
            return
        name = self._goto_var.get().strip()
        if not name:
            return

        if self.cur_idx is not None:
            if not self._save_editor_to_row(self.cur_idx):
                if 0 <= self.cur_idx < len(self.rows):
                    self._goto_var.set(self.rows[self.cur_idx].get("weapon_name", ""))
                return

        for i, row in enumerate(self.rows):
            if row.get("weapon_name", "").strip() == name:
                self._load_row_to_editor(i)
                try:
                    self.tree.selection_set(str(i))
                    self.tree.see(str(i))
                except tk.TclError:
                    pass
                return

    def _toggle_comment(self) -> None:
        if self.cur_idx is None:
            messagebox.showwarning("No Selection", "Select a weapon first.")
            return
        self._apply_editor_to_row_silent(self.cur_idx)
        self._push_undo()
        row = self.rows[self.cur_idx]
        row["__commented__"] = not row.get("__commented__", False)
        self._set_dirty(True)
        self._refresh_tree(keep_idx=self.cur_idx)

    def _delete_row(self) -> None:
        if self.cur_idx is None:
            messagebox.showwarning("No Selection", "Select a weapon first.")
            return
        name = self.rows[self.cur_idx].get("weapon_name", "<unknown>")
        if not messagebox.askyesno("Confirm Delete", f"Delete '{name}'?"):
            return

        self._apply_editor_to_row_silent(self.cur_idx)
        self._push_undo()

        deleted = self.rows.pop(self.cur_idx)
        deleted_blanks = deleted.get("__blanks_before__", 0)

        if self.cur_idx < len(self.rows):
            nxt = self.rows[self.cur_idx]
            nxt["__blanks_before__"] = deleted_blanks + nxt.get("__blanks_before__", 0)
        elif self.rows:
            self.rows[-1]["__blanks_before__"] = (
                self.rows[-1].get("__blanks_before__", 0) + deleted_blanks
            )

        self.cur_idx = None
        self._editor_new()
        self._set_dirty(True)
        self._refresh_tree()
        self._refresh_goto_dropdown()

    def _add_row(self) -> None:
        name = self.fvars["weapon_name"].get().strip()
        if not name:
            messagebox.showwarning("Missing Name", "weapon_name cannot be empty.")
            return
        if any(r.get("weapon_name", "").strip() == name for r in self.rows):
            messagebox.showwarning("Duplicate", f"'{name}' already exists.")
            return

        if self.cur_idx is not None:
            self._save_editor_to_row(self.cur_idx)

        self._push_undo()
        new_row = self._new_row_dict()
        for field, var in self.fvars.items():
            new_row[field] = var.get()

        self.rows.append(new_row)
        self.cur_idx = len(self.rows) - 1
        self._set_dirty(True)
        self._merge_enum_values_from_data()
        self._refresh_tree(keep_idx=self.cur_idx)
        self._refresh_goto_dropdown()
        self._update_row_status()

    def _copy_row(self) -> None:
        if self.cur_idx is None:
            messagebox.showwarning("No Selection", "Select a weapon first.")
            return
        if not self._save_editor_to_row(self.cur_idx):
            return

        src = copy.deepcopy(self.rows[self.cur_idx])
        old_name = src.get("weapon_name", "")
        src["__commented__"] = False
        src["__blanks_before__"] = 0

        dlg = tk.Toplevel(self.root)
        dlg.title("Copy Weapon")
        dlg.geometry("380x160")
        dlg.resizable(False, False)
        dlg.transient(self.root)
        dlg.grab_set()
        dlg.configure(bg=UI_BG)

        card = tk.Frame(
            dlg, bg=UI_BG_ELEVATED, highlightthickness=1,
            highlightbackground=UI_BORDER, padx=20, pady=16,
        )
        card.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        tk.Label(
            card, text="New weapon name", bg=UI_BG_ELEVATED,
            fg=UI_FG_LABEL, font=UI_FONT_LABEL,
        ).pack(anchor="w", pady=(0, 6))
        nvar = tk.StringVar(value=old_name + "_copy")
        ent = tk.Entry(card, textvariable=nvar, width=36, **_entry_kwargs())
        ent.pack(fill=tk.X, pady=(0, 4))
        ent.select_range(0, tk.END)
        ent.focus_set()

        def do_copy() -> None:
            new_name = nvar.get().strip()
            if not new_name:
                messagebox.showwarning("Invalid", "Name cannot be empty.", parent=dlg)
                return
            if any(r.get("weapon_name", "").strip() == new_name for r in self.rows):
                messagebox.showwarning("Duplicate", f"'{new_name}' already exists.", parent=dlg)
                return

            self._push_undo()
            src["weapon_name"] = new_name
            up = src.get("upgrade_name", "")
            for suffix in ("_upgraded", "_up", "_rdw_up"):
                if up == old_name + suffix:
                    src["upgrade_name"] = new_name + suffix
                    break

            self.rows.append(src)
            self.cur_idx = len(self.rows) - 1
            self._set_dirty(True)
            self._load_row_to_editor(self.cur_idx)
            self._merge_enum_values_from_data()
            self._refresh_tree(keep_idx=self.cur_idx)
            self._refresh_goto_dropdown()
            dlg.destroy()

        bf = tk.Frame(card, bg=UI_BG_ELEVATED)
        bf.pack(pady=(12, 0))
        RoundedButton(bf, text="Copy", command=do_copy, bg=UI_BG_ELEVATED,
                      variant="primary", padx=18).pack(side=tk.LEFT, padx=(0, 8))
        RoundedButton(bf, text="Cancel", command=dlg.destroy, bg=UI_BG_ELEVATED,
                      padx=18).pack(side=tk.LEFT)
        ent.bind("<Return>", lambda _e: do_copy())

    def _on_tree_select(self, _event=None) -> None:
        if self._suppress_events:
            return
        sel = self.tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        if self.cur_idx is not None and self.cur_idx != idx:
            prev = self.cur_idx
            new_name = self.fvars["weapon_name"].get().strip()
            if not new_name:
                self._suppress_events = True
                try:
                    self.tree.selection_set(str(prev))
                except tk.TclError:
                    pass
                finally:
                    self._suppress_events = False
                messagebox.showwarning("Missing Name", "weapon_name cannot be empty.")
                return
            for i, row in enumerate(self.rows):
                if i != prev and row.get("weapon_name", "").strip() == new_name:
                    self._suppress_events = True
                    try:
                        self.tree.selection_set(str(prev))
                    except tk.TclError:
                        pass
                    finally:
                        self._suppress_events = False
                    messagebox.showwarning(
                        "Duplicate Name",
                        f"'{new_name}' already exists on row {i + 1}.",
                    )
                    return
            self._apply_editor_to_row_silent(prev)
        self._load_row_to_editor(idx)

    def _on_tree_double_click(self, _event=None) -> None:
        self._on_tree_select()
        self._nb.select(0)

    def _on_tab_change(self, _event=None) -> None:
        idx = self._nb.index(self._nb.select())
        if idx == 1:
            self.root.after_idle(self._enter_spreadsheet_tab)
        elif idx == 2:
            self.root.after_idle(self._enter_preview_tab)

    def _enter_spreadsheet_tab(self) -> None:
        if not self._spreadsheet_active():
            return
        if self.cur_idx is not None:
            self._apply_editor_to_row_silent(self.cur_idx)
        self._tree_keep_idx = self.cur_idx
        self._refresh_tree_now()

    def _sort_rows(self, col: str, reverse: bool) -> None:
        if any(r.get("__blanks_before__", 0) > 0 for r in self.rows):
            if not messagebox.askyesno(
                "Sort Warning",
                "Blank separator lines will move with their rows.\n\nSort anyway?",
                icon="warning",
            ):
                return

        if self.cur_idx is not None:
            if not self._save_editor_to_row(self.cur_idx):
                return

        self._push_undo()

        if self._sort_col == col:
            reverse = not self._sort_reverse
        self._sort_col = col
        self._sort_reverse = reverse

        def key(row: dict) -> str:
            return str(row.get(col, "")).lower()

        self.rows.sort(key=key, reverse=reverse)
        if self.cur_idx is not None and self.rows:
            name = self.fvars["weapon_name"].get().strip()
            for i, row in enumerate(self.rows):
                if row.get("weapon_name", "").strip() == name:
                    self.cur_idx = i
                    break
        self._set_dirty(True)
        self._refresh_tree(keep_idx=self.cur_idx)


def _apply_dark_theme(style: ttk.Style) -> None:
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure(".", background=UI_BG, foreground=UI_FG, font=UI_FONT_SM)
    style.configure("TFrame", background=UI_BG)
    style.configure("Modern.TNotebook", background=UI_BG, borderwidth=0, tabmargins=[0, 0, 0, 0])
    style.configure(
        "Modern.TNotebook.Tab",
        background=UI_BG_BAR,
        foreground=UI_FG_MUTED,
        padding=[16, 8],
        font=UI_FONT_SM,
        borderwidth=0,
    )
    style.map(
        "Modern.TNotebook.Tab",
        background=[("selected", UI_BG), ("active", UI_BG_ELEVATED)],
        foreground=[("selected", UI_ACCENT), ("active", UI_FG)],
        expand=[("selected", [1, 1, 1, 0])],
    )
    style.configure(
        "Modern.TCombobox",
        fieldbackground=UI_SURFACE,
        background=UI_SURFACE,
        foreground=UI_FG,
        arrowcolor=UI_FG_MUTED,
        bordercolor=UI_BORDER,
        lightcolor=UI_BORDER,
        darkcolor=UI_BORDER,
        insertcolor=UI_FG,
        padding=4,
    )
    style.map(
        "Modern.TCombobox",
        fieldbackground=[("readonly", UI_SURFACE), ("focus", UI_SURFACE_HOVER)],
        foreground=[("readonly", UI_FG)],
        bordercolor=[("focus", UI_ACCENT)],
    )
    style.configure(
        "Modern.Treeview",
        background=UI_BG,
        fieldbackground=UI_BG,
        foreground=UI_FG,
        rowheight=26,
        borderwidth=0,
        font=UI_FONT_SM,
    )
    style.configure(
        "Modern.Treeview.Heading",
        background=UI_BG_BAR,
        foreground=UI_FG_LABEL,
        relief="flat",
        font=UI_FONT_LABEL,
        padding=[8, 6],
    )
    style.map(
        "Modern.Treeview",
        background=[("selected", UI_ACCENT_DIM)],
        foreground=[("selected", UI_FG)],
    )
    style.map(
        "Modern.Treeview.Heading",
        background=[("active", UI_SURFACE_HOVER)],
    )
    style.configure(
        "Modern.Vertical.TScrollbar",
        background=UI_BG_BAR,
        troughcolor=UI_BG,
        bordercolor=UI_BG,
        arrowcolor=UI_FG_MUTED,
        relief=tk.FLAT,
    )
    style.configure(
        "Modern.Horizontal.TScrollbar",
        background=UI_BG_BAR,
        troughcolor=UI_BG,
        bordercolor=UI_BG,
        arrowcolor=UI_FG_MUTED,
        relief=tk.FLAT,
    )
    style.map(
        "Modern.Vertical.TScrollbar",
        background=[("active", UI_SURFACE_HOVER), ("pressed", UI_SURFACE)],
    )
    style.map(
        "Modern.Horizontal.TScrollbar",
        background=[("active", UI_SURFACE_HOVER), ("pressed", UI_SURFACE)],
    )


def main() -> None:
    root: tk.Tk
    try:
        from tkinterdnd2 import TkinterDnD
        root = TkinterDnD.Tk()
    except ImportError:
        root = tk.Tk()

    root.title(APP_NAME)
    root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
    root.configure(bg=UI_BG)
    root.update_idletasks()

    style = ttk.Style()
    _apply_dark_theme(style)

    BO3CSVEditor(root)
    root.mainloop()


if __name__ == "__main__":
    main()
