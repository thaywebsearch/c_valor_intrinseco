import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calculadora_gordon import (
    gordon_1estagio, gordon_2estagios, pbv_roe, h_model,
    dcf_2estagios, graham_number,
    owner_earnings, oe_valuation, capm, calcular_wacc,
    multiplo_atual, preco_alvo_multiplo, upside_percent,
    margem_seguranca
)
import ticker_search

@st.cache_data(ttl=3600)
def _buscar_empresa_cache(ticker):
    return ticker_search.buscar_empresa(ticker)


st.set_page_config(page_title="Calculadora de Valor Intrínseco", layout="wide")

if "sp500_ticker" not in st.session_state:
    st.session_state.sp500_ticker = None
if "sp500_dados" not in st.session_state:
    st.session_state.sp500_dados = None

st.title("Calculadora de Valor Intrínseco")
st.markdown("Gordon, P/B×ROE, H-Model, DCF, Graham, Owner Earnings, CAPM/WACC, Relativa e Busca por Ticker")

preco_mercado = 51.80

tab_buscar, tab_g1, tab_g2, tab_pbv, tab_h, tab_dcf, tab_graham, tab_oe, tab_wacc, tab_rel, tab_conc, tab_sp500 = \
    st.tabs(["Buscar Ticker", "Gordon 1", "Gordon 2", "P/B × ROE", "H-Model",
             "DCF", "Graham", "Owner Earnings", "CAPM/WACC", "Relativa", "Conclusão", "S&P 500"])

def sensibilidade_heatmap(df, titulo):
    df_long = df.melt(id_vars=["g"], var_name="r", value_name="VI")
    df_long = df_long[df_long["VI"].notna() & (df_long["VI"] != "N/A")]
    df_long["VI"] = pd.to_numeric(df_long["VI"], errors="coerce")
    if df_long.empty:
        return None
    chart = alt.Chart(df_long).mark_rect().encode(
        x=alt.X("r:O", title="r (%)", sort=None),
        y=alt.Y("g:O", title="g (%)", sort=None),
        color=alt.Color("VI:Q", title="VI ($)",
                        scale=alt.Scale(scheme="redyellowgreen")),
        tooltip=["g", "r", alt.Tooltip("VI:Q", format=".2f")]
    ).properties(width=500, height=400, title=titulo)
    return chart


def tabela_sensibilidade_modelo(func, faixa_g, faixa_r, **kwargs):
    linhas = []
    for gx in faixa_g:
        linha = {"g": f"{gx*100:.1f}%"}
        for rx in faixa_r:
            v = func(gx, rx, **kwargs)
            linha[f"{rx*100:.1f}%"] = round(v, 2) if v is not None else None
        linhas.append(linha)
    return pd.DataFrame(linhas)

