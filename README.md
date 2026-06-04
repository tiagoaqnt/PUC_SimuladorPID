# Simulador PID digital

Interface gráfica modular para simulação e otimização de controle PID digital em processos de primeira ordem com tempo morto.

## Como executar

1. Instale o Python (marque a opção "Add Python to PATH" na instalação).
2. Deixe todos os arquivos (main.py, controlador_tab.py, simulador_tab.py, tab_otimizador.py, requirements.txt) na mesma pasta.
3. Abra o terminal (CMD) dentro dessa pasta.
4. Execute os comandos abaixo de acordo com seu sistema:

Windows:
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Mac / Linux:
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

## Como testar

* Aba 1 (Controlador): Simula a ação do PID em malha aberta (rampa de saturacao).
* Aba 2 (Simulador): Simula o processo em malha aberta (calcula o ganho e o Ts ideal por Astrom).
* Aba 3 (Otimizador): Fecha a malha. O botão 2D mostra a resposta temporal; o botao 3D gera a superfície de oitimização (melhor resposta para cada combinação de Kp e Ti).