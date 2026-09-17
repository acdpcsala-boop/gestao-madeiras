import streamlit as st
import pandas as pd
import sqlite3
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

# -----------------------------------------------------------------------------
# Inicialização do Banco de Dados SQLite (Local & Instantâneo)
# -----------------------------------------------------------------------------
DB_FILE = "luthieria.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Tabela de Estoque
    c.execute('''
        CREATE TABLE IF NOT EXISTS estoque (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            especie TEXT,
            tipo TEXT,
            quantidade INTEGER,
            preco_un REAL
        )
    ''')
    
    # Tabela de Máquinas
    c.execute('''
        CREATE TABLE IF NOT EXISTS maquinas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            categoria TEXT,
            status TEXT,
            descricao TEXT
        )
    ''')
    
    # Tabela Financeira
    c.execute('''
        CREATE TABLE IF NOT EXISTS financeiro (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT,
            tipo TEXT,
            descricao TEXT,
            valor REAL
        )
    ''')
    
    conn.commit()
    conn.close()

# Executa a criação do banco de dados na inicialização
init_db()

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
                if user_input.strip().lower() == "alexandre" and pass_input == "admin123":
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

st.sidebar.title(f"👤 Olá, {st.session_state.get('nome_usuario', 'Alexandre')}")
if st.sidebar.button("🚪 Sair"):
    st.session_state.usuario_logado = False
    st.rerun()

st.sidebar.markdown("---")
st.title("🪵 Sistema Integrado de Gestão - Madeiras & Luthieria")

# Configuração do Gemini
raw_gemini = st.secrets.get("GEMINI_API_KEY", "")
gemini_api_key = str(raw_gemini).replace("\n", "").replace("\r", "").strip() or os.environ.get("GEMINI_API_KEY")

client = None
if gemini_api_key:
    try:
        client = genai.Client(api_key=gemini_api_key)
    except Exception as e:
        st.error(f"Erro ao inicializar Gemini: {e}")

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
    
    conn = sqlite3.connect(DB_FILE)
    df_estoque = pd.read_sql_query("SELECT id, especie AS 'Espécie', tipo AS 'Tipo', quantidade AS 'Quantidade', preco_un AS 'Preço Un. (R$)' FROM estoque", conn)
    conn.close()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Itens Cadastrados")
        st.dataframe(df_estoque.drop(columns=["id"]), use_container_width=True)
        
        if not df_estoque.empty:
            with st.expander("🛠️ Gerenciar / Editar / Excluir Item"):
                itens_dict = {f"ID {row['id']}: {row['Espécie']} ({row['Tipo']})": row['id'] for _, row in df_estoque.iterrows()}
                item_sel_label = st.selectbox("Selecione o item:", list(itens_dict.keys()))
                item_id = itens_dict[item_sel_label]
                
                row_atual = df_estoque[df_estoque["id"] == item_id].iloc[0]
                
                with st.form("form_edit_madeira"):
                    ed_especie = st.text_input("Espécie", value=str(row_atual["Espécie"]))
                    ed_tipo = st.selectbox("Destinação", ["Corpo", "Braço", "Escala", "Tampo", "Outro"], 
                                           index=["Corpo", "Braço", "Escala", "Tampo", "Outro"].index(row_atual["Tipo"]) if row_atual["Tipo"] in ["Corpo", "Braço", "Escala", "Tampo", "Outro"] else 0)
                    ed_qtd = st.number_input("Quantidade", min_value=1, step=1, value=int(row_atual["Quantidade"]))
                    ed_preco = st.number_input("Preço Unitário (R$)", min_value=0.0, step=5.0, value=float(row_atual["Preço Un. (R$)"]))
                    
                    c_salvar, c_excluir = st.columns(2)
                    btn_alterar = c_salvar.form_submit_button("💾 Salvar Alterações")
                    btn_apagar = c_excluir.form_submit_button("🗑️ Excluir Item")
                    
                    if btn_alterar:
                        conn = sqlite3.connect(DB_FILE)
                        c = conn.cursor()
                        c.execute("UPDATE estoque SET especie=?, tipo=?, quantidade=?, preco_un=? WHERE id=?", 
                                  (ed_especie, ed_tipo, ed_qtd, ed_preco, item_id))
                        conn.commit()
                        conn.close()
                        st.toast("✅ Item atualizado com sucesso!")
                        st.rerun()
                        
                    if btn_apagar:
                        conn = sqlite3.connect(DB_FILE)
                        c = conn.cursor()
                        c.execute("DELETE FROM estoque WHERE id=?", (item_id,))
                        conn.commit()
                        conn.close()
                        st.toast("🗑️ Item removido!")
                        st.rerun()

    with col2:
        st.subheader("Adicionar Madeira")
        with st.form("form_madeira"):
            especie = st.text_input("Espécie (ex: Cedro, Jacarandá, Marfim)")
            tipo = st.selectbox("Destinação", ["Corpo", "Braço", "Escala", "Tampo", "Outro"])
            qtd = st.number_input("Quantidade", min_value=1, step=1, value=1)
            preco = st.number_input("Preço Unitário (R$)", min_value=0.0, step=5.0, value=50.0)
            
            if st.form_submit_button("Cadastrar Insumo"):
                if especie.strip():
                    conn = sqlite3.connect(DB_FILE)
                    c = conn.cursor()
                    c.execute("INSERT INTO estoque (especie, tipo, quantidade, preco_un) VALUES (?, ?, ?, ?)",
                              (especie.strip(), tipo, qtd, preco))
                    conn.commit()
                    conn.close()
                    st.toast("✅ Madeira cadastrada!")
                    st.rerun()
                else:
                    st.warning("Preencha o nome da espécie.")