# ============ BUSCAR TICKER ============
with tab_buscar:
    st.subheader("Buscar Dados da Empresa")
    sp500_pendente = st.session_state.sp500_ticker
    if sp500_pendente:
        default_ticker = sp500_pendente
    else:
        default_ticker = "BAC"
    ticker_input = st.text_input("Ticker", value=default_ticker, key="busca_ticker")
    if st.button("Buscar", key="btn_buscar") or sp500_pendente:
        if sp500_pendente:
            st.session_state.sp500_ticker = None
        with st.spinner(f"Buscando dados de {ticker_input}..."):
            dados = _buscar_empresa_cache(ticker_input)
            if dados:
                st.success(f"**{dados['nome']}** ({dados['ticker']}) — {dados['moeda']}")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Preço", f"$ {dados['preco']:.2f}" if dados['preco'] else "N/A")
                col2.metric("Market Cap", ticker_search.formatar_valor(dados['market_cap']))
                col3.metric("P/E", f"{dados['pe']:.2f}x" if dados['pe'] else "N/A")
                col4.metric("P/B", f"{dados['pb']:.2f}x" if dados['pb'] else "N/A")

                st.markdown("---")
                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("EPS", f"$ {dados['eps']:.2f}" if dados['eps'] else "N/A")
                c2.metric("BVPS", f"$ {dados['bvps']:.2f}" if dados['bvps'] else "N/A")
                c3.metric("Div 12m", f"$ {dados['dividends_12m']:.2f}" if dados['dividends_12m'] else "N/A")
                c4.metric("ROE", f"{dados['roe']*100:.1f}%" if dados['roe'] else "N/A")
                c5.metric("Beta", f"{dados['beta']:.2f}" if dados['beta'] else "N/A")

                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("FCF/acao", f"$ {dados['fcf_per_share']:.2f}" if dados['fcf_per_share'] else "N/A")
                c2.metric("EBITDA/acao", f"$ {dados['ebitda_per_share']:.2f}" if dados['ebitda_per_share'] else "N/A")
                c3.metric("Receita/acao", f"$ {dados['receita_per_share']:.2f}" if dados['receita_per_share'] else "N/A")
                c4.metric("Div Yield", f"{dados['dividend_yield']*100:.2f}%" if dados['dividend_yield'] else "N/A")
                c5.metric("EV/EBITDA", f"{dados['ev_ebitda']:.2f}x" if dados['ev_ebitda'] else "N/A")

                re_est, wacc_est = ticker_search.calcular_wacc_estimado(dados)
                g_est = ticker_search.estimar_crescimento(dados)
                st.markdown("---")
                st.markdown("**Estimativas CAPM:**")
                mc1, mc2, mc3 = st.columns(3)
                mc1.metric("Re (CAPM)", f"{re_est*100:.2f}%" if re_est else "N/A")
                mc2.metric("WACC", f"{wacc_est*100:.2f}%" if wacc_est else "N/A")
                mc3.metric("g estimado", f"{g_est*100:.1f}%" if g_est else "N/A")

                if dados['preco'] and dados['preco'] > 0:
                    st.markdown("---")
                    st.markdown("**Valores Intrínsecos (com dados reais):**")
                    params = ticker_search.gerar_parametros_calculo(dados)
                    preco = params['preco']
                    eps = params['eps']
                    bvps = params['bvps']
                    d0 = params['d0']
                    g = params['g_estimado']
                    re = params['re_estimado']
                    roe = params['roe']
                    fcf_pa = params['fcf_per_share']
                    ebitda_pa = params['ebitda_per_share']
                    receita_pa = params['receita_per_share']
                    wacc_e = params['wacc_estimado']
                    div_liq = params['divida_liquida']
                    shares = params['shares']
                    fcf_tot = params['fcf_total']

                    res = {}
                    if d0 and re and re > g:
                        res["Gordon 1E"] = gordon_1estagio(d0, g, re)
                    if eps and bvps:
                        res["Graham"] = graham_number(eps, bvps)
                    if eps:
                        res["OE (g=0)"] = eps / re if re and re > 0 else None
                    if bvps and roe and re and re > 0:
                        res["P/B×ROE"] = pbv_roe(bvps, roe, re, 0)
                    if fcf_tot and shares and shares > 0 and wacc_e and wacc_e > 0:
                        ev = dcf_2estagios(fcf_tot, g, 0.025, 5, wacc_e)
                        if ev and div_liq:
                            res["DCF"] = (ev - div_liq) / shares
                    alvs_r = []
                    if eps:
                        alvs_r.append(preco_alvo_multiplo(13.0, eps))
                    if bvps:
                        alvs_r.append(preco_alvo_multiplo(1.10, bvps))
                    if ebitda_pa:
                        alvs_r.append(preco_alvo_multiplo(11.0, ebitda_pa))
                    if receita_pa:
                        alvs_r.append(preco_alvo_multiplo(2.80, receita_pa))
                    if fcf_pa:
                        alvs_r.append(preco_alvo_multiplo(12.0, fcf_pa))
                    alvs_v = [a for a in alvs_r if a]
                    if alvs_v:
                        res["Relativa"] = sum(alvs_v) / len(alvs_v)

                    df_res = pd.DataFrame([
                        {"Modelo": k, "VI": v, "Margem": f"{(v-preco)/v*100:+.1f}%" if v and v > 0 else "N/A"}
                        for k, v in res.items() if v
                    ])
                    if not df_res.empty:
                        df_plot = df_res.copy()
                        df_plot["Cor"] = df_plot["VI"].apply(lambda v: "Acima" if v > preco else "Abaixo")
                        chart = alt.Chart(df_plot).mark_bar().encode(
                            x=alt.X("Modelo:N", sort=None),
                            y=alt.Y("VI:Q", title="Valor Intrínseco ($)"),
                            color=alt.Color("Cor:N", scale=alt.Scale(domain=["Acima", "Abaixo"], range=["#2ecc71", "#e74c3c"])),
                            tooltip=["Modelo", alt.Tooltip("VI:Q", format=".2f")]
                        ).properties(height=350)
                        rule = alt.Chart(pd.DataFrame({"y": [preco]})).mark_rule(color="blue", strokeDash=[6, 3]).encode(y="y:Q")
                        st.altair_chart(chart + rule, use_container_width=True)
                        st.dataframe(df_res.style.apply(
                            lambda row: ["background: #d4edda" if row.get("Margem","").startswith("+") else
                                         "background: #f8d7da" if row.get("Margem","").startswith("-") else
                                         "" for _ in row], axis=1), hide_index=True)
                        vis = [v for v in res.values() if v]
                        if vis:
                            media = sum(vis) / len(vis)
                            ms_m = (media - preco) / media * 100 if media > 0 else 0
                            st.metric(f"Média {len(vis)} modelos", f"$ {media:.2f}", f"{ms_m:+.1f}%")
            else:
                st.error(f"Ticker '{ticker_input}' não encontrado. Verifique o símbolo.")

