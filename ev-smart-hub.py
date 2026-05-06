from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
import sqlite3

app = FastAPI(title="EV Smart Hub API")

# Configuração inicial do Banco de Dados SQLite
def init_db():
    conn = sqlite3.connect('ev_smart_hub.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS telemetria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            eletroposto_id TEXT,
            voltagem REAL,
            corrente REAL,
            origem_energia TEXT,
            timestamp DATETIME
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Modelo de dados para receber via IoT (ESP32)
class TelemetriaInput(BaseModel):
    eletroposto_id: str
    voltagem: float
    corrente: float
    geracao_solar_ativa: bool # Dado que viria da API SEMS da GoodWe

@app.get("/")
def home():
    return {"message": "EV Smart Hub - Sistema de Gestão Ativo"}

@app.post("/telemetria")
async def registrar_telemetria(dados: TelemetriaInput):
    origem = "SOLAR" if dados.geracao_solar_ativa else "REDE_CONVENCIONAL"
    
    try:
        conn = sqlite3.connect('ev_smart_hub.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO telemetria (eletroposto_id, voltagem, corrente, origem_energia, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (dados.eletroposto_id, dados.voltagem, dados.corrente, origem, datetime.now()))
        conn.commit()
        conn.close()
        
        return {
            "status": "sucesso",
            "origem_utilizada": origem,
            "mensagem": "Carga otimizada via Inteligência EV Smart Hub"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/dashboard/{eletroposto_id}")
def obter_resumo(eletroposto_id: str):
    conn = sqlite3.connect('ev_smart_hub.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM telemetria WHERE eletroposto_id = ? AND origem_energia = "SOLAR"', (eletroposto_id,))
    cargas_limpas = cursor.fetchone()[0]
    conn.close()
    
    return {
        "eletroposto": eletroposto_id,
        "total_sessoes_solar": cargas_limpas,
        "impacto": "Alinhado aos ODS 7 e 13"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)