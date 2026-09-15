import sqlite3
import streamlit as st

# --- BANCO DE DADOS (BACK-END) ---
conn = sqlite3.connect('estoque_madeiras.db')
cursor = conn.cursor()

# Tabela de Madeiras em estoque
cursor.execute("""
               CREATE TABLE IF NOT EXISTS madeiras
               (
                   id
                   INTEGER
                   PRIMARY
                   KEY
                   AUTOINCREMENT,
                   tipo
                   TEXT,
                   comprimento
                   REAL,
                   largura
                   REAL,
                   espessura
                   REAL,
                   preco_metro
                   REAL
               )
               """)

# Tabela de Tipos de Madeira (Menu)
cursor.execute("""
               CREATE TABLE IF NOT EXISTS tipos_madeira
               (
                   id
                   INTEGER
                   PRIMARY
                   KEY
                   AUTOINCREMENT,
                   nome
                   TEXT
                   UNIQUE
               )
               """)

cursor.execute('SELECT COUNT(*) FROM tipos_madeira')
if cursor.fetchone()[0] == 0:
    opcoes_iniciais = [('Jatobá',), ('Massaranduba',), ('Ipê',), ('Pinus',), ('Cedro Rosa',), ('Pau Marfim',),
                       ('Marupá',)]
    cursor.executemany('INSERT INTO tipos_madeira (nome) VALUES (?)', opcoes_iniciais)

# Tabela de Insumos
cursor.execute("""
               CREATE TABLE IF NOT EXISTS insumos
               (
                   id
                   INTEGER
                   PRIMARY
                   KEY
                   AUTOINCREMENT,
                   nome
                   TEXT
                   NOT
                   NULL,
                   categoria
                   TEXT
                   NOT
                   NULL,
                   quantidade
                   REAL
                   NOT
                   NULL,
                   unidade
                   TEXT
                   NOT
                   NULL,
                   qtd_minima
                   REAL
                   NOT
                   NULL
               )
               """)

# Tabela de Maquinário
cursor.execute("""
               CREATE TABLE IF NOT EXISTS maquinas
               (
                   id
                   INTEGER
                   PRIMARY
                   KEY
                   AUTOINCREMENT,
                   nome
                   TEXT
                   NOT
                   NULL,
                   categoria
                   TEXT
                   NOT
                   NULL,
                   status
                   TEXT
                   NOT
                   NULL,
                   defeito
                   TEXT
               )
               """)
conn.commit()

# --- MENU LATERAL DE NAVEGAÇÃO ---
st.sidebar.title('🛠️ Sistema ERP Oficina')
aba_selecionada = st.sidebar.radio(
    'Navegar para:',
    ['🌲 Estoque De Madeiras', '📦 Insumos e Consumíveis', '⚙️ Maquinário e Manutenção']
)

# --- ABA 1: MADEIRAS ---
if aba_selecionada == '🌲 Estoque De Madeiras':
    st.title('🌲 Gestão de Madeiras - Oficina')

    with st.expander('➕ Cadastrar Novo Tipo de Madeira'):
        nova_madeira = st.text_input('Nome da nova madeira')
        if st.button('Adicionar ao menu'):
            if nova_madeira.strip():
                try:
                    cursor.execute('INSERT INTO tipos_madeira (nome) VALUES (?)', (nova_madeira.strip(),))
                    conn.commit()
                    st.success(f'☑️ "{nova_madeira}" adicionada!')
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.warning('⚠️ Essa madeira já existe no menu')

    # Formulário de cadastro de peças
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

    if st.button('Salvar No Estoque'):
        cursor.execute("""
                       INSERT INTO madeiras (tipo, comprimento, largura, espessura, preco_metro)
                       VALUES (?, ?, ?, ?, ?)
                       """, (madeira, comprimento, largura, espessura, preco_metro))
        conn.commit()

        st.success(f'☑️ {madeira} ({comprimento}x{largura}x{espessura} cm) gravado com sucesso!')
        custo_total = (comprimento / 100) * preco_metro
        st.info(f'💰 Custo estimado deste caibro: R$ {custo_total:.2f}')

    # Exibição do Estoque de Madeiras
    st.divider()
    st.subheader('📋 Madeiras Cadastradas No Estoque')
    cursor.execute('SELECT * FROM madeiras')
    dados = cursor.fetchall()

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

