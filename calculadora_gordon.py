#!/usr/bin/env python3
"""
Calculadora de Valor Intrínseco - Gordon, P/B x ROE, H-Model, DCF, Graham & OE
================================================================================
Modelos:
  A) Gordon 1 estagio:   P = D0 * (1+g) / (r-g)
  B) Gordon 2 estagios:  P = soma Dt descontados + terminal
  C) P/B x ROE:          P = BVPS * (ROE - g) / (r - g)
  D) H-Model (Fuller-Hsia): P = D0*(1+g2)/(r-g2) + D0*(n/2)*(g1-g2)/(r-g2)
  E) DCF (2 estagios):   EV = soma FCFt descontados + terminal
                         Valor acao = (EV - Divida Liquida) / Acoes
  F) Graham Number:      GN = sqrt(22.5 * EPS * BVPS)
   G) Owner Earnings:     OE = Lucro Liquido + D&A - Capex Manutencao
                         Valor = OE * (1+g) / (r-g)
   H) CAPM / WACC:        CAPM = RF + beta * (RM - RF)
                         WACC = (E/V) * Re + (D/V) * Rd * (1 - T)
   I) Avaliacao Relativa:  Preco Alvo = Multiplo Setorial * Fundamental
"""

import sys, csv, os
from datetime import datetime
import ticker_search

# ======================== NUCLEO DOS MODELOS ========================

def gordon_1estagio(d0, g, r):
    if r <= g:
        return None
    return d0 * (1 + g) / (r - g)


def gordon_2estagios(d0, g1, g2, n, r):
    if r <= g2:
        return None
    soma = 0.0
    d = d0
    for t in range(1, n + 1):
        d *= (1 + g1)
        soma += d / ((1 + r) ** t)
    terminal = d * (1 + g2) / (r - g2)
    terminal /= (1 + r) ** n
    return soma + terminal


def pbv_roe(bvps, roe, r, g=0):
    if r <= g:
        return None
    if g == 0:
        return bvps * (roe / r)
    return bvps * (roe - g) / (r - g)


def h_model(d0, g1, g2, n, r):
    if r <= g2:
        return None
    return d0 * (1 + g2) / (r - g2) + d0 * (n / 2) * (g1 - g2) / (r - g2)


def dcf_2estagios(fcf0, g1, g2, n, wacc):
    if wacc <= g2:
        return None
    pv_fcf = 0.0
    fcf = fcf0
    for t in range(1, n + 1):
        fcf *= (1 + g1)
        pv_fcf += fcf / ((1 + wacc) ** t)
    terminal = fcf * (1 + g2) / (wacc - g2)
    pv_terminal = terminal / ((1 + wacc) ** n)
    return pv_fcf + pv_terminal


def dcf_1estagio(fcf0, g, wacc):
    if wacc <= g:
        return None
    return fcf0 * (1 + g) / (wacc - g)


def graham_number(eps, bvps):
    if eps <= 0 or bvps <= 0:
        return None
    return (22.5 * eps * bvps) ** 0.5


def owner_earnings(lucro_liquido, da, capex_manutencao):
    return lucro_liquido + da - capex_manutencao


def oe_valuation(oe, r, g=0):
    if r <= g:
        return None
    if g == 0:
        return oe / r
    return oe * (1 + g) / (r - g)


def capm(rf, beta, rm):
    return rf + beta * (rm - rf)


def calcular_wacc(equity, divida, re, rd, t):
    v = equity + divida
    if v <= 0:
        return None
    return (equity / v) * re + (divida / v) * rd * (1 - t)


def multiplo_atual(preco, valor):
    if valor is None or valor == 0:
        return None
    return preco / valor


def preco_alvo_multiplo(multiplo_setorial, valor_fundamental):
    if multiplo_setorial is None or valor_fundamental is None:
        return None
    return multiplo_setorial * valor_fundamental


def upside_percent(alvo, preco):
    if alvo is None or preco is None or preco == 0:
        return None
    return (alvo - preco) / preco * 100


def taxa_retorno_implicita(d0, g, preco):
    if preco <= 0:
        return None
    return (d0 * (1 + g) / preco) + g


def margem_seguranca(vi, preco):
    if vi is None or preco is None or preco <= 0:
        return None
    return (vi - preco) / vi * 100


def payback_anos(d0, g, preco, max_anos=50):
    if preco <= 0:
        return None
    acum = 0.0
    d = d0
    for a in range(1, max_anos + 1):
        d *= (1 + g)
        acum += d
        if acum >= preco:
            return a
    return None


# ======================== FORMATACAO ========================

def fmt(val, dec=2):
    if val is None:
        return "N/A"
    if isinstance(val, str):
        return val
    return f"{val:.{dec}f}"


def exibir_resultado(modelo, label, vi, d0, g, r, preco=None, extra=None):
    print(f"\n--- {label} ---")
    print(f"  Valor Intrinseco:        $ {fmt(vi)}")
    if vi is not None:
        d1 = d0 * (1 + g)
        print(f"  Proximo dividendo (D1):  $ {fmt(d1)}")
        print(f"  Dividend Yield (D1/P):   {fmt(d1/vi*100, 2)}%")

    if preco and preco > 0:
        print(f"  Preco de mercado:       $ {fmt(preco)}")
        ms = margem_seguranca(vi, preco)
        if ms is not None:
            status = "SUBVALORIZADA" if ms > 0 else "SOBREVALORIZADA"
            print(f"  Margem de Seguranca:    {fmt(ms, 2)}% ({status})")
        ri = taxa_retorno_implicita(d0, g, preco) if modelo == 'g1' else None
        if ri is not None:
            print(f"  Retorno implicito (r):  {fmt(ri*100, 2)}%")
        pb = payback_anos(d0, g, preco)
        if pb is not None:
            print(f"  Payback (anos):          {pb}")

    if extra:
        for k, v in extra.items():
            print(f"  {k}: {v}")


def exibir_resultado_dcf(ev, divida_liquida, acoes, preco=None, label="DCF", extra=None):
    print(f"\n--- {label} ---")
    if ev is None:
        print("  Enterprise Value:       N/A")
        return None, None
    eq = ev - divida_liquida
    vp = eq / acoes if acoes > 0 else None
    print(f"  Enterprise Value (EV):   ${fmt(ev)}")
    print(f"  (-) Divida Liquida:      ${fmt(divida_liquida)}")
    print(f"  (=) Equity Value:        ${fmt(eq)}")
    print(f"  Acoes outstanding:       {fmt(acoes, 2)}")
    if vp is not None:
        print(f"  Valor Intrinseco / acao: ${fmt(vp)}")
    if preco and preco > 0 and vp is not None:
        print(f"  Preco de mercado:       ${fmt(preco)}")
        ms = margem_seguranca(vp, preco)
        if ms is not None:
            status = "SUBVALORIZADA" if ms > 0 else "SOBREVALORIZADA"
            print(f"  Margem de Seguranca:    {fmt(ms, 2)}% ({status})")
    if extra:
        for k, v in extra.items():
            print(f"  {k}: {v}")
    return eq, vp


# ======================== TABELA DE SENSIBILIDADE ========================

def gerar_tabela_sensibilidade(d0, g_base, r_base, modelo='g1', arquivo=None,
                               g1=None, g2=None, n=None, bvps=None, roe=None,
                               divida_liquida=None, acoes=None):
    if arquivo is None:
        arquivo = f"sensibilidade_{datetime.now():%Y%m%d_%H%M%S}.csv"

    if modelo == 'pbv' and bvps:
        faixa_g = [g_base + i*0.005 for i in range(-4, 5)]
        faixa_g = [max(0.01, min(0.99, x)) for x in faixa_g]
        faixa_r = [r_base + i*0.005 for i in range(-4, 5)]
        faixa_r = [max(0.01, min(0.99, x)) for x in faixa_r]
    else:
        faixa_g = [g_base + i*0.005 for i in range(-4, 5)]
        faixa_g = [max(0.0, min(0.99, x)) for x in faixa_g]
        faixa_r = [r_base + i*0.005 for i in range(-4, 5)]
        faixa_r = [max(0.01, min(0.99, x)) for x in faixa_r]

    with open(arquivo, "w", newline="") as f:
        w = csv.writer(f)
        cab = [""] + [f"{x*100:.1f}%" for x in faixa_r]
        w.writerow(cab)

        print(f"\n{'':>8}", end="")
        for x in faixa_r:
            print(f"{x*100:>8.1f}%", end="")
        print()

        for gx in faixa_g:
            linha_rotulo = f"{gx*100:.1f}%"
            print(f"{linha_rotulo:>8}", end="")
            linha_csv = [linha_rotulo]
            for rx in faixa_r:
                if modelo == 'g1':
                    v = gordon_1estagio(d0, gx, rx)
                elif modelo == 'g2' and g1 is not None:
                    v = gordon_2estagios(d0, g1, gx, n, rx) if n else None
                elif modelo == 'h' and g1 is not None:
                    v = h_model(d0, g1, gx, n, rx) if n else None
                elif modelo == 'dcf' and g1 is not None and acoes is not None:
                    ev = dcf_2estagios(d0, g1, gx, n, rx) if n else None
                    if ev is not None:
                        v = (ev - (divida_liquida or 0)) / acoes
                    else:
                        v = None
                elif modelo == 'pbv' and bvps is not None:
                    v = pbv_roe(bvps, gx, rx, 0)
                else:
                    v = gordon_1estagio(d0, gx, rx)

                vs = fmt(v, 2) if v is not None else "N/A"
                print(f"{vs:>8}", end="")
                linha_csv.append(vs)
            print()
            w.writerow(linha_csv)

    print(f"\nTabela salva: {arquivo}")
    return arquivo


