import streamlit as st
import pandas as pd
from google import genai
from streamlit_gsheets import GSheetsConnection
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
# Configuração das Conexões (Google Sheets e Gemini API)
# -----------------------------------------------------------------------------
spreadsheet_url = st.secrets.get("SPREADSHEET_URL")
gemini_api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")

client = None
if gemini_api_key:
    try:
        client = genai.Client(api_key=gemini_api_key)
    except Exception as e:
        st.error(f"Erro ao inicializar o cliente do Gemini: {e}")

# Conexão GSheets
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception:
    conn = None

def carregar_dados(sheet_name, colunas_padrao):
    if conn and spreadsheet_url:
        try:
            df = conn.read(spreadsheet=spreadsheet_url, worksheet=sheet_name, ttl="0s")
            if df.empty:
                return pd.DataFrame(columns=colunas_padrao)
            return df
        except Exception:
            return pd.DataFrame(columns=colunas_padrao)
    else:
        # Fallback local via session_state se o Sheets não estiver configurado ainda
        chave_session = f"data_{sheet_name}"
        if chave_session not in st.session_state:
            st.session_state[chave_session] = pd.DataFrame(columns=colunas_padrao)
        return st.session_state[chave_session]

def salvar_dados(sheet_name, df):
    if conn and spreadsheet_url:
        try:
            conn.update(spreadsheet=spreadsheet_url, worksheet=sheet_name, data=df)
            st.success("Dados salvos no Google Sheets!")
        except Exception as e:
            st.error(f"Erro ao salvar no Google Sheets: {e}")
    else:
        st.session_state[f"data_{sheet_name}"] = df
        st.warning("Salvo temporariamente na sessão (Configure o SPREADSHEET_URL nos Secrets para salvar na nuvem permanentemente).")

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
    colunas_estoque = ["Espécie", "Tipo", "Quantidade", "Preço Un. (R$)"]
    df_estoque = carregar_dados("Estoque", colunas_estoque)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Itens Cadastrados")
        st.dataframe(df_estoque, use_container_width=True)
        
    with col2:
        st.subheader("Adicionar Madeira")
        with st.form("form_madeira"):
            especie = st.text_input("Espécie (ex: Cedro, Jacarandá, Marfim)")
            tipo = st.selectbox("Destinação", ["Corpo", "Braço", "Escala", "Tampo", "Outro"])
            qtd = st.number_input("Quantidade", min_value=1, step=1, value=1)
            preco = st.number_input("Preço Unitário (R$)", min_value=0.0, step=5.0, value=50.0)
            
            btn_add_madeira = st.form_submit_button("Cadastrar Insumo")
            if btn_add_madeira:
                if especie:
                    novo_item = pd.DataFrame([{"Espécie": especie, "Tipo": tipo, "Quantidade": qtd, "Preço Un. (R$)": preco}])
                    df_atualizado = pd.concat([df_estoque, novo_item], ignore_index=True)
                    salvar_dados("Estoque", df_atualizado)
                    st.rerun()
                else:
                    st.warning("Preencha o nome da espécie.")

