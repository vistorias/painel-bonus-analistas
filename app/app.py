# -*- coding: utf-8 -*-
# ============================================================
# Painel de Bônus Trimestral (T1) | ANALISTAS (individual por linha no Excel)
# Meses: JANEIRO, FEVEREIRO, MARÇO
# ============================================================

import streamlit as st
import pandas as pd
import json
from pathlib import Path
import unicodedata, re

# ===================== CONFIG BÁSICA =====================
st.set_page_config(page_title="Painel de Bônus | Analistas", layout="wide")
st.title("🧠 Painel de Bônus Trimestral | Analistas")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# ===================== HELPERS =====================
def norm_txt(s: str) -> str:
    """UPPER + remove acentos + colapsa espaços internos."""
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
    if pd.isna(valor):
        return ""
    s = str(valor).strip()
    return "" if s.lower() in ["none", "nan", ""] else s

def bool_safe(v, default=True) -> bool:
    """
    Converte TRUE/FALSE, SIM/NÃO, 1/0 (e variações) para bool.
    Se vazio/NaN: default.
    """
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return default
    s = str(v).strip().lower()

    if s in ["true", "t", "1", "sim", "s", "yes", "y", "ok"]:
        return True
    if s in ["false", "f", "0", "nao", "não", "n", "no"]:
        return False

    # tenta numérico
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

# ===================== CARREGAMENTO ======================
def load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# >>> Ajuste apenas se seus nomes de arquivos forem diferentes
PESOS_PATH = DATA_DIR / "pesos_analistas.json"
PLANILHA_PATH = DATA_DIR / "RESUMO PARA PAINEL - ANALISTAS.xlsx"

try:
    PESOS = load_json(PESOS_PATH)
except Exception as e:
    st.error(f"Erro ao carregar pesos: {e}\nArquivo esperado: {PESOS_PATH.name}")
    st.stop()

MESES = ["TRIMESTRE", "JANEIRO", "FEVEREIRO", "MARÇO"]
filtro_mes = st.radio("📅 Selecione o mês:", MESES, horizontal=True)

def ler_planilha(mes: str) -> pd.DataFrame:
    if PLANILHA_PATH.exists():
        return pd.read_excel(PLANILHA_PATH, sheet_name=mes)
    candidatos = list(DATA_DIR.glob("RESUMO PARA PAINEL - ANALISTAS*.xls*"))
    if not candidatos:
        st.error("Planilha não encontrada na pasta data/ (RESUMO PARA PAINEL - ANALISTAS.xlsx)")
        st.stop()
    return pd.read_excel(sorted(candidatos)[0], sheet_name=mes)

# ===================== VALIDAÇÃO DE COLUNAS =====================
COLS_OBRIG = [
    "NOME", "FUNÇÃO", "VALOR MENSAL META",
    "BATEU_PRODUCAO", "BATEU_TMG_GERAL", "BATEU_TMA_ANALISTA", "BATEU_TEMPO_FILA", "BATEU_CONFORMIDADE"
]
COLS_SUG = ["CIDADE", "DATA DE ADMISSÃO", "TEMPO DE CASA", "OBSERVAÇÃO"]

def checar_colunas(df: pd.DataFrame, mes: str):
    faltando = [c for c in COLS_OBRIG if c not in df.columns]
    if faltando:
        st.error(
            f"Na aba {mes}, faltam colunas obrigatórias: {', '.join(faltando)}.\n"
            f"Colunas encontradas: {', '.join(df.columns)}"
        )
        st.stop()

