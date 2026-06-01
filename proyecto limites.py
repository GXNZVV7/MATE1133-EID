import customtkinter as ctk
import sympy as sp
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import math

# ─────────────────────────────────────────
#  Configuración inicial de CustomTkinter
# ─────────────────────────────────────────
ctk.set_appearance_mode("dark")          # Modo oscuro: se ve más profesional
ctk.set_default_color_theme("blue")


class CalculadoraLimitesApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # ── Configuración de la ventana ──
        self.title("Analizador y Visualizador de Límites · MATE1133")
        self.geometry("1050x650")
        self.minsize(900, 550)

        # Grid: columna 0 = controles, columna 1 = gráfico
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ══════════════════════════════════
        #  PANEL IZQUIERDO — Controles
        # ══════════════════════════════════
        self.frame_controles = ctk.CTkFrame(self, width=320, corner_radius=12)
        self.frame_controles.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        self.frame_controles.grid_propagate(False)   # mantiene el ancho fijo

        # ── Título del panel ──
        ctk.CTkLabel(
            self.frame_controles,
            text="🔢  Calculadora de Límites",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(22, 4))

        ctk.CTkLabel(
            self.frame_controles,
            text="MATE1133 · UCTemuco",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(pady=(0, 18))

        # ── Separador visual ──
        ctk.CTkFrame(self.frame_controles, height=2, fg_color="#3a3a3a").pack(fill="x", padx=20, pady=(0, 18))

        # ── Campo: función f(x) ──
        ctk.CTkLabel(
            self.frame_controles,
            text="Función  f(x):",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=22)

        self.entry_func = ctk.CTkEntry(
            self.frame_controles,
            placeholder_text="Ej: sin(x)/x   |   x**2 - 4   |   1/x",
            height=38
        )
        self.entry_func.pack(fill="x", padx=22, pady=(4, 14))

        # ── Campo: valor h ──
        ctk.CTkLabel(
            self.frame_controles,
            text="Tiende a  h:",
            font=ctk.CTkFont(size=13, weight="bold")
        ).pack(anchor="w", padx=22)

        self.entry_h = ctk.CTkEntry(
            self.frame_controles,
            placeholder_text="Ej: 0   |   2   |   oo   |   -oo",
            height=38
        )
        self.entry_h.pack(fill="x", padx=22, pady=(4, 20))

        # ── Ejemplos rápidos (MEJORA: el usuario ve ejemplos clickeables) ──
        ctk.CTkLabel(
            self.frame_controles,
            text="Ejemplos rápidos:",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(anchor="w", padx=22)

        # Lista de ejemplos: (texto del botón, función, h)
        ejemplos = [
            ("sin(x)/x  →  0",  "sin(x)/x",        "0"),
            ("x²−4  →  2",      "x**2 - 4",         "2"),
            ("1/x²  →  ∞",      "1/x**2",           "oo"),
            ("(x²−1)/(x−1) → 1","(x**2-1)/(x-1)",  "1"),
        ]

        for texto, func, h in ejemplos:
            # Usamos lambda con argumentos por defecto para capturar el valor correcto
            ctk.CTkButton(
                self.frame_controles,
                text=texto,
                height=28,
                font=ctk.CTkFont(size=11),
                fg_color="#2b2b2b",
                hover_color="#3d3d3d",
                command=lambda f=func, hv=h: self._cargar_ejemplo(f, hv)
            ).pack(fill="x", padx=22, pady=2)

        # ── Botón principal ──
        ctk.CTkFrame(self.frame_controles, height=2, fg_color="#3a3a3a").pack(fill="x", padx=20, pady=16)

        self.btn_calcular = ctk.CTkButton(
            self.frame_controles,
            text="▶  Calcular y Graficar",
            height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.calcular_limite_y_graficar
        )
        self.btn_calcular.pack(fill="x", padx=22)

        # ── Resultado ──
        self.label_resultado = ctk.CTkLabel(
            self.frame_controles,
            text="Resultado: —",
            font=ctk.CTkFont(size=15, weight="bold"),
            wraplength=270,   # MEJORA: evita que el texto se salga del panel
            justify="left"
        )
        self.label_resultado.pack(pady=16, padx=22, anchor="w")

        # ── Historial de cálculos (MEJORA nueva) ──
        ctk.CTkLabel(
            self.frame_controles,
            text="Historial:",
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(anchor="w", padx=22)

        self.textbox_historial = ctk.CTkTextbox(
            self.frame_controles,
            height=110,
            font=ctk.CTkFont(size=11),
            state="disabled"   # solo lectura
        )
        self.textbox_historial.pack(fill="x", padx=22, pady=(4, 10))

        # Botón para limpiar historial
        ctk.CTkButton(
            self.frame_controles,
            text="Limpiar historial",
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color="#2b2b2b",
            hover_color="#3d3d3d",
            command=self._limpiar_historial
        ).pack(padx=22, anchor="w")

        # ══════════════════════════════════
        #  PANEL DERECHO — Gráfico
        # ══════════════════════════════════
        self.frame_grafico = ctk.CTkFrame(self, corner_radius=12)
        self.frame_grafico.grid(row=0, column=1, sticky="nsew", padx=(0, 12), pady=12)

        # Configurar matplotlib con fondo oscuro para que combine con la app
        plt.style.use("dark_background")
        self.fig, self.ax = plt.subplots(figsize=(6, 5), dpi=100)
        self.fig.patch.set_facecolor("#2b2b2b")

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_grafico)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

        # Gráfico inicial vacío
        self._mostrar_grafico_inicial()

    # ══════════════════════════════════════════════
    #  MÉTODO PRINCIPAL: Calcular límite y graficar
    # ══════════════════════════════════════════════
    def calcular_limite_y_graficar(self):
        """
        Se ejecuta al presionar el botón.
        Pasos:
          1. Leer los campos de entrada.
          2. Convertir la función a expresión simbólica (SymPy).
          3. Calcular el límite con sp.limit().
          4. Generar los puntos X e Y manualmente (sin NumPy).
          5. Dibujar la curva y marcar el punto/límite.
        """
        # Limpiar el gráfico anterior
        self.ax.clear()
        self.label_resultado.configure(text="Resultado: Calculando...", text_color="white")
        self.update_idletasks()

        func_str = self.entry_func.get().strip()
        h_str    = self.entry_h.get().strip()

        # ── Validar que los campos no estén vacíos ──
        if not func_str or not h_str:
            self.label_resultado.configure(
                text="⚠ Complete ambos campos.",
                text_color="#FF6B6B"
            )
            self._mostrar_grafico_inicial()
            return

        try:
            # ── Paso 1: Crear la variable simbólica ──
            x = sp.Symbol('x')

            # ── Paso 2: Convertir el texto de la función a expresión SymPy ──
            # sympify interpreta cadenas como "sin(x)/x" y las vuelve simbólicas
            f_expr = sp.sympify(func_str)

            # ── Paso 3: Interpretar el valor h ──
            if h_str.lower() in ['oo', 'inf', '+oo', 'infinito', '+inf']:
                h_val = sp.oo       # infinito positivo en SymPy
            elif h_str.lower() in ['-oo', '-inf', '-infinito']:
                h_val = -sp.oo      # infinito negativo
            else:
                h_val = sp.sympify(h_str)

            # ── Paso 4: Calcular el límite simbólicamente ──
            # sp.limit(función, variable, valor) → el corazón matemático del programa
            limite_resultado = sp.limit(f_expr, x, h_val)

            # Mostrar el resultado en la etiqueta
            self.label_resultado.configure(
                text=f"lím f(x) = {limite_resultado}",
                text_color="#4FC3F7"
            )

            # Guardar en el historial
            self._agregar_historial(func_str, h_str, limite_resultado)

            # ── Paso 5: Determinar el rango del eje X para graficar ──
            if h_val == sp.oo:
                x_min, x_max = 0, 50
            elif h_val == -sp.oo:
                x_min, x_max = -50, 0
            else:
                h_float = float(h_val)
                x_min, x_max = h_float - 8, h_float + 8

            # ── Paso 6: Generar puntos X manualmente (sin NumPy) ──
            num_puntos = 600
            paso = (x_max - x_min) / num_puntos
            x_vals = [x_min + i * paso for i in range(num_puntos + 1)]

            # ── Paso 7: Convertir la expresión SymPy a función numérica ──
            # lambdify crea una función Python normal a partir de la expresión simbólica
            f_numerica = sp.lambdify(x, f_expr, modules=['math'])

            # ── Paso 8: Evaluar f(x) en cada punto X ──
            y_vals = []
            for val in x_vals:
                try:
                    y = f_numerica(val)
                    # Descartar valores inválidos (infinitos, NaN, complejos)
                    if isinstance(y, complex) or math.isinf(y) or math.isnan(y):
                        y_vals.append(None)
                    else:
                        y_vals.append(y)
                except Exception:
                    y_vals.append(None)   # puntos sin definición (ej: 1/0)

            # ── MEJORA: Limitar el eje Y para que el gráfico sea legible ──
            # Si los valores son muy grandes, el gráfico se aplana
            y_validos = [v for v in y_vals if v is not None]
            if y_validos:
                y_media  = sum(y_validos) / len(y_validos)
                y_rango  = max(y_validos) - min(y_validos)
                margen   = max(y_rango * 0.6, 5)   # mínimo ±5 de margen
                self.ax.set_ylim(y_media - margen, y_media + margen)

            # ── Dibujar la curva de la función ──
            self.ax.plot(
                x_vals, y_vals,
                color='#4FC3F7',
                linewidth=2,
                label=f'f(x) = {sp.latex(f_expr)}'
            )

            # ── Dibujar línea vertical en x = h (si h es finito) ──
            if not h_val.is_infinite:
                self.ax.axvline(
                    x=float(h_val),
                    color='#FF8A65',
                    linestyle='--',
                    linewidth=1.4,
                    label=f'x → {float(h_val):.2f}'
                )

            # ── Marcar el límite en el gráfico ──
            if limite_resultado.is_real and not limite_resultado.is_infinite:
                lim_float = float(limite_resultado)
                if h_val.is_infinite:
                    # Límite al infinito → línea horizontal (asíntota)
                    self.ax.axhline(
                        y=lim_float,
                        color='#A5D6A7',
                        linestyle=':',
                        linewidth=1.4,
                        label=f'Límite = {lim_float:.4f}'
                    )
                else:
                    # Límite en un punto → círculo rojo en (h, L)
                    self.ax.plot(
                        float(h_val), lim_float,
                        'o',
                        color='#FF5252',
                        markersize=9,
                        zorder=5,
                        label=f'Límite = {lim_float:.4f}'
                    )
            elif limite_resultado.is_infinite:
                # El límite es ±∞ → anotar en el gráfico
                self.ax.text(
                    0.04, 0.94,
                    f'Límite = {limite_resultado}',
                    transform=self.ax.transAxes,
                    color='#FFEB3B',
                    fontsize=11,
                    verticalalignment='top'
                )

            # ── Estética del gráfico ──
            self.ax.set_facecolor("#1e1e1e")
            self.ax.set_title("Comportamiento de la función", color="white", fontsize=13)
            self.ax.set_xlabel("x", color="white")
            self.ax.set_ylabel("f(x)", color="white")
            self.ax.tick_params(colors="white")
            self.ax.grid(True, linestyle='--', alpha=0.3, color='gray')
            self.ax.legend(fontsize=9, facecolor="#2b2b2b", labelcolor="white")

            self.canvas.draw()

        except sp.SympifyError:
            self.label_resultado.configure(
                text="⚠ Expresión inválida.\nRevisa la sintaxis.",
                text_color="#FF6B6B"
            )
            self._mostrar_grafico_inicial()

        except Exception as e:
            self.label_resultado.configure(
                text=f"⚠ Error: {str(e)}",
                text_color="#FF6B6B"
            )
            self._mostrar_grafico_inicial()

    # ══════════════════════════════════════
    #  MÉTODOS AUXILIARES
    # ══════════════════════════════════════

    def _cargar_ejemplo(self, func: str, h: str):
        """Rellena los campos con un ejemplo predefinido."""
        self.entry_func.delete(0, "end")
        self.entry_func.insert(0, func)
        self.entry_h.delete(0, "end")
        self.entry_h.insert(0, h)

    def _agregar_historial(self, func: str, h: str, resultado):
        """Agrega una línea al textbox de historial."""
        self.textbox_historial.configure(state="normal")
        linea = f"lím({func}, {h}) = {resultado}\n"
        self.textbox_historial.insert("end", linea)
        self.textbox_historial.see("end")          # desplaza al final
        self.textbox_historial.configure(state="disabled")

    def _limpiar_historial(self):
        """Borra todo el historial."""
        self.textbox_historial.configure(state="normal")
        self.textbox_historial.delete("1.0", "end")
        self.textbox_historial.configure(state="disabled")

    def _mostrar_grafico_inicial(self):
        """Muestra un gráfico vacío con mensaje de bienvenida."""
        self.ax.clear()
        self.ax.set_facecolor("#1e1e1e")
        self.ax.set_title("Ingresa una función y presiona Calcular", color="gray", fontsize=11)
        self.ax.set_xlabel("x", color="white")
        self.ax.set_ylabel("f(x)", color="white")
        self.ax.tick_params(colors="white")
        self.ax.grid(True, linestyle='--', alpha=0.3, color='gray')
        self.canvas.draw()


# ── Punto de entrada del programa ──
if __name__ == "__main__":
    app = CalculadoraLimitesApp()
    app.mainloop()
