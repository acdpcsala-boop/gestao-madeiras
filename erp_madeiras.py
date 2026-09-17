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

# -----------------------------------------------------------------------------
# Autenticação Simples Nativa
# -----------------------------------------------------------------------------
if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = False

if not st.session_state.usuario_logado:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("🔒 Login - ERP Luthieria")
        with st.form("login_form"):
            user_input = st.text_input("Usuário")
            pass_input = st.text_input("Senha", type="password")
            btn_login = st.form_submit_button("Entrar")
            
            if btn_login:
                if user_input.strip() == "alexandre" and pass_input == "admin123":
                    st.session_state.usuario_logado = True
                    st.session_state.nome_usuario = "Alexandre Carreiro"
                    st.success("Login efetuado com sucesso!")
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
    st.stop()

# =============================================================================
# ÁREA LOGADA DO SISTEMA ERP
# =============================================================================

# Barra Lateral
st.sidebar.title(f"👤 Olá, {st.session_state.get('nome_usuario', 'Alexandre')}")
if st.sidebar.button("🚪 Sair"):
    st.session_state.usuario_logado = False
    st.rerun()

st.sidebar.markdown("---")

st.title("🪵 Sistema Integrado de Gestão - Madeiras & Luthieria")

# -----------------------------------------------------------------------------
# Configuração das Conexões (Tratamento Limpo dos Secrets)
# -----------------------------------------------------------------------------
spreadsheet_url = st.secrets.get("SPREADSHEET_URL", "").strip()
gemini_api_key = st.secrets.get("GEMINI_API_KEY", "").strip() or os.environ.get("GEMINI_API_KEY")

client = None
if gemini_api_key:
    try:
        client = genai.Client(api_key=gemini_api_key)
    except Exception as e:
        st.error(f"Erro ao inicializar Gemini: {e}")

# Conexão com Google Sheets
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    conn = None
    st.error(f"Erro ao inicializar conexão gsheets: {e}")

def carregar_dados(sheet_name, colunas_padrao):
    chave_session = f"data_{sheet_name}"
    if chave_session not in st.session_state:
        st.session_state[chave_session] = pd.DataFrame(columns=colunas_padrao)
        
        if conn and spreadsheet_url:
            try:
                df = conn.read(spreadsheet=spreadsheet_url, worksheet=sheet_name, ttl="0s")
                if df is not None and not df.empty:
                    st.session_state[chave_session] = df
            except Exception as e:
                st.error(f"Erro ao ler aba '{sheet_name}' no Sheets: {e}")
                
    return st.session_state[chave_session]