# ============ GORDON 1 ============
cols = tab_g1.columns(4)
with cols[0]:
    d0_g1 = tab_g1.number_input("D0 (dividendo anual)", value=1.12, step=0.01, format="%.2f", key="g1_d0")
with cols[1]:
    g_g1 = tab_g1.number_input("g (crescimento %)", value=7.0, step=0.5, format="%.1f", key="g1_g") / 100
with cols[2]:
    r_g1 = tab_g1.number_input("r (retorno exigido %)", value=10.0, step=0.5, format="%.1f", key="g1_r") / 100
if True:
    d0_g1 = 1.12
    g_g1 = 0.07
    r_g1 = 0.10
if tab_g1.button("Calcular", key="btn_g1"):
    vi = gordon_1estagio(d0_g1, g_g1, r_g1)
    if vi:
        ms = margem_seguranca(vi, preco_mercado)
        col1, col2, col3 = tab_g1.columns(3)
        col1.metric("Valor Intrínseco", f"$ {vi:.2f}")
        col2.metric("Margem de Segurança", f"{ms:+.1f}%" if ms else "N/A",
                    delta_color="normal" if ms and ms > 0 else ("inverse" if ms and ms < 0 else "off"))
        col3.metric("Preço de Mercado", f"$ {preco_mercado:.2f}")
        faixa_g = np.round(np.linspace(max(0, g_g1-0.04), min(0.15, g_g1+0.04), 9), 3)
        faixa_r = np.round(np.linspace(max(0.03, r_g1-0.04), min(0.20, r_g1+0.04), 9), 3)
        df = tabela_sensibilidade_modelo(lambda gx, rx: gordon_1estagio(d0_g1, gx, rx), faixa_g, faixa_r)
        chart = sensibilidade_heatmap(df, "Gordon 1 estágio - Sensibilidade")
        if chart:
            tab_g1.altair_chart(chart, use_container_width=True)
        tab_g1.dataframe(df.style.format(precision=2).background_gradient(cmap="RdYlGn", axis=None), hide_index=True)
    else:
        tab_g1.error("r deve ser maior que g")

# ============ GORDON 2 ============
cols = tab_g2.columns(5)
d0_g2 = cols[0].number_input("D0", value=1.12, step=0.01, format="%.2f", key="g2_d0")
g1_g2 = cols[1].number_input("g1 alto %", value=8.0, step=0.5, format="%.1f", key="g2_g1") / 100
n_g2 = cols[2].number_input("n anos", value=5, step=1, key="g2_n")
g2_g2 = cols[3].number_input("g2 terminal %", value=4.0, step=0.5, format="%.1f", key="g2_g2") / 100
r_g2 = cols[4].number_input("r %", value=10.0, step=0.5, format="%.1f", key="g2_r") / 100
if True:
    d0_g2 = 1.12
    g1_g2 = 0.08
    n_g2 = 5
    g2_g2 = 0.04
    r_g2 = 0.10
if tab_g2.button("Calcular", key="btn_g2"):
    vi = gordon_2estagios(d0_g2, g1_g2, g2_g2, n_g2, r_g2)
    if vi:
        ms = margem_seguranca(vi, preco_mercado)
        col1, col2, col3 = tab_g2.columns(3)
        col1.metric("Valor Intrínseco", f"$ {vi:.2f}")
        col2.metric("Margem de Segurança", f"{ms:+.1f}%" if ms else "N/A")
        col3.metric("Preço de Mercado", f"$ {preco_mercado:.2f}")
    else:
        tab_g2.error("r deve ser maior que g2")

# ============ P/B x ROE ============
cols = tab_pbv.columns(4)
bvps_pbv = cols[0].number_input("BVPS", value=38.66, step=0.1, format="%.2f", key="pbv_bvps")
roe_pbv = cols[1].number_input("ROE %", value=10.5, step=0.5, format="%.1f", key="pbv_roe") / 100
r_pbv = cols[2].number_input("r %", value=10.0, step=0.5, format="%.1f", key="pbv_r") / 100
g_pbv = cols[3].number_input("g % (0=EPV)", value=0.0, step=0.5, format="%.1f", key="pbv_g") / 100
if True:
    bvps_pbv = 38.66
    roe_pbv = 0.105
    r_pbv = 0.10
    g_pbv = 0.0
