import streamlit as st
import sqlite3
import pandas as pd
import time
import zipfile
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import pytz
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import plotly.graph_objects as go
import shutil
import glob
from streamlit_autorefresh import st_autorefresh

def inicializar_banco():
    try:
        conn = sqlite3.connect('requisicoes.db')
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS requisicoes (
            numero INTEGER PRIMARY KEY,
            cliente TEXT,
            vendedor TEXT,
            data_hora TEXT,
            status TEXT,
            items TEXT,
            observacoes_vendedor TEXT,
            comprador_responsavel TEXT,
            data_hora_resposta TEXT,
            justificativa_recusa TEXT,
            observacao_geral TEXT
        )
        ''')
        conn.commit()
        conn.close()
        print("Banco de dados inicializado com sucesso")
    except Exception as e:
        print(f"Erro ao inicializar banco de dados: {str(e)}")

def mostrar_espaco_armazenamento():
    import plotly.graph_objects as go
    import os
    import glob
    
    # Calcula o espaço usado pelos backups
    backup_files = glob.glob('backup/*')
    espaco_usado = sum(os.path.getsize(f) for f in backup_files) / (1024 * 1024)  # Converte para MB
    
    # Define o espaço total (exemplo: 1000 MB)
    espaco_total = 1000  # MB
    espaco_disponivel = espaco_total - espaco_usado
    
    # Cria o gráfico de rosca
    fig = go.Figure(data=[go.Pie(
        labels=['Disponível', 'Usado'],
        values=[espaco_disponivel, espaco_usado],
        hole=.7,
        marker_colors=['#66b3ff', '#ff9999'],
        textinfo='percent',
        textfont_size=20,
        showlegend=True
    )])
    
    # Atualiza o layout
    fig.update_layout(
        title=dict(
            text="Espaço de Armazenamento",
            y=0.95,
            x=0.5,
            xanchor='center',
            yanchor='top',
            font=dict(size=16)
        ),
        annotations=[dict(
            text=f'{espaco_usado:.1f}MB<br>de {espaco_total}MB',
            x=0.5,
            y=0.5,
            font_size=14,
            showarrow=False
        )],
        height=300,
        margin=dict(t=50, l=0, r=0, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

EMAIL_CONFIG = {
    'SMTP_SERVER': 'smtp-mail.outlook.com',
    'SMTP_PORT': 587,
    'SMTP_ENCRYPTION': 'STARTTLS',
    'EMAIL': 'alerta@jetfrio.com.br',
    'PASSWORD': 'Jet@2007'
}

def enviar_email_requisicao(requisicao, tipo_notificacao):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['EMAIL']
        msg['Subject'] = f"SUA REQUISIÇÃO Nº{requisicao['numero']} FOI {tipo_notificacao.upper()}"
        
        # Define destinatários
        vendedor_email = st.session_state.usuarios[requisicao['vendedor']]['email']
        comprador_email = st.session_state.usuarios.get(requisicao.get('comprador_responsavel', ''), {}).get('email', '')
        
        msg['To'] = vendedor_email
        if comprador_email:
            msg['Cc'] = comprador_email
        
        # Cria tabela HTML dos itens
        html = f"""
        <html>
            <body>
                <h2>Requisição #{requisicao['numero']}</h2>
                <p><strong>Cliente:</strong> {requisicao['cliente']}</p>
                <p><strong>Status:</strong> {requisicao['status']}</p>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0;">
                    <p><strong>Criado por:</strong> {requisicao['vendedor']}</p>
                    <p><strong>Data/Hora Criação:</strong> {requisicao['data_hora']}</p>
                    <p><strong>Respondido por:</strong> {requisicao.get('comprador_responsavel', '-')}</p>
                    <p><strong>Data/Hora Resposta:</strong> {requisicao.get('data_hora_resposta', '-')}</p>
                </div>

                <table border="1" style="border-collapse: collapse; width: 100%;">
                    <tr>
                        <th>Item</th>
                        <th>Código</th>
                        <th>Descrição</th>
                        <th>Marca</th>
                        <th>Qtd</th>
                        <th>Valor Unit.</th>
                        <th>Total</th>
                        <th>Prazo</th>
                    </tr>
        """
        
        for item in requisicao['items']:
            html += f"""
                <tr>
                    <td>{item['item']}</td>
                    <td>{item['codigo']}</td>
                    <td>{item['descricao']}</td>
                    <td>{item['marca']}</td>
                    <td>{item['quantidade']}</td>
                    <td>R$ {item.get('venda_unit', 0):.2f}</td>
                    <td>R$ {item.get('venda_unit', 0) * item['quantidade']:.2f}</td>
                    <td>{item.get('prazo_entrega', '-')}</td>
                </tr>
            """
        
        html += """
                </table>
        """

        # Adiciona observações se existirem
        if requisicao.get('observacao_geral'):
            html += f"""
                <div style="margin-top: 20px; padding: 15px; background-color: #f8f9fa; border-left: 4px solid #2D2C74;">
                    <h3 style="margin-top: 0; color: #2D2C74;">Observações do Comprador:</h3>
                    <p style="margin-bottom: 0;">{requisicao['observacao_geral']}</p>
                </div>
            """

        # Adiciona justificativa de recusa se existir
        if tipo_notificacao.upper() == 'RECUSADA' and requisicao.get('justificativa_recusa'):
            html += f"""
                <div style="margin-top: 20px; padding: 15px; background-color: #ffebee; border-left: 4px solid #c62828;">
                    <h3 style="margin-top: 0; color: #c62828;">Justificativa da Recusa:</h3>
                    <p style="margin-bottom: 0;">{requisicao['justificativa_recusa']}</p>
                </div>
            """

        html += """
            </body>
        </html>
        """
        
        msg.attach(MIMEText(html, 'html'))
        
        # Envia o email
        with smtplib.SMTP(EMAIL_CONFIG['SMTP_SERVER'], EMAIL_CONFIG['SMTP_PORT']) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['EMAIL'], EMAIL_CONFIG['PASSWORD'])
            server.send_message(msg)
        
        return True
    except Exception as e:
        st.error(f"Erro ao enviar email: {str(e)}")
        return False

# Configuração da página
st.set_page_config(
    page_title="PORTAL - JETFRIO",
    layout="wide",
    initial_sidebar_state="expanded"
)

def init_notification_js():
    st.components.v1.html("""
        <script>
        if (!window.Notification) {
            console.log('Este navegador não suporta notificações');
        } else {
            if (Notification.permission !== 'granted' && Notification.permission !== 'denied') {
                Notification.requestPermission().then(function(permission) {
                    if (permission === 'granted') {
                        new Notification('Notificações Ativadas', {
                            body: 'Você receberá notificações sobre suas requisições',
                            icon: '/favicon.ico'
                        });
                    }
                });
            }
        }

        window.createNotification = function(title, body) {
            if (Notification.permission === 'granted') {
                new Notification(title, {
                    body: body,
                    icon: '/favicon.ico',
                    requireInteraction: true
                });
            }
        }
        </script>
    """, height=0)

def notify(title, message):
    if st.session_state.get('notificacoes_ativas', True):
        js = f"""
        <script>
        if (typeof window.createNotification === 'function') {{
            window.createNotification("{title}", "{message}");
        }}
        </script>
        """
        st.components.v1.html(js, height=0)

# Estilo personalizado com adaptação ao tema
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
* {
    font-family: 'Inter', sans-serif;
}
.stApp {
    transition: all 0.3s ease-in-out;
}
.main {
    padding: 2rem;
    background-color: var(--background-color);
    border-radius: 8px;
    margin: 1rem;
}
.sidebar {
    background-color: var(--background-color);
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
    background-color: var(--background-color);
    padding: 1.5rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* Adaptação para inputs */
.stTextInput input,
.stPasswordInput input {
    color: var(--text-color) !important;
    background-color: var(--background-color) !important;
    border-color: var(--secondary-background-color) !important;
}

/* Adaptação para textos */
.stMarkdown, .stText {
    color: var(--text-color) !important;
}

/* Adaptação para containers */
[data-testid="stForm"] {
    background-color: var(--background-color) !important;
    border: 1px solid var(--secondary-background-color) !important;
}

/* Adaptação para sidebar */
section[data-testid="stSidebar"] {
    background-color: var(--background-color) !important;
}

/* Adaptação para cards */
div.element-container {
    color: var(--text-color) !important;
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
        'vendedor': ['dashboard', 'requisicoes', 'configuracoes'],
        'comprador': ['dashboard', 'requisicoes', 'cotacoes', 'importacao', 'configuracoes'],
        'administrador': ['dashboard', 'requisicoes', 'cotacoes', 'importacao', 'configuracoes', 'editar_usuarios', 'excluir_usuarios', 'editar_perfis']
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

def verificar_diretorios():
    try:
        os.makedirs('backup', exist_ok=True)
        return True
    except Exception as e:
        st.error(f"Erro ao criar diretório: {str(e)}")
        return False

def verificar_arquivos():
    try:
        arquivos_necessarios = ['requisicoes.json', 'usuarios.json', 'ultimo_numero.json']
        for arquivo in arquivos_necessarios:
            if not os.path.exists(arquivo):
                with open(arquivo, 'w', encoding='utf-8') as f:
                    json.dump([] if arquivo == 'requisicoes.json' else {}, f, ensure_ascii=False, indent=4)
        os.makedirs('backup', exist_ok=True)
        return True
    except Exception as e:
        st.error(f"Erro ao verificar arquivos: {str(e)}")
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
        verificar_diretorios()  # Verifica e cria diretórios necessários
        
        if not os.path.exists('usuarios.json'):
            with open('usuarios.json', 'w', encoding='utf-8') as f:
                json.dump(usuario_padrao, f, ensure_ascii=False, indent=4)
            print("Arquivo usuarios.json criado com usuário padrão")
            return usuario_padrao

        with open('usuarios.json', 'r', encoding='utf-8') as f:
            usuarios = json.load(f)
            if not usuarios:
                print("Arquivo vazio, retornando usuário padrão")
                return usuario_padrao
            
            if 'ZAQUEU SOUZA' not in usuarios:
                usuarios['ZAQUEU SOUZA'] = usuario_padrao['ZAQUEU SOUZA']
                with open('usuarios.json', 'w', encoding='utf-8') as f:
                    json.dump(usuarios, f, ensure_ascii=False, indent=4)
            
            return usuarios
            
    except Exception as e:
        print(f"Erro ao carregar usuários: {str(e)}")
        return usuario_padrao

def verificar_sistema():
    # Verifica diretórios necessários
    os.makedirs('backup', exist_ok=True)
    
    # Verifica arquivo de requisições
    if not os.path.exists('requisicoes.json'):
        with open('requisicoes.json', 'w', encoding='utf-8') as f:
            json.dump([], f)
    
    # Verifica integridade e restaura se necessário
    if not verificar_integridade_json():
        restaurar_ultimo_backup()

def salvar_usuarios():
    try:
        backup_file = 'usuarios.json.bak'
        # Fazer backup do arquivo atual
        if os.path.exists('usuarios.json'):
            shutil.copy2('usuarios.json', backup_file)
            
        # Salvar os dados
        with open('usuarios.json', 'w', encoding='utf-8') as f:
            usuarios_para_salvar = {
                usuario: {**dados, 'senha': str(dados['senha'])} 
                for usuario, dados in st.session_state.usuarios.items()
            }
            json.dump(usuarios_para_salvar, f, ensure_ascii=False, indent=4)
            
        # Verificar integridade
        with open('usuarios.json', 'r', encoding='utf-8') as f:
            json.load(f)  # Tenta ler o arquivo para verificar se está válido
            
        # Remove backup se tudo deu certo
        if os.path.exists(backup_file):
            os.remove(backup_file)
            
        return True
    except Exception as e:
        # Restaura backup em caso de erro
        if os.path.exists(backup_file):
            shutil.copy2(backup_file, 'usuarios.json')
        st.error(f"Erro ao salvar usuários: {str(e)}")
        return False
    
def carregar_requisicoes():
    try:
        with open('requisicoes.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Erro ao carregar requisições: {str(e)}")
        return []
    try:
        conn = sqlite3.connect('requisicoes.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM requisicoes')
        requisicoes = []
        for row in cursor.fetchall():
            requisicao = {
                'numero': row[0],
                'cliente': row[1],
                'vendedor': row[2],
                'data_hora': row[3],
                'status': row[4],
                'items': json.loads(row[5]),
                'observacoes_vendedor': row[6],
                'comprador_responsavel': row[7],
                'data_hora_resposta': row[8],
                'justificativa_recusa': row[9],
                'observacao_geral': row[10]
            }
            requisicoes.append(requisicao)
        conn.close()
        return requisicoes
    except sqlite3.OperationalError:
        # Se a tabela não existir, inicializa o banco e tenta novamente
        inicializar_banco()
        return carregar_requisicoes()
    except Exception as e:
        st.error(f"Erro ao carregar requisições: {str(e)}")
        return []

def backup_requisicoes():
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f'backup/requisicoes_backup_{timestamp}.json'
        os.makedirs('backup', exist_ok=True)
        
        if os.path.exists('requisicoes.json'):
            shutil.copy2('requisicoes.json', backup_file)
            return True
        return False
    except Exception as e:
        print(f"Erro no backup: {str(e)}")
        return False

def limpar_backups_antigos(dias_retencao=30):
    backup_files = glob.glob('backup/requisicoes_backup_*.json')
    data_limite = datetime.now() - timedelta(days=dias_retencao)
    
    for arquivo in backup_files:
        data_arquivo = datetime.fromtimestamp(os.path.getctime(arquivo))
        if data_arquivo < data_limite:
            os.remove(arquivo)

def verificar_integridade_json():
    try:
        with open('requisicoes.json', 'r', encoding='utf-8') as f:
            json.load(f)
        return True
    except:
        return False

def backup_automatico(dados):
    backup_dir = 'backup/'
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    arquivos_backup = {
        'usuarios': 'usuarios.json',
        'perfis': 'perfis.json',
        'requisicoes': 'requisicoes.json',
        'ultimo_numero': 'ultimo_numero.json'
    }
    
    backup_file = os.path.join(backup_dir, f'backup_{timestamp}.zip')
    
    try:
        with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for nome, arquivo in arquivos_backup.items():
                if os.path.exists(arquivo):
                    zipf.write(arquivo)
        
        return backup_file, os.path.getsize(backup_file)
    except Exception as e:
        st.error(f"Erro ao realizar backup: {str(e)}")
        return None, 0

def restaurar_ultimo_backup():
    backup_dir = 'backup/'
    backups = [f for f in os.listdir(backup_dir) if f.endswith('.zip')]
    if backups:
        ultimo_backup = sorted(backups)[-1]
        backup_path = os.path.join(backup_dir, ultimo_backup)
        
        try:
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                zipf.extractall()
            return True
        except Exception as e:
            st.error(f"Erro ao restaurar backup: {str(e)}")
            return False
    return False

def salvar_requisicao(requisicao):
    conn = sqlite3.connect('requisicoes.db')
    cursor = conn.cursor()
    cursor.execute('''
    INSERT OR REPLACE INTO requisicoes 
    (numero, cliente, vendedor, data_hora, status, items, observacoes_vendedor, 
    comprador_responsavel, data_hora_resposta, justificativa_recusa, observacao_geral)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        requisicao['numero'],
        requisicao['cliente'],
        requisicao['vendedor'],
        requisicao['data_hora'],
        requisicao['status'],
        json.dumps(requisicao['items']),
        requisicao.get('observacoes_vendedor', ''),
        requisicao.get('comprador_responsavel', ''),
        requisicao.get('data_hora_resposta', ''),
        requisicao.get('justificativa_recusa', ''),
        requisicao.get('observacao_geral', '')
    ))
    conn.commit()
    conn.close()
    return True

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

