# ⚡ EV Smart Hub
### Plataforma Inteligente de Gestão de Eletropostos com Energia Renovável

> **EV Challenge 2026 · FIAP × GoodWe · Sprint 1 — Apresentação do Projeto Sustentável**

---

## 🚀 Sobre o Projeto

O **EV Smart Hub** é uma plataforma de gestão inteligente de eletropostos que integra dados de inversores solares GoodWe, sensores IoT e algoritmos de Machine Learning para otimizar o carregamento de veículos elétricos, priorizar energia fotovoltaica e reduzir a pegada de carbono da mobilidade elétrica urbana.

---

## 👥 Equipe

| Nome | RM |
|------|----|
| Brenno F. G. dos Santos | 570525 |
| Eduardo Moreira Silva | 569923 |
| Enzo Stahal Freitas | 569001 |
| Matheus Bruno de Lima | 572944 |

> **Turma:** 1CCPX · **Curso:** Ciências da Computação · **FIAP · 2026**

---

## 🔍 Problema & Justificativa

### O cenário atual
A rápida adoção de veículos elétricos no Brasil expõe uma lacuna crítica: **os eletropostos existentes carecem de gestão inteligente**. Isso resulta em desperdício de energia solar gerada, ausência de monitoramento em tempo real e emissões desnecessárias de CO₂ por depender da rede convencional em horários de pico.

---

## 💡 Proposta de Solução

O **EV Smart Hub** atua em quatro frentes principais:
1. **Integração GoodWe:** Conexão via API SEMS para priorização de energia solar fotovoltaica.
2. **IA Preditiva:** Uso de modelos de Machine Learning para prever demanda de carga e geração solar.
3. **Dashboard:** Gestão em tempo real com indicadores de sustentabilidade e eficiência energética.
---

## 🛠️ Tecnologias Utilizadas

### Backend & Core (Sprint 1)
- **Python 3.12**: Linguagem robusta para processamento de dados e IA.
- **FastAPI**: Framework moderno de alta performance para a construção da API e documentação automática.
- **SQLite**: Banco de dados para armazenamento de séries temporais e logs de energia.
- **Uvicorn**: Servidor de aplicação de alta velocidade.

---

## 🌱 Sustentabilidade & Energias Renováveis

Nossa solução é fundamentada na **Hierarquia da Eficiência Energética (ISO 50001)**:
- **Nível 1:** Eliminação do desperdício através do carregamento inteligente.
- **Nível 2:** Substituição da fonte priorizando a energia solar gerada pelos inversores GoodWe.
- **Nível 3:** Otimização constante via algoritmos preditivos e gestão de picos de consumo.

---

## 🏗️ Arquitetura da Solução

O fluxo de dados inicia na telemetria de sensores IoT e inversores GoodWe, sendo processado pelo **FastAPI**, que armazena as métricas no **SQLite** e disponibiliza as informações em tempo real para o Dashboard e para o motor de IA.

---

## 🗓️ Roadmap

| Sprint | Período | Entregas |
|--------|---------|---------|
| **Sprint 1** ✅ | Sem. 1-2 | Proposta, pitch e core do Backend funcional (FastAPI + SQLite) |
| **Sprint 2** | Sem. 3-4 | Protótipo IoT (Telemetria com ESP32 + integração inicial GoodWe) |
| **Sprint 3** | Sem. 5-6 | Evolução do Backend + Implementação do Modelo de IA (Random Forest) |
| **Sprint 4** | Sem. 7-8 | Desenvolvimento do Dashboard React + App Mobile + MVP Final Integrado |

---

## ▶️ Como Executar

Para testar a infraestrutura de backend desenvolvida nesta Sprint:

1. **Clone o repositório:**
```bash
git clone [https://github.com/BrennoGomes1/ev-smart-hub.git](https://github.com/BrennoGomes1/ev-smart-hub.git)
cd ev-smart-hub