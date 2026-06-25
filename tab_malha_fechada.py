import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import math


class MalhaFechadaTab(ttk.Frame):
    def __init__(self, parent, tab_controlador, tab_simulador):
        super().__init__(parent)
        
        self.tab_controlador = tab_controlador
        self.tab_simulador = tab_simulador
        
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # --- PAINEL ESQUERDO: CONTROLES DO GRÁFICO ---
        self.frame_inputs = ttk.LabelFrame(self, text=" Controle em malha fechada ", padding=15)
        self.frame_inputs.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        lbl_info = ttk.Label(self.frame_inputs, text="Os parâmetros do PID e da\nplanta são importados\nautomaticamente das abas A e B.", 
                             font=("Arial", 9, "italic"), foreground="#555", justify="center")
        lbl_info.grid(row=0, column=0, columnspan=2, pady=(0, 15))

        self.campos = {}
        # ADICIONADO: "Setpoint (°C)" agora pode ser definido diretamente aqui
        inputs_locais = {
            "Offset": "24.0",
            "Setpoint": "60.0",
            "Eixo Y máx": "110.0",
            "Eixo X máx (s)": "400.0"
        }
        
        linha = 1
        for label_text, val in inputs_locais.items():
            lbl = ttk.Label(self.frame_inputs, text=label_text, font=("Arial", 10, "bold"))
            lbl.grid(row=linha, column=0, sticky="w", pady=5)
            entry = ttk.Entry(self.frame_inputs, width=10, justify='center')
            entry.insert(0, val)
            entry.grid(row=linha, column=1, pady=5, padx=5)
            self.campos[label_text] = entry
            linha += 1

        self.btn_simular = ttk.Button(self.frame_inputs, text="Simular Malha Fechada", command=self.simular_malha_fechada)
        self.btn_simular.grid(row=linha, column=0, columnspan=2, pady=20, sticky="ew")
        
        # --- Label para exibir o ITAE calculado ---
        self.lbl_itae = ttk.Label(self.frame_inputs, text="Desempenho ITAE: ---", font=("Arial", 10, "bold"), foreground="#2b579a")
        self.lbl_itae.grid(row=linha+1, column=0, columnspan=2, pady=10)

        # --- PAINEL DIREITO: GRÁFICO 2D ---
        self.frame_plot = ttk.Frame(self)
        self.frame_plot.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        self.fig, self.ax = plt.subplots(figsize=(6, 5), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_plot)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def simular_malha_fechada(self):
        try:
            # 1. Pega os valores locais da Aba C (Limites do gráfico, Offset e Setpoint)
            offset_graus = float(self.campos["Offset"].get())
            sp_graus = float(self.campos["Setpoint"].get())  # ALTERADO: Lê diretamente da tela local
            tempo_max = float(self.campos["Eixo X máx (s)"].get())
            y_max = float(self.campos["Eixo Y máx"].get())

            # 2. Puxa os valores da Aba A (Controlador)
            kp = float(self.tab_controlador.campos["Kp"].get())
            ti = float(self.tab_controlador.campos["Ti (s)"].get())
            td = float(self.tab_controlador.campos["Td (s)"].get())
            fs = float(self.tab_controlador.campos["fs (Hz)"].get())
            
            ts = 1.0 / fs 

            # Calcula as amostras dinamicamente a partir do tempo final do eixo X
            max_amostras = max(10, int(tempo_max / ts))

            # 3. Puxa os valores da Aba B (Simulador/Física da Planta)
            s_min = float(self.tab_simulador.campos["Sensor mín"].get())
            s_max = float(self.tab_simulador.campos["Sensor máx"].get())
            delta_t = float(self.tab_simulador.campos["ΔVP medido"].get())
            delta_m = float(self.tab_simulador.campos["ΔM aplicado (%)"].get())
            t_estab = float(self.tab_simulador.campos["Tempo estabilização (s)"].get())
            tm = float(self.tab_simulador.campos["Tempo morto Tm (s)"].get())

            # 4. Cálculos físicos e discretização da Planta (Processo)
            span_sensor = s_max - s_min
            k_ganho_planta = ((delta_t / span_sensor) * 100) / delta_m
            tau = t_estab / 5.0
            
            b1 = math.exp(-ts / tau)
            a1_proc = k_ganho_planta * (1 - b1)
            atraso_total = int(round(tm / ts)) + 1

            # Normaliza Temperaturas (°C) para Escala do Sensor (%)
            offset_pct = ((offset_graus - s_min) / span_sensor) * 100
            sp_pct = ((sp_graus - s_min) / span_sensor) * 100

            # 5. Coeficientes do Controlador PID
            a0_ctrl = kp * (1 + (ts / ti) + (td / ts))
            a1_ctrl = -kp * (1 + (2 * td / ts))
            a2_ctrl = kp * (td / ts)

            # 6. Inicialização das estruturas do Loop
            amostras = list(range(-atraso_total, max_amostras + 1))
            c_dict = {k: offset_pct for k in amostras}  
            vm_dict = {k: 0.0 for k in amostras}        
            m_dict = {k: 0.0 for k in amostras}         
            e_dict = {k: 0.0 for k in amostras}         

            itae_acumulado = 0.0  

            # 7. Loop de Malha Fechada
            for k in range(0, max_amostras + 1):
                if k >= 1:
                    m_atrasado = vm_dict[k - atraso_total]
                    c_dict[k] = (b1 * c_dict[k - 1]) + (a1_proc * m_atrasado) + (1 - b1) * offset_pct
                
                e_dict[k] = sp_pct - c_dict[k]
                
                # Cálculo do ITAE: (Tempo) * |Erro|
                itae_acumulado += (k * ts) * abs(e_dict[k])

                delta_m = (a0_ctrl * e_dict[k]) + (a1_ctrl * e_dict.get(k - 1, 0.0)) + (a2_ctrl * e_dict.get(k - 2, 0.0))
                
                # Anti-Windup real: parte do valor saturado anterior
                m_atual = vm_dict.get(k - 1, 0.0) + delta_m
                
                vm_dict[k] = max(0.0, min(100.0, m_atual))

            self.lbl_itae.config(text=f"Desempenho ITAE: {itae_acumulado:.2f}")

            # 8. Extrai os dados para o gráfico e cria o vetor de tempo
            c_graus_plot = [(c_dict[k] / 100.0) * span_sensor + s_min for k in amostras]
            vm_plot = [vm_dict[k] for k in amostras]
            sp_linha = [sp_graus] * len(amostras)
            tempos = [k * ts for k in amostras]

            # 9. Plotagem com os limites travados pelo usuário
            self.ax.clear()
            self.ax.plot(tempos, c_graus_plot, '-', color='#ff7f0e', linewidth=2, label='Sensor VP')
            self.ax.plot(tempos, sp_linha, '--', color='#d62728', linewidth=1.5, label='Setpoint SP')
            self.ax.plot(tempos, vm_plot, '-', color='#1f77b4', linewidth=1.5, alpha=0.7, label='Ação PID VM (%)')
            
            self.ax.set_title("Resposta do sistema integrado (malha fechada)", fontsize=11, fontweight='bold')
            self.ax.set_xlabel("Tempo (segundos)")
            self.ax.set_ylabel("Escala das Variáveis")
            
            self.ax.set_xlim(left=-5, right=tempo_max)
            self.ax.set_ylim(bottom=-5, top=y_max)
            
            self.ax.grid(True, linestyle='--', alpha=0.6)
            self.ax.legend()
            self.canvas.draw()

        except ValueError:
            messagebox.showerror("Erro", "Verifique se as Abas A e B possuem apenas números válidos.")
        except Exception as e:
            messagebox.showerror("Erro na Simulação", f"Erro inesperado: {e}")
