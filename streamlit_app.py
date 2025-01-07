import streamlit as st
import pandas as pd
import time
from datetime import datetime
import pytz
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import plotly.graph_objects as go

# Configuração da página
st.set_page_config(
    page_title="PORTAL - JETFRIO",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo personalizado
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
* {
    font-family: 'Inter', sans-serif;
}
.stApp {
    background-color: #f8f9fa;
}
.main {
    padding: 2rem;
    background-color: #BDBDBD;
    border-radius: 8px;
    margin: 1rem;
}
.sidebar {
    background-color: #BDBDBD;
    padding: 2rem 1rem;
}
h1 {
    color: #2D2C74;
    font-size: 1.8rem;
    font-weight: 600;
    margin-bottom: 1.5rem;
}
.stButton > button {
    background-color: #2D2C74;
    color: white;
    border-radius: 4px;
    padding: 0.75rem 1rem;
    font-weight: 500;
}
.stButton > button:hover {
    background-color: #1B81C5;
}
.metric-card {
    background-color: #BDBDBD;
    padding: 1.5rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
</style>
""", unsafe_allow_html=True)

def solicitar_permissao_notificacao():
    st.markdown("""
    <script>
    function solicitarPermissao() {
        if (!("Notification" in window)) {
            alert("Este navegador não suporta notificações na área de trabalho");
        } else if (Notification.permission === "granted") {
            console.log("Permissão para notificações já concedida");
        } else if (Notification.permission !== "denied") {
            Notification.requestPermission().then(function (permission) {
                if (permission === "granted") {
                    console.log("Permissão para notificações concedida");
                }
            });
        }
    }
    solicitarPermissao();
    </script>
    """, unsafe_allow_html=True)

def enviar_notificacao(titulo, corpo, numero_requisicao):
    st.markdown(f"""
    <script>
    function enviarNotificacao() {{
        if (Notification.permission === "granted") {{
            var notification = new Notification("{titulo}", {{
                body: "{corpo}",
                icon: "/favicon.ico",
                tag: "requisicao-{numero_requisicao}",
                requireInteraction: true
            }});
            
            notification.onclick = function() {{
                window.focus();
                const element = document.getElementById("requisicao-{numero_requisicao}");
                if (element) {{
                    element.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                    element.style.animation = 'highlight 2s';
                }}
                notification.close();
            }};
        }}
    }}
    enviarNotificacao();
    </script>
    """, unsafe_allow_html=True)

def get_permissoes_perfil(perfil):
    permissoes_padrao = {
        'vendedor': ['dashboard', 'requisicoes'],
        'comprador': ['dashboard', 'requisicoes', 'cotacoes', 'importacao', 'configuracoes'],
        'administrador': ['dashboard', 'requisicoes', 'cotacoes', 'importacao', 'configuracoes', 
                         'editar_usuarios', 'excluir_usuarios', 'editar_perfis']
    }
    try:
        with open('perfis.json', 'r', encoding='utf-8') as f:
            perfis = json.load(f)
            return perfis.get(perfil, permissoes_padrao.get(perfil, []))
    except FileNotFoundError:
        return permissoes_padrao.get(perfil, [])
    except Exception as e:
        st.error(f"Erro ao carregar permissões: {str(e)}")
        return permissoes_padrao.get(perfil, [])

def save_perfis_permissoes(perfil, permissoes):
    try:
        try:
            with open('perfis.json', 'r', encoding='utf-8') as f:
                perfis = json.load(f)
        except FileNotFoundError:
            perfis = {}
        except json.JSONDecodeError:
            perfis = {}
        
        perfis[perfil] = permissoes
        
        with open('perfis.json', 'w', encoding='utf-8') as f:
            json.dump(perfis, f, ensure_ascii=False, indent=4)
            
        return True
    
    except Exception as e:
        st.error(f"Erro ao salvar permissões: {str(e)}")
        return False

def carregar_usuarios():
    usuario_padrao = {
        'ZAQUEU SOUZA': {
            'senha': None,
            'perfil': 'administrador',
            'email': 'zaqueu@jetfrio.com.br',
            'ativo': True,
            'primeiro_acesso': True,
            'permissoes': get_permissoes_perfil('administrador')
        }
    }
    
    try:
        # Se o arquivo não existir, cria com usuário padrão
        if not os.path.exists('usuarios.json'):
            with open('usuarios.json', 'w', encoding='utf-8') as f:
                json.dump(usuario_padrao, f, ensure_ascii=False, indent=4)
            print("Arquivo usuarios.json criado com usuário padrão")
            return usuario_padrao

        # Lê o arquivo existente
        with open('usuarios.json', 'r', encoding='utf-8') as f:
            usuarios = json.load(f)
            if not usuarios:
                print("Arquivo vazio, retornando usuário padrão")
                return usuario_padrao
                
            # Garante que o usuário administrador existe
            if 'ZAQUEU SOUZA' not in usuarios:
                usuarios['ZAQUEU SOUZA'] = usuario_padrao['ZAQUEU SOUZA']
                with open('usuarios.json', 'w', encoding='utf-8') as f:
                    json.dump(usuarios, f, ensure_ascii=False, indent=4)
            
            return usuarios
            
    except Exception as e:
        print(f"Erro ao carregar usuários: {str(e)}")
        return usuario_padrao

def salvar_usuarios():
    arquivo_usuarios = 'usuarios.json'
    try:
        with open(arquivo_usuarios, 'w', encoding='utf-8') as f:
            json.dump(st.session_state.usuarios, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar usuários: {str(e)}")
        return False

def salvar_requisicoes():
    try:
        with open('requisicoes.json', 'w', encoding='utf-8') as f:
            json.dump(st.session_state.requisicoes, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar requisições: {str(e)}")
        return False

def carregar_requisicoes():
    try:
        if os.path.exists('requisicoes.json'):
            with open('requisicoes.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        return []  # Retorna lista vazia se arquivo não existir
    except json.JSONDecodeError as e:
        # Arquivo existe mas está corrompido ou vazio
        return []
    except Exception as e:
        st.error(f"Erro ao carregar requisições: {str(e)}")
        return []

def get_data_hora_brasil():
    try:
        fuso_brasil = pytz.timezone('America/Sao_Paulo')
        return datetime.now(fuso_brasil).strftime('%H:%M:%S - %d/%m/%Y')
    except Exception as e:
        st.error(f"Erro ao obter data/hora: {str(e)}")
        return datetime.now().strftime('%H:%M:%S - %d/%m/%Y')

def enviar_email(destinatario, assunto, mensagem):
    try:
        EMAIL_SENDER = "seu_email@gmail.com"
        EMAIL_PASSWORD = "sua_senha_app"
        SMTP_SERVER = "smtp.gmail.com"
        SMTP_PORT = 587

        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = destinatario
        msg['Subject'] = assunto
        msg.attach(MIMEText(mensagem, 'plain', 'utf-8'))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Erro ao enviar email: {str(e)}")
        return False

# Inicialização de dados
if 'usuarios' not in st.session_state:
    st.session_state.usuarios = carregar_usuarios()

def get_next_requisition_number():
    try:
        with open('ultimo_numero.json', 'r') as f:
            ultimo_numero = json.load(f)
            proximo_numero = ultimo_numero['numero'] + 1
    except FileNotFoundError:
        proximo_numero = 5000
    
    with open('ultimo_numero.json', 'w') as f:
        json.dump({'numero': proximo_numero}, f)
    
    return proximo_numero

def inicializar_numero_requisicao():
    try:
        with open('ultimo_numero.json', 'r') as f:
            return json.load(f)['numero']
    except FileNotFoundError:
        with open('ultimo_numero.json', 'w') as f:
            json.dump({'numero': 4999}, f)
            return 4999

# Inicialização de dados...
if 'usuarios' not in st.session_state:
    st.session_state.usuarios = carregar_usuarios()
if not os.path.exists('ultimo_numero.json'):
    inicializar_numero_requisicao()
if 'requisicoes' not in st.session_state:
    st.session_state.requisicoes = carregar_requisicoes()

def tela_login():
    st.title("PORTAL - JETFRIO")
    usuario = st.text_input("Usuário", key="usuario_input").upper()
    
    if usuario:
        if usuario in st.session_state.usuarios:
            user_data = st.session_state.usuarios[usuario]
            
            if user_data.get('primeiro_acesso', True):
                st.markdown("### 😊 Primeiro Acesso - Configure sua senha")
                with st.form("primeiro_acesso_form"):
                    nova_senha = st.text_input("Nova Senha", type="password", 
                        help="Mínimo 8 caracteres, incluindo letra maiúscula, minúscula e número")
                    confirma_senha = st.text_input("Confirme a Nova Senha", type="password")
                    
                    if st.form_submit_button("Cadastrar Senha"):
                        if len(nova_senha) < 8:
                            st.error("A senha deve ter no mínimo 8 caracteres")
                            return
                            
                        if nova_senha != confirma_senha:
                            st.error("As senhas não coincidem")
                            return
                            
                        st.session_state.usuarios[usuario]['senha'] = nova_senha
                        st.session_state.usuarios[usuario]['primeiro_acesso'] = False
                        salvar_usuarios()
                        st.success("Senha cadastrada com sucesso!")
                        time.sleep(1)
                        st.rerun()
            else:
                senha = st.text_input("Senha", type="password", key="senha_input")
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    if st.button("Entrar", use_container_width=True):
                        if not user_data.get('ativo', True):
                            st.error("USUÁRIO INATIVO - CONTATE O ADMINISTRADOR")
                            return
                            
                        if user_data['senha'] != senha:
                            st.error("Senha incorreta")
                            return
                            
                        st.session_state['usuario'] = usuario
                        st.session_state['perfil'] = user_data['perfil']
                        st.success(f"Bem-vindo, {usuario}!")
                        time.sleep(1)
                        st.rerun()
                
                with col2:
                    if st.button("Esqueci a Senha", use_container_width=True):
                        st.session_state['modo_login'] = 'recuperar_senha'
                        st.session_state['temp_usuario'] = usuario
                        st.rerun()
        else:
            st.error("Usuário não encontrado no sistema")

    if st.session_state.get('modo_login') == 'recuperar_senha':
        st.markdown("### 🔑 Recuperação de Senha")
        with st.form("recuperar_senha_form"):
            email = st.text_input("Digite seu email cadastrado")
            
            if st.form_submit_button("Verificar Email"):
                if not email:
                    st.error("Digite seu email")
                    return
                    
                usuario = st.session_state.get('temp_usuario')
                if (usuario in st.session_state.usuarios and 
                    st.session_state.usuarios[usuario]['email'].lower() == email.lower()):
                    st.session_state['modo_login'] = 'redefinir_senha'
                    st.rerun()
                else:
                    st.error("Email não corresponde ao cadastrado")

    elif st.session_state.get('modo_login') == 'redefinir_senha':
        st.markdown("### 🔐 Nova Senha")
        with st.form("redefinir_senha_form"):
            nova_senha = st.text_input("Nova Senha", type="password",
                help="Mínimo 8 caracteres, incluindo letra maiúscula, minúscula e número")
            confirma_senha = st.text_input("Confirme a Nova Senha", type="password")
            
            if st.form_submit_button("Redefinir Senha"):
                if len(nova_senha) < 8:
                    st.error("A senha deve ter no mínimo 8 caracteres")
                    return
                    
                if nova_senha != confirma_senha:
                    st.error("As senhas não coincidem")
                    return
                    
                usuario = st.session_state['temp_usuario']
                st.session_state.usuarios[usuario]['senha'] = nova_senha
                st.session_state.usuarios[usuario]['primeiro_acesso'] = False
                salvar_usuarios()
                st.success("Senha redefinida com sucesso!")
                time.sleep(1)
                st.session_state.pop('modo_login')
                st.session_state.pop('temp_usuario')
                st.rerun()

def menu_lateral():
    with st.sidebar:
        st.markdown("""
            <style>
            section[data-testid="stSidebar"] {
                width: 6cm !important;
                background-color: #f8f9fa;
            }
            .sidebar-content {
                padding: 1rem;
            }
            .stButton > button {
                background-color: #2D2C74;
                color: white;
                border-radius: 4px;
            }
            #logout_button {
                width: 2.2cm !important;
                margin-left: 10px;
                font-size: 0.9rem;
                padding: 0.3rem 0.5rem;
            }
            [data-testid="collapsedControl"] {
                color: #2D2C74 !important;
            }
            div[data-testid="stSidebarNav"] {
                max-width: 6cm !important;
            }
            .user-info {
                position: fixed;
                bottom: 60px;
                padding: 10px;
                width: 5.5cm;
                background-color: #f8f9fa;
            }
            .bottom-content {
                position: fixed;
                bottom: 20px;
                width: 6cm;
                padding: 10px;
                background-color: #f8f9fa;
            }
            </style>
        """, unsafe_allow_html=True)

        st.markdown("### Menu")
        st.markdown("---")
        
        menu_items = ["📊 Dashboard", "📝 Requisições"]
        if st.session_state['perfil'] in ['administrador', 'comprador']:
            menu_items.extend(["🛒 Cotações", "✈️ Importação", "⚙️ Configurações"])
        
        menu = st.radio("", menu_items, label_visibility="collapsed")
        
        st.markdown("<div style='flex-grow: 1;'></div>", unsafe_allow_html=True)
        
        st.markdown(
            f"""
            <div class="user-info">
                <p style='margin: 0; font-size: 0.9rem; white-space: nowrap;'>👤 <b>Usuário:</b> {st.session_state.get('usuario', '')}</p>
                <p style='margin: 0; font-size: 0.9rem;'>🔑 <b>Perfil:</b> {st.session_state.get('perfil', '').title()}</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        with st.container():
            if st.button("🚪 Sair", key="logout_button", use_container_width=False):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

        return menu.split(" ")[-1]

def dashboard():
    st.title("Dashboard")
    
    # Definição dos ícones e cores dos status com transparência
    status_config = {
        'ABERTA': {'icon': '📋', 'cor': 'rgba(46, 204, 113, 0.7)'},  # Verde
        'EM ANDAMENTO': {'icon': '⏳', 'cor': 'rgba(241, 196, 15, 0.7)'},  # Amarelo
        'FINALIZADA': {'icon': '✅', 'cor': 'rgba(52, 152, 219, 0.7)'},  # Azul
        'RECUSADA': {'icon': '🚫', 'cor': 'rgba(231, 76, 60, 0.7)'},  # Vermelho
        'TOTAL': {'icon': '📉', 'cor': 'rgba(149, 165, 166, 0.7)'}  # Cinza
    }
    
    # Filtrar requisições baseado no perfil do usuário
    if st.session_state['perfil'] == 'vendedor':
        requisicoes_filtradas = [r for r in st.session_state.requisicoes if r['vendedor'] == st.session_state['usuario']]
        st.info(f"Visualizando requisições do vendedor: {st.session_state['usuario']}")
    else:
        requisicoes_filtradas = st.session_state.requisicoes
    
    # Container principal com duas colunas
    col_metricas, col_grafico = st.columns([1, 2])
    
    # Coluna das métricas com container fixo
    with col_metricas:
        st.markdown("""
            <style>
            .status-box {
                padding: 12px 15px;
                border-radius: 4px;
                margin-bottom: 5px;
                display: flex;
                align-items: center;
                min-height: 45px;
            }
            .status-content {
                display: flex;
                align-items: center;
                width: 100%;
            }
            .status-icon {
                font-size: 20px;
                margin-right: 12px;
                display: flex;
                align-items: center;
            }
            .status-text {
                color: #000000;
                font-weight: 500;
                flex-grow: 1;
                margin: 0;
                line-height: 20px;
            }
            .status-value {
                font-weight: bold;
                font-size: 18px;
                color: #2D2C74;
                margin-left: auto;
            }
            </style>
        """, unsafe_allow_html=True)
        
        with st.container():
            # Contadores com ícones
            abertas = len([r for r in requisicoes_filtradas if r['status'] == 'ABERTA'])
            em_andamento = len([r for r in requisicoes_filtradas if r['status'] == 'EM ANDAMENTO'])
            finalizadas = len([r for r in requisicoes_filtradas if r['status'] in ['FINALIZADA', 'RESPONDIDA']])
            recusadas = len([r for r in requisicoes_filtradas if r['status'] == 'RECUSADA'])
            total = len(requisicoes_filtradas)

            for status, valor in [
                ('ABERTA', abertas),
                ('EM ANDAMENTO', em_andamento),
                ('FINALIZADA', finalizadas),
                ('RECUSADA', recusadas),
                ('TOTAL', total)
            ]:
                st.markdown(f"""
                    <div class="status-box" style="background-color: {status_config[status]['cor']};">
                        <span class="status-icon">{status_config[status]['icon']}</span>
                        <span class="status-text">{status}</span>
                        <span class="status-value">{valor}</span>
                    </div>
                """, unsafe_allow_html=True)

    # Coluna do gráfico
    with col_grafico:
        # Criar duas colunas dentro da coluna do gráfico
        col_vazia, col_filtro = st.columns([3, 1])
        
        # Coluna do filtro (direita)
        with col_filtro:
            st.markdown('<div style="margin-top: 0px;">', unsafe_allow_html=True)
            periodo = st.selectbox(
                "PERÍODO",
                ["ÚLTIMOS 7 DIAS", "HOJE", "ÚLTIMOS 30 DIAS", "ÚLTIMOS 6 MESES"],
                index=0
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Coluna do gráfico (esquerda)
        with col_vazia:
            try:
                import plotly.graph_objects as go
                
                labels = ['Abertas', 'Em Andamento', 'Finalizadas']
                values = [abertas, em_andamento, finalizadas]
                colors = [
                    status_config['ABERTA']['cor'],
                    status_config['EM ANDAMENTO']['cor'],
                    status_config['FINALIZADA']['cor']
                ]

                fig = go.Figure(data=[go.Pie(
                    labels=labels,
                    values=values,
                    hole=.0,
                    marker=dict(colors=colors),
                    textinfo='value',
                    textposition='inside',
                    textfont_size=14,
                    hoverinfo='label+value',
                    showlegend=False
                )])

                fig.update_layout(
                    showlegend=False,
                    margin=dict(t=0, b=0, l=0, r=0),
                    height=350,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )

                st.plotly_chart(fig, use_container_width=True)
            except ImportError:
                st.error("Biblioteca Plotly não encontrada. Execute 'pip install plotly' para instalar.")

    # Tabela detalhada em toda a largura
    st.markdown("### Requisições Detalhadas")
    if requisicoes_filtradas:
        df_requisicoes = pd.DataFrame([{
            'Número': f"#{req['numero']}",
            'Data/Hora Criação': req['data_hora'],  # Mantém o formato original por enquanto
            'Cliente': req['cliente'],
            'Vendedor': req['vendedor'],
            'Status': req['status'],
            'Comprador': req.get('comprador_responsavel', '-'),
            'Data/Hora Resposta': req.get('data_hora_resposta', '-')
        } for req in requisicoes_filtradas])
        
        st.dataframe(
            df_requisicoes,
            hide_index=True,
            use_container_width=True,
            column_config={
                'Número': st.column_config.TextColumn('Número', width='small'),
                'Cliente': st.column_config.TextColumn('Cliente', width='medium'),
                'Vendedor': st.column_config.TextColumn('Vendedor', width='medium'),
                'Data/Hora': st.column_config.TextColumn('Data/Hora', width='medium'),
                'Status': st.column_config.TextColumn('Status', width='small'),
                'Comprador': st.column_config.TextColumn('Comprador', width='medium')
            }
        )
    else:
        st.info("Nenhuma requisição encontrada.")

def nova_requisicao():
    if st.session_state.get('modo_requisicao') != 'nova':
        st.title("Requisições")
        col1, col2 = st.columns([4,1])
        with col2:
            if st.button("🎯 Nova Requisição", type="primary", use_container_width=True):
                st.session_state['modo_requisicao'] = 'nova'
                if 'items_temp' not in st.session_state:
                    st.session_state.items_temp = []
                st.rerun()
        return

    st.title("Nova Requisição")
    col1, col2 = st.columns([1.5,1])
    with col1:
        cliente = st.text_input("Cliente", key="cliente").upper()
    with col2:
        st.write(f"**Vendedor:** {st.session_state.get('usuario', '')}")

    if st.session_state.get('show_qtd_error'):
        st.markdown('<p style="color: #ff4b4b; margin: 0; padding: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">PREENCHIMENTO OBRIGATÓRIO: Quantidade (apenas números)</p>', unsafe_allow_html=True)

    if 'items_temp' not in st.session_state:
        st.session_state.items_temp = []

    st.markdown("""
    <style>
    .requisicao-table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 0;
        table-layout: fixed;
        font-size: 14px;
    }
    .requisicao-table th, .requisicao-table td {
        border: 2px solid #2D2C74;
        padding: 1px !important;
        text-align: center;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        font-size: 14px;
        line-height: 2 !important;
    }
    .requisicao-table th {
        background-color: white;
        border: 2px solid #2D2C74;
        color: #2D2C74;
        font-weight: 600;
        height: 32px !important;
        text-align: center !important;
        font-size: 15px;
    }
    .stTextInput > div > div > input {
        border-radius: 4px !important;
        border: 2px solid #2D2C74 !important;
        padding: 2px 6px !important;
        height: 38px !important;
        background-color: white !important;
        font-size: 14px !important;
        margin: 0 !important;
        min-height: 38px !important;
    }
    .stTextInput.desc-input > div > div > input {
        text-align: left !important;
        padding-left: 8px !important;
    }
    .stTextInput:not(.desc-input) > div > div > input {
        text-align: center !important;
    }
    div[data-testid="column"] {
        padding: 0 !important;
        margin: 0 !important;
    }
    .stButton > button {
        border: 0px solid #2D2C74 !important;
        padding: 0 !important;
        height: 12px !important;
        min-width: 12px !important;
        width: 12px !important;
        line-height: 1 !important;
        font-size: 7px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        background-color: #2D2C74 !important;
        color: white !important;
        margin: 0 1px !important;
    }
    .stButton > button:hover {
        background-color: #1B81C5 !important;
        border-color: #1B81C5 !important;
        color: white !important;
    }
    .stButton > button[kind="primary"] {
        width: auto !important;
        padding: 0 16px !important;
        height: 32px !important;
        font-size: 14px !important;
        border: 2px solid #2D2C74 !important;
    }
    .stButton > button[kind="secondary"] {
        width: auto !important;
        padding: 0 16px !important;
        height: 32px !important;
        font-size: 14px !important;
        border: 2px solid #2D2C74 !important;
    }
    [data-testid="stHorizontalBlock"] {
        gap: 0px !important;
        padding: 0 !important;
        margin-bottom: 2px !important;
    }
    div.row-widget.stButton {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    div.row-widget {
        margin-bottom: 2px !important;
    }
    div[data-testid="column"] > div {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }
    [data-testid="column"] [data-testid="column"] {
        padding: 0 1px !important;
        margin: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("### Itens da Requisição")
    st.markdown("""
    <table class="requisicao-table">
    <thead>
    <tr>
    <th style="width: 5%">ITEM</th>
    <th style="width: 10%">CÓDIGO</th>
    <th style="width: 15%">CÓD. FABRICANTE</th>
    <th style="width: 35%">DESCRIÇÃO</th>
    <th style="width: 15%">MARCA</th>
    <th style="width: 8%">QTD</th>
    <th style="width: 7%">AÇÕES</th>
    </tr>
    </thead>
    </table>
    """, unsafe_allow_html=True)

    if st.session_state.items_temp:
        for idx, item in enumerate(st.session_state.items_temp):
            cols = st.columns([0.5, 1, 1.5, 3.5, 1.5, 0.8, 0.8])
            editing = st.session_state.get('editing_item') == idx

            with cols[0]:
                st.text_input("", value=str(item['item']), disabled=True, key=f"item_{idx}", label_visibility="collapsed")
            with cols[1]:
                if editing:
                    item['codigo'] = st.text_input("", value=item['codigo'], key=f"codigo_edit_{idx}", label_visibility="collapsed").upper()
                else:
                    st.text_input("", value=item['codigo'], disabled=True, key=f"codigo_{idx}", label_visibility="collapsed")
            with cols[2]:
                if editing:
                    item['cod_fabricante'] = st.text_input("", value=item['cod_fabricante'], key=f"fab_edit_{idx}", label_visibility="collapsed").upper()
                else:
                    st.text_input("", value=item['cod_fabricante'], disabled=True, key=f"fab_{idx}", label_visibility="collapsed")
            with cols[3]:
                if editing:
                    item['descricao'] = st.text_input("", value=item['descricao'], key=f"desc_edit_{idx}", label_visibility="collapsed", help="desc-input").upper()
                else:
                    st.text_input("", value=item['descricao'], disabled=True, key=f"desc_{idx}", label_visibility="collapsed", help="desc-input")
            with cols[4]:
                if editing:
                    item['marca'] = st.text_input("", value=item['marca'], key=f"marca_edit_{idx}", label_visibility="collapsed").upper()
                else:
                    st.text_input("", value=item['marca'], disabled=True, key=f"marca_{idx}", label_visibility="collapsed")
            with cols[5]:
                if editing:
                    quantidade = st.text_input("", value=str(item['quantidade']), key=f"qtd_edit_{idx}", label_visibility="collapsed")
                    if quantidade.isdigit():
                        item['quantidade'] = int(quantidade)
                else:
                    st.text_input("", value=str(item['quantidade']), disabled=True, key=f"qtd_{idx}", label_visibility="collapsed")
            with cols[6]:
                col1, col2 = st.columns([1,1])
                with col1:
                    if editing:
                        if st.button("✅", key=f"save_{idx}"):
                            st.session_state.pop('editing_item')
                            st.rerun()
                    else:
                        if st.button("✏️", key=f"edit_{idx}"):
                            st.session_state['editing_item'] = idx
                            st.rerun()
                with col2:
                    if not editing and st.button("❌", key=f"remove_{idx}"):
                        st.session_state.items_temp.pop(idx)
                        for i, item in enumerate(st.session_state.items_temp, 1):
                            item['item'] = i
                        st.rerun()

    proximo_item = len(st.session_state.items_temp) + 1
    cols = st.columns([0.5, 1, 1.57, 3.65, 1.5, 0.8, 0.8])
    with cols[0]:
        st.text_input("", value=str(proximo_item), disabled=True, key="item", label_visibility="collapsed")
    with cols[1]:
        codigo = st.text_input("", value=st.session_state.get('temp_codigo', ''), key="codigo", label_visibility="collapsed").upper()
    with cols[2]:
        cod_fabricante = st.text_input("", value=st.session_state.get('temp_cod_fab', ''), key="cod_fab", label_visibility="collapsed").upper()
    with cols[3]:
        descricao = st.text_input("", value=st.session_state.get('temp_desc', ''), key="desc", label_visibility="collapsed", help="desc-input").upper()
    with cols[4]:
        marca = st.text_input("", value=st.session_state.get('temp_marca', ''), key="marca", label_visibility="collapsed").upper()
    with cols[5]:
        quantidade = st.text_input("", value=st.session_state.get('temp_qtd', ''), key="qtd", label_visibility="collapsed")
    with cols[6]:
        if st.button("➕", key="add"):
            if not descricao:
                st.session_state['show_desc_error'] = True
                st.rerun()
            elif not quantidade or not quantidade.isdigit():
                st.session_state['show_qtd_error'] = True
                st.rerun()
            else:
                novo_item = {
                    'item': proximo_item,
                    'codigo': codigo,
                    'cod_fabricante': cod_fabricante,
                    'descricao': descricao,
                    'marca': marca,
                    'quantidade': int(quantidade),
                    'status': 'ABERTA'
                }
                st.session_state.items_temp.append(novo_item)
                st.session_state['show_desc_error'] = False
                st.session_state['show_qtd_error'] = False
                
                # Inicializa e limpa as variáveis temporárias
                if 'temp_codigo' not in st.session_state:
                    st.session_state.temp_codigo = ''
                if 'temp_cod_fab' not in st.session_state:
                    st.session_state.temp_cod_fab = ''
                if 'temp_desc' not in st.session_state:
                    st.session_state.temp_desc = ''
                if 'temp_marca' not in st.session_state:
                    st.session_state.temp_marca = ''
                if 'temp_qtd' not in st.session_state:
                    st.session_state.temp_qtd = ''
                
                st.session_state.temp_codigo = ''
                st.session_state.temp_cod_fab = ''
                st.session_state.temp_desc = ''
                st.session_state.temp_marca = ''
                st.session_state.temp_qtd = ''
                st.rerun()

    if st.session_state.items_temp:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Enviar", type="primary", use_container_width=True):
                if not cliente:
                    st.error("PREENCHIMENTO OBRIGATÓRIO: Cliente")
                    return
                nova_requisicao = {
                    'numero': get_next_requisition_number(),
                    'cliente': cliente,
                    'vendedor': st.session_state['usuario'],
                    'data_hora': get_data_hora_brasil(),
                    'status': 'ABERTA',
                    'items': st.session_state.items_temp.copy()
                }
                st.session_state.requisicoes.append(nova_requisicao)
                salvar_requisicoes()
                st.session_state.items_temp = []
                st.success("Requisição enviada com sucesso!")
                st.session_state['modo_requisicao'] = None
                st.rerun()
        with col2:
            if st.button("❌ Cancelar", type="secondary", use_container_width=True):
                st.session_state.items_temp = []
                st.session_state['modo_requisicao'] = None
                st.rerun()

def salvar_configuracoes():
    try:
        with open('configuracoes.json', 'w') as f:
            json.dump(st.session_state.config_sistema, f)
    except Exception as e:
        st.error(f"Erro ao salvar configurações: {e}")

def requisicoes():
    st.title("Requisições")
    
    # Atualização automática
    if 'ultima_atualizacao' not in st.session_state:
        st.session_state.ultima_atualizacao = time.time()
    
    if time.time() - st.session_state.ultima_atualizacao > 30:
        st.session_state.requisicoes = carregar_requisicoes()
        st.session_state.ultima_atualizacao = time.time()
        st.rerun()
    
    # Estilização
    st.markdown("""
        <style>
        .filtros-container {
            background-color: white;
            padding: 0px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 12px;
        }
        .requisicao-card {
            background-color: white;
            padding: 8px;
            border-radius: 8px;
            margin-bottom: 8px;
            border-left: 4px solid #2D2C74;
            transition: all 0.3s ease;
        }
        .requisicao-card:hover {
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .detalhes-container {
            background-color: white;
            padding: 0;
            border-radius: 8px;
            margin: 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .status-badge {
            padding: 3px 6px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 500;
        }
        .status-aberta { background-color: #e3f2fd; color: #1976d2; }
        .status-andamento { background-color: #fff3e0; color: #f57c00; }
        .status-finalizada { background-color: #e8f5e9; color: #2e7d32; }
        .status-recusada { background-color: #ffebee; color: #c62828; }
        .requisicao-info {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }
        .requisicao-numero {
            font-size: 14px;
            font-weight: 600;
            color: #2D2C74;
        }
        .requisicao-cliente {
            font-size: 14px;
            color: #666;
            margin-left: 8px;
        }
        .requisicao-data {
            font-size: 12px;
            color: #999;
        }
        .header-info {
            display: flex;
            justify-content: space-between;
            padding: 8px;
            background-color: white;
            border-bottom: 1px solid #eee;
            margin-bottom: 0;
        }
        .header-group { 
            flex: 1;
            padding: 0 8px;
        }
        .header-group p {
            margin: 3px 0;
            color: #444;
        }
        .requisicao-table {
            width: 100%;
            border-collapse: collapse;
            background-color: white;
            border-radius: 0 0 8px 8px;
            overflow: hidden;
            margin-top: 0;
        }
        .requisicao-table th {
            background-color: #2D2C74;
            color: white;
            padding: 8px;
            text-align: center;
            font-weight: 500;
            white-space: nowrap;
        }
        .requisicao-table td {
            padding: 6px 8px;
            border-bottom: 1px solid #eee;
            text-align: center;
            vertical-align: middle;
        }
        .requisicao-table td:nth-child(1),
        .requisicao-table th:nth-child(1) { width: 5%; }
        .requisicao-table td:nth-child(2),
        .requisicao-table th:nth-child(2) { width: 10%; }
        .requisicao-table td:nth-child(3),
        .requisicao-table th:nth-child(3) { width: 35%; }
        .requisicao-table td:nth-child(4),
        .requisicao-table th:nth-child(4) { width: 10%; }
        .requisicao-table td:nth-child(5),
        .requisicao-table th:nth-child(5) { width: 8%; text-align: center; }
        .requisicao-table td:nth-child(6),
        .requisicao-table th:nth-child(6) { width: 12%; text-align: right; }
        .requisicao-table td:nth-child(7),
        .requisicao-table th:nth-child(7) { width: 10%; text-align: center; }
        .requisicao-table td:nth-child(8),
        .requisicao-table th:nth-child(8) { width: 15%; }
        .valor-cell { 
            text-align: right; 
        }
        .action-buttons {
            padding: 10px;
            background-color: white;
            border-top: 1px solid #eee;
            margin-top: 8px;
        }
        .input-container {
            background-color: white;
            padding: 10px;
            border-radius: 8px;
            margin-top: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Botão Nova Requisição
    col1, col2 = st.columns([4,1])
    with col2:
        if st.button("📝 Nova Requisição", key="nova_req", type="primary"):
            st.session_state['modo_requisicao'] = 'nova'
            st.rerun()

    if st.session_state.get('modo_requisicao') == 'nova':
        nova_requisicao()
    else:
        # Filtros em container
        with st.container():
            st.markdown('<div class="filtros-container">', unsafe_allow_html=True)
            
            # Primeira linha de filtros
            col1, col2, col3, col4 = st.columns([2,2,3,1])
            with col1:
                numero_busca = st.text_input("🔍 Número da Requisição", key="busca_numero")
            with col2:
                cliente_busca = st.text_input("👥 Cliente", key="busca_cliente")
            with col3:
                data_col1, data_col2 = st.columns(2)
                with data_col1:
                    data_inicial = st.date_input("Data Inicial", value=None, key="data_inicial")
                with data_col2:
                    data_final = st.date_input("Data Final", value=None, key="data_final")
            with col4:
                st.markdown("<br>", unsafe_allow_html=True)
                buscar = st.button("🔎 Buscar", type="primary", use_container_width=True)

            # Status como chips coloridos
            status_opcoes = {
                "ABERTA": "🔵",
                "EM ANDAMENTO": "🟡",
                "FINALIZADA": "🟢",
                "RECUSADA": "🔴"
            }
            selected_status = st.multiselect(
                "Status",
                options=list(status_opcoes.keys()),
                default=["ABERTA", "EM ANDAMENTO"] if st.session_state['perfil'] != 'vendedor' else list(status_opcoes.keys()),
                format_func=lambda x: f"{status_opcoes[x]} {x}"
            )
            st.markdown('</div>', unsafe_allow_html=True)

        # Lógica de filtragem e exibição
        requisicoes_visiveis = []
        if st.session_state['perfil'] == 'vendedor':
            requisicoes_visiveis = [req for req in st.session_state.requisicoes if req['vendedor'] == st.session_state['usuario']]
        else:
            requisicoes_visiveis = st.session_state.requisicoes.copy()

        # Aplicar filtros
        if buscar:
            if numero_busca:
                requisicoes_visiveis = [req for req in requisicoes_visiveis if str(numero_busca) in str(req['numero'])]
            if cliente_busca:
                requisicoes_visiveis = [req for req in requisicoes_visiveis if cliente_busca.upper() in req['cliente'].upper()]
            if data_inicial and data_final:
                data_inicial_str = data_inicial.strftime('%d/%m/%Y')
                data_final_str = data_final.strftime('%d/%m/%Y')
                requisicoes_visiveis = [req for req in requisicoes_visiveis if data_inicial_str <= req['data_hora'].split()[0] <= data_final_str]

        if not requisicoes_visiveis:
            st.warning("Nenhuma requisição encontrada com os filtros selecionados.")

        # Ordenação por número em ordem decrescente
        requisicoes_visiveis.sort(key=lambda x: x['numero'], reverse=True)

        # Exibição das requisições
        for idx, req in enumerate(requisicoes_visiveis):
            if req['status'] in selected_status:
                st.markdown(f"""
                    <div class="requisicao-card" style="background-color: {
                        'rgba(46, 204, 113, 0.1)' if req['status'] == 'ABERTA'
                        else 'rgba(241, 196, 15, 0.1)' if req['status'] == 'EM ANDAMENTO'
                        else 'rgba(52, 152, 219, 0.1)' if req['status'] == 'FINALIZADA'
                        else 'rgba(231, 76, 60, 0.1)' if req['status'] == 'RECUSADA'
                        else 'white'}">
                        <div class="requisicao-info">
                            <div>
                                <span class="requisicao-numero">#{req['numero']}</span>
                                <span class="requisicao-cliente">{req['cliente']}</span>
                            </div>
                            <div>
                                <span class="status-badge status-{req['status'].lower()}">{req['status']}</span>
                            </div>
                        </div>
                        <div class="requisicao-data">
                            <span>Criado em: {req['data_hora']}</span>
                            <span>Vendedor: {req['vendedor']}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                if st.button(f"Ver Detalhes", key=f"detalhes_{req['numero']}_{idx}"):
                    # Fechar todos os outros detalhes
                    for key in list(st.session_state.keys()):
                        if key.startswith('mostrar_detalhes_') and key != f'mostrar_detalhes_{req["numero"]}':
                            st.session_state.pop(key)
                    # Abrir apenas o detalhe atual
                    st.session_state[f'mostrar_detalhes_{req["numero"]}'] = True
                    st.rerun()

                if st.session_state.get(f'mostrar_detalhes_{req["numero"]}', False):
                    with st.container():
                        st.markdown('<div class="detalhes-container">', unsafe_allow_html=True)
                        
                        # Cabeçalho com título e botão fechar
                        st.markdown('<div class="detalhes-header">', unsafe_allow_html=True)
                        col1, col2 = st.columns([3,1])
                        with col1:
                            st.markdown(f"### Requisição #{req['numero']} - {req['cliente']}")
                        with col2:
                            if st.button("❌ Fechar", key=f"fechar_{req['numero']}_{idx}"):
                                st.session_state.pop(f'mostrar_detalhes_{req["numero"]}')
                                st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)

                        # Informações da requisição
                        st.markdown(f"""
                            <div class="header-info">
                                <div class="header-group">
                                    <p><strong>Criado em:</strong> {req['data_hora']}</p>
                                    <p><strong>Vendedor:</strong> {req['vendedor']}</p>
                                </div>
                                <div class="header-group">
                                    <p><strong>Respondido em:</strong> {req.get('data_hora_resposta', '-')}</p>
                                    <p><strong>Comprador:</strong> {req.get('comprador_responsavel', '-')}</p>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)

                        # Itens da requisição
                        st.markdown('<div class="items-title">Itens da Requisição</div>', unsafe_allow_html=True)
                        if req['items']:
                            st.markdown("""
                                <table class="requisicao-table">
                                    <thead>
                                        <tr>
                                            <th>CÓDIGO</th>
                                            <th>CÓD. FABRICANTE</th>
                                            <th>DESCRIÇÃO</th>
                                            <th>MARCA</th>
                                            <th>QUANTIDADE</th>
                                            <th>PREÇO VENDA</th>
                                            <th>PRAZO</th>
                                            <th>OBSERVAÇÃO</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                            """, unsafe_allow_html=True)

                            for item in req['items']:
                                st.markdown(f"""
                                    <tr>
                                        <td>{item.get('codigo', '-')}</td>
                                        <td>{item.get('cod_fabricante', '-')}</td>
                                        <td style="text-align: left;">{item['descricao']}</td>
                                        <td>{item.get('marca', 'PC')}</td>
                                        <td class="valor-cell">{item['quantidade']}</td>
                                        <td class="valor-cell">R$ {item.get('venda_unit', 0):.2f}</td>
                                        <td>{item.get('prazo_entrega', '-')}</td>
                                        <td>{item.get('observacao', '-')}</td>
                                    </tr>
                                """, unsafe_allow_html=True)
                            st.markdown("</tbody></table>", unsafe_allow_html=True)

                        # Exibir justificativa de recusa apenas nos detalhes quando status for RECUSADA
                        if req['status'] == 'RECUSADA' and 'justificativa_recusa' in req:
                            st.markdown(f"""
                                <div style="background-color: rgba(231, 76, 60, 0.1); padding: 10px; border-radius: 4px; margin-top: 10px;">
                                    <p style="color: #c62828; margin: 0; font-weight: bold;">Justificativa da Recusa:</p>
                                    <p style="margin: 5px 0 0 0;">{req.get("justificativa_recusa", "")}</p>
                                    <p style="margin: 5px 0 0 0; font-size: 12px; color: #666;">
                                        Recusado por: {req.get("comprador_responsavel", "-")} em {req.get("data_hora_recusa", "-")}
                                    </p>
                                </div>
                            """, unsafe_allow_html=True)

                        # Botões de ação conforme o status
                        if st.session_state['perfil'] in ['administrador', 'comprador']:
                            st.markdown('<div class="action-buttons">', unsafe_allow_html=True)
                            if req['status'] == 'ABERTA':
                                col1, col2 = st.columns([1,1])
                                with col1:
                                    if st.button("✅ Aceitar", key=f"aceitar_{req['numero']}_{idx}", type="primary"):
                                        req['status'] = 'EM ANDAMENTO'
                                        req['comprador_responsavel'] = st.session_state['usuario']
                                        req['data_hora_aceite'] = get_data_hora_brasil()
                                        salvar_requisicoes()
                                        st.success("Requisição aceita com sucesso!")
                                        st.rerun()
                                with col2:
                                    if st.button("❌ Recusar", key=f"recusar_{req['numero']}_{idx}", type="secondary"):
                                        st.session_state[f'mostrar_justificativa_{req["numero"]}_{idx}'] = True
                                        st.rerun()

                                # Formulário de justificativa
                                if st.session_state.get(f'mostrar_justificativa_{req["numero"]}_{idx}', False):
                                    with st.form(key=f"form_justificativa_{req['numero']}_{idx}"):
                                        justificativa = st.text_area("Digite a justificativa da recusa", height=70)
                                        col1, col2 = st.columns(2)
                                        
                                        with col1:
                                            if st.form_submit_button("✅ Confirmar Recusa", type="primary", use_container_width=True):
                                                if justificativa.strip():
                                                    req['status'] = 'RECUSADA'
                                                    req['justificativa_recusa'] = justificativa
                                                    req['data_hora_recusa'] = get_data_hora_brasil()
                                                    req['comprador_responsavel'] = st.session_state['usuario']
                                                    salvar_requisicoes()
                                                    st.session_state.pop(f'mostrar_justificativa_{req["numero"]}_{idx}')
                                                    st.success("Requisição recusada com sucesso!")
                                                    st.rerun()
                                                else:
                                                    st.error("Por favor, preencha a justificativa")
                                        
                                        with col2:
                                            if st.form_submit_button("❌ Cancelar", type="secondary", use_container_width=True):
                                                st.session_state.pop(f'mostrar_justificativa_{req["numero"]}_{idx}')
                                                st.rerun()

                            elif req['status'] == 'EM ANDAMENTO':
                                st.markdown('<div class="input-container">', unsafe_allow_html=True)
                                # Interface para resposta do comprador
                                for item_idx, item in enumerate(req['items']):
                                    with st.container():
                                        col1, col2, col3, col4, col5 = st.columns([1,1,1,1,1])
                                        with col1:
                                            item['custo_unit'] = st.number_input(
                                                f"R$ UNIT Item {item['item']} *",
                                                value=item.get('custo_unit', 0.0),
                                                format="%.2f",
                                                key=f"custo_{req['numero']}_{item['item']}_{idx}_{item_idx}"
                                            )
                                        with col2:
                                            item['markup'] = st.number_input(
                                                f"% MARKUP Item {item['item']} *",
                                                value=item.get('markup', 0.0),
                                                format="%.2f",
                                                key=f"markup_{req['numero']}_{item['item']}_{idx}_{item_idx}"
                                            )
                                        with col3:
                                            item['prazo_entrega'] = st.date_input(
                                                "Prazo*",
                                                value=datetime.now(),
                                                min_value=datetime.now(),
                                                key=f"prazo_{req['numero']}_{item['item']}_{idx}_{item_idx}"
                                            )
                                        with col4:
                                            item['observacao'] = st.text_area(
                                                "Observações",
                                                value=item.get('observacao', ''),
                                                height=100,
                                                key=f"obs_{req['numero']}_{item['item']}_{idx}_{item_idx}"
                                            )
                                        with col5:
                                            item['venda_unit'] = item['custo_unit'] * (1 + item['markup']/100)
                                            st.text_input(
                                                "R$ VENDA UNIT",
                                                value=f"R$ {item['venda_unit']:.2f}",disabled=True,
                                                key=f"venda_{req['numero']}_{item['item']}_{idx}_{item_idx}"
                                            )
                                        if st.button("💾 Salvar Item", key=f"salvar_item_{req['numero']}_{item['item']}_{idx}_{item_idx}"):
                                            if item['custo_unit'] > 0 and item['markup'] > 0:
                                                item['salvo'] = True
                                                salvar_requisicoes()
                                                st.success(f"Item {item['item']} salvo com sucesso!")
                                                st.rerun()

                                # Botão de finalizar quando todos os itens estiverem salvos
                                todos_itens_salvos = all(item.get('salvo', False) for item in req['items'])
                                if todos_itens_salvos:
                                    if st.button("✅ Finalizar", key=f"finalizar_{req['numero']}_{idx}", type="primary"):
                                        req['status'] = 'FINALIZADA'
                                        req['data_hora_resposta'] = get_data_hora_brasil()
                                        if salvar_requisicoes():
                                            enviar_notificacao(
                                                f"Requisição {req['numero']} Finalizada",
                                                f"{st.session_state['usuario']} finalizou a requisição Nº{req['numero']} para o cliente {req['cliente']}",
                                                req['numero']
                                            )
                                            st.success("Requisição finalizada com sucesso!")
                                            st.rerun()
                                        else:
                                            st.error("Erro ao salvar a requisição. Tente novamente.")

def configurar_notificacoes():
    st.markdown("#### Configurações de Notificações")
    
    # Inicializar configuração no session_state
    if 'notificacoes_ativas' not in st.session_state:
        st.session_state.notificacoes_ativas = True
    
    # Toggle para ativar/desativar notificações
    notificacoes_ativas = st.toggle(
        "Ativar notificações na área de trabalho",
        value=st.session_state.notificacoes_ativas,
        key="toggle_notificacoes"
    )
    
    # Atualizar estado das notificações
    if notificacoes_ativas != st.session_state.notificacoes_ativas:
        st.session_state.notificacoes_ativas = notificacoes_ativas
        if notificacoes_ativas:
            solicitar_permissao_notificacao()
            st.success("Notificações ativadas com sucesso!")
        else:
            st.warning("Notificações desativadas")
                                        
def save_tema(tema):
    try:
        with open('tema.json', 'w', encoding='utf-8') as f:
            json.dump(tema, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar tema: {str(e)}")
        return False

def configuracoes():
    st.title("Configurações")
    
    # Menu principal
def configuracoes():
    st.title("Configurações")
    
    # Menu principal
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("👥 Usuários", type="primary", use_container_width=True):
            st.session_state['config_modo'] = 'usuarios'
            st.rerun()
    
    with col2:
        if st.button("🔑 Perfis", type="primary", use_container_width=True):
            st.session_state['config_modo'] = 'perfis'
            st.rerun()
    
    with col3:
        if st.button("⚙️ Sistema", type="primary", use_container_width=True):
            st.session_state['config_modo'] = 'sistema'
            st.rerun()

    # Seção de Usuários
    if st.session_state.get('config_modo') == 'usuarios':
        st.markdown("""
            <style>
            .stButton > button {
                background-color: #2D2C74 !important;
                color: white !important;
                border-radius: 4px !important;
                padding: 0.5rem 1rem !important;
                border: none !important;
            }
            .stButton > button:hover {
                background-color: #1B81C5 !important;
            }
            div[data-testid="stForm"] {
                background-color: #f8f9fa;
                padding: 1rem;
                border-radius: 8px;
                margin-bottom: 1rem;
            }
            [data-testid="baseButton-secondary"] {
                background-color: #2D2C74 !important;
                color: white !important;
            }
            [data-testid="baseButton-secondary"]:hover {
                background-color: #1B81C5 !important;
            }
            </style>
        """, unsafe_allow_html=True)

        st.markdown("### Gerenciamento de Usuários")
        
        # Botão de Cadastro
        if st.button("➕ Cadastrar Novo Usuário", type="primary", use_container_width=True):
            st.session_state['modo_usuario'] = 'cadastrar'
            st.rerun()

        # Formulário de Cadastro
        if st.session_state.get('modo_usuario') == 'cadastrar':
            with st.form("cadastro_usuario"):
                st.subheader("Cadastrar Novo Usuário")
                
                col1, col2, col3 = st.columns([2,2,1])
                with col1:
                    novo_usuario = st.text_input("Nome do Usuário").upper()
                with col2:
                    email = st.text_input("Email")
                with col3:
                    perfil = st.selectbox("Perfil", ['vendedor', 'comprador', 'administrador'])

                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("💾 Salvar", type="primary", use_container_width=True):
                        if novo_usuario and email:
                            if novo_usuario not in st.session_state.usuarios:
                                st.session_state.usuarios[novo_usuario] = {
                                    'senha': None,
                                    'perfil': perfil,
                                    'email': email,
                                    'ativo': True,
                                    'primeiro_acesso': True,
                                    'permissoes': get_permissoes_perfil(perfil)
                                }
                                salvar_usuarios()
                                st.success("Usuário cadastrado com sucesso!")
                                st.session_state['modo_usuario'] = None
                                st.rerun()
                            else:
                                st.error("Usuário já existe")
                        else:
                            st.error("Preencha todos os campos")
                
                with col2:
                    if st.form_submit_button("❌ Cancelar", type="primary", use_container_width=True):
                        st.session_state['modo_usuario'] = None
                        st.rerun()

        # Busca e Edição
        busca = st.text_input("🔍 Buscar usuário").upper()
        usuarios_filtrados = {k: v for k, v in st.session_state.usuarios.items() 
                            if busca in k.upper() or busca in v['email'].upper()}

        if usuarios_filtrados:
            st.markdown("#### Editar Usuário")
            usuario_editar = st.selectbox("Selecionar usuário para editar:", list(usuarios_filtrados.keys()))
            
            if usuario_editar:
                dados_usuario = st.session_state.usuarios[usuario_editar]
                col1, col2, col3, col4 = st.columns([2,2,1,1])
                
                with col1:
                    novo_nome = st.text_input("Nome", value=usuario_editar).upper()
                with col2:
                    novo_email = st.text_input("Email", value=dados_usuario['email'])
                with col3:
                    novo_perfil = st.selectbox("Perfil", 
                                             options=['vendedor', 'comprador', 'administrador'],
                                             index=['vendedor', 'comprador', 'administrador'].index(dados_usuario['perfil']))
                with col4:
                    novo_status = st.toggle("Ativo", value=dados_usuario['ativo'])

                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("💾 Salvar Alterações", type="primary", use_container_width=True):
                        if novo_nome != usuario_editar and novo_nome in st.session_state.usuarios:
                            st.error("Nome de usuário já existe")
                        else:
                            if novo_nome != usuario_editar:
                                st.session_state.usuarios[novo_nome] = st.session_state.usuarios.pop(usuario_editar)
                            st.session_state.usuarios[novo_nome].update({
                                'email': novo_email,
                                'perfil': novo_perfil,
                                'ativo': novo_status,
                                'permissoes': get_permissoes_perfil(novo_perfil)
                            })
                            salvar_usuarios()
                            st.success("Alterações salvas com sucesso!")
                            st.rerun()

                with col2:
                    if st.button("🔄 Reset Senha", type="primary", use_container_width=True):
                        st.session_state.usuarios[novo_nome]['senha'] = None
                        st.session_state.usuarios[novo_nome]['primeiro_acesso'] = True
                        salvar_usuarios()
                        st.success("Senha resetada com sucesso!")
                        st.rerun()

                with col3:
                    if st.button("❌ Excluir Usuário", type="primary", use_container_width=True):
                        if dados_usuario['perfil'] != 'administrador':
                            st.session_state.usuarios.pop(novo_nome)
                            salvar_usuarios()
                            st.success("Usuário excluído com sucesso!")
                            st.rerun()
                        else:
                            st.error("Não é possível excluir um administrador")

        # Tabela de Usuários
        st.markdown("#### Usuários Cadastrados")
        usuarios_df = pd.DataFrame([{
            'Usuário': usuario,
            'Email': dados['email'],
            'Perfil': dados['perfil'],
            'Status': '🟢 Ativo' if dados['ativo'] else '🔴 Inativo'
        } for usuario, dados in st.session_state.usuarios.items()])

        st.dataframe(
            usuarios_df,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Usuário": st.column_config.TextColumn("Usuário", width="medium"),
                "Email": st.column_config.TextColumn("Email", width="medium"),
                "Perfil": st.column_config.TextColumn("Perfil", width="small"),
                "Status": st.column_config.TextColumn("Status", width="small")
            }
        )

    # Seção de Perfis
    elif st.session_state.get('config_modo') == 'perfis':
        st.markdown("### Gerenciamento de Perfis")
        
        perfis = ['vendedor', 'comprador', 'administrador']
        perfil_selecionado = st.selectbox("Selecione o perfil para editar", perfis)
        
        st.markdown("#### Permissões de Acesso")
        st.markdown("Defina as telas que este perfil poderá acessar:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            permissoes = {}
            permissoes_atuais = get_permissoes_perfil(perfil_selecionado)
            
            st.markdown("##### Telas do Sistema")
            permissoes['dashboard'] = st.toggle(
                "📊 Dashboard",
                value='dashboard' in permissoes_atuais,
                key=f"perm_dashboard_{perfil_selecionado}"
            )
            permissoes['requisicoes'] = st.toggle(
                "📝 Requisições",
                value='requisicoes' in permissoes_atuais,
                key=f"perm_requisicoes_{perfil_selecionado}"
            )
            permissoes['cotacoes'] = st.toggle(
                "🛒 Cotações",
                value='cotacoes' in permissoes_atuais,
                key=f"perm_cotacoes_{perfil_selecionado}"
            )
            permissoes['importacao'] = st.toggle(
                "✈️ Importação",
                value='importacao' in permissoes_atuais,
                key=f"perm_importacao_{perfil_selecionado}"
            )
            permissoes['configuracoes'] = st.toggle(
                "⚙️ Configurações",
                value='configuracoes' in permissoes_atuais,
                key=f"perm_configuracoes_{perfil_selecionado}"
            )
        
        with col2:
            st.markdown("##### Permissões Administrativas")
            permissoes['editar_usuarios'] = st.toggle(
                "👥 Editar Usuários",
                value='editar_usuarios' in permissoes_atuais,
                key=f"perm_editar_usuarios_{perfil_selecionado}"
            )
            permissoes['excluir_usuarios'] = st.toggle(
                "❌ Excluir Usuários",
                value='excluir_usuarios' in permissoes_atuais,
                key=f"perm_excluir_usuarios_{perfil_selecionado}"
            )
            permissoes['editar_perfis'] = st.toggle(
                "🔑 Editar Perfis",
                value='editar_perfis' in permissoes_atuais,
                key=f"perm_editar_perfis_{perfil_selecionado}"
            )

        if st.button("💾 Salvar Permissões", type="primary"):
            novas_permissoes = [k for k, v in permissoes.items() if v]
            save_perfis_permissoes(perfil_selecionado, novas_permissoes)
            st.success(f"Permissões do perfil {perfil_selecionado} atualizadas com sucesso!")
            st.rerun()

    # Seção de Sistema
    elif st.session_state.get('config_modo') == 'sistema':
        st.markdown("### Configurações do Sistema")
        
        # Se for administrador, mostra todas as abas
        if st.session_state['perfil'] == 'administrador':
            tab1, tab2, tab3, tab4 = st.tabs(["🔔 Notificações", "🎨 Cores", "📝 Fontes", "📐 Layout"])
            
            with tab1:
                configurar_notificacoes()
            
            with tab2:
                st.markdown("#### Cores do Sistema")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    cor_primaria = st.color_picker("Primária", "#2D2C74", key="cor_primaria")
                    cor_texto = st.color_picker("Texto", "#000000", key="cor_texto")
                with col2:
                    cor_secundaria = st.color_picker("Secundária", "#1B81C5", key="cor_secundaria")
                    cor_botoes = st.color_picker("Botões", "#2D2C74", key="cor_botoes")
                with col3:
                    cor_fundo = st.color_picker("Fundo", "#f8f9fa", key="cor_fundo")
                    cor_campos = st.color_picker("Campos", "#ffffff", key="cor_campos")

                st.markdown("#### Preview")
                preview_html = f"""
                    <div style="padding: 20px; border-radius: 10px; background-color: {cor_fundo};">
                        <h4 style="color: {cor_texto};">Exemplo de Visualização</h4>
                        <button style="background-color: {cor_botoes}; color: white; padding: 10px; border: none; border-radius: 5px; margin: 5px;">Botão</button>
                        <input type="text" placeholder="Campo de texto" style="background-color: {cor_campos}; border: 1px solid {cor_secundaria}; padding: 5px; margin: 5px;">
                    </div>
                """
                st.markdown(preview_html, unsafe_allow_html=True)

            with tab3:
                col1, col2 = st.columns(2)
                with col1:
                    familia_fonte = st.selectbox(
                        "Fonte",
                        ["Inter", "Roboto", "Open Sans", "Lato", "Montserrat"]
                    )
                    tamanho_fonte = st.number_input("Tamanho Base", min_value=12, max_value=20, value=16)
                
                with col2:
                    st.markdown("#### Preview da Fonte")
                    preview_font_html = f"""
                        <div style="font-family: {familia_fonte}; font-size: {tamanho_fonte}px;">
                            <p>Exemplo de texto com a fonte {familia_fonte}<br>
                            ABCDEFGHIJKLMNOPQRSTUVWXYZ<br>
                            abcdefghijklmnopqrstuvwxyz<br>
                            0123456789</p>
                        </div>
                    """
                    st.markdown(preview_font_html, unsafe_allow_html=True)

            with tab4:
                col1, col2 = st.columns(2)
                with col1:
                    largura_maxima = st.number_input("Largura Máxima", min_value=800, max_value=1600, value=1200, step=100)
                    padding = st.number_input("Espaçamento", min_value=1, max_value=5, value=2)
                    raio_borda = st.number_input("Raio da Borda", min_value=0, max_value=20, value=4)
                
                with col2:
                    st.markdown("#### Preview do Layout")
                    preview_layout = f"""
                        <div style="max-width: {largura_maxima}px; padding: {padding * 10}px; background-color: {cor_fundo}; border-radius: {raio_borda}px;">
                            <div style="background-color: {cor_secundaria}; padding: 10px; border-radius: {raio_borda}px; margin-bottom: 10px;">
                                Elemento 1
                            </div>
                            <div style="background-color: {cor_secundaria}; padding: 10px; border-radius: {raio_borda}px;">
                                Elemento 2
                            </div>
                        </div>
                    """
                    st.markdown(preview_layout, unsafe_allow_html=True)

            if st.button("💾 Salvar Configurações de Tema", type="primary"):
                tema = {
                    'cores': {
                        'primaria': cor_primaria,
                        'secundaria': cor_secundaria,
                        'fundo': cor_fundo,
                        'texto': cor_texto,
                        'botoes': cor_botoes,
                        'campos': cor_campos
                    },
                    'fonte': {
                        'familia': familia_fonte,
                        'tamanho': tamanho_fonte
                    },
                    'layout': {
                        'largura_maxima': largura_maxima,
                        'padding': padding,
                        'raio_borda': raio_borda
                    }
                }
                save_tema(tema)
                st.success("Configurações de tema atualizadas com sucesso!")
                st.rerun()
        else:
            # Para vendedores e compradores, mostra apenas notificações
            tab1 = st.tabs(["🔔 Notificações"])[0]
            with tab1:
                configurar_notificacoes()

def main():
    if 'usuario' not in st.session_state:
        tela_login()
    else:
        solicitar_permissao_notificacao()
        menu = menu_lateral()
        
        if menu == "Dashboard":
            dashboard()
        elif menu == "Requisições":
            requisicoes()
        elif menu == "Cotações":
            st.title("Cotações")
            st.info("Funcionalidade em desenvolvimento")
        elif menu == "Importação":
            st.title("Importação")
            st.info("Funcionalidade em desenvolvimento")
        elif menu == "Configurações":
            configuracoes()

if __name__ == "__main__":
    main()
