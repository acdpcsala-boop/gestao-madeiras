import streamlit as st
import pandas as pd
import sqlite3
from google import genai
import os

# -----------------------------------------------------------------------------
# Configuração da Página
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Gestão Carreiro Guitars & Luthieria",
    page_icon="🎸",
    layout="wide"
)

# -----------------------------------------------------------------------------
# Inicialização do Banco de Dados SQLite
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
            vencimento TEXT,
            tipo TEXT,
            categoria TEXT,
            descricao TEXT,
            valor REAL,
            status TEXT DEFAULT 'Pago'
        )
    ''')

    # Tabela de Ordens de Serviço
    c.execute('''
        CREATE TABLE IF NOT EXISTS ordens_servico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT,
            telefone TEXT,
            instrumento TEXT,
            servico TEXT,
            valor REAL,
            data_entrada TEXT,
            prazo TEXT,
            status TEXT DEFAULT 'Em Fila'
        )
    ''')
    
    # Migrações para colunas extras em bancos antigos
    for cmd in [
        "ALTER TABLE financeiro ADD COLUMN vencimento TEXT",
        "ALTER TABLE financeiro ADD COLUMN categoria TEXT",
        "ALTER TABLE financeiro ADD COLUMN status TEXT DEFAULT 'Pago'"
    ]:
        try:
            c.execute(cmd)
        except sqlite3.OperationalError:
            pass
            
    conn.commit()
    conn.close()

init_db()

# -----------------------------------------------------------------------------
# Autenticação
# -----------------------------------------------------------------------------
if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = False

if not st.session_state.usuario_logado:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("🔒 Login - Carreiro Guitars ERP")
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
# ÁREA LOGADA
# =============================================================================

st.sidebar.title(f"👤 Olá, {st.session_state.get('nome_usuario', 'Alexandre')}")
if st.sidebar.button("🚪 Sair"):
    st.session_state.usuario_logado = False
    st.rerun()

st.sidebar.markdown("---")
st.title("🎸 Carreiro Guitars - Sistema de Gestão ERP")

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
aba_os, aba_estoque, aba_maquinas, aba_financeiro, aba_ia = st.tabs([
    "📋 Ordens de Serviço",
    "🪵 Estoque & Madeiras", 
    "⚙️ Máquinas & Ferramentas", 
    "💰 Fluxo de Caixa", 
    "🤖 Calculadora & IA"
])

# -----------------------------------------------------------------------------
# ABA 1: Ordens de Serviço (OS)
# -----------------------------------------------------------------------------
with aba_os:
    st.header("📋 Gerenciamento de Ordens de Serviço (OS)")
    
    conn = sqlite3.connect(DB_FILE)
    df_os = pd.read_sql_query("SELECT * FROM ordens_servico", conn)
    conn.close()

    col_os_list, col_os_cad = st.columns([2, 1])
    
    with col_os_list:
        st.subheader("Serviços em Andamento")
        if df_os.empty:
            st.info("Nenhuma Ordem de Serviço cadastrada.")
        else:
            st.dataframe(df_os, use_container_width=True)
            
            with st.expander("🛠️ Atualizar Status / Baixa em OS"):
                os_dict = {f"OS #{row['id']}: {row.get('cliente', '')} - {row.get('instrumento', '')} ({row.get('status', '')})": row['id'] for _, row in df_os.iterrows()}
                os_sel_label = st.selectbox("Selecione a OS:", list(os_dict.keys()))
                os_id = os_dict[os_sel_label]
                
                row_os = df_os[df_os["id"] == os_id].iloc[0]
                
                novo_status = st.selectbox(
                    "Novo Status", 
                    ["Em Fila", "Em Andamento", "Aguardando Peça", "Pronto para Retirada", "Entregue"]
                )
                
                c_att, c_lancar, c_del_os = st.columns(3)
                if c_att.button("💾 Atualizar Status"):
                    conn = sqlite3.connect(DB_FILE)
                    c = conn.cursor()
                    c.execute("UPDATE ordens_servico SET status=? WHERE id=?", (novo_status, os_id))
                    conn.commit()
                    conn.close()
                    st.toast("✅ Status da OS atualizado!")
                    st.rerun()
                    
                if c_lancar.button("💰 Lançar no Financeiro"):
                    conn = sqlite3.connect(DB_FILE)
                    c = conn.cursor()
                    c.execute(
                        "INSERT INTO financeiro (data, vencimento, tipo, categoria, descricao, valor, status) VALUES (date('now'), date('now'), 'Receita', 'Serviço de Luthieria', ?, ?, 'Pago')",
                        (f"OS #{os_id} - {row_os.get('cliente', '')} ({row_os.get('servico', '')})", float(row_os.get('valor', 0)))
                    )
                    conn.commit()
                    conn.close()
                    st.toast("✅ Receita gerada no Fluxo de Caixa!")
                    st.rerun()

                if c_del_os.button("🗑️ Excluir OS"):
                    conn = sqlite3.connect(DB_FILE)
                    c = conn.cursor()
                    c.execute("DELETE FROM ordens_servico WHERE id=?", (os_id,))
                    conn.commit()
                    conn.close()
                    st.toast("OS Removida!")
                    st.rerun()

    with col_os_cad:
        st.subheader("Nova Ordem de Serviço")
        with st.form("form_nova_os"):
            cliente_os = st.text_input("Nome do Cliente")
            tel_os = st.text_input("Telefone / WhatsApp")
            inst_os = st.text_input("Instrumento")
            serv_os = st.text_area("Serviço Solicitado")
            val_os = st.number_input("Valor Combinado (R$)", min_value=0.0, step=20.0, value=150.0)
            
            c_d1, c_d2 = st.columns(2)
            d_ent = c_d1.date_input("Data Entrada")
            d_prz = c_d2.date_input("Prazo de Entrega")
            
            if st.form_submit_button("Criar Ordem de Serviço"):
                if cliente_os.strip() and inst_os.strip():
                    conn = sqlite3.connect(DB_FILE)
                    c = conn.cursor()
                    c.execute(
                        "INSERT INTO ordens_servico (cliente, telefone, instrumento, servico, valor, data_entrada, prazo, status) VALUES (?, ?, ?, ?, ?, ?, ?, 'Em Fila')",
                        (cliente_os.strip(), tel_os.strip(), inst_os.strip(), serv_os.strip(), val_os, str(d_ent), str(d_prz))
                    )
                    conn.commit()
                    conn.close()
                    st.toast("✅ OS cadastrada com sucesso!")
                    st.rerun()
                else:
                    st.warning("Preencha o cliente e o instrumento.")

# -----------------------------------------------------------------------------
# ABA 2: Estoque de Madeiras
# -----------------------------------------------------------------------------
with aba_estoque:
    st.header("Estoque de Madeiras e Insumos")
    
    conn = sqlite3.connect(DB_FILE)
    df_estoque = pd.read_sql_query("SELECT * FROM estoque", conn)
    conn.close()
    
    if not df_estoque.empty and "quantidade" in df_estoque.columns:
        baixo_estoque = df_estoque[df_estoque["quantidade"] <= 2]
        if not baixo_estoque.empty:
            items_str = ", ".join([f"{row.get('especie', '')} ({row.get('quantidade', 0)} un)" for _, row in baixo_estoque.iterrows()])
            st.error(f"⚠️ **Atenção: Itens com estoque baixo (<= 2 un):** {items_str}")
            
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Itens Cadastrados")
        if df_estoque.empty:
            st.info("Nenhum item cadastrado no estoque.")
        else:
            st.dataframe(df_estoque, use_container_width=True)
            
            with st.expander("🛠️ Gerenciar / Editar / Excluir Item"):
                itens_dict = {f"ID {row['id']}: {row.get('especie', '')} ({row.get('tipo', '')})": row['id'] for _, row in df_estoque.iterrows()}
                item_sel_label = st.selectbox("Selecione o item:", list(itens_dict.keys()))
                item_id = itens_dict[item_sel_label]
                
                row_atual = df_estoque[df_estoque["id"] == item_id].iloc[0]
                
                with st.form("form_edit_madeira"):
                    ed_especie = st.text_input("Espécie", value=str(row_atual.get("especie", "")))
                    ed_tipo = st.selectbox("Destinação", ["Corpo", "Braço", "Escala", "Tampo", "Outro"])
                    ed_qtd = st.number_input("Quantidade", min_value=1, step=1, value=int(row_atual.get("quantidade", 1)))
                    ed_preco = st.number_input("Preço Unitário (R$)", min_value=0.0, step=5.0, value=float(row_atual.get("preco_un", 0.0)))
                    
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
# ABA 3: Máquinas & Ferramentas
# -----------------------------------------------------------------------------
with aba_maquinas:
    st.header("Status e Manutenção de Equipamentos")
    
    conn = sqlite3.connect(DB_FILE)
    df_maquinas = pd.read_sql_query("SELECT * FROM maquinas", conn)
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
                nome = str(row.get("nome", ""))
                cat = str(row.get("categoria", ""))
                status = str(row.get("status", ""))
                defeito = str(row.get("descricao", ""))
                
                cor_status = "🔴" if "Quebrada" in status or "Inoperante" in status else ("🟡" if "Preventiva" in status else "🟢")
                
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
# ABA 4: Fluxo de Caixa / Financeiro
# -----------------------------------------------------------------------------
with aba_financeiro:
    st.header("Controle Financeiro & Custos Fixos")
    
    conn = sqlite3.connect(DB_FILE)
    df_fin = pd.read_sql_query("SELECT * FROM financeiro", conn)
    conn.close()
    
    receita_paga = 0.0
    despesa_paga = 0.0
    despesa_pendente = 0.0
    saldo_real = 0.0

    if not df_fin.empty:
        if "status" not in df_fin.columns:
            df_fin["status"] = "Pago"
        if "categoria" not in df_fin.columns:
            df_fin["categoria"] = "Geral"
        if "vencimento" not in df_fin.columns:
            df_fin["vencimento"] = df_fin["data"]
            
        df_fin["status"] = df_fin["status"].fillna("Pago")
        df_fin["categoria"] = df_fin["categoria"].fillna("Geral")
        df_fin["vencimento"] = df_fin["vencimento"].fillna(df_fin["data"])
        
        receita_paga = df_fin[(df_fin["tipo"] == "Receita") & (df_fin["status"] == "Pago")]["valor"].sum()
        despesa_paga = df_fin[(df_fin["tipo"] == "Despesa") & (df_fin["status"] == "Pago")]["valor"].sum()
        despesa_pendente = df_fin[(df_fin["tipo"] == "Despesa") & (df_fin["status"] == "Pendente")]["valor"].sum()
        saldo_real = receita_paga - despesa_paga

    # Metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Receita Realizada", f"R$ {receita_paga:.2f}")
    c2.metric("Despesas Pagas", f"R$ {despesa_paga:.2f}")
    c3.metric("A Pagar (Pendente)", f"R$ {despesa_pendente:.2f}", delta=f"-{despesa_pendente:.2f}", delta_color="inverse")
    c4.metric("Saldo Atual Caixa", f"R$ {saldo_real:.2f}")

    if not df_fin.empty:
        with st.expander("📊 Gráfico de Receitas vs Despesas", expanded=False):
            resumo_tipo = df_fin[df_fin["status"] == "Pago"].groupby("tipo")["valor"].sum()
            st.bar_chart(resumo_tipo)

    st.subheader("📋 Lançamentos e Contas")
    if not df_fin.empty:
        st.dataframe(df_fin, use_container_width=True)
        
        # Filtragem segura de pendências sem linhas longas
        tem_st = "status" in df_fin.columns
        if tem_st:
          