if tab_pbv.button("Calcular", key="btn_pbv"):
    vi = pbv_roe(bvps_pbv, roe_pbv, r_pbv, g_pbv)
    if vi:
        ms = margem_seguranca(vi, preco_mercado)
        col1, col2, col3 = tab_pbv.columns(3)
        col1.metric("Valor Intrínseco", f"$ {vi:.2f}")
        col2.metric("Margem de Segurança", f"{ms:+.1f}%" if ms else "N/A")
        col3.metric("Preço de Mercado", f"$ {preco_mercado:.2f}")
        faixa_g = np.round(np.linspace(max(0, g_pbv), min(0.10, g_pbv+0.04), 9), 3)
        faixa_r = np.round(np.linspace(max(0.03, r_pbv-0.04), min(0.20, r_pbv+0.04), 9), 3)
        df = tabela_sensibilidade_modelo(lambda gx, rx: pbv_roe(bvps_pbv, roe_pbv, rx, gx), faixa_g, faixa_r)
        chart = sensibilidade_heatmap(df, "P/B × ROE - Sensibilidade")
        if chart:
            tab_pbv.altair_chart(chart, use_container_width=True)
        tab_pbv.dataframe(df.style.format(precision=2).background_gradient(cmap="RdYlGn", axis=None), hide_index=True)
    else:
        tab_pbv.error("r deve ser maior que g")

# ============ H-MODEL ============
cols = tab_h.columns(5)
d0_h = cols[0].number_input("D0", value=1.12, step=0.01, format="%.2f", key="h_d0")
g1_h = cols[1].number_input("g1 inicial %", value=8.0, step=0.5, format="%.1f", key="h_g1") / 100
g2_h = cols[2].number_input("g2 terminal %", value=4.0, step=0.5, format="%.1f", key="h_g2") / 100
n_h = cols[3].number_input("n anos", value=5, step=1, key="h_n")
r_h = cols[4].number_input("r %", value=10.0, step=0.5, format="%.1f", key="h_r") / 100
if True:
    d0_h = 1.12
    g1_h = 0.08
    g2_h = 0.04
    n_h = 5
    r_h = 0.10
if tab_h.button("Calcular", key="btn_h"):
    vi = h_model(d0_h, g1_h, g2_h, n_h, r_h)
    if vi:
        ms = margem_seguranca(vi, preco_mercado)
        col1, col2, col3 = tab_h.columns(3)
        col1.metric("Valor Intrínseco", f"$ {vi:.2f}")
        col2.metric("Margem de Segurança", f"{ms:+.1f}%" if ms else "N/A")
        col3.metric("Preço de Mercado", f"$ {preco_mercado:.2f}")
        faixa_g = np.round(np.linspace(max(0, g2_h-0.03), min(0.10, g2_h+0.03), 9), 3)
        faixa_r = np.round(np.linspace(max(0.03, r_h-0.04), min(0.20, r_h+0.04), 9), 3)
        df = tabela_sensibilidade_modelo(lambda gx, rx: h_model(d0_h, g1_h, gx, n_h, rx), faixa_g, faixa_r)
        chart = sensibilidade_heatmap(df, "H-Model - Sensibilidade")
        if chart:
            tab_h.altair_chart(chart, use_container_width=True)
        tab_h.dataframe(df.style.format(precision=2).background_gradient(cmap="RdYlGn", axis=None), hide_index=True)
    else:
        tab_h.error("r deve ser maior que g2")

# ============ DCF ============
cols = tab_dcf.columns(4)
fcf0_dcf = cols[0].number_input("FCF0 (total, ex: 30 B = 30)", value=30.0, step=1.0, format="%.2f", key="dcf_fcf0")
g1_dcf = cols[1].number_input("g1 alto %", value=6.0, step=0.5, format="%.1f", key="dcf_g1") / 100
n_dcf = cols[2].number_input("n anos", value=5, step=1, key="dcf_n")
g2_dcf = cols[3].number_input("g2 terminal %", value=3.0, step=0.5, format="%.1f", key="dcf_g2") / 100
cols2 = tab_dcf.columns(4)
wacc_dcf = cols2[0].number_input("WACC %", value=10.0, step=0.5, format="%.1f", key="dcf_wacc") / 100
divida_dcf = cols2[1].number_input("Dívida Líquida (total)", value=5.0, step=1.0, format="%.2f", key="dcf_divida")
acoes_dcf = cols2[2].number_input("Ações (total)", value=7.8, step=0.1, format="%.2f", key="dcf_acoes")
if True:
    fcf0_dcf = 30.0
    g1_dcf = 0.06
    n_dcf = 5
    g2_dcf = 0.03
    wacc_dcf = 0.10
    divida_dcf = 5.0
    acoes_dcf = 7.8
