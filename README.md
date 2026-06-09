# Calculadora de Valor Intrínseco

Ferramenta completa de valuation com 9 modelos de precificação para análise de empresas listadas em bolsa.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Ativo-brightgreen)

---

## Funcionalidades

### Modelos de Valuation

| Modelo | Fórmula | Uso |
|--------|---------|-----|
| **Gordon 1 Estágio** | `P = D₀ × (1+g) / (r-g)` | Empresas com dividendos estáveis |
| **Gordon 2 Estágios** | `P = Σ Dₜ/(1+r)ᵗ + Terminal` | Empresas em transição de crescimento |
| **P/B × ROE** | `P = BVPS × (ROE-g) / (r-g)` | Bancos e empresas patrimoniais |
| **H-Model (Fuller-Hsia)** | `P = D₀(1+g₂)/(r-g₂) + D₀(n/2)(g₁-g₂)/(r-g₂)` | Declínio linear do crescimento |
| **DCF (2 Estágios)** | `EV = Σ FCFₜ/(1+WACC)ᵗ + Terminal` | Fluxo de caixa livre |
| **Graham Number** | `GN = √(22.5 × EPS × BVPS)` | Value investing (Graham) |
| **Owner Earnings** | `OE = NI + D&A - Capex` | Metodologia Warren Buffett |
| **CAPM / WACC** | `Re = Rf + β(Rm-Rf)` | Custo de capital |
| **Avaliação Relativa** | `Preço Alvo = Múltiplo Setorial × Fundamental` | Comparação com pares |

### Análise Integrada

- **Geração automática** de tabelas de sensibilidade (g × r)
- **Gráficos de calor** interativos com Altair/Streamlit
- **Múltiplos cenários** por modelo (base, conservador, otimista)
- **Conclusão consolidada** com média e recomendação

### Dados de Empresas (Yahoo Finance)

- Busca automática de dados por ticker (`AAPL`, `PETR4.SA`, `BAC`)
- Extração: preço, EPS, BVPS, dividendos, ROE, beta, FCF, EBITDA
- Estimativa automática de Re (CAPM), WACC e taxa de crescimento
- Fallback com dados demo para empresas conhecidas

---

## Instalação

```bash
# Clonar o repositório
git clone https://github.com/SEU_USERNAME/c_valor_intrinseco.git
cd c_valor_intrinseco

# Instalar dependências
pip install -r requirements.txt
```

---

## Uso

### Modo Interativo (menu)

```bash
python calculadora_gordon.py
```

```
Modelos disponíveis:
  1  - Gordon 1 estágio
  2  - Gordon 2 estágios
  3  - P/B x ROE (Residual Income)
  4  - Análise completa BAC
  5  - H-Model (Fuller-Hsia)
  6  - DCF (Fluxo de Caixa Descontado)
  7  - Graham Number
  8  - Owner Earnings (Buffett)
  9  - CAPM / WACC
  10 - Avaliação Relativa (Múltiplos)
  11 - Buscar empresa por ticker (Yahoo Finance)
  0  - Sair
```

### Interface Web (Streamlit)

```bash
streamlit run streamlit_app.py
```

Acesse: `http://localhost:8501`

### Busca por Ticker

```bash
# Análise completa a partir do ticker
python calculadora_gordon.py --ticker BAC
python calculadora_gordon.py --ticker AAPL
python calculadora_gordon.py --ticker PETR4.SA

# Apenas dados da empresa
python ticker_search.py MSFT
```

### Comandos CLI

```bash
# Gordon 1 Estágio
python calculadora_gordon.py --quick 1.12 7 10 51.80

# Gordon 2 Estágios
python calculadora_gordon.py --two-stage 1.12 8 4 5 10 51.80

# H-Model
python calculadora_gordon.py --h-model 1.12 8 4 5 10 51.80

# DCF (valores em bilhões)
python calculadora_gordon.py --dcf 30 6 3 5 10 5 7.8 51.80

# Graham Number
python calculadora_gordon.py --graham 3.46 38.66 51.80

# Owner Earnings
python calculadora_gordon.py --oe 3.46 0.50 0.30 10 3 51.80

# CAPM / WACC
python calculadora_gordon.py --wacc 4.25 1.35 10 340 280 4.5 21

# Avaliação Relativa
python calculadora_gordon.py --relativa 51.80 P/E 3.46 13.0 P/B 38.66 1.1 EV/EBITDA 5.13 11.0

# P/B x ROE
python calculadora_gordon.py --pbv 38.66 10.5 10 0 51.80

# Análise completa BAC
python calculadora_gordon.py --bac
```

---

## Estrutura do Projeto

```
c_valor_intrinseco/
├── calculadora_gordon.py    # Core: 9 modelos de valuation
├── ticker_search.py         # Busca de dados via Yahoo Finance
├── streamlit_app.py         # Interface web interativa
├── requirements.txt         # Dependências Python
├── LICENSE                  # Licença MIT
├── README.md                # Esta documentação
└── .gitignore               # Arquivos ignorados pelo Git
```

---

## Exemplo: Análise BAC

```bash
$ python calculadora_gordon.py --bac

Preco de mercado: $ 51.80
  Gordon 1 estagio (g=7%, r=10%):        $ 39.95  (-29.7%)
  Gordon 2 estagios (g1=8%, g2=4%, r=10%): $ 23.01  (-125.1%)
  P/B x ROE (ROE=10.5%, r=10%):          $ 40.59  (-27.6%)
  H-Model (g1=8%, g2=4%, n=5, r=10%):    $ 21.28  (-143.4%)
  DCF (g1=6%, g2=3%, WACC=10%):          $ 63.62  (+18.6%)
  Graham Number (EPS=3.46, BVPS=38.66):  $ 54.86  (+5.6%)
  Owner Earnings (OE=$3.66, g=3%, r=10%): $ 53.85  (+3.8%)
  Avaliação Relativa (média 5 múlt.):     $ 45.21  (-12.7%)

  >>> Média dos 8 modelos: $ 42.80  (-21.0%)
  >>> RECOMENDAÇÃO: SOBREVALORIZADA - AGUARDAR
```

---

## Dependências

| Pacote | Versão | Uso |
|--------|--------|-----|
| `streamlit` | ≥ 1.28 | Interface web |
| `pandas` | ≥ 2.0 | Manipulação de dados |
| `altair` | ≥ 5.0 | Gráficos interativos |
| `numpy` | ≥ 1.24 | Cálculos numéricos |
| `yfinance` | ≥ 0.2.30 | Dados Yahoo Finance |
| `matplotlib` | ≥ 3.7 | Gráficos (CLI) |

---

## Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-feature`)
3. Commit suas alterações (`git commit -m 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

Veja [CONTRIBUTING.md](CONTRIBUTING.md) para mais detalhes.

---

## Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

## Autor

**c_valor_intrínseco** - Ferramenta de Análise de Valor Intrínseco

Desenvolvido para auxiliar investidores na tomada de decisão fundamentada.
