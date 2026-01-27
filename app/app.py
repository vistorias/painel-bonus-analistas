# -*- coding: utf-8 -*-
# ============================================================
# Painel de Bônus (T1) | ANALISTAS
# - Sidebar azul (NATIVA) FIXA (SEM recolher / sem setinha)
# - Filtros na sidebar
# - Corrige erro do pandas (__iadd__) usando += normal
# - Corrige cortes nos cards (pills em bloco, quebram linha)
# ============================================================

import streamlit as st
import pandas as pd
import json
from pathlib import Path
import unicodedata
import re
import hmac

# ===================== CONFIG =====================
st.set_page_config(
    page_title="Painel de Bônus (T1) | Analistas",
    layout="wide",
    initial_sidebar_state="expanded",  # garante aberta ao carregar
)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

PESOS_PATH = DATA_DIR / "pesos_analistas.json"
PLANILHA_PATH = DATA_DIR / "RESUMO PARA PAINEL - ANALISTAS.xlsx"

MESES = ["TRIMESTRE", "JANEIRO", "FEVEREIRO", "MARÇO"]

# ===================== ESTILO (SIDEBAR AZUL + UI) =====================
st.markdown(
    """
<style>
/* Remove menu/footer (não mexe no header para não bugar o controle) */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* ===== REGRA PRINCIPAL: IMPEDIR RECOLHER =====
   - Some com o botão/setinha de recolher
   - Some com o controle de reabrir (porque não vamos permitir recolher)
*/
button[title="Collapse sidebar"]{ display:none !important; }
div[data-testid="collapsedControl"]{ display:none !important; }

/* ===== SIDEBAR AZUL (NATIVA) ===== */
section[data-testid="stSidebar"]{
  background: #0b1220;
  border-right: 1px solid rgba(255,255,255,.08);
  min-width: 240px !important;
  width: 240px !important;
}
section[data-testid="stSidebar"] *{ color: #e5e7eb; }
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown div{ color:#e5e7eb; }

/* Inputs do Streamlit na sidebar */
section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] textarea,
section[data-testid="stSidebar"] div[role="combobox"]{
  background: rgba(255,255,255,.06) !important;
  border: 1px solid rgba(255,255,255,.12) !important;
  color: #e5e7eb !important;
}
section[data-testid="stSidebar"] label{
  color: rgba(229,231,235,.85) !important;
  font-weight: 800 !important;
}

/* Largura geral */
.block-container { padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1400px; }

/* títulos da sidebar */
.sb-brand{ display:flex; gap:10px; align-items:center; padding: 6px 2px 2px 2px; }
.sb-logo{
  width: 42px; height: 42px; border-radius: 12px;
  background: rgba(255,255,255,.08);
  display:flex; align-items:center; justify-content:center;
  font-weight: 900; font-size: 16px;
  border: 1px solid rgba(255,255,255,.10);
}
.sb-title{ font-weight: 950; font-size: 1.02rem; line-height: 1.1; margin:0; }
.sb-sub{ color: rgba(229,231,235,.70); font-size: .80rem; margin-top: 2px; }
.sb-section-title{
  font-size: .70rem; letter-spacing:.12em; opacity:.75; font-weight: 900;
  margin: 16px 0 10px 0;
}
.sb-divider{ height:1px; background: rgba(255,255,255,.10); margin: 14px 0; }

/* “abas” do menu (estético) */
.nav-pill{
  border: 1px solid rgba(255,255,255,.10);
  background: rgba(255,255,255,.06);
  padding: 10px 12px;
  border-radius: 12px;
  font-weight: 900;
  margin-bottom: 8px;
}
.nav-pill.active{
  background: rgba(59,130,246,.22);
  border-color: rgba(59,130,246,.45);
}

/* ===== HEADER / KPI ===== */
.page-title { font-size: 1.75rem; font-weight: 950; line-height: 1.1; margin:0; }
.page-sub { color: rgba(15,23,42,.60); font-size: .95rem; margin-top: 4px; }

.kpi-row { display:flex; gap:14px; flex-wrap:wrap; margin: 10px 0 14px 0; }
.kpi{
  flex: 1 1 235px;
  border: 1px solid rgba(15,23,42,.10);
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

/* ===== SEÇÕES ===== */
.section{
  border: 1px solid rgba(15,23,42,.10);
  background: #fff;
  border-radius: 16px;
  padding: 14px;
  box-shadow: 0 8px 24px rgba(15,23,42,.06);
}
.section-title{
  font-weight:950;
  font-size:1.05rem;
  margin-bottom:10px;
  display:flex;
  gap:8px;
  align-items:center;
}

/* ===== CARDS ===== */
.person-card{
  border:1px solid rgba(15,23,42,.10);
  background:#fff;
  border-radius:16px;
  padding:14px;
  box-shadow: 0 10px 28px rgba(15,23,42,.06);
  margin-bottom: 12px;
}
.person-name{ font-size:1.02rem; font-weight:950; margin:0; }
.person-meta{ margin:4px 0 10px 0; color: rgba(15,23,42,.70); font-weight:900; font-size:.90rem;}

.person-grid{
  display:grid;
  grid-template-columns: 1fr 1fr;
  gap:10px;
  margin-top:8px;
}

/* pills em bloco (não cortam) */
.pill{
  width:100%;
  background: rgba(15,23,42,.05);
  border:1px solid rgba(15,23,42,.08);
  padding:10px 12px;
  border-radius:14px;
  box-sizing:border-box;
}
.pill .lbl{ font-size:.78rem; font-weight:900; color: rgba(15,23,42,.68); }
.pill .val{ font-size:.92rem; font-weight:950; color: rgba(15,23,42,.90); margin-top:4px; word-break: break-word; }

.bar{ height:10px; background: rgba(15,23,42,.10); border-radius:999px; overflow:hidden; }
.bar>div{ height:100%; background:#0f172a; }

.muted{ color: rgba(15,23,42,.55); font-size:.86rem; }
.warn{ color:#b45309; font-weight:950; }

@media (max-width: 1200px){
  .person-grid{ grid-template-columns: 1fr; }
}
</style>
""",
    unsafe_allow_html=True,
)
# ===================== LOGIN =====================
# Recomendado: usar secrets no Streamlit Cloud
# Settings -> Secrets:
# [auth]
# users = { "analistas@brave" = "brave123", "wendell_bnascimento@outlook.com" = "123456" }