def salvar_dados(sheet_name, df):
    st.session_state[f"data_{sheet_name}"] = df
    if conn and spreadsheet_url:
        try:
            conn.update(spreadsheet=spreadsheet_url, worksheet=sheet_name, data=df)
            st.toast("Salvo na planilha do Google Sheets!")
        except Exception as e:
            st.toast(f"Erro ao sincronizar com Sheets: {e}")

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
            
            if st.form_submit_button("Cadastrar Insumo"):
                if especie:
                    novo_item = pd.DataFrame([{"Espécie": especie, "Tipo": tipo, "Quantidade": qtd, "Preço Un. (R$)": preco}])
                    df_atualizado = pd.concat([df_estoque, novo_item], ignore_index=True)
                    salvar_dados("Estoque", df_atualizado)
                    st.success("Item cadastrado com sucesso!")
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
            
            if st.form_submit_button("Cadastrar Máquina"):
                if nome_maq:
                    nova_maq = pd.DataFrame([{"Nome": nome_maq, "Categoria": categoria_maq, "Status": status_maq, "Descrição/Defeito": defeito_maq}])
                    df_atualizado = pd.concat([df_maquinas, nova_maq], ignore_index=True)
                    salvar_dados("Maquinas", df_atualizado)
                    st.success(f"Máquina '{nome_maq}' cadastrada com sucesso!")
                    st.rerun()
                else:
                    st.warning("Preencha o nome da máquina para cadastrar.")
                
    with col_list:
        st.subheader("Status Das Máquinas e Ferramentas")
        if df_maquinas.empty:
            st.info("Nenhuma máquina cadastrada ainda.")
        else:
            for idx, row in df_maquinas.iterrows():
                nome = str(row.get("Nome", f"Equipamento {idx}"))
                cat = str(row.get("Categoria", "Geral"))
                status = str(row.get("Status", "Operacional"))
                defeito = str(row.get("Descrição/Defeito", ""))
                
                cor_status = "🔴" if "Quebrada" in status else ("🟡" if "Preventiva" in status else "🟢")
                
                with st.expander(f"{cor_status} {nome} - {cat}"):
                    st.write(f"**Status:** {status}")
                    if defeito and defeito.strip() != "nan":
                        st.write(f"**Observação/Defeito:** {defeito}")
                    
                    if st.button(f"🔍 Diagnosticar Defeito com IA", key=f"diag_{idx}"):
                        if not client:
                            st.error("Chave da API do Gemini não encontrada.")
                        else:
                            prompt = (
                                f"Você é um técnico especialista em manutenção de máquinas para marcenaria e luthieria. "
                                f"Analise o equipamento:\n"
                                f"**Equipamento:** {nome} ({cat})\n"
                                f"**Problema:** {defeito or 'Manutenção geral'}\n\n"
                                f"Forneça:\n1. Possíveis causas.\n2. Passo a passo para solução.\n3. Prevenção."
                            )
                            with st.spinner("Analisando defeito com Gemini..."):
                                try:
                                    response = client.models.generate_content(
                                        model="gemini-3.6-flash",
                                        contents=prompt
                                    )
                                    st.markdown("---")
                                    st.markdown("#### 💡 Diagnóstico da IA:")
                                    st.info(response.text)
                                except Exception as e:
                                    st.error(f"Erro na análise: {e}")

# -----------------------------------------------------------------------------
# ABA 3: Fluxo de Caixa / Financeiro
# -----------------------------------------------------------------------------
with aba_financeiro:
    st.header("Controle Financeiro da Luthieria")
    colunas_fin = ["Data", "Tipo", "Descrição", "Valor (R$)"]
    df_fin = carregar_dados("Financeiro", colunas_fin)
    
    if not df_fin.empty and "Valor (R$)" in df_fin.columns:
        df_fin["Valor (R$)"] = pd.to_numeric(df_fin["Valor (R$)"].astype(str).str.replace(",", "."), errors="coerce").fillna(0.0)
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
            desc = st.text_input("Descrição")
            val = st.number_input("Valor (R$)", min_value=0.0, step=10.0, value=100.0)
            
            if st.form_submit_button("Salvar Lançamento"):
                if desc:
                    novo_lan = pd.DataFrame([{"Data": str(data), "Tipo": tipo_fin, "Descrição": desc, "Valor (R$)": val}])
                    df_atualizado = pd.concat([df_fin, novo_lan], ignore_index=True)
                    salvar_dados("Financeiro", df_atualizado)
                    st.success("Lançamento efetuado com sucesso!")
                    st.rerun()
                else:
                    st.warning("Preencha a descrição do lançamento.")

# -----------------------------------------------------------------------------
# ABA 4: Assistente Técnico IA
# -----------------------------------------------------------------------------
with aba_ia:
    st.header("🤖 Consultoria Técnica em Luthieria")
    duvida = st.text_area("Digite sua dúvida técnica:")
    if st.button("Consultar IA"):
        if not duvida:
            st.warning("Digite uma dúvida antes de enviar.")
        elif not client:
            st.error("Chave de API do Gemini não configurada.")
        else:
            with st.spinner("Consultando Gemini..."):
                try:
                    response = client.models.generate_content(
                        model="gemini-3.6-flash",
                        contents=f"Você é um Mestre Luthier especialista. Responda: {duvida}"
                    )
                    st.markdown("### Resposta da IA:")
                    st.success(response.text)
                except Exception as e:
                    st.error(f"Erro na consulta: {e}")
