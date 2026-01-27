# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import json
from pathlib import Path
import unicodedata, re

# ===================== CONFIG BÁSICA =====================
st.set_page_config(page_title="Painel de Bônus (T4) | Analistas", layout="wide")
st.title("🧠 Painel de Bônus Trimestral (T4) | Analistas")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# ===================== HELPERS (TEXTO / % / VARIAÇÕES) =====================
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

def pct_safe(x):
    """Converte valor de % do Excel para fração (0-1). Aceita 0.035 ou 3.5."""
    try:
        x = float(x)
        if x > 1:
            return x / 100.0
        return x
    except Exception:
        return 0.0

def fmt_pct(x):
    try:
        return f"{float(x) * 100:.2f}%"
    except Exception:
        return "0.00%"

def elegivel(valor_meta, obs):
    obs_u = up(obs)
    if pd.isna(valor_meta) or float(valor_meta) == 0:
        return False, "Sem elegibilidade no mês"
    if "LICEN" in obs_u:
        return False, "Licença no mês"
    return True, ""

# ===================== CARREGAMENTO ======================
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# >>> AJUSTE AQUI: nomes dos arquivos dos ANALISTAS
PESOS_PATH = DATA_DIR / "pesos_analistas.json"
IND_PATH = DATA_DIR / "empresa_indicadores_analistas.json"
PLANILHA_PATH = DATA_DIR / "RESUMO PARA PAINEL - ANALISTAS.xlsx"

try:
    PESOS = load_json(PESOS_PATH)
    INDICADORES = load_json(IND_PATH)
except Exception as e:
    st.error(f"Erro ao carregar JSONs: {e}")
    st.stop()

