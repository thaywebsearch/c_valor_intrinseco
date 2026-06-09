# Release v1.0.0

## Calculadora de Valor Intrínseco

Primeira versão estável da ferramenta de valuation com 9 modelos de precificação.

---

## Novidades

### 9 Modelos de Valuation

| Modelo | Descrição |
|--------|-----------|
| Gordon 1E | Dividendos com crescimento constante |
| Gordon 2E | Dois estágios de crescimento |
| P/B×ROE | Receita residual para bancos |
| H-Model | Declínio linear do crescimento |
| DCF | Fluxo de caixa descontado (2 estágios) |
| Graham | Número de Graham (value investing) |
| OE | Owner Earnings (metodologia Buffett) |
| CAPM/WACC | Custo de capital |
| Relativa | Múltiplos setoriais |

### Busca por Ticker

```bash
python calculadora_gordon.py --ticker AAPL
python calculadora_gordon.py --ticker PETR4.SA
```

### Interface Web

```bash
streamlit run streamlit_app.py
```

### Análise BAC

```bash
python calculadora_gordon.py --bac
```

---

## Instalação

```bash
git clone https://github.com/SEU_USERNAME/c_valor_intrinseco.git
cd c_valor_intrinseco
pip install -r requirements.txt
```

---

## Comandos CLI

```bash
--ticker TICKER          # Busca automática por ticker
--bac                    # Análise completa BAC
--quick D0 g% r%         # Gordon 1 estágio
--two-stage D0 g1% g2% n r%  # Gordon 2 estágios
--h-model D0 g1% g2% n r%    # H-Model
--dcf FCF0 g1% g2% n WACC% divida acoes  # DCF
--graham EPS BVPS        # Graham Number
--oe lucro DA capex r%   # Owner Earnings
--wacc RF% beta RM% equity divida Rd% T%  # CAPM/WACC
--relativa preco nome fund mult [...]      # Avaliação Relativa
--pbv BVPS ROE% r%       # P/B × ROE
```

---

## Roadmap

- [ ] Média ponderada por qualidade
- [ ] Monte Carlo
- [ ] Interface mobile
- [ ] Exportar PDF
- [ ] Dados tempo real
- [ ] Comparação entre empresas

---

## Licença

MIT License
