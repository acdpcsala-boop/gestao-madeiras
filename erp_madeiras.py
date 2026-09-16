import streamlit as st
import pandas as pd
from google import genai
import os

# -----------------------------------------------------------------------------
# Configuração da Página
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Gestão de Madeiras & Luthieria",
    page_icon="🪵",
    layout="wide"
)

st.title("🪵 Sistema Integrado de Gestão - Madeiras & Luthieria")

# -----------------------------------------------------------------------------
# Configuração da API do Gemini
# -----------------------------------------------------------------------------
gemini_api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")

client = None
if gemini_api_key:
    try:
        client = genai.Client(api_key=gemini_api_key)
    except Exception as e:
        st.error(f"Erro ao inicializar o cliente do Gemini: {e}")

# -----------------------------------------------------------------------------
# Inicialização dos Dados em Sessão (Módulos do Sistema)
# -----------------------------------------------------------------------------
if "estoque_madeiras" not in st.session_state:
    st.session_state.estoque_madeiras = pd.DataFrame([
        {"Espécie": "Marfim", "Tipo": "Braço", "Quantidade": 12, "Preço Un. (R$)": 85.00},
        {"Espécie": "Jatobá", "Tipo": "Escala", "Quantidade": 25, "Preço Un. (R$)": 40.00},
        {"Espécie": "Cedar (Cedro Rosa)", "Tipo": "Corpo", "Quantidade": 8, "Preço Un. (R$)": 210.00}
    ])

if "maquinas_ferramentas" not in st.session_state:
    st.session_state.maquinas_ferramentas = [
        {"nome": "serra fita Razi", "categoria": "Corte", "status": "Inoperante/Quebrada", "desc_defeito": "Correia do volante está frouxa e faz a lâmina escapar"}
    ]

if "financeiro" not in st.session_state:
    st.session_state.financeiro = pd.DataFrame([
        {"Data": "2026-03-01", "Tipo": "Receita", "Descrição": "Regulagem completa Guit. Ibanez", "Valor (R$)": 250.00},
        {"Data": "2026-03-02", "Tipo": "Despesa", "Descrição": "Compra de lâminas serra fita", "Valor (R$)": 120.00}
    ])

# -----------------------------------------------------------------------------
# Navegação por Abas
# -----------------------------------------------------------------------------
aba_estoque, aba_maquinas, aba_financeiro, aba_ia = st.tabs([
    "🪵 Estoque de Madeiras", 
    "⚙️ Máquinas & Ferramentas", 
    "💰 Fluxo de Caixa", 
    "🤖 Assistente Técnico IA"
])

# -----------------------------------------------------------------------------
# ABA 1: Estoque de Madeiras
# -----------------------------------------------------------------------------
with aba_estoque:
    st.header("Estoque de Madeiras e Insumos")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Itens Cadastrados")
        st.dataframe(st.session_state.estoque_madeiras, use_container_width=True)
        
    with col2:
        st.subheader("Adicionar Madeira")
        with st.form("form_madeira"):
            especie = st.text_input("Espécie (ex: Cedro, Jacarandá)")
            tipo = st.selectbox("Destinação", ["Corpo", "Braço", "Escala", "Tampo", "Outro"])
            qtd = st.number_input("Quantidade", min_value=1, step=1, value=1)
            preco = st.number_input("Preço Unitário (R$)", min_value=0.0, step=5.0, value=50.0)
            
            if st.form_submit_button("Cadastrar Insumo"):
                novo_item = pd.DataFrame([{"Espécie": especie, "Tipo": tipo, "Quantidade": qtd, "Preço Un. (R$)": preco}])
                st.session_state.estoque_madeiras = pd.concat([st.session_state.estoque_madeiras, novo_item], ignore_index=True)
                st.success("Item adicionado ao estoque!")
                st.rerun()