MESES = ["TRIMESTRE", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"]
filtro_mes = st.radio("📅 Selecione o mês:", MESES, horizontal=True)

def ler_planilha(mes: str) -> pd.DataFrame:
    if PLANILHA_PATH.exists():
        return pd.read_excel(PLANILHA_PATH, sheet_name=mes)
    candidatos = list(DATA_DIR.glob("RESUMO PARA PAINEL - ANALISTAS*.xls*"))
    if not candidatos:
        st.error("Planilha não encontrada na pasta data/ (RESUMO PARA PAINEL - ANALISTAS.xlsx)")
        st.stop()
    return pd.read_excel(sorted(candidatos)[0], sheet_name=mes)

# ===================== CÁLCULO (POR MÊS) =====================
def calcula_mes(df_mes: pd.DataFrame, nome_mes: str) -> pd.DataFrame:
    ind_mes_raw = INDICADORES.get(nome_mes, {})
    ind_flags = {up(k): v for k, v in ind_mes_raw.items()}

    def flag(chave: str, default=True):
        return ind_flags.get(up(chave), default)

    df = df_mes.copy()

    def calcula_recebido(row):
        func = up(row.get("FUNÇÃO", ""))
        obs = row.get("OBSERVAÇÃO", "")
        valor_meta = row.get("VALOR MENSAL META", 0)

        # >>> painel somente analistas
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

        metainfo = PESOS.get(func, PESOS.get(row.get("FUNÇÃO", ""), {}))
        # IMPORTANTÍSSIMO: não use "total" no JSON, para não zerar a meta.
        total_func = float(valor_meta if pd.notna(valor_meta) else 0)
        itens = metainfo.get("metas", {})

        recebido, perdas = 0.0, 0.0

        for item, peso in itens.items():
            parcela = total_func * float(peso)
            item_norm = up(item)

            # --- PRODUÇÃO ---
            if item_norm == up("PRODUÇÃO"):
                if flag("producao", True):
                    recebido += parcela
                else:
                    perdas += parcela
                    perdeu_itens.append("Produção")
                continue

            # --- TEMPO MÉDIO GERAL ---
            if item_norm == up("TEMPO MÉDIO GERAL DE ANÁLISE"):
                if flag("tempo_medio_geral", True):
                    recebido += parcela
                else:
                    perdas += parcela
                    perdeu_itens.append("Tempo Médio Geral de Análise")
                continue

            # --- TEMPO MÉDIO DO ANALISTA ---
            if item_norm == up("TEMPO MÉDIO DE ANÁLISE DO ANALISTA"):
                if flag("tempo_medio_analista", True):
                    recebido += parcela
                else:
                    perdas += parcela
                    perdeu_itens.append("Tempo Médio de Análise do Analista")
                continue

            # --- TEMPO MÉDIO DA FILA ---
            if item_norm == up("TEMPO MÉDIO DA FILA"):
                if flag("tempo_medio_fila", True):
                    recebido += parcela
                else:
                    perdas += parcela
                    perdeu_itens.append("Tempo Médio da Fila")
                continue

            # --- CONFORMIDADE ---
            if item_norm == up("CONFORMIDADE"):
                if flag("conformidade", True):
                    recebido += parcela
                else:
                    perdas += parcela
                    perdeu_itens.append("Conformidade")
                continue

            # --- QUALQUER OUTRA META NÃO MAPEADA: considera batida ---
            recebido += parcela

        meta = total_func
        perc = 0.0 if meta == 0 else (recebido / meta) * 100.0

        return pd.Series({
            "MES": nome_mes, "META": meta, "RECEBIDO": recebido, "PERDA": perdas,
            "%": perc, "_badge": "", "_obs": texto_obs(obs), "perdeu_itens": perdeu_itens
        })

    calc = df.apply(calcula_recebido, axis=1)
    return pd.concat([df.reset_index(drop=True), calc], axis=1)

# ===================== LEITURA (TRIMESTRE OU MÊS) =====================
if filtro_mes == "TRIMESTRE":
    try:
        df_o, df_n, df_d = [ler_planilha(m) for m in ["OUTUBRO", "NOVEMBRO", "DEZEMBRO"]]
        st.success("✅ Planilhas carregadas com sucesso: OUTUBRO, NOVEMBRO e DEZEMBRO!")
    except Exception as e:
        st.error(f"Erro ao ler a planilha: {e}")
        st.stop()

    dados_full = pd.concat([
        calcula_mes(df_o, "OUTUBRO"),
        calcula_mes(df_n, "NOVEMBRO"),
        calcula_mes(df_d, "DEZEMBRO")
    ], ignore_index=True)

    group_cols = ["NOME", "FUNÇÃO", "DATA DE ADMISSÃO", "TEMPO DE CASA"]
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

# remove “função fora do painel”
dados_calc = dados_calc[dados_calc["FUNÇÃO"].astype(str).apply(up) == up("ANALISTA")].copy()

# ===================== FILTROS =====================
st.markdown("### 🔎 Filtros")
col1, col2, col3 = st.columns(3)

with col1:
    filtro_nome = st.text_input("Buscar por nome (contém)", "")

with col2:
    tempos = ["Todos"] + sorted(dados_calc["TEMPO DE CASA"].dropna().unique())
    filtro_tempo = st.selectbox("Tempo de casa", tempos)

with col3:
    # opcional: se tiver coluna cidade na base, mostra; se não tiver, ignora
    if "CIDADE" in dados_calc.columns:
        cidades = ["Todas"] + sorted(dados_calc["CIDADE"].dropna().unique())
        filtro_cidade = st.selectbox("Cidade", cidades)
    else:
        filtro_cidade = "Todas"

dados_view = dados_calc.copy()
if filtro_nome:
    dados_view = dados_view[dados_view["NOME"].str.contains(filtro_nome, case=False, na=False)]
if filtro_tempo != "Todos":
    dados_view = dados_view[dados_view["TEMPO DE CASA"] == filtro_tempo]
if filtro_cidade != "Todas" and "CIDADE" in dados_view.columns:
    dados_view = dados_view[dados_view["CIDADE"] == filtro_cidade]

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
cols = st.columns(3)

dados_view = dados_view.sort_values(by="%", ascending=False)

for idx, row in dados_view.iterrows():
    pct = float(row["%"]) if pd.notna(row["%"]) else 0.0
    meta = float(row["META"]) if pd.notna(row["META"]) else 0.0
    recebido = float(row["RECEBIDO"]) if pd.notna(row["RECEBIDO"]) else 0.0
    perdido = float(row["PERDA"]) if pd.notna(row["PERDA"]) else 0.0
    badge = row.get("_badge", "")
    obs_txt = texto_obs(row.get("_obs", ""))
    perdidos_txt = texto_obs(row.get("INDICADORES_NAO_ENTREGUES", ""))

    bg = "#f9f9f9" if not badge else "#eeeeee"

    with cols[idx % 3]:
        subtitulo = []
        if "CIDADE" in row and pd.notna(row.get("CIDADE")):
            subtitulo.append(str(row.get("CIDADE")))
        subtitulo = " — ".join([s for s in subtitulo if s])

        st.markdown(f"""
        <div style="border:1px solid #ccc;padding:16px;border-radius:12px;margin-bottom:12px;background:{bg}">
            <h4 style="margin:0">{str(row.get('NOME','')).title()}</h4>
            <p style="margin:4px 0;"><strong>Analista</strong>{(' — ' + subtitulo) if subtitulo else ''}</p>
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
        if perdidos_txt and "100%" not in perdidos_txt:
            st.caption(f"🔻 Indicadores não entregues: {perdidos_txt}")