[calculadora_unificada (4).py](https://github.com/user-attachments/files/28604292/calculadora_unificada.4.py)
import customtkinter as ctk
import sympy as sp
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import math

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class CalculadoraLimitesApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Analizador y Visualizador de Límites · MATE1133")
        self.geometry("1150x700")
        self.minsize(950, 600)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ── Panel izquierdo ──
        self.frame_controles = ctk.CTkFrame(self, width=320, corner_radius=12)
        self.frame_controles.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        self.frame_controles.grid_propagate(False)

        ctk.CTkLabel(self.frame_controles, text=" 😶‍🌫️ Calculadora de Límites",
                     font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(22, 4))
        ctk.CTkLabel(self.frame_controles, text="MATE1133 · UCTemuco",
                     font=ctk.CTkFont(size=12), text_color="gray").pack(pady=(0, 18))
        ctk.CTkFrame(self.frame_controles, height=2, fg_color="#3a3a3a").pack(fill="x", padx=20, pady=(0, 18))

        ctk.CTkLabel(self.frame_controles, text="Función  f(x):",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=22)
        self.entry_func = ctk.CTkEntry(self.frame_controles,
                                       placeholder_text="Ej: sin(x)/x   |   x**2 - 4   |   1/x", height=38)
        self.entry_func.pack(fill="x", padx=22, pady=(4, 14))

        ctk.CTkLabel(self.frame_controles, text="Tiende a  h:",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=22)
        self.entry_h = ctk.CTkEntry(self.frame_controles,
                                    placeholder_text="Ej: 0   |   2   |   oo   |   -oo", height=38)
        self.entry_h.pack(fill="x", padx=22, pady=(4, 20))

        ctk.CTkLabel(self.frame_controles, text="Ejemplos rápidos:",
                     font=ctk.CTkFont(size=11), text_color="gray").pack(anchor="w", padx=22)
        for texto, func, h in [
            ("sin(x)/x  →  0",   "sin(x)/x",       "0"),
            ("x²−4  →  2",       "x**2 - 4",        "2"),
            ("1/x²  →  ∞",       "1/x**2",          "oo"),
            ("(x²−1)/(x−1) → 1", "(x**2-1)/(x-1)", "1"),
        ]:
            ctk.CTkButton(self.frame_controles, text=texto, height=28,
                          font=ctk.CTkFont(size=11), fg_color="#2b2b2b", hover_color="#3d3d3d",
                          command=lambda f=func, hv=h: self._cargar_ejemplo(f, hv)
                          ).pack(fill="x", padx=22, pady=2)

        ctk.CTkFrame(self.frame_controles, height=2, fg_color="#3a3a3a").pack(fill="x", padx=20, pady=16)

        self.btn_calcular = ctk.CTkButton(self.frame_controles, text="▶  Calcular y Graficar",
                                          height=42, font=ctk.CTkFont(size=14, weight="bold"),
                                          command=self.calcular_limite_y_graficar)
        self.btn_calcular.pack(fill="x", padx=22)

        ctk.CTkFrame(self.frame_controles, height=2, fg_color="#3a3a3a").pack(fill="x", padx=20, pady=(8, 6))
        ctk.CTkLabel(self.frame_controles, text=" Definir f(h) en el punto:",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=22)
        ctk.CTkLabel(self.frame_controles, text="Escribe el valor y márcalo en el gráfico",
                     font=ctk.CTkFont(size=10), text_color="gray", wraplength=270).pack(anchor="w", padx=22, pady=(2, 6))

        self.entry_definir = ctk.CTkEntry(self.frame_controles,
                                          placeholder_text="Ej: 2   |   0   |   -1", height=34)
        self.entry_definir.pack(fill="x", padx=22, pady=(0, 6))

        self.btn_definir = ctk.CTkButton(self.frame_controles, text="▶  Marcar en el gráfico",
                                         height=34, font=ctk.CTkFont(size=12),
                                         fg_color="#1a5276", hover_color="#1f618d",
                                         state="disabled", command=self._definir_limite_manual)
        self.btn_definir.pack(fill="x", padx=22)

        self.label_verificacion = ctk.CTkLabel(self.frame_controles, text="",
                                               font=ctk.CTkFont(size=11), wraplength=270, justify="left")
        self.label_verificacion.pack(anchor="w", padx=22, pady=(2, 0))

        self._punto_limite_x = self._punto_limite_y = self._limite_correcto = None

        self.label_resultado = ctk.CTkLabel(self.frame_controles, text="Resultado: —",
                                            font=ctk.CTkFont(size=13, weight="bold"),
                                            wraplength=270, justify="left")
        self.label_resultado.pack(pady=6, padx=22, anchor="w")

        ctk.CTkLabel(self.frame_controles, text="Historial:",
                     font=ctk.CTkFont(size=11), text_color="gray").pack(anchor="w", padx=22)
        self.textbox_historial = ctk.CTkTextbox(self.frame_controles, height=70,
                                                font=ctk.CTkFont(size=11), state="disabled")
        self.textbox_historial.pack(fill="x", padx=22, pady=(4, 6))
        ctk.CTkButton(self.frame_controles, text="Limpiar historial", height=26,
                      font=ctk.CTkFont(size=11), fg_color="#2b2b2b", hover_color="#3d3d3d",
                      command=self._limpiar_historial).pack(padx=22, anchor="w")

        # ── Panel derecho ──
        self.frame_derecho = ctk.CTkFrame(self, corner_radius=12, fg_color="transparent")
        self.frame_derecho.grid(row=0, column=1, sticky="nsew", padx=(0, 12), pady=12)
        self.frame_derecho.grid_rowconfigure(0, weight=3)
        self.frame_derecho.grid_rowconfigure(1, weight=2)
        self.frame_derecho.grid_columnconfigure(0, weight=1)

        self.frame_grafico = ctk.CTkFrame(self.frame_derecho, corner_radius=12)
        self.frame_grafico.grid(row=0, column=0, sticky="nsew", pady=(0, 6))
        plt.style.use("dark_background")
        self.fig, self.ax = plt.subplots(figsize=(6, 4), dpi=100)
        self.fig.patch.set_facecolor("#2b2b2b")
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_grafico)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        self._mostrar_grafico_inicial()

        self.frame_pasos = ctk.CTkFrame(self.frame_derecho, corner_radius=12)
        self.frame_pasos.grid(row=1, column=0, sticky="nsew", pady=(6, 0))
        ctk.CTkLabel(self.frame_pasos, text="📋  Resolución paso a paso",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=14, pady=(10, 4))
        ctk.CTkFrame(self.frame_pasos, height=2, fg_color="#3a3a3a").pack(fill="x", padx=14, pady=(0, 6))
        self.textbox_pasos = ctk.CTkTextbox(self.frame_pasos, font=ctk.CTkFont(size=12),
                                            state="disabled", fg_color="#1e1e1e", text_color="white")
        self.textbox_pasos.pack(fill="both", expand=True, padx=14, pady=(0, 10))

    def _preprocesar_expr(self, texto: str) -> str:
        import re
        s = texto.strip()
        s = re.sub(r'(\d)([a-zA-Z])', lambda m: m.group(1) + '*' + m.group(2), s)
        fns = {'sin','cos','tan','cot','sec','csc','asin','acos','atan','acot',
               'arcsin','arccos','arctan','sinh','cosh','tanh','sqrt','log','exp'}
        def fix_var_paren(m):
            return m.group(0) if m.group(1) in fns else m.group(1) + '*('
        s = re.sub(r'([a-zA-Z]+)(\()', fix_var_paren, s)
        s = re.sub(r'(\d)(\()', lambda m: m.group(1) + '*(', s)
        s = re.sub(r'\)\(', ')*(', s)
        for fn in ('sin','cos','tan','cot','sec','csc','asin','acos','atan','acot',
                   'sinh','cosh','tanh','sqrt','log','exp'):
            broken = '*'.join(fn)
            if broken in s:
                s = s.replace(broken, fn)
        return s

    def _calcular_limite_manual(self, f_expr, x, h_val):
        TRIG = (sp.sin, sp.cos, sp.tan, sp.cot, sp.sec, sp.csc,
                sp.asin, sp.acos, sp.atan, sp.sinh, sp.cosh, sp.tanh)

        def sust(expr, p):
            try:
                val = sp.simplify(expr.subs(x, p))
                if val == sp.nan: return None
                nv = complex(val)
                return None if (math.isnan(nv.real) or math.isinf(nv.real)) else val
            except Exception: return None

        def cero_en(e, p):
            try:
                v = sp.simplify(e.subs(x, p))
                return v == 0 or abs(complex(v).real) < 1e-12
            except Exception: return False

        def notable_trig(expr, p):
            num, den = sp.fraction(sp.cancel(expr))
            if not (cero_en(num, p) and cero_en(den, p)): return None
            if isinstance(num, sp.sin) and den == num.args[0]: return sp.Integer(1)
            if isinstance(den, sp.sin) and num == den.args[0]: return sp.Integer(1)
            if isinstance(num, sp.tan) and den == num.args[0]: return sp.Integer(1)
            if isinstance(den, sp.tan) and num == den.args[0]: return sp.Integer(1)
            dn = sp.expand(num)
            if dn == 1 - sp.cos(den) or dn == sp.cos(den) - 1: return sp.Integer(0)
            if isinstance(num, sp.sin) and isinstance(den, sp.sin):
                try:
                    c = sp.simplify(num.args[0] / den.args[0])
                    if c.is_number: return c
                except Exception: pass
            for se, de in [(num, den), (den, num)]:
                if isinstance(se, sp.sin):
                    try:
                        c = sp.simplify(se.args[0] / de)
                        if c.is_number:
                            return sp.simplify(c if se is num else 1/c)
                    except Exception: pass
            return None

        def al_infinito(expr, signo):
            try:
                if expr.is_rational_function(x):
                    num, den = sp.fraction(sp.cancel(expr))
                    gn = sp.degree(sp.Poly(num, x)); gd = sp.degree(sp.Poly(den, x))
                    lc_n = sp.LC(sp.Poly(num, x));  lc_d = sp.LC(sp.Poly(den, x))
                    if gn < gd: return sp.Integer(0)
                    if gn == gd: return sp.simplify(lc_n / lc_d)
                    val = float(sp.simplify(lc_n / lc_d)) * signo
                    return sp.oo if val > 0 else -sp.oo
            except Exception: pass
            try:
                val = float(expr.subs(x, 1e6 * signo).evalf())
                return (sp.oo if val > 0 else -sp.oo) if math.isinf(val) else sp.Float(round(val, 6))
            except Exception: return sp.nan

        def aprox_numerica(expr, p):
            try: hf = float(p)
            except Exception: return sp.nan
            fn = sp.lambdify(x, expr, modules=['math'])
            from fractions import Fraction
            for d in [1e-4, 1e-6, 1e-8]:
                try:
                    iz, de = fn(hf - d), fn(hf + d)
                    if all(not math.isnan(v) and not math.isinf(v) for v in [iz, de]):
                        if abs(iz - de) < 1e-4:
                            prom = (iz + de) / 2
                            r = round(prom)
                            if abs(prom - r) < 1e-5: return sp.Integer(r)
                            frac = Fraction(prom).limit_denominator(100)
                            if abs(float(frac) - prom) < 1e-5:
                                return sp.Rational(frac.numerator, frac.denominator)
                            return sp.Float(round(prom, 6))
                except Exception: continue
            return sp.nan

        if h_val == sp.oo:  return al_infinito(f_expr,  1)
        if h_val == -sp.oo: return al_infinito(f_expr, -1)
        r = sust(f_expr, h_val)
        if r is not None: return r
        if f_expr.has(*TRIG):
            r = notable_trig(f_expr, h_val)
            if r is not None: return r
        for fn in [sp.simplify, lambda e: sp.cancel(sp.factor(e))]:
            try:
                r = sust(fn(f_expr), h_val)
                if r is not None: return r
            except Exception: pass
        return aprox_numerica(f_expr, h_val) or sp.nan

    def _generar_pasos(self, f_expr, h_val, h_str, limite_resultado):
        x = sp.Symbol('x')
        TRIG = (sp.sin, sp.cos, sp.tan, sp.cot, sp.sec, sp.csc,
                sp.asin, sp.acos, sp.atan, sp.sinh, sp.cosh, sp.tanh)
        es_trig = lambda e: e.has(*TRIG)

        def cero_en(e, p):
            try:
                v = sp.simplify(e.subs(x, p))
                return v == 0 or abs(complex(v).real) < 1e-12
            except Exception: return False

        pasos = [f"f(x) = {f_expr}", f"x → {h_str}", "─" * 40]

        if h_val in (sp.oo, -sp.oo):
            signo = "+" if h_val == sp.oo else "−"
            pasos.append(f"Tipo: Límite al {signo}∞")
            if f_expr.is_rational_function(x):
                num, den = sp.fraction(sp.cancel(f_expr))
                gn = sp.degree(sp.Poly(num, x)); gd = sp.degree(sp.Poly(den, x))
                lc_n = sp.LC(sp.Poly(num, x));  lc_d = sp.LC(sp.Poly(den, x))
                pasos.append(f"  Num: {num}  (grado {gn})   Den: {den}  (grado {gd})")
                if gn < gd:    pasos.append("  grado num < grado den → límite = 0")
                elif gn == gd: pasos.append(f"  grado num = grado den → cociente líderes: {lc_n}/{lc_d} = {sp.simplify(lc_n/lc_d)}")
                else:          pasos.append("  grado num > grado den → límite = ±∞")
            elif es_trig(f_expr): pasos.append("  sin/cos oscilan entre -1 y 1 → el límite depende del contexto.")
            else:                 pasos.append("  Se analiza el término dominante.")
        else:
            if es_trig(f_expr):
                pasos.append("Tipo: Límite trigonométrico")
                pasos.append("Paso 1: Sustitución directa")
                try:
                    vd = sp.simplify(f_expr.subs(x, h_val))
                    nv = complex(vd).real
                    if not math.isnan(nv) and not math.isinf(nv):
                        pasos.append(f"  f({h_str}) = {vd}  ✔ No hay indeterminación.")
                    else: raise ValueError()
                except Exception:
                    pasos.append(f"  f({h_str}) → indeterminación 0/0")
                    pasos.append("Paso 2: Límite notable trigonométrico")
                    num_e, den_e = sp.fraction(sp.cancel(f_expr))
                    if isinstance(num_e, sp.sin) and cero_en(num_e.args[0], h_val):
                        arg = num_e.args[0]
                        if sp.simplify(arg - den_e) == 0:
                            pasos += [f"  Forma sin(u)/u  con u = {arg} → 0", "  lím sin(u)/u = 1  (límite notable)"]
                        else:
                            c = sp.simplify(arg / den_e)
                            pasos += [f"  sin({arg})/({den_e}) = [sin({arg})/{arg}] · [{arg}/({den_e})]", f"  → 1 · {c} = {c}"]
                    elif isinstance(den_e, sp.sin) and cero_en(den_e.args[0], h_val):
                        pasos.append("  Forma u/sin(u) → lím = 1  (límite notable)")
                    elif isinstance(num_e, sp.tan) and cero_en(num_e.args[0], h_val):
                        arg = num_e.args[0]
                        if sp.simplify(arg - den_e) == 0:
                            pasos += [f"  Forma tan(u)/u  con u = {arg} → 0",
                                      "  tan(u)/u = [sin(u)/u]·[1/cos(u)] → 1·1 = 1"]
                    elif cero_en(num_e, h_val) and cero_en(den_e, h_val):
                        dn = sp.expand(num_e)
                        if sp.simplify(dn - (1 - sp.cos(den_e))) == 0:
                            pasos += [f"  Forma (1-cos(u))/u  con u = {den_e} → 0",
                                      "  lím (1-cos(u))/u = 0  (límite notable)"]
                        else:
                            fs = sp.trigsimp(f_expr)
                            pasos.append(f"  Simplificación trig: {fs}")
                            try: pasos.append(f"  f({h_str}) = {sp.simplify(fs.subs(x, h_val))}")
                            except Exception: pass
                    else:
                        fs = sp.trigsimp(f_expr)
                        pasos.append(f"  Simplificación trig: {fs}")
                        try: pasos.append(f"  f({h_str}) = {sp.simplify(fs.subs(x, h_val))}")
                        except Exception: pasos.append(f"  → Resultado: {limite_resultado}")
            else:
                pasos.append("Tipo: Límite algebraico")
                pasos.append("Paso 1: Sustitución directa")
                try:
                    vd = sp.simplify(f_expr.subs(x, h_val))
                    nv = complex(vd).real
                    if not math.isnan(nv) and not math.isinf(nv):
                        pasos.append(f"  f({h_str}) = {vd}  ✔ No hay indeterminación.")
                    else: raise ValueError()
                except Exception:
                    pasos.append(f"  f({h_str}) → indeterminación")
                    pasos.append("Paso 2: Factorización y cancelación")
                    try:
                        ff = sp.cancel(sp.factor(f_expr))
                        if ff != f_expr:
                            pasos.append(f"  f(x) = {sp.factor(f_expr)}")
                            if ff != sp.factor(f_expr): pasos.append(f"  Cancelando: {ff}")
                            pasos.append(f"  f({h_str}) = {sp.simplify(ff.subs(x, h_val))}")
                        else: raise ValueError()
                    except Exception:
                        fs = sp.simplify(f_expr)
                        if fs != f_expr:
                            pasos.append(f"  Simplificando: {fs}")
                            try: pasos.append(f"  f({h_str}) = {sp.simplify(fs.subs(x, h_val))}")
                            except Exception: pass
                        else:
                            pasos.append(f"  → Aproximación numérica: {limite_resultado}")

        pasos += ["─" * 40, f"  lím f(x) = {limite_resultado}   (x → {h_str})", "─" * 40]
        return pasos

    def calcular_limite_y_graficar(self):
        self.ax.clear()
        self.label_resultado.configure(text="Resultado: Calculando...", text_color="white")
        self._actualizar_pasos([" Calculando..."])
        self.update_idletasks()

        func_str = self.entry_func.get().strip()
        h_str    = self.entry_h.get().strip()
        if not func_str or not h_str:
            self.label_resultado.configure(text=" Complete ambos campos.", text_color="#FF6B6B")
            self._mostrar_grafico_inicial()
            self._actualizar_pasos([" Complete ambos campos."])
            return

        try:
            x = sp.Symbol('x')
            trig_map = {
                'sin': sp.sin, 'cos': sp.cos, 'tan': sp.tan,
                'cot': sp.cot, 'sec': sp.sec, 'csc': sp.csc,
                'asin': sp.asin, 'arcsin': sp.asin, 'acos': sp.acos, 'arccos': sp.acos,
                'atan': sp.atan, 'arctan': sp.atan, 'acot': sp.acot, 'arccot': sp.acot,
                'sinh': sp.sinh, 'cosh': sp.cosh, 'tanh': sp.tanh,
                'exp': sp.exp, 'log': sp.log, 'sqrt': sp.sqrt, 'pi': sp.pi, 'e': sp.E,
            }
            func_str = self._preprocesar_expr(func_str)
            f_expr = sp.sympify(func_str, locals=trig_map)

            if h_str.lower() in ['oo', 'inf', '+oo', 'infinito', '+inf']:   h_val = sp.oo
            elif h_str.lower() in ['-oo', '-inf', '-infinito']:              h_val = -sp.oo
            else:                                                             h_val = sp.sympify(h_str, locals=trig_map)

            limite_resultado = self._calcular_limite_manual(f_expr, x, h_val)
            self.label_resultado.configure(text=f"lím f(x) = {limite_resultado}", text_color="#4FC3F7")
            self._agregar_historial(func_str, h_str, limite_resultado)
            self._actualizar_pasos(self._generar_pasos(f_expr, h_val, h_str, limite_resultado))

            if h_val == sp.oo:    x_min, x_max = 0, 50
            elif h_val == -sp.oo: x_min, x_max = -50, 0
            else:                 h_float = float(h_val); x_min, x_max = h_float - 8, h_float + 8

            paso = (x_max - x_min) / 600
            x_vals = [x_min + i * paso for i in range(601)]
            f_num  = sp.lambdify(x, f_expr, modules=['math'])
            y_vals = []
            for val in x_vals:
                try:
                    y = f_num(val)
                    y_vals.append(None if (isinstance(y, complex) or math.isinf(y) or math.isnan(y)) else y)
                except Exception: y_vals.append(None)

            y_ok = [v for v in y_vals if v is not None]
            if y_ok:
                y_med = sum(y_ok) / len(y_ok)
                margen = max((max(y_ok) - min(y_ok)) * 0.6, 5)
                self.ax.set_ylim(y_med - margen, y_med + margen)

            self.ax.plot(x_vals, y_vals, color='#4FC3F7', linewidth=2, label=f'f(x) = {f_expr}')

            if not h_val.is_infinite:
                self.ax.axvline(x=float(h_val), color='#FF8A65', linestyle='--',
                                linewidth=1.4, label=f'x → {float(h_val):.2f}')

            if limite_resultado.is_real and not limite_resultado.is_infinite:
                lim_float = float(limite_resultado)
                if h_val.is_infinite:
                    self.ax.axhline(y=lim_float, color='#A5D6A7', linestyle=':',
                                    linewidth=1.4, label=f'Límite = {lim_float:.4f}')
                else:
                    self._punto_limite_x = float(h_val)
                    self._punto_limite_y = lim_float
                    self._punto_rellenado = False
                    try:
                        val_d = float(sp.simplify(f_expr.subs(sp.Symbol('x'), h_val)))
                        hay_hueco = math.isnan(val_d) or math.isinf(val_d)
                    except Exception: hay_hueco = True
                    if hay_hueco:
                        self.ax.plot(float(h_val), lim_float, 'o', color='#FF5252', markersize=12,
                                     markerfacecolor='#1e1e1e', markeredgewidth=2.5, zorder=5,
                                     label=f'Límite = {lim_float:.4f} (punto removible)')
                    else:
                        self.ax.plot(float(h_val), lim_float, 'o', color='#FF5252',
                                     markersize=9, zorder=5, label=f'Límite = {lim_float:.4f}')
                    self.btn_definir.configure(state="normal")
                    self._limite_correcto = lim_float
            elif limite_resultado.is_infinite:
                self.ax.text(0.04, 0.94, f'Límite = {limite_resultado}',
                             transform=self.ax.transAxes, color='#FFEB3B', fontsize=11, verticalalignment='top')

            self.ax.set_facecolor("#1e1e1e")
            self.ax.set_title("Comportamiento de la función", color="white", fontsize=13)
            self.ax.set_xlabel("x", color="white"); self.ax.set_ylabel("f(x)", color="white")
            self.ax.tick_params(colors="white")
            self.ax.grid(True, linestyle='--', alpha=0.3, color='gray')
            self.ax.legend(fontsize=9, facecolor="#2b2b2b", labelcolor="white")
            self.canvas.draw()

        except sp.SympifyError:
            self.label_resultado.configure(text=" Expresión inválida.\nRevisa la sintaxis.", text_color="#FF6B6B")
            self._mostrar_grafico_inicial()
            self._actualizar_pasos(["Expresión inválida. Revisa la sintaxis."])
        except Exception as e:
            self.label_resultado.configure(text=f"Error: {str(e)}", text_color="#FF6B6B")
            self._mostrar_grafico_inicial()
            self._actualizar_pasos([f"Error: {str(e)}"])

    def _actualizar_pasos(self, lista_pasos):
        self.textbox_pasos.configure(state="normal")
        self.textbox_pasos.delete("1.0", "end")
        for linea in lista_pasos:
            self.textbox_pasos.insert("end", linea + "\n")
        self.textbox_pasos.configure(state="disabled")

    def _definir_limite_manual(self):
        if self._punto_limite_x is None: return
        valor_str = self.entry_definir.get().strip()
        if not valor_str:
            self.label_verificacion.configure(text=" Escribe un valor primero.", text_color="#FF6B6B")
            return
        try:
            valor_ingresado = float(eval(valor_str, {"__builtins__": {}}, {
                "pi": math.pi, "e": math.e, "sin": math.sin, "cos": math.cos,
                "tan": math.tan, "sqrt": math.sqrt, "log": math.log, "exp": math.exp,
            }))
        except Exception:
            self.label_verificacion.configure(text="⚠ Valor inválido.", text_color="#FF6B6B")
            return

        # Color del punto según proximidad al límite real
        if self._limite_correcto is not None:
            diferencia = abs(valor_ingresado - self._limite_correcto)
            if diferencia < 0.01:   color_punto = '#A5D6A7'   # verde
            elif diferencia < 0.5:  color_punto = '#FFD54F'   # amarillo
            else:                   color_punto = '#FF6B6B'   # rojo
        else:
            color_punto = '#A5D6A7'

        self.ax.plot(self._punto_limite_x, valor_ingresado, 's', color=color_punto,
                     markersize=11, markerfacecolor=color_punto, markeredgecolor='white',
                     markeredgewidth=1.5, zorder=7, label=f'f(h) definida = {valor_ingresado}')
        self.ax.annotate(f'  f(h) = {valor_ingresado}',
                         xy=(self._punto_limite_x, valor_ingresado), color=color_punto, fontsize=10)
        self.canvas.draw()

        if self._limite_correcto is not None:
            if diferencia < 0.01:
                self.label_verificacion.configure(
                    text=f"✔ ¡Correcto! f(h) = {valor_ingresado} coincide con el límite.", text_color="#A5D6A7")
            elif diferencia < 0.5:
                self.label_verificacion.configure(
                    text=f"⚠ Casi. El límite real es {self._limite_correcto:.4f}, tu valor se aleja en {diferencia:.4f}.",
                    text_color="#FFD54F")
            else:
                self.label_verificacion.configure(
                    text=f"✗ Incorrecto. El límite real es {self._limite_correcto}, no {valor_ingresado}.",
                    text_color="#FF6B6B")

    def _cargar_ejemplo(self, func: str, h: str):
        self.entry_func.delete(0, "end"); self.entry_func.insert(0, func)
        self.entry_h.delete(0, "end");   self.entry_h.insert(0, h)

    def _agregar_historial(self, func: str, h: str, resultado):
        self.textbox_historial.configure(state="normal")
        self.textbox_historial.insert("end", f"lím({func}, {h}) = {resultado}\n")
        self.textbox_historial.see("end")
        self.textbox_historial.configure(state="disabled")

    def _limpiar_historial(self):
        self.textbox_historial.configure(state="normal")
        self.textbox_historial.delete("1.0", "end")
        self.textbox_historial.configure(state="disabled")

    def _mostrar_grafico_inicial(self):
        self.ax.clear()
        self.ax.set_facecolor("#1e1e1e")
        self.ax.set_title("Ingresa una función y presiona Calcular", color="gray", fontsize=11)
        self.ax.set_xlabel("x", color="white"); self.ax.set_ylabel("f(x)", color="white")
        self.ax.tick_params(colors="white")
        self.ax.grid(True, linestyle='--', alpha=0.3, color='gray')
        self.canvas.draw()

    def on_closing(self):
        try:
            for after_id in self.tk.call('after', 'info').split():
                try: self.after_cancel(after_id)
                except Exception: pass
        except Exception: pass
        try: plt.close('all')
        except Exception: pass
        try: self.destroy()
        except Exception: pass


