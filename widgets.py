import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import calendar as _calendar
from constants import (BG_DARK, BG_CARD, BG_CARD2, ACCENT, ACCENT2,
                       TEXT_WHITE, TEXT_MUTED, SUCCESS, WARNING, INFO, ICON_EMOJIS)


class IconPicker(tk.Toplevel):
    """Diálogo modal para elegir un emoji como icono de categoría."""

    COLS = 8

    def __init__(self, parent):
        super().__init__(parent)
        self.withdraw()
        self.selected = None

        self.title("Elige un icono")
        self.configure(bg=BG_CARD)
        self.resizable(False, False)
        self.transient(parent)
        self._build()

        self.update_idletasks()
        pw = parent.winfo_rootx() + parent.winfo_width() // 2 - self.winfo_reqwidth() // 2
        ph = parent.winfo_rooty() + parent.winfo_height() // 2 - self.winfo_reqheight() // 2
        self.geometry(f"+{pw}+{ph}")
        self.deiconify()

        self.bind("<Escape>", lambda _: self.destroy())
        self.wait_visibility()
        self.grab_set()
        self.focus_set()

    def _build(self):
        tk.Label(self, text="Elige un icono para la categoría",
                 bg=BG_CARD, fg=TEXT_WHITE,
                 font=("Segoe UI", 11, "bold"),
                 pady=10, padx=12).pack(fill="x")

        grid_f = tk.Frame(self, bg=BG_CARD, padx=10, pady=4)
        grid_f.pack()

        btn_cfg = dict(bg=BG_CARD2, activebackground=BG_DARK, relief="flat",
                       bd=0, cursor="hand2", font=("Segoe UI", 16), width=2)
        for i, emoji in enumerate(ICON_EMOJIS):
            row, col = divmod(i, self.COLS)
            b = tk.Button(grid_f, text=emoji,
                          command=lambda e=emoji: self._pick(e),
                          **btn_cfg)
            b.grid(row=row, column=col, padx=3, pady=3)

        sep = tk.Frame(self, bg=BG_CARD2, height=1)
        sep.pack(fill="x", padx=10, pady=(6, 2))

        custom_f = tk.Frame(self, bg=BG_CARD, padx=10, pady=8)
        custom_f.pack(fill="x")
        tk.Label(custom_f, text="O escribe tu emoji:", bg=BG_CARD,
                 fg=TEXT_MUTED, font=("Segoe UI", 9)).pack(side="left")
        self._custom_var = tk.StringVar()
        entry = tk.Entry(custom_f, textvariable=self._custom_var,
                         bg=BG_CARD2, fg=TEXT_WHITE, insertbackground=TEXT_WHITE,
                         relief="flat", font=("Segoe UI", 14), width=4)
        entry.pack(side="left", padx=8)
        tk.Button(custom_f, text="Usar",
                  command=self._use_custom,
                  bg=ACCENT, fg="white", relief="flat",
                  font=("Segoe UI", 9, "bold"),
                  padx=8, pady=3, cursor="hand2").pack(side="left")

    def _pick(self, emoji):
        self.selected = emoji
        self.destroy()

    def _use_custom(self):
        val = self._custom_var.get().strip()
        if val:
            self.selected = val
            self.destroy()


# ══════════════════════════════════════════════════════════════════════════════
# WIDGETS CUSTOM
# ══════════════════════════════════════════════════════════════════════════════
class RoundedFrame(tk.Canvas):
    """Canvas que simula un frame con bordes redondeados."""
    def __init__(self, parent, bg=BG_CARD, radius=16, **kwargs):
        super().__init__(parent, bg=parent["bg"] if hasattr(parent,"__getitem__") else BG_DARK,
                         highlightthickness=0, **kwargs)
        self._bg = bg
        self._radius = radius
        self.bind("<Configure>", self._draw)

    def _draw(self, event=None):
        self.delete("bg")
        w, h, r = self.winfo_width(), self.winfo_height(), self._radius
        self._round_rect(2, 2, w-2, h-2, r, fill=self._bg, outline="", tags="bg")
        self.tag_lower("bg")

    def _round_rect(self, x1, y1, x2, y2, r, **kw):
        pts = [
            x1+r, y1,  x2-r, y1,
            x2,   y1,  x2,   y1+r,
            x2,   y2-r,x2,   y2,
            x2-r, y2,  x1+r, y2,
            x1,   y2,  x1,   y2-r,
            x1,   y1+r,x1,   y1,
            x1+r, y1,
        ]
        return self.create_polygon(pts, smooth=True, **kw)


