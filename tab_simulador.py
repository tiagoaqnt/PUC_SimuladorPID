import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import math


class SimuladorTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Configuração de pesos da aba
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)  # Linha do Gráfico
        self.rowconfigure(1, weight=1)  # Linha da Tabela

        # --- PAINEL ESQUERDO: INPUTS PRÁTICOS ---
        self.frame_inputs = ttk.LabelFrame(self, text=" Modelagem Prática do Forno ", padding=12)
        self.frame_inputs.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=10, pady=10)

        self.campos = {}
        # Valores padrão baseados rigorosamente nos seus exemplos práticos do caderno
        valores_padrao = {
            "Sensor mín (°C)": "10.0",
            "Sensor máx (°C)": "80.0",
            "ΔM aplicado (%)": "50.0",
            "ΔT medido (°C)": "40.0",
            "Tempo estabilização (s)": "300",
            "Tempo morto Tm (s)": "30",
            "Temp. inicial (°C)": "24.0",
            "Amostras máx": "100"
        }
        
        for i, (label_text, val) in enumerate(valores_padrao.items()):
            lbl = ttk.Label(self.frame_inputs, text=label_text, font=("Arial", 9, "bold"))
            lbl.grid(row=i, column=0, sticky="w", pady=4)
            
            entry = ttk.Entry(self, width=12, justify='center')
            entry.insert(0, val)
            entry.grid(row=i, column=1, in_=self.frame_inputs, pady=4, padx=10)
            self.campos[label_text] = entry

        # Vincula o evento de digitação no Tempo de Estabilização para sugerir o Ts dinamicamente
        self.campos["Tempo estabilização (s)"].bind("<KeyRelease>", self.calcular_faixa_astrom)

        # Labels informativas sobre os cálculos dinâmicos realizados
        self.lbl_astrom = ttk.Label(self.frame_inputs, text="Faixa Ts ideal: ---", font=("Arial", 9, "italic"), foreground="#2b579a")
        self.lbl_astrom.grid(row=8, column=0, columnspan=2, pady=2)

        self.lbl_ganho_calc = ttk.Label(self.frame_inputs, text="Ganho K calculado: ---", font=("Arial", 9, "bold"), foreground="#e81123")
        self.lbl_ganho_calc.grid(row=9, column=0, columnspan=2, pady=2)

        self.lbl_equacao = ttk.Label(self.frame_inputs, text="c(k) = b1*c(k-1) + a1*m(k-3)", font=("Arial", 9, "italic"), foreground="#555")
        self.lbl_equacao.grid(row=10, column=0, columnspan=2, pady=(10, 2))

        # Botão de Execução
        self.btn_simular = ttk.Button(self.frame_inputs, text="Simular Parte B", command=self.simular_parte_b)
        self.btn_simular.grid(row=11, column=0, columnspan=2, pady=10, sticky="ew")

        # --- PAINEL DIREITO SUPERIOR: GRÁFICO ---
        self.frame_plot = ttk.Frame(self)
        self.frame_plot.grid(row=0, column=1, sticky="nsew", padx=10, pady=5)

        self.fig, self.ax = plt.subplots(figsize=(6, 3.2), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_plot)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # --- PAINEL DIREITO INFERIOR: TABELA ---
        self.frame_table = ttk.LabelFrame(self, text="Tabela de dados", padding=5)
        self.frame_table.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)

        colunas = ("k", "t", "vm", "ck_pct", "ck_graus")
        self.tree = ttk.Treeview(self.frame_table, columns=colunas, show="headings")
        
        self.tree.heading("k", text="Amostra (k)")
        self.tree.heading("t", text="Tempo real (s)")
        self.tree.heading("vm", text="Entrada VM (%)")
        self.tree.heading("ck_pct", text="Saída c(k) (%)")
        self.tree.heading("ck_graus", text="Temperatura (°C)")

        for col in colunas:
            self.tree.column(col, anchor="center", width=120)

        scrollbar = ttk.Scrollbar(self.frame_table, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Executa os cálculos iniciais baseados no caderno
        self.calcular_faixa_astrom()
        self.simular_parte_b()

    def calcular_faixa_astrom(self, event=None):
        """Calcula dinamicamente a recomendação de Karl Åström com base no tempo de subida/estabilização"""
        try:
            t_estab = float(self.campos["Tempo estabilização (s)"].get())
            tau = t_estab / 5.0
            ts_min = tau / 10.0
            ts_max = tau / 5.0
            self.lbl_astrom.config(text=f"Åström ({ts_min:.0f}s < Ts < {ts_max:.0f}s)")
            return round((ts_min + ts_max) / 2.0)  # Retorna o ponto médio padrão como sugestão
        except ValueError:
            self.lbl_astrom.config(text="Faixa Ts ideal: insira o tempo")
            return 1.0

    def simular_parte_b(self):
        try:
            for i in self.tree.get_children():
                self.tree.delete(i)

            # 1. Captura e Cálculo Prático do Ganho K conforme o SPAN do seu Sensor
            s_min = float(self.campos["Sensor mín (°C)"].get())
            s_max = float(self.campos["Sensor máx (°C)"].get())
            delta_t = float(self.campos["ΔT medido (°C)"].get())
            delta_m = float(self.campos["ΔM aplicado (%)"].get())
            
            span_sensor = s_max - s_min
            if span_sensor <= 0:
                raise ValueError("O valor máximo do sensor deve ser maior que o mínimo.")
                
            # %ΔC = (Variação de Temperatura / SPAN) * 100
            pct_delta_c = (delta_t / span_sensor) * 100
            k_ganho = pct_delta_c / delta_m
            
            self.lbl_ganho_calc.config(text=f"Ganho K: {k_ganho:.4f} (%/%)")

            # 2. Resgate dos Tempos e Cálculo do Período de Amostragem Ts Ótimo
            t_estab = float(self.campos["Tempo estabilização (s)"].get())
            tau = t_estab / 5.0
            ts = self.calcular_faixa_astrom()  # Adota o Ts ideal calculado de acordo com o tempo de subida
            
            tm = float(self.campos["Tempo morto Tm (s)"].get())
            t_inicial = float(self.campos["Temp. inicial (°C)"].get())
            max_amostras = int(self.campos["Amostras máx"].get())

            # 3. Discretização exata do processo físico
            b1 = math.exp(-ts / tau)
            a1 = k_ganho * (1 - b1)
            
            # Relação exata do tempo morto discreto
            atraso_puro = int(round(tm / ts))
            atraso_total = 1 + atraso_puro
            
            self.lbl_equacao.config(text=f"c(k) = {b1:.4f}c(k-1) + {a1:.4f}m(k-{atraso_total})")

            # 4. Condições Iniciais em Percentagem do Sensor (Equilíbrio Térmico Inicial)
            c_inicial_pct = ((t_inicial - s_min) / span_sensor) * 100
            offset_termico = (1 - b1) * c_inicial_pct

            amostras_historico = list(range(-atraso_total, max_amostras + 1))
            
            # Montagem do perfil de entrada VM (Degrau de 50% saltando para 100% em k=50)
            vm_dict = {}
            for k in amostras_historico:
                if k < 0:
                    vm_dict[k] = 0.0
                elif 0 <= k < 50:
                    vm_dict[k] = 50.0
                else:
                    vm_dict[k] = 100.0

            # Inicializa a saída com a condição térmica inicial
            c_dict = {}
            for k in range(-atraso_total, 1):
                c_dict[k] = c_inicial_pct

            # Loop recursivo do Simulador por Equações de Diferenças
            for k in range(1, max_amostras + 1):
                m_atrasado = vm_dict[k - atraso_total]
                c_anterior = c_dict[k - 1]
                c_dict[k] = (b1 * c_anterior) + (a1 * m_atrasado) + offset_termico

            # 5. Preenchimento da Tabela e preparação das listas de plotagem
            vm_plot = []
            c_pct_plot = []
            c_graus_plot = []
            
            for k in amostras_historico:
                vm_plot.append(vm_dict[k])
                c_pct_plot.append(c_dict[k])
                
                # Conversão inversa: transforma a saída normalizada (%) de volta para graus físicos (°C)
                t_graus = (c_dict[k] / 100.0) * span_sensor + s_min
                c_graus_plot.append(t_graus)
                
                t_real = k * ts
                self.tree.insert("", tk.END, values=(
                    k, f"{t_real:.0f}", f"{vm_dict[k]:.1f}", f"{c_dict[k]:.2f}", f"{t_graus:.2f}"
                ))

            # 6. Atualização Dinâmica do Gráfico do Matplotlib
            self.ax.clear()
            self.ax.plot(amostras_historico, vm_plot, 'o-', color='#1f77b4', linewidth=1.5, label='VM (Potência %)')
            self.ax.plot(amostras_historico, c_pct_plot, 'o-', color='#2ca02c', linewidth=1.5, label='c(k) saída normalizada (%)')
            self.ax.plot(amostras_historico, c_graus_plot, 'o-', color='#ff7f0e', linewidth=2, label='Temperatura do forno (°C)')
            self.ax.set_title("Simulação em malha aberta", fontsize=11, fontweight='bold')
            self.ax.set_xlabel(f"Amostra k (Ts = {ts}s)")
            self.ax.set_ylabel("Escala das variáveis")
            self.ax.grid(True, linestyle='--', alpha=0.6)
            self.ax.legend()
            self.canvas.draw()

        except ValueError as e:
            messagebox.showerror("Erro de Validação", str(e) if str(e) else "Insira números válidos.")
        except ZeroDivisionError:
            messagebox.showerror("Erro", "Divisão por zero detectada. Verifique as diferenças dos parâmetros.")
