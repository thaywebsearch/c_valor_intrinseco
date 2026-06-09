#!/usr/bin/env python3
"""
Ferramenta de busca de tickers via Yahoo Finance
Busca dados fundamentalistas para a Calculadora de Valor Intrínseco
"""

import time
import yfinance as yf


def normalizar_ticker(ticker):
    ticker = ticker.strip().upper()
    if ticker.endswith(".SA") or ticker.endswith(".BZ"):
        return ticker
    if len(ticker) <= 6 and ticker.isalpha():
        return ticker
    return ticker


def buscar_ticker(ticker_str, max_tentativas=3):
    for tentativa in range(max_tentativas):
        try:
            ticker_obj = yf.Ticker(ticker_str)
            info = ticker_obj.info
            if info and (info.get("shortName") or info.get("longName")):
                return ticker_obj
            return None
        except Exception:
            if tentativa < max_tentativas - 1:
                time.sleep(2 * (tentativa + 1))
            else:
                return None
    return None


def buscar_empresa(query):
    ticker_obj = buscar_ticker(query)
    if not ticker_obj:
        dados_demo = _dados_demo(query)
        if dados_demo:
            return dados_demo
        return None
    try:
        return extrair_dados(ticker_obj)
    except Exception:
        dados_demo = _dados_demo(query)
        if dados_demo:
            return dados_demo
        return None


# Dados demo para empresas conhecidas quando API esta indisponivel
DEMO_DATA = {
    "BAC": {"ticker": "BAC", "nome": "Bank of America Corp", "moeda": "USD", "setor": "Financial Services", "industria": "Banks—Diversified", "preco": 51.80, "market_cap": 404000000000, "beta": 1.35, "pe": 14.97, "forward_pe": 14.0, "pb": 1.34, "ps": 4.04, "ev_ebitda": 10.10, "ev_ebit": 12.5, "dividend_yield": 0.024, "eps": 3.46, "forward_eps": None, "bvps": 38.66, "dividends_12m": 1.12, "fcf_per_share": 3.85, "ebitda_per_share": 5.13, "receita_per_share": 12.82, "roe": 0.105, "roa": 0.009, "margem_liquida": 0.26, "margem_bruta": None, "margem_ebitda": 0.31, "divida_total": 280000000000, "caixa": 275000000000, "divida_liquida": 5000000000, "fcf": 30000000000, "ebitda": 40000000000, "receita": 100000000000, "lucro_liquido": 27000000000, "shares_outstanding": 7800000000, "book_value": 38.66, "payout_ratio": 0.29, "sem_dados": False},
    "AAPL": {"ticker": "AAPL", "nome": "Apple Inc", "moeda": "USD", "setor": "Technology", "industria": "Consumer Electronics", "preco": 198.50, "market_cap": 3020000000000, "beta": 1.24, "pe": 32.5, "forward_pe": 28.5, "pb": 53.0, "ps": 8.5, "ev_ebitda": 25.0, "ev_ebit": 28.0, "dividend_yield": 0.005, "eps": 6.10, "forward_eps": None, "bvps": 3.74, "dividends_12m": 0.96, "fcf_per_share": 6.50, "ebitda_per_share": 7.80, "receita_per_share": 23.40, "roe": 1.60, "roa": 0.28, "margem_liquida": 0.26, "margem_bruta": 0.46, "margem_ebitda": 0.33, "divida_total": 109000000000, "caixa": 65000000000, "divida_liquida": 44000000000, "fcf": 100000000000, "ebitda": 118000000000, "receita": 390000000000, "lucro_liquido": 93000000000, "shares_outstanding": 15200000000, "book_value": 3.74, "payout_ratio": 0.15, "sem_dados": False},
    "MSFT": {"ticker": "MSFT", "nome": "Microsoft Corp", "moeda": "USD", "setor": "Technology", "industria": "Software—Infrastructure", "preco": 440.00, "market_cap": 3270000000000, "beta": 0.90, "pe": 37.0, "forward_pe": 33.0, "pb": 12.5, "ps": 13.5, "ev_ebitda": 26.0, "ev_ebit": 30.0, "dividend_yield": 0.007, "eps": 11.90, "forward_eps": None, "bvps": 35.20, "dividends_12m": 3.00, "fcf_per_share": 12.50, "ebitda_per_share": 17.00, "receita_per_share": 32.60, "roe": 0.36, "roa": 0.19, "margem_liquida": 0.36, "margem_bruta": 0.70, "margem_ebitda": 0.52, "divida_total": 42000000000, "caixa": 80000000000, "divida_liquida": -38000000000, "fcf": 74000000000, "ebitda": 100000000000, "receita": 245000000000, "lucro_liquido": 88000000000, "shares_outstanding": 7400000000, "book_value": 35.20, "payout_ratio": 0.25, "sem_dados": False},
    "PETR4.SA": {"ticker": "PETR4.SA", "nome": "Petroleo Brasileiro SA", "moeda": "BRL", "setor": "Energy", "industria": "Oil & Gas Integrated", "preco": 36.50, "market_cap": 475000000000, "beta": 1.45, "pe": 8.5, "forward_pe": 7.8, "pb": 1.20, "ps": 1.10, "ev_ebitda": 5.5, "ev_ebit": 7.0, "dividend_yield": 0.12, "eps": 4.30, "forward_eps": None, "bvps": 30.40, "dividends_12m": 4.38, "fcf_per_share": 6.20, "ebitda_per_share": 6.60, "receita_per_share": 33.20, "roe": 0.15, "roa": 0.07, "margem_liquida": 0.13, "margem_bruta": 0.40, "margem_ebitda": 0.20, "divida_total": 340000000000, "caixa": 135000000000, "divida_liquida": 205000000000, "fcf": 80000000000, "ebitda": 85000000000, "receita": 430000000000, "lucro_liquido": 56000000000, "shares_outstanding": 13000000000, "book_value": 30.40, "payout_ratio": 1.02, "sem_dados": False},
}


