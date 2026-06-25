import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d import Axes3D  
import numpy as np
import math


class Otimizador3DTab(ttk.Frame):
    def __init__(self, parent, tab_controlador, tab_simulador):
        super().__init__(parent)
        
        self.tab_controlador = tab_controlador
        self.tab_simulador = tab_simulador
        
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)  
        self.rowconfigure(1, weight=1)  

        # --- PAINEL ESQUERDO: LIMITES DA VARREDURA ---
        self.frame_inputs = ttk.LabelFrame(self, text=" Limites de Varredura do Grid ", padding=15)
        self.frame_inputs.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=10, pady=10)

        self.campos = {}
        inputs_locais = {
            "Offset": "24.0",
            "Tempo total Sim (s)": "400.0",
            "Kp Mínimo": "0.1",
            "Kp Máximo": "2.0",
            "Ti Mínimo (s)": "1.0",
            "Ti Máximo (s)": "200.0"
        }
        
        linha = 1
        for label_text, val in inputs_locais.items():
            lbl = ttk.Label(self.frame_inputs, text=label_text, font=("Arial", 10, "bold"))
            lbl.grid(row=linha, column=0, sticky="w", pady=4)
            entry = ttk.Entry(self.frame_inputs, width=10, justify='center')
            entry.insert(0, val)
            entry.grid(row=linha, column=1, pady=4, padx=5)
            self.campos[label_text] = entry
            linha += 1

        self.btn_otimizar = ttk.Button(self.frame_inputs, text="Gerar Otimização 3D", command=self.processar_otimizacao)
        self.btn_otimizar.grid(row=linha, column=0, columnspan=2, pady=20, sticky="ew")

        # --- PAINEL DIREITO SUPERIOR: SUPERFÍCIE 3D ---
        self.frame_plot = ttk.Frame(self)
        self.frame_plot.grid(row=0, column=1, sticky="nsew", padx=10, pady=5)

        self.fig = plt.figure(figsize=(6, 3.5), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_plot)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # --- PAINEL DIREITO INFERIOR: TABELA ITAE ---
        self.frame_table = ttk.LabelFrame(self, text=" Matriz de Resultados (Ordenada por melhor ITAE) ", padding=5)
        self.frame_table.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)

        colunas = ("kp", "ti", "itae")
        self.tree = ttk.Treeview(self.frame_table, columns=colunas, show="headings")
        
        self.tree.heading("kp", text="Ganho Proporcional (Kp)")
        self.tree.heading("ti", text="Tempo Integral (Ti s)")
        self.tree.heading("itae", text="Índice Desempenho ITAE")

        for col in colunas:
            self.tree.column(col, anchor="center", width=150)

        scrollbar = ttk.Scrollbar(self.frame_table, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def rodar_simulacao_interna(self, kp, ti, td, fs, offset_graus, tempo_max, s_min, s_max, delta_t, delta_m, t_estab, tm):
        ts = 1.0 / fs
        max_amostras = max(10, int(tempo_max / ts))

        span_sensor = s_max - s_min
        k_ganho_planta = ((delta_t / span_sensor) * 100) / delta_m
        tau = t_estab / 5.0
        
        b1 = math.exp(-ts / tau)
        a1_proc = k_ganho_planta * (1 - b1)
        atraso_total = int(round(tm / ts)) + 1

        offset_pct = ((offset_graus - s_min) / span_sensor) * 100
        sp_pct = ((float(self.tab_controlador.campos["Setpoint"].get()) - s_min) / span_sensor) * 100

        a0_ctrl = kp * (1 + (ts / ti) + (td / ts))
        a1_ctrl = -kp * (1 + (2 * td / ts))
        a2_ctrl = kp * (td / ts)

        c_prev = offset_pct
        c_historico = [offset_pct] * (atraso_total + 1)
        vm_historico = [0.0] * (atraso_total + 1)
        e_historico = [0.0, 0.0]
        
        itae = 0.0

        for k in range(0, max_amostras + 1):
            if k >= 1:
                m_atrasado = vm_historico[-atraso_total]
                c_atual = (b1 * c_prev) + (a1_proc * m_atrasado) + (1 - b1) * offset_pct
                c_prev = c_atual
            else:
                c_atual = offset_pct

            e_k = sp_pct - c_atual
            itae += (k * ts) * abs(e_k)
            
            delta_m = (a0_ctrl * e_k) + (a1_ctrl * e_historico[-1]) + (a2_ctrl * e_historico[-2])
            m_atual = vm_historico[-1] + delta_m
            vm_k = max(0.0, min(100.0, m_atual))

            c_historico.append(c_atual)
            vm_historico.append(vm_k)
            e_historico.append(e_k)

        return itae

    def processar_otimizacao(self):
        try:
            for item in self.tree.get_children():
                self.tree.delete(item)

            # 1. Parâmetros locais e limites definidos pelo usuário
            offset_graus = float(self.campos["Offset"].get())
            tempo_max = float(self.campos["Tempo total Sim (s)"].get())
            
            kp_min = float(self.campos["Kp Mínimo"].get())
            kp_max = float(self.campos["Kp Máximo"].get())
            ti_min = float(self.campos["Ti Mínimo (s)"].get())
            ti_max = float(self.campos["Ti Máximo (s)"].get())

            # 2. Parâmetros nominais importados das outras abas
            td = float(self.tab_controlador.campos["Td (s)"].get())
            fs = float(self.tab_controlador.campos["fs (Hz)"].get())

            s_min = float(self.tab_simulador.campos["Sensor mín"].get())
            s_max = float(self.tab_simulador.campos["Sensor máx"].get())
            delta_t = float(self.tab_simulador.campos["ΔVP medido"].get())
            delta_m = float(self.tab_simulador.campos["ΔM aplicado (%)"].get())
            t_estab = float(self.tab_simulador.campos["Tempo estabilização (s)"].get())
            tm = float(self.tab_simulador.campos["Tempo morto Tm (s)"].get())

            # 3. Geração do Grid baseado estritamente nos limites da tela (20x20)
            kp_vetor = np.linspace(kp_min, kp_max, 20)
            ti_vetor = np.linspace(ti_min, ti_max, 20)
            
            X, Y = np.meshgrid(kp_vetor, ti_vetor)
            Z = np.zeros(X.shape)

            # 4. Execução em lote das simulações
            lista_resultados = []
            for i in range(X.shape[0]):
                for j in range(X.shape[1]):
                    kp_teste = X[i, j]
                    ti_teste = Y[i, j]
                    
                    itae_val = self.rodar_simulacao_interna(
                        kp_teste, ti_teste, td, fs, offset_graus, tempo_max,
                        s_min, s_max, delta_t, delta_m, t_estab, tm
                    )
                    Z[i, j] = itae_val
                    lista_resultados.append((kp_teste, ti_teste, itae_val))

            # 5. Ordena os resultados para exibir na tabela (Do menor ITAE para o maior)
            lista_resultados.sort(key=lambda x: x[2])

            # Popula a tabela com os resultados do grid ordenados (Exibe as 50 melhores combinações)
            for res in lista_resultados[:50]:
                self.tree.insert("", tk.END, values=(f"{res[0]:.4f}", f"{res[1]:.2f}", f"{res[2]:.2f}"))

            # 6. Plotagem da Superfície 3D
            self.fig.clf()
            ax = self.fig.add_subplot(111, projection='3d')
            surf = ax.plot_surface(X, Y, Z, cmap='turbo', edgecolor='none', alpha=0.85)
            
            ax.set_title("Superfície 3D de Otimização do Critério ITAE", fontsize=11, fontweight='bold')
            ax.set_xlabel("Ganho Kp")
            ax.set_ylabel("Tempo Ti (s)")
            ax.set_zlabel("Métrica ITAE")
            
            self.fig.colorbar(surf, ax=ax, shrink=0.5, aspect=10, pad=0.08)
            self.canvas.draw()

        except ValueError:
            messagebox.showerror("Erro", "Verifique se todas as abas e limites possuem dados numéricos válidos.")
        except Exception as e:
            messagebox.showerror("Erro no Processamento", f"Ocorreu um erro: {e}")