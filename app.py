import sqlite3
import streamlit as st

# --- BANCO DE DADOS (BACK-END) ---.
conn = sqlite3.connect('estoque_madeiras.db')
cursor = conn.cursor()

# Cria a tabela garantindo os parênteses e a sintaxe limpa.
cursor.execute("""
        
    CREATE
        TABLE IF NOT EXISTS madeiras (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT,
        comprimento REAL,
        largura REAL,
        espessura REAL,
        preco_metro REAL
    )
""")
conn.commit()

# ---INCLUIR A PARTIR DAQUI ---
cursor.execute("""
    CREATE TABLE IF NOT EXISTS tipos_madeira (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT UNIQUE
    )
 """)

cursor.execute('SELECT COUNT(*) FROM tipos_madeira')
if cursor.fetchone()[0] == 0:
    opcoes_iniciais = [('Jatobá',), ('Massaranduba',), ('Ipê',), ('Pinus',), ('Cedro Rosa',), ('Pau Marfim',), ('Marupá',)]
    cursor.executemany('INSERT INTO tipos_madeira (nome) VALUES  (?)', opcoes_iniciais)

conn.commit()
# --- INTERFACE (Front-end) ---
st.title('🌲 Gestão De Madeiras - Oficina')
with st.expander('➕ Cadastrar Novo Tipo de Madeira'):
    nova_madeira = st.text_input('Nome da nova madeira')
    if st.button('Adicionar ao menu'):
        if nova_madeira.strip():
            try:
                cursor.execute('INSERT INTO tipos_madeira (nome) VALUES (?)', (nova_madeira.strip(),))
                conn.commit()
                st.success(f'☑️ "{nova_madeira}" adicionada!')
                st.rerun()  # Recarrega a tela para atualizar o menu
            except sqlite3.IntegrityError:
                st.warning('⚠️ Essa madeira já existe no menu')

# Formulário de entrada
cursor.execute('SELECT nome FROM tipos_madeira')
opcoes_madeira = [item[0] for item in cursor.fetchall()]

madeira = st.selectbox('Tipo de madeira', opcoes_madeira)

col1, col2, col3 = st.columns(3)
with col1:
    comprimento = st.number_input('Comprimento (cm)', value=100.0)
with col2:
    largura = st.number_input('Largura (cm)', value=5.0)
with col3:
    espessura = st.number_input('Espessura (cm)', value=5.0)

preco_metro = st.number_input('Preço por metro linear (R$)', value=15.0)

# Botão salvar no banco
if st.button('Salvar No Estoque'):
    # Insere as informações diretamente no banco SQLite
    cursor.execute(
        """
        INSERT INTO madeiras (tipo, comprimento, largura, espessura, preco_metro)
        VALUES (?, ?, ?, ?, ?)
    """,
        (madeira, comprimento, largura, espessura, preco_metro),
    )

    conn.commit()  # Confirma a gravação dos dados

    st.success(
        f'☑️ {madeira} ({comprimento}x{largura}x{espessura} cm) gravado com sucesso no banco de dados!'
    )

    # --- ADICIONE ESTAS DUAS LINHAS ABAIXO ---
    custo_total = (comprimento / 100) * preco_metro
    st.info(f'💰 Custo estimado deste caibro: R$ {custo_total:.2f}')

    # --- EXIBIR O ESTOQUE CADASTRADO ---
    st.divider()  # Cria uma linha divisória charmosa na tela
    st.subheader('📋 Madeiras Cadastradas No Estoque')

    # Busca todos os registros salvos no banco de dados SQLite
    cursor.execute('SELECT * FROM madeiras')
    dados = cursor.fetchall()

    # Exibe na tela em formato de tabela interativa
    if dados:
        st.dataframe(
            dados,
            column_config={
                "0": "ID",
                "1": "Tipo",
                "2": "Comprimento (cm)",
                "3": "Largura (cm)",
                "4": "Espessura (cm)",
                "5": "Preço/m (R$)",
            },
        )
    else:
        st.info("Nenhuma madeira cadastrada no momento.")