# ===================== CÁLCULO (POR MÊS) =====================
def calcula_mes(df_mes: pd.DataFrame, nome_mes: str) -> pd.DataFrame:
    df = df_mes.copy()

    # valida colunas
    checar_colunas(df, nome_mes)

    def calcula_recebido(row):
        func = up(row.get("FUNÇÃO", ""))
        nome = row.get("NOME", "")
        obs = row.get("OBSERVAÇÃO", "")
        valor_meta = row.get("VALOR MENSAL META", 0)

        # painel SOMENTE Analista
        if func != up("ANALISTA"):
            return pd.Series({
                "MES": nome_mes, "META": 0.0, "RECEBIDO": 0.0, "PERDA": 0.0, "%": 0.0,
                "_badge": "Função fora do painel", "_obs": texto_obs(obs), "perdeu_itens": []
            })

        ok, motivo = elegivel(valor_meta, obs)
        perdeu_itens = []

        if not ok:
            return pd.Series({
                "MES": nome_mes, "META": 0.0, "RECEBIDO": 0.0, "PERDA": 0.0, "%": 0.0,
                "_badge": motivo, "_obs": texto_obs(obs), "perdeu_itens": perdeu_itens
            })

        # pesos do analista
        metainfo = PESOS.get(up("ANALISTA"), {})
        itens = metainfo.get("metas", {})

        # meta vem do Excel
        total_func = float(valor_meta if pd.notna(valor_meta) else 0.0)

        recebido, perdas = 0.0, 0.0

        for item, peso in itens.items():
            parcela = total_func * float(peso)
            item_norm = up(item)

            # PRODUÇÃO (individual)
            if item_norm == up("PRODUÇÃO") or item_norm == up("PRODUCAO"):
                bateu = bool_safe(row.get("BATEU_PRODUCAO"), True)
                if bateu:
                    recebido += parcela
                else:
                    perdas += parcela
                    perdeu_itens.append("Produção")
                continue

            # TEMPO MÉDIO GERAL (marca)
            if item_norm == up("TEMPO MÉDIO GERAL DE ANÁLISE") or item_norm == up("TEMPO MEDIO GERAL DE ANALISE"):
                bateu = bool_safe(row.get("BATEU_TMG_GERAL"), True)
                if bateu:
                    recebido += parcela
                else:
                    perdas += parcela
                    perdeu_itens.append("Tempo Médio Geral de Análise")
                continue

            # TEMPO MÉDIO DO ANALISTA (individual)
            if item_norm == up("TEMPO MÉDIO DE ANÁLISE DO ANALISTA") or item_norm == up("TEMPO MEDIO DE ANALISE DO ANALISTA"):
                bateu = bool_safe(row.get("BATEU_TMA_ANALISTA"), True)
                if bateu:
                    recebido += parcela
                else:
                    perdas += parcela
                    perdeu_itens.append("Tempo Médio de Análise do Analista")
                continue

            # TEMPO MÉDIO DA FILA
            if item_norm == up("TEMPO MÉDIO DA FILA") or item_norm == up("TEMPO MEDIO DA FILA"):
                bateu = bool_safe(row.get("BATEU_TEMPO_FILA"), True)
                if bateu:
                    recebido += parcela
                else:
                    perdas += parcela
                    perdeu_itens.append("Tempo Médio da Fila")
                continue

            # CONFORMIDADE
            if item_norm == up("CONFORMIDADE"):
                bateu = bool_safe(row.get("BATEU_CONFORMIDADE"), True)
                if bateu:
                    recebido += parcela
                else:
                    perdas += parcela
                    perdeu_itens.append("Conformidade")
                continue

            # qualquer outra meta (se existir no JSON) -> considera batida
            recebido += parcela

        meta = total_func
        perc = 0.0 if meta == 0 else (recebido / meta) * 100.0

        return pd.Series({
            "MES": nome_mes, "META": meta, "RECEBIDO": recebido, "PERDA": perdas,
            "%": perc, "_badge": "", "_obs": texto_obs(obs), "perdeu_itens": perdeu_itens
        })

    calc = df.apply(calcula_recebido, axis=1)
    out = pd.concat([df.reset_index(drop=True), calc], axis=1)

    # remove tudo que não é analista (garantia extra)
    out = out[out["FUNÇÃO"].astype(str).apply(up) == up("ANALISTA")].copy()
    return out

# ===================== LEITURA (TRIMESTRE OU MÊS) =====================
if filtro_mes == "TRIMESTRE":
    try:
        df_j, df_f, df_m = [ler_planilha(m) for m in ["JANEIRO", "FEVEREIRO", "MARÇO"]]
        st.success("✅ Planilhas carregadas com sucesso: JANEIRO, FEVEREIRO e MARÇO!")
    except Exception as e:
        st.error(f"Erro ao ler a planilha: {e}")
        st.stop()

    dados_full = pd.concat([
        calcula_mes(df_j, "JANEIRO"),
        calcula_mes(df_f, "FEVEREIRO"),
        calcula_mes(df_m, "MARÇO")
    ], ignore_index=True)

    group_cols = []
    for c in ["CIDADE", "NOME", "FUNÇÃO", "DATA DE ADMISSÃO", "TEMPO DE CASA"]:
        if c in dados_full.columns:
            group_cols.append(c)

    if not group_cols:
        group_cols = ["NOME", "FUNÇÃO"]

    agg = (dados_full
           .groupby(group_cols, dropna=False)
           .agg({
               "META": "sum",
               "RECEBIDO": "sum",
               "PERDA": "sum",
               "_obs": lambda x: ", ".join(sorted({s for s in x if s})),
               "_badge": lambda x: " / ".join(sorted({s for s in x if s}))
           })
           .reset_index())

    agg["%"] = agg.apply(lambda r: 0.0 if r["META"] == 0 else (r["RECEBIDO"] / r["META"]) * 100.0, axis=1)

    perdas_pessoa = (
        dados_full.assign(_lost=lambda d: d.apply(
            lambda r: [f"{it} ({r['MES']})" for it in r["perdeu_itens"]],
            axis=1))
        .groupby(group_cols, dropna=False)["_lost"]
        .sum()
        .apply(lambda L: ", ".join(sorted(set(L))))
        .reset_index()
        .rename(columns={"_lost": "INDICADORES_NAO_ENTREGUES"})
    )

    dados_calc = agg.merge(perdas_pessoa, on=group_cols, how="left")
    dados_calc["INDICADORES_NAO_ENTREGUES"] = dados_calc["INDICADORES_NAO_ENTREGUES"].fillna("")