if tab_dcf.button("Calcular", key="btn_dcf"):
    ev = dcf_2estagios(fcf0_dcf, g1_dcf, g2_dcf, n_dcf, wacc_dcf)
    if ev:
        vp = (ev - divida_dcf) / acoes_dcf
        ms = margem_seguranca(vp, preco_mercado)
        col1, col2, col3, col4 = tab_dcf.columns(4)
        col1.metric("Enterprise Value", f"$ {ev:.2f}")
        col2.metric("Valor / ação", f"$ {vp:.2f}")
        col3.metric("Margem de Segurança", f"{ms:+.1f}%" if ms else "N/A")
        col4.metric("Preço Mercado", f"$ {preco_mercado:.2f}")
        tab_dcf.info(f"EV - Dívida ({divida_dcf:.2f}) / Ações ({acoes_dcf:.2f}) = ${vp:.2f}")
        faixa_g = np.round(np.linspace(max(0, g2_dcf-0.03), min(0.10, g2_dcf+0.03), 9), 3)
        faixa_r = np.round(np.linspace(max(0.03, wacc_dcf-0.04), min(0.20, wacc_dcf+0.04), 9), 3)
        df = tabela_sensibilidade_modelo(
            lambda gx, rx: ((dcf_2estagios(fcf0_dcf, g1_dcf, gx, n_dcf, rx) or 0) - divida_dcf) / acoes_dcf,
            faixa_g, faixa_r)
        chart = sensibilidade_heatmap(df, "DCF - Sensibilidade ($/ação)")
        if chart:
            tab_dcf.altair_chart(chart, use_container_width=True)
        tab_dcf.dataframe(df.style.format(precision=2).background_gradient(cmap="RdYlGn", axis=None), hide_index=True)
    else:
        tab_dcf.error("WACC deve ser maior que g2")

# ============ GRAHAM ============
cols = tab_graham.columns(3)
eps_g = cols[0].number_input("EPS (lucro por ação)", value=3.46, step=0.01, format="%.2f", key="graham_eps")
bvps_g = cols[1].number_input("BVPS (book value)", value=38.66, step=0.01, format="%.2f", key="graham_bvps")
if True:
    eps_g = 3.46
    bvps_g = 38.66
if tab_graham.button("Calcular", key="btn_graham"):
    gn = graham_number(eps_g, bvps_g)
    if gn:
        ms = margem_seguranca(gn, preco_mercado)
        col1, col2, col3 = tab_graham.columns(3)
        col1.metric("Graham Number", f"$ {gn:.2f}")
        col2.metric("Margem de Segurança", f"{ms:+.1f}%" if ms else "N/A")
        col3.metric("Preço Mercado", f"$ {preco_mercado:.2f}")
        tab_graham.markdown(f"""
| Indicador | Atual | Graham (max) |
|---|---|---|
| P/E | {preco_mercado/eps_g:.2f} | 15 |
| P/B | {preco_mercado/bvps_g:.2f} | 1.5 |
""")
        status = "✅ SUBVALORIZADA" if ms and ms > 0 else "❌ SOBREVALORIZADA"
        tab_graham.success(f"**{status}** | Graham Number = √(22.5 × {eps_g:.2f} × {bvps_g:.2f}) = ${gn:.2f}")
    else:
        tab_graham.error("EPS e BVPS devem ser positivos")

# ============ OWNER EARNINGS ============
cols = tab_oe.columns(4)
oe_lucro = cols[0].number_input("Lucro Líquido / ação", value=3.46, step=0.01, format="%.2f", key="oe_lucro")
oe_da = cols[1].number_input("D&A / ação", value=0.50, step=0.01, format="%.2f", key="oe_da")
oe_capex = cols[2].number_input("Capex Manut. / ação", value=0.30, step=0.01, format="%.2f", key="oe_capex")
r_oe = cols[3].number_input("r %", value=10.0, step=0.5, format="%.1f", key="oe_r") / 100
cols2_oe = tab_oe.columns(2)
g_oe = cols2_oe[0].number_input("g % (0=EPV)", value=3.0, step=0.5, format="%.1f", key="oe_g") / 100
if True:
    oe_lucro = 3.46
    oe_da = 0.50
    oe_capex = 0.30
    r_oe = 0.10
    g_oe = 0.03