# ======================== GRAFICO ========================

def gerar_grafico(d0, g_base, r_base, preco, modelo='g1', arquivo="grafico_gordon.png",
                  g1=None, n=None, bvps=None, roe=None, divida_liquida=None, acoes=None):
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("matplotlib nao instalado. Pulando grafico.")
        return

    faixa_g = np.linspace(max(0.01, g_base - 0.04), min(0.20, g_base + 0.04), 40)
    faixa_r = np.linspace(max(0.03, r_base - 0.04), min(0.20, r_base + 0.04), 40)
    G, R = np.meshgrid(faixa_g, faixa_r)

    V = np.zeros_like(G)
    for i in range(len(faixa_r)):
        for j in range(len(faixa_g)):
            if modelo == 'g1':
                v = gordon_1estagio(d0, G[i, j], R[i, j])
            elif modelo == 'h' and g1 is not None and n:
                v = h_model(d0, g1, G[i, j], n, R[i, j])
            elif modelo == 'dcf' and g1 is not None and n and acoes is not None:
                ev = dcf_2estagios(d0, g1, G[i, j], n, R[i, j])
                if ev is not None:
                    v = (ev - (divida_liquida or 0)) / acoes
                else:
                    v = None
            elif modelo == 'pbv' and bvps:
                v = pbv_roe(bvps, roe or 0.10, R[i, j], G[i, j])
            else:
                v = gordon_1estagio(d0, G[i, j], R[i, j])
            V[i, j] = v if v is not None and v < 500 else np.nan

    fig, ax = plt.subplots(figsize=(10, 7))
    cmap = ax.pcolormesh(G * 100, R * 100, V, shading='auto', cmap='RdYlGn')
    fig.colorbar(cmap, ax=ax, label='Valor Intrinseco ($)')

    if preco and preco > 0:
        ax.contour(G * 100, R * 100, V, levels=[preco], colors='blue', linewidths=2, linestyles='--')
        ax.text(g_base * 100 + 0.5, r_base * 100 - 1, f'Preco: ${preco:.0f}', color='blue', fontsize=9)

    ax.set_xlabel('Taxa de Crescimento g (%)')
    ax.set_ylabel('Taxa de Retorno Exigida r (%)')
    titulo = f"BAC - Valor Intrinseco ({modelo.upper()})"
    if preco:
        titulo += f" | Mercado: ${preco:.2f}"
    ax.set_title(titulo)
    ax.plot(g_base * 100, r_base * 100, 'ko', markersize=8, label='Cenario Base')
    ax.legend()
    fig.tight_layout()
    fig.savefig(arquivo, dpi=150)
    print(f"Grafico salvo: {arquivo}")
    plt.close(fig)


# ======================== EXECUCAO BAC ========================