# --- ABA 2: INSUMOS ---
elif aba_selecionada == '📦 Insumos e Consumíveis':
    st.title('📦 Controle de Insumos e Consumíveis')

    with st.expander('➕ Cadastrar Novo Insumo'):
        with st.form('form_insumo'):
            nome_insumo = st.text_input('Nome do Insumo (ex: Cola Titebond III, Lixa 220)')
            categoria_insumo = st.selectbox('Categoria',
                                            ['Colas', 'Lixas', 'Acabamento/Óleo', 'Lâminas/Fresas', 'Outros'])
            qtd = st.number_input('Quantidade Atual', min_value=0.0, step=1.0)
            unidade = st.selectbox('Unidade de Medida', ["Unidades", 'ml', 'Litros', 'Metros', 'Folhas', 'Kg'])
            qtd_minima = st.number_input('Estoque mínimo (Alerta)', min_value=0.0, step=1.0)

            btn_salvar_insumo = st.form_submit_button('Salvar Insumo')

            if btn_salvar_insumo:
                if nome_insumo:
                    cursor.execute("""
                                   INSERT INTO insumos (nome, categoria, quantidade, unidade, qtd_minima)
                                   VALUES (?, ?, ?, ?, ?)
                                   """, (nome_insumo, categoria_insumo, qtd, unidade, qtd_minima))
                    conn.commit()
                    st.success(f"☑️ Insumo '{nome_insumo}' cadastrado com sucesso!")
                    st.rerun()
                else:
                    st.warning("⚠️ Preencha o nome do insumo.")

    st.divider()
    st.subheader("📋 Insumos em Estoque")
    cursor.execute("SELECT id, nome, categoria, quantidade, unidade, qtd_minima FROM insumos")
    dados_insumos = cursor.fetchall()

    if dados_insumos:
        st.dataframe(
            dados_insumos,
            column_config={
                "0": "ID",
                "1": "Nome",
                "2": "Categoria",
                "3": "Quantidade",
                "4": "Unidade",
                "5": "Mínimo Desejado",
            }
        )
    else:
        st.info("Nenhum insumo cadastrado até o momento.")

# --- ABA 3: MAQUINÁRIO ---
elif aba_selecionada == '⚙️ Maquinário e Manutenção':
    st.title('⚙️ Controle de Maquinário e Manutenção')

    with st.expander('➕ Cadastrar Nova Máquina'):
        with st.form('form_maquina'):
            nome_maquina = st.text_input('Nome da Máquina / Ferramenta')
            categoria_maquina = st.selectbox('Categoria', ['Corte', 'Usinagem', 'Lixamento', 'Manual', 'Laser/CNC'])
            status_maquina = st.selectbox('Status Atual',
                                          ['Funcionando', 'Requer Atenção', 'Em Manutenção', 'Inoperante/Quebrada'])
            defeito = st.text_area('Descrição do Defeito / Observação (Opcional)')

            btn_salvar_maquina = st.form_submit_button('Cadastrar Máquina')
            if btn_salvar_maquina:
                if nome_maquina:
                    cursor.execute("""
                                   INSERT INTO maquinas (nome, categoria, status, defeito)
                                   VALUES (?, ?, ?, ?)
                                   """, (nome_maquina, categoria_maquina, status_maquina, defeito))
                    conn.commit()
                    st.success(f"☑️ Máquina '{nome_maquina}' cadastrada com sucesso!")
                    st.rerun()
                else:
                    st.warning('⚠️ Preencha o nome da máquina.')

    st.divider()
    st.subheader('📋 Status Das Máquinas e Ferramentas')
    cursor.execute('SELECT id, nome, categoria, status, defeito FROM maquinas')
    maquinas = cursor.fetchall()

    if maquinas:
        for maq in maquinas:
            id_m, nome, cat, status, desc_defeito = maq
            cor = "🟢" if status == 'Funcionando' else '🟡' if status == 'Requer Atenção' else '🔴'

            st.markdown(f'### {cor} {nome} - *{cat}*')
            st.write(f'**Status:** {status}')
            if desc_defeito:
                st.warning(f'**Observação/Defeito:** {desc_defeito}')
            st.divider()
    else:
        st.info('Nenhuma máquina cadastrada no momento.')
