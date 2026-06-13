import re, math
from fractions import Fraction
import customtkinter as ctk
import sympy as sp
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from sympy.calculus.accumulationbounds import AccumulationBounds

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

x = sp.Symbol('x')
TRIG = (sp.sin, sp.cos, sp.tan, sp.cot, sp.sec, sp.csc,
        sp.asin, sp.acos, sp.atan, sp.acot, sp.sinh, sp.cosh, sp.tanh)
TRIG_MAP = {
    'sin': sp.sin, 'cos': sp.cos, 'tan': sp.tan, 'cot': sp.cot,
    'sec': sp.sec, 'csc': sp.csc, 'asin': sp.asin, 'arcsin': sp.asin,
    'acos': sp.acos, 'arccos': sp.acos, 'atan': sp.atan, 'arctan': sp.atan,
    'acot': sp.acot, 'arccot': sp.acot, 'sinh': sp.sinh, 'cosh': sp.cosh,
    'tanh': sp.tanh, 'exp': sp.exp, 'log': sp.log, 'sqrt': sp.sqrt,
    'pi': sp.pi, 'e': sp.E,
}
MATH_ENV = {"__builtins__": {}, "pi": math.pi, "e": math.e,
            "sin": math.sin, "cos": math.cos, "tan": math.tan,
            "sqrt": math.sqrt, "log": math.log, "exp": math.exp}

# ── Utilidades numéricas / simbólicas ──────────────────────────────────────────

def _es_valido(v):
    if v is None or v is sp.nan or isinstance(v, AccumulationBounds): return False
    try: return not (math.isnan(complex(v).real) or math.isinf(complex(v).real))
    except: return False

def _es_inf(v):
    return (not isinstance(v, AccumulationBounds)) and v in (sp.oo, -sp.oo)

def _sust(expr, p):
    try:
        val = sp.simplify(expr.subs(x, p))
        nv = complex(val)
        return None if (math.isnan(nv.real) or math.isinf(nv.real)) else val
    except: return None

def _cero_en(e, p):
    try: return abs(complex(sp.simplify(e.subs(x, p))).real) < 1e-12
    except: return False

def _notable_trig(expr, p):
    num, den = sp.fraction(sp.cancel(expr))
    if not (_cero_en(num, p) and _cero_en(den, p)): return None
    for fn in (sp.sin, sp.tan):
        if isinstance(num, fn) and den == num.args[0]: return sp.Integer(1)
        if isinstance(den, fn) and num == den.args[0]: return sp.Integer(1)
    dn = sp.expand(num)
    if dn in (1 - sp.cos(den), sp.cos(den) - 1): return sp.Integer(0)
    if isinstance(num, sp.sin) and isinstance(den, sp.sin):
        try:
            c = sp.simplify(num.args[0] / den.args[0])
            if c.is_number: return c
        except: pass
    for se, de in [(num, den), (den, num)]:
        if isinstance(se, sp.sin):
            try:
                c = sp.simplify(se.args[0] / de)
                if c.is_number: return sp.simplify(c if se is num else 1/c)
            except: pass
    return None

def _aprox_num(expr, p):
    try: hf = float(p)
    except: return sp.nan
    fn = sp.lambdify(x, expr, modules=['math'])
    def muestras(lado):
        pts = []
        for k in [1, 2, 3]:
            try:
                v = fn(hf + lado * 1e-6 * k)
                if not (math.isnan(v) or math.isinf(v)): pts.append(v)
            except: pass
        return pts
    for d_exp in [4, 6, 8]:
        d = 10**(-d_exp)
        iz = [fn(hf - d*k) for k in [1,2,3] if _safe_float(fn, hf - d*k)]
        de = [fn(hf + d*k) for k in [1,2,3] if _safe_float(fn, hf + d*k)]
        if not iz or not de: continue
        if max(iz)-min(iz) > 1e-3 or max(de)-min(de) > 1e-3: return sp.nan
        if abs(iz[-1] - de[-1]) > 1e-4: return sp.nan
        prom = (iz[-1] + de[-1]) / 2
        r = round(prom)
        if abs(prom - r) < 1e-5: return sp.Integer(r)
        frac = Fraction(prom).limit_denominator(100)
        if abs(float(frac) - prom) < 1e-5: return sp.Rational(frac.numerator, frac.denominator)
        return sp.Float(round(prom, 6))
    return sp.nan

def _safe_float(fn, val):
    try: v = fn(val); return not (math.isnan(v) or math.isinf(v))
    except: return False