def analisar_bac():
    print("=" * 65)
    print("   ANALISE BANK OF AMERICA (BAC) - MAIO 2026")
    print("=" * 65)

    d0 = 1.12
    preco = 51.80
    bvps = 38.66
    roe = 0.105
    r = 0.10
    g = 0.07
    g1 = 0.08
    g2 = 0.04
    n = 5

    # DCF params (valores agregados em bilhoes)
    fcf0 = 30.0
    divida_liquida = 5.0
    acoes = 7.8
    wacc = 0.10
    dcf_g1 = 0.06
    dcf_g2 = 0.03
    dcf_n = 5

    # Graham params
    eps = 3.46

    # Owner Earnings params (por acao)
    oe_lucro = 3.46
    oe_da = 0.50
    oe_capex = 0.30

    # CAPM / WACC params
    rf = 0.0425
    beta = 1.35
    rm = 0.10
    bac_equity = 340.0
    bac_divida = 280.0
    bac_re = 0.0
    bac_rd = 0.045
    bac_t = 0.21

    # Avaliacao Relativa params
    rel_eps = 3.46
    rel_bvps = 38.66
    rel_ebitda_pa = 5.13
    rel_receita_pa = 12.82
    rel_fcf_pa = 3.85

    print(f"\nParametros:")
    print(f"  D0             = $ {d0:.2f}")
    print(f"  Preco mercado  = $ {preco:.2f}")
    print(f"  BVPS           = $ {bvps:.2f}")
    print(f"  ROE            = {roe*100:.1f}%")
    print(f"  r (base)       = {r*100:.1f}%")
    print(f"  g (1 estagio)  = {g*100:.1f}%")
    print(f"  g1 (2 estag.)  = {g1*100:.1f}% ({n} anos)")
    print(f"  g2 (perpetuo)  = {g2*100:.1f}%")
    print(f"  --- DCF ---")
    print(f"  FCF0 (total)   = $ {fcf0:.1f} B")
    print(f"  Divida Liquida = $ {divida_liquida:.1f} B")
    print(f"  Acoes          = {acoes:.1f} B")
    print(f"  WACC           = {wacc*100:.1f}%")
    print(f"  g1 (cresc.)    = {dcf_g1*100:.1f}% ({dcf_n} anos)")
    print(f"  g2 (terminal)  = {dcf_g2*100:.1f}%")
    print(f"  --- Graham ---")
    print(f"  EPS            = $ {eps:.2f}")
    print(f"  --- Owner Earnings ---")
    print(f"  Lucro Liquido  = $ {oe_lucro:.2f}")
    print(f"  D&A            = $ {oe_da:.2f}")
    print(f"  Capex Manut.   = $ {oe_capex:.2f}")
    print(f"  --- CAPM / WACC ---")
    print(f"  RF (T 10y)     = {rf*100:.2f}%")
    print(f"  Beta           = {beta:.2f}")
    print(f"  RM (mercado)   = {rm*100:.0f}%")
    print(f"  Equity (E)     = $ {bac_equity:.0f} B")
    print(f"  Divida (D)     = $ {bac_divida:.0f} B")
    print(f"  Rd (custo divida) = {bac_rd*100:.1f}%")
    print(f"  T (taxa)       = {bac_t*100:.0f}%")
    print(f"  --- Relativa ---")
    print(f"  EPS            = $ {rel_eps:.2f}")
    print(f"  BVPS           = $ {rel_bvps:.2f}")
    print(f"  EBITDA/acao    = $ {rel_ebitda_pa:.2f}")
    print(f"  Receita/acao   = $ {rel_receita_pa:.2f}")
    print(f"  FCF/acao       = $ {rel_fcf_pa:.2f}")

    # ---- Modelo A: Gordon 1 estagio ----
    print("\n" + "=" * 65)
    print("   MODELO A: GORDON 1 ESTAGIO")
    print("=" * 65)
    print(f"\n{'Cenario':<15} {'g':>6} {'r':>6} {'VI':>10} {'Margem':>8}")
    print("-" * 50)

    cenarios_g1 = [
        ("Base", g, r),
        ("Conservador", 0.05, 0.11),
        ("Otimista", 0.09, 0.09),
        ("Cresc. Baixo", 0.04, 0.10),
        ("Ret. Alto", 0.07, 0.12),
        ("Ret. Baixo", 0.07, 0.085),
    ]
    for nome, gc, rc in cenarios_g1:
        vi = gordon_1estagio(d0, gc, rc)
        ms = margem_seguranca(vi, preco)
        vi_s = fmt(vi, 2) if vi is not None else "N/A  "
        ms_s = f"{ms:+.1f}%" if ms is not None else " N/A "
        status = "SUB" if ms is not None and ms > 10 else ("JUSTA" if ms is not None and ms >= -10 else "SOBRE")
        print(f"{nome:<15} {gc*100:>5.1f}% {rc*100:>5.1f}% ${vi_s:>8} {ms_s:>8} ({status})")

    # ---- Modelo B: Gordon 2 estagios ----
    print("\n" + "=" * 65)
    print("   MODELO B: GORDON 2 ESTAGIOS")
    print("=" * 65)
    print(f"\n{'Cenario':<15} {'g1':>6} {'g2':>6} {'r':>6} {'VI':>10} {'Margem':>8}")
    print("-" * 55)

    cenarios_g2 = [
        ("Base", 0.08, 0.04, 0.10),
        ("Conservador", 0.07, 0.035, 0.11),
        ("Otimista", 0.09, 0.045, 0.09),
        ("g2 mais alto", 0.08, 0.05, 0.10),
        ("r mais alto", 0.08, 0.04, 0.12),
    ]
    for nome, gc1, gc2, rc in cenarios_g2:
        vi = gordon_2estagios(d0, gc1, gc2, n, rc)
        ms = margem_seguranca(vi, preco)
        vi_s = fmt(vi, 2) if vi is not None else "N/A  "
        ms_s = f"{ms:+.1f}%" if ms is not None else " N/A "
        status = "SUB" if ms is not None and ms > 10 else ("JUSTA" if ms is not None and ms >= -10 else "SOBRE")
        print(f"{nome:<15} {gc1*100:>5.1f}% {gc2*100:>5.1f}% {rc*100:>5.1f}% ${vi_s:>8} {ms_s:>8} ({status})")

    # ---- Modelo C: P/B x ROE ----
    print("\n" + "=" * 65)
    print("   MODELO C: P/B x ROE (RESIDUAL INCOME)")
    print("=" * 65)
    print(f"\n{'Cenario':<15} {'ROE':>6} {'g':>6} {'r':>6} {'VI':>10} {'Margem':>8}")
    print("-" * 55)

    cenarios_pbv = [
        ("Base", 0.105, 0.0, 0.10),
        ("Com crescimento", 0.105, 0.04, 0.10),
        ("ROE maior", 0.12, 0.0, 0.10),
        ("ROE menor", 0.09, 0.0, 0.10),
        ("r maior", 0.105, 0.0, 0.12),
    ]
    for nome, rroe, rg, rr in cenarios_pbv:
        vi = pbv_roe(bvps, rroe, rr, rg)
        ms = margem_seguranca(vi, preco)
        vi_s = fmt(vi, 2) if vi is not None else "N/A  "
        ms_s = f"{ms:+.1f}%" if ms is not None else " N/A "
        status = "SUB" if ms is not None and ms > 10 else ("JUSTA" if ms is not None and ms >= -10 else "SOBRE")
        g_label = f"{rg*100:.1f}%" if rg > 0 else "0%"
        print(f"{nome:<15} {rroe*100:>5.1f}% {g_label:>6} {rr*100:>5.1f}% ${vi_s:>8} {ms_s:>8} ({status})")

    # ---- Modelo D: H-Model ----
    print("\n" + "=" * 65)
    print("   MODELO D: H-MODEL (FULLER-HSIA)")
    print("=" * 65)
    print(f"\n{'Cenario':<15} {'g1':>6} {'g2':>6} {'n':>4} {'r':>6} {'VI':>10} {'Margem':>8}")
    print("-" * 60)

    cenarios_h = [
        ("Base", 0.08, 0.04, 5, 0.10),
        ("Conservador", 0.07, 0.035, 5, 0.11),
        ("Otimista", 0.09, 0.045, 6, 0.09),
        ("Declinio curto", 0.08, 0.04, 3, 0.10),
        ("Declinio longo", 0.08, 0.04, 8, 0.10),
        ("g2 mais alto", 0.08, 0.05, 5, 0.10),
    ]
    for nome, hg1, hg2, hn, hr in cenarios_h:
        vi = h_model(d0, hg1, hg2, hn, hr)
        ms = margem_seguranca(vi, preco)
        vi_s = fmt(vi, 2) if vi is not None else "N/A  "
        ms_s = f"{ms:+.1f}%" if ms is not None else " N/A "
        status = "SUB" if ms is not None and ms > 10 else ("JUSTA" if ms is not None and ms >= -10 else "SOBRE")
        print(f"{nome:<15} {hg1*100:>5.1f}% {hg2*100:>5.1f}% {hn:>4} {hr*100:>5.1f}% ${vi_s:>8} {ms_s:>8} ({status})")

    # ---- Modelo E: DCF ----
    print("\n" + "=" * 65)
    print("   MODELO E: DCF (FLUXO DE CAIXA DESCONTADO)")
    print("=" * 65)
    print(f"\n{'Cenario':<15} {'g1':>6} {'g2':>6} {'n':>4} {'WACC':>6} {'EV':>10} {'$/acao':>8} {'Margem':>8}")
    print("-" * 70)

    cenarios_dcf = [
        ("Base", 0.06, 0.03, 5, 0.10),
        ("Conservador", 0.05, 0.025, 5, 0.11),
        ("Otimista", 0.07, 0.035, 5, 0.09),
        ("Cresc. alto", 0.08, 0.03, 5, 0.10),
        ("WACC alto", 0.06, 0.03, 5, 0.12),
        ("g2 maior", 0.06, 0.04, 5, 0.10),
    ]
    for nome, dg1, dg2, dn, dw in cenarios_dcf:
        ev = dcf_2estagios(fcf0, dg1, dg2, dn, dw)
        eq = (ev - divida_liquida) if ev is not None else None
        vp = eq / acoes if eq is not None else None
        ms = margem_seguranca(vp, preco)
        ev_s = fmt(ev, 2) if ev is not None else "N/A"
        vp_s = fmt(vp, 2) if vp is not None else "N/A"
        ms_s = f"{ms:+.1f}%" if ms is not None else " N/A "
        status = "SUB" if ms is not None and ms > 10 else ("JUSTA" if ms is not None and ms >= -10 else "SOBRE")
        print(f"{nome:<15} {dg1*100:>5.1f}% {dg2*100:>5.1f}% {dn:>4} {dw*100:>5.1f}% ${ev_s:>8} ${vp_s:>7} {ms_s:>8} ({status})")

    # ---- Modelo F: Graham Number ----
    print("\n" + "=" * 65)
    print("   MODELO F: GRAHAM NUMBER")
    print("=" * 65)
    gn = graham_number(eps, bvps)
    print(f"\n  Graham Number = sqrt(22.5 * EPS * BVPS)")
    print(f"                 = sqrt(22.5 * {eps:.2f} * {bvps:.2f})")
    print(f"                 = $ {fmt(gn)}")
    if gn is not None:
        ms_gn = margem_seguranca(gn, preco)
        ms_s_gn = f"{ms_gn:+.1f}%" if ms_gn is not None else "N/A"
        status_gn = "SUBVALORIZADA" if ms_gn is not None and ms_gn > 0 else ("SOBREVALORIZADA" if ms_gn is not None else "N/A")
        print(f"\n  Preco de mercado:       $ {fmt(preco)}")
        print(f"  Margem de Seguranca:    {ms_s_gn} ({status_gn})")
        print(f"  P/E maximo implicito:   {fmt(preco/eps, 2)} (max Graham: 15)")
        print(f"  P/B maximo implicito:   {fmt(preco/bvps, 2)} (max Graham: 1.5)")

    # ---- Modelo G: Owner Earnings (Buffett) ----
    print("\n" + "=" * 65)
    print("   MODELO G: OWNER EARNINGS (WARREN BUFFETT)")
    print("=" * 65)
    oe = owner_earnings(oe_lucro, oe_da, oe_capex)
    print(f"\n  OE = Lucro Liquido + D&A - Capex Manutencao")
    print(f"     = {oe_lucro:.2f} + {oe_da:.2f} - {oe_capex:.2f}")
    print(f"     = $ {oe:.2f} / acao")
    print(f"\n{'Cenario':<15} {'g':>6} {'r':>6} {'OE':>6} {'VI':>10} {'Margem':>8}")
    print("-" * 55)
    cenarios_oe = [
        ("EPV (g=0)", 0.0, 0.10),
        ("Base", 0.03, 0.10),
        ("Conservador", 0.02, 0.11),
        ("Otimista", 0.04, 0.09),
        ("Ret. Alto", 0.03, 0.12),
    ]
    for nome, og, or_ in cenarios_oe:
        vi = oe_valuation(oe, or_, og)
        ms = margem_seguranca(vi, preco)
        vi_s = fmt(vi, 2) if vi is not None else "N/A"
        ms_s = f"{ms:+.1f}%" if ms is not None else "N/A"
        status = "SUB" if ms is not None and ms > 10 else ("JUSTA" if ms is not None and ms >= -10 else "SOBRE")
        g_label = f"{og*100:.0f}%" if og > 0 else "0%"
        print(f"{nome:<15} {g_label:>6} {or_*100:>5.1f}% ${oe:>5.2f} ${vi_s:>8} {ms_s:>8} ({status})")

    # ---- Modelo H: CAPM / WACC ----
    print("\n" + "=" * 65)
    print("   MODELO H: CAPM / WACC")
    print("=" * 65)
    re_capm = capm(rf, beta, rm)
    wacc_val = calcular_wacc(bac_equity, bac_divida, re_capm, bac_rd, bac_t)
    print(f"\n  CAPM:")
    print(f"    Re = RF + Beta * (RM - RF)")
    print(f"       = {rf*100:.2f}% + {beta:.2f} * ({rm*100:.0f}% - {rf*100:.2f}%)")
    print(f"       = {re_capm*100:.2f}%")
    if wacc_val is not None:
        print(f"\n  WACC:")
        print(f"    WACC = E/V * Re + D/V * Rd * (1 - T)")
        print(f"         = {bac_equity:.0f}/{bac_equity+bac_divida:.0f} * {re_capm*100:.2f}% + {bac_divida:.0f}/{bac_equity+bac_divida:.0f} * {bac_rd*100:.1f}% * (1 - {bac_t*100:.0f}%)")
        print(f"         = {wacc_val*100:.2f}%")

    # ---- Modelo I: Avaliacao Relativa ----
    print("\n" + "=" * 65)
    print("   MODELO I: AVALIACAO RELATIVA (MULTIPLOS)")
    print("=" * 65)
    setor = {
        "P/E":      {"multiplo": 13.0, "label": "P/E (Preco/Lucro)", "fund": rel_eps},
        "P/B":      {"multiplo": 1.10, "label": "P/B (Preco/Book)", "fund": rel_bvps},
        "EV/EBITDA":{"multiplo": 11.0, "label": "EV/EBITDA", "fund": rel_ebitda_pa},
        "P/S":      {"multiplo": 2.80, "label": "P/S (Preco/Receita)", "fund": rel_receita_pa},
        "P/FCF":    {"multiplo": 12.0, "label": "P/FCF (Preco/FCF)", "fund": rel_fcf_pa},
    }
    print(f"\n{'Multiplo':<20} {'Atual':>8} {'Setor':>8} {'Alvo':>8} {'Upside':>8}")
    print("-" * 56)
    alvos = []
    for chave, dados in setor.items():
        mult_atual = multiplo_atual(preco, dados["fund"])
        alvo = preco_alvo_multiplo(dados["multiplo"], dados["fund"])
        ups = upside_percent(alvo, preco)
        alvos.append(alvo)
        print(f"{dados['label']:<20} {fmt(mult_atual,2):>8} {dados['multiplo']:>8.1f}x ${fmt(alvo,2):>8} {fmt(ups,1):>8}%")
    alvos_validos = [a for a in alvos if a is not None]
    if alvos_validos:
        media_alvo = sum(alvos_validos) / len(alvos_validos)
        ups_media = upside_percent(media_alvo, preco)
        print(f"\n  >>> Media dos alvos: $ {fmt(media_alvo,2)} ({ups_media:+.1f}%)")

    # ---- Tabelas e graficos ----
    pasta = os.path.dirname(os.path.abspath(__file__))
    gerar_tabela_sensibilidade(d0, g, r, 'g1', os.path.join(pasta, "sensibilidade_gordon1_bac.csv"))
    gerar_tabela_sensibilidade(d0, g_base=g2, r_base=r, modelo='h',
                               arquivo=os.path.join(pasta, "sensibilidade_h_model_bac.csv"),
                               g1=g1, n=n)
    gerar_tabela_sensibilidade(fcf0, g_base=dcf_g2, r_base=wacc, modelo='dcf',
                               arquivo=os.path.join(pasta, "sensibilidade_dcf_bac.csv"),
                               g1=dcf_g1, n=dcf_n, divida_liquida=divida_liquida, acoes=acoes)
    gerar_tabela_sensibilidade(d0, g, r, 'pbv', os.path.join(pasta, "sensibilidade_pbv_bac.csv"),
                               bvps=bvps, roe=roe)
    gerar_grafico(d0, g, r, preco, 'g1', os.path.join(pasta, "grafico_gordon1_bac.png"))
    gerar_grafico(d0, g1=g1, g_base=g2, r_base=r, preco=preco, modelo='h',
                  arquivo=os.path.join(pasta, "grafico_h_model_bac.png"), n=n)
    gerar_grafico(fcf0, g1=dcf_g1, g_base=dcf_g2, r_base=wacc, preco=preco, modelo='dcf',
                  arquivo=os.path.join(pasta, "grafico_dcf_bac.png"), n=dcf_n,
                  divida_liquida=divida_liquida, acoes=acoes)
    gerar_grafico(d0, g, r, preco, 'pbv', os.path.join(pasta, "grafico_pbv_bac.png"),
                  bvps=bvps, roe=roe)

    # ---- Conclusao ----
    print("\n" + "=" * 65)
    print("   CONCLUSAO")
    print("=" * 65)

    vi_g1 = gordon_1estagio(d0, g, r)
    vi_g2 = gordon_2estagios(d0, g1, g2, n, r)
    vi_pbv = pbv_roe(bvps, roe, r, 0)
    vi_h = h_model(d0, g1, g2, n, r)
    ev_dcf = dcf_2estagios(fcf0, dcf_g1, dcf_g2, dcf_n, wacc)
    vi_dcf = (ev_dcf - divida_liquida) / acoes if ev_dcf is not None else None
    vi_gn = graham_number(eps, bvps)
    oe_val = owner_earnings(oe_lucro, oe_da, oe_capex)
    vi_oe = oe_valuation(oe_val, r, 0.03)
    rel_setor_mult = {"P/E": 13.0, "P/B": 1.10, "EV/EBITDA": 11.0, "P/S": 2.80, "P/FCF": 12.0}
    rel_fund = {"P/E": rel_eps, "P/B": rel_bvps, "EV/EBITDA": rel_ebitda_pa, "P/S": rel_receita_pa, "P/FCF": rel_fcf_pa}
    rel_alvos = [preco_alvo_multiplo(rel_setor_mult[k], rel_fund[k]) for k in rel_setor_mult]
    rel_alvos_v = [a for a in rel_alvos if a is not None]
    vi_rel = sum(rel_alvos_v) / len(rel_alvos_v) if rel_alvos_v else None

    ms1 = margem_seguranca(vi_g1, preco)
    ms2 = margem_seguranca(vi_g2, preco)
    ms3 = margem_seguranca(vi_pbv, preco)
    ms4 = margem_seguranca(vi_h, preco)
    ms5 = margem_seguranca(vi_dcf, preco)
    ms6 = margem_seguranca(vi_gn, preco)
    ms7 = margem_seguranca(vi_oe, preco)
    ms8 = margem_seguranca(vi_rel, preco) if vi_rel else None

    print(f"\nPreco de mercado: $ {preco:.2f}")
    print(f"  Gordon 1 estagio (g={g*100:.0f}%, r={r*100:.0f}%):        $ {fmt(vi_g1)}  ({ms1:+.1f}%)")
    print(f"  Gordon 2 estagios (g1={g1*100:.0f}%, g2={g2*100:.0f}%, r={r*100:.0f}%): $ {fmt(vi_g2)}  ({ms2:+.1f}%)")
    print(f"  P/B x ROE (ROE={roe*100:.1f}%, r={r*100:.0f}%):              $ {fmt(vi_pbv)}  ({ms3:+.1f}%)")
    print(f"  H-Model (g1={g1*100:.0f}%, g2={g2*100:.0f}%, n={n}, r={r*100:.0f}%):    $ {fmt(vi_h)}  ({ms4:+.1f}%)")
    print(f"  DCF (g1={dcf_g1*100:.0f}%, g2={dcf_g2*100:.0f}%, WACC={wacc*100:.0f}%):        $ {fmt(vi_dcf)}  ({ms5:+.1f}%)")
    print(f"  Graham Number (EPS={eps}, BVPS={bvps}):          $ {fmt(vi_gn)}  ({ms6:+.1f}%)")
    print(f"  Owner Earnings (OE=${oe_val:.2f}, g=3%, r=10%):         $ {fmt(vi_oe)}  ({ms7:+.1f}%)")
    print(f"  Avaliacao Relativa (media 5 multiplos):            $ {fmt(vi_rel)}  ({ms8:+.1f}%)" if vi_rel else "")

    vis = [v for v in [vi_g1, vi_g2, vi_pbv, vi_h, vi_dcf, vi_gn, vi_oe, vi_rel] if v is not None]
    if vis:
        media = sum(vis) / len(vis)
        ms_media = margem_seguranca(media, preco)
        print(f"\n  >>> Media dos {len(vis)} modelos: $ {fmt(media, 2)}  ({ms_media:+.1f}%)")
        if ms_media > 15:
            print("  >>> RECOMENDACAO: SUBVALORIZADA - COMPRA")
        elif ms_media > 0:
            print("  >>> RECOMENDACAO: LIGEIRAMENTE SUBVALORIZADA - MANTER/ACUMULAR")
        elif ms_media > -15:
            print("  >>> RECOMENDACAO: PROXIMA DO JUSTO - MANTER")
        else:
            print("  >>> RECOMENDACAO: SOBREVALORIZADA - AGUARDAR")

    print()


