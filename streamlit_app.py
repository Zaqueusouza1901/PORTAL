import streamlit as st
import os
import firebase_admin
from firebase_admin import credentials, auth, db
import pandas as pd
import time
import json
import smtplib
import logging
import shutil
import glob
import pytz
import gzip
from streamlit import session_state as state
from firebase_admin import db, auth
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import plotly.graph_objects as go
from google.cloud import firestore
from google.oauth2 import service_account
import streamlit_autorefresh
from streamlit_autorefresh import st_autorefresh

# Configuração da página (DEVE SER A PRIMEIRA CHAMADA DO STREAMLIT)
st.set_page_config(
    page_title="PORTAL - JETFRIO",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicialização do Firebase
if not firebase_admin._apps:
    try:
        # Carrega as credenciais do st.secrets e converte para string JSON
        cred_dict = dict(st.secrets["FIREBASE_CREDENTIALS"])
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://portal-fd465-default-rtdb.firebaseio.com/'
        })
        print("Firebase inicializado com st.secrets!")
    except Exception as e:
        st.error(f"Erro ao inicializar o Firebase com st.secrets: {e}")
        # Se falhar, tenta carregar de um arquivo (útil para desenvolvimento local)
        try:
            # Caminho absoluto para o arquivo JSON
            caminho_arquivo_json = "portal-fd465-firebase-adminsdk-fbsvc-490ec0697a.json"
            cred = credentials.Certificate(caminho_arquivo_json)
            firebase_admin.initialize_app(cred, {
                'databaseURL': 'https://portal-fd465-default-rtdb.firebaseio.com/'
            })
            print("Firebase inicializado com arquivo JSON local!")
        except FileNotFoundError:
            st.error("Arquivo JSON de credenciais não encontrado.")
        except Exception as e:
            st.error(f"Erro ao inicializar o Firebase com arquivo JSON local: {e}")

db = firebase_admin.db

def criar_usuario_admin():
    try:
        # Referência ao nó 'usuarios' no Firebase
        usuarios_ref = db.reference('usuarios')
        
        # Verificar se o usuário administrador já existe
        usuario_admin = None
        todos_usuarios = usuarios_ref.get()
        
        if todos_usuarios:
            for uid, dados_usuario in todos_usuarios.items():
                if dados_usuario.get('nome') == "ZAQUEU SOUZA":
                    usuario_admin = dados_usuario
                    break
        
        # Se o usuário administrador não existir, cadastrá-lo
        if not usuario_admin:
            user_id = "admin"  # Um ID fixo para o administrador
            novo_usuario_data = {
                'nome': "ZAQUEU SOUZA",
                'email': "Importacao@jetfrio.com.br",
                'senha': "Za@031162",
                'perfil': "administrador",
                'ativo': True,
                'data_criacao': get_data_hora_brasil()
            }
            usuarios_ref.child(user_id).set(novo_usuario_data)
            print("Usuário administrador cadastrado com sucesso!")
    except Exception as e:
        print(f"Erro ao criar usuário administrador: {str(e)}")

def mostrar_espaco_armazenamento():
    
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
                </div>... <table border="1" style="border-collapse: collapse; width: 100%;">
                    <tr>... <th>Código</th>
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
            destinatarios = [vendedor_email]
            if comprador_email:
                destinatarios.append(comprador_email)
            server.send_message(msg)
        
        return True
    except Exception as e:
        st.error(f"Erro ao enviar email: {str(e)}")
        return False

def save_perfis_permissoes(perfil, permissoes):
    try:
        ref = db.child(perfil).set(permissoes)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar permissões: {str(e)}")
        return False

def importar_dados_antigos(caminho_arquivo):
    try:
        # Carregar dados do JSON
        with open(caminho_arquivo, 'r', encoding='utf-8') as file:
            requisicoes_antigas = json.load(file)

        # Referência para o nó 'requisicoes' no Firebase
        ref = db.reference('/requisicoes')

        # Inserir dados formatados
        for req in requisicoes_antigas:
            numero_req = req.get('numero', '')  # Use 'numero' para corresponder à chave no JSON
            
            # Converter a string JSON de items para uma lista de dicionários
            items_str = req.get('items', '[]')  # Obtém a string JSON ou usa '[]' como padrão
            try:
                items = json.loads(items_str)  # Converte a string para uma lista de dicionários
            except json.JSONDecodeError:
                st.error(f"Erro ao decodificar items da requisição {numero_req}. Verifique a formatação JSON.")
                continue  # Pula para a próxima requisição em caso de erro

            requisicao_data = {
                'numero': numero_req,
                'cliente': req.get('cliente'),
                'vendedor': req.get('vendedor'),
                'data_hora': req.get('data_hora'),
                'status': req.get('status'),
                'items': items,
                'observacoes_vendedor': req.get('observacoes_vendedor', ''),  # Usar get para campos opcionais
                'comprador_responsavel': req.get('comprador_responsavel', ''),
                'data_hora_resposta': req.get('data_hora_resposta', ''),
                'justificativa_recusa': req.get('justificativa_recusa', ''),
                'observacao_geral': req.get('observacao_geral', '')
            }
            
            ref.child(numero_req).set(requisicao_data)

        st.success("Dados importados com sucesso para o Firebase!")
        return True
    except FileNotFoundError:
        st.error(f"Arquivo não encontrado: {caminho_arquivo}")
        return False
    except Exception as e:
        st.error(f"Erro na importação: {str(e)}")
        return False

def carregar_usuarios():
    try:
        ref = db.reference('/usuarios')
        usuarios = ref.get()
        if usuarios:
            return usuarios  # Retorna um dicionário de usuários
        else:
            return {} # Retorna um dicionário vazio em vez de None
    except Exception as e:
        st.error(f"Erro ao carregar usuários: {str(e)}")
        return {} # Retorna um dicionário vazio em caso de erro

