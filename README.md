# Simulador PID digital

Interface gráfica modular para simulação e otimização de controle PID digital em processos de primeira ordem com tempo morto.

## Como executar direto (sem precisar de Python)

Se você gerou ou baixou o executável do projeto, basta:
1. Ir até a pasta `dist/`.
2. Dar dois cliques no arquivo `main.exe`.

## Como rodar via código (ambiente de desenvolvimento)

1. **Pré-requisito:** Instale o Python (marque a opção "Add Python to PATH" na instalação).
2. **Terminal:** Abra o prompt de comando (CMD ou PowerShell) dentro dessa pasta.
3. **Comandos:** Execute as linhas abaixo de acordo com seu sistema:

### Windows:
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py

### Mac / Linux:
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 main.py

---

## 🛠️ Como gerar um novo .exe

Caso faça alterações no código e queira compilar um novo executável independente para Windows, use o PyInstaller:

```powershell
.\.venv\Scripts\python.exe -m PyInstaller --noconsole --onefile main.py