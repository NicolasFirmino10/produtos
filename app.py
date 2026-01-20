import streamlit as st
import pandas as pd
from io import BytesIO
import os

st.set_page_config(page_title="Controle de Itens", layout="wide")
st.title("📦 Controle de Estoque / Compras")

ARQUIVO_CSV = "dados_salvos.csv"

# =============================
# 🔄 CARREGAMENTO INICIAL
# =============================
if "itens" not in st.session_state:
    if os.path.exists(ARQUIVO_CSV):
        df_salvo = pd.read_csv(ARQUIVO_CSV)

        # 🔒 Tratamento seguro dos tipos
        df_salvo["Caixas"] = pd.to_numeric(df_salvo["Caixas"], errors="coerce").fillna(0).astype(int)
        df_salvo["Unidades por Caixa"] = pd.to_numeric(
            df_salvo["Unidades por Caixa"], errors="coerce"
        ).fillna(0).astype(int)
        df_salvo["Preço Unitário (R$)"] = pd.to_numeric(
            df_salvo["Preço Unitário (R$)"], errors="coerce"
        ).fillna(0.0)

        st.session_state.itens = []
        for _, row in df_salvo.iterrows():
            st.session_state.itens.append({
                "item": row["Item"],
                "caixas": row["Caixas"],
                "unidades": row["Unidades por Caixa"],
                "preco": row["Preço Unitário (R$)"]
            })
    else:
        st.session_state.itens = [{
            "item": "",
            "caixas": 0,
            "unidades": 0,
            "preco": 0.0
        }]

st.write("Preencha os dados. Os cálculos são automáticos.")

dados = []

# =============================
# 🧾 LISTA DE ITENS
# =============================
for i in range(len(st.session_state.itens)):
    st.subheader(f"Item {i + 1}")

    col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 0.5])

    item = col1.text_input(
        "Nome do Item",
        value=st.session_state.itens[i]["item"],
        key=f"item_{i}"
    )

    caixas = col2.number_input(
        "Caixas",
        min_value=0,
        step=1,
        value=int(st.session_state.itens[i]["caixas"]),
        key=f"caixas_{i}"
    )

    unidades_por_caixa = col3.number_input(
        "Unidades por Caixa",
        min_value=0,
        step=1,
        value=int(st.session_state.itens[i]["unidades"]),
        key=f"unidades_{i}"
    )

    preco_unitario = col4.number_input(
        "Preço Unitário (R$)",
        min_value=0.0,
        step=0.01,
        value=float(st.session_state.itens[i]["preco"]),
        key=f"preco_{i}"
    )

    excluir = col5.button("🗑️", key=f"delete_{i}")

    if excluir:
        st.session_state.itens.pop(i)
        st.rerun()

    total_unidades = caixas * unidades_por_caixa
    valor_total = total_unidades * preco_unitario

    dados.append({
        "Item": item,
        "Caixas": caixas,
        "Unidades por Caixa": unidades_por_caixa,
        "Total de Unidades": total_unidades,
        "Preço Unitário (R$)": preco_unitario,
        "Valor Total (R$)": valor_total
    })

    st.session_state.itens[i] = {
        "item": item,
        "caixas": caixas,
        "unidades": unidades_por_caixa,
        "preco": preco_unitario
    }

# =============================
# ➕ ADICIONAR ITEM
# =============================
st.divider()

if st.button("➕ Adicionar novo item"):
    st.session_state.itens.append({
        "item": "",
        "caixas": 0,
        "unidades": 0,
        "preco": 0.0
    })
    st.rerun()

# =============================
# 📊 RESUMO + SALVAMENTO
# =============================
df = pd.DataFrame(dados)

if not df.empty:
    # Remove itens sem nome
    df = df[df["Item"].str.strip() != ""]

    df.to_csv(ARQUIVO_CSV, index=False)

    st.divider()
    st.subheader("📊 Resumo")
    st.dataframe(df, use_container_width=True)

    total_caixas = df["Caixas"].sum()
    total_unidades = df["Total de Unidades"].sum()
    valor_geral = df["Valor Total (R$)"].sum()

    st.subheader("🧮 Totais Gerais")
    col1, col2, col3 = st.columns(3)

    col1.metric("Total de Caixas", int(total_caixas))
    col2.metric("Total de Unidades", int(total_unidades))
    col3.metric("Valor Total Geral (R$)", f"{valor_geral:,.2f}")

    # =============================
    # 📥 DOWNLOAD EXCEL
    # =============================
    def gerar_excel(dataframe):
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            dataframe.to_excel(writer, index=False, sheet_name="Resumo")
        buffer.seek(0)
        return buffer

    st.download_button(
        label="⬇️ Baixar Planilha Excel",
        data=gerar_excel(df),
        file_name="controle_itens.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
