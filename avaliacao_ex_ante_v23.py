import os
import json
from io import BytesIO
from datetime import datetime
from uuid import uuid4

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

st.set_page_config(
    page_title="Avaliação ex ante – Embrapa Territorial",
    layout="wide"
)

# =========================================================
# CONFIGURAÇÕES
# =========================================================
HISTORICO_CSV = "historico_avaliacoes.csv"
UNIDADES_CSV = "unidades.csv"
AREAS_CSV = "areas_tematicas.csv"
PARCEIROS_CSV = "parceiros.csv"
PUBLICOS_CSV = "publicos.csv"
EMPREGADOS_CSV = "empregados.csv"
RESULTADOS_CSV = "resultados_embrapa.csv"
DOMINIO_EMAIL_PERMITIDO = "@embrapa.br"


def gerar_id_proposta():
    data = datetime.now().strftime("%Y%m%d")
    sufixo = uuid4().hex[:8].upper()
    return f"TER-{data}-{sufixo}"

TIPOS_PROPOSTA = [
    "",
    "Pesquisa científica",
    "Desenvolvimento metodológico",
    "Plataforma de dados",
    "Sistema de monitoramento",
    "Suporte a políticas públicas",
    "Outro",
]

PORTFOLIOS = [
    "",
    "Sistemas de Produção Sustentáveis e Resilientes",
    "Clima, recursos naturais e transformação ecológica",
    "Protagonismo do consumidor",
    "Bioeficiência na agropecuária",
    "Economia da biodiversidade",
    "Economia verde",
    "Agroecologia e Inclusão Socioprodutiva",
    "Biorrevolução",
    "Transformação digital na agropecuária",
]

# =========================================================
# LEITURA DAS TABELAS-BASE
# =========================================================
@st.cache_data
def carregar_tabela(caminho):
    try:
        if os.path.exists(caminho) and os.path.getsize(caminho) > 0:
            return pd.read_csv(caminho)
        else:
            return pd.DataFrame()
    except Exception:
        return pd.DataFrame()


df_unidades = carregar_tabela("unidades.csv")
df_areas = carregar_tabela("areas_tematicas.csv")
df_parceiros = carregar_tabela("parceiros.csv")
df_publicos = carregar_tabela("publicos.csv")
df_empregados = carregar_tabela("empregados.csv")
df_resultados = carregar_tabela("resultados_embrapa.csv")

# =========================================================
# SESSION STATE
# =========================================================
if "etapa" not in st.session_state:
    st.session_state.etapa = 1

if "scores" not in st.session_state:
    st.session_state.scores = {}

if "cadastro" not in st.session_state:
    st.session_state.cadastro = {
        "id_proposta": gerar_id_proposta(),
        "titulo": "",
        "proponente": "",
        "equipe": "",
        "ids_equipe": [],
        "nomes_equipe": [],
        "id_unidade": "",
        "nome_unidade": "",
        "id_area_tematica": "",
        "nome_area_tematica": "",
        "portfolio": "",
        "tipo_proposta": "",
        "ids_resultados": [],
        "categorias_resultados": [],
        "tipos_resultados": [],
        "comprovantes_resultados": [],
        "exemplos_resultados": [],
        "id_resultado": "",
        "categoria_resultado": "",
        "tipo_resultado": "",
        "comprovante_resultado": "",
        "exemplos_resultado": "",
        "duracao_meses": 36,
        "valor_solicitado": 0.0,
        "ids_parceiros": [],
        "nomes_parceiros": [],
        "ids_publicos": [],
        "nomes_publicos": [],
        "resumo": "",
        "anotacoes": "",
        "consideracoes": "",
        "data_avaliacao": "",
    }

if "resultados_calculados" not in st.session_state:
    st.session_state.resultados_calculados = False

if "avaliacao_salva" not in st.session_state:
    st.session_state.avaliacao_salva = False

if "anotacoes_indicadores" not in st.session_state:
    st.session_state.anotacoes_indicadores = {}

if "admin_autenticado" not in st.session_state:
    st.session_state.admin_autenticado = False

if "auth_user" not in st.session_state:
    st.session_state.auth_user = None

if "access_token" not in st.session_state:
    st.session_state.access_token = ""

if "refresh_token" not in st.session_state:
    st.session_state.refresh_token = ""

if "user_profile" not in st.session_state:
    st.session_state.user_profile = None

