
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Saúde em Foco — ABC Paulista",
    page_icon="🩺",
    layout="wide"
)

DADOS = Path(__file__).parent / "dados" / "tratados"


@st.cache_data
def ler(nome, **kw):
    return pd.read_csv(
        DADOS / nome,
        encoding="utf-8-sig",
        dtype={"codigo_ibge": str},
        **kw
    )


base = ler("base_municipal_saude_em_foco.csv")
dist = ler("distribuicao_populacao_registros_cnes.csv")
amb = ler("indicador_ambulatorial_sus.csv")
esf = ler("indicador_esfera_administrativa.csv")


tot_reg = base["quantidade_registros"].sum()
tot_pop = base["populacao_2022"].sum()

taxa_reg = tot_reg / tot_pop * 1e4

pearson = base["populacao_2022"].corr(
    base["quantidade_registros"]
)

spearman = base["populacao_2022"].corr(
    base["quantidade_registros"],
    method="spearman"
)


st.title("🩺 Saúde em Foco — ABC Paulista")

st.caption(
    "Distribuição de registros de estabelecimentos de saúde (CNES) "
    "frente à população (Censo 2022). "
    "Exploratório e municipal: não mede acesso, qualidade ou capacidade."
)


with st.sidebar:
    st.header("Filtros")

    sel = st.multiselect(
        "Municípios",
        base["municipio"].tolist(),
        default=base["municipio"].tolist()
    )

    st.markdown(
        "**Fontes:** CNES (Ministério da Saúde) e "
        "IBGE/SIDRA 4709 (Censo 2022)."
    )


if not sel:
    st.warning("Selecione ao menos um município.")
    st.stop()


b, d, a, e = (
    x[x["municipio"].isin(sel)]
    for x in (base, dist, amb, esf)
)


# ABAS DO DASHBOARD (SEM MAPA)

tabs = st.tabs([
    "Visão geral",
    "Taxa por habitante",
    "População × registros",
    "Ambulatorial SUS",
    "Correlação",
    "Limitações"
])


# ABA 1 — VISÃO GERAL

with tabs[0]:

    c = st.columns(4)

    c[0].metric(
        "Municípios",
        len(b)
    )

    c[1].metric(
        "Registros CNES",
        f"{b['quantidade_registros'].sum():,}".replace(",", ".")
    )

    c[2].metric(
        "População 2022",
        f"{b['populacao_2022'].sum():,}".replace(",", ".")
    )

    c[3].metric(
        "Registros / 10 mil hab. (ponderada)",
        f"{b['quantidade_registros'].sum() / b['populacao_2022'].sum() * 1e4:.2f}".replace(".", ",")
    )

    st.caption(
        f"Média simples entre os 7 municípios: "
        f"{base['registros_cnes_por_10mil_hab'].mean():.2f}; "
        f"taxa regional ponderada: {taxa_reg:.2f}."
    )

    st.plotly_chart(
        px.bar(
            b.sort_values("quantidade_registros"),
            x="quantidade_registros",
            y="municipio",
            orientation="h",
            text="quantidade_registros",
            labels={
                "quantidade_registros": "Registros CNES",
                "municipio": ""
            }
        ),
        width="stretch"
    )

    st.dataframe(
        b.drop(
            columns=["codigo_ibge", "uf", "codigo_cnes_6"]
        ).rename(
            columns={
                "municipio": "Município",
                "quantidade_registros": "Registros",
                "populacao_2022": "População 2022",
                "registros_cnes_por_10mil_hab": "Registros/10 mil hab."
            }
        ),
        hide_index=True,
        width="stretch"
    )


# ABA 2 — TAXA POR HABITANTE

with tabs[1]:

    st.subheader("H2 — Registros CNES por 10 mil habitantes")

    fig = px.bar(
        b.sort_values(
            "registros_cnes_por_10mil_hab",
            ascending=False
        ),
        x="municipio",
        y="registros_cnes_por_10mil_hab",
        text="registros_cnes_por_10mil_hab",
        labels={
            "registros_cnes_por_10mil_hab": "Registros por 10 mil hab.",
            "municipio": ""
        }
    )

    fig.add_hline(
        y=taxa_reg,
        line_dash="dash",
        annotation_text=f"Regional ponderada: {taxa_reg:.2f}"
    )

    fig.update_traces(
        texttemplate="%{text:.2f}"
    )

    st.plotly_chart(
        fig,
        width="stretch"
    )

    st.info(
        "São Caetano do Sul tem taxa muito superior às demais (90,79). "
        "É um ponto a investigar, não evidência de melhor acesso ou qualidade."
    )


# ABA 3 — POPULAÇÃO × REGISTROS