def styled_button(parent, text, command, color=ACCENT, fg=TEXT_WHITE, font_size=11, padx=18, pady=8):
    btn = tk.Button(
        parent, text=text, command=command,
        bg=color, fg=fg, relief="flat", cursor="hand2",
        font=("Segoe UI", font_size, "bold"),
        activebackground=color, activeforeground=fg,
        padx=padx, pady=pady
    )
    btn.bind("<Enter>", lambda e: btn.config(bg=_lighten(color)))
    btn.bind("<Leave>", lambda e: btn.config(bg=color))
    return btn


def _lighten(hex_color: str, factor: float = 0.15) -> str:
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    r = min(255, int(r + (255 - r) * factor))
    g = min(255, int(g + (255 - g) * factor))
    b = min(255, int(b + (255 - b) * factor))
    return f"#{r:02x}{g:02x}{b:02x}"


def label(parent, text, size=11, bold=False, color=TEXT_WHITE, **kw):
    weight = "bold" if bold else "normal"
    return tk.Label(parent, text=text, bg=parent["bg"],
                    fg=color, font=("Segoe UI", size, weight), **kw)


# ══════════════════════════════════════════════════════════════════════════════
# SELECTOR DE FECHA (CALENDARIO DESPLEGABLE)
# ══════════════════════════════════════════════════════════════════════════════

class DatePicker(tk.Toplevel):
    """Calendario desplegable que rellena un Entry con la fecha ISO seleccionada."""

    MESES = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
             "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

    def __init__(self, parent, entry_widget):
        super().__init__(parent)
        self.withdraw()  # ocultar inmediatamente para evitar parpadeo en (0,0)
        self._entry = entry_widget
        try:
            d = datetime.date.fromisoformat(entry_widget.get().strip())
        except ValueError:
            d = datetime.date.today()
        self._year  = d.year
        self._month = d.month

        self.overrideredirect(True)
        self.configure(bg=BG_CARD2,
                       highlightbackground=ACCENT, highlightthickness=1)
        self.transient(parent)
        self._build()

        # Posicionar justo bajo el entry y mostrar ya en la posición correcta
        self.update_idletasks()
        ex = entry_widget.winfo_rootx()
        ey = entry_widget.winfo_rooty() + entry_widget.winfo_height() + 4
        sw = self.winfo_screenwidth()
        pw = self.winfo_reqwidth()
        if ex + pw > sw:
            ex = sw - pw - 4
        self.geometry(f"+{ex}+{ey}")
        self.deiconify()  # mostrar en la posición ya calculada

        self.bind("<Escape>", lambda e: self.destroy())
        self.wait_visibility()
        self.grab_set()
        self.focus_set()

    def _build(self):
        for w in self.winfo_children():
            w.destroy()

        # Cabecera mes/año con flechas de navegación
        hdr = tk.Frame(self, bg=BG_CARD2, padx=6, pady=6)
        hdr.pack(fill="x")
        nav_cfg = dict(bg=BG_CARD2, fg=TEXT_WHITE, relief="flat",
                       font=("Segoe UI", 10, "bold"), cursor="hand2",
                       activebackground=BG_DARK, activeforeground=TEXT_WHITE,
                       bd=0, padx=10, pady=2)
        tk.Button(hdr, text="◀", command=self._prev_month, **nav_cfg).pack(side="left")
        tk.Label(hdr, text=f"{self.MESES[self._month]} {self._year}",
                 bg=BG_CARD2, fg=TEXT_WHITE,
                 font=("Segoe UI", 10, "bold"),
                 width=17, anchor="center").pack(side="left", expand=True)
        tk.Button(hdr, text="▶", command=self._next_month, **nav_cfg).pack(side="right")

        # Nombres de los días de la semana
        dias_f = tk.Frame(self, bg=BG_CARD2, padx=6)
        dias_f.pack(fill="x")
        for col, d in enumerate(["Lu", "Ma", "Mi", "Ju", "Vi", "Sá", "Do"]):
            fg = ACCENT if col >= 5 else TEXT_MUTED
            tk.Label(dias_f, text=d, bg=BG_CARD2, fg=fg,
                     font=("Segoe UI", 8, "bold"),
                     width=3, anchor="center").grid(row=0, column=col, padx=2, pady=(0, 2))

        # Grid de días
        grid_f = tk.Frame(self, bg=BG_CARD2, padx=6, pady=4)
        grid_f.pack()
        today = datetime.date.today()
        try:
            sel = datetime.date.fromisoformat(self._entry.get().strip())
        except ValueError:
            sel = None

        for row_i, week in enumerate(_calendar.monthcalendar(self._year, self._month)):
            for col_i, day in enumerate(week):
                if day == 0:
                    tk.Label(grid_f, text="", bg=BG_CARD2,
                             width=3, height=1).grid(row=row_i, column=col_i,
                                                     padx=2, pady=2)
                    continue
                d = datetime.date(self._year, self._month, day)
                if d == sel:
                    bg, fg = ACCENT, TEXT_WHITE
                elif d == today:
                    bg, fg = SUCCESS, TEXT_WHITE
                else:
                    bg = BG_DARK
                    fg = ACCENT if col_i >= 5 else TEXT_WHITE
                tk.Button(grid_f, text=str(day), bg=bg, fg=fg,
                          relief="flat", font=("Segoe UI", 9),
                          width=3, height=1, cursor="hand2",
                          activebackground=ACCENT, activeforeground=TEXT_WHITE,
                          bd=0,
                          command=lambda dd=d: self._select(dd)
                          ).grid(row=row_i, column=col_i, padx=2, pady=2)

    def _prev_month(self):
        self._month -= 1
        if self._month < 1:
            self._month = 12
            self._year -= 1
        self._build()

    def _next_month(self):
        self._month += 1
        if self._month > 12:
            self._month = 1
            self._year += 1
        self._build()

    def _select(self, date: datetime.date):
        self._entry.delete(0, "end")
        self._entry.insert(0, date.isoformat())
        self.destroy()