# -----------------------------------------------------------------------------
# ABA 2: Máquinas & Ferramentas
# -----------------------------------------------------------------------------
with aba_maquinas:
    st.header("Status e Manutenção de Equipamentos")
    colunas_maquinas = ["Nome", "Categoria", "Status", "Descrição/Defeito"]
    df_maquinas = carregar_dados("Maquinas", colunas_maquinas)
    
    col_cad, col_list = st.columns([1, 1])
    
    with col_cad:
        st.subheader("Cadastrar Nova Máquina / Ferramenta")
        with st.form("form_maquina"):
            nome_maq = st.text_input("Nome da Máquina / Ferramenta")
            categoria_maq = st.selectbox("Categoria", ["Corte", "Lixamento", "Medição/Precisão", "Tupia/Usinagem", "Outro"])
            status_maq = st.selectbox("Status Atual", ["Operacional", "Manutenção Preventiva", "Inoperante/Quebrada"])
            defeito_maq = st.text_area("Descrição do Defeito / Observação")
            
            btn_add_maq = st.form_submit_button("Cadastrar Máquina")
            if btn_add_maq:
                if nome_maq:
                    nova_maq = pd.DataFrame([{"Nome": nome_maq, "Categoria": categoria_maq, "Status": status_maq, "Descrição/Defeito": defeito_maq}])
                    df_atualizado = pd.concat([df_maquinas, nova_maq], ignore_index=True)
                    salvar_dados("Maquinas", df_atualizado)
                    st.rerun()
                else:
                    st.warning("Informe o nome do equipamento.")
                
    with col_list:
        st.subheader("Status Das Máquinas e Ferramentas")
        if df_maquinas.empty:
            st.info("Nenhuma máquina cadastrada ainda.")
        else:
            for idx, row in df_maquinas.iterrows():
                nome = row.get("Nome", f"Equipamento {idx}")
                cat = row.get("Categoria", "Geral")
                status = row.get("Status", "Desconhecido")
                defeito = row.get("Descrição/Defeito", "Sem observações")
                
                cor_status = "🔴" if "Quebrada" in str(status) else ("🟡" if "Preventiva" in str(status) else "🟢")
                
                with st.expander(f"{cor_status} {nome} - {cat}"):
                    st.write(f"**Status:** {status}")
                    st.write(f"**Observação/Defeito:** {defeito}")
                    
                    if st.button(f"🔍 Diagnosticar Defeito com IA", key=f"diag_{idx}"):
                        if not client:
                            st.error("Chave de API do Gemini não configurada.")
                        else:
                            prompt = (
                                f"Você é um técnico especialista em manutenção de máquinas para marcenaria e luthieria. "
                                f"Analise o seguinte equipamento:\n"
                                f"**Equipamento:** {nome} ({cat})\n"
                                f"**Problema relatado:** {defeito or 'Manutenção geral'}\n\n"
                                f"Forneça:\n"
                                f"1. Possíveis causas do problema.\n"
                                f"2. Passo a passo detalhado e seguro para solução.\n"
                                f"3. Recomendações de manutenção preventiva."
                            )
                            with st.spinner("Analisando defeito com o Gemini..."):
                                try:
                                    response = client.models.generate_content(
                                        model="gemini-3.6-flash",
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
    colunas_fin = ["Data", "Tipo", "Descrição", "Valor (R$)"]
    df_fin = carregar_dados("Financeiro", colunas_fin)
    
    if not df_fin.empty and "Valor (R$)" in df_fin.columns:
        # Garantir conversão numérica dos valores
        df_fin["Valor (R$)"] = pd.to_numeric(df_fin["Valor (R$)"], errors="coerce").fillna(0.0)
        
        receita_total = df_fin[df_fin["Tipo"] == "Receita"]["Valor (R$)"].sum()
        despesa_total = df_fin[df_fin["Tipo"] == "Despesa"]["Valor (R$)"].sum()
        saldo = receita_total - despesa_total
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Receita Bruta", f"R$ {receita_total:.2f}")
        c2.metric("Despesas Totais", f"R$ {despesa_total:.2f}")
        c3.metric("Saldo Líquido", f"R$ {saldo:.2f}", delta=f"{saldo:.2f}")
    
    st.subheader("Lançamentos")
    st.dataframe(df_fin, use_container_width=True)
    
    with st.expander("➕ Novo Lançamento Financeiro"):
        with st.form("form_fin"):
            data = st.date_input("Data")
            tipo_fin = st.selectbox("Tipo", ["Receita", "Despesa"])
            desc = st.text_input("Descrição (ex: Regulagem Guitarra, Compra de Trastes)")
            val = st.number_input("Valor (R$)", min_value=0.0, step=10.0, value=100.0)
            
            btn_salvar_fin = st.form_submit_button("Salvar Lançamento")
            if btn_salvar_fin:
                if desc:
                    novo_lan = pd.DataFrame([{"Data": str(data), "Tipo": tipo_fin, "Descrição": desc, "Valor (R$)": val}])
                    df_atualizado = pd.concat([df_fin, novo_lan], ignore_index=True)
                    salvar_dados("Financeiro", df_atualizado)
                    st.rerun()
                else:
                    st.warning("Preencha a descrição do lançamento.")

# -----------------------------------------------------------------------------
# ABA 4: Assistente Técnico IA
# -----------------------------------------------------------------------------
with aba_ia:
    st.header("🤖 Consultoria Técnica em Luthieria & Madeiras")
    st.write("Faça perguntas sobre secagem de madeiras, colagem, escolha de verniz, cálculo de escala ou projetos.")
    
    duvida = st.text_area("Digite sua dúvida técnica:")
    if st.button("Consultar IA"):
        if not duvida:
            st.warning("Por favor, digite uma dúvida antes de enviar.")
        elif not client:
            st.error("Chave de API do Gemini não configurada.")
        else:
            prompt_geral = (
                f"Você é um Mestre Luthier especialista em construção de guitarras e baixos e em escolha de madeiras. "
                f"Responda à seguinte dúvida com precisão técnica e tom profissional:\n\n{duvida}"
            )
            with st.spinner("Consultando conhecimento técnico..."):
                try:
                    response = client.models.generate_content(
                        model="gemini-3.6-flash",
                        contents=prompt_geral
                    )
                    st.markdown("### Resposta da IA:")
                    st.success(response.text)
                except Exception as e:
                    st.error(f"Erro na consulta: {e}")