def _safe_eq(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))

def get_usuarios():
    # 1) tenta pegar do secrets
    try:
        return dict(st.secrets["auth"]["users"])
    except Exception:
        # 2) fallback local (se não tiver secrets)
        return {
            "analistas@brave": "brave123",
            "wendell_bnascimento@outlook.com": "123456",
        }

USUARIOS = get_usuarios()

def autenticar(email: str, senha: str) -> bool:
    email = (email or "").strip().lower()
    senha = (senha or "").strip()
    if email not in USUARIOS:
        return False
    return _safe_eq(str(USUARIOS[email]), senha)

def tela_login():
    st.markdown(
        """
<style>
/* tela cheia e centralizada (não depende do padding do Streamlit) */
div.block-container{
  padding-top: 0rem !important;
  padding-bottom: 0rem !important;
  max-width: 100% !important;
}

.login-fixed{
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.login-box{
  width: 520px;
  max-width: calc(100vw - 48px);
  background: #ffffff;
  border: 1px solid rgba(15,23,42,.10);
  border-radius: 18px;
  box-shadow: 0 14px 40px rgba(15,23,42,.10);
  padding: 26px 26px 18px 26px;
}

.login-top{
  display:flex;
  flex-direction:column;
  align-items:center;
  gap:10px;
  margin-bottom: 14px;
}
.login-logo{
  width: 58px; height: 58px; border-radius: 16px;
  background: rgba(59,130,246,.12);
  border: 1px solid rgba(59,130,246,.20);
  display:flex; align-items:center; justify-content:center;
  font-size: 26px; font-weight: 950;
}
.login-title{ font-size: 1.35rem; font-weight: 950; margin: 0; text-align:center; }
.login-sub{ color: rgba(15,23,42,.60); margin: 0; font-size: .95rem; text-align:center; }

.login-links{
  text-align:center;
  margin-top: 10px;
  color: rgba(15,23,42,.60);
  font-size: .90rem;
}
.login-links span{ opacity:.7; }
</style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="login-fixed"><div class="login-box">', unsafe_allow_html=True)

    st.markdown(
        """
<div class="login-top">
  <div class="login-logo">📄</div>
  <h2 class="login-title">Bem-vindo de volta!</h2>
  <p class="login-sub">Entre com suas credenciais para acessar o sistema</p>
</div>
""",
        unsafe_allow_html=True,
    )

    with st.form("login_form", clear_on_submit=False):
        email = st.text_input("E-mail", value=st.session_state.get("login_email", ""))
        senha = st.text_input("Senha", type="password")
        entrar = st.form_submit_button("Entrar", use_container_width=True)

    if entrar:
        if autenticar(email, senha):
            st.session_state["autenticado"] = True
            st.session_state["login_email"] = (email or "").strip().lower()
            st.rerun()
        else:
            st.session_state["autenticado"] = False
            st.error("Credenciais inválidas.")

    st.markdown(
        """
<div class="login-links">
  <div><span>Esqueci minha senha</span></div>
  <div style="margin-top:6px;"><span>Não tem conta? Cadastre-se</span></div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown("</div></div>", unsafe_allow_html=True)

# GATE: se não estiver logado, mostra login e trava o resto do app
if not st.session_state.get("autenticado", False):
    tela_login()
    st.stop()
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

def load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

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

# ===================== DADOS ======================
try:
    PESOS = load_json(PESOS_PATH)
except Exception as e:
    st.error(f"Erro ao carregar pesos: {e}\nArquivo esperado: {PESOS_PATH.name}")
    st.stop()

def ler_planilha(mes: str) -> pd.DataFrame:
    if PLANILHA_PATH.exists():
        return pd.read_excel(PLANILHA_PATH, sheet_name=mes)
    candidatos = list(DATA_DIR.glob("RESUMO PARA PAINEL - ANALISTAS*.xls*"))
    if not candidatos:
        st.error("Planilha não encontrada em data/ (RESUMO PARA PAINEL - ANALISTAS.xlsx)")
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

    df = df[df["FUNÇÃO"].astype(str).apply(up) == up("ANALISTA")].copy()

    metainfo = PESOS.get(up("ANALISTA"), {})
    itens = metainfo.get("metas", {})

    def calcula_recebido(row):
        obs = row.get("OBSERVAÇÃO", "")
        valor_meta = row.get("VALOR MENSAL META", 0)

        ok, motivo = elegivel(valor_meta, obs)
        perdeu_itens = []

        if not ok:
            return pd.Series({
                "MES": nome_mes, "META": 0.0, "RECEBIDO": 0.0, "PERDA": 0.0, "%": 0.0,
                "_badge": motivo, "_obs": texto_obs(obs), "perdeu_itens": perdeu_itens
            })

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
                    perdeu_itens.append("Tempo Médio do Analista")
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
            "MES": nome_mes, "META": meta, "RECEBIDO": recebido, "PERDA": perdas, "%": perc,
            "_badge": "", "_obs": texto_obs(obs), "perdeu_itens": perdeu_itens
        })

    calc = df.apply(calcula_recebido, axis=1)
    out = pd.concat([df.reset_index(drop=True), calc], axis=1)
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
        agg["%"] = agg.apply(lambda r: 0.0 if r["META"] == 0 else (r["RECEBIDO"] / r["META"]) * 100.0, axis=1)

        perdas_pessoa = (
            full.assign(_lost=lambda d: d.apply(
                lambda r: [f"{it} ({r['MES']})" for it in (r["perdeu_itens"] or [])],
                axis=1))
            .groupby(group_cols, dropna=False)["_lost"]
            .sum()
            .apply(lambda L: ", ".join(sorted(set(L))) if isinstance(L, list) else "")
            .reset_index()
            .rename(columns={"_lost": "INDICADORES_NAO_ENTREGUES"})
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

# ===================== SIDEBAR (AZUL, COM ABAS + FILTROS) =====================
with st.sidebar:
    st.markdown(
        """
<div class="sb-brand">
  <div class="sb-logo">📊</div>
  <div>
    <p class="sb-title">Painel Analistas</p>
    <div class="sb-sub">Bônus • T1</div>
  </div>
</div>
<div class="sb-divider"></div>
<div class="sb-section-title">MENU PRINCIPAL</div>
""",
        unsafe_allow_html=True,
    )

    pagina = st.radio(
        "Navegação",
        ["Dashboard", "Relatório"],
        index=1,
        label_visibility="collapsed"
    )

    st.markdown(
        f"""
<div class="nav-pill {'active' if pagina=='Dashboard' else ''}">🏠 Dashboard</div>
<div class="nav-pill {'active' if pagina=='Relatório' else ''}">📄 Relatório</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="sb-divider"></div><div class="sb-section-title">FILTROS</div>', unsafe_allow_html=True)

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

    st.markdown(
        """
<div class="sb-divider"></div>
<div style="opacity:.85;font-weight:900;font-size:.80rem;">Logado como</div>
<div style="font-weight:950;margin-top:2px;">analistas@brave</div>
""",
        unsafe_allow_html=True,
    )
    st.markdown('<div class="sb-divider"></div>', unsafe_allow_html=True)
    if st.button("Sair", use_container_width=True):
        st.session_state["autenticado"] = False
        st.rerun()
# ===================== CONTEÚDO =====================
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
    st.markdown('<div class="section-title">📌 Resumo</div>', unsafe_allow_html=True)

    cumprimento_medio = 0.0 if total_possivel == 0 else (recebido / total_possivel) * 100.0
    resumo = pd.DataFrame(
        {
            "Item": ["Total possível", "Recebido", "Deixou de ganhar", "Cumprimento médio"],
            "Valor": [brl(total_possivel), brl(recebido), brl(perda), f"{cumprimento_medio:.1f}%"],
        }
    )
    st.dataframe(resumo, use_container_width=True, hide_index=True)

    top = dados_view.head(5).copy()
    cols_top = [c for c in ["NOME", "CIDADE", "%", "RECEBIDO", "PERDA"] if c in top.columns]
    top = top[cols_top]
    if "%" in top.columns:
        top["%"] = top["%"].apply(lambda x: f"{float(x):.1f}%")
    if "RECEBIDO" in top.columns:
        top["RECEBIDO"] = top["RECEBIDO"].apply(brl)
    if "PERDA" in top.columns:
        top["PERDA"] = top["PERDA"].apply(brl)
    if "CIDADE" in top.columns:
        top["CIDADE"] = top["CIDADE"].astype(str).str.title()

    st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">🏆 Top 5</div>', unsafe_allow_html=True)
    st.dataframe(top, use_container_width=True, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">👥 Analistas</div>', unsafe_allow_html=True)

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
        if tempo:
            meta_line = f"{meta_line} • {tempo}"

        with cols_cards[idx % 2]:
            st.markdown(
                f"""
<div class="person-card">
  <p class="person-name">{nome}</p>
  <div class="person-meta">{meta_line}</div>

  <div class="person-grid">
    <div class="pill"><div class="lbl">Meta</div><div class="val">{brl(meta)}</div></div>
    <div class="pill"><div class="lbl">Recebido</div><div class="val">{brl(rec)}</div></div>
    <div class="pill"><div class="lbl">Perda</div><div class="val">{brl(per)}</div></div>
    <div class="pill"><div class="lbl">Cumprimento</div><div class="val">{pct:.1f}%</div></div>
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

    st.markdown("</div>", unsafe_allow_html=True)