def _lateral(expr, p, dir):
    # Aproxima el límite lateral evaluando la función en tres puntos
    # cada vez más cercanos a h (pasos: 1e-7, 2e-7, 3e-7) desde el lado
    # indicado ('+' = derecha, '-' = izquierda).
    # Se toma el valor más próximo a h (k=3) como mejor aproximación.
    # Luego se intenta expresar el resultado como entero, fracción exacta
    # o decimal de 6 cifras, en ese orden de precisión.
    try:
        hf = float(p)
    except:
        return sp.nan
    sign = 1 if dir == '+' else -1
    fn = sp.lambdify(x, expr, modules=['math'])
    vals = []
    for k in [1, 2, 3]:   # tres puntos: cada uno más cerca de h que el anterior
        try:
            v = fn(hf + sign * 1e-7 * k)
            if not (math.isnan(v) or math.isinf(v)):
                vals.append(v)
        except:
            pass
    if not vals:
        return sp.nan
    prom = vals[-1]   # usar el punto más cercano a h
    r = round(prom)
    if abs(prom - r) < 1e-5:          # ¿es un entero?
        return sp.Integer(r)
    frac = Fraction(prom).limit_denominator(100)
    if abs(float(frac) - prom) < 1e-5:  # ¿es una fracción simple?
        return sp.Rational(frac.numerator, frac.denominator)
    return sp.Float(round(prom, 6))     # decimal de 6 cifras


# ── Motor de cálculo principal ─────────────────────────────────────────────────

def calcular_limite(f_expr, h_val):
    """Devuelve el límite analítico. sp.nan → no existe."""
    # ±∞
    if h_val in (sp.oo, -sp.oo):
        s = 1 if h_val == sp.oo else -1
        if f_expr.is_rational_function(x):
            num, den = sp.fraction(sp.cancel(f_expr))
            gn, gd = sp.degree(sp.Poly(num,x)), sp.degree(sp.Poly(den,x))
            lc = sp.LC(sp.Poly(num,x)) / sp.LC(sp.Poly(den,x))
            if gn < gd: return sp.Integer(0)
            if gn == gd: return sp.simplify(lc)
            return sp.oo if float(sp.simplify(lc))*s > 0 else -sp.oo
        try:
            val = float(f_expr.subs(x, 1e6*s).evalf())
            return (sp.oo if val > 0 else -sp.oo) if math.isinf(val) else sp.Float(round(val,6))
        except: return sp.nan

    # [1] Analítico primario: límites laterales bilaterales
    ld, li = _lateral(f_expr, h_val, '+'), _lateral(f_expr, h_val, '-')
    ok_d, ok_i = _es_valido(ld) or _es_inf(ld), _es_valido(li) or _es_inf(li)
    if ok_d and ok_i:
        if ld == li: return ld
        try:
            if abs(float(sp.simplify(ld-li).evalf())) < 1e-8: return ld
        except: pass
        if sp.simplify(ld-li) == 0: return ld
        return sp.nan
    if ok_d: return ld
    if ok_i: return li

    # [2] Analítico secundario: sustitución / límites notables / factorización
    r = _sust(f_expr, h_val)
    if r is not None: return r
    if f_expr.has(*TRIG):
        r = _notable_trig(f_expr, h_val)
        if r is not None: return r
    for tr in [sp.simplify, lambda e: sp.cancel(sp.factor(e))]:
        try:
            r = _sust(tr(f_expr), h_val)
            if r is not None: return r
        except: pass

    # [3] Respaldo numérico bilateral
    return _aprox_num(f_expr, h_val)


def _es_nan(v):
    return v is sp.nan or v == sp.nan


# ── Generador de pasos ─────────────────────────────────────────────────────────