if tab_oe.button("Calcular", key="btn_oe"):
    oe = owner_earnings(oe_lucro, oe_da, oe_capex)
    vi = oe_valuation(oe, r_oe, g_oe)
    if vi:
        ms = margem_seguranca(vi, preco_mercado)
        col1, col2, col3, col4 = tab_oe.columns(4)
        col1.metric("Owner Earnings", f"$ {oe:.2f}")
        col2.metric("Valor Intrínseco", f"$ {vi:.2f}")
        col3.metric("Margem de Segurança", f"{ms:+.1f}%" if ms else "N/A")
        col4.metric("Preço Mercado", f"$ {preco_mercado:.2f}")
        tab_oe.info(f"OE = {oe_lucro:.2f} + {oe_da:.2f} - {oe_capex:.2f} = ${oe:.2f}")
        faixa_g = np.round(np.linspace(max(0, g_oe-0.03), min(0.10, g_oe+0.03), 9), 3)
        faixa_r = np.round(np.linspace(max(0.03, r_oe-0.04), min(0.20, r_oe+0.04), 9), 3)
        df = tabela_sensibilidade_modelo(lambda gx, rx: oe_valuation(oe, rx, gx), faixa_g, faixa_r)
        chart = sensibilidade_heatmap(df, "Owner Earnings - Sensibilidade")
        if chart:
            tab_oe.altair_chart(chart, use_container_width=True)
        tab_oe.dataframe(df.style.format(precision=2).background_gradient(cmap="RdYlGn", axis=None), hide_index=True)
    else:
        tab_oe.error("r deve ser maior que g")

# ============ CAPM / WACC ============
cols = tab_wacc.columns(4)
rf_w = cols[0].number_input("RF (T 10y %)", value=4.25, step=0.1, format="%.2f", key="wacc_rf") / 100
beta_w = cols[1].number_input("Beta", value=1.35, step=0.01, format="%.2f", key="wacc_beta")
rm_w = cols[2].number_input("RM (mercado %)", value=10.0, step=0.5, format="%.1f", key="wacc_rm") / 100
cols2_w = tab_wacc.columns(4)
eq_w = cols2_w[0].number_input("Equity (E)", value=340.0, step=10.0, format="%.1f", key="wacc_eq")
dv_w = cols2_w[1].number_input("Dívida (D)", value=280.0, step=10.0, format="%.1f", key="wacc_dv")
rd_w = cols2_w[2].number_input("Rd (custo dívida %)", value=4.5, step=0.1, format="%.1f", key="wacc_rd") / 100
t_w = cols2_w[3].number_input("T (IR %)", value=21.0, step=1.0, format="%.0f", key="wacc_t") / 100
if True:
    rf_w = 0.0425
    beta_w = 1.35
    rm_w = 0.10
    eq_w = 340.0
    dv_w = 280.0
    rd_w = 0.045
    t_w = 0.21
if tab_wacc.button("Calcular", key="btn_wacc"):
    re_w = capm(rf_w, beta_w, rm_w)
    wacc_w = calcular_wacc(eq_w, dv_w, re_w, rd_w, t_w)
    col1, col2, col3 = tab_wacc.columns(3)
    col1.metric("Re (CAPM)", f"{re_w*100:.2f}%")
    if wacc_w:
        col2.metric("WACC", f"{wacc_w*100:.2f}%")
        v = eq_w + dv_w
        tab_wacc.markdown(f"""
| Componente | Valor | Peso | Custo | Contribuição |
|---|---|---|---|---|
| Equity | $ {eq_w:.1f} | {eq_w/v*100:.1f}% | {re_w*100:.2f}% | {eq_w/v*re_w*100:.2f}% |
| Dívida | $ {dv_w:.1f} | {dv_w/v*100:.1f}% | {rd_w*100:.1f}% × (1-{t_w*100:.0f}%) = {rd_w*(1-t_w)*100:.2f}% | {dv_w/v*rd_w*(1-t_w)*100:.2f}% |
| **Total** | **$ {v:.1f}** | **100%** | | **{wacc_w*100:.2f}%** |
""")
        tab_wacc.success(f"**WACC = {wacc_w*100:.2f}%**")
    else:
        tab_wacc.error("Verifique os valores de Equity e Dívida")

