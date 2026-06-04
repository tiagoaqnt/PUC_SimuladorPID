import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.mplot3d import Axes3D  
import numpy as np


class OtimizadorTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # --- PAINEL ESQUERDO: APENAS COEFICIENTES E EQUAÇÕES ---
        self.frame_inputs = ttk.LabelFrame(self, text=" Configuração da Malha Fechada ", padding=12)
        self.frame_inputs.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # 1. Seção do Simulador (Parte B)
        lbl_ref_proc = ttk.Label(self.frame_inputs, text="Referência do Forno:\nc(k) = b1·c(k-1) + a1·m(k-d) + offset", 
                                 font=("Arial", 9, "italic"), foreground="#555", justify="center")
        lbl_ref_proc.grid(row=0, column=0, columnspan=2, pady=(0, 10))

        self.campos = {}
        inputs_processo = {
            "Coeficiente b1": "0.8607",
            "Coeficiente a1": "0.0398",
            "Atraso d (amostras)": "4",
            "Offset (°C ou %)": "24.0"
        }
        
        linha = 1
        for label_text, val in inputs_processo.items():
            lbl = ttk.Label(self.frame_inputs, text=label_text, font=("Arial", 9, "bold"))
            lbl.grid(row=linha, column=0, sticky="w", pady=3)
            entry = ttk.Entry(self.frame_inputs, width=12, justify='center')
            entry.insert(0, val)
            entry.grid(row=linha, column=1, pady=3, padx=10)
            self.campos[label_text] = entry
            linha += 1

        # Separador Visual
        ttk.Separator(self.frame_inputs, orient='horizontal').grid(row=linha, column=0, columnspan=2, sticky="ew", pady=10)
        linha += 1

        # 2. Seção do Controlador (Parte A - Necessário manter Kp e Ti abertos para poder variar no 3D)
        lbl_ref_ctrl = ttk.Label(self.frame_inputs, text="Parâmetros de Sintonia PID:", 
                                 font=("Arial", 9, "italic"), foreground="#555")
        lbl_ref_ctrl.grid(row=linha, column=0, columnspan=2, pady=(0, 5))
        linha += 1

        inputs_controlador = {
            "Kp Nominal": "0.9",
            "Ti Nominal (s)": "15.0",
            "Td (s)": "0.1",
            "Ts Amostragem (s)": "9.0",
            "Setpoint Desejado": "35.0",
            "Amostras máx": "100"
        }

        for label_text, val in inputs_controlador.items():
            lbl = ttk.Label(self.frame_inputs, text=label_text, font=("Arial", 9, "bold"))
            lbl.grid(row=linha, column=0, sticky="w", pady=3)
            entry = ttk.Entry(self.frame_inputs, width=12, justify='center')
            entry.insert(0, val)
            entry.grid(row=linha, column=1, pady=3, padx=10)
            self.campos[label_text] = entry
            linha += 1

        # Botões e Indicadores
        self.btn_2d = ttk.Button(self.frame_inputs, text="Ver Resposta Temporal (2D)", command=self.simular_2d)
        self.btn_2d.grid(row=linha, column=0, columnspan=2, pady=(15, 5), sticky="ew")
        
        self.btn_3d = ttk.Button(self.frame_inputs, text="Gerar Superfície Otimização (3D)", command=self.simular_3d)
        self.btn_3d.grid(row=linha+1, column=0, columnspan=2, pady=5, sticky="ew")

        self.lbl_iae = ttk.Label(self.frame_inputs, text="Desempenho IAE: ---", 
                                 font=("Arial", 9, "bold"), foreground="#2b579a")
        self.lbl_iae.grid(row=linha+2, column=0, columnspan=2, pady=5)

        # --- PAINEL DIREITO: GRÁFICO DINÂMICO ---
        self.frame_plot = ttk.Frame(self)
        self.frame_plot.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        self.fig = plt.figure(figsize=(6, 5), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_plot)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.simular_2d()

    def rodar_loop_matematico(self, kp, ti, td, max_amostras):
        """Loop de malha fechada direto baseado nos coeficientes inseridos"""
        # Resgata coeficientes do processo direto da tela
        b1 = float(self.campos["Coeficiente b1"].get())
        a1_proc = float(self.campos["Coeficiente a1"].get())
        atraso_total = int(self.campos["Atraso d (amostras)"].get())
        offset = float(self.campos["Offset (°C ou %)"].get())
        
        ts = float(self.campos["Ts Amostragem (s)"].get())
        sp = float(self.campos["Setpoint Desejado"].get())
        
        # Coeficientes do Controlador PID recalculados dinamicamente para a varredura
        a0_ctrl = kp * (1 + (ts / ti) + (td / ts))
        a1_ctrl = -kp * (1 + (2 * td / ts))
        a2_ctrl = kp * (td / ts)
        
        amostras = list(range(-atraso_total, max_amostras + 1))
        c_dict = {k: offset for k in amostras}  # Começa estabilizado no offset
        vm_dict = {k: 0.0 for k in amostras}
        e_dict = {k: 0.0 for k in amostras}
        
        iae_acumulado = 0.0
        
        for k in range(0, max_amostras + 1):
            if k >= 1:
                m_atrasado = vm_dict[k - atraso_total]
                c_dict[k] = (b1 * c_dict[k - 1]) + (a1_proc * m_atrasado) + (1 - b1) * offset
            
            e_dict[k] = sp - c_dict[k]
            iae_acumulado += abs(e_dict[k])
            
            delta_m = (a0_ctrl * e_dict[k]) + (a1_ctrl * e_dict.get(k - 1, 0.0)) + (a2_ctrl * e_dict.get(k - 2, 0.0))
            m_atual = vm_dict[k - 1] + delta_m
            vm_dict[k] = max(0.0, min(100.0, m_atual))
            
        return amostras, c_dict, vm_dict, iae_acumulado, sp

    def simular_2d(self):
        try:
            kp = float(self.campos["Kp Nominal"].get())
            ti = float(self.campos["Ti Nominal (s)"].get())
            td = float(self.campos["Td (s)"].get())
            max_amostras = int(self.campos["Amostras máx"].get())
            
            amostras, c_dict, vm_dict, iae, sp = self.rodar_loop_matematico(kp, ti, td, max_amostras)
            self.lbl_iae.config(text=f"Desempenho IAE: {iae:.2f}")
            
            c_vals = [c_dict[k] for k in amostras]
            vm_vals = [vm_dict[k] for k in amostras]
            sp_linha = [sp] * len(amostras)
            
            self.fig.clf()
            ax = self.fig.add_subplot(111)
            ax.plot(amostras, c_vals, 'o-', color='#ff7f0e', markersize=3, label='Saída do Forno c(k)')
            ax.plot(amostras, sp_linha, '--', color='r', label='Setpoint (SP)')
            ax.plot(amostras, vm_vals, 'o-', color='#1f77b4', markersize=3, alpha=0.5, label='Ação do Controlador VM (%)')
            
            ax.set_title("Resposta Temporal em Malha Fechada (Parte C)", fontsize=11, fontweight='bold')
            ax.set_xlabel("Amostra (k)")
            ax.set_ylabel("Escala das Variáveis")
            ax.grid(True, linestyle='--', alpha=0.6)
            ax.legend()
            self.canvas.draw()
        except ValueError:
            messagebox.showerror("Erro", "Verifique os campos numéricos.")

    def simular_3d(self):
        try:
            kp_nom = float(self.campos["Kp Nominal"].get())
            ti_nom = float(self.campos["Ti Nominal (s)"].get())
            td = float(self.campos["Td (s)"].get())
            max_amostras = int(self.campos["Amostras máx"].get())
            
            kp_vetor = np.linspace(max(0.05, kp_nom * 0.1), kp_nom * 2.5, 20)
            ti_vetor = np.linspace(max(1.0, ti_nom * 0.1), ti_nom * 2.5, 20)
            X, Y = np.meshgrid(kp_vetor, ti_vetor)
            Z = np.zeros(X.shape)
            
            for i in range(X.shape[0]):
                for j in range(X.shape[1]):
                    _, _, _, iae_val, _ = self.rodar_loop_matematico(X[i, j], Y[i, j], td, max_amostras)
                    Z[i, j] = iae_val
            
            self.fig.clf()
            ax = self.fig.add_subplot(111, projection='3d')
            surf = ax.plot_surface(X, Y, Z, cmap='turbo', edgecolor='none', alpha=0.85)
            
            ax.set_title("Superfície 3D de Otimização do Critério IAE", fontsize=11, fontweight='bold')
            ax.set_xlabel("Ganho Kp")
            ax.set_ylabel("Tempo Ti (s)")
            ax.set_zlabel("Desempenho IAE")
            self.fig.colorbar(surf, ax=ax, shrink=0.5, aspect=10, pad=0.08)
            self.canvas.draw()
        except ValueError:
            messagebox.showerror("Erro", "Erro ao processar simulação 3D.")