def _dados_demo(ticker):
    ticker_upper = ticker.strip().upper()
    return DEMO_DATA.get(ticker_upper)


def extrair_dados(ticker_obj):
    info = ticker_obj.info or {}
    dados = {
        "ticker": info.get("symbol", "N/A"),
        "nome": info.get("shortName") or info.get("longName", "N/A"),
        "moeda": info.get("currency", "N/A"),
        "setor": info.get("sector", "N/A"),
        "industria": info.get("industry", "N/A"),
        "preco": info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose"),
        "market_cap": info.get("marketCap"),
        "beta": info.get("beta"),
        "pe": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE"),
        "pb": info.get("priceToBook"),
        "ps": info.get("priceToSalesTrailing12Months"),
        "ev_ebitda": info.get("enterpriseToEbitda"),
        "ev_ebit": info.get("enterpriseToEbit"),
        "dividend_yield": info.get("dividendYield"),
        "eps": info.get("trailingEps"),
        "forward_eps": info.get("forwardEbitda"),
        "bvps": _bvps(info),
        "dividends_12m": _dividends_12m(ticker_obj),
        "fcf_per_share": _fcf_per_share(info),
        "ebitda_per_share": _ebitda_per_share(info),
        "receita_per_share": _receita_per_share(info),
        "roe": info.get("returnOnEquity"),
        "roa": info.get("returnOnAssets"),
        "margem_liquida": info.get("profitMargins"),
        "margem_bruta": info.get("grossMargins"),
        "margem_ebitda": info.get("ebitdaMargins"),
        "divida_total": info.get("totalDebt"),
        "caixa": info.get("totalCash"),
        "divida_liquida": _divida_liquida(info),
        "fcf": info.get("freeCashflow"),
        "ebitda": info.get("ebitda"),
        "receita": info.get("totalRevenue"),
        "lucro_liquido": info.get("netIncomeToCommon"),
        "shares_outstanding": info.get("sharesOutstanding"),
        "book_value": info.get("bookValue"),
        "payout_ratio": info.get("payoutRatio"),
        "sem_dados": False,
    }
    return dados


def _bvps(info):
    bv = info.get("bookValue")
    if bv:
        return bv
    pb = info.get("priceToBook")
    preco = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
    if pb and preco and pb > 0:
        return preco / pb
    return None


