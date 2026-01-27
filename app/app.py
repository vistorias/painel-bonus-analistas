# -*- coding: utf-8 -*-
# ============================================================
# Painel de Bônus Trimestral (T1) | ANALISTAS
# Sidebar REAL (coluna à esquerda) com toggle estável
# ============================================================

import streamlit as st
import pandas as pd
import json
from pathlib import Path
import unicodedata, re

# ===================== CONFIG =====================
st.set_page_config(page_title="Painel de Bônus (T1) | Analistas", layout="wide")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# ===================== ESTADO (SIDEBAR ABERTA/FECHADA) =====================
if "sb_open" not in st.session_state:
    st.session_state.sb_open = True

def toggle_sidebar():
    st.session_state.sb_open = not st.session_state.sb_open

# ===================== ESTILO (UI) =====================
st.markdown(
    """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

.block-container { padding-top: 1.1rem; padding-bottom: 2rem; max-width: 1400px; }
h1,h2,h3 { letter-spacing:-0.02em; }

:root{
  --sb-bg: #0b1220;
  --sb-fg: #e5e7eb;
  --sb-muted: rgba(229,231,235,.70);
  --card-border: rgba(15,23,42,.10);
  --shadow: 0 10px 28px rgba(15,23,42,.06);
}

/* “Sidebar” como coluna (estilização) */
.sidebar-wrap{
  background: var(--sb-bg);
  color: var(--sb-fg);
  border-radius: 18px;
  padding: 14px 12px;
  border: 1px solid rgba(255,255,255,.08);
  box-shadow: 0 12px 34px rgba(0,0,0,.22);
  position: sticky;
  top: 10px;
}

/* títulos e divisores */
.sb-brand{ display:flex; gap:10px; align-items:center; margin-top: 8px; }
.sb-logo{
  width: 42px; height: 42px; border-radius: 12px;
  background: rgba(255,255,255,.08);
  display:flex; align-items:center; justify-content:center;
  font-weight: 900; font-size: 16px;
  border: 1px solid rgba(255,255,255,.10);
}
.sb-title{ font-weight: 950; font-size: 1.02rem; line-height: 1.1; }
.sb-sub{ color: var(--sb-muted); font-size: .80rem; margin-top: 2px; }
.sb-menu-title{ font-size: .70rem; letter-spacing:.10em; opacity:.75; font-weight: 900; margin: 16px 0 10px 0; }
.sb-divider{ height:1px; background: rgba(255,255,255,.10); margin: 14px 0; }

/* Pills menu */
.sb-pill{
  border: 1px solid rgba(255,255,255,.10);
  background: rgba(255,255,255,.06);
  padding: 10px 12px;
  border-radius: 12px;
  font-weight: 850;
  margin-bottom: 8px;
}
.sb-pill.active{
  background: rgba(59,130,246,.22);
  border-color: rgba(59,130,246,.45);
}

/* Força labels/inputs claros no fundo escuro */
.sidebar-wrap label, .sidebar-wrap span, .sidebar-wrap p, .sidebar-wrap div {
  color: var(--sb-fg) !important;
}
.sidebar-wrap .stTextInput input,
.sidebar-wrap .stSelectbox div[data-baseweb="select"] > div{
  background: rgba(255,255,255,.06) !important;
  border: 1px solid rgba(255,255,255,.12) !important;
  color: var(--sb-fg) !important;
}
.sidebar-wrap .stRadio div[role="radiogroup"]{
  background: rgba(255,255,255,.03);
  border: 1px solid rgba(255,255,255,.08);
  padding: 10px 10px 2px 10px;
  border-radius: 14px;
}

/* Botão toggle */
.sb-toggle-btn button{
  width: 100%;
  border-radius: 12px !important;
  font-weight: 900 !important;
  border: 1px solid rgba(255,255,255,.14) !important;
  background: rgba(255,255,255,.08) !important;
  color: var(--sb-fg) !important;
}
.sb-toggle-btn button:hover{
  background: rgba(255,255,255,.12) !important;
}

/* Header */
.page-title { font-size: 1.7rem; font-weight: 950; line-height: 1.1; }
.page-sub { color: rgba(15,23,42,.60); font-size: .95rem; margin-top: 4px; }

/* KPI cards */
.kpi-row { display:flex; gap:14px; flex-wrap:wrap; margin: 10px 0 14px 0; }
.kpi{
  flex: 1 1 235px;
  border: 1px solid var(--card-border);
  background: #fff;
  border-radius: 14px;
  padding: 14px;
  box-shadow: 0 8px 24px rgba(15,23,42,.06);
}
.kpi-top{ display:flex; align-items:center; justify-content:space-between; gap:10px; }
.kpi-title{ font-size:.90rem; font-weight: 950; color: rgba(15,23,42,.72); }
.kpi-icon{
  width:38px; height:38px; border-radius:12px;
  display:flex; align-items:center; justify-content:center;
  font-size:18px; font-weight:950;
  border: 1px solid rgba(15,23,42,.08);
}
.kpi-icon.blue{ background: rgba(59,130,246,.14); color: rgba(59,130,246,1); }
.kpi-icon.green{ background: rgba(34,197,94,.14); color: rgba(34,197,94,1); }
.kpi-icon.amber{ background: rgba(245,158,11,.16); color: rgba(245,158,11,1); }
.kpi-icon.purple{ background: rgba(168,85,247,.14); color: rgba(168,85,247,1); }
.kpi-value{ font-size:1.55rem; font-weight: 950; margin-top:6px; }
.kpi-sub{ font-size:.85rem; color: rgba(15,23,42,.55); margin-top:2px; }

/* Section */
.section{
  border: 1px solid var(--card-border);
  background: #fff;
  border-radius: 16px;
  padding: 14px;
  box-shadow: 0 8px 24px rgba(15,23,42,.06);
}
.section-title{ font-weight:950; font-size:1.05rem; margin-bottom:10px; display:flex; gap:8px; align-items:center;
}

/* Cards */
.person-card{
  border:1px solid var(--card-border);
  background:#fff;
  border-radius:16px;
  padding:14px;
  box-shadow: var(--shadow);
  margin-bottom: 12px;
}
.person-name{ font-size:1.02rem; font-weight:950; margin:0; }
.person-meta{ margin:4px 0 10px 0; color: rgba(15,23,42,.70); font-weight:900; font-size:.90rem;}
.person-grid{ display:grid; grid-template-columns: 1fr 1fr; gap:10px; margin-top:8px; }
.pill{
  width:100%;
  display:flex; gap:8px; align-items:center; justify-content:space-between;
  background: rgba(15,23,42,.05);
  border:1px solid rgba(15,23,42,.08);
  padding:8px 10px;
  border-radius:999px;
  font-size:.82rem;
  font-weight:900;
  color: rgba(15,23,42,.78);
  box-sizing:border-box;
  white-space:nowrap;
  overflow:hidden;
  text-overflow:ellipsis;
}
.bar{ height:10px; background: rgba(15,23,42,.10); border-radius:999px; overflow:hidden; }
.bar>div{ height:100%; background:#0f172a; }
.muted{ color: rgba(15,23,42,.55); font-size:.86rem; }
.warn{ color:#b45309; font-weight:950; }
</style>
""",
    unsafe_allow_html=True,
)