# -----------------------------------------------------------------------------
# ABA 2: Máquinas & Ferramentas
# -----------------------------------------------------------------------------
with aba_maquinas:
    st.header("Status e Manutenção de Equipamentos")
    col_cad, col_list = st.columns([1, 1])
    
    with col_cad:
        st.subheader("Cadastrar Nova Máquina / Ferramenta")
        with st.form("form_maquina"):
            nome_maq = st.text_input("Nome da Máquina / Ferramenta")
            categoria_maq = st.selectbox("Categoria", ["Corte", "Lixamento", "Medição/Precisão", "Tupia/Usinagem", "Outro"])
            status_maq = st.selectbox("Status Atual", ["Operacional", "Manutenção Preventiva", "Inoperante/Quebrada"])
            defeito_maq = st.text_area("Descrição do Defeito / Observação (Opcional)")
            
            if st.form_submit_button("Cadastrar Máquina") and nome_maq:
                st.session_state.maquinas_ferramentas.append({
                    "nome": nome_maq,
                    "categoria": categoria_maq,
                    "status": status_maq,
                    "desc_defeito": defeito_maq
                })
                st.success("Equipamento cadastrado com sucesso!")
                st.rerun()
                
    with col_list:
        st.subheader("Status Das Máquinas e Ferramentas")
        for idx, item in enumerate(st.session_state.maquinas_ferramentas):
            cor_status = "🔴" if "Quebrada" in item["status"] else ("🟡" if "Preventiva" in item["status"] else "🟢")
            with st.expander(f"{cor_status} {item['nome']} - {item['categoria']}"):
                st.write(f"**Status:** {item['status']}")
                if item["desc_defeito"]:
                    st.write(f"**Observação/Defeito:** {item['desc_defeito']}")
                
                if st.button(f"🔍 Diagnosticar Defeito com IA ({item['nome']})", key=f"diag_{idx}"):
                    if not client:
                        st.error("Chave de API do Gemini não configurada em Secrets.")
                    else:
                        prompt = (
                            f"Você é um técnico especialista em manutenção de máquinas para marcenaria e luthieria. "
                            f"Analise o seguinte equipamento:\n"
                            f"**Equipamento:** {item['nome']} ({item['categoria']})\n"
                            f"**Problema relatado:** {item['desc_defeito'] or 'Manutenção geral'}\n\n"
                            f"Forneça:\n1. Possíveis causas do problema.\n2. Passo a passo detalhado para solução.\n3. Recomendações preventivas."
                        )
                        with st.spinner("Analisando defeito com o Gemini..."):
                            try:
                                response = client.models.generate_content(
                                    model="gemini-1.5-flash",
                                    contents=prompt
                                )
                                st.markdown("---")
                                st.markdown("#### 💡 Diagnóstico e Instruções da IA:")
                                st.info(response.text)
                            except Exception as e:
                                st.error(f"Erro ao processar diagnóstico: {e}")

# -----------------------------------------------------------------------------
# ABA 3: Fluxo de Caixa / Financeiro
# -----------------------------------------------------------------------------
with aba_financeiro:
    st.header("Controle Financeiro da Luthieria")
    df_fin = st.session_state.financeiro
    receita_total = df_fin[df_fin["Tipo"] == "Receita"]["Valor (R$)"].sum()
    despesa_total = df_fin[df_fin["Tipo"] == "Despesa"]["Valor (R$)"].sum()
    saldo = receita_total - despesa_total
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Receita Bruta", f"R$ {receita_total:.2f}")
    c2.metric("Despesas Totais", f"R$ {despesa_total:.2f}")
    c3.metric("Saldo Líquido", f"R$ {saldo:.2f}", delta=f"{saldo:.2f}")
    
    st.subheader("Lançamentos")
    st.dataframe(df_fin, use_container_width=True)

# -----------------------------------------------------------------------------
# ABA 4: Assistente Técnico IA
# -----------------------------------------------------------------------------
with aba_ia:
    st.header("🤖 Consultoria Técnica em Luthieria & Madeiras")
    duvida = st.text_area("Digite sua dúvida técnica:")
    if st.button("Consultar IA"):
        if not duvida:
            st.warning("Digite uma dúvida antes de enviar.")
        elif not client:
            st.error("Chave de API do Gemini não configurada.")
        else:
            with st.spinner("Consultando conhecimento técnico..."):
                try:
                    response = client.models.generate_content(
                        model="gemini-3.6-flash",
                        contents=duvida
                    )
                    st.markdown("### Resposta da IA:")
                    st.success(response.text)
                except Exception as e:
                    st.error(f"Erro na consulta: {e}")