def salvar_usuario(usuario_id, usuario_data):
  try:
    ref = db.reference('/usuarios')
    ref.child(usuario_id).set(usuario_data)
    return True
  except Exception as e:
    st.error(f"Erro ao salvar usuario: {str(e)}")
    return False

def migrar_dados_json_para_firebase():
    try:
        with open('requisicoes.json', 'r', encoding='utf-8') as f:
            requisicoes_json = json.load(f)
        
        # Referência ao nó 'requisicoes' no Firebase
        ref = db.reference('/requisicoes')
        
        for req in requisicoes_json:
            req_data = {
                'numero': req['REQUISIÇÃO'],
                'cliente': req['CLIENTE'],
                'vendedor': req['VENDEDOR'],
                'data_hora': req['Data/Hora Criação:'],
                'status': req['STATUS'],
                'items': [{
                    'codigo': req['CÓDIGO'],
                    'descricao': req['DESCRIÇÃO'],
                    'marca': req['MARCA'],
                    'quantidade': req['QUANTIDADE'],
                    'venda_unit': req[' R$ UNIT '].replace('R$ ', '').replace(',', '.').strip(),
                    'prazo_entrega': req['PRAZO']
                }],
                'observacoes_vendedor': '',
                'comprador_responsavel': req['COMPRADOR'],
                'data_hora_resposta': req['Data/Hora Resposta:'],
                'justificativa_recusa': '',
                'observacao_geral': req['OBSERVAÇÕES DO COMPRADOR']
            }
            
            # Usar o número da requisição como chave
            ref.child(req['REQUISIÇÃO']).set(req_data)
        
        return True
    except Exception as e:
        print(f"Erro na migração para Firebase: {str(e)}")
        return False
    
import json

def carregar_requisicoes():
    try:
        ref = db.reference('/requisicoes')
        requisicoes = ref.get()

        if requisicoes:
            lista_requisicoes = []
            for numero, req_str in requisicoes.items():
                try:
                    req = json.loads(req_str) if isinstance(req_str, str) else req_str # Desserializa se for string
                    lista_requisicoes.append(req)
                except (TypeError, json.JSONDecodeError) as e:
                    st.error(f"Erro ao decodificar requisição {numero}: {str(e)}")
                    continue  # Pula para a próxima requisição em caso de erro

            return lista_requisicoes
        else:
            return []

    except Exception as e:
        st.error(f"Erro ao carregar requisições: {str(e)}")
        return []

def renumerar_requisicoes():
    try:
        ref = db.reference('/requisicoes')
        requisicoes = ref.get()
        
        if not requisicoes:
            novo_numero = 5656  # Começar a partir de 5656 se não houver requisições
        else:
            # Encontrar o maior número de requisição
            maior_numero = max(int(req['numero']) for req in requisicoes.values())
            novo_numero = maior_numero + 1  # Começar do próximo número disponível
        
        requisicoes_ordenadas = sorted(requisicoes.items(), key=lambda x: x[1]['data_hora'])
        
        for old_key, req_data in requisicoes_ordenadas:
            novo_key = str(novo_numero)
            req_data['numero'] = novo_key
            
            ref.child(old_key).delete()
            ref.child(novo_key).set(req_data)
            
            novo_numero += 1
        
        return True
    except Exception as e:
        print(f"Erro ao renumerar requisições no Firebase: {str(e)}")
        return False

def backup_requisicoes():
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f'backup/requisicoes_backup_{timestamp}.json'
        os.makedirs('backup', exist_ok=True)
        
        # Obter dados do Firebase
        ref = db.reference('/requisicoes')
        requisicoes = ref.get()
        
        # Salvar dados em um arquivo JSON
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(requisicoes, f, ensure_ascii=False, indent=4)
        
        return True
    except Exception as e:
        print(f"Erro no backup: {str(e)}")
        return False

def comprimir_backup(backup_path):
    with open(backup_path, 'rb') as f_in:
        with gzip.open(f'{backup_path}.gz', 'wb') as f_out:
            f_out.writelines(f_in)
    os.remove(backup_path)  # Remove o arquivo ZIP original após a compressão

def limpar_backups_antigos(backup_dir, dias_manter=7):
    try:
        data_limite = datetime.now() - timedelta(days=dias_manter)
        
        for arquivo in os.listdir(backup_dir):
            if arquivo.startswith('backup_') and arquivo.endswith('.json.gz'):
                caminho_arquivo = os.path.join(backup_dir, arquivo)
                data_arquivo = datetime.fromtimestamp(os.path.getctime(caminho_arquivo))
                
                if data_arquivo < data_limite:
                    os.remove(caminho_arquivo)
    except Exception as e:
        print(f"Erro ao limpar backups antigos: {str(e)}")

def restaurar_backup():
    try:
        # Referências para os nós no Firebase
        requisicoes_ref = db.reference('/requisicoes')
        
        # Fazer backup preventivo antes de limpar
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_preventivo = f'backups/pre_restore_{timestamp}.json'
        dados_atuais = requisicoes_ref.get()
        with open(backup_preventivo, 'w', encoding='utf-8') as f:
            json.dump(dados_atuais, f, ensure_ascii=False, indent=4)
        
        # Carrega dados do backup
        with gzip.open('backup/ultimo_backup.json.gz', 'rt', encoding='utf-8') as f:
            dados = json.load(f)
        
        # Limpa dados atuais e insere dados do backup
        requisicoes_ref.delete()
        requisicoes_ref.set(dados['requisicoes'])
        
        # Atualiza outros nós se necessário
        if 'usuarios' in dados:
            db.reference('/usuarios').set(dados['usuarios'])
        if 'perfis' in dados:
            db.reference('/perfis').set(dados['perfis'])
        
        # Recarrega dados na sessão
        st.session_state.requisicoes = carregar_requisicoes()
        st.success("Backup restaurado com sucesso!")
        return True
        
    except Exception as e:
        st.error(f"Erro ao restaurar backup: {str(e)}")
        # Restaura backup preventivo em caso de erro
        if os.path.exists(backup_preventivo):
            with open(backup_preventivo, 'r', encoding='utf-8') as f:
                dados_preventivos = json.load(f)
            requisicoes_ref.set(dados_preventivos)
        return False