# ════════════════════════════════════════════════════════════════
class CalculadoraTrigExtendida(CalculadoraLimitesApp):
    TRIG_FNS = (sp.sin, sp.cos, sp.tan, sp.cot, sp.sec, sp.csc,
                sp.asin, sp.acos, sp.atan, sp.acot, sp.sinh, sp.cosh, sp.tanh)

    def __init__(self):
        super().__init__()
        self.title("Analizador y Visualizador de Límites · MATE1133  [+Trig]")
        self._agregar_ejemplos_trig()

    def _agregar_ejemplos_trig(self):
        ctk.CTkFrame(self.frame_controles, height=2, fg_color="#3a3a3a").pack(fill="x", padx=20, pady=(10, 6))
        ctk.CTkLabel(self.frame_controles, text="📐 Ejemplos trigonométricos:",
                     font=ctk.CTkFont(size=11, weight="bold"), text_color="#4FC3F7").pack(anchor="w", padx=22)
        for texto, func, h in [
            ("sin(2x)/x  →  0",        "sin(2*x)/x",         "0"),
            ("tan(3x)/(5x)  →  0",     "tan(3*x)/(5*x)",     "0"),
            ("(1-cos(x))/x²  →  0",    "(1-cos(x))/x**2",    "0"),
            ("sin²(x)/x²  →  0",       "sin(x)**2/x**2",     "0"),
            ("sin(x)/tan(x)  →  0",    "sin(x)/tan(x)",      "0"),
            ("(cos(x)-1)/sin(x) → 0",  "(cos(x)-1)/sin(x)",  "0"),
            ("x·sin(1/x)  →  ∞",       "x*sin(1/x)",         "oo"),
        ]:
            ctk.CTkButton(self.frame_controles, text=texto, height=28,
                          font=ctk.CTkFont(size=11), fg_color="#1a3a4a", hover_color="#1f5270",
                          command=lambda f=func, hv=h: self._cargar_ejemplo(f, hv)
                          ).pack(fill="x", padx=22, pady=2)

    def _resolver_trig_notable(self, expr, x, p):
        expr_c = sp.cancel(expr)
        num, den = sp.fraction(expr_c)

        def cero(e):
            try:
                v = sp.simplify(e.subs(x, p))
                return v == 0 or abs(complex(v).real) < 1e-12
            except Exception: return False

        if isinstance(num, sp.sin) and cero(num) and cero(den):
            try:
                c = sp.simplify(num.args[0] / den)
                if c.is_number: return c, f"Forma sin(ax)/(bx): cociente = {c}"
            except Exception: pass

        if isinstance(den, sp.sin) and cero(den) and cero(num):
            try:
                c = sp.simplify(num / den.args[0])
                if c.is_number: return c, f"Forma (ax)/sin(bx): cociente = {c}"
            except Exception: pass

        if isinstance(num, sp.tan) and cero(num) and cero(den):
            try:
                c = sp.simplify(num.args[0] / den)
                if c.is_number: return c, f"Forma tan(ax)/(bx): cociente = {c}"
            except Exception: pass

        num_exp = sp.expand(num)
        if cero(den):
            try: grado_den = sp.degree(sp.Poly(den, x))
            except Exception: grado_den = 1
            if grado_den == 1:
                for cos_arg in [a.args[0] for a in num_exp.atoms(sp.cos)]:
                    if sp.simplify(num_exp - (1 - sp.cos(cos_arg))) == 0:
                        return sp.Integer(0), "Forma (1-cos(ax))/(bx) → 0"

        if cero(den):
            for cos_arg in [a.args[0] for a in num_exp.atoms(sp.cos)]:
                if sp.simplify(num_exp - (1 - sp.cos(cos_arg))) == 0:
                    try:
                        c2 = sp.simplify(sp.expand(den) / x**2)
                        if c2.is_number and c2 != 0:
                            a_coef = sp.simplify(cos_arg / x)
                            if a_coef.is_number:
                                res = sp.Rational(1, 2) * a_coef**2 / c2
                                return res, f"Forma (1-cos(ax))/(bx²) → {res}"
                    except Exception: pass

        if num.is_Pow and isinstance(num.base, sp.sin) and num.exp == 2:
            if cero(num.base) and cero(den):
                try:
                    c2 = sp.simplify(num.base.args[0]**2 / den)
                    if c2.is_number: return c2, f"Forma sin²(ax)/(bx²) → {c2}"
                except Exception: pass

        fs = sp.trigsimp(expr)
        if fs != expr:
            try:
                v = sp.simplify(fs.subs(x, p))
                nv = complex(v).real
                if not math.isnan(nv) and not math.isinf(nv):
                    return v, f"Simplificación trigonométrica: f(x) = {fs}"
            except Exception: pass

        try:
            n_iter, d_iter, pasos_lh = num, den, []
            for iteration in range(1, 4):
                n_iter = sp.diff(n_iter, x); d_iter = sp.diff(d_iter, x)
                cociente_lh = sp.cancel(n_iter / d_iter)
                pasos_lh.append(f"  Iter {iteration}: {n_iter} / {d_iter} = {cociente_lh}")
                try:
                    v = sp.simplify(cociente_lh.subs(x, p))
                    nv = complex(v).real
                    if not math.isnan(nv) and not math.isinf(nv):
                        desc = (f"L'Hôpital (x{iteration}): 0/0 → aplicar regla\n"
                                + "\n".join(pasos_lh) + f"\n  → resultado = {v}")
                        return v, desc
                except Exception: pass
        except Exception: pass
        return None, None

    def _calcular_limite_manual(self, f_expr, x, h_val):
        resultado_base = super()._calcular_limite_manual(f_expr, x, h_val)
        if resultado_base is not sp.nan and resultado_base != sp.nan:
            return resultado_base
        if f_expr.has(*self.TRIG_FNS) and h_val not in (sp.oo, -sp.oo):
            r, _ = self._resolver_trig_notable(f_expr, x, h_val)
            if r is not None: return r
        try:
            r_sp = sp.limit(f_expr, x, h_val)
            if r_sp is not sp.nan: return r_sp
        except Exception: pass
        return sp.nan

    def _generar_pasos(self, f_expr, h_val, h_str, limite_resultado):
        pasos = super()._generar_pasos(f_expr, h_val, h_str, limite_resultado)
        if f_expr.has(*self.TRIG_FNS) and h_val not in (sp.oo, -sp.oo):
            x = sp.Symbol('x')
            try:
                vd = sp.simplify(f_expr.subs(x, h_val))
                hay_indet = math.isnan(complex(vd).real) or math.isinf(complex(vd).real)
            except Exception: hay_indet = True
            if hay_indet:
                _, descripcion = self._resolver_trig_notable(f_expr, x, h_val)
                if descripcion:
                    idx = max(len(pasos) - 3, 0)
                    extras = ["", "── Resolución trigonométrica extendida ──"]
                    extras += [f"  {l}" for l in descripcion.split("\n")]
                    for i, linea in enumerate(extras):
                        pasos.insert(idx + i, linea)
        return pasos


# ════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = CalculadoraTrigExtendida()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