# -----------------------------------------------------------------------------
# ABA 2: Máquinas & Ferramentas
# -----------------------------------------------------------------------------
with aba_maquinas:
    st.header("Status e Manutenção de Equipamentos")
    
    conn = sqlite3.connect(DB_FILE)
    df_maquinas = pd.read_sql_query("SELECT id, nome AS 'Nome', categoria AS 'Categoria', status AS 'Status', descricao AS 'Descrição/Defeito' FROM maquinas", conn)
    conn.close()
    
    col_cad, col_list = st.columns([1, 1])
    
    with col_cad:
        st.subheader("Cadastrar Nova Máquina / Ferramenta")
        with st.form("form_maquina"):
            nome_maq = st.text_input("Nome da Máquina / Ferramenta")
            categoria_maq = st.selectbox("Categoria", ["Corte", "Lixamento", "Medição/Precisão", "Tupia/Usinagem", "Outro"])
            status_maq = st.selectbox("Status Atual", ["Operacional", "Manutenção Preventiva", "Inoperante/Quebrada"])
            defeito_maq = st.text_area("Descrição do Defeito / Observação")
            
            if st.form_submit_button("Cadastrar Máquina"):
                if nome_maq.strip():
                    conn = sqlite3.connect(DB_FILE)
                    c = conn.cursor()
                    c.execute("INSERT INTO maquinas (nome, categoria, status, descricao) VALUES (?, ?, ?, ?)",
                              (nome_maq.strip(), categoria_maq, status_maq, defeito_maq.strip()))
                    conn.commit()
                    conn.close()
                    st.toast(f"✅ Máquina '{nome_maq}' cadastrada!")
                    st.rerun()
                else:
                    st.warning("Preencha o nome da máquina.")
                
    with col_list:
        st.subheader("Status Das Máquinas e Ferramentas")
        if df_maquinas.empty:
            st.info("Nenhuma máquina cadastrada ainda.")
        else:
            for _, row in df_maquinas.iterrows():
                m_id = row["id"]
                nome = str(row["Nome"])
                cat = str(row["Categoria"])
                status = str(row["Status"])
                defeito = str(row["Descrição/Defeito"])
                
                cor_status = "🔴" if "Quebrada" in status else ("🟡" if "Preventiva" in status else "🟢")
                
                with st.expander(f"{cor_status} {nome} - {cat}"):
                    st.write(f"**Status:** {status}")
                    if defeito:
                        st.write(f"**Observação/Defeito:** {defeito}")
                    
                    c_ia, c_del = st.columns([3, 1])
                    if c_ia.button(f"🔍 Diagnosticar Defeito com IA", key=f"diag_{m_id}"):
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
                    
                    if c_del.button(f"🗑️ Excluir", key=f"del_maq_{m_id}"):
                        conn = sqlite3.connect(DB_FILE)
                        c = conn.cursor()
                        c.execute("DELETE FROM maquinas WHERE id=?", (m_id,))
                        conn.commit()
                        conn.close()
                        st.toast(f"🗑️ Máquina '{nome}' removida!")
                        st.rerun()

# -----------------------------------------------------------------------------
# ABA 3: Fluxo de Caixa / Financeiro
# -----------------------------------------------------------------------------
with aba_financeiro:
    st.header("Controle Financeiro da Luthieria")
    
    conn = sqlite3.connect(DB_FILE)
    df_fin = pd.read_sql_query("SELECT id, data AS 'Data', tipo AS 'Tipo', descricao AS 'Descrição', valor AS 'Valor (R$)' FROM financeiro", conn)
    conn.close()
    
    if not df_fin.empty:
        receita_total = df_fin[df_fin["Tipo"] == "Receita"]["Valor (R$)"].sum()
        despesa_total = df_fin[df_fin["Tipo"] == "Despesa"]["Valor (R$)"].sum()
        saldo = receita_total - despesa_total
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Receita Bruta", f"R$ {receita_total:.2f}")
        c2.metric("Despesas Totais", f"R$ {despesa_total:.2f}")
        c3.metric("Saldo Líquido", f"R$ {saldo:.2f}", delta=f"{saldo:.2f}")
    
    st.subheader("Lançamentos")
    st.dataframe(df_fin.drop(columns=["id"]), use_container_width=True)
    
    with st.expander("➕ Novo Lançamento Financeiro"):
        with st.form("form_fin"):
            data = st.date_input("Data")
            tipo_fin = st.selectbox("Tipo", ["Receita", "Despesa"])
            desc = st.text_input("Descrição")
            val = st.number_input("Valor (R$)", min_value=0.0, step=10.0, value=100.0)
            
            if st.form_submit_button("Salvar Lançamento"):
                if desc.strip():
                    conn = sqlite3.connect(DB_FILE)
                    c = conn.cursor()
                    c.execute("INSERT INTO financeiro (data, tipo, descricao, valor) VALUES (?, ?, ?, ?)",
                              (str(data), tipo_fin, desc.strip(), val))
                    conn.commit()
                    conn.close()
                    st.toast("✅ Lançamento gravado!")
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