def generar_pasos(f_expr, h_val, h_str, res):
    no_existe = _es_nan(res)
    sep = "─" * 40
    P = [f"f(x) = {f_expr}", f"x → {h_str}", sep]

    if h_val in (sp.oo, -sp.oo):
        sig = "+" if h_val == sp.oo else "−"
        P.append(f"Tipo: Límite al {sig}∞  [analítico primario: término dominante]")
        if f_expr.is_rational_function(x):
            try:
                num, den = sp.fraction(sp.cancel(f_expr))
                gn, gd = sp.degree(sp.Poly(num,x)), sp.degree(sp.Poly(den,x))
                lc_n, lc_d = sp.LC(sp.Poly(num,x)), sp.LC(sp.Poly(den,x))
                P.append(f"  Num (gr.{gn}): {num}  |  Den (gr.{gd}): {den}")
                if gn < gd:    P.append("  gr.num < gr.den → límite = 0")
                elif gn == gd: P.append(f"  gr.iguales → cociente líderes = {sp.simplify(lc_n/lc_d)}")
                else:          P.append("  gr.num > gr.den → límite = ±∞")
            except: P.append("  Se analiza el término dominante.")
        else:
            P.append("  Se analiza el término dominante en ±∞.")
    else:
        P.append("Tipo: Límite " + ("trigonométrico" if f_expr.has(*TRIG) else "algebraico"))

        # ── Estrategia 1: Límites laterales ───────────────────────────────────
        P.append("")
        P.append("Estrategia 1 — Límites laterales (condición de existencia)")
        P.append("  Propiedad: lím f(x) existe  ⟺  lím⁺ f(x) = lím⁻ f(x)")
        try:
            ld = _lateral(f_expr, h_val, '+')
            li = _lateral(f_expr, h_val, '-')
            def _fmt(v): return "no converge" if isinstance(v, AccumulationBounds) else str(v)
            ld_nan = _es_nan(ld) or isinstance(ld, AccumulationBounds)
            li_nan = _es_nan(li) or isinstance(li, AccumulationBounds)
            P += [f"  lím⁺ = {_fmt(ld)}", f"  lím⁻ = {_fmt(li)}"]
            if not ld_nan and not li_nan and ld == li:
                P.append("  Laterales coinciden ✔ → límite existe")
            elif not ld_nan and not li_nan and ld != li:
                P.append("  Laterales DISTINTOS ✗ → discontinuidad de salto → límite NO existe")
            elif ld_nan and li_nan:
                P.append("  Ambos laterales no convergen → función oscilatoria o asíntota vertical")
            else:
                P.append("  Un lateral no converge → asíntota o discontinuidad esencial de un lado")
        except Exception as e:
            P.append(f"  Cálculo lateral no resolvió: {e}")

        # ── Estrategia 2: Sustitución directa ─────────────────────────────────
        P.append("")
        P.append("Estrategia 2 — Sustitución directa")
        P.append("  Propiedad: si f es continua en h → lím f(x) = f(h)")
        vd = _sust(f_expr, h_val)
        if vd is not None:
            P.append(f"  f({h_str}) = {vd}  ✔  (función continua en el punto)")
        else:
            P.append(f"  f({h_str}) → indeterminación → se requiere simplificación")

            if f_expr.has(*TRIG):
                # ── Estrategia 3a: Límites notables trigonométricos ────────────
                P.append("")
                P.append("Estrategia 3 — Límites notables trigonométricos")
                P.append("  Propiedad fundamental: lím[u→0] sin(u)/u = 1")
                num_e, den_e = sp.fraction(sp.cancel(f_expr))
                if isinstance(num_e, sp.sin) and _cero_en(num_e.args[0], h_val):
                    arg = num_e.args[0]
                    c = sp.simplify(arg / den_e)
                    P.append(f"  Forma: sin({arg}) / ({den_e})")
                    P.append(f"  → lím notable: {c}")
                elif isinstance(den_e, sp.sin) and _cero_en(den_e.args[0], h_val):
                    P.append("  Forma: u / sin(u)  →  inversa del notable → 1")
                elif isinstance(num_e, sp.tan) and _cero_en(num_e.args[0], h_val):
                    P.append(f"  Forma: tan({num_e.args[0]}) / ({den_e})")
                    P.append("  Propiedad: lím[u→0] tan(u)/u = 1")
                else:
                    fs = sp.cancel(sp.expand_trig(f_expr))
                    if fs != f_expr:
                        P.append(f"  Se aplica identidad trigonométrica: f(x) = {fs}")
                        r2 = _sust(fs, h_val)
                        if r2 is not None: P.append(f"  f({h_str}) = {r2}")
                    else:
                        P.append("  No se identificó notable directo → ver resolución trig extendida")
            else:
                # ── Estrategia 3b: Factorización / simplificación algebraica ──
                P.append("")
                P.append("Estrategia 3 — Factorización / simplificación algebraica")
                P.append("  Propiedad: si (x−h) es factor común → se cancela (discontinuidad removible)")
                try:
                    ff = sp.cancel(sp.factor(f_expr))
                    if ff != f_expr:
                        P.append(f"  Factorizando: {sp.factor(f_expr)}")
                        P.append(f"  Cancelando (x−{h_str}): f(x) simplificada = {ff}")
                        r2 = _sust(ff, h_val)
                        if r2 is not None: P.append(f"  Sustitución directa: f({h_str}) = {r2}")
                        else: P.append("  Simplificación no resolvió la indeterminación")
                    else: raise ValueError()
                except:
                    if no_existe:
                        P += ["  No hay factor cancelable algebraicamente.",
                              "  → Laterales distintos o función oscilatoria → límite NO existe."]
                    else:
                        P.append("  No hay factor cancelable → respaldo numérico bilateral aplicado")

        # ── Diagnóstico cuando el límite no existe ─────────────────────────────
        if no_existe:
            P.append("")
            P.append("⚠ El límite NO existe. Causa probable:")
            try:
                ld2 = _lateral(f_expr, h_val, '+')
                li2 = _lateral(f_expr, h_val, '-')
                ld2_nan = _es_nan(ld2) or isinstance(ld2, AccumulationBounds)
                li2_nan = _es_nan(li2) or isinstance(li2, AccumulationBounds)
                if not ld2_nan and not li2_nan:
                    P.append(f"  Discontinuidad de salto: lím⁺ = {ld2}  ≠  lím⁻ = {li2}")
                elif ld2_nan and li2_nan:
                    P.append("  Función oscilatoria (ej. sin(1/x)) o asíntota vertical bilateral")
                else:
                    P.append("  Asíntota vertical de un solo lado o discontinuidad esencial")
            except:
                P.append("  Laterales distintos o comportamiento no acotado cerca del punto")

    res_str = "No existe" if no_existe else str(res)
    P += [sep, f"  lím f(x) = {res_str}   (x → {h_str})", sep]
    return P