# Inicialização de dados
if 'usuarios' not in st.session_state:
    st.session_state.usuarios = carregar_usuarios()
    verificar_diretorios()  # Garante que os diretórios necessários existam
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
            
            if user_data.get('primeiro_acesso', True) or user_data.get('senha') is None:
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

def menu_lateral():
    with st.sidebar:
        st.markdown("""
            <style>
            section[data-testid="stSidebar"] {
                width: 6cm !important;
                background-color: var(--background-color) !important;
            }
            .sidebar-content {
                padding: 1rem;
                background-color: var(--background-color) !important;
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
                color: var(--text-color) !important;
            }
            div[data-testid="stSidebarNav"] {
                max-width: 6cm !important;
                background-color: var(--background-color) !important;
            }
            .user-info {
                position: fixed;
                bottom: 60px;
                padding: 10px;
                width: 5.5cm;
                background-color: var(--background-color) !important;
                color: var(--text-color) !important;
            }
            .user-info p {
                color: var(--text-color) !important;
            }
            .bottom-content {
                position: fixed;
                bottom: 20px;
                width: 6cm;
                padding: 10px;
                background-color: var(--background-color) !important;
            }
            div[data-testid="stSidebarUserContent"] {
                background-color: var(--background-color) !important;
            }
            .stRadio > label {
                color: var(--text-color) !important;
            }
            </style>
        """, unsafe_allow_html=True)

        st.markdown("### Menu")
        st.markdown("---")
        
        menu_items = ["📊 Dashboard", "📝 Requisições", "⚙️ Configurações"]
        if st.session_state['perfil'] in ['administrador', 'comprador']:
            menu_items.insert(-1, "🛒 Cotações")
            menu_items.insert(-1, "✈️ Importação")
        
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
                
                # Dados para o gráfico
                dados_grafico = []
                if abertas > 0:
                    dados_grafico.append(('Abertas', abertas, status_config['ABERTA']['cor']))
                if em_andamento > 0:
                    dados_grafico.append(('Em Andamento', em_andamento, status_config['EM ANDAMENTO']['cor']))
                if finalizadas > 0:
                    dados_grafico.append(('Finalizadas', finalizadas, status_config['FINALIZADA']['cor']))
                if recusadas > 0:
                    dados_grafico.append(('Recusadas', recusadas, status_config['RECUSADA']['cor']))

                # Se não houver dados, incluir todos os status com valor 0
                if not dados_grafico:
                    dados_grafico = [
                        ('Abertas', 0, status_config['ABERTA']['cor']),
                        ('Em Andamento', 0, status_config['EM ANDAMENTO']['cor']),
                        ('Finalizadas', 0, status_config['FINALIZADA']['cor']),
                        ('Recusadas', 0, status_config['RECUSADA']['cor'])
                    ]

                labels = [d[0] for d in dados_grafico]
                values = [d[1] for d in dados_grafico]
                colors = [d[2] for d in dados_grafico]

                fig = go.Figure(data=[go.Pie(
                    labels=labels,
                    values=values,
                    hole=.0,
                    marker=dict(colors=colors),
                    textinfo='value+label',
                    textposition='inside',
                    textfont_size=13,
                    hoverinfo='label+value+percent',
                    showlegend=True
                )])

                fig.update_layout(
                    showlegend=False,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    ),
                    margin=dict(t=30, b=0, l=0, r=0),
                    height=350,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )

                fig.update_traces(
                    textposition='inside',
                    pull=[0.00] * len(dados_grafico)
                )

                st.plotly_chart(fig, use_container_width=True)
            except ImportError:
                st.error("Biblioteca Plotly não encontrada. Execute 'pip install plotly' para instalar.")

    # Tabela detalhada em toda a largura
    st.markdown("### Requisições Detalhadas")
    if requisicoes_filtradas:
        # Ordenar requisições por número em ordem decrescente
        requisicoes_filtradas = sorted(requisicoes_filtradas, key=lambda x: x['numero'], reverse=True)
        
        df_requisicoes = pd.DataFrame([{
            'Número': f"{req['numero']}",
            'Data/Hora Criação': req['data_hora'],
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
                'Data/Hora Criação': st.column_config.TextColumn('Data/Hora Criação', width='medium'),
                'Status': st.column_config.TextColumn('Status', width='small'),
                'Comprador': st.column_config.TextColumn('Comprador', width='medium'),
                'Data/Hora Resposta': st.column_config.TextColumn('Data/Hora Resposta', width='medium')
            }
        )
    else:
        st.info("Nenhuma requisição encontrada.")

def nova_requisicao():
    # Inicializa a variável de observações no início da função
    observacoes_vendedor = ""
    
    if st.session_state.get('modo_requisicao') != 'nova':
        st.title("REQUISIÇÕES")
        col1, col2 = st.columns([4,1])
        with col2:
            if st.button("🎯 NOVA REQUISIÇÃO", type="primary", use_container_width=True):
                st.session_state['modo_requisicao'] = 'nova'
                if 'items_temp' not in st.session_state:
                    st.session_state.items_temp = []
                st.rerun()
        return

    st.title("NOVA REQUISIÇÃO")
    col1, col2 = st.columns([1.5,1])
    with col1:
        cliente = st.text_input("CLIENTE", key="cliente").upper()
    with col2:
        st.write(f"**VENDEDOR:** {st.session_state.get('usuario', '')}")

    col1, col2 = st.columns(2)
    with col2:
        if st.button("❌ CANCELAR", type="secondary", use_container_width=True):
            st.session_state.items_temp = []
            st.session_state['modo_requisicao'] = None
            st.rerun()

    if st.session_state.get('show_qtd_error'):
        st.markdown('<p style="color: #ff4b4b; margin: 0; padding: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">PREENCHIMENTO OBRIGATÓRIO: QUANTIDADE</p>', unsafe_allow_html=True)

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
        border: 2px solid #2D2C74 !important;
        padding: 1px !important;
        text-align: center;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        font-size: 14px;
        line-height: 2 !important;
        background-color: var(--background-color);
        color: var(--text-color);
    }
    .requisicao-table th {
        background-color: white;
        border: 2px solid #2D2C74;
        color: #2D2C74;
        font-weight: 600;
        height: 32px !important;
        text-align: center !important;
        font-size: 15px;
        text-transform: uppercase;
    }
    .stTextInput > div > div > input {
        border-radius: 4px !important;
        border: 1px solid var(--secondary-background-color) !important;
        padding: 2px 6px !important;
        height: 38px !important;
        background-color: var(--background-color) !important;
        color: var(--text-color) !important;
        font-size: 14px !important;
        margin: 0 !important;
        min-height: 38px !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: var(--primary-color) !important;
        box-shadow: 0 0 0 1px var(--primary-color) !important;
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
        margin: 2 !important;
    }
    .stButton > button {
        border: 1px solid #2D2C74 !important;
        padding: 2px !important;
        height: 10px !important;
        min-width: 10px !important;
        width: 10px !important;
        line-height: 1 !important;
        font-size: 12px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        background-color: #2D2C74 !important;
        color: white !important;
        margin: 0 2px !important;
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
        display: inline-block !important;
        margin: 0 2px !important;
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
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("### ITENS DA REQUISIÇÃO")
    st.markdown("""
    <table class="requisicao-table">
    <thead>
    <tr>
    <th style="width: 5%">ITEM</th>
    <th style="width: 15%">CÓDIGO</th>
    <th style="width: 20%">CÓD. FABRICANTE</th>
    <th style="width: 35%">DESCRIÇÃO</th>
    <th style="width: 15%">MARCA</th>
    <th style="width: 5%">QTD</th>
    <th style="width: 5%">AÇÕES</th>
    </tr>
    </thead>
    </table>
    """, unsafe_allow_html=True)

    if st.session_state.items_temp:
        for idx, item in enumerate(st.session_state.items_temp):
            cols = st.columns([0.5, 1.5, 2, 3.5, 1.5, 0.5, 0.5])
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
                    try:
                        quantidade_float = float(quantidade.replace(',', '.'))
                        item['quantidade'] = quantidade_float
                    except ValueError:
                        pass
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
    cols = st.columns([0.5, 1.5, 2, 3.5, 1.5, 0.5, 0.5])
    with cols[0]:
        st.text_input("", value=str(proximo_item), disabled=True, key=f"item_{proximo_item}", label_visibility="collapsed")
    with cols[1]:
        codigo = st.text_input("", key=f"codigo_{proximo_item}", label_visibility="collapsed").upper()
    with cols[2]:
        cod_fabricante = st.text_input("", key=f"cod_fab_{proximo_item}", label_visibility="collapsed").upper()
    with cols[3]:
        descricao = st.text_input("", key=f"desc_{proximo_item}", label_visibility="collapsed", help="desc-input").upper()
    with cols[4]:
        marca = st.text_input("", key=f"marca_{proximo_item}", label_visibility="collapsed").upper()
    with cols[5]:
        quantidade = st.text_input("", key=f"qtd_{proximo_item}", label_visibility="collapsed")
    with cols[6]:
        if st.button("➕", key=f"add_{proximo_item}"):
            if not descricao:
                st.session_state['show_desc_error'] = True
                st.rerun()
            else:
                try:
                    qtd = float(quantidade.replace(',', '.'))
                    novo_item = {
                        'item': proximo_item,
                        'codigo': codigo,
                        'cod_fabricante': cod_fabricante,
                        'descricao': descricao,
                        'marca': marca,
                        'quantidade': qtd,
                        'status': 'ABERTA'
                    }
                    st.session_state.items_temp.append(novo_item)
                    st.session_state['show_desc_error'] = False
                    st.session_state['show_qtd_error'] = False
                    st.rerun()
                except ValueError:
                    st.session_state['show_qtd_error'] = True
                    st.rerun()

    if st.session_state.items_temp:
        # Checkbox para mostrar campo de observações
        mostrar_obs = st.checkbox("INCLUIR OBSERVAÇÕES")
        
        # Campo de observações só aparece se o checkbox estiver marcado
        if mostrar_obs:
            st.markdown("### OBSERVAÇÕES")
            observacoes_vendedor = st.text_area(
                "Insira suas observações aqui",
                key="observacoes_vendedor",
                height=100
            )
        else:
            observacoes_vendedor = ""  # Valor padrão quando não há observações

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ ENVIAR", type="primary", use_container_width=True):
                if not cliente:
                    st.error("PREENCHIMENTO OBRIGATÓRIO: CLIENTE")
                    return
                
                nova_req = {
                    'numero': get_next_requisition_number(),
                    'cliente': cliente,
                    'vendedor': st.session_state['usuario'],
                    'data_hora': get_data_hora_brasil(),
                    'status': 'ABERTA',
                    'items': st.session_state.items_temp.copy(),
                    'observacoes_vendedor': observacoes_vendedor
                }
                
                if salvar_requisicao(nova_req):
                    st.session_state.requisicoes = carregar_requisicoes()
                    st.session_state.items_temp = []
                    st.success("Requisição enviada com sucesso!")
                    st.session_state['modo_requisicao'] = None
                    st.rerun()

def salvar_configuracoes():
    try:
        with open('configuracoes.json', 'w') as f:
            json.dump(st.session_state.config_sistema, f)
    except Exception as e:
        st.error(f"Erro ao salvar configurações: {e}")

def requisicoes():
    st.title("REQUISIÇÕES")
    
    # Atualização automática
    if 'ultima_atualizacao' not in st.session_state:
        st.session_state.ultima_atualizacao = time.time()
    
    if time.time() - st.session_state.ultima_atualizacao > 60:
        st.session_state.requisicoes = carregar_requisicoes()
        st.session_state.ultima_atualizacao = time.time()
        st.rerun()

    # Estilização
    st.markdown("""
        <style>
        .filtros-container {
            background-color: white;
            padding: 0px;
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 12px;
        }
        .requisicao-card {
            background-color: white;
            padding: 4px;
            border-radius: 8px;
            margin-bottom: 4px;
            border-left: 4px solid #2D2C74;
            transition: all 0.3s ease;
        }
        .requisicao-card.expandido {
            border-radius: 8px 8px 0 0;
            margin-bottom: 0;
        }
        .card-expandido {
            margin-top: -4px;
            border-top: none;
            border-radius: 0 0 8px 8px;
            background-color: #f8f9fa;
            padding: 5px;
            border-left: 4px solid #2D2C74;
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
            padding: 0px;
            background-color: white;
            border-bottom: 1px solid #eee;
            margin-bottom: 0;
        }
        .header-group { 
            flex: 1;
            padding: 0 8px;
        }
        .header-group p {
            margin: 0px 0;
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
            text-transform: uppercase;
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
        .requisicao-table th:nth-child(2) { width: 15%; }
        .requisicao-table td:nth-child(3),
        .requisicao-table th:nth-child(3) { width: 35%; }
        .requisicao-table td:nth-child(4),
        .requisicao-table th:nth-child(4) { width: 10%; }
        .requisicao-table td:nth-child(5),
        .requisicao-table th:nth-child(5) { width: 5%; text-align: center; }
        .requisicao-table td:nth-child(6),
        .requisicao-table th:nth-child(6) { width: 10%; text-align: right; }
        .requisicao-table td:nth-child(7),
        .requisicao-table th:nth-child(7) { width: 10%; text-align: right; }
        .requisicao-table td:nth-child(8),
        .requisicao-table th:nth-child(8) { width: 10%; text-align: center; }
        .valor-cell { 
            text-align: right; 
        }
        .action-buttons {
            padding: 1px;
            background-color: white;
            border-top: 1px solid #eee;
            margin-top: 0px;
            display: flex;
            justify-content: space-between;
            gap: 10px;
        }
        .input-container {
            background-color: white;
            padding: 0px;
            border-radius: 8px;
            margin-top: 1px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .observacao-geral {
            margin-top: 10px;
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 8px;
        }
        .btn-aceitar {
            background-color: #2e7d32 !important;
            color: white !important;
        }
        .btn-recusar {
            background-color: #c62828 !important;
            color: white !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Botão Nova Requisição
    col1, col2 = st.columns([4,1])
    with col2:
        if st.button("📝 NOVA REQUISIÇÃO", key="nova_req", type="primary"):
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
                numero_busca = st.text_input("🔍 NÚMERO DA REQUISIÇÃO", key="busca_numero")
            with col2:
                cliente_busca = st.text_input("👥 CLIENTE", key="busca_cliente")
            with col3:
                data_col1, data_col2 = st.columns(2)
                with data_col1:
                    data_inicial = st.date_input("DATA INICIAL", value=None, key="data_inicial")
                with data_col2:
                    data_final = st.date_input("DATA FINAL", value=None, key="data_final")
            with col4:
                st.markdown("<br>", unsafe_allow_html=True)
                buscar = st.button("🔎 BUSCAR", type="primary", use_container_width=True)

            # Status como chips coloridos
            status_opcoes = {
                "ABERTA": "🔵",
                "EM ANDAMENTO": "🟡",
                "FINALIZADA": "🟢",
                "RECUSADA": "🔴"
            }
            selected_status = st.multiselect(
                "STATUS",
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
            st.warning("NENHUMA REQUISIÇÃO ENCONTRADA COM OS FILTROS SELECIONADOS.")

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
                        else 'var(--background-color)'};
                        color: var(--text-color)">
                        <div class="requisicao-info" style="color: var(--text-color)">
                            <div>
                                <span class="requisicao-numero" style="color: var(--text-color)"></span>
                                <span class="requisicao-numero" style="color: var(--text-color)">{req['numero']}</span>
                                <span class="requisicao-cliente" style="color: var(--text-color)">{req['cliente']}</span>
                            </div>
                            <div>
                                <span class="status-badge status-{req['status'].lower()}">{req['status']}</span>
                            </div>
                        </div>
                        <div class="requisicao-data" style="color: var(--text-color); display: flex; justify-content: space-between;">
                            <div>
                                <span>CRIADO EM: {req['data_hora']}</span>
                                <span>VENDEDOR: {req['vendedor']}</span>
                            </div>
                            <span>COMPRADOR: {req.get('comprador_responsavel', '-')}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                if st.button(f"VER DETALHES", key=f"detalhes_{req['numero']}_{idx}"):
                    for key in list(st.session_state.keys()):
                        if key.startswith('mostrar_detalhes_') and key != f'mostrar_detalhes_{req["numero"]}':
                            st.session_state.pop(key)
                    st.session_state[f'mostrar_detalhes_{req["numero"]}'] = True
                    st.rerun()

                if st.session_state.get(f'mostrar_detalhes_{req["numero"]}', False):
                    with st.container():
                        st.markdown("""
                            <div class="detalhes-container" style="
                                background-color: var(--background-color);
                                color: var(--text-color) !important;
                                border: 1px solid var(--secondary-background-color);">
                        """, unsafe_allow_html=True)
                        
                        st.markdown("""
                            <div class="detalhes-header" style="
                                background-color: var(--background-color);
                                color: var(--text-color) !important;
                                border-bottom: 1px solid var(--secondary-background-color);">
                        """, unsafe_allow_html=True)
                        
                        if req['status'] == 'ABERTA' and st.session_state['perfil'] in ['comprador', 'administrador']:
                            col1, col2, col3, col4 = st.columns([2,1,1,1])
                            with col2:
                                if st.button("✅", key=f"aceitar_{req['numero']}", type="primary"):
                                    req['status'] = 'EM ANDAMENTO'
                                    req['comprador_responsavel'] = st.session_state['usuario']
                                    req['data_hora_aceite'] = get_data_hora_brasil()
                                    if salvar_requisicao(req):
                                        enviar_notificacao(
                                            f"Requisição {req['numero']} Aceita",
                                            f"{st.session_state['usuario']} aceitou a requisição Nº{req['numero']} para o cliente {req['cliente']}",
                                            req['numero']
                                        )
                                        st.success("Requisição aceita com sucesso!")
                                        st.rerun()
                            with col3:
                                if st.button("❌", key=f"recusar_{req['numero']}", type="primary"):
                                    st.session_state[f'mostrar_justificativa_{req["numero"]}'] = True
                                    st.rerun()
                            with col4:
                                if st.button("FECHAR", key=f"fechar_{req['numero']}_{idx}"):
                                    st.session_state.pop(f'mostrar_detalhes_{req["numero"]}')
                                    st.rerun()
                        else:
                            col1, col2 = st.columns([3,1])
                            with col2:
                                if st.button("FECHAR", key=f"fechar_{req['numero']}_{idx}"):
                                    st.session_state.pop(f'mostrar_detalhes_{req["numero"]}')
                                    st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)

                        st.markdown(f"""
                            <div class="header-info" style="
                                background-color: var(--background-color);
                                color: var(--text-color) !important;
                                border-bottom: 1px solid var(--secondary-background-color);">
                                <div class="header-group">
                                    <p style="color: var(--text-color) !important"><strong style="color: var(--text-color) !important">CRIADO EM:</strong> {req['data_hora']}</p>
                                    <p style="color: var(--text-color) !important"><strong style="color: var(--text-color) !important">VENDEDOR:</strong> {req['vendedor']}</p>
                                </div>
                                <div class="header-group">
                                    <p style="color: var(--text-color) !important"><strong style="color: var(--text-color) !important">RESPONDIDO EM:</strong> {req.get('data_hora_resposta','-')}</p>
                                    <p style="color: var(--text-color) !important"><strong style="color: var(--text-color) !important">COMPRADOR:</strong> {req.get('comprador_responsavel', '-')}</p>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)

                         # Campo de justificativa (aparece somente após clicar em recusar)
                        if st.session_state.get(f'mostrar_justificativa_{req["numero"]}', False):
                            st.markdown("### JUSTIFICATIVA DA RECUSA")
                            justificativa = st.text_area(
                                "Digite a justificativa da recusa",
                                key=f"justificativa_{req['numero']}",
                                height=100
                            )
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("CONFIRMAR RECUSA", key=f"confirmar_recusa_{req['numero']}", type="primary", use_container_width=True):
                                    if not justificativa:
                                        st.error("Por favor, informe a justificativa da recusa.")
                                        return
                                    
                                    req['status'] = 'RECUSADA'
                                    req['comprador_responsavel'] = st.session_state['usuario']
                                    req['data_hora_resposta'] = get_data_hora_brasil()
                                    req['justificativa_recusa'] = justificativa
                                    
                                    if salvar_requisicao(req):
                                        try:
                                            enviar_notificacao(
                                                f"Requisição {req['numero']} Recusada",
                                                f"{st.session_state['usuario']} recusou a requisição Nº{req['numero']} para o cliente {req['cliente']}. Justificativa: {justificativa}",
                                                req['numero']
                                            )
                                            enviar_email_requisicao(req, "recusada")
                                            st.success("Requisição recusada com sucesso!")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Erro ao enviar notificação: {str(e)}")
                                    
                            with col2:
                                if st.button("CANCELAR", key=f"cancelar_recusa_{req['numero']}", type="secondary", use_container_width=True):
                                    st.session_state.pop(f'mostrar_justificativa_{req["numero"]}')
                                    st.rerun()

                        # Itens da requisição
                        st.markdown('<div class="items-title">ITENS DA REQUISIÇÃO</div>', unsafe_allow_html=True)
                        if req['items']:
                            items_df = pd.DataFrame([{
                                'Código': item.get('codigo', '-'),
                                'Cód. Fabricante': item.get('cod_fabricante', '-'),
                                'Descrição': item['descricao'],
                                'Marca': item.get('marca', 'PC'),
                                'QTD': item['quantidade'],
                                'R$ Venda Unit': f"R$ {item.get('venda_unit', 0):.2f}",
                                'R$ Total': f"R$ {(item.get('venda_unit', 0) * item['quantidade']):.2f}",
                                'Prazo': item.get('prazo_entrega', '-')
                            } for item in req['items']])

                            st.dataframe(
                                items_df,
                                hide_index=True,
                                use_container_width=True,
                                column_config={
                                    "Código": st.column_config.TextColumn("CÓDIGO", width=35),
                                    "Cód. Fabricante": st.column_config.TextColumn("CÓD. FABRICANTE", width=100),
                                    "Descrição": st.column_config.TextColumn("DESCRIÇÃO", width=350),
                                    "Marca": st.column_config.TextColumn("MARCA", width=80),
                                    "QTD": st.column_config.NumberColumn("QTD", width=30),
                                    "R$ Venda Unit": st.column_config.TextColumn("R$ VENDA UNIT", width=70),
                                    "R$ Total": st.column_config.TextColumn("R$ TOTAL", width=80),
                                    "Prazo": st.column_config.TextColumn("PRAZO", width=100)
                                }
                            )

                            # Exibição das observações do vendedor
                            if req.get('observacoes_vendedor'):
                                st.markdown("""
                                    <div style='background-color: var(--background-color);
                                              border-radius: 4px; 
                                              padding: 10px; 
                                              margin: 10px 0 0px 0; 
                                              border-left: 4px solid #1B81C5;
                                              border: 1px solid var(--secondary-background-color);'>
                                        <p style='color: var(--text-color); 
                                                  font-weight: bold; 
                                                  margin-bottom: 10px;'>OBSERVAÇÕES DO VENDEDOR:</p>
                                        <p style='margin: 0 0 5px 0; color: var(--text-color);'>{}</p>
                                    </div>
                                """.format(req['observacoes_vendedor']), unsafe_allow_html=True)

                            # Exibição da justificativa de recusa
                            if req['status'] == 'RECUSADA':
                                st.markdown("""
                                    <div style='
                                        background-color: rgba(198, 40, 40, 0.1);
                                        padding: 15px;
                                        border-radius: 8px;
                                        margin: 10px 0;
                                        border: 1px solid rgba(198, 40, 40, 0.3);
                                        box-shadow: 0 2px 4px rgba(198, 40, 40, 0.1);'>
                                        <p style='
                                            color: rgb(198, 40, 40);
                                            font-weight: bold;
                                            margin-bottom: 5px;
                                            font-size: 14px;'>
                                            JUSTIFICATIVA DA RECUSA:
                                        </p>
                                        <p style='
                                            margin: 0;
                                            color: rgb(198, 40, 40);
                                            opacity: 0.9;'>
                                            {}
                                        </p>
                                    </div>
                                """.format(req.get('justificativa_recusa', 'Não informada')), unsafe_allow_html=True)

                            # Exibição da observação do comprador
                            if req.get('observacao_geral'):
                                st.markdown("""
                                    <div style='background-color: var(--background-color);
                                              border-radius: 4px; 
                                              padding: 15px; 
                                              margin: 20px 0 25px 0; 
                                              border-left: 4px solid #2D2C74;
                                              border: 1px solid var(--secondary-background-color);'>
                                        <p style='color: var(--text-color); 
                                                  font-weight: bold; 
                                                  margin-bottom: 10px;'>OBSERVAÇÕES DO COMPRADOR:</p>
                                        <p style='margin: 0 0 5px 0; color: var(--text-color);'>{}</p>
                                    </div>
                                """.format(req['observacao_geral']), unsafe_allow_html=True)

                            if req['status'] == 'EM ANDAMENTO' and st.session_state['perfil'] in ['comprador', 'administrador']:
                                st.markdown('<div class="input-container">', unsafe_allow_html=True)
                                
                                # Seleção do item para resposta
                                item_selecionado = st.selectbox(
                                    "SELECIONE O ITEM PARA RESPONDER",
                                    options=[f"ITEM {item['item']}: {item['descricao']}" for item in req['items']],
                                    key=f"select_item_{req['numero']}"
                                )
                                
                                # Índice do item selecionado
                                item_idx = int(item_selecionado.split(':')[0].replace('ITEM ', '')) - 1
                                item = req['items'][item_idx]

                                # Campos de resposta em linha única
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    item['custo_unit'] = st.number_input(
                                        "R$ UNIT",
                                        value=item.get('custo_unit', 0.0),
                                        min_value=0.0,
                                        format="%.2f",
                                        key=f"custo_{req['numero']}_{item_idx}"
                                    )
                                with col2:
                                    item['markup'] = st.number_input(
                                        "% MARKUP",
                                        value=item.get('markup', 0.0),
                                        min_value=0.0,
                                        format="%.2f",
                                        step=1.0,
                                        key=f"markup_{req['numero']}_{item_idx}"
                                    )
                                with col3:
                                    item['prazo_entrega'] = st.text_input(
                                        "PRAZO",
                                        value=item.get('prazo_entrega', ''),
                                        key=f"prazo_{req['numero']}_{item_idx}"
                                    )

                                # Checkbox e campo para observações
                                mostrar_obs = st.checkbox(
                                    "INCLUIR OBSERVAÇÕES",
                                    key=f"show_obs_{req['numero']}"
                                )
                                observacao_geral = ""
                                if mostrar_obs:
                                    observacao_geral = st.text_area(
                                        "OBSERVAÇÕES GERAIS",
                                        value=req.get('observacao_geral', ''),
                                        height=100,
                                        key=f"obs_{req['numero']}"
                                    )

                                # Botões alinhados horizontalmente
                                col_btn1, col_btn2 = st.columns(2)
                                with col_btn1:
                                    if st.button("💾 SALVAR ITEM", key=f"salvar_{req['numero']}_{item_idx}", type="primary"):
                                        # Calcular valor de venda
                                        item['venda_unit'] = item['custo_unit'] * (1 + (item['markup'] / 100))
                                        item['venda_total'] = item['venda_unit'] * item['quantidade']
                                        item['salvo'] = True
                                        if mostrar_obs:
                                            req['observacao_geral'] = observacao_geral
                                        salvar_requisicao(req)
                                        st.success(f"ITEM {item['item']} SALVO COM SUCESSO!")
                                        st.rerun()
                                
                                with col_btn2:
                                    todos_itens_salvos = all(item.get('salvo', False) for item in req['items'])
                                    if todos_itens_salvos:
                                        if st.button("✅ FINALIZAR", key=f"finalizar_{req['numero']}", type="primary"):
                                            req['status'] = 'FINALIZADA'
                                            req['data_hora_resposta'] = get_data_hora_brasil()
                                            if salvar_requisicao(req):
                                                enviar_email_requisicao(req, "finalizada")
                                                enviar_notificacao(
                                                    f"REQUISIÇÃO {req['numero']} FINALIZADA",
                                                    f"{st.session_state['usuario']} finalizou a requisição Nº{req['numero']} para o cliente {req['cliente']}",
                                                    req['numero']
                                                )
                                                st.success("REQUISIÇÃO FINALIZADA COM SUCESSO!")
                                                st.rerun()
                                            else:
                                                st.error("ERRO AO SALVAR A REQUISIÇÃO. TENTE NOVAMENTE.")

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
    
    # Botão de teste de notificação
    st.markdown("---")
    st.markdown("#### Testar Notificações")
    if st.button("🔔 Enviar Notificação de Teste", type="primary"):
        enviar_notificacao(
            "Teste de Notificação",
            "Se você está vendo esta mensagem, as notificações estão funcionando corretamente!",
            "teste"
        )
        st.success("Notificação de teste enviada!")
                                        
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
    
    if st.session_state['perfil'] in ['administrador', 'comprador']:
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
    else:
        st.session_state['config_modo'] = 'sistema'

    if st.session_state.get('config_modo') == 'usuarios' and st.session_state['perfil'] == 'administrador':
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
        
        if st.button("➕ Cadastrar Novo Usuário", type="primary", use_container_width=True):
            st.session_state['modo_usuario'] = 'cadastrar'
            st.rerun()

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

        usuarios_filtrados = st.session_state.usuarios

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
        
        if st.session_state['perfil'] == 'administrador':
            tab1, tab2 = st.tabs(["📊 Monitoramento", "⚙️ Personalizar"])
            
            with tab1:
                st.markdown("#### Monitoramento do Sistema")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("##### Desempenho do Sistema")
                    
                    import plotly.graph_objects as go
                    
                    fig = go.Figure(go.Indicator(
                        mode = "gauge+number+delta",
                        value = 75,
                        domain = {'x': [0, 1], 'y': [0, 1]},
                        title = {'text': "Desempenho"},
                        number = {'suffix': "%"},
                        gauge = {
                            'axis': {'range': [None, 100]},
                            'bar': {'color': "rgba(0,0,0,0)"},
                            'steps': [
                                {'range': [0, 50], 'color': "red"},
                                {'range': [50, 75], 'color': "yellow"},
                                {'range': [75, 100], 'color': "green"}
                            ],
                            'threshold': {
                                'line': {'color': "red", 'width': 4},
                                'thickness': 0.75,
                                'value': 90
                            }
                        }
                    ))
                    
                    st.plotly_chart(fig)
                
                with col2:
                    st.markdown("##### Armazenamento de Backup")
                    fig = mostrar_espaco_armazenamento()
                    st.plotly_chart(fig)
                
                st.markdown("#### Visualização de Dados")
                if st.button("🔍 Visualizar Dados do Banco", type="primary"):
                    conn = sqlite3.connect('requisicoes.db')
                    df = pd.read_sql_query("SELECT * FROM requisicoes", conn)
                    st.dataframe(df)
                    conn.close()
                
                st.markdown("#### Configurações de Backup")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("##### Frequência de Backup")
                    backup_diario = st.toggle("Backup Diário", value=st.session_state.get('backup_diario', False))
                    backup_semanal = st.toggle("Backup Semanal", value=st.session_state.get('backup_semanal', False))
                    backup_mensal = st.toggle("Backup Mensal", value=st.session_state.get('backup_mensal', False))
                
                with col2:
                    st.markdown("##### Último Backup")
                    st.info(f"Data: {get_data_hora_brasil()}")
                
                if st.button("🔄 Forçar Backup Agora", type="primary"):
                    backup_file, backup_size = backup_automatico(st.session_state)
                    if backup_file:
                        st.success(f"Backup realizado com sucesso! Tamanho: {backup_size/1024:.2f} MB")
                
                # Lista de Backups Disponíveis
                st.markdown("#### Backups Disponíveis")
                
                import os
                backup_dir = "backups"
                if os.path.exists(backup_dir):
                    backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.py') or f.endswith('.zip')]
                    
                    if backup_files:
                        for backup_file in backup_files:
                            col1, col2, col3 = st.columns([3, 1, 1])
                            file_path = os.path.join(backup_dir, backup_file)
                            file_size = os.path.getsize(file_path)
                            
                            with col1:
                                st.text(backup_file)
                            with col2:
                                st.text(f"{file_size/1024:.2f} KB")
                            with col3:
                                with open(file_path, "rb") as f:
                                    bytes_data = f.read()
                                    st.download_button(
                                        label="⬇️",
                                        data=bytes_data,
                                        file_name=backup_file,
                                        mime="application/octet-stream",
                                        key=f"download_{backup_file}"
                                    )
                    else:
                        st.info("Nenhum arquivo de backup encontrado.")
                else:
                    st.warning("Diretório de backup não encontrado.")

def main():

    # Inicializar o banco de dados
    inicializar_banco()
    
    # Adiciona atualização automática a cada 120 segundos
    st_autorefresh(interval=1200000, key="datarefresh")
    
    if 'usuario' not in st.session_state:
        tela_login()
    else:
        solicitar_permissao_notificacao()
        
        # Adicione aqui a mensagem fixa
        col1, col2 = st.columns([3,1])
        with col2:
            st.markdown(f"""
                <div style='
                    background-color: var(--background-color);
                    padding: 8px;
                    border-radius: 4px;
                    font-size: 12px;
                    text-align: right;
                    color: var(--text-color);'>
                    🔄 Última atualização: {get_data_hora_brasil()}
                </div>
            """, unsafe_allow_html=True)
       
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
