import customtkinter as ctk
import sympy as sp
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import math

# Configuración inicial de la apariencia de CustomTkinter
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class CalculadoraLimitesApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configuración de la ventana principal
        self.title("Calculadora y Visualizador de Límites - MATE1133")
        self.geometry("900x600")
        self.minsize(800, 500)

        # Configurar el grid layout de la ventana
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- PANEL IZQUIERDO: Controles e Inputs ---
        self.frame_controles = ctk.CTkFrame(self, width=300, corner_radius=0)
        self.frame_controles.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        self.label_titulo = ctk.CTkLabel(self.frame_controles, text="Cálculo de Límites", font=ctk.CTkFont(size=20, weight="bold"))
        self.label_titulo.pack(pady=(20, 20))

        # Input: Función f(x)
        self.label_func = ctk.CTkLabel(self.frame_controles, text="Ingrese la función f(x):")
        self.label_func.pack(anchor="w", padx=20)
        self.entry_func = ctk.CTkEntry(self.frame_controles, placeholder_text="Ej: sin(x)/x, x**2 - 4")
        self.entry_func.pack(fill="x", padx=20, pady=(0, 15))

        # Input: Valor h (Tendencia)
        self.label_h = ctk.CTkLabel(self.frame_controles, text="Tiende a (h):")
        self.label_h.pack(anchor="w", padx=20)
        self.entry_h = ctk.CTkEntry(self.frame_controles, placeholder_text="Ej: 0, oo (infinito)")
        self.entry_h.pack(fill="x", padx=20, pady=(0, 25))

        # Botón de Acción (Control de Ejecución)
        self.btn_calcular = ctk.CTkButton(self.frame_controles, text="Calcular y Graficar", command=self.calcular_limite_y_graficar)
        self.btn_calcular.pack(fill="x", padx=20, pady=10)

        # Etiqueta para mostrar el resultado teórico
        self.label_resultado = ctk.CTkLabel(self.frame_controles, text="Resultado: ", font=ctk.CTkFont(size=16, weight="bold"))
        self.label_resultado.pack(pady=20, padx=20, anchor="w")

        # --- PANEL DERECHO: Visualización Gráfica ---
        self.frame_grafico = ctk.CTkFrame(self)
        self.frame_grafico.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=10)
        
        # Configuración inicial de Matplotlib
        self.fig, self.ax = plt.subplots(figsize=(6, 5), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_grafico)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        
        # Gráfico por defecto
        self.ax.set_title("Visualización de la Función")
        self.ax.set_xlabel("x")
        self.ax.set_ylabel("f(x)")
        self.ax.grid(True)
        self.canvas.draw()

    def calcular_limite_y_graficar(self):
        """
        Función que se ejecuta al presionar el botón.
        Evalúa el límite usando SymPy y grafica con Matplotlib (sin NumPy).
        """
        # Limpiar gráfico y mensajes previos
        self.ax.clear()
        self.label_resultado.configure(text="Resultado: Calculando...")
        self.update_idletasks()

        func_str = self.entry_func.get()
        h_str = self.entry_h.get().strip()

        if not func_str or not h_str:
            self.label_resultado.configure(text="Error: Complete los campos.")
            return

        try:
            # 1. Definición Simbólica y Análisis Teórico (SymPy)
            x = sp.Symbol('x')
            f_expr = sp.sympify(func_str)

            # Manejo de límites al infinito
            if h_str.lower() in ['oo', 'inf', '+oo', 'infinito']:
                h_val = sp.oo
            elif h_str.lower() in ['-oo', '-inf', '-infinito']:
                h_val = -sp.oo
            else:
                h_val = sp.sympify(h_str)

            # Evaluación del límite
            limite_resultado = sp.limit(f_expr, x, h_val)
            self.label_resultado.configure(text=f"Límite: {limite_resultado}")

            # 2. Renderizado del Gráfico (Matplotlib sin NumPy)
            # Determinar el rango de ploteo según si el límite es al infinito o a un punto
            if h_val == sp.oo:
                x_min, x_max = 0, 100
            elif h_val == -sp.oo:
                x_min, x_max = -100, 0
            else:
                h_float = float(h_val)
                x_min, x_max = h_float - 10, h_float + 10

            # Generar puntos X iterando manualmente (Reemplazo de np.linspace)
            num_puntos = 500
            paso = (x_max - x_min) / num_puntos
            x_vals = [x_min + i * paso for i in range(num_puntos + 1)]
            y_vals = []

            # Lambdify convierte la expresión SymPy para que use la librería 'math' estándar
            f_numerica = sp.lambdify(x, f_expr, modules=['math'])

            # Evaluar Y para cada X, manejando excepciones matemáticas (ej: división por cero)
            for val in x_vals:
                try:
                    y = f_numerica(val)
                    # Evitar graficar números complejos o infinitos que rompan el ploteo
                    if isinstance(y, complex) or math.isinf(y) or math.isnan(y):
                        y_vals.append(None)
                    else:
                        y_vals.append(y)
                except Exception:
                    y_vals.append(None)

            # Dibujar la función
            self.ax.plot(x_vals, y_vals, color='blue', label=f'$f(x)={sp.latex(f_expr)}$')

            # Dibujar una línea punteada indicando el valor hacia el que tiende x (h) — solo si h es finito
            if not h_val.is_infinite:
                try:
                    self.ax.axvline(x=float(h_val), color='red', linestyle='--', label=f'x \u2192 {float(h_val):.2f}')
                except Exception:
                    pass

            # Si el límite es un número real y finito, marcarlo.
            # - Si h es infinito: dibujar una asíntota horizontal (línea y = L)
            # - Si h es finito: marcar el punto (h, L)
            if limite_resultado.is_real and not limite_resultado.is_infinite:
                try:
                    if h_val.is_infinite:
                        self.ax.axhline(y=float(limite_resultado), color='green', linestyle='--', label=f'Límite = {float(limite_resultado):.2f}')
                    else:
                        self.ax.plot(float(h_val), float(limite_resultado), marker='o', color='red', label=f'Límite en {float(h_val):.2f}')
                except Exception:
                    pass
            else:
                # Si el límite no es un número finito (por ejemplo infinito), mostrar una nota en el gráfico
                if limite_resultado.is_infinite:
                    self.ax.text(0.02, 0.95, f'Límite = {limite_resultado}', transform=self.ax.transAxes, verticalalignment='top')

            # Configurar visuales del gráfico
            self.ax.set_title("Comportamiento de la Función")
            self.ax.set_xlabel("x")
            self.ax.set_ylabel("f(x)")
            self.ax.grid(True, linestyle='--', alpha=0.7)
            self.ax.legend()

            # Actualizar el canvas en la interfaz
            self.canvas.draw()

        except sp.SympifyError:
            self.label_resultado.configure(text="Error: Expresión matemática inválida.")
            self._limpiar_grafico()
        except Exception as e:
            self.label_resultado.configure(text=f"Error inesperado: {str(e)}")
            self._limpiar_grafico()

    def _limpiar_grafico(self):
        """Limpia el gráfico en caso de error para evitar confusiones."""
        self.ax.clear()
        self.ax.set_title("Visualización de la Función")
        self.ax.grid(True)
        self.canvas.draw()

if __name__ == "__main__":
    app = CalculadoraLimitesApp()
    app.mainloop()