def analisar_empresa_ticker(ticker_str):
    resultado = ticker_search.executar_analise_completa(ticker_str)
    if not resultado:
        return
    dados, params = resultado
    preco = params["preco"]
    eps = params["eps"]
    bvps = params["bvps"]
    d0 = params["d0"]
    g = params["g_estimado"]
    re = params["re_estimado"]
    wacc_est = params["wacc_estimado"]
    roe = params["roe"]
    fcf_pa = params["fcf_per_share"]
    ebitda_pa = params["ebitda_per_share"]
    receita_pa = params["receita_per_share"]
    divida_liq = params["divida_liquida"]
    shares = params["shares"]
    fcf_total = params["fcf_total"]
    beta = params["beta"]
    if not preco or preco <= 0:
        print("Preco nao disponivel.")
        return
    print("\n" + "=" * 65)
    print(f"   ANALISE DE VALOR INTRINSECO: {dados['ticker']}")
    print("=" * 65)
    vi_g1 = gordon_1estagio(d0, g, re) if d0 else None
    vi_gn = graham_number(eps, bvps) if eps and bvps else None
    vi_oe = oe_valuation(eps, re, g) if eps else None
    vi_pbv = pbv_roe(bvps, roe, re, 0) if bvps and roe else None
    vi_dcf = None
    if fcf_total and shares and shares > 0 and wacc_est and wacc_est > 0:
        ev_dcf = dcf_2estagios(fcf_total, g, 0.025, 5, wacc_est)
        if ev_dcf and divida_liq:
            vi_dcf = (ev_dcf - divida_liq) / shares
    print(f"\n  Preco atual:       $ {fmt(preco)}")
    print(f"\n{'Modelo':<35} {'VI':>8} {'Margem':>8}")
    print("-" * 55)
    resultados = {}
    if vi_g1:
        ms = margem_seguranca(vi_g1, preco)
        resultados["Gordon 1E"] = vi_g1
        print(f"{'Gordon 1E (g='+str(round(g*100,1))+'%, r='+str(round(re*100,1))+'%)':<35} ${fmt(vi_g1):>7} {ms:+.1f}%" if ms else f"{'Gordon 1E':<35} ${fmt(vi_g1):>7}")
    if vi_pbv:
        ms = margem_seguranca(vi_pbv, preco)
        resultados["P/B x ROE"] = vi_pbv
        print(f"{'P/B x ROE (ROE='+str(round(roe*100,1))+'%)':<35} ${fmt(vi_pbv):>7} {ms:+.1f}%" if ms else f"{'P/B x ROE':<35} ${fmt(vi_pbv):>7}")
    if vi_gn:
        ms = margem_seguranca(vi_gn, preco)
        resultados["Graham Number"] = vi_gn
        print(f"{'Graham Number':<35} ${fmt(vi_gn):>7} {ms:+.1f}%" if ms else f"{'Graham Number':<35} ${fmt(vi_gn):>7}")
    if vi_oe:
        ms = margem_seguranca(vi_oe, preco)
        resultados["Owner Earnings"] = vi_oe
        print(f"{'Owner Earnings (g=0)':<35} ${fmt(vi_oe):>7} {ms:+.1f}%" if ms else f"{'Owner Earnings':<35} ${fmt(vi_oe):>7}")
    if vi_dcf:
        ms = margem_seguranca(vi_dcf, preco)
        resultados["DCF"] = vi_dcf
        print(f"{'DCF (WACC='+str(round(wacc_est*100,1))+'%)':<35} ${fmt(vi_dcf):>7} {ms:+.1f}%" if ms else f"{'DCF':<35} ${fmt(vi_dcf):>7}")
    alvos_rel = []
    if eps:
        alvos_rel.append(preco_alvo_multiplo(13.0, eps))
    if bvps:
        alvos_rel.append(preco_alvo_multiplo(1.10, bvps))
    if ebitda_pa:
        alvos_rel.append(preco_alvo_multiplo(11.0, ebitda_pa))
    if receita_pa:
        alvos_rel.append(preco_alvo_multiplo(2.80, receita_pa))
    if fcf_pa:
        alvos_rel.append(preco_alvo_multiplo(12.0, fcf_pa))
    alvos_v = [a for a in alvos_rel if a]
    if alvos_v:
        vi_rel = sum(alvos_v) / len(alvos_v)
        ms = margem_seguranca(vi_rel, preco)
        resultados["Relativa"] = vi_rel
        print(f"{'Relativa (media 5 mult.)':<35} ${fmt(vi_rel):>7} {ms:+.1f}%" if ms else f"{'Relativa':<35} ${fmt(vi_rel):>7}")
    vis = [v for v in resultados.values() if v]
    if vis:
        media = sum(vis) / len(vis)
        ms_media = margem_seguranca(media, preco)
        print(f"\n  >>> Media dos {len(vis)} modelos: $ {fmt(media, 2)}  ({ms_media:+.1f}%)")
        if ms_media > 15:
            print("  >>> RECOMENDACAO: SUBVALORIZADA - COMPRA")
        elif ms_media > 0:
            print("  >>> RECOMENDACAO: LIGEIRAMENTE SUBVALORIZADA - MANTER/ACUMULAR")
        elif ms_media > -15:
            print("  >>> RECOMENDACAO: PROXIMA DO JUSTO - MANTER")
        else:
            print("  >>> RECOMENDACAO: SOBREVALORIZADA - AGUARDAR")
    print()