# ── Resolución trigonométrica extendida (subclase) ────────────────────────────

def _resolver_trig(expr, p):
    """Intenta resolver límites trig notables más complejos. Devuelve (val, desc) o (None, None)."""
    expr_c = sp.cancel(expr)
    num, den = sp.fraction(expr_c)
    def cero(e):
        try: return abs(complex(sp.simplify(e.subs(x, p))).real) < 1e-12
        except: return False

    for fn, lbl in [(sp.sin, "sin"), (sp.tan, "tan")]:
        if isinstance(num, fn) and cero(num) and cero(den):
            try:
                c = sp.simplify(num.args[0] / den)
                if c.is_number: return c, f"Forma {lbl}(ax)/(bx) → {c}"
            except: pass
        if isinstance(den, fn) and cero(den) and cero(num):
            try:
                c = sp.simplify(num / den.args[0])
                if c.is_number: return c, f"Forma (ax)/{lbl}(bx) → {c}"
            except: pass

    num_exp = sp.expand(num)
    for cos_arg in [a.args[0] for a in num_exp.atoms(sp.cos)]:
        if sp.simplify(num_exp - (1 - sp.cos(cos_arg))) == 0 and cero(den):
            try:
                gd = sp.degree(sp.Poly(den, x))
            except: gd = 1
            if gd == 1: return sp.Integer(0), "Forma (1-cos(ax))/(bx) → 0"
            try:
                c2 = sp.simplify(sp.expand(den) / x**2)
                a_c = sp.simplify(cos_arg / x)
                if c2.is_number and c2 != 0 and a_c.is_number:
                    res = sp.Rational(1,2) * a_c**2 / c2
                    return res, f"Forma (1-cos(ax))/(bx²) → {res}"
            except: pass

    if num.is_Pow and isinstance(num.base, sp.sin) and num.exp == 2 and cero(num.base) and cero(den):
        try:
            c2 = sp.simplify(num.base.args[0]**2 / den)
            if c2.is_number: return c2, f"Forma sin²(ax)/(bx²) → {c2}"
        except: pass

    fs = sp.cancel(sp.expand_trig(expr))
    if fs != expr:
        try:
            v = sp.simplify(fs.subs(x, p)); nv = complex(v).real
            if not (math.isnan(nv) or math.isinf(nv)):
                return v, f"Identidad trig: f(x) = {fs}"
        except: pass

    try:
        cancelado = sp.cancel(sp.factor(num) / sp.factor(den))
        if cancelado != expr:
            v = sp.simplify(cancelado.subs(x, p)); nv = complex(v).real
            if not (math.isnan(nv) or math.isinf(nv)):
                return v, f"Factorización: f(x) = {cancelado}"
    except: pass

    return None, None


# ── Preprocesador de expresiones ───────────────────────────────────────────────

def preprocesar(texto):
    FNS = {'sin','cos','tan','cot','sec','csc','asin','acos','atan','acot',
           'arcsin','arccos','arctan','sinh','cosh','tanh','sqrt','log','exp'}
    s = texto.strip()
    s = re.sub(r'(\d)([a-zA-Z])', lambda m: m.group(1)+'*'+m.group(2), s)
    s = re.sub(r'([a-zA-Z]+)(\()',
               lambda m: m.group(0) if m.group(1) in FNS else m.group(1)+'*(', s)
    s = re.sub(r'(\d)(\()', lambda m: m.group(1)+'*(', s)
    s = re.sub(r'\)\(', ')*(', s)
    for fn in FNS:
        broken = '*'.join(fn)
        if broken in s: s = s.replace(broken, fn)
    return s


# ── GUI ────────────────────────────────────────────────────────────────────────