with tabs[2]:

    st.subheader(
        "Participação na população × participação nos registros"
    )

    m = d.melt(
        id_vars="municipio",
        value_vars=[
            "participacao_populacao_pct",
            "participacao_registros_cnes_pct"
        ],
        var_name="indicador",
        value_name="pct"
    )

    m["indicador"] = m["indicador"].map({
        "participacao_populacao_pct": "% da população",
        "participacao_registros_cnes_pct": "% dos registros CNES"
    })

    st.plotly_chart(
        px.bar(
            m,
            x="municipio",
            y="pct",
            color="indicador",
            barmode="group",
            labels={
                "pct": "%",
                "municipio": "",
                "indicador": ""
            }
        ),
        width="stretch"
    )

    st.dataframe(
        d[
            [
                "municipio",
                "participacao_populacao_pct",
                "participacao_registros_cnes_pct",
                "diferenca_participacao_pp",
                "indice_registros_vs_populacao"
            ]
        ].rename(
            columns={
                "municipio": "Município",
                "participacao_populacao_pct": "% pop.",
                "participacao_registros_cnes_pct": "% registros",
                "diferenca_participacao_pp": "Diferença (p.p.)",
                "indice_registros_vs_populacao": "Índice"
            }
        ),
        hide_index=True,
        width="stretch"
    )

    st.caption(
        "Índice = % dos registros ÷ % da população. "
        "Acima de 1: mais registros do que o peso populacional."
    )


# ABA 4 — AMBULATORIAL SUS

with tabs[3]:

    st.subheader(
        "Registros com CO_AMBULATORIAL_SUS = SIM"
    )

    st.caption(
        "Indica atendimento ambulatorial SUS apenas; "
        "não equivale à rede pública nem a todo atendimento SUS."
    )

    c1, c2 = st.columns(2)

    c1.plotly_chart(
        px.bar(
            a,
            x="municipio",
            y="percentual_ambulatorial_sus",
            text="percentual_ambulatorial_sus",
            labels={
                "percentual_ambulatorial_sus": "% do total de registros",
                "municipio": ""
            }
        ),
        width="stretch"
    )

    c2.plotly_chart(
        px.bar(
            a,
            x="municipio",
            y="registros_ambulatoriais_sus_por_10mil_hab",
            text="registros_ambulatoriais_sus_por_10mil_hab",
            labels={
                "registros_ambulatoriais_sus_por_10mil_hab": "Por 10 mil hab.",
                "municipio": ""
            }
        ),
        width="stretch"
    )

    st.dataframe(
        a.drop(columns="codigo_ibge"),
        hide_index=True,
        width="stretch"
    )

    with st.expander("Esfera administrativa (CNES)"):

        st.caption(
            "MUNICIPAL/ESTADUAL é a esfera informada no CNES; "
            "não classifica a rede como pública ou privada."
        )

        st.dataframe(
            e.drop(columns="codigo_ibge"),
            hide_index=True,
            width="stretch"
        )


# ABA 5 — CORRELAÇÃO

with tabs[4]:

    st.subheader(
        "H3 — Associação exploratória entre população e registros"
    )

    c = st.columns(2)

    c[0].metric(
        "Pearson",
        f"{pearson:.3f}".replace(".", ",")
    )

    c[1].metric(
        "Spearman",
        f"{spearman:.3f}".replace(".", ",")
    )

    st.plotly_chart(
        px.scatter(
            base,
            x="populacao_2022",
            y="quantidade_registros",
            text="municipio",
            labels={
                "populacao_2022": "População 2022",
                "quantidade_registros": "Registros CNES"
            }
        ).update_traces(
            textposition="top center",
            marker_size=11
        ),
        width="stretch"
    )

    st.warning(
        "Apenas 7 municípios: correlação é exploratória, "
        "não demonstra causalidade. "
        "H4 (relação com produção de serviços) não foi testada."
    )


# ABA 6 — LIMITAÇÕES

with tabs[5]:

    st.subheader(
        "Limitações e cuidados de interpretação"
    )

    st.markdown("""
- A contagem de registros CNES **não** mede capacidade, qualidade, acesso ou suficiência dos serviços.
- O CNES inclui estabelecimentos públicos e privados; **não** rotulamos os 6.290 registros como públicos.
- `CO_AMBULATORIAL_SUS` refere-se só a atendimento ambulatorial SUS.
- `CO_MOTIVO_DESAB` está preenchido em 1.663 registros; a situação de atividade não foi confirmada, então os indicadores descrevem **registros cadastrados**.
- A competência do CNES pode diferir do ano do Censo 2022 (população).
- Análise **municipal**: não permite conclusões por bairro.
- Correlação ≠ causalidade; n = 7. H3 é exploratória e H4 não foi testada.
- Junção CNES × IBGE pelos 6 primeiros dígitos do código municipal.
""")