# ======================== MODO INTERATIVO ========================

def modo_interativo():
    print("=" * 60)
    print("   CALCULADORA DE VALOR INTRINSECO")
    print("=" * 60)
    print("\nModelos disponiveis:")
    print("  1 - Gordon 1 estagio")
    print("  2 - Gordon 2 estagios")
    print("  3 - P/B x ROE (Residual Income)")
    print("  4 - Analise completa BAC")
    print("  5 - H-Model (Fuller-Hsia)")
    print("  6 - DCF (Fluxo de Caixa Descontado)")
    print("  7 - Graham Number")
    print("  8 - Owner Earnings (Buffett)")
    print("  9 - CAPM / WACC")
    print("  10 - Avaliacao Relativa (Multiplos)")
    print("  11 - Buscar empresa por ticker (Yahoo Finance)")
    print("  0 - Sair")

    try:
        op = int(input("\nEscolha: ") or "4")
    except ValueError:
        op = 4

    if op == 0:
        return
    if op == 4:
        analisar_bac()
        return

    if op == 1:
        d0 = float(input("D0 (dividendo anual): "))
        g = float(input("g (crescimento %, ex: 7): ")) / 100
        r = float(input("r (retorno exigido %, ex: 10): ")) / 100
        pm = input("Preco de mercado (opcional): ")
        pm = float(pm) if pm.strip() else None
        exibir_resultado('g1', "Gordon 1 Estagio", gordon_1estagio(d0, g, r), d0, g, r, pm)
        gerar_tabela_sensibilidade(d0, g, r, 'g1')

    elif op == 2:
        d0 = float(input("D0 (dividendo anual): "))
        g1 = float(input("g1 - cresc. alto % (ex: 8): ")) / 100
        n = int(input("N. anos cresc. alto: "))
        g2 = float(input("g2 - cresc. perpetuo % (ex: 4): ")) / 100
        r = float(input("r (retorno exigido %, ex: 10): ")) / 100
        pm = input("Preco de mercado (opcional): ")
        pm = float(pm) if pm.strip() else None
        vi = gordon_2estagios(d0, g1, g2, n, r)
        exibir_resultado('g2', f"Gordon 2 Estagios (g1={g1*100:.0f}%/{n}a -> g2={g2*100:.0f}%)",
                         vi, d0, g1, r, pm, extra={"g2 perpetuo": f"{g2*100:.1f}%"})

    elif op == 3:
        bvps = float(input("BVPS (book value por acao): "))
        roe = float(input("ROE % (ex: 10.5): ")) / 100
        r = float(input("r (retorno exigido %, ex: 10): ")) / 100
        g = input("g (crescimento %, opcional, Enter=0): ")
        g = float(g) / 100 if g.strip() else 0
        pm = input("Preco de mercado (opcional): ")
        pm = float(pm) if pm.strip() else None
        vi = pbv_roe(bvps, roe, r, g)
        extra = {"BVPS": f"${bvps:.2f}", "ROE": f"{roe*100:.1f}%"}
        exibir_resultado('pbv', f"P/B x ROE {'(c/ cresc.)' if g > 0 else '(s/ cresc.)'}",
                         vi, bvps * roe, g, r, pm, extra=extra)

    elif op == 5:
        d0 = float(input("D0 (dividendo anual): "))
        g1 = float(input("g1 - cresc. inicial % (ex: 8): ")) / 100
        g2 = float(input("g2 - cresc. terminal % (ex: 4): ")) / 100
        n = int(input("n - anos de declinio linear: "))
        r = float(input("r (retorno exigido %, ex: 10): ")) / 100
        pm = input("Preco de mercado (opcional): ")
        pm = float(pm) if pm.strip() else None
        vi = h_model(d0, g1, g2, n, r)
        exibir_resultado('h', f"H-Model (g1={g1*100:.0f}% -> g2={g2*100:.0f}%, {n}a)",
                         vi, d0, g1, r, pm,
                         extra={"g2 terminal": f"{g2*100:.1f}%", "n": str(n)})
        gerar_tabela_sensibilidade(d0, g_base=g2, r_base=r, modelo='h', g1=g1, n=n)

    elif op == 6:
        fcf0 = float(input("FCF0 (Free Cash Flow total, em milhoes): "))
        g1 = float(input("g1 - cresc. alto % (ex: 6): ")) / 100
        n = int(input("n - anos de cresc. alto: "))
        g2 = float(input("g2 - cresc. terminal % (ex: 3): ")) / 100
        wacc = float(input("WACC % (ex: 10): ")) / 100
        divida = float(input("Divida Liquida total (milhoes): "))
        acoes = float(input("Acoes outstanding (milhoes): "))
        pm = input("Preco de mercado por acao (opcional): ")
        pm = float(pm) if pm.strip() else None
        ev = dcf_2estagios(fcf0, g1, g2, n, wacc)
        _, vp = exibir_resultado_dcf(ev, divida, acoes, pm,
                                     label=f"DCF (g1={g1*100:.0f}%/{n}a -> g2={g2*100:.0f}%, WACC={wacc*100:.0f}%)",
                                     extra={"g1": f"{g1*100:.1f}%", "g2": f"{g2*100:.1f}%", "n": str(n), "WACC": f"{wacc*100:.1f}%"})
        gerar_tabela_sensibilidade(fcf0, g_base=g2, r_base=wacc, modelo='dcf',
                                   g1=g1, n=n, divida_liquida=divida, acoes=acoes)

    elif op == 7:
        eps = float(input("EPS (lucro por acao): "))
        bvps = float(input("BVPS (book value por acao): "))
        pm = input("Preco de mercado (opcional): ")
        pm = float(pm) if pm.strip() else None
        gn = graham_number(eps, bvps)
        print(f"\n--- Graham Number ---")
        print(f"  Graham Number = sqrt(22.5 * {eps:.2f} * {bvps:.2f})")
        print(f"                 = $ {fmt(gn)}")
        if gn is not None and pm and pm > 0:
            ms = margem_seguranca(gn, pm)
            if ms is not None:
                status = "SUBVALORIZADA" if ms > 0 else "SOBREVALORIZADA"
                print(f"  Margem de Seguranca:    {fmt(ms, 2)}% ({status})")
            print(f"  P/E atual:              {fmt(pm/eps, 2)} (Graham max: 15)")
            print(f"  P/B atual:              {fmt(pm/bvps, 2)} (Graham max: 1.5)")

    elif op == 8:
        lucro = float(input("Lucro Liquido por acao: "))
        da = float(input("D&A (depreciacao/amortizacao) por acao: "))
        capex = float(input("Capex de manutencao por acao: "))
        r = float(input("r (retorno exigido %, ex: 10): ")) / 100
        g = input("g (crescimento %, opcional, Enter=0): ")
        g = float(g) / 100 if g.strip() else 0
        pm = input("Preco de mercado (opcional): ")
        pm = float(pm) if pm.strip() else None
        oe = owner_earnings(lucro, da, capex)
        vi = oe_valuation(oe, r, g)
        print(f"\n--- Owner Earnings ---")
        print(f"  OE = {lucro:.2f} + {da:.2f} - {capex:.2f} = $ {oe:.2f}")
        if vi is not None:
            print(f"  Valor Intrinseco (g={g*100:.1f}%, r={r*100:.1f}%): $ {fmt(vi)}")
        if pm and pm > 0 and vi is not None:
            ms = margem_seguranca(vi, pm)
            if ms is not None:
                status = "SUBVALORIZADA" if ms > 0 else "SOBREVALORIZADA"
                print(f"  Margem de Seguranca:    {fmt(ms, 2)}% ({status})")
            print(f"  Preco / OE (P/OE):      {fmt(pm/oe, 2)}")