# ============ RELATIVA ============
tab_rel.subheader("Múltiplos da Empresa vs. Setor")
cols = tab_rel.columns(2)
fator_nome = cols[0].text_input("Nome do múltiplo (ex: P/E)", value="P/E", key="rel_nome")
fator_fund = cols[1].number_input("Valor fundamental", value=3.46, step=0.01, format="%.2f", key="rel_fund")
cols2 = tab_rel.columns(3)
fator_mult_setor = cols2[0].number_input("Múltiplo setorial", value=13.0, step=0.5, format="%.1f", key="rel_mult")
fator_pm = cols2[1].number_input("Preço mercado", value=preco_mercado, step=1.0, format="%.2f", key="rel_pm")
if True:
    fator_fund = 3.46
    fator_mult_setor = 13.0
    fator_nome = "P/E"
if tab_rel.button("Calcular", key="btn_rel"):
    mult_a = multiplo_atual(fator_pm, fator_fund)
    alvo = preco_alvo_multiplo(fator_mult_setor, fator_fund)
    ups = upside_percent(alvo, fator_pm)
    col1, col2, col3, col4 = tab_rel.columns(4)
    col1.metric(f"{fator_nome} Atual", f"{mult_a:.2f}x" if mult_a else "N/A")
    col2.metric(f"{fator_nome} Setor", f"{fator_mult_setor:.1f}x")
    col3.metric("Preço Alvo", f"$ {alvo:.2f}" if alvo else "N/A")
    col4.metric("Upside", f"{ups:+.1f}%" if ups else "N/A",
                delta_color="normal" if ups and ups > 0 else ("inverse" if ups and ups < 0 else "off"))
tab_rel.markdown("---")
tab_rel.subheader("BAC vs. Setor (múltiplos pré-definidos)")
if tab_rel.button("Calcular BAC múltiplos", key="btn_rel_bac") or True:
    bac_mult = {
        "P/E":       {"fund": 3.46, "setor": 13.0},
        "P/B":       {"fund": 38.66, "setor": 1.10},
        "EV/EBITDA": {"fund": 5.13, "setor": 11.0},
        "P/S":       {"fund": 12.82, "setor": 2.80},
        "P/FCF":     {"fund": 3.85, "setor": 12.0},
    }
    linhas = []
    for nome, d in bac_mult.items():
        mult_a = multiplo_atual(preco_mercado, d["fund"])
        alvo = preco_alvo_multiplo(d["setor"], d["fund"])
        ups = upside_percent(alvo, preco_mercado)
        linhas.append({"Múltiplo": nome, "Atual": f"{mult_a:.2f}x" if mult_a else "N/A",
                       "Setor": f"{d['setor']:.1f}x", "Alvo": f"$ {alvo:.2f}" if alvo else "N/A",
                       "Upside": f"{ups:+.1f}%" if ups else "N/A"})
    df_rel = pd.DataFrame(linhas)
    tab_rel.dataframe(df_rel.style.apply(
        lambda row: ["background: #d4edda" if row.get("Upside","").startswith("+") else
                     "background: #f8d7da" if row.get("Upside","").startswith("-") else
                     "" for _ in row], axis=1), hide_index=True)
    alvos_val = [preco_alvo_multiplo(d["setor"], d["fund"]) for d in bac_mult.values()]
    alvos_val = [a for a in alvos_val if a]
    if alvos_val:
        media_rel = sum(alvos_val) / len(alvos_val)
        ups_rel = upside_percent(media_rel, preco_mercado)
        tab_rel.metric("Média dos Alvos", f"$ {media_rel:.2f}", f"{ups_rel:+.1f}%" if ups_rel else None)

