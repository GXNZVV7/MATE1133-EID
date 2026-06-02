import customtkinter as ctk
import sympy as sp
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import math

#  Configuración inicial de CustomTkint
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class CalculadoraLimitesApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Analizador y Visualizador de Límites · MATE1133")
        self.geometry("1150x700")
        self.minsize(950, 600)

        # Grid principal: columna 0 = controles, columna 1 = gráfico + pasos
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        
        #  PANEL IZQUIERDO — Controles
        self.frame_controles = ctk.CTkFrame(self, width=320, corner_radius=12)
        self.frame_controles.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        self.frame_controles.grid_propagate(False)

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

        ctk.CTkFrame(self.frame_controles, height=2, fg_color="#3a3a3a").pack(fill="x", padx=20, pady=(0, 18))

        # Campo: función f(x)
        ctk.CTkLabel(self.frame_controles, text="Función  f(x):",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=22)
        self.entry_func = ctk.CTkEntry(self.frame_controles,
                                       placeholder_text="Ej: sin(x)/x   |   x**2 - 4   |   1/x",
                                       height=38)
        self.entry_func.pack(fill="x", padx=22, pady=(4, 14))

        # Campo: valor h
        ctk.CTkLabel(self.frame_controles, text="Tiende a  h:",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=22)
        self.entry_h = ctk.CTkEntry(self.frame_controles,
                                    placeholder_text="Ej: 0   |   2   |   oo   |   -oo",
                                    height=38)
        self.entry_h.pack(fill="x", padx=22, pady=(4, 20))

        # Ejemplos rápidos
        ctk.CTkLabel(self.frame_controles, text="Ejemplos rápidos:",
                     font=ctk.CTkFont(size=11), text_color="gray").pack(anchor="w", padx=22)

        ejemplos = [
            ("sin(x)/x  →  0",   "sin(x)/x",       "0"),
            ("x²−4  →  2",       "x**2 - 4",        "2"),
            ("1/x²  →  ∞",       "1/x**2",          "oo"),
            ("(x²−1)/(x−1) → 1", "(x**2-1)/(x-1)", "1"),
        ]
        for texto, func, h in ejemplos:
            ctk.CTkButton(self.frame_controles, text=texto, height=28,
                          font=ctk.CTkFont(size=11), fg_color="#2b2b2b",
                          hover_color="#3d3d3d",
                          command=lambda f=func, hv=h: self._cargar_ejemplo(f, hv)
                          ).pack(fill="x", padx=22, pady=2)

        ctk.CTkFrame(self.frame_controles, height=2, fg_color="#3a3a3a").pack(fill="x", padx=20, pady=16)

        # Botón calcular
        self.btn_calcular = ctk.CTkButton(self.frame_controles, text="▶  Calcular y Graficar",
                                          height=42, font=ctk.CTkFont(size=14, weight="bold"),
                                          command=self.calcular_limite_y_graficar)
        self.btn_calcular.pack(fill="x", padx=22)

        # ── Sección: Definir el límite manualmente ──
        ctk.CTkFrame(self.frame_controles, height=2, fg_color="#3a3a3a").pack(fill="x", padx=20, pady=(8, 6))

        ctk.CTkLabel(
            self.frame_controles,
            text="✏️  Definir f(h) en el punto:",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(anchor="w", padx=22)

        ctk.CTkLabel(
            self.frame_controles,
            text="Escribe el valor y márcalo en el gráfico",
            font=ctk.CTkFont(size=10),
            text_color="gray",
            wraplength=270
        ).pack(anchor="w", padx=22, pady=(2, 6))

        # Campo donde el usuario escribe su valor
        self.entry_definir = ctk.CTkEntry(
            self.frame_controles,
            placeholder_text="Ej: 2   |   0   |   -1",
            height=34
        )
        self.entry_definir.pack(fill="x", padx=22, pady=(0, 6))

        # Botón para marcar ese valor en el gráfico
        self.btn_definir = ctk.CTkButton(
            self.frame_controles,
            text="📍  Marcar en el gráfico",
            height=34,
            font=ctk.CTkFont(size=12),
            fg_color="#1a5276",
            hover_color="#1f618d",
            state="disabled",
            command=self._definir_limite_manual
        )
        self.btn_definir.pack(fill="x", padx=22)

        # Etiqueta que indica si el valor ingresado es correcto o no
        self.label_verificacion = ctk.CTkLabel(
            self.frame_controles,
            text="",
            font=ctk.CTkFont(size=11),
            wraplength=270,
            justify="left"
        )
        self.label_verificacion.pack(anchor="w", padx=22, pady=(2, 0))

        # Variables internas del punto
        self._punto_limite_x  = None
        self._punto_limite_y  = None
        self._limite_correcto = None

        # Resultado
        self.label_resultado = ctk.CTkLabel(self.frame_controles, text="Resultado: —",
                                            font=ctk.CTkFont(size=13, weight="bold"),
                                            wraplength=270, justify="left")
        self.label_resultado.pack(pady=6, padx=22, anchor="w")

        # Historial
        ctk.CTkLabel(self.frame_controles, text="Historial:",
                     font=ctk.CTkFont(size=11), text_color="gray").pack(anchor="w", padx=22)
        self.textbox_historial = ctk.CTkTextbox(self.frame_controles, height=70,
                                                font=ctk.CTkFont(size=11), state="disabled")
        self.textbox_historial.pack(fill="x", padx=22, pady=(4, 6))

        ctk.CTkButton(self.frame_controles, text="Limpiar historial", height=26,
                      font=ctk.CTkFont(size=11), fg_color="#2b2b2b", hover_color="#3d3d3d",
                      command=self._limpiar_historial).pack(padx=22, anchor="w")
        
        #  PANEL DERECHO — Gráfico arriba + Paso a paso abajo
        self.frame_derecho = ctk.CTkFrame(self, corner_radius=12, fg_color="transparent")
        self.frame_derecho.grid(row=0, column=1, sticky="nsew", padx=(0, 12), pady=12)

        # El panel derecho tiene 2 filas: gráfico (peso 3) y pasos (peso 2)
        self.frame_derecho.grid_rowconfigure(0, weight=3)
        self.frame_derecho.grid_rowconfigure(1, weight=2)
        self.frame_derecho.grid_columnconfigure(0, weight=1)

        # ── Gráfico ──
        self.frame_grafico = ctk.CTkFrame(self.frame_derecho, corner_radius=12)
        self.frame_grafico.grid(row=0, column=0, sticky="nsew", pady=(0, 6))

        plt.style.use("dark_background")
        self.fig, self.ax = plt.subplots(figsize=(6, 4), dpi=100)
        self.fig.patch.set_facecolor("#2b2b2b")

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_grafico)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        self._mostrar_grafico_inicial()

        # ── Panel PASO A PASO ──
        self.frame_pasos = ctk.CTkFrame(self.frame_derecho, corner_radius=12)
        self.frame_pasos.grid(row=1, column=0, sticky="nsew", pady=(6, 0))

        ctk.CTkLabel(self.frame_pasos, text="📋  Resolución paso a paso",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=14, pady=(10, 4))

        ctk.CTkFrame(self.frame_pasos, height=2, fg_color="#3a3a3a").pack(fill="x", padx=14, pady=(0, 6))

        # Textbox de solo lectura donde aparecen los pasos
        self.textbox_pasos = ctk.CTkTextbox(self.frame_pasos, font=ctk.CTkFont(size=12),
                                            state="disabled", fg_color="#1e1e1e",
                                            text_color="white")
        self.textbox_pasos.pack(fill="both", expand=True, padx=14, pady=(0, 10))

    
    #  MÉTODO: Generar el paso a paso del límite
    def _generar_pasos(self, f_expr, h_val, h_str, limite_resultado):
        """
        Genera una explicación paso a paso de cómo se resuelve el límite.
        Detecta el tipo de límite y explica la estrategia usada.
        """
        x = sp.Symbol('x')
        pasos = []

        pasos.append(f"Función ingresada:  f(x) = {f_expr}")
        pasos.append(f"Se evalúa el límite cuando x → {h_str}")
        pasos.append("─" * 45)

        # ── Caso 1: Límite al infinito ──
        if h_val == sp.oo or h_val == -sp.oo:
            pasos.append("Tipo: Límite al infinito")
            pasos.append("")
            pasos.append("Estrategia: analizar el comportamiento")
            pasos.append("de f(x) cuando x crece sin límite.")
            pasos.append("")

            # Ver si es una fracción para aplicar truco del término dominante
            if f_expr.is_rational_function(x):
                num, den = sp.fraction(f_expr)
                grado_num = sp.degree(sp.Poly(num, x))
                grado_den = sp.degree(sp.Poly(den, x))
                pasos.append(f"  Grado del numerador:    {grado_num}")
                pasos.append(f"  Grado del denominador:  {grado_den}")
                pasos.append("")
                if grado_num < grado_den:
                    pasos.append("  Grado num < Grado den")
                    pasos.append("  → El límite tiende a 0")
                elif grado_num == grado_den:
                    pasos.append("  Grado num = Grado den")
                    pasos.append("  → El límite es el cociente")
                    pasos.append("    de los coeficientes líderes")
                else:
                    pasos.append("  Grado num > Grado den")
                    pasos.append("  → El límite tiende a ±∞")

        # ── Caso 2: Límite en un punto finito ──
        else:
            pasos.append("Tipo: Límite en un punto finito")
            pasos.append("")

            # Intentar sustitución directa
            try:
                valor_directo = f_expr.subs(x, h_val)
                valor_directo_simplificado = sp.simplify(valor_directo)

                # Verificar si da indeterminación 0/0 o inf/inf
                if valor_directo_simplificado == sp.nan or str(valor_directo_simplificado) == 'nan':
                    raise ValueError("indeterminado")

                es_indeterminado = False
                try:
                    num_val = float(valor_directo_simplificado)
                    if math.isnan(num_val) or math.isinf(num_val):
                        es_indeterminado = True
                except Exception:
                    # No se pudo convertir a float, puede ser simbólico válido
                    es_indeterminado = False

                if not es_indeterminado:
                    pasos.append("Paso 1: Sustitución directa")
                    pasos.append(f"  f({h_str}) = {valor_directo_simplificado}")
                    pasos.append("")
                    pasos.append("✔ La sustitución directa funciona.")
                    pasos.append(f"  No hay indeterminación.")
                else:
                    raise ValueError("indeterminado")

            except Exception:
                # Hay indeterminación → intentar simplificar
                pasos.append("Paso 1: Sustitución directa")
                pasos.append(f"  f({h_str}) → indeterminación")
                pasos.append("")
                pasos.append("Paso 2: Simplificación algebraica")

                f_simplificada = sp.simplify(f_expr)
                if f_simplificada != f_expr:
                    pasos.append(f"  f(x) simplificada = {f_simplificada}")
                    pasos.append("")
                    pasos.append("Paso 3: Sustitución tras simplificar")
                    try:
                        val_simp = f_simplificada.subs(x, h_val)
                        pasos.append(f"  f({h_str}) = {sp.simplify(val_simp)}")
                    except Exception:
                        pasos.append(f"  → Resultado: {limite_resultado}")
                else:
                    # Intentar factorizar
                    try:
                        f_factor = sp.factor(f_expr)
                        if f_factor != f_expr:
                            pasos.append(f"  Factorizando: {f_factor}")
                            pasos.append("")
                            pasos.append("Paso 3: Cancelar términos comunes")
                            pasos.append("  y sustituir x → " + h_str)
                    except Exception:
                        pass
                    pasos.append(f"  → Resultado tras simplificar: {limite_resultado}")

        # ── Resultado final siempre ──
        pasos.append("")
        pasos.append("─" * 45)
        pasos.append(f"  lím f(x)  =  {limite_resultado}   cuando x → {h_str}")
        pasos.append("─" * 45)

        return pasos
    #  MÉTODO PRINCIPAL: Calcular límite y graficar
    def calcular_limite_y_graficar(self):
        self.ax.clear()
        self.label_resultado.configure(text="Resultado: Calculando...", text_color="white")
        self._actualizar_pasos(["⏳ Calculando..."])
        self.update_idletasks()

        func_str = self.entry_func.get().strip()
        h_str    = self.entry_h.get().strip()

        if not func_str or not h_str:
            self.label_resultado.configure(text="⚠ Complete ambos campos.", text_color="#FF6B6B")
            self._mostrar_grafico_inicial()
            self._actualizar_pasos(["⚠ Complete ambos campos."])
            return

        try:
            # Paso 1: variable simbólica
            x = sp.Symbol('x')

            # Paso 2: convertir texto a expresión SymPy
            f_expr = sp.sympify(func_str)

            # Paso 3: interpretar h
            if h_str.lower() in ['oo', 'inf', '+oo', 'infinito', '+inf']:
                h_val = sp.oo
            elif h_str.lower() in ['-oo', '-inf', '-infinito']:
                h_val = -sp.oo
            else:
                h_val = sp.sympify(h_str)

            # Paso 4: calcular el límite con SymPy
            limite_resultado = sp.limit(f_expr, x, h_val)

            self.label_resultado.configure(
                text=f"lím f(x) = {limite_resultado}",
                text_color="#4FC3F7"
            )

            # Guardar en historial
            self._agregar_historial(func_str, h_str, limite_resultado)

            # ── Mostrar paso a paso ──
            pasos = self._generar_pasos(f_expr, h_val, h_str, limite_resultado)
            self._actualizar_pasos(pasos)

            # Rango del eje X
            if h_val == sp.oo:
                x_min, x_max = 0, 50
            elif h_val == -sp.oo:
                x_min, x_max = -50, 0
            else:
                h_float = float(h_val)
                x_min, x_max = h_float - 8, h_float + 8

            # Generar puntos X sin NumPy
            num_puntos = 600
            paso = (x_max - x_min) / num_puntos
            x_vals = [x_min + i * paso for i in range(num_puntos + 1)]

            # Convertir a función numérica
            f_numerica = sp.lambdify(x, f_expr, modules=['math'])

            # Evaluar Y
            y_vals = []
            for val in x_vals:
                try:
                    y = f_numerica(val)
                    if isinstance(y, complex) or math.isinf(y) or math.isnan(y):
                        y_vals.append(None)
                    else:
                        y_vals.append(y)
                except Exception:
                    y_vals.append(None)

            # Limitar eje Y
            y_validos = [v for v in y_vals if v is not None]
            if y_validos:
                y_media = sum(y_validos) / len(y_validos)
                y_rango = max(y_validos) - min(y_validos)
                margen  = max(y_rango * 0.6, 5)
                self.ax.set_ylim(y_media - margen, y_media + margen)

            # Dibujar curva
            self.ax.plot(x_vals, y_vals, color='#4FC3F7', linewidth=2,
                         label=f'f(x) = {sp.latex(f_expr)}')

            # Línea vertical en x = h
            if not h_val.is_infinite:
                self.ax.axvline(x=float(h_val), color='#FF8A65', linestyle='--',
                                linewidth=1.4, label=f'x → {float(h_val):.2f}')

            # Marcar el límite
            if limite_resultado.is_real and not limite_resultado.is_infinite:
                lim_float = float(limite_resultado)
                if h_val.is_infinite:
                    self.ax.axhline(y=lim_float, color='#A5D6A7', linestyle=':',
                                    linewidth=1.4, label=f'Límite = {lim_float:.4f}')
                else:
                    # Guardar datos del punto para poder rellenarlo después
                    self._punto_limite_x   = float(h_val)
                    self._punto_limite_y   = lim_float
                    self.btn_definir.configure(state="normal")
                    self._punto_rellenado  = False   # empieza vacío

                    # Detectar si hay indeterminación (función no definida en h)
                    try:
                        val_directo = float(sp.simplify(f_expr.subs(sp.Symbol('x'), h_val)))
                        hay_hueco = math.isnan(val_directo) or math.isinf(val_directo)
                    except Exception:
                        hay_hueco = True

                    if hay_hueco:
                        # Círculo HUECO — punto removible (indeterminación)
                        self.ax.plot(float(h_val), lim_float,
                                     'o',                      # marcador círculo
                                     color='#FF5252',
                                     markersize=12,
                                     markerfacecolor='#1e1e1e',  # interior igual al fondo → parece hueco
                                     markeredgewidth=2.5,
                                     zorder=5,
                                     label=f'Límite = {lim_float:.4f} (punto removible)')
                        # Mostrar botón para rellenar
                        self.btn_definir.configure(state="normal")
                        self._limite_correcto = lim_float
                    else:
                        # Círculo RELLENO normal
                        self.ax.plot(float(h_val), lim_float,
                                     'o', color='#FF5252',
                                     markersize=9, zorder=5,
                                     label=f'Límite = {lim_float:.4f}')
                        self.btn_definir.configure(state="normal")
                        self._limite_correcto = lim_float
            elif limite_resultado.is_infinite:
                self.ax.text(0.04, 0.94, f'Límite = {limite_resultado}',
                             transform=self.ax.transAxes, color='#FFEB3B',
                             fontsize=11, verticalalignment='top')

            # Estética
            self.ax.set_facecolor("#1e1e1e")
            self.ax.set_title("Comportamiento de la función", color="white", fontsize=13)
            self.ax.set_xlabel("x", color="white")
            self.ax.set_ylabel("f(x)", color="white")
            self.ax.tick_params(colors="white")
            self.ax.grid(True, linestyle='--', alpha=0.3, color='gray')
            self.ax.legend(fontsize=9, facecolor="#2b2b2b", labelcolor="white")
            self.canvas.draw()

        except sp.SympifyError:
            self.label_resultado.configure(text="⚠ Expresión inválida.\nRevisa la sintaxis.",
                                           text_color="#FF6B6B")
            self._mostrar_grafico_inicial()
            self._actualizar_pasos(["⚠ Expresión inválida. Revisa la sintaxis."])

        except Exception as e:
            self.label_resultado.configure(text=f"⚠ Error: {str(e)}", text_color="#FF6B6B")
            self._mostrar_grafico_inicial()
            self._actualizar_pasos([f"⚠ Error: {str(e)}"])

    #  MÉTODOS AUXILIARES

    def _actualizar_pasos(self, lista_pasos):
        """Muestra los pasos en el textbox del panel inferior."""
        self.textbox_pasos.configure(state="normal")
        self.textbox_pasos.delete("1.0", "end")
        for linea in lista_pasos:
            self.textbox_pasos.insert("end", linea + "\n")
        self.textbox_pasos.configure(state="disabled")

    def _definir_limite_manual(self):
        """
        El usuario escribe un valor en el campo entry_definir.
        Se dibuja ese punto en el gráfico y se compara con el límite real.
        """
        if self._punto_limite_x is None:
            return

        valor_str = self.entry_definir.get().strip()
        if not valor_str:
            self.label_verificacion.configure(
                text="⚠ Escribe un valor primero.",
                text_color="#FF6B6B"
            )
            return

        try:
            valor_ingresado = float(sp.sympify(valor_str))
        except Exception:
            self.label_verificacion.configure(
                text="⚠ Valor inválido.",
                text_color="#FF6B6B"
            )
            return

        # Dibujar el punto que el usuario definió (color verde)
        self.ax.plot(
            self._punto_limite_x,
            valor_ingresado,
            's',                        # cuadrado para diferenciarlo
            color='#A5D6A7',
            markersize=11,
            markerfacecolor='#A5D6A7',
            markeredgecolor='white',
            markeredgewidth=1.5,
            zorder=7,
            label=f'f(h) definida = {valor_ingresado}'
        )

        # Anotar el valor en el gráfico
        self.ax.annotate(
            f'  f(h) = {valor_ingresado}',
            xy=(self._punto_limite_x, valor_ingresado),
            color='#A5D6A7',
            fontsize=10
        )

        self.canvas.draw()

        # Verificar si el valor ingresado coincide con el límite real
        if self._limite_correcto is not None:
            diferencia = abs(valor_ingresado - self._limite_correcto)
            if diferencia < 0.001:
                self.label_verificacion.configure(
                    text=f"✔ ¡Correcto! f(h) = {valor_ingresado} coincide con el límite.",
                    text_color="#A5D6A7"
                )
            else:
                self.label_verificacion.configure(
                    text=f"✗ El límite real es {self._limite_correcto}, no {valor_ingresado}.",
                    text_color="#FF6B6B"
                )

    def _cargar_ejemplo(self, func: str, h: str):
        self.entry_func.delete(0, "end")
        self.entry_func.insert(0, func)
        self.entry_h.delete(0, "end")
        self.entry_h.insert(0, h)

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
        self.ax.set_xlabel("x", color="white")
        self.ax.set_ylabel("f(x)", color="white")
        self.ax.tick_params(colors="white")
        self.ax.grid(True, linestyle='--', alpha=0.3, color='gray')
        self.canvas.draw()


if __name__ == "__main__":
    app = CalculadoraLimitesApp()
    app.mainloop()
