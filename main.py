import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sys


from tab_controlador import ControladorTab
from tab_simulador import SimuladorTab
from tab_otimizador import OtimizadorTab


class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('SIMULADOR DE CONTROLE DIGITAL')
        self.geometry("1050x600")
        
        # Tela principal
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # Configura o fechamento completo ao clicar no "X" da janela
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 1. Criação do notebook (gerenciador de abas)
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # 2. Instanciando e adicionando a aba do controlador (Parte A)
        self.tab_controlador = ControladorTab(self.notebook)
        self.notebook.add(self.tab_controlador, text=" Controlador (Parte A) ")

        # 2. Instanciando e adicionando a aba do simulador (Parte B)
        self.tab_simulador = SimuladorTab(self.notebook)
        self.notebook.add(self.tab_simulador, text=" Simulador (Parte B) ")

        # 3. Instanciando e adicionando a aba do otimizador (Parte C)
        self.tab_otimizador = OtimizadorTab(self.notebook)
        self.notebook.add(self.tab_otimizador, text=" Otimizador (Parte C) ")

    def on_closing(self):
        """Garante que o script Python pare totalmente ao fechar a janela"""
        plt.close('all')  # Fecha os gráficos do matplotlib em segundo plano
        self.destroy()    # Destrói a interface do Tkinter
        sys.exit()        # Mata o processo do script no terminal/IDLE








def main():
    app = Application()
    app.mainloop()


if __name__ == '__main__':
    main()