class App(ctk.CTk):
    EJEMPLOS = [
        ("sin(x)/x  →  0",   "sin(x)/x",       "0"),
        ("x²−4  →  2",       "x**2 - 4",        "2"),
        ("1/x²  →  ∞",       "1/x**2",          "oo"),
        ("(x²−1)/(x−1) → 1", "(x**2-1)/(x-1)", "1"),
    ]
    EJEMPLOS_TRIG = [
        ("sin(2x)/x  →  0",       "sin(2*x)/x",        "0"),
        ("tan(3x)/(5x)  →  0",    "tan(3*x)/(5*x)",    "0"),
        ("(1-cos(x))/x²  →  0",   "(1-cos(x))/x**2",   "0"),
        ("sin²(x)/x²  →  0",      "sin(x)**2/x**2",    "0"),
        ("sin(x)/tan(x)  →  0",   "sin(x)/tan(x)",     "0"),
        ("(cos(x)-1)/sin(x) → 0", "(cos(x)-1)/sin(x)", "0"),
        ("x·sin(1/x)  →  ∞",      "x*sin(1/x)",        "oo"),
    ]

    def __init__(self):
        super().__init__()
        self.title("Analizador de Límites · MATE1133")
        self.geometry("1150x700"); self.minsize(950, 600)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._punto_limite_x = self._punto_limite_y = self._limite_correcto = None
        self._build_ui()

    # ── Construcción de la UI ──────────────────────────────────────────────────

    def _lbl(self, parent, text, size=12, bold=False, color=None, **kw):
        font = ctk.CTkFont(size=size, weight="bold" if bold else "normal")
        kw2 = dict(text=text, font=font)
        if color: kw2["text_color"] = color
        return ctk.CTkLabel(parent, **kw2, **kw)

    def _sep(self, parent, pady=(0,0)):
        ctk.CTkFrame(parent, height=2, fg_color="#3a3a3a").pack(fill="x", padx=20, pady=pady)

    def _btn_ejemplo(self, parent, texto, func, h, fg="#2b2b2b", hov="#3d3d3d"):
        ctk.CTkButton(parent, text=texto, height=28, font=ctk.CTkFont(size=11),
                      fg_color=fg, hover_color=hov,
                      command=lambda: self._cargar(func, h)).pack(fill="x", padx=22, pady=2)

    def _build_ui(self):
        fc = ctk.CTkFrame(self, width=320, corner_radius=12)
        fc.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        fc.grid_propagate(False)
        self.frame_controles = fc

        self._lbl(fc, " 😶‍🌫️ Calculadora de Límites", 18, bold=True).pack(pady=(22,4))
        self._lbl(fc, "MATE1133 · UCTemuco", color="gray").pack(pady=(0,18))
        self._sep(fc, pady=(0,18))

        for lbl_text, attr in [("Función  f(x):", "entry_func"), ("Tiende a  h:", "entry_h")]:
            self._lbl(fc, lbl_text, 13, bold=True).pack(anchor="w", padx=22)
            ph = ("Ej: sin(x)/x   |   x**2 - 4   |   1/x" if "func" in attr
                  else "Ej: 0   |   2   |   oo   |   -oo")
            e = ctk.CTkEntry(fc, placeholder_text=ph, height=38)
            e.pack(fill="x", padx=22, pady=(4,14))
            setattr(self, attr, e)

        self._lbl(fc, "Ejemplos rápidos:", color="gray").pack(anchor="w", padx=22)
        for t, f, h in self.EJEMPLOS:
            self._btn_ejemplo(fc, t, f, h)
        self._sep(fc, pady=16)

        ctk.CTkButton(fc, text="▶  Calcular y Graficar", height=42,
                      font=ctk.CTkFont(size=14, weight="bold"),
                      command=self.calcular).pack(fill="x", padx=22)
        self._sep(fc, pady=(8,6))

        self._lbl(fc, " Definir f(h) en el punto:", 12, bold=True).pack(anchor="w", padx=22)
        self._lbl(fc, "Escribe el valor y márcalo en el gráfico",
                  10, color="gray", wraplength=270).pack(anchor="w", padx=22, pady=(2,6))
        self.entry_definir = ctk.CTkEntry(fc, placeholder_text="Ej: 2   |   0   |   -1", height=34)
        self.entry_definir.pack(fill="x", padx=22, pady=(0,6))
        self.btn_definir = ctk.CTkButton(fc, text="▶  Marcar en el gráfico", height=34,
                                         font=ctk.CTkFont(size=12),
                                         fg_color="#1a5276", hover_color="#1f618d",
                                         state="disabled", command=self._marcar_punto)
        self.btn_definir.pack(fill="x", padx=22)
        self.label_verif = ctk.CTkLabel(fc, text="", font=ctk.CTkFont(size=11),
                                        wraplength=270, justify="left")
        self.label_verif.pack(anchor="w", padx=22, pady=(2,0))

        self.label_resultado = ctk.CTkLabel(fc, text="Resultado: —",
                                            font=ctk.CTkFont(size=13, weight="bold"),
                                            wraplength=270, justify="left")
        self.label_resultado.pack(pady=6, padx=22, anchor="w")

        self._lbl(fc, "Historial:", color="gray").pack(anchor="w", padx=22)
        self.textbox_hist = ctk.CTkTextbox(fc, height=70,
                                           font=ctk.CTkFont(size=11), state="disabled")
        self.textbox_hist.pack(fill="x", padx=22, pady=(4,6))
        ctk.CTkButton(fc, text="Limpiar historial", height=26,
                      font=ctk.CTkFont(size=11), fg_color="#2b2b2b", hover_color="#3d3d3d",
                      command=self._limpiar_hist).pack(padx=22, anchor="w")

        # Panel derecho
        fd = ctk.CTkFrame(self, corner_radius=12, fg_color="transparent")
        fd.grid(row=0, column=1, sticky="nsew", padx=(0,12), pady=12)
        fd.grid_rowconfigure(0, weight=3); fd.grid_rowconfigure(1, weight=2)
        fd.grid_columnconfigure(0, weight=1)

        fg_frame = ctk.CTkFrame(fd, corner_radius=12)
        fg_frame.grid(row=0, column=0, sticky="nsew", pady=(0,6))
        plt.style.use("dark_background")
        self.fig, self.ax = plt.subplots(figsize=(6,4), dpi=100)
        self.fig.patch.set_facecolor("#2b2b2b")
        self.canvas = FigureCanvasTkAgg(self.fig, master=fg_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        self._grafico_inicial()

        fp = ctk.CTkFrame(fd, corner_radius=12)
        fp.grid(row=1, column=0, sticky="nsew", pady=(6,0))
        ctk.CTkLabel(fp, text="📋  Resolución paso a paso",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=14, pady=(10,4))
        self._sep(fp, pady=(0,6))
        self.textbox_pasos = ctk.CTkTextbox(fp, font=ctk.CTkFont(size=12),
                                            state="disabled", fg_color="#1e1e1e", text_color="white")
        self.textbox_pasos.pack(fill="both", expand=True, padx=14, pady=(0,10))

    # ── Acciones ───────────────────────────────────────────────────────────────

    def _cargar(self, func, h):
        for e, v in [(self.entry_func, func), (self.entry_h, h)]:
            e.delete(0, "end"); e.insert(0, v)

    def _set_pasos(self, lineas):
        self.textbox_pasos.configure(state="normal")
        self.textbox_pasos.delete("1.0", "end")
        for l in lineas: self.textbox_pasos.insert("end", l + "\n")
        self.textbox_pasos.configure(state="disabled")

    def _agregar_hist(self, func, h, res):
        self.textbox_hist.configure(state="normal")
        self.textbox_hist.insert("end", f"lím({func}, {h}) = {res}\n")
        self.textbox_hist.see("end")
        self.textbox_hist.configure(state="disabled")

    def _limpiar_hist(self):
        self.textbox_hist.configure(state="normal")
        self.textbox_hist.delete("1.0", "end")
        self.textbox_hist.configure(state="disabled")

    def _grafico_inicial(self):
        self.ax.clear(); self.ax.set_facecolor("#1e1e1e")
        self.ax.set_title("Ingresa una función y presiona Calcular", color="gray", fontsize=11)
        self.ax.set_xlabel("x", color="white"); self.ax.set_ylabel("f(x)", color="white")
        self.ax.tick_params(colors="white")
        self.ax.grid(True, linestyle='--', alpha=0.3, color='gray')
        self.canvas.draw()

    def _estilo_ax(self, titulo="Comportamiento de la función"):
        self.ax.set_facecolor("#1e1e1e")
        self.ax.set_title(titulo, color="white", fontsize=13)
        self.ax.set_xlabel("x", color="white"); self.ax.set_ylabel("f(x)", color="white")
        self.ax.tick_params(colors="white")
        self.ax.grid(True, linestyle='--', alpha=0.3, color='gray')
        self.ax.legend(fontsize=9, facecolor="#2b2b2b", labelcolor="white")
        self.canvas.draw()

    def calcular(self):
        self.ax.clear()
        self.label_resultado.configure(text="Calculando...", text_color="white")
        self._set_pasos([" Calculando..."]); self.update_idletasks()

        fs = self.entry_func.get().strip()
        hs = self.entry_h.get().strip()
        if not fs or not hs:
            self.label_resultado.configure(text="Complete ambos campos.", text_color="#FF6B6B")
            self._grafico_inicial(); self._set_pasos(["Complete ambos campos."]); return

        try:
            f_expr = sp.sympify(preprocesar(fs), locals=TRIG_MAP)
            if   hs.lower() in ('oo','inf','+oo','infinito','+inf'): h_val = sp.oo
            elif hs.lower() in ('-oo','-inf','-infinito'):           h_val = -sp.oo
            else:                                                     h_val = sp.sympify(hs, locals=TRIG_MAP)

            res = calcular_limite(f_expr, h_val)
            # Asegurar que AccumBounds se trate como "no existe"
            if isinstance(res, AccumulationBounds): res = sp.nan
            no_existe = _es_nan(res)

            txt_res = "lím f(x) = No existe" if no_existe else f"lím f(x) = {res}"
            self.label_resultado.configure(text=txt_res,
                                           text_color="#FF8A65" if no_existe else "#4FC3F7")
            self._agregar_hist(fs, hs, "No existe" if no_existe else res)
            self._set_pasos(generar_pasos(f_expr, h_val, hs, res))
            self._dibujar(f_expr, h_val, res, no_existe)

        except sp.SympifyError:
            self.label_resultado.configure(text="Expresión inválida.", text_color="#FF6B6B")
            self._grafico_inicial(); self._set_pasos(["Expresión inválida."])
        except Exception as e:
            self.label_resultado.configure(text=f"Error: {e}", text_color="#FF6B6B")
            self._grafico_inicial(); self._set_pasos([f"Error: {e}"])

    def _dibujar(self, f_expr, h_val, res, no_existe):
        if h_val == sp.oo:    xr = (0, 50)
        elif h_val == -sp.oo: xr = (-50, 0)
        else:                 hf = float(h_val); xr = (hf-8, hf+8)

        paso = (xr[1]-xr[0]) / 600
        xs = [xr[0]+i*paso for i in range(601)]
        fn = sp.lambdify(x, f_expr, modules=['math'])
        ys = []
        for v in xs:
            try:
                y = fn(v)
                ys.append(None if (isinstance(y,complex) or math.isinf(y) or math.isnan(y)) else y)
            except: ys.append(None)

        y_ok = [v for v in ys if v is not None]
        if y_ok:
            # Si la función tiene saltos o crece demasiado, la escala calculada con
            # todos los puntos distorsiona la vista cerca de h. En ese caso se usa
            # solo los valores dentro de un radio ±2 alrededor del punto evaluado.
            if not h_val.is_infinite:
                hf_centro = float(h_val)
                y_cerca = [v for xi, v in zip(xs, ys)
                           if v is not None and abs(xi - hf_centro) <= 2]
                if y_cerca and (max(y_cerca) - min(y_cerca)) < (max(y_ok) - min(y_ok)) * 0.5:
                    y_ref = y_cerca
                else:
                    y_ref = y_ok
            else:
                y_ref = y_ok
            ym = sum(y_ref) / len(y_ref)
            mg = max((max(y_ref) - min(y_ref)) * 0.6, 5)
            self.ax.set_ylim(ym - mg, ym + mg)

        self.ax.plot(xs, ys, color='#4FC3F7', linewidth=2, label=f'f(x) = {f_expr}')

        if not h_val.is_infinite:
            self.ax.axvline(x=float(h_val), color='#FF8A65', linestyle='--',
                            linewidth=1.4, label=f'x → {float(h_val):.2f}')

        if no_existe:
            self.ax.text(0.04, 0.94, 'Límite: No existe',
                         transform=self.ax.transAxes, color='#FF8A65', fontsize=11, va='top')
        elif res.is_real and not res.is_infinite:
            lf = float(res)
            if h_val.is_infinite:
                self.ax.axhline(y=lf, color='#A5D6A7', linestyle=':',
                                linewidth=1.4, label=f'Límite = {lf:.4f}')
            else:
                self._punto_limite_x, self._punto_limite_y = float(h_val), lf
                try:
                    vd = float(sp.simplify(f_expr.subs(x, h_val)))
                    hueco = math.isnan(vd) or math.isinf(vd)
                except: hueco = True
                kw = dict(color='#FF5252', zorder=5, label=f'Límite = {lf:.4f}')
                if hueco: self.ax.plot(float(h_val), lf, 'o', markersize=12,
                                       markerfacecolor='#1e1e1e', markeredgewidth=2.5, **kw)
                else:     self.ax.plot(float(h_val), lf, 'o', markersize=9, **kw)
                self.btn_definir.configure(state="normal")
                self._limite_correcto = lf
        elif res.is_infinite:
            self.ax.text(0.04, 0.94, f'Límite = {res}',
                         transform=self.ax.transAxes, color='#FFEB3B', fontsize=11, va='top')

        self._estilo_ax()

    def _marcar_punto(self):
        if self._punto_limite_x is None: return
        vs = self.entry_definir.get().strip()
        if not vs:
            self.label_verif.configure(text="Escribe un valor primero.", text_color="#FF6B6B"); return
        try:
            vi = float(eval(vs, MATH_ENV))
        except:
            self.label_verif.configure(text="⚠ Valor inválido.", text_color="#FF6B6B"); return

        dif = abs(vi - self._limite_correcto) if self._limite_correcto is not None else 0
        color = '#A5D6A7' if dif < 0.01 else ('#FFD54F' if dif < 0.5 else '#FF6B6B')
        self.ax.plot(self._punto_limite_x, vi, 's', color=color, markersize=11,
                     markerfacecolor=color, markeredgecolor='white',
                     markeredgewidth=1.5, zorder=7, label=f'f(h) = {vi}')
        self.ax.annotate(f'  f(h) = {vi}',
                         xy=(self._punto_limite_x, vi), color=color, fontsize=10)
        self.canvas.draw()

        if self._limite_correcto is not None:
            if dif < 0.01:
                msg, col = f"✔ Correcto! f(h) = {vi} coincide.", '#A5D6A7'
            elif dif < 0.5:
                msg, col = f"⚠ Casi. Real = {self._limite_correcto:.4f}, diferencia = {dif:.4f}.", '#FFD54F'
            else:
                msg, col = f"✗ Incorrecto. Real = {self._limite_correcto}, no {vi}.", '#FF6B6B'
            self.label_verif.configure(text=msg, text_color=col)

    def on_closing(self):
        try:
            for aid in self.tk.call('after','info').split():
                try: self.after_cancel(aid)
                except: pass
        except: pass
        try: plt.close('all')
        except: pass
        try: self.destroy()
        except: pass


class AppTrig(App):
    def __init__(self):
        super().__init__()
        self.title("Analizador de Límites · MATE1133  [+Trig]")
        self._sep(self.frame_controles, pady=(10,6))
        self._lbl(self.frame_controles, "📐 Ejemplos trigonométricos:",
                  11, bold=True, color="#4FC3F7").pack(anchor="w", padx=22)
        for t, f, h in self.EJEMPLOS_TRIG:
            self._btn_ejemplo(self.frame_controles, t, f, h, fg="#1a3a4a", hov="#1f5270")

    def _calcular_limite(self, f_expr, h_val):
        res = calcular_limite(f_expr, h_val)
        if _es_nan(res) and f_expr.has(*TRIG) and h_val not in (sp.oo, -sp.oo):
            r, _ = _resolver_trig(f_expr, h_val)
            if r is not None: return r
        return res

    def calcular(self):
        # Parche temporal: usar la versión trig-extendida para el cálculo
        fs = self.entry_func.get().strip()
        hs = self.entry_h.get().strip()
        if not fs or not hs:
            self.label_resultado.configure(text="Complete ambos campos.", text_color="#FF6B6B")
            self._grafico_inicial(); self._set_pasos(["Complete ambos campos."]); return
        try:
            f_expr = sp.sympify(preprocesar(fs), locals=TRIG_MAP)
            if   hs.lower() in ('oo','inf','+oo','infinito','+inf'): h_val = sp.oo
            elif hs.lower() in ('-oo','-inf','-infinito'):           h_val = -sp.oo
            else:                                                     h_val = sp.sympify(hs, locals=TRIG_MAP)

            res = self._calcular_limite(f_expr, h_val)
            if isinstance(res, AccumulationBounds): res = sp.nan
            no_existe = _es_nan(res)

            # Info trig extra en los pasos
            pasos = generar_pasos(f_expr, h_val, hs, res)
            if f_expr.has(*TRIG) and h_val not in (sp.oo, -sp.oo):
                try:
                    vd = sp.simplify(f_expr.subs(x, h_val))
                    indet = math.isnan(complex(vd).real) or math.isinf(complex(vd).real)
                except: indet = True
                if indet:
                    _, desc = _resolver_trig(f_expr, h_val)
                    if desc:
                        idx = max(len(pasos)-3, 0)
                        for i, l in enumerate(["", "── Resolución trig extendida ──", f"  {desc}"]):
                            pasos.insert(idx+i, l)

            txt = "lím f(x) = No existe" if no_existe else f"lím f(x) = {res}"
            self.label_resultado.configure(text=txt,
                                           text_color="#FF8A65" if no_existe else "#4FC3F7")
            self._agregar_hist(fs, hs, "No existe" if no_existe else res)
            self._set_pasos(pasos)
            self.ax.clear(); self._dibujar(f_expr, h_val, res, no_existe)

        except sp.SympifyError:
            self.label_resultado.configure(text="Expresión inválida.", text_color="#FF6B6B")
            self._grafico_inicial(); self._set_pasos(["Expresión inválida."])
        except Exception as e:
            self.label_resultado.configure(text=f"Error: {e}", text_color="#FF6B6B")
            self._grafico_inicial(); self._set_pasos([f"Error: {e}"])


if __name__ == "__main__":
    app = AppTrig()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
