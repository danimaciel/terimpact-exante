import os
import json
from io import BytesIO
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
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

# =========================================================
# SESSION STATE
# =========================================================
if "etapa" not in st.session_state:
    st.session_state.etapa = 1

if "scores" not in st.session_state:
    st.session_state.scores = {}

if "cadastro" not in st.session_state:
    st.session_state.cadastro = {
        "id_proposta": "",
        "titulo": "",
        "proponente": "",
        "equipe": "",
        "id_unidade": "",
        "nome_unidade": "",
        "id_area_tematica": "",
        "nome_area_tematica": "",
        "portfolio": "",
        "tipo_proposta": "",
        "duracao_meses": 36,
        "valor_solicitado": 0.0,
        "ids_parceiros": [],
        "nomes_parceiros": [],
        "ids_publicos": [],
        "nomes_publicos": [],
        "resumo": "",
        "data_avaliacao": "",
    }

if "resultados_calculados" not in st.session_state:
    st.session_state.resultados_calculados = False

if "avaliacao_salva" not in st.session_state:
    st.session_state.avaliacao_salva = False

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

# =========================================================
# FUNÇÕES
# =========================================================
def validar_cadastro(cadastro):
    obrigatorios = {
        "id_proposta": "ID da proposta",
        "titulo": "Título",
        "proponente": "Proponente",
        "nome_unidade": "Unidade",
        "nome_area_tematica": "Área temática",
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


def montar_dataframe_respostas(scores_dict):
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


def montar_linha_historico(cadastro, scores, dim_scores, indices):
    linha = {}
    linha.update(cadastro)
    linha["ids_parceiros"] = " | ".join(cadastro.get("ids_parceiros", []))
    linha["nomes_parceiros"] = " | ".join(cadastro.get("nomes_parceiros", []))
    linha["ids_publicos"] = " | ".join(cadastro.get("ids_publicos", []))
    linha["nomes_publicos"] = " | ".join(cadastro.get("nomes_publicos", []))
    linha["timestamp_salvamento"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for q in QUESTOES:
        codigo = q["codigo"]
        linha[f"score_{codigo}"] = scores[codigo]
        linha[f"desc_{codigo}"] = q["opcoes"][scores[codigo]]

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


def carregar_historico(caminho_csv=HISTORICO_CSV):
    if os.path.exists(caminho_csv):
        return pd.read_csv(caminho_csv)
    return pd.DataFrame()


def resetar_avaliacao():
    st.session_state.etapa = 1
    st.session_state.resultados_calculados = False
    st.session_state.avaliacao_salva = False
    st.session_state.cadastro = {
        "id_proposta": "",
        "titulo": "",
        "proponente": "",
        "equipe": "",
        "id_unidade": "",
        "nome_unidade": "",
        "id_area_tematica": "",
        "nome_area_tematica": "",
        "portfolio": "",
        "tipo_proposta": "",
        "duracao_meses": 36,
        "valor_solicitado": 0.0,
        "ids_parceiros": [],
        "nomes_parceiros": [],
        "ids_publicos": [],
        "nomes_publicos": [],
        "resumo": "",
        "data_avaliacao": "",
    }
    st.session_state.scores = {q["codigo"]: 3 for q in QUESTOES}


# =========================================================
# CÁLCULOS
# =========================================================
dim_scores = calcular_dimensoes(st.session_state.scores)
indices = calcular_indices(dim_scores)
df_respostas = montar_dataframe_respostas(st.session_state.scores)
df_dimensoes = pd.DataFrame([{"Dimensão": k, "Pontuação média": v} for k, v in dim_scores.items()])
df_resumo = pd.DataFrame([indices])
df_historico = carregar_historico()

# =========================================================
# TOPO
# =========================================================
st.title("Avaliação ex ante de propostas – Embrapa Territorial")
st.caption("Versão 2.3 – fluxo guiado + histórico + tabelas-base relacionais")

nomes_etapas = {
    1: "Dados da proposta",
    2: "Avaliação",
    3: "Resultados",
    4: "Exportação",
}

st.progress(st.session_state.etapa / 4)
st.markdown(f"**Etapa {st.session_state.etapa} de 4 — {nomes_etapas[st.session_state.etapa]}**")

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

    with col1:
        id_proposta = st.text_input("ID da proposta", value=cadastro_atual["id_proposta"])
        titulo = st.text_input("Título da proposta", value=cadastro_atual["titulo"])
        proponente = st.text_input("Nome do proponente", value=cadastro_atual["proponente"])
        equipe = st.text_input("Equipe responsável", value=cadastro_atual["equipe"])

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
        portfolio = st.text_input("Portfólio / programa", value=cadastro_atual["portfolio"])
        tipo_proposta = st.selectbox(
            "Tipo de proposta",
            ["", "Pesquisa", "Desenvolvimento", "Inovação", "Serviço", "Outro"],
            index=["", "Pesquisa", "Desenvolvimento", "Inovação", "Serviço", "Outro"].index(cadastro_atual["tipo_proposta"])
            if cadastro_atual["tipo_proposta"] in ["", "Pesquisa", "Desenvolvimento", "Inovação", "Serviço", "Outro"] else 0,
        )
        duracao_meses = st.number_input("Duração prevista (meses)", min_value=0, value=int(cadastro_atual["duracao_meses"]))
        valor_solicitado = st.number_input("Valor solicitado (R$)", min_value=0.0, value=float(cadastro_atual["valor_solicitado"]))

        if parceiros_opcoes:
            nomes_parceiros = list(parceiros_opcoes.keys())
            parceiros_sel = st.multiselect(
                "Parceiros principais",
                options=nomes_parceiros,
                default=cadastro_atual["nomes_parceiros"]
            )
        else:
            parceiros_sel = []

        if publicos_opcoes:
            nomes_publicos = list(publicos_opcoes.keys())
            publicos_sel = st.multiselect(
                "Públicos-alvo",
                options=nomes_publicos,
                default=cadastro_atual["nomes_publicos"]
            )
        else:
            publicos_sel = []

    resumo = st.text_area("Resumo executivo da proposta", height=180, value=cadastro_atual["resumo"])

    if st.button("Salvar dados e continuar para avaliação"):
        novo_cadastro = {
            "id_proposta": id_proposta,
            "titulo": titulo,
            "proponente": proponente,
            "equipe": equipe,
            "id_unidade": unidades_opcoes.get(unidade_sel, "") if unidades_opcoes else "",
            "nome_unidade": unidade_sel,
            "id_area_tematica": areas_opcoes.get(area_sel, "") if areas_opcoes else "",
            "nome_area_tematica": area_sel,
            "portfolio": portfolio,
            "tipo_proposta": tipo_proposta,
            "duracao_meses": duracao_meses,
            "valor_solicitado": valor_solicitado,
            "ids_parceiros": [parceiros_opcoes[p] for p in parceiros_sel] if parceiros_opcoes else [],
            "nomes_parceiros": parceiros_sel,
            "ids_publicos": [publicos_opcoes[p] for p in publicos_sel] if publicos_opcoes else [],
            "nomes_publicos": publicos_sel,
            "resumo": resumo,
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
            st.dataframe(df_historico[colunas_visiveis], use_container_width=True)

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
        st.write(f"**Unidade:** {cadastro['nome_unidade']}")
        st.write(f"**Área temática:** {cadastro['nome_area_tematica']}")
        st.write(f"**Parceiros:** {', '.join(cadastro['nomes_parceiros']) if cadastro['nomes_parceiros'] else 'Nenhum'}")
        st.write(f"**Públicos-alvo:** {', '.join(cadastro['nomes_publicos']) if cadastro['nomes_publicos'] else 'Nenhum'}")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Impacto potencial", indices["impacto_potencial"])
        c2.metric("Maturidade da trajetória", indices["maturidade_trajetoria"])
        c3.metric("Capacidade institucional", indices["capacidade_institucional"])
        c4.metric("Índice estratégico", indices["indice_estrategico"])

        st.markdown(f"### Classificação: **{indices['classificacao']}**")

        col_esq, col_dir = st.columns([1, 1])

        with col_esq:
            st.markdown("#### Pontuação por dimensão")
            st.dataframe(df_dimensoes, use_container_width=True)

        with col_dir:
            st.markdown("#### Perfil de impacto")
            fig = gerar_radar(dim_scores)
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("#### Respostas detalhadas")
        st.dataframe(df_respostas, use_container_width=True)

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
                st.session_state.avaliacao_salva = True
                st.success("Avaliação salva no histórico com sucesso.")

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
        st.json(cadastro)

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
            st.dataframe(df_historico, use_container_width=True)

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

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Voltar para resultados"):
                st.session_state.etapa = 3
                st.rerun()

        with col2:
            if st.button("Iniciar nova avaliação"):
                resetar_avaliacao()
                st.rerun()