else:
    try:
        df_mes = ler_planilha(filtro_mes)
        st.success(f"✅ Planilha de {filtro_mes} carregada!")
    except Exception as e:
        st.error(f"Erro ao ler a planilha: {e}")
        st.stop()

    dados_calc = calcula_mes(df_mes, filtro_mes)
    dados_calc["INDICADORES_NAO_ENTREGUES"] = dados_calc["perdeu_itens"].apply(
        lambda L: ", ".join(L) if isinstance(L, list) and L else ""
    )

# garantia final: só analistas
dados_calc = dados_calc[dados_calc["FUNÇÃO"].astype(str).apply(up) == up("ANALISTA")].copy()

# ===================== FILTROS =====================
st.markdown("### 🔎 Filtros")
cols_f = st.columns(3)

with cols_f[0]:
    filtro_nome = st.text_input("Buscar por nome (contém)", "")

with cols_f[1]:
    if "CIDADE" in dados_calc.columns:
        cidades = ["Todas"] + sorted([c for c in dados_calc["CIDADE"].dropna().unique()])
        filtro_cidade = st.selectbox("Cidade", cidades)
    else:
        filtro_cidade = "Todas"

with cols_f[2]:
    if "TEMPO DE CASA" in dados_calc.columns:
        tempos = ["Todos"] + sorted([t for t in dados_calc["TEMPO DE CASA"].dropna().unique()])
        filtro_tempo = st.selectbox("Tempo de casa", tempos)
    else:
        filtro_tempo = "Todos"

dados_view = dados_calc.copy()
if filtro_nome:
    dados_view = dados_view[dados_view["NOME"].astype(str).str.contains(filtro_nome, case=False, na=False)]
if filtro_cidade != "Todas" and "CIDADE" in dados_view.columns:
    dados_view = dados_view[dados_view["CIDADE"] == filtro_cidade]
if filtro_tempo != "Todos" and "TEMPO DE CASA" in dados_view.columns:
    dados_view = dados_view[dados_view["TEMPO DE CASA"] == filtro_tempo]

# ===================== RESUMO =====================
st.markdown("### 📊 Resumo Geral")
colA, colB, colC = st.columns(3)
with colA:
    st.success(f"💰 Total possível: R$ {dados_view['META'].sum():,.2f}")
with colB:
    st.info(f"📈 Recebido: R$ {dados_view['RECEBIDO'].sum():,.2f}")
with colC:
    st.error(f"📉 Deixou de ganhar: R$ {dados_view['PERDA'].sum():,.2f}")

# ===================== CARDS =====================
st.markdown("### 👥 Analistas")
cols_cards = st.columns(3)

dados_view = dados_view.sort_values(by="%", ascending=False)

for i, row in dados_view.iterrows():
    pct = float(row["%"]) if pd.notna(row.get("%")) else 0.0
    meta = float(row["META"]) if pd.notna(row.get("META")) else 0.0
    recebido = float(row["RECEBIDO"]) if pd.notna(row.get("RECEBIDO")) else 0.0
    perdido = float(row["PERDA"]) if pd.notna(row.get("PERDA")) else 0.0

    badge = row.get("_badge", "")
    obs_txt = texto_obs(row.get("_obs", row.get("OBSERVAÇÃO", "")))
    perdidos_txt = texto_obs(row.get("INDICADORES_NAO_ENTREGUES", ""))

    bg = "#f9f9f9" if not badge else "#eeeeee"

    with cols_cards[list(dados_view.index).index(i) % 3]:
        cidade_txt = ""
        if "CIDADE" in row and pd.notna(row.get("CIDADE")) and str(row.get("CIDADE")).strip():
            cidade_txt = f" — {str(row.get('CIDADE')).title()}"

        st.markdown(f"""
        <div style="border:1px solid #ccc;padding:16px;border-radius:12px;margin-bottom:12px;background:{bg}">
            <h4 style="margin:0">{str(row.get('NOME','')).title()}</h4>
            <p style="margin:4px 0;"><strong>Analista</strong>{cidade_txt}</p>
            <p style="margin:4px 0;">
                <strong>Meta {'Trimestral' if filtro_mes=='TRIMESTRE' else 'Mensal'}:</strong> R$ {meta:,.2f}<br>
                <strong>Recebido:</strong> R$ {recebido:,.2f}<br>
                <strong>Deixou de ganhar:</strong> R$ {perdido:,.2f}<br>
                <strong>Cumprimento:</strong> {pct:.1f}%
            </p>
            <div style="height: 10px; background: #ddd; border-radius: 5px; overflow: hidden;">
                <div style="width: {max(0.0, min(100.0, pct)):.1f}%; background: black; height: 100%;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if badge:
            st.caption(f"⚠️ {badge}")
        if obs_txt:
            st.caption(f"🗒️ {obs_txt}")
        if perdidos_txt:
            st.caption(f"🔻 Indicadores não entregues: {perdidos_txt}")
