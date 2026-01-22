import streamlit as st
import pandas as pd
from io import BytesIO
import os

# =============================
# ⚙️ CONFIGURAÇÕES
# =============================
st.set_page_config(page_title="Controle de Itens", layout="wide")
st.title("📦 Controle de Estoque / Compras")

ARQUIVO_CSV = "dados_salvos.csv"
MARGEM_PADRAO = 0.35  # 35%

# =============================
# 🔄 CARREGAMENTO INICIAL
# =============================
if "itens" not in st.session_state:
    if os.path.exists(ARQUIVO_CSV):
        df_salvo = pd.read_csv(ARQUIVO_CSV)

        if "Preço Unitário (R$)" in df_salvo.columns:
            df_salvo.rename(columns={
                "Preço Unitário (R$)": "Preço Unitário Compra (R$)"
            }, inplace=True)

        if "Margem (%)" not in df_salvo.columns:
            df_salvo["Margem (%)"] = MARGEM_PADRAO * 100

        df_salvo["Caixas"] = pd.to_numeric(df_salvo.get("Caixas", 0), errors="coerce").fillna(0).astype(int)
        df_salvo["Unidades por Caixa"] = pd.to_numeric(
            df_salvo.get("Unidades por Caixa", 0), errors="coerce"
        ).fillna(0).astype(int)

        df_salvo["Preço Unitário Compra (R$)"] = pd.to_numeric(
            df_salvo.get("Preço Unitário Compra (R$)", 0.0), errors="coerce"
        ).fillna(0.0)

        df_salvo["Margem (%)"] = pd.to_numeric(
            df_salvo.get("Margem (%)", MARGEM_PADRAO * 100), errors="coerce"
        ).fillna(MARGEM_PADRAO * 100)

        st.session_state.itens = []
        for _, row in df_salvo.iterrows():
            st.session_state.itens.append({
                "item": row.get("Item", ""),
                "caixas": row["Caixas"],
                "unidades": row["Unidades por Caixa"],
                "preco": row["Preço Unitário Compra (R$)"],
                "margem": row["Margem (%)"] / 100
            })
    else:
        st.session_state.itens = [{
            "item": "",
            "caixas": 0,
            "unidades": 0,
            "preco": 0.0,
            "margem": MARGEM_PADRAO
        }]

st.write("Cada produto possui **margem própria** e os **resultados aparecem em tempo real**.")

dados = []

# =============================
# 🧾 ITENS
# =============================
for i in range(len(st.session_state.itens)):
    st.subheader(f"📦 Item {i + 1}")

    col1, col2, col3, col4, col5, col6 = st.columns([3, 1, 1, 1, 1, 0.5])

    item = col1.text_input("Nome", st.session_state.itens[i]["item"], key=f"item_{i}")
    caixas = col2.number_input("Caixas", 0, step=1, value=int(st.session_state.itens[i]["caixas"]), key=f"caixas_{i}")
    unidades = col3.number_input("Unid/Caixa", 0, step=1, value=int(st.session_state.itens[i]["unidades"]), key=f"unidades_{i}")
    preco = col4.number_input("Preço Compra", 0.0, step=0.01, value=float(st.session_state.itens[i]["preco"]), key=f"preco_{i}")
    margem = col5.number_input("Margem (%)", 0.0, 90.0, value=float(st.session_state.itens[i]["margem"] * 100), key=f"margem_{i}")
    excluir = col6.button("🗑️", key=f"delete_{i}")

    if excluir:
        st.session_state.itens.pop(i)
        st.rerun()

    # =============================
    # 📊 CÁLCULOS
    # =============================
    margem_dec = margem / 100
    total_unidades = caixas * unidades
    valor_compra = total_unidades * preco
    preco_venda = preco / (1 - margem_dec) if margem_dec < 1 else 0
    valor_venda = total_unidades * preco_venda
    lucro = valor_venda - valor_compra

    # =============================
    # 📌 RESULTADO VISUAL DO ITEM
    # =============================
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Preço Venda (R$)", f"{preco_venda:,.2f}")
    c2.metric("Total Compra (R$)", f"{valor_compra:,.2f}")
    c3.metric("Total Venda (R$)", f"{valor_venda:,.2f}")
    c4.metric("Lucro (R$)", f"{lucro:,.2f}")

    st.divider()

    dados.append({
        "Item": item,
        "Caixas": caixas,
        "Unidades por Caixa": unidades,
        "Total de Unidades": total_unidades,
        "Preço Unitário Compra (R$)": round(preco, 2),
        "Margem (%)": round(margem, 2),
        "Preço Unitário Venda (R$)": round(preco_venda, 2),
        "Valor Total Compra (R$)": round(valor_compra, 2),
        "Valor Total Venda (R$)": round(valor_venda, 2),
        "Lucro Total (R$)": round(lucro, 2)
    })

    st.session_state.itens[i] = {
        "item": item,
        "caixas": caixas,
        "unidades": unidades,
        "preco": preco,
        "margem": margem_dec
    }

# =============================
# ➕ NOVO ITEM
# =============================
if st.button("➕ Adicionar novo item"):
    st.session_state.itens.append({
        "item": "",
        "caixas": 0,
        "unidades": 0,
        "preco": 0.0,
        "margem": MARGEM_PADRAO
    })
    st.rerun()

# =============================
# 📊 RESUMO FINAL
# =============================
df = pd.DataFrame(dados)

if not df.empty:
    df = df[df["Item"].str.strip() != ""]
    df.to_csv(ARQUIVO_CSV, index=False)

    st.subheader("📊 Resumo Geral")
    st.dataframe(df, use_container_width=True)

    st.subheader("🧮 Totais Gerais")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Compra (R$)", f"{df['Valor Total Compra (R$)'].sum():,.2f}")
    col2.metric("Total Venda (R$)", f"{df['Valor Total Venda (R$)'].sum():,.2f}")
    col3.metric("Lucro Total (R$)", f"{df['Lucro Total (R$)'].sum():,.2f}")

    def gerar_excel(df):
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Resumo")
        buffer.seek(0)
        return buffer

    st.download_button(
        "⬇️ Baixar Excel",
        gerar_excel(df),
        "controle_itens.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