# =========================================================
# QUESTÕES
# =========================================================
QUESTOES = [
    {"dimensao": "Econômica", "codigo": "E1", "pergunta": "Qual o potencial da proposta para gerar ganhos de eficiência econômica ou produtiva?", "opcoes": {1: "Muito baixo", 2: "Baixo", 3: "Moderado", 4: "Alto", 5: "Muito alto / transformador"}},
    {"dimensao": "Econômica", "codigo": "E2", "pergunta": "Qual o potencial da proposta para reduzir custos, riscos ou perdas em sistemas produtivos ou institucionais?", "opcoes": {1: "Muito baixo", 2: "Baixo", 3: "Moderado", 4: "Alto", 5: "Muito alto"}},
    {"dimensao": "Econômica", "codigo": "E3", "pergunta": "Qual o potencial da proposta para criar ou fortalecer atividades econômicas, mercados ou oportunidades produtivas?", "opcoes": {1: "Muito baixo", 2: "Baixo", 3: "Moderado", 4: "Alto", 5: "Muito alto"}},
    {"dimensao": "Social", "codigo": "S1", "pergunta": "Qual o potencial da proposta para beneficiar grupos sociais relevantes (produtores, comunidades, gestores públicos etc.)?", "opcoes": {1: "Muito baixo", 2: "Baixo", 3: "Moderado", 4: "Alto", 5: "Muito alto"}},
    {"dimensao": "Social", "codigo": "S2", "pergunta": "Qual o potencial da proposta para contribuir para inclusão social, redução de desigualdades ou fortalecimento de capacidades?", "opcoes": {1: "Muito baixo", 2: "Baixo", 3: "Moderado", 4: "Alto", 5: "Muito alto"}},
    {"dimensao": "Social", "codigo": "S3", "pergunta": "Qual o potencial da proposta para melhorar condições de vida, segurança alimentar ou acesso a recursos e serviços?", "opcoes": {1: "Muito baixo", 2: "Baixo", 3: "Moderado", 4: "Alto", 5: "Muito alto"}},
    {"dimensao": "Ambiental", "codigo": "A1", "pergunta": "Qual o potencial da proposta para contribuir para conservação de recursos naturais ou biodiversidade?", "opcoes": {1: "Muito baixo", 2: "Baixo", 3: "Moderado", 4: "Alto", 5: "Muito alto"}},
    {"dimensao": "Ambiental", "codigo": "A2", "pergunta": "Qual o potencial da proposta para contribuir para mitigação ou adaptação às mudanças climáticas?", "opcoes": {1: "Muito baixo", 2: "Baixo", 3: "Moderado", 4: "Alto", 5: "Muito alto"}},
    {"dimensao": "Ambiental", "codigo": "A3", "pergunta": "Qual o potencial da proposta para promover uso sustentável do território ou dos recursos naturais?", "opcoes": {1: "Muito baixo", 2: "Baixo", 3: "Moderado", 4: "Alto", 5: "Muito alto"}},
    {"dimensao": "Política", "codigo": "P1", "pergunta": "Qual o potencial da proposta para informar ou apoiar processos de formulação de políticas públicas?", "opcoes": {1: "Muito baixo", 2: "Baixo", 3: "Moderado", 4: "Alto", 5: "Muito alto"}},
    {"dimensao": "Política", "codigo": "P2", "pergunta": "Qual o potencial da proposta para influenciar decisões de gestores públicos ou instituições?", "opcoes": {1: "Muito baixo", 2: "Baixo", 3: "Moderado", 4: "Alto", 5: "Muito alto"}},
    {"dimensao": "Política", "codigo": "P3", "pergunta": "Qual o potencial da proposta para gerar evidências ou instrumentos relevantes para políticas públicas?", "opcoes": {1: "Muito baixo", 2: "Baixo", 3: "Moderado", 4: "Alto", 5: "Muito alto"}},
    {"dimensao": "Institucional", "codigo": "I1", "pergunta": "Qual o potencial da proposta para fortalecer capacidades institucionais da Embrapa ou de parceiros?", "opcoes": {1: "Muito baixo", 2: "Baixo", 3: "Moderado", 4: "Alto", 5: "Muito alto"}},
    {"dimensao": "Institucional", "codigo": "I2", "pergunta": "Qual o potencial da proposta para gerar bases de dados, métodos ou ferramentas estratégicas?", "opcoes": {1: "Muito baixo", 2: "Baixo", 3: "Moderado", 4: "Alto", 5: "Muito alto"}},
    {"dimensao": "Institucional", "codigo": "I3", "pergunta": "Qual o potencial da proposta para fortalecer redes de colaboração ou posicionamento institucional da Embrapa?", "opcoes": {1: "Muito baixo", 2: "Baixo", 3: "Moderado", 4: "Alto", 5: "Muito alto"}},
    {"dimensao": "Trajetória de impacto", "codigo": "T1", "pergunta": "Os usuários potenciais dos resultados estão claramente identificados?", "opcoes": {1: "Inexistente", 2: "Pouco claro", 3: "Parcialmente identificado", 4: "Bem identificado", 5: "Muito claramente identificado"}},
    {"dimensao": "Trajetória de impacto", "codigo": "T2", "pergunta": "Existem parcerias institucionais relevantes associadas à proposta?", "opcoes": {1: "Inexistentes", 2: "Fracas", 3: "Moderadas", 4: "Fortes", 5: "Muito fortes"}},
    {"dimensao": "Trajetória de impacto", "codigo": "T3", "pergunta": "Existe uma estratégia plausível de uso ou aplicação dos resultados?", "opcoes": {1: "Nenhuma", 2: "Fraca", 3: "Parcial", 4: "Bem definida", 5: "Muito robusta"}},
    {"dimensao": "Trajetória de impacto", "codigo": "T4", "pergunta": "A proposta se apoia em resultados prévios ou evidências existentes?", "opcoes": {1: "Nenhuma", 2: "Limitada", 3: "Moderada", 4: "Forte", 5: "Muito forte"}},
    {"dimensao": "Trajetória de impacto", "codigo": "T5", "pergunta": "Existe capacidade institucional para implementação ou difusão dos resultados?", "opcoes": {1: "Nenhuma", 2: "Limitada", 3: "Moderada", 4: "Forte", 5: "Muito forte"}},
]

DIMENSOES = [
    "Econômica",
    "Social",
    "Ambiental",
    "Política",
    "Institucional",
    "Trajetória de impacto",
]

for q in QUESTOES:
    if q["codigo"] not in st.session_state.scores:
        st.session_state.scores[q["codigo"]] = 3
    if q["codigo"] not in st.session_state.anotacoes_indicadores:
        st.session_state.anotacoes_indicadores[q["codigo"]] = ""

# =========================================================
# FUNÇÕES
# =========================================================
def validar_cadastro(cadastro):
    obrigatorios = {
        "titulo": "Título",
        "proponente": "Proponente",
        "nomes_equipe": "Equipe responsável",
        "nome_unidade": "Unidade",
        "nome_area_tematica": "Área temática",
        "tipos_resultados": "Resultado esperado",
        "resumo": "Resumo executivo",
    }
    faltantes = []
    for chave, label in obrigatorios.items():
        valor = cadastro.get(chave, "")
        if isinstance(valor, list):
            if len(valor) == 0:
                faltantes.append(label)
        else:
            if str(valor).strip() == "":
                faltantes.append(label)
    return faltantes


def calcular_dimensoes(scores_dict):
    resultado = {}
    for dim in DIMENSOES:
        codigos = [q["codigo"] for q in QUESTOES if q["dimensao"] == dim]
        valores = [scores_dict[c] for c in codigos]
        resultado[dim] = round(sum(valores) / len(valores), 2)
    return resultado


def calcular_indices(dim_scores):
    impacto_potencial = round(
        (dim_scores["Econômica"] + dim_scores["Social"] + dim_scores["Ambiental"] + dim_scores["Política"]) / 4,
        2,
    )
    maturidade = round(dim_scores["Trajetória de impacto"], 2)
    capacidade = round(dim_scores["Institucional"], 2)
    indice_estrategico = round(impacto_potencial * 0.5 + maturidade * 0.3 + capacidade * 0.2, 2)

    if indice_estrategico >= 4.0:
        classificacao = "Alta prioridade"
    elif indice_estrategico >= 3.0:
        classificacao = "Prioridade média"
    else:
        classificacao = "Baixa prioridade"

    return {
        "impacto_potencial": impacto_potencial,
        "maturidade_trajetoria": maturidade,
        "capacidade_institucional": capacidade,
        "indice_estrategico": indice_estrategico,
        "classificacao": classificacao,
    }


