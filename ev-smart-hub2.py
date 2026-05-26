import random
import math
import time
import threading
import sqlite3
from datetime import datetime, timezone
from typing import Optional


try:
    import uvicorn
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse
    HAS_API = True
except ImportError:
    HAS_API = False
    print("[AVISO] FastAPI/uvicorn não encontrado. Rodando apenas simulação no terminal.")
    print(" Instale com: pip install fastapi uvicorn\n")


FATOR_EMISSAO_GRID_KG_KWH = 0.0817   # MCTIC 2023: fator médio da rede brasileira
POTENCIA_MAX_SOLAR_KW     = 15.0      # Inversor GoodWe SDT15K simulado
POTENCIA_MAX_CHARGER_KW   = 7.4       # Carregador AC Wallbox típico (32A, 230V)
CAPACIDADE_BATERIA_KWH    = 60.0      # Bateria referência: BYD Dolphin
CICLO_SIMULACAO_SEG       = 2         # Intervalo de atualização dos sensores


# BANCO DE DADOS 
def init_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE telemetry (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            ts          TEXT    NOT NULL,
            solar_kw    REAL,
            grid_kw     REAL,
            load_kw     REAL,
            co2_avoided REAL,
            pct_solar   REAL
        )
    """)
    conn.execute("""
        CREATE TABLE charger_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            ts          TEXT    NOT NULL,
            charger_id  INTEGER,
            status      TEXT,
            soc_pct     REAL,
            power_kw    REAL,
            source      TEXT
        )
    """)
    conn.commit()
    return conn

DB = init_db()


# SIMULADOR DE INVERSOR SOLAR GOODWE (curva diária realista)
class GoodWeInverterSimulator:
    """
    Simula a telemetria de um inversor GoodWe SDT15K.
    Usa curva senoidal ajustada ao horário local + ruído gaussiano
    para representar variação de irradiância (nuvens, ângulo solar).
    Referência: IEC 61724-1 (monitoramento de sistemas FV).
    """

    def __init__(self):
        self.model      = "GoodWe SDT15K-ET"
        self.capacity   = POTENCIA_MAX_SOLAR_KW
        self.today_kwh  = 0.0
        self.total_kwh  = random.uniform(1200, 4500)  # histórico fictício

    def get_power_kw(self) -> float:
        """
        Geração solar baseada na hora do dia (curva gaussiana centrada ao meio-dia).
        Horário UTC-3 (São Paulo).
        """
        hour = datetime.now().hour + datetime.now().minute / 60.0
        # Pico ao meio-dia solar (~12h), zeros antes das 6h e depois das 18h
        peak = self.capacity * math.exp(-0.5 * ((hour - 12.0) / 3.0) ** 2)
        if hour < 6 or hour > 18:
            peak = 0.0
        # Ruído de 15% simulando passagem de nuvens
        noise = random.gauss(0, peak * 0.15)
        return max(0.0, round(peak + noise, 3))

    def get_telemetry(self) -> dict:
        power = self.get_power_kw()
        self.today_kwh  += power * (CICLO_SIMULACAO_SEG / 3600)
        self.total_kwh  += power * (CICLO_SIMULACAO_SEG / 3600)
        return {
            "model"       : self.model,
            "power_kw"    : power,
            "today_kwh"   : round(self.today_kwh, 3),
            "total_kwh"   : round(self.total_kwh, 3),
            "temperature" : round(random.uniform(28, 55), 1),   
            "efficiency"  : round(random.uniform(96.5, 98.5), 2) 
        }


# SIMULADOR DE ELETROPOSTOS
class EVCharger:
    """
    Simula um ponto de carregamento AC (Wallbox 7,4 kW).
    Estados: IDLE → CONNECTED → CHARGING → FULL
    """
    ESTADOS = ["IDLE", "CONNECTED", "CHARGING", "FULL"]

    def __init__(self, charger_id: int):
        self.id      = charger_id
        self.status  = "IDLE"
        self.soc     = 0.0    # Estado de Carga (%)
        self.power   = 0.0    # Potência sendo entregue (kW)
        self.source  = "NONE" # SOLAR | GRID | MIXED | NONE
        self._timer  = 0

    def update(self, available_solar_kw: float) -> float:
        """Retorna a potência consumida neste ciclo."""
        self._timer += 1

        # simula chegada de veículos
        if self.status == "IDLE" and random.random() < 0.03:
            self.status = "CONNECTED"
            self.soc    = random.uniform(5, 40)
            self._timer = 0

        elif self.status == "CONNECTED" and self._timer > 3:
            self.status = "CHARGING"

        elif self.status == "CHARGING":
            # Eficiência de carregamento: 92% (perdas no conversor)
            delta_soc = (self.power / CAPACIDADE_BATERIA_KWH) * (CICLO_SIMULACAO_SEG / 36) * 0.92
            self.soc  = min(100.0, self.soc + delta_soc)

            if self.soc >= 99.5:
                self.status = "FULL"
                self.power  = 0.0
                self.source = "NONE"

        elif self.status == "FULL" and random.random() < 0.05:
            self.status = "IDLE"
            self.soc    = 0.0

        # Determina potência e fonte de energia
        if self.status == "CHARGING":
            demanded = POTENCIA_MAX_CHARGER_KW
            if available_solar_kw >= demanded:
                self.power  = demanded
                self.source = "SOLAR"
                return demanded
            elif available_solar_kw > 0.5:
                self.power  = demanded
                self.source = "MIXED"
                return demanded
            else:
                self.power  = demanded * 0.7  # horário de pico
                self.source = "GRID"
                return self.power
        else:
            self.power  = 0.0
            self.source = "NONE"
            return 0.0

    def to_dict(self) -> dict:
        return {
            "id"      : self.id,
            "status"  : self.status,
            "soc_pct" : round(self.soc, 1),
            "power_kw": round(self.power, 2),
            "source"  : self.source
        }


# MOTOR DE DECISÃO ENERGÉTICA 
class EnergyDecisionEngine:
    """
    Hierarquia de prioridade baseada na ISO 50001:
      1. Usar geração solar disponível nos carregadores ativos
      2. Complementar com rede apenas se insuficiente
      3. Limitar consumo da rede em horário de pico (18h-21h)

    Calcula métricas de sustentabilidade em tempo real.
    """

    def __init__(self):
        self.inverter    = GoodWeInverterSimulator()
        self.chargers    = [EVCharger(i) for i in range(1, 4)]
        self.total_solar = 0.0
        self.total_grid  = 0.0
        self.co2_avoided = 0.0
        self.snapshot    = {}

    def _is_peak_hour(self) -> bool:
        h = datetime.now().hour
        return 18 <= h <= 21

    def tick(self) -> dict:
        inv = self.inverter.get_telemetry()
        solar_available = inv["power_kw"]

        # Distribui solar entre carregadores por ordem de prioridade
        remaining_solar = solar_available
        total_load      = 0.0
        charger_states  = []

        for c in self.chargers:
            consumed = c.update(remaining_solar)
            remaining_solar = max(0.0, remaining_solar - consumed)
            if c.source in ("SOLAR", "MIXED"):
                solar_fraction = min(consumed, solar_available)
            else:
                solar_fraction = 0.0
            total_load += consumed
            charger_states.append(c.to_dict())

        # Balanço energético
        grid_kw = max(0.0, total_load - solar_available)

        # Pico: limitar demanda da rede em 20%
        if self._is_peak_hour() and grid_kw > 0:
            grid_kw *= 0.8

        solar_used     = min(solar_available, total_load)
        pct_solar      = (solar_used / total_load * 100) if total_load > 0 else 0.0
        co2_cycle      = grid_kw * (CICLO_SIMULACAO_SEG / 3600) * FATOR_EMISSAO_GRID_KG_KWH
        co2_avoided_cyc= solar_used * (CICLO_SIMULACAO_SEG / 3600) * FATOR_EMISSAO_GRID_KG_KWH

        self.total_solar += solar_used  * (CICLO_SIMULACAO_SEG / 3600)
        self.total_grid  += grid_kw     * (CICLO_SIMULACAO_SEG / 3600)
        self.co2_avoided += co2_avoided_cyc

        ts = datetime.now(timezone.utc).isoformat()

        # Persiste no banco
        DB.execute(
            "INSERT INTO telemetry (ts, solar_kw, grid_kw, load_kw, co2_avoided, pct_solar) VALUES (?,?,?,?,?,?)",
            (ts, round(solar_available,3), round(grid_kw,3), round(total_load,3),
             round(self.co2_avoided,4), round(pct_solar,2))
        )
        for c_dict in charger_states:
            DB.execute(
                "INSERT INTO charger_log (ts, charger_id, status, soc_pct, power_kw, source) VALUES (?,?,?,?,?,?)",
                (ts, c_dict["id"], c_dict["status"], c_dict["soc_pct"],
                 c_dict["power_kw"], c_dict["source"])
            )
        DB.commit()

        self.snapshot = {
            "timestamp"       : ts,
            "inversor_goodwe" : inv,
            "eletropostos"    : charger_states,
            "balanco"         : {
                "solar_kw"    : round(solar_available, 3),
                "grid_kw"     : round(grid_kw, 3),
                "total_load_kw": round(total_load, 3),
                "pct_solar"   : round(pct_solar, 2),
                "horario_pico": self._is_peak_hour()
            },
            "sustentabilidade": {
                "co2_evitado_kg"  : round(self.co2_avoided, 4),
                "energia_solar_kwh": round(self.total_solar, 4),
                "energia_rede_kwh" : round(self.total_grid, 4),
            }
        }
        return self.snapshot


# ENGINE GLOBAL
engine = EnergyDecisionEngine()

def simulation_loop():
    """Loop de simulação em background."""
    while True:
        data = engine.tick()
        # Imprime resumo no terminal
        b = data["balanco"]
        s = data["sustentabilidade"]
        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] "
            f"Solar: {b['solar_kw']:5.2f} kW | "
            f"Rede: {b['grid_kw']:5.2f} kW | "
            f"Carga: {b['total_load_kw']:5.2f} kW | "
            f"%Solar: {b['pct_solar']:5.1f}% | "
            f"CO₂ evitado: {s['co2_evitado_kg']:.4f} kg"
        )
        time.sleep(CICLO_SIMULACAO_SEG)


# API REST 
if HAS_API:
    app = FastAPI(
        title="EV Smart Hub API",
        description=(
            "Plataforma Inteligente de Gestão de Eletropostos com Energia Renovável\n\n"
            "**Sprint 2 — Prova de Conceito Funcional**\n"
            "FIAP × GoodWe · EV Challenge 2026 · Turma 1CCPX"
        ),
        version="2.0.0"
    )

    @app.get("/", response_class=HTMLResponse, tags=["Root"])
    def root():
        return """
        <html><head><title>EV Smart Hub</title></head>
        <body style="font-family:monospace;background:#0d1117;color:#39d353;padding:2rem">
        <h1> EV Smart Hub — Sprint 2</h1>
        <p>API em operação. Acesse <a href="/docs" style="color:#58a6ff">/docs</a> para a documentação interativa.</p>
        <p>Endpoints principais:</p>
        <ul>
          <li><a href="/status" style="color:#58a6ff">/status</a> — snapshot em tempo real</li>
          <li><a href="/telemetry/history" style="color:#58a6ff">/telemetry/history</a> — histórico de telemetria</li>
          <li><a href="/chargers" style="color:#58a6ff">/chargers</a> — estado dos eletropostos</li>
          <li><a href="/sustainability" style="color:#58a6ff">/sustainability</a> — métricas de sustentabilidade</li>
        </ul>
        </body></html>
        """

    @app.get("/status", tags=["Monitoramento"],
             summary="Snapshot em tempo real do sistema")
    def get_status():
        """Retorna o estado atual do inversor, eletropostos e balanço energético."""
        return engine.snapshot if engine.snapshot else {"status": "inicializando"}

    @app.get("/chargers", tags=["Eletropostos"],
             summary="Estado de todos os eletropostos")
    def get_chargers():
        return {"eletropostos": [c.to_dict() for c in engine.chargers]}

    @app.get("/chargers/{charger_id}", tags=["Eletropostos"],
             summary="Estado de um eletroposto específico")
    def get_charger(charger_id: int):
        for c in engine.chargers:
            if c.id == charger_id:
                return c.to_dict()
        return {"error": "Eletroposto não encontrado"}, 404

    @app.get("/sustainability", tags=["Sustentabilidade"],
             summary="Métricas de CO₂ evitado e energia renovável")
    def get_sustainability():
        s = engine.snapshot.get("sustentabilidade", {})
        total = s.get("energia_solar_kwh", 0) + s.get("energia_rede_kwh", 0)
        return {
            **s,
            "arvores_equivalentes": round(s.get("co2_evitado_kg", 0) / 21.77, 4),
            "pct_renovavel_total"  : round(
                s.get("energia_solar_kwh", 0) / total * 100 if total > 0 else 0, 2
            )
        }

    @app.get("/telemetry/history", tags=["Telemetria"],
             summary="Últimos N registros de telemetria")
    def get_history(limit: int = 20):
        rows = DB.execute(
            "SELECT * FROM telemetry ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return {"count": len(rows), "data": [dict(r) for r in rows]}

    @app.get("/charger_log/history", tags=["Telemetria"],
             summary="Histórico de eventos dos eletropostos")
    def get_charger_log(limit: int = 30):
        rows = DB.execute(
            "SELECT * FROM charger_log ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return {"count": len(rows), "data": [dict(r) for r in rows]}


# ENTRY POINT
if __name__ == "__main__":
    print("=" * 70)
    print("    EV Smart Hub — Sprint 2: Prova de Conceito Funcional")
    print("  FIAP × GoodWe · EV Challenge 2026 · Turma 1CCPX")
    print("=" * 70)
    print(f"  Inversor simulado : GoodWe SDT15K ({POTENCIA_MAX_SOLAR_KW} kW)")
    print(f"  Eletropostos      : 3 × Wallbox AC ({POTENCIA_MAX_CHARGER_KW} kW cada)")
    print(f"  Ciclo de dados    : {CICLO_SIMULACAO_SEG}s")
    print(f"  Fator CO₂ grid BR : {FATOR_EMISSAO_GRID_KG_KWH} kg/kWh (MCTIC 2023)")
    print("=" * 70)

    # Inicia simulação em thread separada
    t = threading.Thread(target=simulation_loop, daemon=True)
    t.start()

    if HAS_API:
        print("\n  API disponível em: http://localhost:8000")
        print("  Documentação    : http://localhost:8000/docs\n")
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")
    else:
        print("\n  [Modo terminal] Simulação ativa. Pressione Ctrl+C para encerrar.\n")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nSimulação encerrada.")