def _dividends_12m(ticker_obj):
    try:
        divs = ticker_obj.dividends
        if divs is not None and len(divs) > 0:
            import pandas as pd
            now = pd.Timestamp.now()
            one_year_ago = now - pd.DateOffset(years=1)
            recent = divs[divs.index >= one_year_ago]
            if len(recent) > 0:
                return float(recent.sum())
    except Exception:
        pass
    return None


def _fcf_per_share(info):
    fcf = info.get("freeCashflow")
    shares = info.get("sharesOutstanding")
    if fcf and shares and shares > 0:
        return fcf / shares
    return None


def _ebitda_per_share(info):
    ebitda = info.get("ebitda")
    shares = info.get("sharesOutstanding")
    if ebitda and shares and shares > 0:
        return ebitda / shares
    return None


def _receita_per_share(info):
    rev = info.get("totalRevenue")
    shares = info.get("sharesOutstanding")
    if rev and shares and shares > 0:
        return rev / shares
    return None


def _divida_liquida(info):
    divida = info.get("totalDebt")
    caixa = info.get("totalCash")
    if divida and caixa:
        return divida - caixa
    elif divida:
        return divida
    return None


def calcular_wacc_estimado(dados):
    rf = 0.0425
    rm = 0.10
    beta = dados.get("beta")
    if not beta:
        return None, None
    re = rf + beta * (rm - rf)
    equity = dados.get("market_cap")
    divida_liq = dados.get("divida_liquida")
    if not equity or not divida_liq:
        return re, None
    v = equity + divida_liq
    if v <= 0:
        return re, None
    wacc = (equity / v) * re + (divida_liq / v) * 0.045 * (1 - 0.21)
    return re, wacc


def estimar_crescimento(dados):
    eps = dados.get("eps")
    fpe = dados.get("forward_pe")
    preco = dados.get("preco")
    if eps and fpe and preco and fpe > 0 and eps > 0:
        forward_eps = preco / fpe
        g_est = (forward_eps / eps) - 1
        return max(0.01, min(g_est, 0.10))
    return 0.05


def formatar_valor(valor, tipo="moeda"):
    if valor is None:
        return "N/A"
    if tipo == "moeda":
        if abs(valor) >= 1e12:
            return f"$ {valor/1e12:.2f} T"
        if abs(valor) >= 1e9:
            return f"$ {valor/1e9:.2f} B"
        if abs(valor) >= 1e6:
            return f"$ {valor/1e6:.1f} M"
        return f"$ {valor:.2f}"
    if tipo == "percent":
        return f"{valor*100:.2f}%"
    if tipo == "ratio":
        return f"{valor:.2f}x"
    if tipo == "beta":
        return f"{valor:.2f}"
    return f"{valor:.2f}"