# ===================== HELPERS =====================
def norm_txt(s: str) -> str:
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return ""
    s = str(s).strip().upper()
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = re.sub(r"\s+", " ", s)
    return s

def up(s):
    return norm_txt(s)

def texto_obs(valor):
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return ""
    s = str(valor).strip()
    return "" if s.lower() in ["none", "nan", ""] else s

def bool_safe(v, default=True) -> bool:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return default
    s = str(v).strip().lower()
    if s in ["true", "t", "1", "sim", "s", "yes", "y", "ok"]:
        return True
    if s in ["false", "f", "0", "nao", "não", "n", "no"]:
        return False
    try:
        return float(s) != 0
    except Exception:
        return default

def elegivel(valor_meta, obs):
    obs_u = up(obs)
    if pd.isna(valor_meta) or float(valor_meta) == 0:
        return False, "Sem elegibilidade no mês"
    if "LICEN" in obs_u:
        return False, "Licença no mês"
    return True, ""

def brl(x: float) -> str:
    try:
        return f"R$ {float(x):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"

def render_kpis(total_possivel, recebido, perda, qtd):
    st.markdown(
        f"""
    <div class="kpi-row">
      <div class="kpi">
        <div class="kpi-top">
          <div class="kpi-title">Total possível</div>
          <div class="kpi-icon blue">R$</div>
        </div>
        <div class="kpi-value">{brl(total_possivel)}</div>
        <div class="kpi-sub">Base filtrada</div>
      </div>

      <div class="kpi">
        <div class="kpi-top">
          <div class="kpi-title">Recebido</div>
          <div class="kpi-icon green">+</div>
        </div>
        <div class="kpi-value">{brl(recebido)}</div>
        <div class="kpi-sub">Somatório do período</div>
      </div>

      <div class="kpi">
        <div class="kpi-top">
          <div class="kpi-title">Deixou de ganhar</div>
          <div class="kpi-icon amber">!</div>
        </div>
        <div class="kpi-value">{brl(perda)}</div>
        <div class="kpi-sub">Perdas por metas</div>
      </div>

      <div class="kpi">
        <div class="kpi-top">
          <div class="kpi-title">Analistas</div>
          <div class="kpi-icon purple">👤</div>
        </div>
        <div class="kpi-value">{int(qtd)}</div>
        <div class="kpi-sub">Registros no filtro</div>
      </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

# ===================== ARQUIVOS ======================
def load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

PESOS_PATH = DATA_DIR / "pesos_analistas.json"
PLANILHA_PATH = DATA_DIR / "RESUMO PARA PAINEL - ANALISTAS.xlsx"

try:
    PESOS = load_json(PESOS_PATH)
except Exception as e:
    st.error(f"Erro ao carregar pesos: {e}\nArquivo esperado: {PESOS_PATH.name}")
    st.stop()

MESES = ["TRIMESTRE", "JANEIRO", "FEVEREIRO", "MARÇO"]

def ler_planilha(mes: str) -> pd.DataFrame:
    if PLANILHA_PATH.exists():
        return pd.read_excel(PLANILHA_PATH, sheet_name=mes)
    candidatos = list(DATA_DIR.glob("RESUMO PARA PAINEL - ANALISTAS*.xls*"))
    if not candidatos:
        st.error("Planilha não encontrada na pasta data/ (RESUMO PARA PAINEL - ANALISTAS.xlsx)")
        st.stop()
    return pd.read_excel(sorted(candidatos)[0], sheet_name=mes)

COLS_OBRIG = [
    "NOME", "FUNÇÃO", "VALOR MENSAL META",
    "BATEU_PRODUCAO", "BATEU_TMG_GERAL", "BATEU_TMA_ANALISTA", "BATEU_TEMPO_FILA", "BATEU_CONFORMIDADE"
]

def checar_colunas(df: pd.DataFrame, mes: str):
    faltando = [c for c in COLS_OBRIG if c not in df.columns]
    if faltando:
        st.error(f"Na aba {mes}, faltam colunas obrigatórias: {', '.join(faltando)}")
        st.stop()

def calcula_mes(df_mes: pd.DataFrame, nome_mes: str) -> pd.DataFrame:
    df = df_mes.copy()
    checar_colunas(df, nome_mes)

    def calcula_recebido(row):
        func = up(row.get("FUNÇÃO", ""))
        obs = row.get("OBSERVAÇÃO", "")
        valor_meta = row.get("VALOR MENSAL META", 0)

        if func != up("ANALISTA"):
            return pd.Series({
                "MES": nome_mes, "META": 0.0, "RECEBIDO": 0.0, "PERDA": 0.0, "%": 0.0,
                "_badge": "", "_obs": texto_obs(obs), "perdeu_itens": []
            })

        ok, motivo = elegivel(valor_meta, obs)
        perdeu_itens = []
        if not ok:
            return pd.Series({
                "MES": nome_mes, "META": 0.0, "RECEBIDO": 0.0, "PERDA": 0.0, "%": 0.0,
                "_badge": motivo, "_obs": texto_obs(obs), "perdeu_itens": perdeu_itens
            })

        metainfo = PESOS.get(up("ANALISTA"), {})
        itens = metainfo.get("metas", {})
        total_func = float(valor_meta if pd.notna(valor_meta) else 0.0)

        recebido, perdas = 0.0, 0.0

        for item, peso in itens.items():
            parcela = total_func * float(peso)
            item_norm = up(item)

            if item_norm in [up("PRODUÇÃO"), up("PRODUCAO")]:
                bateu = bool_safe(row.get("BATEU_PRODUCAO"), True)
                if bateu: recebido += parcela
                else:
                    perdas += parcela
                    perdeu_itens.append("Produção")
                continue

            if item_norm in [up("TEMPO MÉDIO GERAL DE ANÁLISE"), up("TEMPO MEDIO GERAL DE ANALISE")]:
                bateu = bool_safe(row.get("BATEU_TMG_GERAL"), True)
                if bateu: recebido += parcela
                else:
                    perdas += parcela
                    perdeu_itens.append("Tempo Médio Geral de Análise")
                continue

            if item_norm in [up("TEMPO MÉDIO DE ANÁLISE DO ANALISTA"), up("TEMPO MEDIO DE ANALISE DO ANALISTA")]:
                bateu = bool_safe(row.get("BATEU_TMA_ANALISTA"), True)
                if bateu: recebido += parcela
                else:
                    perdas += parcela
                    perdeu_itens.append("Tempo Médio de Análise do Analista")
                continue

            if item_norm in [up("TEMPO MÉDIO DA FILA"), up("TEMPO MEDIO DA FILA")]:
                bateu = bool_safe(row.get("BATEU_TEMPO_FILA"), True)
                if bateu: recebido += parcela
                else:
                    perdas += parcela
                    perdeu_itens.append("Tempo Médio da Fila")
                continue

            if item_norm == up("CONFORMIDADE"):
                bateu = bool_safe(row.get("BATEU_CONFORMIDADE"), True)
                if bateu: recebido += parcela
                else:
                    perdas += parcela
                    perdeu_itens.append("Conformidade")
                continue

            recebido += parcela

        meta = total_func
        perc = 0.0 if meta == 0 else (recebido / meta) * 100.0

        return pd.Series({
            "MES": nome_mes, "META": meta, "RECEBIDO": recebido, "PERDA": perdas,
            "%": perc, "_badge": "", "_obs": texto_obs(obs), "perdeu_itens": perdeu_itens
        })

    calc = df.apply(calcula_recebido, axis=1)
    out = pd.concat([df.reset_index(drop=True), calc], axis=1)
    out = out[out["FUNÇÃO"].astype(str).apply(up) == up("ANALISTA")].copy()
    return out

def montar_base(periodo: str) -> pd.DataFrame:
    if periodo == "TRIMESTRE":
        df_j, df_f, df_m = [ler_planilha(m) for m in ["JANEIRO", "FEVEREIRO", "MARÇO"]]
        full = pd.concat(
            [calcula_mes(df_j, "JANEIRO"), calcula_mes(df_f, "FEVEREIRO"), calcula_mes(df_m, "MARÇO")],
            ignore_index=True
        )

        group_cols = [c for c in ["CIDADE", "NOME", "FUNÇÃO", "DATA DE ADMISSÃO", "TEMPO DE CASA"] if c in full.columns]
        if not group_cols:
            group_cols = ["NOME", "FUNÇÃO"]

        agg = (full.groupby(group_cols, dropna=False)
               .agg({
                   "META":"sum",
                   "RECEBIDO":"sum",
                   "PERDA":"sum",
                   "_obs": lambda x: ", ".join(sorted({s for s in x if s})),
                   "_badge": lambda x: " / ".join(sorted({s for s in x if s}))
               })
               .reset_index())

        agg["%"] = agg.apply(lambda r: 0.0 if r["META"]==0 else (r["RECEBIDO"]/r["META"])*100.0, axis=1)

        perdas_pessoa = (
            full.assign(_lost=lambda d: d.apply(
                lambda r: [f"{it} ({r['MES']})" for it in r["perdeu_itens"]],
                axis=1
            ))
            .groupby(group_cols, dropna=False)["_lost"]
            .sum()
            .apply(lambda L: ", ".join(sorted(set(L))))
            .reset_index()
            .rename(columns={"_lost":"INDICADORES_NAO_ENTREGUES"})
        )

        out = agg.merge(perdas_pessoa, on=group_cols, how="left")
        out["INDICADORES_NAO_ENTREGUES"] = out["INDICADORES_NAO_ENTREGUES"].fillna("")
        return out

    df_mes = ler_planilha(periodo)
    out = calcula_mes(df_mes, periodo)
    out["INDICADORES_NAO_ENTREGUES"] = out["perdeu_itens"].apply(
        lambda L: ", ".join(L) if isinstance(L, list) and L else ""
    )
    return out

# ===================== LAYOUT PRINCIPAL: SIDEBAR (COLUNA) + CONTEÚDO =====================
if st.session_state.sb_open:
    col_sb, col_main = st.columns([0.27, 0.73], gap="large")
else:
    col_sb, col_main = st.columns([0.10, 0.90], gap="large")

# ===================== SIDEBAR =====================
with col_sb:
    st.markdown('<div class="sidebar-wrap">', unsafe_allow_html=True)

    st.markdown('<div class="sb-toggle-btn">', unsafe_allow_html=True)
    st.button("« Recolher" if st.session_state.sb_open else "» Abrir", on_click=toggle_sidebar)
    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.sb_open:
        st.markdown(
            """
<div class="sb-brand">
  <div class="sb-logo">📊</div>
  <div>
    <div class="sb-title">Painel Analistas</div>
    <div class="sb-sub">Bônus • T1</div>
  </div>
</div>

<div class="sb-menu-title">MENU PRINCIPAL</div>
<div class="sb-pill">Dashboard</div>
<div class="sb-pill active">Relatório</div>
<div class="sb-divider"></div>
<div class="sb-menu-title">FILTROS</div>
""",
            unsafe_allow_html=True,
        )

        filtro_mes = st.radio("Período", MESES, index=0, key="periodo")

        dados_calc = montar_base(filtro_mes)
        dados_calc = dados_calc[dados_calc["FUNÇÃO"].astype(str).apply(up) == up("ANALISTA")].copy()

        cidades = ["Todas"] + (sorted([c for c in dados_calc["CIDADE"].dropna().unique()]) if "CIDADE" in dados_calc.columns else [])
        tempos = ["Todos"] + (sorted([t for t in dados_calc["TEMPO DE CASA"].dropna().unique()]) if "TEMPO DE CASA" in dados_calc.columns else [])

        with st.form("filtros_form", clear_on_submit=False):
            filtro_nome = st.text_input("Buscar por nome", value=st.session_state.get("f_nome", ""))
            filtro_cidade = st.selectbox("Cidade", cidades, index=0)
            filtro_tempo = st.selectbox("Tempo de casa", tempos, index=0)
            aplicar = st.form_submit_button("Aplicar filtros")
        if aplicar:
            st.session_state["f_nome"] = filtro_nome

        st.markdown('<div class="sb-divider"></div>', unsafe_allow_html=True)
        st.markdown('<p style="margin:0;color:rgba(229,231,235,.7);font-weight:800;">Logado como</p>', unsafe_allow_html=True)
        st.markdown('<p style="margin:2px 0 0 0;font-weight:900;">analistas@brave</p>', unsafe_allow_html=True)

    else:
        # Sidebar recolhida: mantém só o período (opcional) e usa defaults
        filtro_mes = st.session_state.get("periodo", "TRIMESTRE")
        dados_calc = montar_base(filtro_mes)
        dados_calc = dados_calc[dados_calc["FUNÇÃO"].astype(str).apply(up) == up("ANALISTA")].copy()
        filtro_nome = st.session_state.get("f_nome", "")
        filtro_cidade = "Todas"
        filtro_tempo = "Todos"

    st.markdown('</div>', unsafe_allow_html=True)

# ===================== CONTEÚDO =====================
with col_main:
    dados_view = dados_calc.copy()

    if filtro_nome:
        dados_view = dados_view[dados_view["NOME"].astype(str).str.contains(filtro_nome, case=False, na=False)]
    if filtro_cidade != "Todas" and "CIDADE" in dados_view.columns:
        dados_view = dados_view[dados_view["CIDADE"] == filtro_cidade]
    if filtro_tempo != "Todos" and "TEMPO DE CASA" in dados_view.columns:
        dados_view = dados_view[dados_view["TEMPO DE CASA"] == filtro_tempo]

    dados_view = dados_view.sort_values(by="%", ascending=False)

    periodo_label = "Trimestre" if filtro_mes == "TRIMESTRE" else filtro_mes

    st.markdown(
        f"""
<div>
  <div class="page-title">Relatório de Bônus</div>
  <div class="page-sub">Visão consolidada de <b>{periodo_label}</b></div>
</div>
""",
        unsafe_allow_html=True,
    )

    total_possivel = float(dados_view["META"].sum()) if "META" in dados_view.columns else 0.0
    recebido = float(dados_view["RECEBIDO"].sum()) if "RECEBIDO" in dados_view.columns else 0.0
    perda = float(dados_view["PERDA"].sum()) if "PERDA" in dados_view.columns else 0.0
    qtd = len(dados_view)

    render_kpis(total_possivel, recebido, perda, qtd)

    left, right = st.columns([1.05, 1.25], gap="large")

    with left:
        st.markdown('<div class="section">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Resumo</div>', unsafe_allow_html=True)

        cumprimento_medio = 0.0 if total_possivel == 0 else (recebido / total_possivel) * 100.0
        resumo = pd.DataFrame(
            {"Item":["Total possível","Recebido","Deixou de ganhar","Cumprimento médio"],
             "Valor":[brl(total_possivel), brl(recebido), brl(perda), f"{cumprimento_medio:.1f}%"]}
        )
        st.dataframe(resumo, use_container_width=True, hide_index=True)

        top = dados_view.head(5).copy()
        cols_top = [c for c in ["NOME","CIDADE","%","RECEBIDO","PERDA"] if c in top.columns]
        top = top[cols_top]
        if "%" in top.columns: top["%"] = top["%"].apply(lambda x: f"{float(x):.1f}%")
        if "RECEBIDO" in top.columns: top["RECEBIDO"] = top["RECEBIDO"].apply(brl)
        if "PERDA" in top.columns: top["PERDA"] = top["PERDA"].apply(brl)
        if "CIDADE" in top.columns: top["CIDADE"] = top["CIDADE"].astype(str).str.title()

        st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Top 5</div>', unsafe_allow_html=True)
        st.dataframe(top, use_container_width=True, hide_index=True)

        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="section">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Analistas</div>', unsafe_allow_html=True)

        cols_cards = st.columns(2, gap="medium")
        for idx, (_, row) in enumerate(dados_view.iterrows()):
            pct = float(row.get("%", 0) or 0)
            meta = float(row.get("META", 0) or 0)
            rec = float(row.get("RECEBIDO", 0) or 0)
            per = float(row.get("PERDA", 0) or 0)

            nome = str(row.get("NOME", "")).title()
            cidade = str(row.get("CIDADE", "")).title() if "CIDADE" in dados_view.columns else ""
            tempo = str(row.get("TEMPO DE CASA", "")).strip() if "TEMPO DE CASA" in dados_view.columns else ""

            obs = texto_obs(row.get("_obs", row.get("OBSERVAÇÃO", "")))
            perdidos_txt = texto_obs(row.get("INDICADORES_NAO_ENTREGUES", ""))

            tag = "Excelente" if pct >= 95 else ("Atenção" if pct < 80 else "Ok")
            meta_line = f"Analista — {cidade}" if cidade else "Analista"
            if tempo: meta_line = f"{meta_line} • {tempo}"

            with cols_cards[idx % 2]:
                st.markdown(
                    f"""
<div class="person-card">
  <p class="person-name">{nome}</p>
  <div class="person-meta">{meta_line}</div>

  <div class="person-grid">
    <div class="pill"><span>Meta</span><b>{brl(meta)}</b></div>
    <div class="pill"><span>Recebido</span><b>{brl(rec)}</b></div>
    <div class="pill"><span>Perda</span><b>{brl(per)}</b></div>
    <div class="pill"><span>Cumprimento</span><b>{pct:.1f}%</b></div>
  </div>

  <div style="height:10px"></div>
  <div class="bar"><div style="width:{max(0,min(100,pct)):.1f}%"></div></div>

  <div style="height:10px"></div>
  <div class="muted"><b>Status:</b> {tag}</div>

  {"<div style='height:8px'></div><div class='muted'><span class='warn'>Indicadores não entregues:</span> "+perdidos_txt+"</div>" if perdidos_txt else ""}
  {"<div style='height:8px'></div><div class='muted'>Obs.: "+obs+"</div>" if obs else ""}
</div>
""",
                    unsafe_allow_html=True,
                )

        st.markdown('</div>', unsafe_allow_html=True)