def salvar_requisicao(requisicao):
    try:
        ref = db.reference('/requisicoes')
        ref.child(requisicao['numero']).set(requisicao) # AQUI ESTÁ O PROBLEMA!
        return True
    except Exception as e:
        st.error(f"Erro ao salvar requisição: {str(e)}")
        return False

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
        ref = db.reference('/requisicoes')
        requisicoes = ref.get()

        if not requisicoes:
            proximo_numero = 5000
        else:
            # Usar uma compreensão de lista com tratamento de erro para garantir que 'numero' seja um inteiro
            numeros = [int(req['numero']) for req in requisicoes.values() if isinstance(req['numero'], (int, str)) and str(req['numero']).isdigit()]
            proximo_numero = max(numeros) + 1 if numeros else 5000

        # Atualiza o número no Firebase
        db.reference('/ultimo_numero').set({'numero': proximo_numero})

        return str(proximo_numero)  # Garante que o retorno seja uma string
    except Exception as e:
        st.error(f"Erro ao gerar número da requisição: {str(e)}")
        return None

def inicializar_numero_requisicao():
    try:
        ref = db.reference('/ultimo_numero')
        ultimo_numero = ref.get()
        if not ultimo_numero:
            ref.set({'numero': 4999})
            return 4999
        return ultimo_numero['numero']
    except Exception as e:
        st.error(f"Erro ao inicializar número de requisição: {str(e)}")
        return 4999

# Inicialização de dados
if 'usuarios' not in st.session_state:
    st.session_state.usuarios = carregar_usuarios()
    if 'requisicoes' not in st.session_state:
        st.session_state.requisicoes = carregar_requisicoes()

# Inicialização dos perfis
if 'perfis' not in st.session_state:
    perfis_ref = db.reference('/perfis')
    perfis = perfis_ref.get()
    if not perfis:
        perfis = {
            'vendedor': {
                'dashboard': True,
                'requisicoes': True,
                'cotacoes': True,
                'importacao': False,
                'configuracoes': False,
                'editar_usuarios': False,
                'excluir_usuarios': False,
                'editar_perfis': False
            },
            'comprador': {
                'dashboard': True,
                'requisicoes': True,
                'cotacoes': True,
                'importacao': True,
                'configuracoes': False,
                'editar_usuarios': False,
                'excluir_usuarios': False,
                'editar_perfis': False
            },
            'administrador': {
                'dashboard': True,
                'requisicoes': True,
                'cotacoes': True,
                'importacao': True,
                'configuracoes': True,
                'editar_usuarios': True,
                'excluir_usuarios': True,
                'editar_perfis': True
            }
        }
        perfis_ref.set(perfis)
    st.session_state.perfis = perfis

inicializar_numero_requisicao()
        