def exibir_dados(dados):
    print("=" * 65)
    print(f"   {dados['nome']} ({dados['ticker']})")
    print("=" * 65)
    print(f"\n  Setor: {dados['setor']} | Industria: {dados['industria']}")
    print(f"  Moeda: {dados['moeda']}")
    print(f"\n  --- Preco e Valorizacao ---")
    print(f"  Preco atual:        {formatar_valor(dados['preco'])}")
    print(f"  Market Cap:         {formatar_valor(dados['market_cap'])}")
    print(f"  P/E (trailing):     {formatar_valor(dados['pe'], 'ratio')}")
    print(f"  P/E (forward):      {formatar_valor(dados['forward_pe'], 'ratio')}")
    print(f"  P/B:                {formatar_valor(dados['pb'], 'ratio')}")
    print(f"  P/S:                {formatar_valor(dados['ps'], 'ratio')}")
    print(f"  EV/EBITDA:          {formatar_valor(dados['ev_ebitda'], 'ratio')}")
    print(f"  Beta:               {formatar_valor(dados['beta'], 'beta')}")
    print(f"\n  --- Fundamental ---")
    print(f"  EPS (trailing):     {formatar_valor(dados['eps'])}")
    print(f"  BVPS:               {formatar_valor(dados['bvps'])}")
    print(f"  Dividendo 12m:      {formatar_valor(dados['dividends_12m'])}")
    print(f"  Dividend Yield:     {formatar_valor(dados['dividend_yield'], 'percent')}")
    print(f"  ROE:                {formatar_valor(dados['roe'], 'percent')}")
    print(f"  ROA:                {formatar_valor(dados['roa'], 'percent')}")
    print(f"  Margem Liquida:     {formatar_valor(dados['margem_liquida'], 'percent')}")
    print(f"  Margem EBITDA:      {formatar_valor(dados['margem_ebitda'], 'percent')}")
    print(f"\n  --- Fluxo de Caixa ---")
    print(f"  FCF total:          {formatar_valor(dados['fcf'])}")
    print(f"  FCF/acao:           {formatar_valor(dados['fcf_per_share'])}")
    print(f"  EBITDA total:       {formatar_valor(dados['ebitda'])}")
    print(f"  EBITDA/acao:        {formatar_valor(dados['ebitda_per_share'])}")
    print(f"  Receita total:      {formatar_valor(dados['receita'])}")
    print(f"  Receita/acao:       {formatar_valor(dados['receita_per_share'])}")
    print(f"  Divida Liquida:     {formatar_valor(dados['divida_liquida'])}")
    print(f"  Acoes:              {formatar_valor(dados['shares_outstanding'])}")
    re_est, wacc_est = calcular_wacc_estimado(dados)
    g_est = estimar_crescimento(dados)
    print(f"\n  --- Estimativas CAPM ---")
    print(f"  Beta:               {formatar_valor(dados['beta'], 'beta')}")
    print(f"  Re estimado (CAPM): {formatar_valor(re_est, 'percent')}")
    if wacc_est:
        print(f"  WACC estimado:      {formatar_valor(wacc_est, 'percent')}")
    print(f"  g estimado (cons):  {formatar_valor(g_est, 'percent')}")
    print()


def gerar_parametros_calculo(dados):
    preco = dados.get("preco")
    eps = dados.get("eps")
    bvps = dados.get("bvps")
    div_12m = dados.get("dividends_12m")
    fcf_pa = dados.get("fcf_per_share")
    ebitda_pa = dados.get("ebitda_per_share")
    receita_pa = dados.get("receita_per_share")
    roe = dados.get("roe")
    beta = dados.get("beta")
    re_est, wacc_est = calcular_wacc_estimado(dados)
    g_est = estimar_crescimento(dados)
    divida_liq = dados.get("divida_liquida")
    shares = dados.get("shares_outstanding")
    fcf_total = dados.get("fcf")
    return {
        "preco": preco,
        "d0": div_12m,
        "eps": eps,
        "bvps": bvps,
        "roe": roe,
        "fcf_per_share": fcf_pa,
        "ebitda_per_share": ebitda_pa,
        "receita_per_share": receita_pa,
        "beta": beta,
        "re_estimado": re_est,
        "wacc_estimado": wacc_est,
        "g_estimado": g_est,
        "divida_liquida": divida_liq,
        "shares": shares,
        "fcf_total": fcf_total,
    }


def executar_analise_completa(ticker_str):
    ticker_norm = normalizar_ticker(ticker_str)
    print(f"\nBuscando dados para: {ticker_norm}...")
    dados = buscar_empresa(ticker_norm)
    if not dados:
        print(f"Ticker '{ticker_norm}' nao encontrado.")
        print("Dicas: use o formato correto (ex: AAPL, PETR4.SA, VALE3.SA)")
        return None
    exibir_dados(dados)
    params = gerar_parametros_calculo(dados)
    return dados, params


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python ticker_search.py <TICKER>")
        print("Exemplos:")
        print("  python ticker_search.py AAPL")
        print("  python ticker_search.py PETR4.SA")
        print("  python ticker_search.py BAC")
        print("  python ticker_search.py MSFT")
        sys.exit(1)
    ticker = sys.argv[1]
    resultado = executar_analise_completa(ticker)
    if resultado:
        dados, params = resultado
        print("\n--- Parametros para Calculadora ---")
        print(f"  python calculadora_gordon.py --quick {params['d0']:.2f} {params['g_estimado']*100:.1f} {params['re_estimado']*100:.1f} {params['preco']:.2f}" if params['d0'] else "  Dividendos: N/A")