# ══════════════════════════════════════════════════════════════════════════════
# DIÁLOGO EDITAR GASTO
# ══════════════════════════════════════════════════════════════════════════════

class EditExpenseDialog(tk.Toplevel):
    """Diálogo modal para editar un gasto existente."""

    def __init__(self, parent, dm, expense: dict, on_save):
        super().__init__(parent)
        self.withdraw()
        self._dm      = dm
        self._expense = expense
        self._on_save = on_save

        self.title("✏️ Editar Gasto")
        self.configure(bg=BG_DARK)
        self.resizable(False, False)
        self.transient(parent)
        self._build()

        self.update_idletasks()
        dw = self.winfo_reqwidth()
        dh = self.winfo_reqheight()
        px, py = parent.winfo_x(), parent.winfo_y()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        self.geometry(f"+{px + (pw - dw)//2}+{py + (ph - dh)//2}")
        self.deiconify()

        self.wait_visibility()
        self.grab_set()
        self._date_entry.focus_set()

    def _build(self):
        e = self._expense
        inner = tk.Frame(self, bg=BG_CARD, padx=24, pady=20)
        inner.pack(fill="both", expand=True, padx=16, pady=16)

        label(inner, "✏️  Editar Gasto", 14, bold=True).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 16))

        # Fecha
        label(inner, "Fecha", 10, color=TEXT_MUTED).grid(
            row=1, column=0, sticky="w", pady=(0, 2))
        self._date_var = tk.StringVar(master=self, value=e["date"])
        date_wrap = tk.Frame(inner, bg=BG_CARD)
        date_wrap.grid(row=2, column=0, sticky="w", pady=(0, 10), padx=(0, 12))
        self._date_entry = tk.Entry(date_wrap, textvariable=self._date_var,
                                    bg=BG_CARD2, fg=TEXT_WHITE,
                                    insertbackground=TEXT_WHITE, relief="flat",
                                    font=("Segoe UI", 11), width=13)
        self._date_entry.pack(side="left", ipady=5)
        tk.Button(date_wrap, text="📅", bg=BG_CARD2, fg=TEXT_WHITE,
                  relief="flat", font=("Segoe UI", 10), cursor="hand2",
                  activebackground=BG_CARD2, activeforeground=ACCENT,
                  bd=0, padx=6, pady=5,
                  command=lambda: DatePicker(self, self._date_entry)
                  ).pack(side="left")

        # Categoría
        label(inner, "Categoría", 10, color=TEXT_MUTED).grid(
            row=1, column=1, sticky="w", pady=(0, 2))
        self._cat_var = tk.StringVar(master=self, value=e["category"])
        cats = self._dm.categories
        cat_cb = ttk.Combobox(inner, textvariable=self._cat_var, values=cats,
                              width=18, font=("Segoe UI", 11), state="readonly")
        if e["category"] in cats:
            cat_cb.current(cats.index(e["category"]))
        cat_cb.grid(row=2, column=1, sticky="w", ipady=4, pady=(0, 10))

        # Descripción
        label(inner, "Descripción", 10, color=TEXT_MUTED).grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(0, 2))
        self._desc_var = tk.StringVar(master=self, value=e["description"])
        tk.Entry(inner, textvariable=self._desc_var,
                 bg=BG_CARD2, fg=TEXT_WHITE,
                 insertbackground=TEXT_WHITE, relief="flat",
                 font=("Segoe UI", 11), width=38
                 ).grid(row=4, column=0, columnspan=2, sticky="w", ipady=5, pady=(0, 10))

        # Importe
        label(inner, "Importe (€)", 10, color=TEXT_MUTED).grid(
            row=5, column=0, sticky="w", pady=(0, 2))
        self._amount_var = tk.StringVar(master=self, value=str(e["amount"]))
        tk.Entry(inner, textvariable=self._amount_var,
                 bg=BG_CARD2, fg=TEXT_WHITE,
                 insertbackground=TEXT_WHITE, relief="flat",
                 font=("Segoe UI", 11), width=14
                 ).grid(row=6, column=0, sticky="w", ipady=5, pady=(0, 10), padx=(0, 12))

        # Recurrente
        self._rec_var = tk.BooleanVar(master=self, value=bool(e["recurring"]))
        ttk.Checkbutton(inner, text="🔁 Recurrente",
                        variable=self._rec_var).grid(row=6, column=1, sticky="w", pady=(0, 10))

        # Botones
        btn_frame = tk.Frame(inner, bg=BG_CARD)
        btn_frame.grid(row=7, column=0, columnspan=2, sticky="e", pady=(4, 0))
        styled_button(btn_frame, "💾 Guardar", self._guardar,
                      color=SUCCESS, font_size=10, pady=6).pack(side="left", padx=(0, 8))
        styled_button(btn_frame, "Cancelar", self.destroy,
                      color=BG_CARD2, font_size=10, pady=6).pack(side="left")

    def _guardar(self):
        new_date   = self._date_var.get().strip()
        new_cat    = self._cat_var.get().strip()
        new_desc   = self._desc_var.get().strip()
        new_amount = self._amount_var.get().strip().replace(",", ".").replace("€", "")

        if not all([new_date, new_cat, new_desc, new_amount]):
            messagebox.showerror("Error", "Rellena todos los campos.", parent=self)
            return
        try:
            datetime.date.fromisoformat(new_date)
        except ValueError:
            messagebox.showerror("Error",
                                 "Fecha inválida. Usa AAAA-MM-DD o el botón 📅.",
                                 parent=self)
            return
        try:
            amount_f = float(new_amount)
        except ValueError:
            messagebox.showerror("Error",
                                 "Importe inválido. Usa números (ej: 12.50).",
                                 parent=self)
            return

        self._dm.update_expense(
            self._expense["id"], new_date, new_cat, new_desc, amount_f,
            recurring=int(self._rec_var.get())
        )
        self.destroy()
        self._on_save()
