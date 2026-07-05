#!/usr/bin/env python3
"""
EconoHogar - Control de Gastos y Economía Doméstica
Aplicación de escritorio para Ubuntu
"""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, colorchooser
import datetime
from collections import defaultdict

from constants import (BG_DARK, BG_CARD, BG_CARD2, ACCENT, ACCENT2,
                       TEXT_WHITE, TEXT_MUTED, SUCCESS, WARNING, INFO,
                       MATPLOTLIB_OK, CATEGORY_COLORS, CATEGORY_ICONS,
                       DATA_FILE, DB_FILE)
from data_manager import DataManager
from widgets import (IconPicker, RoundedFrame, DatePicker, EditExpenseDialog,
                     styled_button, label, _lighten)

try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
except ImportError:
    pass


# ══════════════════════════════════════════════════════════════════════════════
# VENTANA PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════
class EconoHogar(tk.Tk):
    def __init__(self):
        super().__init__()
        self.dm = DataManager()
        self.title("EconoHogar – Control de Gastos")
        self.configure(bg=BG_DARK)
        self.minsize(1100, 700)
        self.geometry("1280x800")

        # Estado mes/año activo
        now = datetime.date.today()
        self.active_year  = tk.IntVar(value=now.year)
        self.active_month = tk.IntVar(value=now.month)
        # Mes anterior para detectar cambio y proponer recurrentes
        self._prev_ym = f"{now.year:04d}-{now.month:02d}"

        self._build_ui()
        self.refresh_all()
        self._bind_shortcuts()

    def _bind_shortcuts(self):
        self.bind_all("<Control-n>", lambda e: self._shortcut_new_expense())
        self.bind_all("<Control-N>", lambda e: self._shortcut_new_expense())
        self.bind_all("<Control-Delete>", lambda e: self._delete_expense())
        # Flechas solo navegan si el foco no está en un widget de texto
        self.bind_all("<Left>",  self._shortcut_prev_month)
        self.bind_all("<Right>", self._shortcut_next_month)

    def _shortcut_new_expense(self):
        self.notebook.select(self.tab_expenses)
        self.exp_date.focus_set()

    def _is_text_widget(self):
        w = self.focus_get()
        return isinstance(w, (tk.Entry, tk.Text, ttk.Combobox, tk.Spinbox))

    def _shortcut_prev_month(self, event=None):
        if self._is_text_widget():
            return
        m = self.active_month.get()
        y = self.active_year.get()
        m -= 1
        if m < 1:
            m = 12
            y -= 1
        self.active_month.set(m)
        self.active_year.set(y)
        self._on_month_change()

    def _shortcut_next_month(self, event=None):
        if self._is_text_widget():
            return
        m = self.active_month.get()
        y = self.active_year.get()
        m += 1
        if m > 12:
            m = 1
            y += 1
        self.active_month.set(m)
        self.active_year.set(y)
        self._on_month_change()

    # ── Cambio de mes con detección de recurrentes ─────────────────────────────
    def _on_month_change(self):
        """Llama a refresh_all y, si cambió el mes, propone copiar recurrentes."""
        new_ym  = f"{self.active_year.get():04d}-{self.active_month.get():02d}"
        prev_ym = self._prev_ym
        if prev_ym and prev_ym != new_ym:
            recurrentes = self.dm.recurring_expenses_for_month(prev_ym)
            if recurrentes:
                self._offer_recurring(recurrentes, new_ym)
        self._prev_ym = new_ym
        self.refresh_all()

    def _offer_recurring(self, recurrentes: list, new_ym: str):
        """Ofrece copiar gastos recurrentes del mes anterior al mes nuevo."""
        # Solo proponer los que no existen ya en el mes nuevo (misma cat + descripción)
        existentes = self.dm.expenses_for_month(new_ym)
        existentes_keys = {(e["category"], e["description"]) for e in existentes}
        pendientes = [e for e in recurrentes
                      if (e["category"], e["description"]) not in existentes_keys]
        if not pendientes:
            return

        dialog = tk.Toplevel(self)
        dialog.title("Gastos recurrentes")
        dialog.configure(bg=BG_DARK)
        dialog.transient(self)

        tk.Label(dialog, text="Tienes gastos recurrentes del mes anterior.\n¿Cuáles quieres añadir?",
                 bg=BG_DARK, fg=TEXT_WHITE, font=("Segoe UI", 11), justify="left").pack(padx=20, pady=(16, 8))

        vars_checks = []
        for e in pendientes:
            var = tk.BooleanVar(master=dialog, value=True)
            texto = f"  {e['category']} — {e['description']}  ({e['amount']:.2f} €)"
            ttk.Checkbutton(dialog, text=texto, variable=var).pack(anchor="w", padx=20, pady=2)
            vars_checks.append((var, e))

        def _aceptar():
            import calendar
            # Usar el último día del mes si el día original no existe en el mes nuevo
            year, month = int(new_ym[:4]), int(new_ym[5:7])
            last_day = calendar.monthrange(year, month)[1]
            for var, e in vars_checks:
                if var.get():
                    orig_day = int(e["date"][8:10])
                    day = min(orig_day, last_day)
                    new_date = f"{new_ym}-{day:02d}"
                    self.dm.add_expense(new_date, e["category"], e["description"],
                                        e["amount"], recurring=1)
            dialog.destroy()
            self.refresh_all()

        def _cancelar():
            dialog.destroy()

        btn_frame = tk.Frame(dialog, bg=BG_DARK)
        btn_frame.pack(pady=16)
        tk.Button(btn_frame, text="Añadir seleccionados", command=_aceptar,
                  bg=ACCENT, fg="white", relief="flat", padx=12, pady=6).pack(side="left", padx=8)
        tk.Button(btn_frame, text="Omitir", command=_cancelar,
                  bg=BG_CARD, fg=TEXT_MUTED, relief="flat", padx=12, pady=6).pack(side="left", padx=8)

        dialog.wait_visibility()
        dialog.grab_set()
        dialog.wait_window()

    # ── Layout principal ───────────────────────────────────────────────────────
    def _build_ui(self):
        # Sidebar
        self.sidebar = tk.Frame(self, bg=BG_CARD2, width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self._build_sidebar()

        # Contenido principal
        self.main = tk.Frame(self, bg=BG_DARK)
        self.main.pack(side="left", fill="both", expand=True)

        # Notebook (pestañas)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Custom.TNotebook", background=BG_DARK, borderwidth=0)
        style.configure("Custom.TNotebook.Tab",
                        background=BG_CARD, foreground=TEXT_MUTED,
                        font=("Segoe UI", 10, "bold"), padding=[16, 8],
                        borderwidth=0)
        style.map("Custom.TNotebook.Tab",
                  background=[("selected", ACCENT)],
                  foreground=[("selected", TEXT_WHITE)])

        self.notebook = ttk.Notebook(self.main, style="Custom.TNotebook")
        self.notebook.pack(fill="both", expand=True, padx=12, pady=12)

        self.tab_dashboard  = tk.Frame(self.notebook, bg=BG_DARK)
        self.tab_expenses   = tk.Frame(self.notebook, bg=BG_DARK)
        self.tab_charts     = tk.Frame(self.notebook, bg=BG_DARK)
        self.tab_savings    = tk.Frame(self.notebook, bg=BG_DARK)
        self.tab_categories = tk.Frame(self.notebook, bg=BG_DARK)

        self.notebook.add(self.tab_dashboard,  text="  📊 Dashboard  ")
        self.notebook.add(self.tab_expenses,   text="  💸 Gastos  ")
        self.notebook.add(self.tab_charts,     text="  📈 Gráficos  ")
        self.notebook.add(self.tab_savings,    text="  💰 Ahorro  ")
        self.notebook.add(self.tab_categories, text="  🏷️ Categorías  ")

        self._build_dashboard()
        self._build_expenses_tab()
        self._build_charts_tab()
        self._build_savings_tab()
        self._build_categories_tab()

    # ── Sidebar ────────────────────────────────────────────────────────────────
    def _build_sidebar(self):
        tk.Label(self.sidebar, text="💰", bg=BG_CARD2,
                 font=("Segoe UI", 32)).pack(pady=(28, 4))
        tk.Label(self.sidebar, text="EconoHogar", bg=BG_CARD2,
                 fg=TEXT_WHITE, font=("Segoe UI", 14, "bold")).pack()
        tk.Label(self.sidebar, text="Tu economía doméstica", bg=BG_CARD2,
                 fg=TEXT_MUTED, font=("Segoe UI", 9)).pack(pady=(2, 20))

        ttk.Separator(self.sidebar, orient="horizontal").pack(fill="x", padx=16, pady=8)

        # Selector de mes/año
        nav = tk.Frame(self.sidebar, bg=BG_CARD2)
        nav.pack(fill="x", padx=12, pady=4)
        label(nav, "Periodo activo", 9, color=TEXT_MUTED).pack(anchor="w")

        row_y = tk.Frame(nav, bg=BG_CARD2)
        row_y.pack(fill="x", pady=2)
        label(row_y, "Año:", 10).pack(side="left")
        tk.Spinbox(row_y, from_=2020, to=2040, textvariable=self.active_year,
                   width=6, bg=BG_CARD, fg=TEXT_WHITE, buttonbackground=BG_CARD,
                   relief="flat", font=("Segoe UI", 10),
                   command=self._on_month_change).pack(side="right")

        row_m = tk.Frame(nav, bg=BG_CARD2)
        row_m.pack(fill="x", pady=2)
        label(row_m, "Mes:", 10).pack(side="left")
        tk.Spinbox(row_m, from_=1, to=12, textvariable=self.active_month,
                   width=4, bg=BG_CARD, fg=TEXT_WHITE, buttonbackground=BG_CARD,
                   relief="flat", font=("Segoe UI", 10),
                   command=self._on_month_change).pack(side="right")

        ttk.Separator(self.sidebar, orient="horizontal").pack(fill="x", padx=16, pady=12)

        # Salario del mes
        label(self.sidebar, "Salario mensual", 9, color=TEXT_MUTED).pack(anchor="w", padx=16)
        self.salary_var = tk.StringVar()
        sal_entry = tk.Entry(self.sidebar, textvariable=self.salary_var,
                             bg=BG_CARD, fg=TEXT_WHITE, insertbackground=TEXT_WHITE,
                             relief="flat", font=("Segoe UI", 12, "bold"),
                             justify="center")
        sal_entry.pack(fill="x", padx=16, pady=4, ipady=6)

        styled_button(self.sidebar, "💾 Guardar salario",
                      self._save_salary, color=SUCCESS,
                      font_size=9, padx=8, pady=5).pack(fill="x", padx=16, pady=2)

        ttk.Separator(self.sidebar, orient="horizontal").pack(fill="x", padx=16, pady=12)

        # Resumen rápido sidebar
        self.sb_spent   = self._sidebar_stat("Gastado", "0,00 €")
        self.sb_salary  = self._sidebar_stat("Salario", "0,00 €")
        self.sb_balance = self._sidebar_stat("Balance", "0,00 €", color=SUCCESS)

        # Botón añadir gasto rápido
        tk.Frame(self.sidebar, bg=BG_CARD2).pack(expand=True)
        styled_button(self.sidebar, "➕  Añadir Gasto",
                      lambda: self.notebook.select(1),
                      color=ACCENT, font_size=11).pack(fill="x", padx=16, pady=(0, 24))

    def _sidebar_stat(self, label_text, value_text, color=TEXT_WHITE):
        frame = tk.Frame(self.sidebar, bg=BG_CARD2)
        frame.pack(fill="x", padx=16, pady=3)
        tk.Label(frame, text=label_text, bg=BG_CARD2, fg=TEXT_MUTED,
                 font=("Segoe UI", 9)).pack(anchor="w")
        lbl = tk.Label(frame, text=value_text, bg=BG_CARD2, fg=color,
                       font=("Segoe UI", 13, "bold"))
        lbl.pack(anchor="w")
        return lbl

    # ── Dashboard ──────────────────────────────────────────────────────────────
    def _build_dashboard(self):
        tab = self.tab_dashboard
        # Header
        hdr = tk.Frame(tab, bg=BG_DARK)
        hdr.pack(fill="x", padx=16, pady=(16, 8))
        self.dash_title = label(hdr, "Dashboard – Enero 2025", 18, bold=True)
        self.dash_title.pack(side="left")

        # KPI cards row
        self.kpi_frame = tk.Frame(tab, bg=BG_DARK)
        self.kpi_frame.pack(fill="x", padx=16, pady=8)

        # Recent expenses list
        mid = tk.Frame(tab, bg=BG_DARK)
        mid.pack(fill="both", expand=True, padx=16, pady=8)

        left = tk.Frame(mid, bg=BG_DARK)
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))

        label(left, "Últimos gastos del mes", 12, bold=True).pack(anchor="w", pady=(0, 6))
        self.recent_frame = tk.Frame(left, bg=BG_CARD, pady=4)
        self.recent_frame.pack(fill="both", expand=True)

        right = tk.Frame(mid, bg=BG_DARK, width=260)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        label(right, "Top categorías", 12, bold=True).pack(anchor="w", pady=(0, 6))
        self.top_cat_frame = tk.Frame(right, bg=BG_CARD)
        self.top_cat_frame.pack(fill="both", expand=True)

    def _kpi_card(self, parent, icon, title, value, color=ACCENT, subtitle=""):
        card = tk.Frame(parent, bg=BG_CARD, padx=16, pady=14)
        card.pack(side="left", fill="both", expand=True, padx=6)
        tk.Label(card, text=icon, bg=BG_CARD, font=("Segoe UI", 22)).pack(anchor="w")
        tk.Label(card, text=title, bg=BG_CARD, fg=TEXT_MUTED,
                 font=("Segoe UI", 9)).pack(anchor="w")
        tk.Label(card, text=value, bg=BG_CARD, fg=color,
                 font=("Segoe UI", 18, "bold")).pack(anchor="w")
        if subtitle:
            tk.Label(card, text=subtitle, bg=BG_CARD, fg=TEXT_MUTED,
                     font=("Segoe UI", 8)).pack(anchor="w")
        return card

    # ── Pestaña Gastos ─────────────────────────────────────────────────────────
    def _build_expenses_tab(self):
        tab = self.tab_expenses

        # Formulario
        form_card = tk.Frame(tab, bg=BG_CARD, padx=20, pady=16)
        form_card.pack(fill="x", padx=16, pady=(16, 8))

        label(form_card, "➕  Nuevo Gasto", 13, bold=True).grid(
            row=0, column=0, columnspan=6, sticky="w", pady=(0, 12))

        # Fecha (entry + botón calendario)
        label(form_card, "Fecha", 10, color=TEXT_MUTED).grid(row=1, column=0, sticky="w", padx=(0, 8))
        date_wrap = tk.Frame(form_card, bg=BG_CARD)
        date_wrap.grid(row=2, column=0, padx=(0, 12), sticky="w")
        self.exp_date = tk.Entry(date_wrap, bg=BG_CARD2, fg=TEXT_WHITE,
                                 insertbackground=TEXT_WHITE, relief="flat",
                                 font=("Segoe UI", 11), width=12)
        self.exp_date.insert(0, datetime.date.today().isoformat())
        self.exp_date.pack(side="left", ipady=5)
        tk.Button(date_wrap, text="📅", bg=BG_CARD2, fg=TEXT_WHITE,
                  relief="flat", font=("Segoe UI", 10), cursor="hand2",
                  activebackground=BG_CARD2, activeforeground=ACCENT,
                  bd=0, padx=6, pady=5,
                  command=lambda: DatePicker(self, self.exp_date)
                  ).pack(side="left")

        # Categoría
        label(form_card, "Categoría", 10, color=TEXT_MUTED).grid(row=1, column=1, sticky="w")
        self.exp_cat_var = tk.StringVar()
        self.exp_cat_cb = ttk.Combobox(form_card, textvariable=self.exp_cat_var, width=18,
                                        font=("Segoe UI", 11), state="readonly")
        self.exp_cat_cb.grid(row=2, column=1, padx=(0, 12), ipady=4)

        # Descripción
        label(form_card, "Descripción", 10, color=TEXT_MUTED).grid(row=1, column=2, sticky="w")
        self.exp_desc = tk.Entry(form_card, bg=BG_CARD2, fg=TEXT_WHITE,
                                  insertbackground=TEXT_WHITE, relief="flat",
                                  font=("Segoe UI", 11), width=24)
        self.exp_desc.grid(row=2, column=2, padx=(0, 12), ipady=5)

        # Importe
        label(form_card, "Importe (€)", 10, color=TEXT_MUTED).grid(row=1, column=3, sticky="w")
        self.exp_amount = tk.Entry(form_card, bg=BG_CARD2, fg=TEXT_WHITE,
                                    insertbackground=TEXT_WHITE, relief="flat",
                                    font=("Segoe UI", 11), width=10)
        self.exp_amount.grid(row=2, column=3, padx=(0, 12), ipady=5)

        # Checkbox recurrente
        self.exp_rec_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(form_card, text="🔁 Recurrente",
                        variable=self.exp_rec_var).grid(row=2, column=4, padx=(0, 8))

        styled_button(form_card, "➕ Añadir", self._add_expense,
                      color=ACCENT).grid(row=2, column=5, padx=4)

        # Lista gastos
        list_hdr = tk.Frame(tab, bg=BG_DARK)
        list_hdr.pack(fill="x", padx=16, pady=(4, 2))
        self.expenses_month_label = label(list_hdr, "Gastos del mes", 12, bold=True)
        self.expenses_month_label.pack(side="left")

        # Campo de búsqueda (a la derecha, antes del filtro de categoría)
        search_wrap = tk.Frame(list_hdr, bg=BG_DARK)
        search_wrap.pack(side="right", padx=(0, 12))
        label(search_wrap, "🔍", 11).pack(side="left", padx=(0, 4))
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(search_wrap, textvariable=self.search_var,
                                bg=BG_CARD2, fg=TEXT_WHITE, insertbackground=TEXT_WHITE,
                                relief="flat", font=("Segoe UI", 10), width=20)
        search_entry.pack(side="left", ipady=3)
        tk.Button(search_wrap, text="✕", bg=BG_DARK, fg=TEXT_MUTED,
                  relief="flat", font=("Segoe UI", 9), cursor="hand2",
                  activebackground=BG_DARK, activeforeground=ACCENT, bd=0,
                  command=lambda: (self.search_var.set(""), self._refresh_expenses())
                  ).pack(side="left", padx=(2, 0))
        self.search_var.trace_add("write", lambda *_: self._refresh_expenses())

        # Filtro por categoría
        filter_wrap = tk.Frame(list_hdr, bg=BG_DARK)
        filter_wrap.pack(side="right")
        label(filter_wrap, "Filtrar:", 10, color=TEXT_MUTED).pack(side="left", padx=(0, 6))
        self.filter_cat_var = tk.StringVar(value="Todas")
        self.filter_cat_cb = ttk.Combobox(filter_wrap, textvariable=self.filter_cat_var,
                                           width=18, font=("Segoe UI", 10), state="readonly")
        self.filter_cat_cb.pack(side="left")
        self.filter_cat_cb.bind("<<ComboboxSelected>>", lambda e: self._refresh_expenses())

        # Treeview
        tree_frame = tk.Frame(tab, bg=BG_CARD)
        tree_frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        cols = ("Fecha", "Categoría", "Descripción", "Importe")
        style = ttk.Style()
        style.configure("Expense.Treeview",
                        background=BG_CARD, foreground=TEXT_WHITE,
                        fieldbackground=BG_CARD, rowheight=32,
                        font=("Segoe UI", 10))
        style.configure("Expense.Treeview.Heading",
                        background=BG_CARD2, foreground=TEXT_WHITE,
                        font=("Segoe UI", 10, "bold"))
        style.map("Expense.Treeview", background=[("selected", ACCENT2)])

        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings",
                                  style="Expense.Treeview")
        widths = [100, 140, 320, 100]
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center" if col == "Importe" else "w")

        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # Doble clic abre el diálogo de edición
        self.tree.bind("<Double-1>", self._edit_expense)

        styled_button(tab, "🗑️  Eliminar seleccionado",
                      self._delete_expense, color="#C62828",
                      font_size=9, pady=5).pack(anchor="e", padx=16, pady=4)

    # ── Pestaña Gráficos ───────────────────────────────────────────────────────
    def _build_charts_tab(self):
        tab = self.tab_charts
        ctrl = tk.Frame(tab, bg=BG_DARK)
        ctrl.pack(fill="x", padx=16, pady=8)

        label(ctrl, "Tipo de gráfico:", 10, color=TEXT_MUTED).pack(side="left", padx=(0, 8))
        self.chart_type = tk.StringVar(value="monthly_pie")
        options = [
            ("🥧 Tarta mensual",        "monthly_pie"),
            ("📊 Barras mensual",       "monthly_bar"),
            ("📈 Evolución anual",      "annual_line"),
            ("🗓️ Gastos por día",      "daily_bar"),
            ("🔀 Comparativa mensual", "monthly_compare"),
        ]
        for text, val in options:
            tk.Radiobutton(ctrl, text=text, variable=self.chart_type, value=val,
                           bg=BG_DARK, fg=TEXT_WHITE, selectcolor=ACCENT2,
                           activebackground=BG_DARK, activeforeground=TEXT_WHITE,
                           font=("Segoe UI", 10), command=self.refresh_charts
                           ).pack(side="left", padx=6)

        self.chart_container = tk.Frame(tab, bg=BG_DARK)
        self.chart_container.pack(fill="both", expand=True, padx=16, pady=8)

    # ── Pestaña Ahorro ─────────────────────────────────────────────────────────
    def _build_savings_tab(self):
        tab = self.tab_savings
        self.savings_frame = tk.Frame(tab, bg=BG_DARK)
        self.savings_frame.pack(fill="both", expand=True, padx=16, pady=16)

    # ── Pestaña Categorías ─────────────────────────────────────────────────────
    def _build_categories_tab(self):
        tab = self.tab_categories
        top = tk.Frame(tab, bg=BG_DARK)
        top.pack(fill="x", padx=16, pady=12)
        label(top, "Gestión de Categorías", 14, bold=True).pack(side="left")

        btn_row = tk.Frame(tab, bg=BG_DARK)
        btn_row.pack(fill="x", padx=16, pady=4)
        styled_button(btn_row, "➕ Nueva categoría", self._new_category,
                      color=SUCCESS, font_size=10, pady=6).pack(side="left", padx=4)
        styled_button(btn_row, "✏️ Renombrar", self._rename_category,
                      color=INFO, font_size=10, pady=6).pack(side="left", padx=4)
        styled_button(btn_row, "🗑️ Eliminar", self._remove_category,
                      color="#C62828", font_size=10, pady=6).pack(side="left", padx=4)
        styled_button(btn_row, "🎨 Cambiar color", self._change_cat_color,
                      color=ACCENT2, font_size=10, pady=6).pack(side="left", padx=4)
        styled_button(btn_row, "😀 Cambiar icono", self._change_cat_icon,
                      color="#6A4C93", font_size=10, pady=6).pack(side="left", padx=4)

        # Contenedor con scroll para el grid de categorías
        scroll_container = tk.Frame(tab, bg=BG_DARK)
        scroll_container.pack(fill="both", expand=True, padx=16, pady=8)

        self._cat_canvas = tk.Canvas(scroll_container, bg=BG_DARK, highlightthickness=0)
        cat_scrollbar = ttk.Scrollbar(scroll_container, orient="vertical",
                                      command=self._cat_canvas.yview)
        self._cat_canvas.configure(yscrollcommand=cat_scrollbar.set)

        cat_scrollbar.pack(side="right", fill="y")
        self._cat_canvas.pack(side="left", fill="both", expand=True)

        self.cat_frame = tk.Frame(self._cat_canvas, bg=BG_DARK)
        self._cat_canvas_window = self._cat_canvas.create_window(
            (0, 0), window=self.cat_frame, anchor="nw"
        )

        def _on_cat_frame_configure(_event):
            self._cat_canvas.configure(scrollregion=self._cat_canvas.bbox("all"))

        def _on_cat_canvas_configure(event):
            self._cat_canvas.itemconfig(self._cat_canvas_window, width=event.width)

        self.cat_frame.bind("<Configure>", _on_cat_frame_configure)
        self._cat_canvas.bind("<Configure>", _on_cat_canvas_configure)

        # Scroll con rueda del ratón
        def _on_mousewheel(event):
            self._cat_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self._cat_canvas.bind("<MouseWheel>", _on_mousewheel)
        self.cat_frame.bind("<MouseWheel>", _on_mousewheel)

    # ══════════════════════════════════════════════════════════════════════════
    # ACCIONES
    # ══════════════════════════════════════════════════════════════════════════
    def _save_salary(self):
        ym = f"{self.active_year.get():04d}-{self.active_month.get():02d}"
        try:
            val = float(self.salary_var.get().replace(",", ".").replace("€", "").strip())
        except ValueError:
            messagebox.showerror("Error", "Introduce un importe válido.")
            return
        self.dm.set_salary(ym, val)
        self.refresh_all()

    def _add_expense(self):
        date = self.exp_date.get().strip()
        cat  = self.exp_cat_var.get().strip()
        desc = self.exp_desc.get().strip()
        amt  = self.exp_amount.get().strip().replace(",", ".").replace("€", "")
        if not all([date, cat, desc, amt]):
            messagebox.showerror("Error", "Rellena todos los campos.")
            return
        try:
            datetime.date.fromisoformat(date)
        except ValueError:
            messagebox.showerror("Error",
                                 "Fecha inválida. Usa el formato AAAA-MM-DD\n"
                                 "o haz clic en 📅 para elegir del calendario.")
            return
        try:
            amount = float(amt)
        except ValueError:
            messagebox.showerror("Error", "Importe inválido. Usa números (ej: 12.50).")
            return
        self.dm.add_expense(date, cat, desc, amount, recurring=int(self.exp_rec_var.get()))
        self.exp_desc.delete(0, "end")
        self.exp_amount.delete(0, "end")
        self.exp_rec_var.set(False)
        self.refresh_all()

    def _delete_expense(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecciona un gasto para eliminar.")
            return
        # Obtener descripción e importe para mostrarlos en la confirmación
        vals = self.tree.item(sel[0])["values"]
        descripcion = vals[2]
        importe = vals[3]
        confirmado = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Seguro que quieres eliminar este gasto?\n\n"
            f"Descripción: {descripcion}\n"
            f"Importe: {importe}",
            parent=self
        )
        if not confirmado:
            return
        self.dm.delete_expense(int(sel[0]))
        self.refresh_all()

    def _edit_expense(self, event=None):
        # Fix timing: obtener la fila bajo el cursor directamente en lugar de
        # depender de selection(), que puede estar vacía cuando se dispara <Double-1>.
        if event:
            row_id = self.tree.identify_row(event.y)
            if not row_id:
                return
            self.tree.selection_set(row_id)
        sel = self.tree.selection()
        if not sel:
            return
        expense = self.dm.get_expense(int(sel[0]))
        if expense is None:
            return
        EditExpenseDialog(self, self.dm, expense, self.refresh_all)

    def _new_category(self):
        name = simpledialog.askstring("Nueva categoría", "Nombre de la categoría:",
                                      parent=self)
        if name is None:
            return
        name = name.strip()
        if not name:
            messagebox.showerror("Error", "El nombre de la categoría no puede estar vacío.")
            return
        if name in self.dm.categories:
            messagebox.showwarning("Aviso", f"La categoría '{name}' ya existe.")
            return
        # Insertar antes de abrir el color chooser: si el WM lanza TclError al
        # hacer grab en el chooser, la categoría no se pierde.
        fallback = CATEGORY_COLORS[len(self.dm.categories) % len(CATEGORY_COLORS)]
        self.dm.add_category(name, fallback)
        self.update()
        self.lift()
        self.focus_force()
        try:
            color = colorchooser.askcolor(title="Color de la categoría",
                                          parent=self)[1]
        except tk.TclError:
            color = None
        if color:
            self.dm.set_category_color(name, color)
        icon_picker = IconPicker(self)
        self.wait_window(icon_picker)
        if icon_picker.selected:
            self.dm.set_category_icon(name, icon_picker.selected)
        self.refresh_all()

    def _remove_category(self):
        sel = self._selected_category()
        if sel:
            if messagebox.askyesno("Confirmar", f"¿Eliminar categoría '{sel}'?"):
                self.dm.remove_category(sel)
                self.refresh_all()

    def _rename_category(self):
        sel = self._selected_category()
        if not sel:
            return
        new_name = simpledialog.askstring("Renombrar categoría",
                                          f"Nuevo nombre para '{sel}':",
                                          initialvalue=sel, parent=self)
        if new_name is None:
            return
        new_name = new_name.strip()
        if not new_name:
            messagebox.showerror("Error", "El nombre no puede estar vacío.")
            return
        if new_name == sel:
            return
        if new_name in self.dm.categories:
            messagebox.showwarning("Aviso", f"Ya existe una categoría llamada '{new_name}'.")
            return
        self.dm.rename_category(sel, new_name)
        self.refresh_all()

    def _change_cat_color(self):
        sel = self._selected_category()
        if sel:
            self.update()
            self.lift()
            self.focus_force()
            try:
                color = colorchooser.askcolor(title=f"Color para '{sel}'",
                                              parent=self)[1]
            except tk.TclError:
                messagebox.showerror(
                    "Error", "No se pudo abrir el selector de color.")
                return
            if color:
                self.dm.set_category_color(sel, color)
                self.refresh_all()

    def _change_cat_icon(self):
        sel = self._selected_category()
        if not sel:
            return
        picker = IconPicker(self)
        self.wait_window(picker)
        if picker.selected:
            self.dm.set_category_icon(sel, picker.selected)
            self.refresh_all()

    def _selected_category(self):
        # Recorre las cards de categorías buscando la seleccionada
        if hasattr(self, "_sel_cat") and self._sel_cat is not None:
            return self._sel_cat
        messagebox.showwarning("Aviso", "Selecciona una categoría primero.")
        return None

    # ══════════════════════════════════════════════════════════════════════════
    # REFRESH
    # ══════════════════════════════════════════════════════════════════════════
    def refresh_all(self):
        self._refresh_sidebar()
        self._refresh_dashboard()
        self._refresh_expenses()
        self.refresh_charts()
        self._refresh_savings()
        self._refresh_categories()
        self._update_combobox()

    def _ym(self):
        return f"{self.active_year.get():04d}-{self.active_month.get():02d}"

    def _month_name(self, month: int) -> str:
        names = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
                 "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
        return names[month - 1]

    def _refresh_sidebar(self):
        ym = self._ym()
        expenses = self.dm.expenses_for_month(ym)
        total_spent = sum(e["amount"] for e in expenses)
        salary = self.dm.get_salary(ym)
        balance = salary - total_spent
        self.salary_var.set(f"{salary:.2f}")
        self.sb_spent.config(text=f"{total_spent:,.2f} €")
        self.sb_salary.config(text=f"{salary:,.2f} €")
        color = SUCCESS if balance >= 0 else ACCENT
        self.sb_balance.config(text=f"{balance:,.2f} €", fg=color)

    def _refresh_dashboard(self):
        ym = self._ym()
        y, m = self.active_year.get(), self.active_month.get()
        mn = self._month_name(m)
        self.dash_title.config(text=f"Dashboard – {mn} {y}")

        expenses = self.dm.expenses_for_month(ym)
        total = sum(e["amount"] for e in expenses)
        salary = self.dm.get_salary(ym)
        balance = salary - total

        # KPI cards
        for w in self.kpi_frame.winfo_children():
            w.destroy()

        days_in_month = (datetime.date(y, m % 12 + 1, 1) - datetime.timedelta(days=1)).day if m < 12 else 31
        daily_avg = total / max(days_in_month, 1)
        pct = (total / salary * 100) if salary else 0

        self._kpi_card(self.kpi_frame, "💸", "Total gastado",
                       f"{total:,.2f} €", ACCENT,
                       f"{pct:.1f}% del salario")
        self._kpi_card(self.kpi_frame, "💰", "Salario",
                       f"{salary:,.2f} €", INFO, f"{mn} {y}")
        bal_color = SUCCESS if balance >= 0 else ACCENT
        self._kpi_card(self.kpi_frame, "🏦", "Balance",
                       f"{balance:,.2f} €", bal_color,
                       "Ahorro estimado" if balance >= 0 else "Déficit")
        self._kpi_card(self.kpi_frame, "📅", "Media diaria",
                       f"{daily_avg:,.2f} €", WARNING,
                       f"{len(expenses)} gastos registrados")

        # Recent expenses
        for w in self.recent_frame.winfo_children():
            w.destroy()
        last_10 = sorted(expenses, key=lambda e: e["date"], reverse=True)[:10]
        if not last_10:
            tk.Label(self.recent_frame, text="Sin gastos este mes",
                     bg=BG_CARD, fg=TEXT_MUTED,
                     font=("Segoe UI", 11)).pack(pady=24)
        for e in last_10:
            row = tk.Frame(self.recent_frame, bg=BG_CARD, pady=6)
            row.pack(fill="x", padx=12)
            icon = self.dm.category_icon(e["category"])
            color = self.dm.category_color(e["category"])
            tk.Label(row, text=icon, bg=BG_CARD,
                     font=("Segoe UI", 14)).pack(side="left", padx=(0, 8))
            info_f = tk.Frame(row, bg=BG_CARD)
            info_f.pack(side="left", fill="x", expand=True)
            tk.Label(info_f, text=e["description"], bg=BG_CARD, fg=TEXT_WHITE,
                     font=("Segoe UI", 10, "bold"), anchor="w").pack(anchor="w")
            tk.Label(info_f, text=f"{e['category']}  ·  {e['date']}", bg=BG_CARD,
                     fg=TEXT_MUTED, font=("Segoe UI", 8), anchor="w").pack(anchor="w")
            tk.Label(row, text=f"{e['amount']:,.2f} €", bg=BG_CARD, fg=color,
                     font=("Segoe UI", 12, "bold")).pack(side="right", padx=8)
            ttk.Separator(self.recent_frame, orient="horizontal").pack(
                fill="x", padx=12)

        # Top categorías
        for w in self.top_cat_frame.winfo_children():
            w.destroy()
        by_cat = defaultdict(float)
        for e in expenses:
            by_cat[e["category"]] += e["amount"]
        sorted_cats = sorted(by_cat.items(), key=lambda x: x[1], reverse=True)[:6]
        for cat, amt in sorted_cats:
            row = tk.Frame(self.top_cat_frame, bg=BG_CARD, pady=6)
            row.pack(fill="x", padx=12)
            icon = self.dm.category_icon(cat)
            color = self.dm.category_color(cat)
            pct2 = (amt / total * 100) if total else 0
            tk.Label(row, text=icon, bg=BG_CARD, font=("Segoe UI", 14)).pack(side="left")
            mid_f = tk.Frame(row, bg=BG_CARD)
            mid_f.pack(side="left", fill="x", expand=True, padx=8)
            tk.Label(mid_f, text=cat, bg=BG_CARD, fg=TEXT_WHITE,
                     font=("Segoe UI", 10), anchor="w").pack(anchor="w")
            # Mini barra
            bar_bg = tk.Frame(mid_f, bg=BG_CARD2, height=4)
            bar_bg.pack(fill="x", pady=2)
            tk.Frame(bar_bg, bg=color, height=4,
                     width=int(pct2 * 1.2)).pack(side="left")
            tk.Label(row, text=f"{amt:,.0f}€", bg=BG_CARD, fg=color,
                     font=("Segoe UI", 10, "bold")).pack(side="right")
            ttk.Separator(self.top_cat_frame, orient="h").pack(fill="x", padx=8)

    def _refresh_expenses(self):
        ym = self._ym()
        for item in self.tree.get_children():
            self.tree.delete(item)
        expenses = self.dm.expenses_for_month(ym)
        cat_filter = self.filter_cat_var.get() if hasattr(self, "filter_cat_var") else "Todas"
        visible = expenses if cat_filter == "Todas" else [e for e in expenses if e["category"] == cat_filter]
        # Filtro por texto (descripción o categoría, case-insensitive)
        texto = self.search_var.get().strip().lower() if hasattr(self, "search_var") else ""
        if texto:
            visible = [e for e in visible
                       if texto in e["description"].lower() or texto in e["category"].lower()]
        for e in sorted(visible, key=lambda e: e["date"], reverse=True):
            # Prefijo visual para gastos recurrentes
            desc = ("🔁 " if e.get("recurring") else "") + e["description"]
            self.tree.insert("", "end", iid=str(e["id"]), values=(
                e["date"], e["category"], desc, f"{e['amount']:.2f} €"
            ))
        mn = self._month_name(self.active_month.get())
        total_all = sum(e["amount"] for e in expenses)
        total_vis = sum(e["amount"] for e in visible)
        if cat_filter == "Todas":
            label_txt = f"Gastos de {mn} {self.active_year.get()}  –  Total: {total_all:,.2f} €"
        else:
            label_txt = (f"Gastos de {mn} {self.active_year.get()}  –  "
                         f"{cat_filter}: {total_vis:,.2f} €  /  Total mes: {total_all:,.2f} €")
        self.expenses_month_label.config(text=label_txt)

    def _update_combobox(self):
        cats = self.dm.categories
        icons = [f"{self.dm.category_icon(c)}  {c}" for c in cats]
        self.exp_cat_cb["values"] = icons
        if icons and not self.exp_cat_var.get():
            self.exp_cat_cb.current(0)
        # Sincronizar variable con nombre sin icono al añadir
        self.exp_cat_cb.bind("<<ComboboxSelected>>", self._on_cat_select)
        # Actualizar opciones del filtro preservando la selección actual
        prev = self.filter_cat_var.get() if hasattr(self, "filter_cat_var") else "Todas"
        self.filter_cat_cb["values"] = ["Todas"] + cats
        if prev in (["Todas"] + cats):
            self.filter_cat_var.set(prev)
        else:
            self.filter_cat_var.set("Todas")

    def _on_cat_select(self, event=None):
        val = self.exp_cat_var.get()
        # strip emoji prefix
        parts = val.split("  ", 1)
        if len(parts) == 2:
            self.exp_cat_var.set(parts[1])

    # ── Gráficos ───────────────────────────────────────────────────────────────
    def refresh_charts(self):
        if not MATPLOTLIB_OK:
            for w in self.chart_container.winfo_children():
                w.destroy()
            tk.Label(self.chart_container,
                     text="⚠️  matplotlib no está instalado.\n"
                          "Ejecuta:  pip install matplotlib",
                     bg=BG_DARK, fg=WARNING,
                     font=("Segoe UI", 13)).pack(pady=60)
            return

        for w in self.chart_container.winfo_children():
            w.destroy()

        ct = self.chart_type.get()
        ym = self._ym()
        y  = self.active_year.get()
        m  = self.active_month.get()

        plt.rcParams.update({
            "figure.facecolor": BG_CARD,
            "axes.facecolor":   BG_CARD,
            "axes.edgecolor":   TEXT_MUTED,
            "text.color":       TEXT_WHITE,
            "axes.labelcolor":  TEXT_WHITE,
            "xtick.color":      TEXT_MUTED,
            "ytick.color":      TEXT_MUTED,
            "axes.grid":        True,
            "grid.color":       BG_CARD2,
            "grid.linewidth":   0.6,
        })

        fig = Figure(figsize=(9, 5), facecolor=BG_CARD)
        dispatch = {
            "monthly_pie":     self._chart_pie,
            "monthly_bar":     self._chart_bar,
            "annual_line":     self._chart_annual_line,
            "daily_bar":       self._chart_daily_bar,
            "monthly_compare": self._chart_monthly_compare,
        }
        handler = dispatch.get(ct)
        if handler:
            handler(fig, ym, y, m)

        fig.tight_layout(pad=1.5)
        canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _chart_pie(self, fig, ym, y, m):
        expenses = self.dm.expenses_for_month(ym)
        by_cat = defaultdict(float)
        for e in expenses:
            by_cat[e["category"]] += e["amount"]
        if not by_cat:
            self._no_data(fig)
            return
        ax = fig.add_subplot(111)
        labels = list(by_cat.keys())
        sizes  = list(by_cat.values())
        colors = [self.dm.category_color(c) for c in labels]
        icons  = [self.dm.category_icon(c) for c in labels]
        label_txt = [f"{icons[i]} {labels[i]}\n{sizes[i]:,.2f}€ ({sizes[i]/sum(sizes)*100:.1f}%)"
                     for i in range(len(labels))]
        wedges, _ = ax.pie(
            sizes, labels=None, colors=colors,
            startangle=140, pctdistance=0.8,
            wedgeprops={"linewidth": 2, "edgecolor": BG_CARD})
        ax.legend(wedges, label_txt, loc="center left",
                  bbox_to_anchor=(1, 0, 0.5, 1), framealpha=0, fontsize=8)
        ax.set_title(f"Distribución de gastos – {self._month_name(m)} {y}",
                     color=TEXT_WHITE, fontsize=13, pad=16)

    def _chart_bar(self, fig, ym, y, m):
        expenses = self.dm.expenses_for_month(ym)
        by_cat = defaultdict(float)
        for e in expenses:
            by_cat[e["category"]] += e["amount"]
        if not by_cat:
            self._no_data(fig)
            return
        ax    = fig.add_subplot(111)
        cats  = list(by_cat.keys())
        vals  = list(by_cat.values())
        colors = [self.dm.category_color(c) for c in cats]
        bars = ax.bar(range(len(cats)), vals, color=colors,
                      width=0.6, edgecolor=BG_CARD, linewidth=1.5)
        for bar, val in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(vals)*0.01,
                    f"{val:,.0f}€", ha="center", va="bottom", color=TEXT_WHITE, fontsize=8)
        icons = [self.dm.category_icon(c) for c in cats]
        ax.set_xticks(range(len(cats)))
        ax.set_xticklabels([f"{icons[i]}\n{cats[i]}" for i in range(len(cats))], fontsize=8)
        ax.set_title(f"Gastos por categoría – {self._month_name(m)} {y}",
                     color=TEXT_WHITE, fontsize=13)
        ax.set_ylabel("Euros (€)")

    def _chart_annual_line(self, fig, _ym, y, _m):
        monthly_totals = []
        month_labels   = []
        for mo in range(1, 13):
            total = sum(e["amount"] for e in self.dm.expenses_for_month(f"{y:04d}-{mo:02d}"))
            monthly_totals.append(total)
            month_labels.append(self._month_name(mo)[:3])
        ax = fig.add_subplot(111)
        ax.plot(range(12), monthly_totals, color=ACCENT, linewidth=2.5,
                marker="o", markersize=7, markerfacecolor=ACCENT2)
        ax.fill_between(range(12), monthly_totals, alpha=0.15, color=ACCENT)
        for xi, val in enumerate(monthly_totals):
            if val > 0:
                ax.text(xi, val + max(monthly_totals or [1])*0.02,
                        f"{val:,.0f}€", ha="center", fontsize=7, color=TEXT_MUTED)
        salary_year = [self.dm.get_salary(f"{y:04d}-{mo:02d}") for mo in range(1, 13)]
        if any(s > 0 for s in salary_year):
            ax.plot(range(12), salary_year, color=SUCCESS, linewidth=1.5,
                    linestyle="--", label="Salario")
            ax.legend(framealpha=0)
        ax.set_xticks(range(12))
        ax.set_xticklabels(month_labels)
        ax.set_title(f"Evolución de gastos – {y}", color=TEXT_WHITE, fontsize=13)
        ax.set_ylabel("Euros (€)")

    def _chart_daily_bar(self, fig, ym, y, m):
        expenses = self.dm.expenses_for_month(ym)
        by_day = defaultdict(float)
        for e in expenses:
            by_day[int(e["date"].split("-")[2])] += e["amount"]
        days = list(range(1, 32))
        vals = [by_day.get(d, 0) for d in days]
        colors = [ACCENT if v > 0 else BG_CARD2 for v in vals]
        ax = fig.add_subplot(111)
        ax.bar(days, vals, color=colors, width=0.7)
        avg = sum(vals) / max(sum(1 for v in vals if v > 0), 1)
        ax.axhline(avg, color=WARNING, linestyle="--", linewidth=1.2,
                   label=f"Media: {avg:.2f}€")
        ax.legend(framealpha=0)
        ax.set_title(f"Gastos diarios – {self._month_name(m)} {y}",
                     color=TEXT_WHITE, fontsize=13)
        ax.set_xlabel("Día del mes")
        ax.set_ylabel("Euros (€)")

    def _chart_monthly_compare(self, fig, _ym, y, m):
        def prev_ym(yy, mm, delta):
            mm -= delta
            while mm < 1:
                mm += 12; yy -= 1
            return yy, mm

        months_data = []
        for delta in (2, 1, 0):
            yy, mm = prev_ym(y, m, delta)
            exps = self.dm.expenses_for_month(f"{yy:04d}-{mm:02d}")
            by_cat = defaultdict(float)
            for e in exps:
                by_cat[e["category"]] += e["amount"]
            months_data.append((yy, mm, by_cat))

        all_cats = list(dict.fromkeys(c for _, _, bc in months_data for c in bc))
        if not all_cats:
            self._no_data(fig)
            return

        ax = fig.add_subplot(111)
        n  = len(all_cats)
        w  = 0.25
        xs = range(n)
        month_colors = ["#4A6FA5", WARNING, ACCENT]
        max_val = max((v for _, _, bc in months_data for v in bc.values()), default=1)

        for i, (yy, mm, by_cat) in enumerate(months_data):
            vals    = [by_cat.get(c, 0) for c in all_cats]
            offsets = [x + (i - 1) * w for x in xs]
            bars = ax.bar(offsets, vals, width=w * 0.9,
                          color=month_colors[i], edgecolor=BG_CARD,
                          linewidth=1, label=f"{self._month_name(mm)[:3]} {yy}")
            for bar, val in zip(bars, vals):
                if val > 0:
                    ax.text(bar.get_x() + bar.get_width() / 2,
                            bar.get_height() + max_val * 0.01,
                            f"{val:,.0f}€", ha="center", va="bottom",
                            color=TEXT_WHITE, fontsize=7)

        icons = [self.dm.category_icon(c) for c in all_cats]
        ax.set_xticks(list(xs))
        ax.set_xticklabels([f"{icons[i]}\n{all_cats[i]}" for i in range(n)], fontsize=8)
        ax.set_ylabel("Euros (€)")
        ax.set_title(f"Comparativa mensual – {self._month_name(m)} {y} vs meses anteriores",
                     color=TEXT_WHITE, fontsize=13)
        ax.legend(framealpha=0, fontsize=9)

    def _no_data(self, fig):
        ax = fig.add_subplot(111)
        ax.text(0.5, 0.5, "Sin datos para este periodo",
                ha="center", va="center", color=TEXT_MUTED, fontsize=14,
                transform=ax.transAxes)
        ax.set_axis_off()

    # ── Ahorro ─────────────────────────────────────────────────────────────────
    def _refresh_savings(self):
        for w in self.savings_frame.winfo_children():
            w.destroy()

        ym = self._ym()
        y, m = self.active_year.get(), self.active_month.get()
        expenses = self.dm.expenses_for_month(ym)
        total_spent = sum(e["amount"] for e in expenses)
        salary = self.dm.get_salary(ym)
        balance = salary - total_spent

        label(self.savings_frame, "💰 Análisis de Ahorro", 16, bold=True).pack(
            anchor="w", pady=(0, 16))

        # Balance card
        bal_card = tk.Frame(self.savings_frame, bg=SUCCESS if balance >= 0 else ACCENT,
                            padx=24, pady=18)
        bal_card.pack(fill="x", pady=(0, 16))
        mn = self._month_name(m)
        tk.Label(bal_card, text=f"Balance de {mn} {y}",
                 bg=bal_card["bg"], fg=TEXT_WHITE,
                 font=("Segoe UI", 11)).pack(anchor="w")
        tk.Label(bal_card, text=f"{'✅' if balance >= 0 else '❌'}  {balance:+,.2f} €",
                 bg=bal_card["bg"], fg=TEXT_WHITE,
                 font=("Segoe UI", 22, "bold")).pack(anchor="w")
        pct_saved = (balance / salary * 100) if salary else 0
        tk.Label(bal_card,
                 text=f"Ahorro: {pct_saved:.1f}% del salario" if balance >= 0
                      else "Gastos superiores al salario",
                 bg=bal_card["bg"], fg=TEXT_WHITE,
                 font=("Segoe UI", 10)).pack(anchor="w")

        # Oportunidades de ahorro
        label(self.savings_frame, "💡 Oportunidades de ahorro", 13, bold=True).pack(
            anchor="w", pady=(8, 8))

        by_cat = defaultdict(float)
        for e in expenses:
            by_cat[e["category"]] += e["amount"]

        tips_shown = 0
        OPTIONAL_CATS = {"Ocio", "Ropa", "Gimnasio", "Viajes", "Otros"}

        for cat, amt in sorted(by_cat.items(), key=lambda x: x[1], reverse=True):
            pct = (amt / total_spent * 100) if total_spent else 0
            tip = None
            if cat in OPTIONAL_CATS and pct > 15:
                tip = (f"El gasto en '{cat}' representa el {pct:.1f}% del total. "
                       f"Reducirlo un 20% ahorraría {amt*0.2:,.2f} €/mes.")
            elif pct > 40 and cat not in {"Hipoteca", "Alquiler"}:
                tip = (f"'{cat}' ocupa el {pct:.1f}% del presupuesto. "
                       f"Considera revisar estos gastos.")
            if tip:
                tip_card = tk.Frame(self.savings_frame, bg=BG_CARD, padx=16, pady=10)
                tip_card.pack(fill="x", pady=4)
                icon = self.dm.category_icon(cat)
                color = self.dm.category_color(cat)
                tk.Label(tip_card, text=f"{icon}  {cat}",
                         bg=BG_CARD, fg=color,
                         font=("Segoe UI", 11, "bold")).pack(anchor="w")
                tk.Label(tip_card, text=tip, bg=BG_CARD, fg=TEXT_WHITE,
                         font=("Segoe UI", 10), wraplength=700,
                         justify="left").pack(anchor="w", pady=2)
                tips_shown += 1

        if balance >= 0 and pct_saved >= 20:
            tip_card = tk.Frame(self.savings_frame, bg="#1B5E20", padx=16, pady=10)
            tip_card.pack(fill="x", pady=4)
            tk.Label(tip_card,
                     text=f"🎉  ¡Excelente! Estás ahorrando el {pct_saved:.1f}% de tu salario. "
                          f"Considera invertir parte del excedente.",
                     bg="#1B5E20", fg=TEXT_WHITE,
                     font=("Segoe UI", 11), wraplength=700).pack(anchor="w")

        if not tips_shown and not expenses:
            tk.Label(self.savings_frame,
                     text="Sin gastos registrados este mes. ¡Añade gastos para ver el análisis!",
                     bg=BG_DARK, fg=TEXT_MUTED,
                     font=("Segoe UI", 11)).pack(pady=24)

        # Proyección anual
        label(self.savings_frame, "📅 Proyección anual de ahorro", 13, bold=True).pack(
            anchor="w", pady=(16, 8))
        annual_saved = 0
        for mo in range(1, 13):
            ymo = f"{y:04d}-{mo:02d}"
            s = self.dm.get_salary(ymo)
            sp = sum(e["amount"] for e in self.dm.expenses_for_month(ymo))
            annual_saved += max(s - sp, 0)

        proj_card = tk.Frame(self.savings_frame, bg=BG_CARD2, padx=20, pady=14)
        proj_card.pack(fill="x", pady=4)
        tk.Label(proj_card, text=f"Ahorro acumulado en {y}:",
                 bg=BG_CARD2, fg=TEXT_MUTED,
                 font=("Segoe UI", 10)).pack(anchor="w")
        tk.Label(proj_card, text=f"{annual_saved:,.2f} €",
                 bg=BG_CARD2, fg=SUCCESS,
                 font=("Segoe UI", 20, "bold")).pack(anchor="w")

    # ── Categorías ─────────────────────────────────────────────────────────────
    def _refresh_categories(self):
        for w in self.cat_frame.winfo_children():
            w.destroy()
        self._sel_cat = None

        cats = self.dm.categories
        cols = 4
        for i, cat in enumerate(cats):
            row_f = i // cols
            col_f = i % cols
            color = self.dm.category_color(cat)
            icon  = self.dm.category_icon(cat)

            card = tk.Frame(self.cat_frame, bg=BG_CARD, padx=14, pady=10,
                            cursor="hand2")
            card.grid(row=row_f, column=col_f, padx=8, pady=8, sticky="nsew")
            self.cat_frame.columnconfigure(col_f, weight=1)

            tk.Label(card, text=icon, bg=BG_CARD,
                     font=("Segoe UI", 24)).pack(anchor="w")
            tk.Label(card, text=cat, bg=BG_CARD, fg=TEXT_WHITE,
                     font=("Segoe UI", 11, "bold")).pack(anchor="w")
            # color strip
            tk.Frame(card, bg=color, height=4).pack(fill="x", pady=(6, 0))

            def _select(event, c=cat, cd=card):
                self._sel_cat = c
                for child in self.cat_frame.winfo_children():
                    child.config(bg=BG_CARD)
                    for sub in child.winfo_children():
                        if isinstance(sub, (tk.Label, tk.Frame)):
                            try:
                                sub.config(bg=BG_CARD)
                            except Exception:
                                pass
                cd.config(bg=BG_CARD2)
                for sub in cd.winfo_children():
                    try:
                        sub.config(bg=BG_CARD2)
                    except Exception:
                        pass

            card.bind("<Button-1>", _select)
            for child in card.winfo_children():
                child.bind("<Button-1>", _select)

            # Propagar rueda del ratón desde las cards y sus hijos al canvas
            def _bind_mousewheel(widget):
                widget.bind("<MouseWheel>", lambda e: self._cat_canvas.yview_scroll(
                    int(-1 * (e.delta / 120)), "units"))
                for sub in widget.winfo_children():
                    _bind_mousewheel(sub)

            _bind_mousewheel(card)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = EconoHogar()
    app.mainloop()
