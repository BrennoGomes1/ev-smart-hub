#  EV Smart Hub

> **Plataforma Inteligente de Gestão de Eletropostos com Energia Renovável**
> EV Challenge 2026 · FIAP × GoodWe · Sprint 2 — Prova de Conceito Funcional

---

### Equipe — Turma 1CCPX · Ciências da Computação · FIAP 2026

| Nome | RM |
| :--- | :--- |
| Brenno F. G. dos Santos | 570525 |
| Eduardo Moreira Silva | 569923 |
| Enzo Stahal Freitas | 569001 |
| Matheus Bruno de Lima | 572944 |

---

##  Índice

1. [Sobre o Projeto](#sobre-o-projeto)
2. [Sprint 2 — O que foi entregue](#sprint-2--o-que-foi-entregue)
3. [Arquitetura do Sistema](#arquitetura-do-sistema)
4. [Diagrama de Fluxo de Dados](#diagrama-de-fluxo-de-dados)
5. [Motor de Decisão Energética](#motor-de-decisão-energética)
6. [Justificativas Técnicas](#justificativas-técnicas)
7. [Sustentabilidade e Energias Renováveis](#sustentabilidade-e-energias-renováveis)
8. [Dados Simulados — Resultados](#dados-simulados--resultados)
9. [Como Executar](#como-executar)
10. [Endpoints da API](#endpoints-da-api)
---

## Sobre o Projeto

O **EV Smart Hub** é uma plataforma de gestão inteligente de eletropostos que integra dados de inversores solares GoodWe, sensores IoT e algoritmos de decisão energética para:

- **Priorizar energia fotovoltaica** no carregamento de veículos elétricos
- **Reduzir a pegada de carbono** da mobilidade elétrica urbana
- **Otimizar o uso da rede elétrica** em horários de pico
- **Gerar métricas de sustentabilidade** em tempo real

---

## Sprint 2 — O que foi entregue

Esta sprint implementa a **Prova de Conceito Funcional** do sistema, com simulação completa em Python e API REST operacional.

### Funcionalidades implementadas

| Componente | Descrição | Status |
|---|---|---|
| `GoodWeInverterSimulator` | Telemetria do inversor GoodWe SDT15K com curva diária realista | ✅ Funcional |
| `EVCharger` | 3 eletropostos com máquina de estados (IDLE → CHARGING → FULL) | ✅ Funcional |
| `EnergyDecisionEngine` | Motor de prioridade solar ISO 50001 + throttle de pico | ✅ Funcional |
| `SQLite` | Persistência de telemetria e logs de carregamento | ✅ Funcional |
| `FastAPI` | 6 endpoints REST com documentação automática (Swagger) | ✅ Funcional |
| Métricas CO₂ | Cálculo em tempo real de emissões evitadas (fator MCTIC 2023) | ✅ Funcional |

---

## Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                        EV SMART HUB v2                          │
├──────────────┬──────────────────┬───────────────────────────────┤
│  CAMADA DE   │   CAMADA DE      │      CAMADA DE                │
│  SENSORES    │   PROCESSAMENTO  │      EXPOSIÇÃO                │
│  (Simulada)  │   (Python Core)  │      (FastAPI)                │
├──────────────┼──────────────────┼───────────────────────────────┤
│              │                  │                               │
│  ┌─────────┐ │  ┌─────────────┐ │  GET /status                  │
│  │ Inversor│ │  │  Energy     │ │  GET /chargers                │
│  │ GoodWe  │►│  │  Decision   │►│  GET /chargers/{id}           │
│  │ SDT15K  │ │  │  Engine     │ │  GET /sustainability          │
│  └─────────┘ │  └──────┬──────┘ │  GET /telemetry/history       │
│              │         │        │  GET /charger_log/history     │
│  ┌─────────┐ │  ┌──────▼──────┐ │                               │
│  │Charger 1│◄│  │   SQLite    │ │  ┌──────────────────────────┐ │
│  │Charger 2│ │  │  Database   │ │  │  /docs  (Swagger UI)     │ │
│  │Charger 3│ │  │(em memória) │ │  │  Documentação interativa │ │
│  └─────────┘ │  └─────────────┘ │  └──────────────────────────┘ │
└──────────────┴──────────────────┴───────────────────────────────┘
```

### Componentes e responsabilidades

**`GoodWeInverterSimulator`**
Simula a telemetria de um inversor solar GoodWe SDT15K-ET (15 kW). A geração fotovoltaica é modelada por uma curva gaussiana centrada ao meio-dia solar, com ruído gaussiano de ±15% para representar variações de irradiância (nuvens, ângulo solar). Parâmetros físicos baseados na norma IEC 61724-1 (Monitoramento de Sistemas FV).

**`EVCharger`**
Máquina de estados finitos que simula um ponto de carregamento AC (Wallbox 7,4 kW / 32A / 230V). Ciclo de vida: `IDLE → CONNECTED → CHARGING → FULL → IDLE`. A eficiência de carregamento (92%) é baseada em valores típicos de conversores AC-DC.

**`EnergyDecisionEngine`**
Núcleo da solução. Aplica a hierarquia de eficiência energética (ISO 50001) para distribuir energia solar entre os eletropostos ativos, complementando com rede apenas quando necessário. Em horário de pico (18h–21h), reduz automaticamente a demanda da rede em 20%.

**`SQLite`**
Banco de dados leve usado para persistência de séries temporais de telemetria e logs de carregamento. Em ambiente de produção, substituído por PostgreSQL com TimescaleDB para eficiência em séries temporais.

**`FastAPI`**
Framework Python moderno com suporte a documentação automática via OpenAPI (Swagger). Escolhido pela alta performance assíncrona, tipagem nativa e facilidade de evolução para integração com a API SEMS da GoodWe.

---

## Diagrama de Fluxo de Dados

```
  ┌───────────────────────────────────────────────────────────┐
  │                   CICLO DE SIMULAÇÃO (2s)                  │
  └───────────────────────────────────────────────────────────┘
           │
           ▼
  ┌─────────────────┐       Curva gaussiana + ruído
  │  Inversor Solar │ ──────(hora local → potência kW)──────►  solar_kw
  │  GoodWe SDT15K  │
  └─────────────────┘
           │
           │  solar_kw disponível
           ▼
  ┌─────────────────────────────────────────────────────────┐
  │              MOTOR DE DECISÃO ENERGÉTICA                │
  │                                                         │
  │  Para cada eletroposto (prioridade por ordem):          │
  │    SE solar_disponível >= demanda_charger:              │
  │       fonte = "SOLAR"   ← zero emissão                 │
  │    SENÃO SE solar_disponível > 0.5 kW:                  │
  │       fonte = "MIXED"   ← emissão parcial              │
  │    SENÃO:                                               │
  │       fonte = "GRID"    ← potência reduzida 30%        │
  │          (em horário de pico: throttle adicional -20%)  │
  └─────────────────────────────────────────────────────────┘
           │
           ▼
  ┌──────────────────────────────┐   ┌──────────────────────┐
  │        SQLite DB             │   │   Métricas em tempo  │
  │  • tabela: telemetry         │   │   real:              │
  │  • tabela: charger_log       │   │   • CO₂ evitado (kg) │
  │  (timestamp, kW, fonte, SoC) │   │   • % energia solar  │
  └──────────────────────────────┘   │   • kWh totais       │
           │                         └──────────────────────┘
           ▼
  ┌──────────────────────────────┐
  │       FastAPI REST           │
  │   (porta 8000)               │
  │   • /status                  │
  │   • /chargers                │
  │   • /sustainability          │
  │   • /telemetry/history       │
  └──────────────────────────────┘
```

---

## Motor de Decisão Energética

O coração da Sprint 2 é o `EnergyDecisionEngine`, que implementa três níveis de decisão:

### Nível 1 — Prioridade Solar (Eliminação do desperdício)
Toda geração fotovoltaica disponível é alocada prioritariamente aos eletropostos em carregamento. A energia solar que não for consumida representa excedente que poderia ser injetado na rede (funcionalidade prevista nas Sprints 3–4).

### Nível 2 — Complementação pela Rede
Quando a geração solar é insuficiente para atender toda a demanda, a rede elétrica complementa. O sistema classifica a fonte como `MIXED` (solar + rede) ou `GRID` (apenas rede).

### Nível 3 — Gestão de Pico (18h–21h)
Em horário de pico, o sistema reduz automaticamente a potência de carregamento via rede em 20%, alinhado às tarifas horo-sazonais da ANEEL e ao conceito de *demand response*.

```python
# Pseudocódigo do motor de decisão
for charger in chargers:
    if solar_available >= charger.demand:
        charger.source = "SOLAR"       # ← zero emissão de CO₂
    elif solar_available > 0.5:
        charger.source = "MIXED"       # ← emissão reduzida
    else:
        charger.source = "GRID"
        if is_peak_hour():
            charger.power *= 0.80      # ← demand response
```

---

## Justificativas Técnicas

### Por que Python 3.12?
Python é a linguagem dominante em projetos de IoT, data science e automação energética. Sua biblioteca padrão permite simular um sistema completo sem dependências externas pesadas, facilitando a demonstração da prova de conceito.

### Por que FastAPI?
FastAPI oferece performance comparável a frameworks Node.js (benchmarks TechEmpower), suporte nativo a tipagem com Pydantic e geração automática de documentação OpenAPI — essencial para futura integração com a API SEMS da GoodWe e com dashboards React.

### Por que SQLite?
Para uma prova de conceito com séries temporais curtas, SQLite oferece zero configuração, armazenamento em memória (`:memory:`) e SQL padrão. Em produção (Sprint 4), migramos para PostgreSQL + TimescaleDB, otimizado para séries temporais de energia.

### Por que curva gaussiana para irradiância?
A geração solar segue aproximadamente uma distribuição gaussiana ao longo do dia, centrada no horário de maior irradiância (≈12h solar). O ruído gaussiano de ±15% representa variações reais causadas por nuvens e sombreamento — modelo usado em softwares como PVSyst e SAM (NREL).

### Por que fator de emissão 0,0817 kg CO₂/kWh?
Valor do Fator Médio de Emissão do Sistema Interligado Nacional (SIN) publicado pelo MCTIC em 2023. É o índice oficial usado no Brasil para inventários de emissões de GEE no setor elétrico.

---

## Sustentabilidade e Energias Renováveis

### Conexão com os conceitos do semestre

| Conceito | Aplicação no EV Smart Hub |
|---|---|
| **Energia Fotovoltaica** | Inversor GoodWe SDT15K como fonte primária. Curva de geração baseada em física solar (irradiância, ângulo de incidência). |
| **Eficiência Energética (ISO 50001)** | Hierarquia de 3 níveis: eliminar desperdício → substituir fonte → otimizar consumo. |
| **Gestão de Demanda (Demand Response)** | Throttle automático de 20% em horário de pico (18h–21h), alinhado às tarifas horo-sazonais ANEEL. |
| **Mobilidade Elétrica Sustentável** | Maximiza fração de carga renovável nos VEs, reduzindo emissões do ciclo de vida. |
| **Métricas de Carbono** | Cálculo contínuo de CO₂ evitado usando fator de emissão oficial (MCTIC 2023). |
| **IoT e Monitoramento** | Telemetria em tempo real dos eletropostos e inversor, base para decisões automatizadas. |

### Impacto projetado (escala real)

Considerando um hub com 3 eletropostos operando 8h/dia com 60% de aproveitamento solar:

- **Energia solar utilizada:** ≈ 21,6 kWh/dia
- **CO₂ evitado:** ≈ 1,76 kg/dia → **643 kg/ano por hub**
- **Equivalente em árvores:** ≈ 29 árvores/ano (absorção média 22 kg CO₂/árvore/ano)

---

## Dados Simulados — Resultados

Exemplo de saída do terminal após 30 segundos de execução:

```
[14:02:01] Solar:  8.43 kW | Rede:  0.00 kW | Carga:  7.40 kW | %Solar: 100.0% | CO₂ evitado: 0.0004 kg
[14:02:03] Solar:  9.11 kW | Rede:  0.00 kW | Carga: 14.80 kW | %Solar:  61.6% | CO₂ evitado: 0.0008 kg
[14:02:05] Solar:  7.82 kW | Rede:  6.98 kW | Carga: 14.80 kW | %Solar:  52.8% | CO₂ evitado: 0.0012 kg
[14:02:07] Solar:  0.00 kW | Rede:  0.00 kW | Carga:  0.00 kW | %Solar:   0.0% | CO₂ evitado: 0.0012 kg
```

Exemplo de resposta do endpoint `/sustainability`:

```json
{
  "co2_evitado_kg": 0.0312,
  "energia_solar_kwh": 0.2847,
  "energia_rede_kwh": 0.1203,
  "arvores_equivalentes": 0.0014,
  "pct_renovavel_total": 70.3
}
```

---

## Como Executar

### Pré-requisitos

- Python 3.10+ instalado
- pip disponível

### Passo a passo

```bash
# 1. Clone o repositório
git clone https://github.com/BrennoGomes1/ev-smart-hub.git
cd ev-smart-hub

# 2. Instale as dependências
pip install fastapi uvicorn

# 3. Execute o protótipo
python ev-smart-hub.py
```

### O que esperar

```
======================================================================
    EV Smart Hub — Sprint 2: Prova de Conceito Funcional
  FIAP × GoodWe · EV Challenge 2026 · Turma 1CCPX
======================================================================
  Inversor simulado : GoodWe SDT15K (15.0 kW)
  Eletropostos      : 3 × Wallbox AC (7.4 kW cada)
  Ciclo de dados    : 2s
  Fator CO₂ grid BR : 0.0817 kg/kWh (MCTIC 2023)
======================================================================

  API disponível em: http://localhost:8000
  Documentação    : http://localhost:8000/docs

[14:05:00] Solar:  6.21 kW | Rede: 1.19 kW | Carga: 7.40 kW | %Solar: 83.9% | CO₂ evitado: 0.0003 kg
```

Acesse `http://localhost:8000/docs` para explorar todos os endpoints via Swagger UI.

> **Sem FastAPI instalado?** O script ainda funciona no modo terminal, exibindo os dados de simulação a cada 2 segundos.

---

## Endpoints da API

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/` | Página inicial (HTML) |
| `GET` | `/status` | Snapshot completo em tempo real |
| `GET` | `/chargers` | Estado de todos os eletropostos |
| `GET` | `/chargers/{id}` | Estado de um eletroposto específico |
| `GET` | `/sustainability` | CO₂ evitado, kWh solar, % renovável |
| `GET` | `/telemetry/history` | Histórico de telemetria (param: `limit`) |
| `GET` | `/charger_log/history` | Histórico de eventos dos chargers |
| `GET` | `/docs` | Documentação Swagger UI |

---

## Licença

Projeto acadêmico desenvolvido para o **EV Challenge 2026 — FIAP × GoodWe**.
Uso educacional. Todos os direitos reservados aos integrantes da equipe.
