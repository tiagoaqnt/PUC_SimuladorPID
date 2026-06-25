import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class ControladorTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Configuração de pesos da aba (Esquerda fixa, direita expande dividida entre gráfico e tabela)
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)  # Linha do Gráfico
        self.rowconfigure(1, weight=1)  # Linha da Tabela

        # --- PAINEL ESQUERDO: INPUTS (Ocupa as duas linhas verticais) ---
        self.frame_inputs = ttk.LabelFrame(self, text=" Parâmetros do controlador ", padding=15)
        self.frame_inputs.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=10, pady=10)

        self.campos = {}
        valores_padrao = {
            "Kp": "0.9",
            "Ti (s)": "1",
            "Td (s)": "0.01", 
            "fs (Hz)": "10",
            "VP inicial": "24.0",
            "Setpoint": "60.0", 
            "Amostras máx.": "100"
        }
        
        for i, (label_text, val) in enumerate(valores_padrao.items()):
            lbl = ttk.Label(self.frame_inputs, text=label_text, font=("Arial", 10, "bold"))
            lbl.grid(row=i, column=0, sticky="w", pady=5)
            
            entry = ttk.Entry(self, width=12, justify='center')
            entry.insert(0, val)
            entry.grid(row=i, column=1, in_=self.frame_inputs, pady=5, padx=10)
            self.campos[label_text] = entry

        # Label para mostrar os coeficientes calculados (Invertido para row=7)
        self.lbl_coefs = ttk.Label(self.frame_inputs, text="a0 = 0 | a1 = 0 | a2 = 0", font=("Arial", 10, "italic"), foreground="#555")
        self.lbl_coefs.grid(row=7, column=0, columnspan=2, pady=(15, 5))

        # Botão de Execução (Invertido para row=8)
        self.btn_simular = ttk.Button(self.frame_inputs, text="Simular Parte A", command=self.simular_parte_a)
        self.btn_simular.grid(row=8, column=0, columnspan=2, pady=15, sticky="ew")

        # --- PAINEL DIREITO SUPERIOR: GRÁFICO ---
        self.frame_plot = ttk.Frame(self)
        self.frame_plot.grid(row=0, column=1, sticky="nsew", padx=10, pady=5)

        self.fig, self.ax = plt.subplots(figsize=(6, 3.2), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame_plot)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # --- PAINEL DIREITO INFERIOR: TABELA (EXCEL STYLE) ---
        self.frame_table = ttk.LabelFrame(self, text="Tabela de dados", padding=5)
        self.frame_table.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)

        # Configuração das colunas equivalentes ao Excel
        colunas = ("k", "t", "vp", "sp", "erro", "mk", "vm")
        self.tree = ttk.Treeview(self.frame_table, columns=colunas, show="headings")
        
        # Cabeçalhos
        self.tree.heading("k", text="Amostra (k)")
        self.tree.heading("t", text="Tempo (t)")
        self.tree.heading("vp", text="Var. Processo c(k)")
        self.tree.heading("sp", text="Setpoint (SP)")
        self.tree.heading("erro", text="Erro e(k)")
        self.tree.heading("mk", text="Saída m(k)")
        self.tree.heading("vm", text="Var. Manipulada (VM)")

        # Alinhamento e dimensionamento
        for col in colunas:
            self.tree.column(col, anchor="center", width=110)

        # Barra de rolagem vertical para navegar pelas amostras
        scrollbar = ttk.Scrollbar(self.frame_table, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Executa a simulação inicial para popular os dados e o gráfico
        self.simular_parte_a()

    def simular_parte_a(self):
        try:
            # Limpa as linhas antigas da tabela antes de recalcular
            for linha in self.tree.get_children():
                self.tree.delete(linha)

            # Captura de variáveis
            kp = float(self.campos["Kp"].get())
            ti = float(self.campos["Ti (s)"].get())
            td = float(self.campos["Td (s)"].get())
            fs = float(self.campos["fs (Hz)"].get())
            sp = float(self.campos["Setpoint"].get())
            vp_inicial = float(self.campos["VP inicial"].get())
            max_amostras = int(self.campos["Amostras máx."].get())

            ts = 1 / fs
            
            # Cálculo dos Coeficientes
            a0 = kp * (1 + (ts / ti) + (td / ts))
            a1 = -kp * (1 + (2 * td / ts))
            a2 = kp * (td / ts)

            # Imprime equação
            sinal_a1 = "+" if a1 >= 0 else "-"
            sinal_a2 = "+" if a2 >= 0 else "-"
            self.lbl_coefs.config(text=f"m(k) = {a0:.3f}e(k) {sinal_a1} {abs(a1):.3f}e(k-1) {sinal_a2} {abs(a2):.3f}e(k-2) + m(k-1)")
            
            # Inicialização das estruturas de dados
            amostras = list(range(-2, max_amostras + 1))
            vm_historico = [0.0, 0.0]
            sp_historico = [0.0, 0.0]
            
            # Insere as condições iniciais nulas na tabela (k = -2 e k = -1)
            self.tree.insert("", tk.END, values=(-2, f"{-2*ts:.2f}", f"{vp_inicial:.2f}", f"{vp_inicial:.2f}", "0.00", "0.00", "0.00"))
            self.tree.insert("", tk.END, values=(-1, f"{-1*ts:.2f}", f"{vp_inicial:.2f}", f"{vp_inicial:.2f}", "0.00", "0.00", "0.00"))
            
            e_menos2 = 0.0
            e_menos1 = 0.0
            m_anterior = 0.0
            
            # Loop de cálculo
            for k in range(0, max_amostras + 1):
                e_k = sp - vp_inicial
                
                delta_m = (a0 * e_k) + (a1 * e_menos1) + (a2 * e_menos2)
                m_k = m_anterior + delta_m
                
                vm_k = max(0.0, min(100.0, m_k))
                vm_historico.append(vm_k)
                sp_historico.append(sp)
                
                # Insere a linha calculada na tabela estilo Excel
                t_real = k * ts
                self.tree.insert("", tk.END, values=(
                    k, 
                    f"{t_real:.2f}", 
                    f"{vp_inicial:.2f}", 
                    f"{sp:.2f}", 
                    f"{e_k:.2f}", 
                    f"{m_k:.2f}", 
                    f"{vm_k:.2f}"
                ))
                
                # Atualização do histórico
                e_menos2 = e_menos1
                e_menos1 = e_k
                m_anterior = vm_k
                
            # Atualização dinâmica do gráfico
            self.ax.clear()
            self.ax.plot(amostras, vm_historico, 'o-', color='#ff7f0e', markersize=4, label='VM (Sinal Saturado %)')
            self.ax.plot(amostras, sp_historico, 'o-', color='#1f77b4', linewidth=1.5, label='SP (Setpoint)')
            self.ax.set_title("Resposta do controlador em malha aberta", fontsize=11, fontweight='bold')
            self.ax.set_xlabel("Amostras (k)")
            self.ax.set_ylabel("Variável Manipulada (VM %)")
            self.ax.set_ylim(-5, 105)
            self.ax.grid(True, linestyle='--', alpha=0.6)
            self.ax.legend()
            self.canvas.draw()
            
        except ValueError:
            messagebox.showerror("Erro", "Insira apenas números válidos.")
        except ZeroDivisionError:
            messagebox.showerror("Erro", "Ti e fs não podem ser zero.")