# ======================== CLI ========================

def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "--quick":
            d0 = float(sys.argv[2])
            g = float(sys.argv[3]) / 100
            r = float(sys.argv[4]) / 100
            pm = float(sys.argv[5]) if len(sys.argv) > 5 else None
            exibir_resultado('g1', "Gordon 1 Estagio", gordon_1estagio(d0, g, r), d0, g, r, pm)
        elif cmd == "--two-stage":
            d0 = float(sys.argv[2])
            g1 = float(sys.argv[3]) / 100
            g2 = float(sys.argv[4]) / 100
            n = int(sys.argv[5])
            r = float(sys.argv[6]) / 100
            pm = float(sys.argv[7]) if len(sys.argv) > 7 else None
            vi = gordon_2estagios(d0, g1, g2, n, r)
            exibir_resultado('g2', f"Gordon 2 Estagios", vi, d0, g1, r, pm,
                             extra={"g2 perpetuo": f"{g2*100:.1f}%"})
        elif cmd == "--h-model":
            d0 = float(sys.argv[2])
            g1 = float(sys.argv[3]) / 100
            g2 = float(sys.argv[4]) / 100
            n = int(sys.argv[5])
            r = float(sys.argv[6]) / 100
            pm = float(sys.argv[7]) if len(sys.argv) > 7 else None
            vi = h_model(d0, g1, g2, n, r)
            exibir_resultado('h', f"H-Model (g1={g1*100:.0f}% -> g2={g2*100:.0f}%, {n}a)",
                             vi, d0, g1, r, pm,
                             extra={"g2 terminal": f"{g2*100:.1f}%", "n": str(n)})
        elif cmd == "--dcf":
            fcf0 = float(sys.argv[2])
            g1 = float(sys.argv[3]) / 100
            g2 = float(sys.argv[4]) / 100
            n = int(sys.argv[5])
            wacc = float(sys.argv[6]) / 100
            divida = float(sys.argv[7])
            acoes = float(sys.argv[8])
            pm = float(sys.argv[9]) if len(sys.argv) > 9 else None
            ev = dcf_2estagios(fcf0, g1, g2, n, wacc)
            exibir_resultado_dcf(ev, divida, acoes, pm,
                                 label=f"DCF (g1={g1*100:.0f}%/{n}a -> g2={g2*100:.0f}%, WACC={wacc*100:.0f}%)",
                                 extra={"g1": f"{g1*100:.1f}%", "g2": f"{g2*100:.1f}%", "n": str(n), "WACC": f"{wacc*100:.1f}%"})
        elif cmd == "--graham":
            eps = float(sys.argv[2])
            bvps = float(sys.argv[3])
            pm = float(sys.argv[4]) if len(sys.argv) > 4 else None
            gn = graham_number(eps, bvps)
            print(f"\n--- Graham Number ---")
            print(f"  Graham Number = sqrt(22.5 * {eps:.2f} * {bvps:.2f})")
            print(f"                 = $ {fmt(gn)}")
            if gn is not None and pm and pm > 0:
                ms = margem_seguranca(gn, pm)
                if ms is not None:
                    status = "SUBVALORIZADA" if ms > 0 else "SOBREVALORIZADA"
                    print(f"  Margem de Seguranca:    {fmt(ms, 2)}% ({status})")
                print(f"  P/E atual:              {fmt(pm/eps, 2)} (Graham max: 15)")
                print(f"  P/B atual:              {fmt(pm/bvps, 2)} (Graham max: 1.5)")
        elif cmd == "--wacc":
            rf_c = float(sys.argv[2]) / 100
            beta_c = float(sys.argv[3])
            rm_c = float(sys.argv[4]) / 100
            eq_c = float(sys.argv[5])
            dv_c = float(sys.argv[6])
            rd_c = float(sys.argv[7]) / 100
            t_c = float(sys.argv[8]) / 100
            re_c = capm(rf_c, beta_c, rm_c)
            wacc_c = calcular_wacc(eq_c, dv_c, re_c, rd_c, t_c)
            print(f"\n--- CAPM ---")
            print(f"  Re = {rf_c*100:.2f}% + {beta_c:.2f} * ({rm_c*100:.0f}% - {rf_c*100:.2f}%)")
            print(f"     = {re_c*100:.2f}%")
            if wacc_c is not None:
                print(f"\n--- WACC ---")
                print(f"  WACC = {wacc_c*100:.2f}%")
        elif cmd == "--relativa":
            pm_r = float(sys.argv[2])
            pares_r = []
            i = 3
            while i + 2 < len(sys.argv):
                nome_r = sys.argv[i]
                fund_r = float(sys.argv[i+1])
                mult_r = float(sys.argv[i+2])
                pares_r.append((nome_r, fund_r, mult_r))
                i += 3
            if not pares_r:
                print("Uso: --relativa preco nome1 fund1 mult1 nome2 fund2 mult2 ...")
                return
            print(f"\n{'Multiplo':<20} {'Atual':>8} {'Setor':>8} {'Alvo':>8} {'Upside':>8}")
            print("-" * 56)
            alvos_r = []
            for nome, fund, mult_s in pares_r:
                mult_a = multiplo_atual(pm_r, fund)
                alvo = preco_alvo_multiplo(mult_s, fund)
                ups = upside_percent(alvo, pm_r)
                if alvo is not None:
                    alvos_r.append(alvo)
                print(f"{nome:<20} {fmt(mult_a,2):>8} {mult_s:>8.1f}x ${fmt(alvo,2):>8} {fmt(ups,1):>8}%")
            if alvos_r:
                media_alvo = sum(alvos_r) / len(alvos_r)
                ups_media = upside_percent(media_alvo, pm_r)
                print(f"\n  >>> Media dos alvos: $ {fmt(media_alvo,2)} ({ups_media:+.1f}%)")
        elif cmd == "--oe":
            lucro = float(sys.argv[2])
            da = float(sys.argv[3])
            capex = float(sys.argv[4])
            r = float(sys.argv[5]) / 100
            g = float(sys.argv[6]) / 100 if len(sys.argv) > 6 else 0
            pm = float(sys.argv[7]) if len(sys.argv) > 7 else None
            oe = owner_earnings(lucro, da, capex)
            vi = oe_valuation(oe, r, g)
            print(f"\n--- Owner Earnings ---")
            print(f"  OE = {lucro:.2f} + {da:.2f} - {capex:.2f} = $ {oe:.2f}")
            if vi is not None:
                print(f"  Valor Intrinseco (g={g*100:.1f}%, r={r*100:.1f}%): $ {fmt(vi)}")
            if pm and pm > 0 and vi is not None:
                ms = margem_seguranca(vi, pm)
                if ms is not None:
                    status = "SUBVALORIZADA" if ms > 0 else "SOBREVALORIZADA"
                    print(f"  Margem de Seguranca:    {fmt(ms, 2)}% ({status})")
            print(f"  Preco / OE (P/OE):      {fmt(pm/oe, 2)}")

    elif op == 9:
        print("\n--- CAPM ---")
        rf_i = float(input("RF (livre de risco %, ex: 4.25): ")) / 100
        beta_i = float(input("Beta: "))
        rm_i = float(input("RM (retorno mercado %, ex: 10): ")) / 100
        re_i = capm(rf_i, beta_i, rm_i)
        print(f"  Re (custo equity) = {re_i*100:.2f}%")
        print("\n--- WACC ---")
        eq_i = float(input("Equity (valor mercado, ex: 340): "))
        dv_i = float(input("Divida (valor mercado, ex: 280): "))
        rd_i = float(input("Rd (custo divida %, ex: 4.5): ")) / 100
        t_i = float(input("T (aliquota IR % , ex: 21): ")) / 100
        wacc_i = calcular_wacc(eq_i, dv_i, re_i, rd_i, t_i)
        if wacc_i is not None:
            print(f"  WACC = {wacc_i*100:.2f}%")
            v = eq_i + dv_i
            print(f"\n  Ponderacao:")
            print(f"    Equity: {eq_i:.1f} / {v:.1f} = {eq_i/v*100:.1f}%  x {re_i*100:.2f}% = {eq_i/v*re_i*100:.2f}%")
            print(f"    Divida: {dv_i:.1f} / {v:.1f} = {dv_i/v*100:.1f}%  x {rd_i*100:.1f}% x (1-{t_i*100:.0f}%) = {dv_i/v*rd_i*(1-t_i)*100:.2f}%")

    elif op == 10:
        print("\n--- Avaliacao Relativa ---")
        print("Informe os dados DA empresa e o multiplo DO SETOR:")
        pares = []
        while True:
            nome = input("Nome do multiplo (ex: P/E) ou Enter para calcular: ").strip()
            if not nome:
                break
            fundamental = float(input(f"  Valor fundamental ({nome}): "))
            mult_setor = float(input(f"  Multiplo setorial ({nome}): "))
            pares.append((nome, fundamental, mult_setor))
        pm = input("Preco de mercado (opcional): ")
        pm = float(pm) if pm.strip() else None
        if not pares:
            print("Nenhum multiplo informado.")
            return
        print(f"\n{'Multiplo':<20} {'Atual':>8} {'Setor':>8} {'Alvo':>8} {'Upside':>8}")
        print("-" * 56)
        alvos = []
        for nome, fund, mult_s in pares:
            mult_a = multiplo_atual(pm, fund)
            alvo = preco_alvo_multiplo(mult_s, fund)
            ups = upside_percent(alvo, pm)
            if alvo is not None:
                alvos.append(alvo)
            mult_a_s = fmt(mult_a, 2) if mult_a is not None else "N/A"
            alvo_s = fmt(alvo, 2) if alvo is not None else "N/A"
            ups_s = f"{ups:+.1f}%" if ups is not None else "N/A"
            print(f"{nome:<20} {mult_a_s:>8} {mult_s:>8.1f}x ${alvo_s:>8} {ups_s:>8}")
        if alvos:
            media_alvo = sum(alvos) / len(alvos)
            ups_media = upside_percent(media_alvo, pm)
            print(f"\n  >>> Media dos alvos: $ {fmt(media_alvo,2)} ({ups_media:+.1f}%)")

    elif op == 11:
        ticker_input = input("Ticker da empresa (ex: AAPL, PETR4.SA, BAC): ").strip()
        if ticker_input:
            analisar_empresa_ticker(ticker_input)