def gerar_radar(dim_scores):
    categorias = list(dim_scores.keys())
    valores = list(dim_scores.values())

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=valores + [valores[0]],
            theta=categorias + [categorias[0]],
            fill="toself",
            name="Pontuação",
        )
    )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
        showlegend=False,
        height=500,
    )
    return fig


def montar_dataframe_respostas(scores_dict, anotacoes_dict=None):
    anotacoes_dict = anotacoes_dict or {}
    linhas = []
    for q in QUESTOES:
        nota = scores_dict[q["codigo"]]
        linhas.append(
            {
                "Dimensão": q["dimensao"],
                "Código": q["codigo"],
                "Pergunta": q["pergunta"],
                "Nota": nota,
                "Descrição da resposta": q["opcoes"][nota],
                "Anotações": anotacoes_dict.get(q["codigo"], ""),
            }
        )
    return pd.DataFrame(linhas)


def exportar_excel(df_respostas, df_dimensoes, df_resumo, cadastro):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame([cadastro]).to_excel(writer, sheet_name="Cadastro", index=False)
        df_respostas.to_excel(writer, sheet_name="Respostas", index=False)
        df_dimensoes.to_excel(writer, sheet_name="Dimensões", index=False)
        df_resumo.to_excel(writer, sheet_name="Resumo", index=False)
    return output.getvalue()


def montar_resumo_cadastro(cadastro):
    return pd.DataFrame(
        [
            {"Campo": "Identificador automático", "Valor": cadastro.get("id_proposta", "")},
            {"Campo": "Título", "Valor": cadastro.get("titulo", "")},
            {"Campo": "Proponente", "Valor": cadastro.get("proponente", "")},
            {"Campo": "Equipe", "Valor": " | ".join(cadastro.get("nomes_equipe", [])) or cadastro.get("equipe", "")},
            {"Campo": "Unidade", "Valor": cadastro.get("nome_unidade", "")},
            {"Campo": "Área temática", "Valor": cadastro.get("nome_area_tematica", "")},
            {"Campo": "Portfólio / programa", "Valor": cadastro.get("portfolio", "")},
            {"Campo": "Tipo de proposta", "Valor": cadastro.get("tipo_proposta", "")},
            {"Campo": "Resultados esperados", "Valor": " | ".join(cadastro.get("tipos_resultados", [])) or cadastro.get("tipo_resultado", "")},
            {"Campo": "Parceiros principais", "Valor": " | ".join(cadastro.get("nomes_parceiros", []))},
            {"Campo": "Públicos-alvo", "Valor": " | ".join(cadastro.get("nomes_publicos", []))},
            {"Campo": "Data da avaliação", "Valor": cadastro.get("data_avaliacao", "")},
        ]
    )


