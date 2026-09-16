import sqlite3
from google import genai
import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Gestão Madeiras & Luthieria", page_icon="🪵", layout="wide"
)

# -----------------------------------------------------------------------------
# Configuração e Conexão com o Gemini (via Secrets do Streamlit)
# -----------------------------------------------------------------------------
api_key = st.secrets.get("GEMINI_API_KEY")

if api_key:
    client = genai.Client(api_key=api_key)
else:
    client = None
    st.warning(
        "⚠️ Chave 'GEMINI_API_KEY' não encontrada nos Secrets do Streamlit Cloud."
    )

# -----------------------------------------------------------------------------
# Banco de Dados (SQLite)
# -----------------------------------------------------------------------------
conn = sqlite3.connect("gestao_madeiras.db", check_same_thread=False)
cursor = conn.cursor()

# Criação da tabela de máquinas/ferramentas caso não exista
cursor.execute("""
CREATE TABLE IF NOT EXISTS maquinas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    categoria TEXT NOT NULL,
    status TEXT NOT NULL,
    defeito TEXT
)
""")
conn.commit()

# -----------------------------------------------------------------------------
# Interface do Usuário (Streamlit)
# -----------------------------------------------------------------------------
st.title("🪵 Gestão de Madeiras, Máquinas e Ferramentas")
st.markdown("---")

st.subheader("➕ Cadastrar Nova Máquina / Ferramenta")

with st.form("form_maquina", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        nome_maq = st.text_input("Nome da Máquina / Ferramenta")
        categoria_maq = st.selectbox(
            "Categoria",
            ["Corte", "Lixamento", "Usinagem/CNC", "Manual", "Outros"],
        )
    with col2:
        status_maq = st.selectbox(
            "Status Atual", ["Funcionando", "Requer Atenção", "Inoperante/Quebrada"]
        )
        defeito_maq = st.text_area(
            "Descrição do Defeito / Observação (Opcional)"
        )

    btn_cadastrar = st.form_submit_button("Cadastrar Máquina")

if btn_cadastrar:
    if nome_maq:
        cursor.execute(
            "INSERT INTO maquinas (nome, categoria, status, defeito) VALUES (?, ?, ?, ?)",
            (nome_maq, categoria_maq, status_maq, defeito_maq),
        )
        conn.commit()
        st.success(f"Máquina '{nome_maq}' cadastrada com sucesso!")
        st.rerun()
    else:
        st.error("Por favor, preencha o nome da máquina.")

st.divider()

# -----------------------------------------------------------------------------
# Exibição das Máquinas e Diagnóstico de IA
# -----------------------------------------------------------------------------
st.subheader("📋 Status Das Máquinas e Ferramentas")
cursor.execute("SELECT id, nome, categoria, status, defeito FROM maquinas")
maquinas = cursor.fetchall()

if maquinas:
    for maq in maquinas:
        id_m, nome, cat, status, desc_defeito = maq

        # Definição de ícones de status
        cor = (
            "🟢"
            if status == "Funcionando"
            else "🟡" if status == "Requer Atenção" else "🔴"
        )

        st.markdown(f"### {cor} {nome} - *{cat}*")
        st.write(f"**Status:** {status}")

        if desc_defeito:
            st.warning(f"**Observação/Defeito:** {desc_defeito}")

            # Botão para acionar a IA do Gemini
            if st.button(
                f"🤖 Diagnosticar Defeito com IA ({nome})", key=f"btn_{id_m}"
            ):
                if not client:
                    st.error(
                        "Não foi possível acionar a IA. Configure a GEMINI_API_KEY nos Secrets."
                    )
                else:
                    with st.spinner("Analisando defeito com o Gemini..."):
                        try:
                            prompt = (
                                f"Você é um técnico especialista em manutenção de máquinas e ferramentas "
                                f"de marcenaria e luthieria. Analise o seguinte problema:\n\n"
                                f"**Equipamento:** {nome} ({cat})\n"
                                f"**Problema relatado:** {desc_defeito}\n\n"
                                f"Forneça:\n"
                                f"1. Possíveis causas do problema.\n"
                                f"2. Passo a passo detalhado e seguro para solução/conserto.\n"
                                f"3. Recomendações de manutenção preventiva."
                            )

                            response = client.models.generate_content(
                                model="gemini-1.5-flash", contents=prompt
                            )

                            st.markdown("---")
                            st.markdown("#### 💡 Diagnóstico e Instruções da IA:")
                            st.info(response.text)
                        except Exception as e:
                            st.error(f"Erro ao processar diagnóstico: {e}")
        st.divider()
else:
    st.info("Nenhuma máquina cadastrada no momento.")