# ============ CONCLUSÃO ============
tab_conv = tab_conc
if tab_conv.button("Calcular todos os modelos", key="btn_conc") or True:
    d0 = 1.12
    bvps = 38.66
    roe = 0.105
    r = 0.10
    g = 0.07
    g1 = 0.08
    g2 = 0.04
    n = 5
    fcf0 = 30.0
    divida = 5.0
    acoes = 7.8
    wacc = 0.10
    dcf_g1 = 0.06
    dcf_g2 = 0.03
    dcf_n = 5
    eps = 3.46
    oe_l = 3.46
    oe_d = 0.50
    oe_c = 0.30
    oe_g = 0.03

    resultados = {
        "Gordon 1 estágio": gordon_1estagio(d0, g, r),
        "Gordon 2 estágios": gordon_2estagios(d0, g1, g2, n, r),
        "P/B × ROE": pbv_roe(bvps, roe, r, 0),
        "H-Model": h_model(d0, g1, g2, n, r),
    }
    ev_dcf = dcf_2estagios(fcf0, dcf_g1, dcf_g2, dcf_n, wacc)
    resultados["DCF"] = (ev_dcf - divida) / acoes if ev_dcf else None
    resultados["Graham Number"] = graham_number(eps, bvps)
    oe = owner_earnings(oe_l, oe_d, oe_c)
    resultados["Owner Earnings"] = oe_valuation(oe, r, oe_g)
    rel_mult = {"P/E": 13.0, "P/B": 1.10, "EV/EBITDA": 11.0, "P/S": 2.80, "P/FCF": 12.0}
    rel_fund = {"P/E": 3.46, "P/B": 38.66, "EV/EBITDA": 5.13, "P/S": 12.82, "P/FCF": 3.85}
    rel_alvos = [preco_alvo_multiplo(rel_mult[k], rel_fund[k]) for k in rel_mult]
    rel_alvos_v = [a for a in rel_alvos if a is not None]
    resultados["Relativa"] = sum(rel_alvos_v) / len(rel_alvos_v) if rel_alvos_v else None

    df_conc = pd.DataFrame([
        {"Modelo": nome, "VI": vi,
         "Margem": f"{margem_seguranca(vi, preco_mercado):+.1f}%" if vi else "N/A"}
        for nome, vi in resultados.items()
    ])
    df_plot = df_conc.dropna(subset=["VI"]).copy()
    if not df_plot.empty:
        df_plot["Cor"] = df_plot["VI"].apply(
            lambda v: "Acima" if v > preco_mercado else "Abaixo")
        chart = alt.Chart(df_plot).mark_bar().encode(
            x=alt.X("Modelo:N", sort=None),
            y=alt.Y("VI:Q", title="Valor Intrínseco ($)"),
            color=alt.Color("Cor:N", scale=alt.Scale(
                domain=["Acima", "Abaixo"],
                range=["#2ecc71", "#e74c3c"])),
            tooltip=["Modelo", alt.Tooltip("VI:Q", format=".2f")]
        ).properties(height=400, title="Comparação dos Modelos")
        rule = alt.Chart(pd.DataFrame({"y": [preco_mercado]})).mark_rule(
            color="blue", strokeDash=[6, 3]).encode(y="y:Q")
        tab_conv.altair_chart(chart + rule, use_container_width=True)

    tab_conv.dataframe(df_conc.style.apply(
        lambda row: ["background: #d4edda" if row.get("Margem","").startswith("+") else
                     "background: #f8d7da" if row.get("Margem","").startswith("-") else
                     "" for _ in row], axis=1), hide_index=True)

    vis_validos = [v for v in resultados.values() if v is not None]
    if vis_validos:
        media = sum(vis_validos) / len(vis_validos)
        ms_media = margem_seguranca(media, preco_mercado)
        if ms_media and ms_media > 15:
            rec = "SUBVALORIZADA - COMPRA"
        elif ms_media and ms_media > 0:
            rec = "LIGEIRAMENTE SUBVALORIZADA - MANTER/ACUMULAR"
        elif ms_media and ms_media > -15:
            rec = "PRÓXIMA DO JUSTO - MANTER"
        else:
            rec = "SOBREVALORIZADA - AGUARDAR"
        tab_conv.metric(f"Média de {len(vis_validos)} modelos", f"$ {media:.2f}",
                       f"{ms_media:+.1f}%" if ms_media else None)
        tab_conv.success(f"**Recomendação: {rec}**")

# ============ S&P 500 ============
with tab_sp500:
    st.subheader("S&P 500 - Lista de Empresas")
    import sp500
    tickers_sp = sp500.listar_sp500()
    st.info(f"{len(tickers_sp)} empresas disponiveis")
    busca_sp = st.text_input("Buscar ticker (ex: AAPL, MS)", key="sp500_busca")
    if busca_sp:
        resultados_sp = sp500.buscar_sp500_por_nome(busca_sp)
    else:
        resultados_sp = tickers_sp
    if resultados_sp:
        st.write(f"**{len(resultados_sp)}** resultados")
        cols_per_row = 6
        visiveis = resultados_sp[:120]
        rows = [visiveis[i:i+cols_per_row] for i in range(0, len(visiveis), cols_per_row)]
        for row in rows:
            cols = st.columns(cols_per_row)
            for i, t in enumerate(row):
                if cols[i].button(t, key=f"sp_{t}"):
                    from ticker_search import executar_analise_completa
                    with st.spinner(f"A carregar {t}..."):
                        res = executar_analise_completa(t)
                        if res:
                            dados, params = res
                            st.session_state.sp500_ticker = t
                            st.session_state.sp500_dados = (dados, params)
                            st.success(f"**{t}** carregado! Vá a outros tabs para calcular.")
                        else:
                            st.error(f"Nao foi possivel carregar {t}")
        if len(resultados_sp) > 120:
            st.caption(f"... e mais {len(resultados_sp) - 120} tickers")