def montar_linha_historico(cadastro, scores, dim_scores, indices):
    linha = {}
    linha.update(cadastro)
    linha["ids_equipe"] = " | ".join(cadastro.get("ids_equipe", []))
    linha["nomes_equipe"] = " | ".join(cadastro.get("nomes_equipe", []))
    linha["ids_resultados"] = " | ".join(cadastro.get("ids_resultados", []))
    linha["categorias_resultados"] = " | ".join(cadastro.get("categorias_resultados", []))
    linha["tipos_resultados"] = " | ".join(cadastro.get("tipos_resultados", []))
    linha["comprovantes_resultados"] = " | ".join(cadastro.get("comprovantes_resultados", []))
    linha["exemplos_resultados"] = " | ".join(cadastro.get("exemplos_resultados", []))
    linha["ids_parceiros"] = " | ".join(cadastro.get("ids_parceiros", []))
    linha["nomes_parceiros"] = " | ".join(cadastro.get("nomes_parceiros", []))
    linha["ids_publicos"] = " | ".join(cadastro.get("ids_publicos", []))
    linha["nomes_publicos"] = " | ".join(cadastro.get("nomes_publicos", []))
    linha["timestamp_salvamento"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for q in QUESTOES:
        codigo = q["codigo"]
        linha[f"score_{codigo}"] = scores[codigo]
        linha[f"desc_{codigo}"] = q["opcoes"][scores[codigo]]
        linha[f"anotacao_{codigo}"] = st.session_state.anotacoes_indicadores.get(codigo, "")

    for dim, valor in dim_scores.items():
        linha[f"dim_{dim}"] = valor

    for k, v in indices.items():
        linha[k] = v

    return linha


def salvar_historico_csv(cadastro, scores, dim_scores, indices, caminho_csv=HISTORICO_CSV):
    linha = montar_linha_historico(cadastro, scores, dim_scores, indices)
    df_novo = pd.DataFrame([linha])

    if os.path.exists(caminho_csv):
        df_existente = pd.read_csv(caminho_csv)
        df_final = pd.concat([df_existente, df_novo], ignore_index=True)
    else:
        df_final = df_novo

    df_final.to_csv(caminho_csv, index=False, encoding="utf-8-sig")
    return df_final


def obter_config_supabase():
    try:
        url = st.secrets.get("SUPABASE_URL", "")
        chave = st.secrets.get("SUPABASE_SERVICE_ROLE_KEY", "") or st.secrets.get("SUPABASE_ANON_KEY", "")
        tabela = st.secrets.get("SUPABASE_TABLE", "avaliacoes")
    except Exception:
        return None

    if not url or not chave:
        return None

    return {
        "url": url.rstrip("/"),
        "chave": chave,
        "tabela": tabela,
    }


def email_permitido(email):
    return email.strip().lower().endswith(DOMINIO_EMAIL_PERMITIDO)


def headers_supabase(token=None, prefer=None):
    config = obter_config_supabase()
    if not config:
        return None

    headers = {
        "apikey": config["chave"],
        "Authorization": f"Bearer {token or config['chave']}",
        "Content-Type": "application/json",
    }
    if prefer:
        headers["Prefer"] = prefer
    return headers


def criar_conta_supabase(email, senha, nome):
    config = obter_config_supabase()
    if not config:
        return False, "Supabase não configurado em st.secrets."

    if not email_permitido(email):
        return False, f"Use um email institucional com domínio {DOMINIO_EMAIL_PERMITIDO}."

    payload = {
        "email": email.strip().lower(),
        "password": senha,
        "data": {
            "nome": nome.strip(),
            "papel": "proponente",
        },
    }
    try:
        resposta = requests.post(
            f"{config['url']}/auth/v1/signup",
            headers=headers_supabase(),
            json=payload,
            timeout=15,
        )
        if resposta.status_code >= 400:
            detalhe = resposta.json().get("msg", resposta.text)
            return False, f"Não foi possível criar a conta: {detalhe}"
        return True, "Conta criada. Verifique seu email para confirmar o cadastro antes de entrar."
    except requests.RequestException as erro:
        return False, f"Falha ao criar conta: {erro}"


def login_supabase(email, senha):
    config = obter_config_supabase()
    if not config:
        return False, "Supabase não configurado em st.secrets."

    if not email_permitido(email):
        return False, f"Use um email institucional com domínio {DOMINIO_EMAIL_PERMITIDO}."

    payload = {
        "email": email.strip().lower(),
        "password": senha,
    }
    try:
        resposta = requests.post(
            f"{config['url']}/auth/v1/token?grant_type=password",
            headers=headers_supabase(),
            json=payload,
            timeout=15,
        )
        if resposta.status_code >= 400:
            detalhe = resposta.json().get("error_description", resposta.text)
            return False, f"Não foi possível entrar: {detalhe}"

        dados = resposta.json()
        st.session_state.auth_user = dados.get("user", {})
        st.session_state.access_token = dados.get("access_token", "")
        st.session_state.refresh_token = dados.get("refresh_token", "")
        st.session_state.user_profile = carregar_profile_usuario(st.session_state.access_token)
        return True, "Login realizado."
    except requests.RequestException as erro:
        return False, f"Falha ao entrar: {erro}"


def carregar_profile_usuario(token):
    config = obter_config_supabase()
    if not config or not token:
        return None

    try:
        resposta = requests.get(
            f"{config['url']}/rest/v1/profiles",
            headers=headers_supabase(token),
            params={"select": "*", "id": "eq." + st.session_state.auth_user.get("id", "")},
            timeout=15,
        )
        if resposta.status_code >= 400:
            return None
        registros = resposta.json()
        return registros[0] if registros else None
    except requests.RequestException:
        return None


def usuario_logado():
    return bool(st.session_state.get("access_token") and st.session_state.get("auth_user"))


def sair():
    st.session_state.auth_user = None
    st.session_state.access_token = ""
    st.session_state.refresh_token = ""
    st.session_state.user_profile = None
    st.session_state.admin_autenticado = False
    resetar_avaliacao()


def exibir_autenticacao():
    st.subheader("Acesso ao TerImpact")
    st.caption(f"Use seu email institucional {DOMINIO_EMAIL_PERMITIDO}.")

    aba_login, aba_cadastro = st.tabs(["Entrar", "Criar conta"])

    with aba_login:
        email_login = st.text_input("Email institucional", key="login_email")
        senha_login = st.text_input("Senha", type="password", key="login_senha")
        if st.button("Entrar"):
            ok, msg = login_supabase(email_login, senha_login)
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

    with aba_cadastro:
        nome_cadastro = st.text_input("Nome completo", key="cadastro_nome")
        email_cadastro = st.text_input("Email institucional", key="cadastro_email")
        senha_cadastro = st.text_input("Senha", type="password", key="cadastro_senha")
        if st.button("Criar conta"):
            if len(senha_cadastro) < 8:
                st.error("Use uma senha com pelo menos 8 caracteres.")
            else:
                ok, msg = criar_conta_supabase(email_cadastro, senha_cadastro, nome_cadastro)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

    st.stop()


def salvar_historico_supabase(cadastro, scores, dim_scores, indices):
    config = obter_config_supabase()
    if not config:
        return False, "Supabase não configurado em st.secrets."

    payload = {
        "id_proposta": cadastro.get("id_proposta", ""),
        "titulo": cadastro.get("titulo", ""),
        "proponente": cadastro.get("proponente", ""),
        "cadastro": cadastro,
        "scores": scores,
        "anotacoes_indicadores": st.session_state.anotacoes_indicadores,
        "dim_scores": dim_scores,
        "indices": indices,
    }
    endpoint = f"{config['url']}/rest/v1/{config['tabela']}"
    headers = {
        "apikey": config["chave"],
        "Authorization": f"Bearer {config['chave']}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }

    try:
        resposta = requests.post(endpoint, headers=headers, json=payload, timeout=15)
        resposta.raise_for_status()
        return True, "Avaliação salva no Supabase."
    except requests.RequestException as erro:
        return False, f"Não foi possível salvar no Supabase: {erro}"


def carregar_avaliacoes_supabase():
    config = obter_config_supabase()
    if not config:
        return pd.DataFrame(), "Supabase não configurado em st.secrets."

    endpoint = f"{config['url']}/rest/v1/{config['tabela']}"
    headers = {
        "apikey": config["chave"],
        "Authorization": f"Bearer {config['chave']}",
    }
    params = {
        "select": "*",
        "order": "created_at.desc",
    }

    try:
        resposta = requests.get(endpoint, headers=headers, params=params, timeout=15)
        resposta.raise_for_status()
        registros = resposta.json()
    except requests.RequestException as erro:
        return pd.DataFrame(), f"Não foi possível consultar o Supabase: {erro}"

    linhas = []
    for registro in registros:
        cadastro = registro.get("cadastro") or {}
        indices_reg = registro.get("indices") or {}
        dim_scores_reg = registro.get("dim_scores") or {}
        linhas.append(
            {
                "created_at": registro.get("created_at", ""),
                "id_proposta": registro.get("id_proposta", ""),
                "titulo": registro.get("titulo", ""),
                "proponente": registro.get("proponente", ""),
                "unidade": cadastro.get("nome_unidade", ""),
                "area_tematica": cadastro.get("nome_area_tematica", ""),
                "portfolio": cadastro.get("portfolio", ""),
                "tipo_proposta": cadastro.get("tipo_proposta", ""),
                "resultados": " | ".join(cadastro.get("tipos_resultados", [])) or cadastro.get("tipo_resultado", ""),
                "indice_estrategico": indices_reg.get("indice_estrategico", ""),
                "classificacao": indices_reg.get("classificacao", ""),
                "impacto_potencial": indices_reg.get("impacto_potencial", ""),
                "maturidade_trajetoria": indices_reg.get("maturidade_trajetoria", ""),
                "capacidade_institucional": indices_reg.get("capacidade_institucional", ""),
                "dimensoes": json.dumps(dim_scores_reg, ensure_ascii=False),
                "cadastro_json": json.dumps(cadastro, ensure_ascii=False),
                "scores_json": json.dumps(registro.get("scores") or {}, ensure_ascii=False),
                "anotacoes_indicadores_json": json.dumps(registro.get("anotacoes_indicadores") or {}, ensure_ascii=False),
            }
        )

    return pd.DataFrame(linhas), ""


def admin_autenticado():
    perfil = st.session_state.get("user_profile") or {}
    if perfil.get("papel") == "admin":
        return True

    try:
        senha_configurada = st.secrets.get("ADMIN_PASSWORD", "")
    except Exception:
        senha_configurada = ""

    if not senha_configurada:
        st.warning("Painel administrativo sem senha configurada. Defina ADMIN_PASSWORD em st.secrets.")
        return False

    if st.session_state.get("admin_autenticado", False):
        return True

    senha = st.text_input("Senha administrativa", type="password")
    if st.button("Acessar painel"):
        if senha == senha_configurada:
            st.session_state.admin_autenticado = True
            st.rerun()
        else:
            st.error("Senha incorreta.")

    return False


def carregar_historico(caminho_csv=HISTORICO_CSV):
    if os.path.exists(caminho_csv):
        return pd.read_csv(caminho_csv)
    return pd.DataFrame()


def resetar_avaliacao():
    st.session_state.etapa = 1
    st.session_state.resultados_calculados = False
    st.session_state.avaliacao_salva = False
    st.session_state.cadastro = {
        "id_proposta": gerar_id_proposta(),
        "titulo": "",
        "proponente": "",
        "equipe": "",
        "ids_equipe": [],
        "nomes_equipe": [],
        "id_unidade": "",
        "nome_unidade": "",
        "id_area_tematica": "",
        "nome_area_tematica": "",
        "portfolio": "",
        "tipo_proposta": "",
        "ids_resultados": [],
        "categorias_resultados": [],
        "tipos_resultados": [],
        "comprovantes_resultados": [],
        "exemplos_resultados": [],
        "id_resultado": "",
        "categoria_resultado": "",
        "tipo_resultado": "",
        "comprovante_resultado": "",
        "exemplos_resultado": "",
        "duracao_meses": 36,
        "valor_solicitado": 0.0,
        "ids_parceiros": [],
        "nomes_parceiros": [],
        "ids_publicos": [],
        "nomes_publicos": [],
        "resumo": "",
        "anotacoes": "",
        "consideracoes": "",
        "data_avaliacao": "",
    }
    st.session_state.scores = {q["codigo"]: 3 for q in QUESTOES}
    st.session_state.anotacoes_indicadores = {q["codigo"]: "" for q in QUESTOES}


# =========================================================
# CÁLCULOS
# =========================================================
dim_scores = calcular_dimensoes(st.session_state.scores)
indices = calcular_indices(dim_scores)
df_respostas = montar_dataframe_respostas(st.session_state.scores, st.session_state.anotacoes_indicadores)
df_dimensoes = pd.DataFrame([{"Dimensão": k, "Pontuação média": v} for k, v in dim_scores.items()])
df_resumo = pd.DataFrame([indices])
df_historico = carregar_historico()

# =========================================================
# TOPO
# =========================================================
st.title("Avaliação ex ante de propostas – Embrapa Territorial")
st.caption("Versão 2.3 – fluxo guiado + histórico + tabelas-base relacionais")

if not usuario_logado():
    exibir_autenticacao()

perfil_usuario = st.session_state.get("user_profile") or {}
email_usuario = (st.session_state.get("auth_user") or {}).get("email", "")
nome_usuario = perfil_usuario.get("nome") or email_usuario
papel_usuario = perfil_usuario.get("papel", "proponente")

col_usuario, col_sair = st.columns([4, 1])
with col_usuario:
    st.caption(f"Usuário: {nome_usuario} | Perfil: {papel_usuario}")
with col_sair:
    if st.button("Sair"):
        sair()
        st.rerun()

nomes_etapas = {
    1: "Dados da proposta",
    2: "Avaliação",
    3: "Resultados",
    4: "Exportação",
    5: "Governança",
}

col_status, col_admin = st.columns([4, 1])
with col_status:
    st.progress(st.session_state.etapa / 5)
    st.markdown(f"**Etapa {st.session_state.etapa} de 5 — {nomes_etapas[st.session_state.etapa]}**")
with col_admin:
    if st.button("Governança"):
        st.session_state.etapa = 5
        st.rerun()

# =========================================================
# ETAPA 1
# =========================================================
if st.session_state.etapa == 1:
    st.subheader("Etapa 1 — Dados da proposta")

    cadastro_atual = st.session_state.cadastro
    col1, col2 = st.columns(2)

    unidades_opcoes = {}
    if not df_unidades.empty:
        unidades_opcoes = dict(zip(df_unidades["nome_unidade"], df_unidades["id_unidade"]))

    areas_opcoes = {}
    if not df_areas.empty:
        areas_opcoes = dict(zip(df_areas["nome_area"], df_areas["id_area"]))

    parceiros_opcoes = {}
    if not df_parceiros.empty:
        parceiros_opcoes = dict(zip(df_parceiros["nome_parceiro"], df_parceiros["id_parceiro"]))

    publicos_opcoes = {}
    if not df_publicos.empty:
        publicos_opcoes = dict(zip(df_publicos["nome_publico"], df_publicos["id_publico"]))

    empregados_opcoes = {}
    if not df_empregados.empty:
        empregados_opcoes = dict(zip(df_empregados["nome_empregado"], df_empregados["id_empregado"]))

    resultados_opcoes = {}
    if not df_resultados.empty:
        resultados_opcoes = dict(zip(df_resultados["tipo_resultado"], df_resultados["id_resultado"]))

    with col1:
        titulo = st.text_input("Título da proposta", value=cadastro_atual["titulo"])
        proponente = st.text_input("Proponente", value=nome_usuario, disabled=True)

        if empregados_opcoes:
            nomes_empregados = list(empregados_opcoes.keys())
            equipe_sel = st.multiselect(
                "Equipe responsável",
                options=nomes_empregados,
                default=[
                    nome for nome in cadastro_atual.get("nomes_equipe", [])
                    if nome in nomes_empregados
                ],
            )
            if equipe_sel:
                colunas_equipe = ["nome_empregado", "cargo", "funcao"]
                equipe_preview = df_empregados[df_empregados["nome_empregado"].isin(equipe_sel)][colunas_equipe]
                st.dataframe(equipe_preview, width="stretch", hide_index=True)
        else:
            equipe_texto = st.text_input("Equipe responsável (tabela não carregada)", value=cadastro_atual["equipe"])
            equipe_sel = [nome.strip() for nome in equipe_texto.split(";") if nome.strip()]

        if unidades_opcoes:
            nomes_unidades = list(unidades_opcoes.keys())
            unidade_sel = st.selectbox(
                "Unidade",
                options=[""] + nomes_unidades,
                index=([""] + nomes_unidades).index(cadastro_atual["nome_unidade"])
                if cadastro_atual["nome_unidade"] in ([""] + nomes_unidades) else 0
            )
        else:
            unidade_sel = st.text_input("Unidade (tabela não carregada)", value=cadastro_atual["nome_unidade"])

        if areas_opcoes:
            nomes_areas = list(areas_opcoes.keys())
            area_sel = st.selectbox(
                "Área temática",
                options=[""] + nomes_areas,
                index=([""] + nomes_areas).index(cadastro_atual["nome_area_tematica"])
                if cadastro_atual["nome_area_tematica"] in ([""] + nomes_areas) else 0
            )
        else:
            area_sel = st.text_input("Área temática (tabela não carregada)", value=cadastro_atual["nome_area_tematica"])

    with col2:
        portfolio = st.selectbox(
            "Portfólio / programa",
            PORTFOLIOS,
            index=PORTFOLIOS.index(cadastro_atual["portfolio"])
            if cadastro_atual["portfolio"] in PORTFOLIOS else 0,
        )
        tipo_proposta = st.selectbox(
            "Tipo de proposta",
            TIPOS_PROPOSTA,
            index=TIPOS_PROPOSTA.index(cadastro_atual["tipo_proposta"])
            if cadastro_atual["tipo_proposta"] in TIPOS_PROPOSTA else 0,
        )

        resultados_sel = []
        resultados_info = []
        if resultados_opcoes:
            nomes_resultados = list(resultados_opcoes.keys())
            resultados_padrao = cadastro_atual.get("tipos_resultados") or (
                [cadastro_atual.get("tipo_resultado")]
                if cadastro_atual.get("tipo_resultado") in nomes_resultados else []
            )
            resultados_sel = st.multiselect(
                "Resultados esperados",
                options=nomes_resultados,
                default=[r for r in resultados_padrao if r in nomes_resultados],
            )
            if resultados_sel:
                resultados_info = (
                    df_resultados[df_resultados["tipo_resultado"].isin(resultados_sel)]
                    .sort_values("tipo_resultado")
                    .to_dict("records")
                )
                st.dataframe(
                    pd.DataFrame(resultados_info)[
                        ["categoria_resultado", "tipo_resultado", "comprovante_entrega", "exemplos"]
                    ],
                    width="stretch",
                    hide_index=True,
                )
        else:
            resultado_texto = st.text_input("Resultados esperados (tabela não carregada)", value=cadastro_atual["tipo_resultado"])
            resultados_sel = [r.strip() for r in resultado_texto.split(";") if r.strip()]
            resultados_info = [{"tipo_resultado": r} for r in resultados_sel]

        duracao_meses = st.number_input("Duração prevista (meses)", min_value=0, value=int(cadastro_atual["duracao_meses"]))
        valor_solicitado = st.number_input("Valor solicitado (R$)", min_value=0.0, value=float(cadastro_atual["valor_solicitado"]))

        if parceiros_opcoes:
            nomes_parceiros = list(parceiros_opcoes.keys())
            parceiros_sel = st.multiselect(
                "Parceiros principais",
                options=nomes_parceiros,
                default=[p for p in cadastro_atual["nomes_parceiros"] if p in nomes_parceiros]
            )
        else:
            parceiros_sel = []

        if publicos_opcoes:
            nomes_publicos = list(publicos_opcoes.keys())
            publicos_sel = st.multiselect(
                "Públicos-alvo",
                options=nomes_publicos,
                default=[p for p in cadastro_atual["nomes_publicos"] if p in nomes_publicos]
            )
        else:
            publicos_sel = []

    resumo = st.text_area("Resumo executivo da proposta", height=180, value=cadastro_atual["resumo"])
    anotacoes = st.text_area(
        "Anotações sobre a proposta",
        height=120,
        value=cadastro_atual.get("anotacoes", ""),
        placeholder="Registre pontos de atenção, dúvidas, hipóteses ou informações úteis para a avaliação.",
    )
    consideracoes = st.text_area(
        "Considerações adicionais",
        height=120,
        value=cadastro_atual.get("consideracoes", ""),
        placeholder="Inclua observações finais, ressalvas metodológicas ou recomendações preliminares.",
    )

    if st.button("Salvar dados e continuar para avaliação"):
        id_proposta = cadastro_atual.get("id_proposta") or gerar_id_proposta()
        ids_resultados = [r.get("id_resultado", "") for r in resultados_info if r.get("id_resultado", "")]
        categorias_resultados = [r.get("categoria_resultado", "") for r in resultados_info if r.get("categoria_resultado", "")]
        tipos_resultados = [r.get("tipo_resultado", "") for r in resultados_info if r.get("tipo_resultado", "")]
        comprovantes_resultados = [
            r.get("comprovante_entrega", r.get("comprovante_resultado", ""))
            for r in resultados_info
            if r.get("comprovante_entrega", r.get("comprovante_resultado", ""))
        ]
        exemplos_resultados = [
            r.get("exemplos", r.get("exemplos_resultado", ""))
            for r in resultados_info
            if r.get("exemplos", r.get("exemplos_resultado", ""))
        ]

        novo_cadastro = {
            "id_proposta": id_proposta,
            "titulo": titulo,
            "proponente": proponente,
            "equipe": " | ".join(equipe_sel),
            "ids_equipe": [empregados_opcoes[p] for p in equipe_sel] if empregados_opcoes else [],
            "nomes_equipe": equipe_sel,
            "id_unidade": unidades_opcoes.get(unidade_sel, "") if unidades_opcoes else "",
            "nome_unidade": unidade_sel,
            "id_area_tematica": areas_opcoes.get(area_sel, "") if areas_opcoes else "",
            "nome_area_tematica": area_sel,
            "portfolio": portfolio,
            "tipo_proposta": tipo_proposta,
            "ids_resultados": ids_resultados,
            "categorias_resultados": categorias_resultados,
            "tipos_resultados": tipos_resultados,
            "comprovantes_resultados": comprovantes_resultados,
            "exemplos_resultados": exemplos_resultados,
            "id_resultado": " | ".join(ids_resultados),
            "categoria_resultado": " | ".join(categorias_resultados),
            "tipo_resultado": " | ".join(tipos_resultados),
            "comprovante_resultado": " | ".join(comprovantes_resultados),
            "exemplos_resultado": " | ".join(exemplos_resultados),
            "duracao_meses": duracao_meses,
            "valor_solicitado": valor_solicitado,
            "ids_parceiros": [parceiros_opcoes[p] for p in parceiros_sel] if parceiros_opcoes else [],
            "nomes_parceiros": parceiros_sel,
            "ids_publicos": [publicos_opcoes[p] for p in publicos_sel] if publicos_opcoes else [],
            "nomes_publicos": publicos_sel,
            "resumo": resumo,
            "anotacoes": anotacoes,
            "consideracoes": consideracoes,
            "data_avaliacao": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }

        faltantes = validar_cadastro(novo_cadastro)

        if faltantes:
            st.error("Preencha os campos obrigatórios antes de continuar:")
            for item in faltantes:
                st.write(f"- {item}")
        else:
            st.session_state.cadastro = novo_cadastro
            st.session_state.etapa = 2
            st.rerun()

    with st.expander("Ver histórico já salvo"):
        if df_historico.empty:
            st.write("Ainda não há avaliações salvas.")
        else:
            colunas_visiveis = [c for c in [
                "timestamp_salvamento", "id_proposta", "titulo", "proponente",
                "nome_unidade", "nome_area_tematica", "indice_estrategico", "classificacao"
            ] if c in df_historico.columns]
            st.dataframe(df_historico[colunas_visiveis], width="stretch")

# =========================================================
# ETAPA 2
# =========================================================
elif st.session_state.etapa == 2:
    st.subheader("Etapa 2 — Avaliação da proposta")
    st.info("Responda às questões abaixo e depois clique em 'Calcular resultados'.")

    for dim in DIMENSOES:
        st.markdown(f"### {dim}")
        qs_dim = [q for q in QUESTOES if q["dimensao"] == dim]

        for q in qs_dim:
            codigo = q["codigo"]
            st.markdown(f"**{codigo}** — {q['pergunta']}")
            opcao_formatada = {k: f"{k} — {v}" for k, v in q["opcoes"].items()}

            st.session_state.scores[codigo] = st.radio(
                f"Selecione a resposta para {codigo}",
                options=list(opcao_formatada.keys()),
                format_func=lambda x: opcao_formatada[x],
                horizontal=True,
                index=st.session_state.scores[codigo] - 1,
                key=f"radio_{codigo}",
                label_visibility="collapsed",
            )

            with st.expander("Ver rubrica / âncora da questão"):
                for nota, texto in opcao_formatada.items():
                    st.write(f"{nota}: {texto}")

            with st.expander(f"Anotações do indicador {codigo}"):
                st.session_state.anotacoes_indicadores[codigo] = st.text_area(
                    f"Anotações para {codigo}",
                    value=st.session_state.anotacoes_indicadores.get(codigo, ""),
                    height=80,
                    key=f"nota_{codigo}",
                    label_visibility="collapsed",
                    placeholder="Registre uma justificativa, evidência ou dúvida específica deste indicador.",
                )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Voltar para dados da proposta"):
            st.session_state.etapa = 1
            st.rerun()

    with col2:
        if st.button("Calcular resultados"):
            st.session_state.resultados_calculados = True
            st.session_state.avaliacao_salva = False
            st.session_state.etapa = 3
            st.rerun()

# =========================================================
# ETAPA 3
# =========================================================
elif st.session_state.etapa == 3:
    if not st.session_state.resultados_calculados:
        st.warning("Os resultados ainda não foram calculados.")
        if st.button("Ir para avaliação"):
            st.session_state.etapa = 2
            st.rerun()
    else:
        st.subheader("Etapa 3 — Resultados da avaliação")
        cadastro = st.session_state.cadastro

        st.markdown("### Síntese da proposta")
        st.write(f"**ID:** {cadastro['id_proposta']}")
        st.write(f"**Título:** {cadastro['titulo']}")
        st.write(f"**Proponente:** {cadastro['proponente']}")
        st.write(f"**Equipe:** {', '.join(cadastro.get('nomes_equipe', [])) if cadastro.get('nomes_equipe') else cadastro.get('equipe', 'Não informada')}")
        st.write(f"**Unidade:** {cadastro['nome_unidade']}")
        st.write(f"**Área temática:** {cadastro['nome_area_tematica']}")
        st.write(
            f"**Resultados esperados:** {', '.join(cadastro.get('tipos_resultados', [])) if cadastro.get('tipos_resultados') else cadastro.get('tipo_resultado', 'Não informado')}"
        )
        if cadastro.get("categorias_resultados") or cadastro.get("categoria_resultado"):
            categorias = cadastro.get("categorias_resultados", [])
            st.write(f"**Categorias dos resultados:** {', '.join(categorias) if categorias else cadastro['categoria_resultado']}")
        st.write(f"**Parceiros:** {', '.join(cadastro['nomes_parceiros']) if cadastro['nomes_parceiros'] else 'Nenhum'}")
        st.write(f"**Públicos-alvo:** {', '.join(cadastro['nomes_publicos']) if cadastro['nomes_publicos'] else 'Nenhum'}")
        if cadastro.get("anotacoes"):
            st.write(f"**Anotações:** {cadastro['anotacoes']}")
        if cadastro.get("consideracoes"):
            st.write(f"**Considerações adicionais:** {cadastro['consideracoes']}")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Impacto potencial", indices["impacto_potencial"])
        c2.metric("Maturidade da trajetória", indices["maturidade_trajetoria"])
        c3.metric("Capacidade institucional", indices["capacidade_institucional"])
        c4.metric("Índice estratégico", indices["indice_estrategico"])

        st.markdown(f"### Classificação: **{indices['classificacao']}**")

        col_esq, col_dir = st.columns([1, 1])

        with col_esq:
            st.markdown("#### Pontuação por dimensão")
            st.dataframe(df_dimensoes, width="stretch")

        with col_dir:
            st.markdown("#### Perfil de impacto")
            fig = gerar_radar(dim_scores)
            st.plotly_chart(fig, width="stretch")

        st.markdown("#### Respostas detalhadas")
        st.dataframe(df_respostas, width="stretch")

        b1, b2, b3 = st.columns(3)

        with b1:
            if st.button("Voltar para avaliação"):
                st.session_state.etapa = 2
                st.rerun()

        with b2:
            if st.button("Salvar avaliação no histórico"):
                salvar_historico_csv(
                    cadastro=st.session_state.cadastro,
                    scores=st.session_state.scores,
                    dim_scores=dim_scores,
                    indices=indices,
                )
                supabase_ok, supabase_msg = salvar_historico_supabase(
                    cadastro=st.session_state.cadastro,
                    scores=st.session_state.scores,
                    dim_scores=dim_scores,
                    indices=indices,
                )
                st.session_state.avaliacao_salva = True
                st.success("Avaliação salva no histórico local com sucesso.")
                if supabase_ok:
                    st.success(supabase_msg)
                else:
                    st.info(supabase_msg)

        with b3:
            if st.button("Continuar para exportação"):
                st.session_state.etapa = 4
                st.rerun()

        if st.session_state.avaliacao_salva:
            st.info("Esta avaliação já foi salva no histórico nesta sessão.")

# =========================================================
# ETAPA 4
# =========================================================
elif st.session_state.etapa == 4:
    if not st.session_state.resultados_calculados:
        st.warning("Não há resultados disponíveis para exportação.")
        if st.button("Ir para avaliação"):
            st.session_state.etapa = 2
            st.rerun()
    else:
        st.subheader("Etapa 4 — Exportação e salvamento")
        cadastro = st.session_state.cadastro

        st.markdown("### Resumo da proposta")
        st.dataframe(montar_resumo_cadastro(cadastro), width="stretch", hide_index=True)
        st.markdown("### Arquivos para download")

        json_data = {
            "cadastro": cadastro,
            "scores": st.session_state.scores,
            "dim_scores": dim_scores,
            "indices": indices,
        }

        st.download_button(
            label="Baixar JSON completo",
            data=json.dumps(json_data, ensure_ascii=False, indent=2),
            file_name="avaliacao_ex_ante.json",
            mime="application/json",
        )

        csv_respostas = df_respostas.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            label="Baixar respostas em CSV",
            data=csv_respostas,
            file_name="respostas_avaliacao.csv",
            mime="text/csv",
        )

        excel_data = exportar_excel(df_respostas, df_dimensoes, df_resumo, cadastro)
        st.download_button(
            label="Baixar relatório em Excel",
            data=excel_data,
            file_name="avaliacao_ex_ante.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        st.markdown("### Histórico acumulado")
        df_historico = carregar_historico()

        if df_historico.empty:
            st.write("Ainda não há histórico salvo.")
        else:
            st.dataframe(df_historico, width="stretch")

            historico_csv_bytes = df_historico.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                label="Baixar histórico consolidado (CSV)",
                data=historico_csv_bytes,
                file_name="historico_avaliacoes.csv",
                mime="text/csv",
            )

            output_hist = BytesIO()
            with pd.ExcelWriter(output_hist, engine="openpyxl") as writer:
                df_historico.to_excel(writer, sheet_name="Histórico", index=False)

            st.download_button(
                label="Baixar histórico consolidado (Excel)",
                data=output_hist.getvalue(),
                file_name="historico_avaliacoes.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("Voltar para resultados"):
                st.session_state.etapa = 3
                st.rerun()

        with col2:
            if st.button("Abrir painel de governança"):
                st.session_state.etapa = 5
                st.rerun()

        with col3:
            if st.button("Iniciar nova avaliação"):
                resetar_avaliacao()
                st.rerun()

# =========================================================
# ETAPA 5
# =========================================================
elif st.session_state.etapa == 5:
    st.subheader("Etapa 5 — Governança das avaliações")
    st.caption("Área administrativa para consultar, filtrar e exportar avaliações salvas no Supabase.")

    if admin_autenticado():
        df_avaliacoes, erro_supabase = carregar_avaliacoes_supabase()

        if erro_supabase:
            st.error(erro_supabase)
        elif df_avaliacoes.empty:
            st.info("Ainda não há avaliações salvas no Supabase.")
        else:
            total = len(df_avaliacoes)
            media_indice = pd.to_numeric(df_avaliacoes["indice_estrategico"], errors="coerce").mean()
            ultima_data = df_avaliacoes["created_at"].max()

            c1, c2, c3 = st.columns(3)
            c1.metric("Avaliações salvas", total)
            c2.metric("Índice médio", round(media_indice, 2) if pd.notna(media_indice) else "-")
            c3.metric("Último registro", str(ultima_data)[:19])

            texto_busca = st.text_input("Buscar por título, proponente, unidade ou ID")
            df_filtrado = df_avaliacoes.copy()
            if texto_busca.strip():
                busca = texto_busca.strip().lower()
                colunas_busca = ["id_proposta", "titulo", "proponente", "unidade", "area_tematica", "portfolio"]
                mascara = df_filtrado[colunas_busca].fillna("").apply(
                    lambda linha: linha.astype(str).str.lower().str.contains(busca).any(),
                    axis=1,
                )
                df_filtrado = df_filtrado[mascara]

            colunas_visiveis = [
                "created_at",
                "id_proposta",
                "titulo",
                "proponente",
                "unidade",
                "area_tematica",
                "portfolio",
                "resultados",
                "indice_estrategico",
                "classificacao",
            ]
            st.dataframe(df_filtrado[colunas_visiveis], width="stretch", hide_index=True)

            csv_admin = df_filtrado.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                label="Baixar avaliações filtradas (CSV)",
                data=csv_admin,
                file_name="avaliacoes_terimpact.csv",
                mime="text/csv",
            )

            output_admin = BytesIO()
            with pd.ExcelWriter(output_admin, engine="openpyxl") as writer:
                df_filtrado.to_excel(writer, sheet_name="Avaliações", index=False)

            st.download_button(
                label="Baixar avaliações filtradas (Excel)",
                data=output_admin.getvalue(),
                file_name="avaliacoes_terimpact.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Voltar para dados da proposta"):
                st.session_state.etapa = 1
                st.rerun()
        with col2:
            if st.button("Sair do painel administrativo"):
                st.session_state.admin_autenticado = False
                st.rerun()