def tela_login():
    st.markdown("""
        <style>
        div.stButton > button:first-child {
            background-color: #0088ff;
            color: white;
            font-weight: bold;
        }
        div.stButton > button:hover {
            background-color: #0066cc;
            color: white;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("PORTAL - JETFRIO")
    nome_usuario = st.text_input("Nome de Usuário", key="usuario_input").upper()
    senha = st.text_input("Senha", type="password", key="senha_input")
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("Entrar", use_container_width=True, type="primary"):
            try:
                # Autenticação para o usuário administrador
                if nome_usuario == "ZAQUEU SOUZA" and senha == "Za@031162":
                    st.session_state['user_id'] = "admin"
                    st.session_state['usuario'] = "ZAQUEU SOUZA"
                    st.session_state['email'] = "Importacao@jetfrio.com.br"
                    st.session_state['perfil'] = "administrador"
                    st.success(f"Bem-vindo, {st.session_state['usuario']}!")
                    st.rerun()
                
                else:
                    # Busca o usuário no Realtime Database com base no nome de usuário
                    usuarios_ref = db.reference('usuarios')
                    todos_usuarios = usuarios_ref.get()
                    
                    usuario_encontrado = None
                    user_id = None
                    
                    for uid, dados_usuario in todos_usuarios.items():
                        if dados_usuario.get('nome', '').upper() == nome_usuario:
                            usuario_encontrado = dados_usuario
                            user_id = uid
                            break
                    
                    # Se o usuário não for encontrado, exibe uma mensagem de erro
                    if usuario_encontrado is None:
                        st.error("Usuário não encontrado.")
                        return
                    
                    # Valida a senha
                    senha_armazenada = usuario_encontrado.get('senha', '')
                    if senha != senha_armazenada:
                        st.error("Senha incorreta.")
                        return
                    
                    # Define as variáveis de sessão
                    st.session_state['user_id'] = user_id
                    st.session_state['usuario'] = usuario_encontrado.get('nome', nome_usuario)
                    st.session_state['perfil'] = usuario_encontrado.get('perfil', 'vendedor')
                    
                    st.success(f"Bem-vindo, {st.session_state['usuario']}!")
                    st.rerun()

            except Exception as e:
                st.error(f"Erro ao fazer login: {str(e)}")
    
    with col2:
        if st.button("Esqueci a Senha", use_container_width=True):
            st.warning("Entre em contato com o administrador para redefinir sua senha.")

def criar_novo_usuario(email, senha, nome, perfil):
    try:
        # Verificar se o usuário atual tem permissão para criar novos usuários
        if not tem_permissao_criar_usuario():
            st.error("Você não tem permissão para criar novos usuários.")
            return False

        user = auth.create_user(
            email=email,
            password=senha
        )
        
        # Adicionar informações adicionais ao Realtime Database
        user_ref = db.reference(f'/usuarios/{user.uid}')
        user_ref.set({
            'nome': nome,
            'email': email,
            'perfil': perfil,
            'ativo': True,
            'data_criacao': get_data_hora_brasil()
        })
        
        return True
    except Exception as e:
        st.error(f"Erro ao criar usuário: {str(e)}")
        return False

def tem_permissao_criar_usuario():
    if 'perfil' not in st.session_state:
        return False
    
    perfil_atual = st.session_state['perfil']
    perfis_ref = db.reference('/perfis')
    perfis = perfis_ref.get()
    
    if perfis and perfil_atual in perfis:
        return perfis[perfil_atual].get('editar_usuarios', False)
    
    return False

def menu_lateral():
    if 'user_id' not in st.session_state:
        return None  # Retorna None se o usuário não estiver autenticado

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

        # Obter as permissões do perfil do usuário
        permissoes = get_permissoes_perfil(st.session_state.get('perfil', 'vendedor'))
        
        # Lista de itens de menu com base nas permissões
        menu_items = []
        if permissoes.get('dashboard', False):
            menu_items.append("📊 Dashboard")
        if permissoes.get('requisicoes', False):
            menu_items.append("📝 Requisições")
        if permissoes.get('cotacoes', False):
            menu_items.append("🛒 Cotações")
        if permissoes.get('importacao', False):
            menu_items.append("✈️ Importação")
        if permissoes.get('configuracoes', False):
            menu_items.append("⚙️ Configurações")
        
        if not menu_items:
            st.warning("Nenhuma tela disponível para este perfil.")
            return None
        
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
                try:
                    firebase_admin.auth.revoke_refresh_tokens(st.session_state.get('user_id', ''))
                except Exception as e:
                    st.error(f"Erro ao fazer logout: {str(e)}")
                finally:
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    st.rerun()

        return menu.split(" ")[-1]

def dashboard():
    # Garante que as requisições sejam carregadas
    if 'requisicoes' not in st.session_state:
        st.session_state.requisicoes = carregar_requisicoes()
    
    # Definição dos ícones e cores dos status com transparência
    status_config = {
        'ABERTA': {'icon': '📋', 'cor': 'rgba(46, 204, 113, 0.7)'},  # Verde
        'EM ANDAMENTO': {'icon': '⏳', 'cor': 'rgba(241, 196, 15, 0.7)'},  # Amarelo
        'FINALIZADA': {'icon': '✅', 'cor': 'rgba(52, 152, 219, 0.7)'},  # Azul
        'RECUSADA': {'icon': '🚫', 'cor': 'rgba(231, 76, 60, 0.7)'},  # Vermelho
        'TOTAL': {'icon': '📉', 'cor': 'rgba(149, 165, 166, 0.7)'}  # Cinza
    }
    
    # Filtrar requisições baseado no perfil do usuário
    if st.session_state.get('perfil') == 'vendedor':
        requisicoes_filtradas = [r for r in st.session_state.requisicoes if r['vendedor'] == st.session_state.get('usuario')]
        st.info(f"Visualizando requisições do vendedor: {st.session_state.get('usuario')}")
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

            numero_req = get_next_requisition_number()
            if numero_req is None:
                st.error("ERRO AO GERAR NÚMERO DA REQUISIÇÃO. TENTE NOVAMENTE.")
                return

            nova_req = {
                'numero': numero_req,
                'cliente': cliente,
                'vendedor': st.session_state['usuario'],
                'data_hora': get_data_hora_brasil(),
                'status': 'ABERTA',
                'items': st.session_state.items_temp.copy(),
                'observacoes_vendedor': observacoes_vendedor
            }
            if salvar_requisicao(nova_req):
                    # Limpar os dados temporários
                    st.session_state.items_temp = []
                    st.session_state['modo_requisicao'] = None

                    # Atualizar a lista de requisições
                    st.session_state.requisicoes = carregar_requisicoes()

                    # Exibir toast de sucesso
                    st.toast('Requisição enviada com sucesso!', icon='✅')
                    
                    # Aguardar brevemente antes de recarregar
                    time.sleep(1)
                    st.rerun()
                
def salvar_configuracoes():
    try:
        # Referência para o nó 'configuracoes' no Firebase
        config_ref = db.reference('/configuracoes')
        
        # Salvar as configurações no Firebase
        config_ref.set(st.session_state.config_sistema)
        
        st.success("Configurações salvas com sucesso!")
    except Exception as e:
        st.error(f"Erro ao salvar configurações: {str(e)}")

def carregar_configuracoes():
    try:
        # Referência para o nó 'configuracoes' no Firebase
        config_ref = db.reference('/configuracoes')
        
        # Obter as configurações do Firebase
        configuracoes = config_ref.get()
        
        # Se não houver configurações, retornar um dicionário vazio ou configurações padrão
        if not configuracoes:
            return {}  # ou return configuracoes_padrao
        
        return configuracoes
    except Exception as e:
        st.error(f"Erro ao carregar configurações: {e}")
        return {}  # ou return configuracoes_padrao

# Inicialização das configurações (você pode adicionar isso no início do seu script principal)
if 'config_sistema' not in st.session_state:
    st.session_state.config_sistema = carregar_configuracoes()

def carregar_temas():
    try:
        temas_ref = db.reference('/temas')
        temas = temas_ref.get()
        if temas:
            return temas
        else:
            return {}
    except Exception as e:
        st.error(f"Erro ao carregar temas: {str(e)}")
        return {}

def aplicar_tema(tema):
    if tema:
        st.markdown(f"""
            <style>
            body {{
                font-family: {tema.get('font_family', 'Arial')};
                font-size: {tema.get('font_size', 12)}px;
                color: {tema.get('text_color', '#000000')};
                background-color: {tema.get('background_color', '#FFFFFF')};
            }}
            :root {{
                --primary-color: {tema.get('primary_color', '#2D2C74')};
                --background-color: {tema.get('background_color', '#FFFFFF')};
                --text-color: {tema.get('text_color', '#000000')};
            }}
            </style>
        """, unsafe_allow_html=True)
        st.success("Tema aplicado com sucesso!")
    else:
        st.warning("Nenhum tema selecionado.")

def salvar_tema_usuario(tema):
    try:
        tema_usuario_ref = db.reference(f'/temas_usuarios/{st.session_state["usuario"]}')
        tema_usuario_ref.set(tema)
        st.success("Tema salvo para o usuário com sucesso!")
    except Exception as e:
        st.error(f"Erro ao salvar tema: {str(e)}")

def remover_tema_usuario():
    try:
        tema_usuario_ref = db.reference(f'/temas_usuarios/{st.session_state["usuario"]}')
        tema_usuario_ref.delete()
        st.success("Tema removido para o usuário com sucesso!")
    except Exception as e:
        st.error(f"Erro ao remover tema: {str(e)}")

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

        # Carrega as requisições do Firebase
        requisicoes_firebase = carregar_requisicoes()

        # Verifica se st.session_state.requisicoes existe, senão, inicializa com as requisições do Firebase
        if 'requisicoes' not in st.session_state:
            st.session_state.requisicoes = requisicoes_firebase
        else:
            # Se já existe, atualiza com os dados do Firebase
            st.session_state.requisicoes = requisicoes_firebase

        # Lógica de filtragem e exibição
        requisicoes_visiveis = []
        if st.session_state['perfil'] == 'vendedor':
            requisicoes_visiveis = [req for req in st.session_state.requisicoes if req['vendedor'] == st.session_state['usuario']]
        else:
            requisicoes_visiveis = st.session_state.requisicoes.copy()

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
                        'rgba(46, 204, 113, 0.2)' if req['status'] == 'ABERTA'
                        else 'rgba(241, 196, 15, 0.2)' if req['status'] == 'EM ANDAMENTO'
                        else 'rgba(52, 152, 219, 0.2)' if req['status'] == 'FINALIZADA'
                        else 'rgba(231, 76, 60, 0.2)' if req['status'] == 'RECUSADA'
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
                            <span>COMPRADOR: {req.get('comprador_responsavel', '-')}
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

                        # Garante que req['items'] é uma lista de dicionários
                        items = req.get('items', [])
                        if items and isinstance(items, str):
                            try:
                                items = json.loads(items)  # Converte a string JSON para uma lista
                            except json.JSONDecodeError as e:
                                st.error(f"Erro ao decodificar os itens da requisição {req['numero']}: {e}")
                                items = []  # Garante que items seja uma lista vazia para evitar erros

                        if items:
                            items_df = pd.DataFrame([{
                                'Código': item.get('codigo', '-'),
                                'Cód. Fabricante': item.get('cod_fabricante', '-'),
                                'Descrição': item['descricao'],
                                'Marca': item.get('marca', 'PC'),
                                'QTD': item['quantidade'],
                                'R$ Venda Unit': f"R$ {item.get('venda_unit', 0):.2f}",
                                'R$ Total': f"R$ {(item.get('venda_unit', 0) * item['quantidade']):.2f}",
                                'Prazo': item.get('prazo_entrega', '-')
                            } for item in items])

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
                                    options=[f"ITEM {item['item']}: {item['descricao']}" for item in items],
                                    key=f"select_item_{req['numero']}"
                                )

                                # Índice do item selecionado
                                item_idx = int(item_selecionado.split(':')[0].replace('ITEM ', '')) - 1
                                item = items[item_idx]

                                # Campos de resposta em linha única
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    custo_str = st.text_input(
                                        "R$ UNIT",
                                        value=f"{item.get('custo_unit', 0.0):,.2f}".replace(',', '_').replace('.', ',').replace('_', '.'),
                                        key=f"custo_{req['numero']}_{item_idx}"
                                    )
                                    # Converte o valor digitado para float
                                    try:
                                        custo_str = custo_str.replace('.', '').replace(',', '.')
                                        item['custo_unit'] = float(custo_str)
                                    except ValueError:
                                        item['custo_unit'] = 0.0

                                with col2:
                                    item['markup'] = st.number_input(
                                        "% MARKUP",
                                        value=item.get('markup', 0.0),
                                        min_value=0.0,
                                        format="%.0f",
                                        step=1.0,
                                        key=f"markup_{req['numero']}_{item_idx}"
                                    )
                                with col3:
                                    item['prazo_entrega'] = st.text_input(
                                        "PRAZO",
                                        value=item.get('prazo_entrega', ''),
                                        key=f"prazo_{req['numero']}_{item_idx}"
                                    )

                                # Cálculo automático quando custo e markup são preenchidos
                                if item['custo_unit'] > 0 and item['markup'] > 0:
                                    item['venda_unit'] = item['custo_unit'] * (1 + (item['markup'] / 100))
                                    item['venda_total'] = item['venda_unit'] * item['quantidade']
                                    item['salvo'] = True
                                    salvar_requisicao(req)

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
                                        if mostrar_obs:
                                            req['observacao_geral'] = observacao_geral
                                        salvar_requisicao(req)
                                        st.success(f"ITEM {item['item']} SALVO COM SUCESSO!")
                                        st.rerun()

                                with col_btn2:
                                    todos_itens_salvos = all(item.get('salvo', False) for item in items)
                                    if todos_itens_salvos:
                                        if st.button("✅ FINALIZAR", key=f"finalizar_{req['numero']}", type="primary"):
                                            req['status'] = 'FINALIZADA'
                                            req['data_hora_resposta'] = get_data_hora_brasil()
                                            if salvar_requisicao(req):
                                                enviar_email_requisicao(req, "finalizada")
                                                st.success("REQUISIÇÃO FINALIZADA COM SUCESSO!")
                                                st.rerun()
                                            else:
                                                st.error("ERRO AO SALVAR A REQUISIÇÃO. TENTE NOVAMENTE.")
                                                
def get_permissoes_perfil(perfil):
    # Referência para o nó 'perfis' no Firebase
    perfis_ref = db.reference('perfis')
    
    # Busca as permissões do perfil específico no Firebase
    permissoes = perfis_ref.child(perfil).get()
    
    # Se não encontrar permissões específicas, use as permissões padrão
    if not permissoes:
        permissoes_padrao = {
            'vendedor': {
                'dashboard': True,
                'requisicoes': True,
                'cotacoes': True,
                'importacao': False,
                'configuracoes': False,
                'editar_usuarios': False,
                'excluir_usuarios': False,
                'editar_perfis': False
            },
            'comprador': {
                'dashboard': True,
                'requisicoes': True,
                'cotacoes': True,
                'importacao': True,
                'configuracoes': False,
                'editar_usuarios': False,
                'excluir_usuarios': False,
                'editar_perfis': False
            },
            'administrador': {
                'dashboard': True,
                'requisicoes': True,
                'cotacoes': True,
                'importacao': True,
                'configuracoes': True,
                'editar_usuarios': True,
                'excluir_usuarios': True,
                'editar_perfis': True
            }
        }
        permissoes = permissoes_padrao.get(perfil, permissoes_padrao['vendedor'])
        
        # Salva as permissões padrão no Firebase para uso futuro
        perfis_ref.child(perfil).set(permissoes)
    
    return permissoes

def configuracoes():
    st.title("Configurações")

    permissoes = get_permissoes_perfil(st.session_state['perfil'])

    if permissoes.get('configuracoes', False):
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

        # Botão para cadastrar novo usuário (só aparece se tiver permissão)
        if permissoes.get('cadastrar_usuarios', False):
            if st.button("➕ Cadastrar Novo Usuário", type="primary", use_container_width=True):
                st.session_state['modo_usuario'] = 'cadastrar'
                st.rerun()

        # Form para cadastrar novo usuário (só aparece se o botão for clicado)
        if st.session_state.get('modo_usuario') == 'cadastrar':
            with st.form("cadastro_usuario"):
                st.subheader("Cadastrar Novo Usuário")

                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    novo_usuario = st.text_input("Nome do Usuário").upper()
                with col2:
                    email = st.text_input("Email")
                with col3:
                    perfil = st.selectbox("Perfil", ['vendedor', 'comprador', 'administrador'])

                if st.form_submit_button("Cadastrar"):
                    if novo_usuario and email and perfil:
                        usuarios_ref = db.reference('usuarios')
                        novo_usuario_data = {
                            'nome': novo_usuario,
                            'email': email,
                            'perfil': perfil,
                            'ativo': True
                        }
                        usuarios_ref.child(novo_usuario).set(novo_usuario_data)
                        st.success(f"Usuário {novo_usuario} cadastrado com sucesso!")
                        st.session_state['modo_usuario'] = None
                        st.rerun()
                    else:
                        st.error("Por favor, preencha todos os campos.")

        usuarios_ref = db.reference('usuarios')
        usuarios_filtrados = usuarios_ref.get()

        if usuarios_filtrados and permissoes.get('editar_usuarios', False):
            st.markdown("#### Editar Usuário")
            usuario_editar = st.selectbox("Selecionar usuário para editar:", list(usuarios_filtrados.keys()))

            if isinstance(usuarios_filtrados, dict):
                if usuario_editar:
                    dados_usuario = usuarios_filtrados[usuario_editar]
                    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])

                    with col1:
                        novo_nome = st.text_input("Nome", value=usuario_editar).upper()
                    with col2:
                        novo_email = st.text_input("Email", value=dados_usuario['email'])
                    with col3:
                        novo_perfil = st.selectbox("Perfil",
                                                 options=['vendedor', 'comprador', 'administrador'],
                                                 index=['vendedor', 'comprador', 'administrador'].index(
                                                     dados_usuario['perfil']))
                    with col4:
                        novo_status = st.toggle("Ativo", value=dados_usuario['ativo'])

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("💾 Salvar Alterações", type="primary", use_container_width=True):
                            if novo_nome != usuario_editar and novo_nome in usuarios_filtrados:
                                st.error("Nome de usuário já existe")
                            else:
                                novo_dados = {
                                    'email': novo_email,
                                    'perfil': novo_perfil,
                                    'ativo': novo_status,
                                }
                                if novo_nome != usuario_editar:
                                    usuarios_ref.child(usuario_editar).delete()
                                    usuarios_ref.child(novo_nome).set(novo_dados)
                                else:
                                    usuarios_ref.child(novo_nome).update(novo_dados)
                            st.success("Alterações salvas com sucesso!")
                            st.rerun()

                    with col2:
                        if st.button("🔄 Reset Senha", type="primary", use_container_width=True):
                            usuarios_ref.child(novo_nome).update({
                                'senha': None,
                                'primeiro_acesso': True
                            })
                            st.success("Senha resetada com sucesso!")
                            st.rerun()

                    with col3:
                        # Excluir Usuário (só aparece se tiver permissão)
                        if permissoes.get('excluir_usuarios', False):
                            if st.button("❌ Excluir Usuário", type="primary", use_container_width=True):
                                if dados_usuario['perfil'] != 'administrador':
                                    usuarios_ref.child(novo_nome).delete()
                                    st.success("Usuário excluído com sucesso!")
                                    st.rerun()
                                else:
                                    st.error("Não é possível excluir um administrador")
            else:
                st.warning("Nenhum usuário encontrado para editar.")

        st.markdown("#### Usuários Cadastrados")
        usuarios_ref = db.reference('usuarios')
        usuarios = usuarios_ref.get()

        # Verifica se usuarios é um dicionário antes de prosseguir
        if isinstance(usuarios, dict):
            usuarios_df = pd.DataFrame([{
                'Usuário': usuario,
                'Email': dados['email'],
                'Perfil': dados['perfil'],
                'Status': '🟢 Ativo' if dados['ativo'] else '🔴 Inativo'
            } for usuario, dados in usuarios.items()])

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
        else:
            st.info("Nenhum usuário cadastrado.")
    # Seção de Perfis
    elif st.session_state.get('config_modo') == 'perfis':
        st.markdown("### Gerenciamento de Perfis")
        
        perfil_selecionado = st.selectbox("Selecione o perfil para editar", ['vendedor', 'comprador', 'administrador'])
        
        st.markdown("#### Permissões de Acesso")
        st.markdown("Defina as telas que este perfil poderá acessar:")
        
        col1, col2 = st.columns(2)
        
        perfis_ref = db.reference('perfis')
        perfil_atual = perfis_ref.child(perfil_selecionado).get() or {}
        
        with col1:
            st.markdown("##### Telas do Sistema")
            permissoes = {}
            for tela, icone in [
                ('dashboard', '📊 Dashboard'),
                ('requisicoes', '📝 Requisições'),
                ('cotacoes', '🛒 Cotações'),
                ('importacao', '✈️ Importação'),
                ('configuracoes', '⚙️ Configurações')
            ]:
                valor_padrao = True if tela in ['dashboard', 'requisicoes', 'cotacoes'] else False
                key = f"{perfil_selecionado}_{tela}"
                permissoes[tela] = st.toggle(
                    icone,
                    value=perfil_atual.get(tela, valor_padrao),
                    key=key
                )
        
        with col2:
            st.markdown("##### Permissões Administrativas")
            for permissao, icone in [
                ('cadastrar_usuarios', '➕ Cadastrar Usuários'),
                ('editar_usuarios', '👥 Editar Usuários'),
                ('excluir_usuarios', '❌ Excluir Usuários'),
                ('editar_perfis', '🔑 Editar Perfis')
            ]:
                valor_padrao = True if perfil_selecionado == 'administrador' else False
                key = f"{perfil_selecionado}_{permissao}"
                permissoes[permissao] = st.toggle(
                    icone,
                    value=perfil_atual.get(permissao, valor_padrao),
                    key=key
                )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Salvar Permissões", type="primary", use_container_width=True):
                try:
                    perfis_ref.child(perfil_selecionado).set(permissoes)
                    st.success(f"Permissões do perfil {perfil_selecionado} atualizadas com sucesso!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar permissões: {str(e)}")
            
    # Seção de Sistema
    if st.session_state.get('config_modo') == 'sistema':
        st.markdown("### Configurações do Sistema")

        if st.session_state['perfil'] == 'administrador':
            tab1, tab2 = st.tabs(["📊 Monitoramento", "🎨 Personalizar"])

            with tab1:
                if permissoes.get('acessar_monitoramento', False):
                    st.markdown("#### Monitoramento do Sistema")

                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("##### Banco de Dados")
                        try:
                            requisicoes_ref = db.reference('requisicoes')
                            total_requisicoes = len(requisicoes_ref.get() or {})

                            st.metric("Total de Requisições", total_requisicoes)
                            st.metric("Tamanho do Banco", "N/A para Firebase")
                        except Exception as e:
                            st.error(f"Erro ao acessar banco de dados: {str(e)}")

                    st.markdown("##### Desempenho do Firebase")
                    try:
                        st.info("Funcionalidade em desenvolvimento")
                    except Exception as e:
                        st.error(f"Erro ao monitorar desempenho do Firebase: {str(e)}")

                with col2:
                    st.markdown("##### Gerenciamento de Backups")
                    col_backup, col_import = st.columns(2)
                    with col_backup:
                        backup_dir = "backups"
                        if not os.path.exists(backup_dir):
                            os.makedirs(backup_dir)

                        if st.button("💾 Backup Manual", type="primary"):
                            try:
                                all_data = db.reference().get()
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                backup_file = f"{backup_dir}/backup_{timestamp}.json"

                                with open(backup_file, 'w') as f:
                                    json.dump(all_data, f, indent=4)

                                st.success(f"Backup criado com sucesso: {backup_file}")
                            except Exception as e:
                                st.error(f"Erro ao criar backup: {str(e)}")

                    with col_import:
                        st.markdown("##### Importação de Backup")
                        uploaded_file = st.file_uploader(
                            "Selecione o arquivo de backup",
                            type=['json'],
                            help="Arquivos suportados: JSON"
                        )

                        if uploaded_file is not None:
                            if st.button("📥 Restaurar Backup", type="primary"):
                                try:
                                    dados = json.loads(uploaded_file.getvalue().decode('utf-8'))
                                    requisicoes_ref = db.reference('requisicoes')
                                    for req in dados:
                                        requisicoes_ref.child(str(req['numero'])).set(req)

                                    st.success(f"Backup restaurado com sucesso! {len(dados)} requisições importadas.")
                                    st.rerun()

                                except Exception as e:
                                    st.error(f"Erro na restauração: {str(e)}")

                st.markdown("##### Backups Disponíveis")
                backup_dir = "backups"
                if os.path.exists(backup_dir):
                    backup_files = [f for f in os.listdir(backup_dir) if f.endswith(('.zip', '.json', '.txt', '.py'))]

                    if backup_files:
                        backup_info = []
                        for backup_file in backup_files:
                            file_path = os.path.join(backup_dir, backup_file)
                            file_size = os.path.getsize(file_path)
                            creation_time = os.path.getctime(file_path)
                            sp_tz = pytz.timezone('America/Sao_Paulo')
                            creation_datetime = datetime.fromtimestamp(creation_time)
                            creation_datetime = pytz.utc.localize(creation_datetime).astimezone(sp_tz)
                            backup_info.append({
                                'arquivo': backup_file,
                                'caminho': file_path,
                                'tamanho': file_size,
                                'data_criacao': creation_datetime,
                                'tipo': 'AUTOMÁTICO' if 'auto' in backup_file.lower() else 'MANUAL'
                            })

                        backup_info.sort(key=lambda x: x['data_criacao'], reverse=True)

                        for backup in backup_info:
                            col_arquivo, col_data, col_tamanho, col_download, col_excluir = st.columns([4, 3, 2, 1, 1])

                            with col_arquivo:
                                st.markdown(f"**{backup['arquivo']}**")
                            with col_data:
                                st.markdown(f"{backup['data_criacao'].strftime('%d/%m/%Y %H:%M:%S')}")
                            with col_tamanho:
                                tamanho_kb = backup['tamanho'] / 1024
                                st.markdown(f"{tamanho_kb:.1f} KB")
                            with col_download:
                                with open(backup['caminho'], "rb") as f:
                                    bytes_data = f.read()
                                    st.download_button(
                                        label="⬇️",
                                        data=bytes_data,
                                        file_name=backup['arquivo'],
                                        mime="application/octet-stream",
                                        key=f"download_{backup['arquivo']}"
                                    )
                            with col_excluir:
                                if st.button("🗑️", key=f"delete_{backup['arquivo']}"):
                                    try:
                                        os.remove(backup['caminho'])
                                        st.success("Backup removido com sucesso!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Erro ao remover backup: {str(e)}")

                    else:
                        st.info("Nenhum arquivo de backup encontrado.")

            with tab2:
                if permissoes.get('acessar_personalizacao', False):
                    st.write("#### Personalização do Tema")

                    if 'theme_config' not in st.session_state:
                        st.session_state['theme_config'] = {
                            'font_family': 'Arial',
                            'font_size': 12,
                            'primary_color': '#2D2C74',
                            'background_color': '#FFFFFF',
                            'text_color': '#000000'
                        }

                    # Estilos de letras
                    font_family = st.selectbox("Estilo da Fonte", [
                                                "Arial",
                                                "Verdana",
                                                "Times New Roman",
                                                "Helvetica",
                                                "Georgia",
                                                "Courier New",
                                                "Lucida Sans Unicode",
                                                "Tahoma",
                                                "Trebuchet MS",
                                                "Impact",
                                                "Comic Sans MS",
                                                "Arial Black",
                                                "Book Antiqua",
                                                "Cambria",
                                                "Didot",
                                                "Garamond",
                                                "Lucida Console",
                                                "Palatino Linotype"
                                            ],
                                               index=[
                                                    "Arial",
                                                    "Verdana",
                                                    "Times New Roman",
                                                    "Helvetica",
                                                    "Georgia",
                                                    "Courier New",
                                                    "Lucida Sans Unicode",
                                                    "Tahoma",
                                                    "Trebuchet MS",
                                                    "Impact",
                                                    "Comic Sans MS",
                                                    "Arial Black",
                                                    "Book Antiqua",
                                                    "Cambria",
                                                    "Didot",
                                                    "Garamond",
                                                    "Lucida Console",
                                                    "Palatino Linotype"
                                               ].index(st.session_state['theme_config'].get('font_family', 'Arial')),
                                               key='font_family')

                    # Tamanho da fonte
                    font_size = st.slider("Tamanho da Fonte", 10, 24,
                                         st.session_state['theme_config'].get('font_size', 12),
                                         key='font_size')

                    # Cores do tema
                    primary_color = st.color_picker("Cor Primária",
                                                    st.session_state['theme_config'].get('primary_color', '#2D2C74'),
                                                    key='primary_color')
                    background_color = st.color_picker("Cor de Fundo",
                                                        st.session_state['theme_config'].get('background_color',
                                                                                             '#FFFFFF'),
                                                        key='background_color')
                    text_color = st.color_picker("Cor do Texto",
                                                    st.session_state['theme_config'].get('text_color', '#000000'),
                                                    key='text_color')

                    # Aplica as configurações de estilo dinamicamente
                    st.markdown(f"""
                        <style>
                        body {{
                            font-family: {font_family};
                            font-size: {font_size}px;
                            color: {text_color};
                            background-color: {background_color};
                        }}
                        :root {{
                            --primary-color: {primary_color};
                            --background-color: {background_color};
                            --text-color: {text_color};
                        }}
                        </style>
                    """, unsafe_allow_html=True)

                    # Salvar as configurações
                    if st.button("Salvar Personalização"):
                        theme_config = {
                            "font_family": font_family,
                            "font_size": font_size,
                            "primary_color": primary_color,
                            "background_color": background_color,
                            "text_color": text_color
                        }
                        st.session_state['theme_config'] = theme_config
                        salvar_configuracoes()
                        st.success("Personalização salva com sucesso!")
                else:
                    st.info("Você não tem permissão para acessar esta tela.")
                    
def main():
    if 'usuario' not in st.session_state:
        tela_login()
    else:
        # Adiciona a mensagem fixa
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
        
        permissoes = get_permissoes_perfil(st.session_state.get('perfil', 'vendedor'))
        
        if menu == "Dashboard" and permissoes.get('dashboard', False):
            dashboard()
        elif menu == "Requisições" and permissoes.get('requisicoes', False):
            requisicoes()
        elif menu == "Cotações" and permissoes.get('cotacoes', False):
            st.title("Cotações")
            st.info("Funcionalidade em desenvolvimento")
        elif menu == "Importação" and permissoes.get('importacao', False):
            st.title("Importação")
            st.info("Funcionalidade em desenvolvimento")
        elif menu == "Configurações" and permissoes.get('configuracoes', False):
            configuracoes()
        else:
            st.error("Você não tem permissão para acessar esta tela.")

if __name__ == "__main__":
    main()