# ======================== CLI ========================

def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "--quick":
            d0 = float(sys.argv[2])
            g = float(sys.argv[3]) / 100
            r = float(sys.argv[4]) / 100
            pm = float(sys.argv[5]) if len(sys.argv) > 5 else None
            exibir_resultado('g1', "Gordon 1 Estagio", gordon_1estagio(d0, g, r), d0, g, r, pm)
        elif cmd == "--two-stage":
            d0 = float(sys.argv[2])
            g1 = float(sys.argv[3]) / 100
            g2 = float(sys.argv[4]) / 100
            n = int(sys.argv[5])
            r = float(sys.argv[6]) / 100
            pm = float(sys.argv[7]) if len(sys.argv) > 7 else None
            vi = gordon_2estagios(d0, g1, g2, n, r)
            exibir_resultado('g2', "Gordon 2 Estagios", vi, d0, g1, r, pm,
                             extra={"g2 perpetuo": f"{g2*100:.1f}%"})
        elif cmd == "--h-model":
            d0 = float(sys.argv[2])
            g1 = float(sys.argv[3]) / 100
            g2 = float(sys.argv[4]) / 100
            n = int(sys.argv[5])
            r = float(sys.argv[6]) / 100
            pm = float(sys.argv[7]) if len(sys.argv) > 7 else None
            vi = h_model(d0, g1, g2, n, r)
            exibir_resultado('h', f"H-Model (g1={g1*100:.0f}% -> g2={g2*100:.0f}%, {n}a)",
                             vi, d0, g1, r, pm,
                             extra={"g2 terminal": f"{g2*100:.1f}%", "n": str(n)})
        elif cmd == "--dcf":
            fcf0 = float(sys.argv[2])
            g1 = float(sys.argv[3]) / 100
            g2 = float(sys.argv[4]) / 100
            n = int(sys.argv[5])
            wacc = float(sys.argv[6]) / 100
            divida = float(sys.argv[7])
            acoes = float(sys.argv[8])
            pm = float(sys.argv[9]) if len(sys.argv) > 9 else None
            ev = dcf_2estagios(fcf0, g1, g2, n, wacc)
            exibir_resultado_dcf(ev, divida, acoes, pm,
                                 label=f"DCF (g1={g1*100:.0f}%/{n}a -> g2={g2*100:.0f}%, WACC={wacc*100:.0f}%)",
                                 extra={"g1": f"{g1*100:.1f}%", "g2": f"{g2*100:.1f}%", "n": str(n), "WACC": f"{wacc*100:.1f}%"})
        elif cmd == "--graham":
            eps = float(sys.argv[2])
            bvps = float(sys.argv[3])
            pm = float(sys.argv[4]) if len(sys.argv) > 4 else None
            gn = graham_number(eps, bvps)
            print(f"\n--- Graham Number ---")
            print(f"  Graham Number = sqrt(22.5 * {eps:.2f} * {bvps:.2f})")
            print(f"                 = $ {fmt(gn)}")
            if gn is not None and pm and pm > 0:
                ms = margem_seguranca(gn, pm)
                if ms is not None:
                    status = "SUBVALORIZADA" if ms > 0 else "SOBREVALORIZADA"
                    print(f"  Margem de Seguranca:    {fmt(ms, 2)}% ({status})")
                print(f"  P/E atual:              {fmt(pm/eps, 2)} (Graham max: 15)")
                print(f"  P/B atual:              {fmt(pm/bvps, 2)} (Graham max: 1.5)")
        elif cmd == "--oe":
            lucro = float(sys.argv[2])
            da = float(sys.argv[3])
            capex = float(sys.argv[4])
            r = float(sys.argv[5]) / 100
            g = float(sys.argv[6]) / 100 if len(sys.argv) > 6 else 0
            pm = float(sys.argv[7]) if len(sys.argv) > 7 else None
            oe = owner_earnings(lucro, da, capex)
            vi = oe_valuation(oe, r, g)
            print(f"\n--- Owner Earnings ---")
            print(f"  OE = {lucro:.2f} + {da:.2f} - {capex:.2f} = $ {oe:.2f}")
            if vi is not None:
                print(f"  Valor Intrinseco (g={g*100:.1f}%, r={r*100:.1f}%): $ {fmt(vi)}")
            if pm and pm > 0 and vi is not None:
                ms = margem_seguranca(vi, pm)
                if ms is not None:
                    status = "SUBVALORIZADA" if ms > 0 else "SOBREVALORIZADA"
                    print(f"  Margem de Seguranca:    {fmt(ms, 2)}% ({status})")
                print(f"  Preco / OE (P/OE):      {fmt(pm/oe, 2)}")
        elif cmd == "--wacc":
            rf_c = float(sys.argv[2]) / 100
            beta_c = float(sys.argv[3])
            rm_c = float(sys.argv[4]) / 100
            eq_c = float(sys.argv[5])
            dv_c = float(sys.argv[6])
            rd_c = float(sys.argv[7]) / 100
            t_c = float(sys.argv[8]) / 100
            re_c = capm(rf_c, beta_c, rm_c)
            wacc_c = calcular_wacc(eq_c, dv_c, re_c, rd_c, t_c)
            print(f"\n--- CAPM ---")
            print(f"  Re = {rf_c*100:.2f}% + {beta_c:.2f} * ({rm_c*100:.0f}% - {rf_c*100:.2f}%)")
            print(f"     = {re_c*100:.2f}%")
            if wacc_c is not None:
                print(f"\n--- WACC ---")
                print(f"  WACC = {wacc_c*100:.2f}%")
        elif cmd == "--relativa":
            pm_r = float(sys.argv[2])
            pares_r = []
            i = 3
            while i + 2 < len(sys.argv):
                nome_r = sys.argv[i]
                fund_r = float(sys.argv[i+1])
                mult_r = float(sys.argv[i+2])
                pares_r.append((nome_r, fund_r, mult_r))
                i += 3
            if not pares_r:
                print("Uso: --relativa preco nome1 fund1 mult1 nome2 fund2 mult2 ...")
                return
            print(f"\n{'Multiplo':<20} {'Atual':>8} {'Setor':>8} {'Alvo':>8} {'Upside':>8}")
            print("-" * 56)
            alvos_r = []
            for nome, fund, mult_s in pares_r:
                mult_a = multiplo_atual(pm_r, fund)
                alvo = preco_alvo_multiplo(mult_s, fund)
                ups = upside_percent(alvo, pm_r)
                if alvo is not None:
                    alvos_r.append(alvo)
                print(f"{nome:<20} {fmt(mult_a,2):>8} {mult_s:>8.1f}x ${fmt(alvo,2):>8} {fmt(ups,1):>8}%")
            if alvos_r:
                media_alvo = sum(alvos_r) / len(alvos_r)
                ups_media = upside_percent(media_alvo, pm_r)
                print(f"\n  >>> Media dos alvos: $ {fmt(media_alvo,2)} ({ups_media:+.1f}%)")
        elif cmd == "--pbv":
            bvps = float(sys.argv[2])
            roe = float(sys.argv[3]) / 100
            r = float(sys.argv[4]) / 100
            g = float(sys.argv[5]) / 100 if len(sys.argv) > 5 else 0
            pm = float(sys.argv[6]) if len(sys.argv) > 6 else None
            vi = pbv_roe(bvps, roe, r, g)
            exibir_resultado('pbv', f"P/B x ROE", vi, bvps * roe, g, r, pm,
                             extra={"BVPS": f"${bvps:.2f}", "ROE": f"{roe*100:.1f}%"})
        elif cmd == "--ticker":
            ticker_sym = sys.argv[2]
            analisar_empresa_ticker(ticker_sym)
        elif cmd == "--bac":
            analisar_bac()
        else:
            print("Uso:")
            print("  python calculadora_gordon.py --ticker AAPL")
            print("  python calculadora_gordon.py --bac")
            print("  python calculadora_gordon.py --quick D0 g% r% [preco]")
            print("  python calculadora_gordon.py --two-stage D0 g1% g2% n r% [preco]")
            print("  python calculadora_gordon.py --h-model D0 g1% g2% n r% [preco]")
            print("  python calculadora_gordon.py --dcf FCF0 g1% g2% n WACC% divida acoes [preco]")
            print("  python calculadora_gordon.py --graham EPS BVPS [preco]")
            print("  python calculadora_gordon.py --oe lucro DA capex r% [g%] [preco]")
            print("  python calculadora_gordon.py --wacc RF% beta RM% equity divida Rd% T%")
            print("  python calculadora_gordon.py --relativa preco nome fund mult [nome fund mult ...]")
            print("  python calculadora_gordon.py --pbv BVPS ROE% r% [g%] [preco]")
    else:
        modo_interativo()


if __name__ == "__main__":
    main()
