# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [1.0.0] - 2026-06-07

### Adicionado

- **Gordon 1 Estágio** — `P = D₀ × (1+g) / (r-g)`
- **Gordon 2 Estágios** — Dois estágios de crescimento com valor terminal
- **P/B × ROE** — Modelo de receita residual para bancos
- **H-Model (Fuller-Hsia)** — Declínio linear do crescimento
- **DCF (2 Estágios)** — Fluxo de caixa descontado com bridge EV→Equity→$/ação
- **Graham Number** — `GN = √(22.5 × EPS × BVPS)`
- **Owner Earnings (Buffett)** — `OE = NI + D&A - Capex`
- **CAPM / WACC** — Custo de capital e custo médio ponderado
- **Avaliação Relativa** — Múltiplos setoriais (P/E, P/B, EV/EBITDA, P/S, P/FCF)
- **Busca por Ticker** — Dados via Yahoo Finance com fallback demo
- **Análise BAC** — Case study completo com todos os modelos
- **Interface Web** — Streamlit com abas interativas e gráficos de calor
- **CLI** — 10 comandos para uso via terminal
- **Modo Interativo** — Menu com 11 opções
- Tabelas de sensibilidade (g × r)
- Gráficos de calor com Altair
- Recomendação automática (SUBVALORIZADA / SOBREVALORIZADA)
- Margem de segurança para cada modelo

### Estrutura

- `calculadora_gordon.py` — Core com 9 modelos de valuation
- `ticker_search.py` — Busca de dados via Yahoo Finance
- `streamlit_app.py` — Interface web interativa
- `requirements.txt` — Dependências Python
- `README.md` — Documentação completa
- `ABOUT.md` — Contexto e filosofia do projeto
- `CONTRIBUTING.md` — Guia de contribuição
- `LICENSE` — Licença MIT
- `.gitignore` — Arquivos ignorados

## [0.9.0] - 2026-06-06

### Adicionado

- Versão beta com modelos Gordon, P/B×ROE e H-Model
- Primeira versão do DCF
- Graham Number e Owner Earnings
- Análise BAC como case study

## [0.8.0] - 2026-06-05

### Adicionado

- Estrutura inicial do projeto
- Modelo Gordon 1 e 2 estágios
- Modo interativo e CLI básico

## [Unreleased]

### Planejado

- Média ponderada por qualidade dos inputs
- Simulação Monte Carlo
- Interface mobile
- Exportar relatórios em PDF
- Dados em tempo real via API
- Comparação entre empresas
- Histórico de valuation
