import streamlit as st
import sqlite3
import hashlib
import firebase_admin
import pandas as pd
import time
import zipfile
import matplotlib.pyplot as plt
import gzip
import logging
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
import locale
from streamlit_autorefresh import st_autorefresh
from firebase_admin import credentials, db
from email.mime.base import MIMEBase
from email import encoders

BACKUP_CONFIG = {
    'frequencia': 'diario',  # diario, horario, personalizado
    'hora': '18:00',  # Para backups diários
    'intervalo_horas': 1,  # Para backups horários
    'dias_semana': [0, 1, 2, 3, 4],  # 0=segunda, 6=domingo
    'enviar_email': True,
    'email_destino': 'Importacao@jetfrio.com.br',
    'ultimo_backup': None
}

def carregar_config_backup():
    try:
        with open('config_backup.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Se o arquivo não existir, cria com valores padrão
        with open('config_backup.json', 'w') as f:
            json.dump(BACKUP_CONFIG, f)
        return BACKUP_CONFIG.copy()

def salvar_config_backup(config):
    with open('config_backup.json', 'w') as f:
        json.dump(config, f)
        
def gerar_hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def inicializar_banco_usuarios():
    os.makedirs('database', exist_ok=True)
    conn = sqlite3.connect('database/usuarios.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL,
        senha TEXT,
        perfil TEXT NOT NULL,
        ativo BOOLEAN NOT NULL DEFAULT 1,
        primeiro_acesso BOOLEAN NOT NULL DEFAULT 1,
        token_sessao TEXT,
        data_ultimo_acesso TEXT,
        data_criacao TEXT NOT NULL,
        data_modificacao TEXT
    )
    ''')
    
    conn.commit()
    conn.close()

def inicializar_sistema():
    try:
        # Criar diretórios necessários
        os.makedirs('database', exist_ok=True)
        os.makedirs('backups', exist_ok=True)
        
        # Inicializar bancos
        inicializar_banco_usuarios()
        inicializar_banco()
        
        # Migrar dados existentes se necessário
        if os.path.exists('usuarios.json'):
            conn = sqlite3.connect('database/usuarios.db')
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM usuarios')
            total_usuarios = cursor.fetchone()[0]
            conn.close()
            
            # Só migra se não houver usuários no banco
            if total_usuarios == 0:
                migrar_usuarios_json_para_sqlite()
        
        # Executar backup automático diário
        timestamp = datetime.now().strftime('%d%m%Y')
        backup_path = f'backups/backup_{timestamp}.zip'
        
        # Verifica se já existe backup do dia
        if not os.path.exists(backup_path):
            backup_automatico()
            
        # Verificar se é hora de enviar o backup por email (18h)
        fuso_brasil = pytz.timezone('America/Sao_Paulo')
        hora_atual = datetime.now(fuso_brasil).hour
        minuto_atual = datetime.now(fuso_brasil).minute
        
        # Arquivo para controlar o último envio
        ultimo_envio_file = 'ultimo_envio_backup.txt'
        hoje = datetime.now(fuso_brasil).strftime('%Y-%m-%d')
        
        # Verifica se é 18h e ainda não foi enviado hoje
        if hora_atual == 18 and minuto_atual < 5:  # Janela de 5 minutos para evitar múltiplos envios
            enviar_hoje = True
            
            if os.path.exists(ultimo_envio_file):
                with open(ultimo_envio_file, 'r') as f:
                    ultimo_envio = f.read().strip()
                if ultimo_envio == hoje:
                    enviar_hoje = False
            
            if enviar_hoje:
                if os.path.exists(backup_path):
                    if enviar_backup_por_email(backup_path):
                        # Registrar o envio
                        with open(ultimo_envio_file, 'w') as f:
                            f.write(hoje)
                else:
                    logging.error(f"Arquivo de backup não encontrado para envio: {backup_path}")
            
        # Limpar backups antigos
        limpar_backups_antigos('backups')
        
        return True
    except Exception as e:
        st.error(f"Erro na inicialização do sistema: {str(e)}")
        logging.error(f"Erro na inicialização do sistema: {str(e)}")
        return False

def migrar_usuarios_json_para_sqlite():
    try:
        with open('usuarios.json', 'r', encoding='utf-8') as f:
            usuarios_json = json.load(f)
            
        conn = sqlite3.connect('database/usuarios.db')
        cursor = conn.cursor()
        
        for nome, dados in usuarios_json.items():
            cursor.execute('''
                INSERT OR REPLACE INTO usuarios 
                (nome, email, senha, perfil, ativo, primeiro_acesso, data_criacao)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                nome,
                dados['email'],
                dados['senha'],
                dados['perfil'],
                dados['ativo'],
                dados.get('primeiro_acesso', True),
                get_data_hora_brasil()
            ))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Erro na migração: {str(e)}")
        return False

def inicializar_banco():
    try:
        conn = sqlite3.connect('database/requisicoes.db')  # Caminho correto
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS requisicoes
            (numero TEXT PRIMARY KEY, 
            cliente TEXT,
            vendedor TEXT,
            data_hora TEXT,
            status TEXT,
            items TEXT,
            observacoes_vendedor TEXT,
            comprador_responsavel TEXT,
            data_hora_resposta TEXT,
            justificativa_recusa TEXT,
            observacao_geral TEXT)''')
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Erro ao inicializar banco: {str(e)}")

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
            destinatarios = [vendedor_email]
            if comprador_email:
                destinatarios.append(comprador_email)
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

def enviar_backup_por_email(backup_path, destinatario):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['EMAIL']
        msg['To'] = destinatario
        msg['Subject'] = f"Backup Automático - Portal Jetfrio - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        
        corpo_email = f"""
        <html>
            <body>
                <h2>Backup Automático do Sistema</h2>
                <p>Segue em anexo o backup automático gerado em {get_data_hora_brasil()}</p>
                <p><strong>Sistema:</strong> Portal Jetfrio</p>
                <p><strong>Tamanho do arquivo:</strong> {os.path.getsize(backup_path) / (1024 * 1024):.2f} MB</p>
                <p>Este é um email automático, por favor não responda.</p>
            </body>
        </html>
        """
        
        msg.attach(MIMEText(corpo_email, 'html'))
        
        # Anexar o arquivo de backup
        with open(backup_path, 'rb') as f:
            anexo = MIMEBase('application', 'octet-stream')
            anexo.set_payload(f.read())
            encoders.encode_base64(anexo)
            anexo.add_header('Content-Disposition', 'attachment', filename=os.path.basename(backup_path))
            msg.attach(anexo)
        
        # Enviar o email
        with smtplib.SMTP(EMAIL_CONFIG['SMTP_SERVER'], EMAIL_CONFIG['SMTP_PORT']) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['EMAIL'], EMAIL_CONFIG['PASSWORD'])
            server.send_message(msg)
        
        return True
    except Exception as e:
        st.error(f"Erro ao enviar backup por email: {str(e)}")
        return False

def verificar_backup_automatico():
    try:
        config_backup = carregar_config_backup()
        agora = datetime.now()
        ultimo_backup = config_backup.get('ultimo_backup')
        
        # Se nunca foi feito backup, faz agora
        if not ultimo_backup:
            backup_automatico()
            return
        
        # Converter para objeto datetime se for string
        if isinstance(ultimo_backup, str):
            try:
                ultimo_backup = datetime.strptime(ultimo_backup, '%H:%M:%S - %d/%m/%Y')
            except:
                ultimo_backup = None
        
        # Verificar frequência configurada
        if config_backup['frequencia'] == 'diario':
            hora_backup = datetime.strptime(config_backup['hora'], '%H:%M').time()
            if agora.time() >= hora_backup and (not ultimo_backup or ultimo_backup.date() < agora.date()):
                backup_automatico()
        
        elif config_backup['frequencia'] == 'horario':
            intervalo = timedelta(hours=config_backup['intervalo_horas'])
            if not ultimo_backup or (agora - ultimo_backup) >= intervalo:
                backup_automatico()
        
        elif config_backup['frequencia'] == 'personalizado':
            dia_semana = agora.weekday()
            if dia_semana in config_backup['dias_semana']:
                hora_backup = datetime.strptime(config_backup['hora'], '%H:%M').time()
                if agora.time() >= hora_backup and (not ultimo_backup or ultimo_backup.date() < agora.date()):
                    backup_automatico()
    
    except Exception as e:
        logging.error(f"Erro na verificação de backup automático: {str(e)}")

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
    diretorios = ['database', 'backups']
    for dir in diretorios:
        if not os.path.exists(dir):
            os.makedirs(dir)
            
    # Verificar se o banco existe
    if not os.path.exists('database/requisicoes.db'):
        inicializar_banco()
    return True

def importar_dados_antigos():
    timestamp = datetime.now().strftime('%d%m%Y_%H%M%S')  # Definir timestamp no início da função
    try:
        # Verificar maior número atual antes da importação
        conn = sqlite3.connect('database/requisicoes.db')
        cursor = conn.cursor()
        cursor.execute('SELECT MAX(CAST(numero AS INTEGER)) FROM requisicoes')
        ultimo_numero_atual = cursor.fetchone()[0] or 4999
        
        # Carregar dados do JSON
        with open('requisicoes.json', 'r', encoding='utf-8') as file:
            requisicoes_antigas = json.load(file)

        # Backup preventivo
        shutil.copy2('database/requisicoes.db', f'backups/pre_import_{timestamp}.db')

        # Inserir dados formatados
        for req in requisicoes_antigas:
            numero_req = int(req.get('REQUISIÇÃO', 0))
            if numero_req > ultimo_numero_atual:
                ultimo_numero_atual = numero_req
                
            items = [{
                'item': 1,
                'codigo': req.get('CÓDIGO', ''),
                'cod_fabricante': '',
                'descricao': req.get('DESCRIÇÃO', ''),
                'marca': req.get('MARCA', ''),
                'quantidade': float(req.get('QUANTIDADE', 0)),
                'status': 'ABERTA'
            }]
            
            cursor.execute('''
                INSERT OR REPLACE INTO requisicoes 
                (numero, cliente, vendedor, data_hora, status, items, 
                observacoes_vendedor, comprador_responsavel, data_hora_resposta,
                justificativa_recusa, observacao_geral)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                req.get('REQUISIÇÃO'),
                req.get('CLIENTE'),
                req.get('VENDEDOR'),
                req.get('Data/Hora Criação:'),
                req.get('STATUS'),
                json.dumps(items),
                '',
                req.get('COMPRADOR', ''),
                req.get('Data/Hora Resposta:'),
                '',
                req.get('OBSERVAÇÕES DO COMPRADOR', '')
            ))

        # Atualizar último número
        with open('ultimo_numero.json', 'w') as f:
            json.dump({'numero': ultimo_numero_atual}, f)
            
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        # Restaurar backup em caso de erro
        if os.path.exists(f'backups/pre_import_{timestamp}.db'):
            shutil.copy2(f'backups/pre_import_{timestamp}.db', 'database/requisicoes.db')
        print(f"Erro na importação: {str(e)}")
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
    try:
        with open('usuarios.json', 'r', encoding='utf-8') as f:
            usuarios = json.load(f)
            return usuarios
    except json.JSONDecodeError:
        # Retorna usuário padrão em caso de erro
        return {
            'ZAQUEU SOUZA': {
                'senha': None,
                'perfil': 'administrador',
                'email': 'zaqueu@jetfrio.com.br',
                'ativo': True,
                'primeiro_acesso': True
            }
        }

def salvar_usuarios():
    try:
        backup_file = 'usuarios.json.bak'
        # Fazer backup do arquivo atual
        if os.path.exists('usuarios.json'):
            shutil.copy2('usuarios.json', backup_file)
            
        # Salvar os dados garantindo que primeiro_acesso seja salvo corretamente
        with open('usuarios.json', 'w', encoding='utf-8') as f:
            usuarios_para_salvar = {
                usuario: {
                    'senha': str(dados['senha']),
                    'perfil': dados['perfil'],
                    'email': dados['email'],
                    'ativo': dados['ativo'],
                    'primeiro_acesso': dados.get('primeiro_acesso', True)
                }
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

def migrar_dados_json_para_sqlite():
    try:
        with open('requisicoes.json', 'r', encoding='utf-8') as f:
            requisicoes_json = json.load(f)
        
        conn = sqlite3.connect('database/requisicoes.db')
        cursor = conn.cursor()
        
        for req in requisicoes_json:
            cursor.execute('''
                INSERT OR REPLACE INTO requisicoes 
                (numero, cliente, vendedor, data_hora, status, items, 
                observacoes_vendedor, comprador_responsavel, data_hora_resposta,
                justificativa_recusa, observacao_geral)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                req['REQUISIÇÃO'],
                req['CLIENTE'],
                req['VENDEDOR'],
                req['Data/Hora Criação:'],
                req['STATUS'],
                json.dumps([{
                    'codigo': req['CÓDIGO'],
                    'descricao': req['DESCRIÇÃO'],
                    'marca': req['MARCA'],
                    'quantidade': req['QUANTIDADE'],
                    'venda_unit': req[' R$ UNIT '].replace('R$ ', '').replace(',', '.').strip(),
                    'prazo_entrega': req['PRAZO']
                }]),
                '',
                req['COMPRADOR'],
                req['Data/Hora Resposta:'],
                '',
                req['OBSERVAÇÕES DO COMPRADOR']
            ))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Erro na migração: {str(e)}")
        return False
    
def carregar_requisicoes():
    try:
        conn = sqlite3.connect('database/requisicoes.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM requisicoes')
        requisicoes = []
        for row in cursor.fetchall():
            try:
                items = json.loads(row[5]) if row[5] else []
            except:
                items = []
                
            requisicao = {
                'numero': row[0],
                'cliente': row[1],
                'vendedor': row[2],
                'data_hora': row[3],
                'status': row[4],
                'items': items,
                'observacoes_vendedor': row[6],
                'comprador_responsavel': row[7],
                'data_hora_resposta': row[8],
                'justificativa_recusa': row[9],
                'observacao_geral': row[10]
            }
            requisicoes.append(requisicao)
        conn.close()
        return requisicoes
    except Exception as e:
        st.error(f"Erro ao carregar requisições: {str(e)}")
        return []

def renumerar_requisicoes():
    try:
        conn = sqlite3.connect('requisicoes.db')
        cursor = conn.cursor()
        
        # Buscar todas as requisições ordenadas por data
        cursor.execute('SELECT * FROM requisicoes ORDER BY data_hora')
        requisicoes = cursor.fetchall()
        
        # Iniciar numeração a partir de 5092
        novo_numero = 5092
        
        # Atualizar cada requisição com novo número
        for req in requisicoes:
            cursor.execute('''
                UPDATE requisicoes 
                SET numero = ? 
                WHERE numero = ?
            ''', (novo_numero, req[0]))
            novo_numero += 1
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Erro ao renumerar requisições: {str(e)}")
        return False

def backup_requisicoes():
    try:
        timestamp = datetime.now().strftime("%d%m%Y_%H%M%S")
        backup_file = f'backup/requisicoes_backup_{timestamp}.json'
        os.makedirs('backup', exist_ok=True)
        
        if os.path.exists('requisicoes.json'):
            shutil.copy2('requisicoes.json', backup_file)
            return True
        return False
    except Exception as e:
        print(f"Erro no backup: {str(e)}")
        return False

def verificar_integridade_db():
    conn = sqlite3.connect('database/requisicoes.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA integrity_check")
    resultado = cursor.fetchone()
    conn.close()
    return resultado[0] == 'ok'

def verificar_conteudo_backup(arquivo_backup):
    with zipfile.ZipFile(arquivo_backup, 'r') as zip_ref:
        arquivos_esperados = ['usuarios.db', 'requisicoes.db', 'usuarios.json', 'perfis.json', 'requisicoes.json', 'ultimo_numero.json']
        arquivos_presentes = zip_ref.namelist()
        return all(arquivo in arquivos_presentes for arquivo in arquivos_esperados)

def backup_automatico(dados=None):
    try:
        # Carrega configurações de backup
        config_backup = carregar_config_backup()
        
        # Criar diretório de backup se não existir
        backup_dir = 'backups/'
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%d%m%Y_%H%M%S')
        
        # Definir arquivos para backup
        arquivos_backup = {
            'usuarios_db': 'database/usuarios.db',
            'requisicoes_db': 'database/requisicoes.db',
            'usuarios': 'usuarios.json',
            'perfis': 'perfis.json',
            'requisicoes': 'requisicoes.json',
            'ultimo_numero': 'ultimo_numero.json'
        }
        
        backup_file = os.path.join(backup_dir, f'backup_{timestamp}.json')
        
        # Criar arquivo JSON com todos os dados
        dados_backup = {}
        for nome, arquivo in arquivos_backup.items():
            if os.path.exists(arquivo):
                if arquivo.endswith('.db'):
                    conn = sqlite3.connect(arquivo)
                    cursor = conn.cursor()
                    cursor.execute(f"SELECT * FROM {nome.split('_')[0]}")
                    dados = cursor.fetchall()
                    colunas = [desc[0] for desc in cursor.description]
                    dados_backup[nome] = {
                        'colunas': colunas,
                        'dados': dados
                    }
                    conn.close()
                else:
                    with open(arquivo, 'r', encoding='utf-8') as f:
                        dados_backup[nome] = json.load(f)
        
        # Salvar o backup em JSON
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(dados_backup, f, ensure_ascii=False, indent=4)
        
        # Enviar por email se configurado
        if config_backup.get('enviar_email', False):
            enviar_backup_por_email(backup_file, config_backup['email_destino'])
        
        # Atualizar último backup
        config_backup['ultimo_backup'] = get_data_hora_brasil()
        salvar_config_backup(config_backup)
        
        return backup_file, os.path.getsize(backup_file)
    except Exception as e:
        logging.error(f"Erro ao realizar backup: {str(e)}")
        return None, 0
    
def comprimir_backup(backup_path):
    with open(backup_path, 'rb') as f_in:
        with gzip.open(f'{backup_path}.gz', 'wb') as f_out:
            f_out.writelines(f_in)
    os.remove(backup_path)  # Remove o arquivo ZIP original após a compressão

def limpar_backups_antigos(backup_dir, dias_manter=7):
    try:
        data_limite = datetime.now() - timedelta(days=dias_manter)
        
        for arquivo in os.listdir(backup_dir):
            if arquivo.startswith('backup_') and arquivo.endswith('.zip'):
                caminho_arquivo = os.path.join(backup_dir, arquivo)
                data_arquivo = datetime.fromtimestamp(os.path.getctime(caminho_arquivo))
                
                if data_arquivo < data_limite:
                    os.remove(caminho_arquivo)
    except Exception as e:
        print(f"Erro ao limpar backups antigos: {str(e)}")

def listar_backups(backup_dir='backups/'):
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        
    st.title("Gerenciamento de Backups")
    
    # Lista e organiza backups
    backups = []
    for arquivo in os.listdir(backup_dir):
        if arquivo.startswith('backup_') and (arquivo.endswith('.zip') or arquivo.endswith('.gz')):
            caminho_arquivo = os.path.join(backup_dir, arquivo)
            tamanho = os.path.getsize(caminho_arquivo)
            data_criacao = datetime.fromtimestamp(os.path.getctime(caminho_arquivo))
            
            # Identifica se é backup automático ou manual
            tipo = 'AUTOMÁTICO' if 'auto' in arquivo.lower() else 'MANUAL'
            
            # Formata o tamanho do arquivo
            if tamanho < 1024:
                tamanho_fmt = f"{tamanho} B"
            elif tamanho < 1024**2:
                tamanho_fmt = f"{tamanho/1024:.1f} KB"
            else:
                tamanho_fmt = f"{tamanho/1024**2:.1f} MB"
            
            backups.append({
                'Data': data_criacao.strftime('%d/%m/%Y'),
                'Hora': data_criacao.strftime('%H:%M:%S'),
                'Tipo': tipo,
                'Tamanho': tamanho_fmt,
                'Arquivo': arquivo,
                'Caminho': caminho_arquivo
            })
    
    if backups:
        # Cria DataFrame e ordena por data/hora mais recente
        df = pd.DataFrame(backups)
        df = df.sort_values(by=['Data', 'Hora'], ascending=[False, False])
        
        # Configura a exibição do DataFrame
        st.dataframe(
            df,
            column_config={
                "Data": st.column_config.TextColumn(
                    "Data",
                    width="small",
                    help="Data de criação do backup"
                ),
                "Hora": st.column_config.TextColumn(
                    "Hora",
                    width="small"
                ),
                "Tipo": st.column_config.TextColumn(
                    "Tipo",
                    width="medium"
                ),
                "Tamanho": st.column_config.TextColumn(
                    "Tamanho",
                    width="small"
                ),
                "Arquivo": "Nome do Arquivo",
                "Caminho": None  # Oculta a coluna do caminho
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Adiciona botões de ação para cada backup
        for idx, backup in df.iterrows():
            col1, col2 = st.columns([1, 4])
            with col1:
                with open(backup['Caminho'], 'rb') as file:
                    st.download_button(
                        "📥 Download",
                        file,
                        file_name=backup['Arquivo'],
                        mime="application/octet-stream",
                        key=f"download_{idx}"
                    )
            with col2:
                if st.button("🗑️ Excluir", key=f"delete_{idx}"):
                    try:
                        os.remove(backup['Caminho'])
                        st.success("Backup removido com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao remover backup: {str(e)}")
    else:
        st.info("Nenhum backup encontrado.")

def restaurar_backup():
    try:
        conn = sqlite3.connect('database/requisicoes.db')
        cursor = conn.cursor()
        
        # Verificar maior número antes da restauração
        cursor.execute('SELECT MAX(CAST(numero AS INTEGER)) FROM requisicoes')
        ultimo_numero_atual = cursor.fetchone()[0] or 4999
        
        # Fazer backup preventivo antes de limpar
        timestamp = datetime.now().strftime('%d%m%dY_%H%M%S')
        shutil.copy2('database/requisicoes.db', f'backups/pre_restore_{timestamp}.db')
        
        # Limpa tabela atual
        cursor.execute('DELETE FROM requisicoes')
        
        # Carrega dados do backup
        with open('backup/ultimo_backup.json', 'r', encoding='utf-8') as f:
            dados = json.load(f)
            
        for req in dados:
            # Garante que items seja string JSON
            if isinstance(req['items'], list):
                req['items'] = json.dumps(req['items'])
            
            # Verifica se o número é maior que o último número atual
            if int(req['numero']) > ultimo_numero_atual:
                ultimo_numero_atual = int(req['numero'])
                
            cursor.execute('''
                INSERT INTO requisicoes 
                (numero, cliente, vendedor, data_hora, status, items,
                observacoes_vendedor, comprador_responsavel, data_hora_resposta,
                justificativa_recusa, observacao_geral)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                req['numero'],
                req['cliente'],
                req['vendedor'],
                req['data_hora'],
                req['status'],
                req['items'],
                req.get('observacoes_vendedor', ''),
                req.get('comprador_responsavel', ''),
                req.get('data_hora_resposta', ''),
                req.get('justificativa_recusa', ''),
                req.get('observacao_geral', '')
            ))
        
        # Atualiza o arquivo de controle do último número
        with open('ultimo_numero.json', 'w') as f:
            json.dump({'numero': ultimo_numero_atual}, f)
            
        conn.commit()
        conn.close()
        
        # Recarrega dados na sessão
        st.session_state.requisicoes = carregar_requisicoes()
        st.success("Backup restaurado com sucesso!")
        return True
        
    except Exception as e:
        st.error(f"Erro ao restaurar backup: {str(e)}")
        # Restaura backup preventivo em caso de erro
        if os.path.exists(f'backups/pre_restore_{timestamp}.db'):
            shutil.copy2(f'backups/pre_restore_{timestamp}.db', 'database/requisicoes.db')
        return False

def salvar_requisicao(requisicao):
    conn = sqlite3.connect('database/requisicoes.db')
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
        # Conecta ao banco de dados
        conn = sqlite3.connect('database/requisicoes.db')
        cursor = conn.cursor()
        
        # Busca o maior número de requisição atual
        cursor.execute('SELECT MAX(CAST(numero AS INTEGER)) FROM requisicoes')
        ultimo_numero = cursor.fetchone()[0]
        
        # Se não houver registros, começa do 5000
        if not ultimo_numero:
            proximo_numero = 5000
        else:
            proximo_numero = int(ultimo_numero) + 1
            
        # Atualiza o arquivo de controle
        with open('ultimo_numero.json', 'w') as f:
            json.dump({'numero': proximo_numero}, f)
            
        conn.close()
        return proximo_numero
        
    except Exception as e:
        st.error(f"Erro ao gerar número da requisição: {str(e)}")
        return None

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
    verificar_diretorios()
    if not os.path.exists('ultimo_numero.json'):
        inicializar_numero_requisicao()
    if 'requisicoes' not in st.session_state:
        importar_dados_antigos()
        st.session_state.requisicoes = carregar_requisicoes()

# Adicionar aqui a inicialização dos perfis
if 'perfis' not in st.session_state:
    try:
        with open('perfis.json', 'r') as f:
            st.session_state.perfis = json.load(f)
    except FileNotFoundError:
        st.session_state.perfis = {
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
    usuario = st.text_input("Usuário", key="usuario_input").upper()
    
    if usuario:
        if usuario in st.session_state.usuarios:
            user_data = st.session_state.usuarios[usuario]
            
            if user_data.get('senha') is None or user_data.get('primeiro_acesso', True):
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
                            
                        st.session_state.usuarios[usuario]['senha'] = gerar_hash_senha(nova_senha)
                        st.session_state.usuarios[usuario]['primeiro_acesso'] = False
                        st.session_state.usuarios[usuario]['data_ultimo_acesso'] = get_data_hora_brasil()
                        if salvar_usuarios():
                            st.success("Senha cadastrada com sucesso!")
                            time.sleep(1)
                            st.rerun()

            else:
                senha = st.text_input("Senha", type="password", key="senha_input")
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    if st.button("Entrar", use_container_width=True, type="primary"):
                        if not user_data.get('ativo', True):
                            st.error("USUÁRIO INATIVO - CONTATE O ADMINISTRADOR")
                            return
                        
                        senha_digitada_hash = gerar_hash_senha(senha)
                        senha_armazenada = user_data['senha']
                        
                        # Se a senha armazenada não for hash, compara diretamente
                        if len(senha_armazenada) != 64:  # Tamanho do hash SHA-256
                            if senha != senha_armazenada:
                                st.error("Senha incorreta")
                                return
                            # Atualiza para o formato hash
                            st.session_state.usuarios[usuario]['senha'] = senha_digitada_hash
                            salvar_usuarios()
                        else:
                            # Compara os hashes
                            if senha_digitada_hash != senha_armazenada:
                                st.error("Senha incorreta")
                                return
                            
                        st.session_state['usuario'] = usuario
                        st.session_state['perfil'] = user_data['perfil']
                        st.session_state.usuarios[usuario]['data_ultimo_acesso'] = get_data_hora_brasil()
                        salvar_usuarios()
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
    if 'requisicoes' not in st.session_state:
        st.session_state.requisicoes = carregar_requisicoes()
    
    # Definição dos ícones e cores dos status com transparência
    status_config = {
        'ABERTA': {'icon': '🗒️', 'cor': 'rgba(46, 204, 113, 0.7)'},  # Verde
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
        with open('configuracoes.json', 'w') as f:
            json.dump(st.session_state.config_sistema, f)
    except Exception as e:
        st.error(f"Erro ao salvar configurações: {e}")

def requisicoes():
    st.title("REQUISIÇÕES")
    
    # Configurações de cores mais saturadas
    status_config = {
        'ABERTA': {'icon': '🗒️', 'color': 'rgba(46, 204, 113, 0.3)', 'border': '#2ecc71'},
        'EM ANDAMENTO': {'icon': '⏳', 'color': 'rgba(241, 196, 15, 0.3)', 'border': '#f39c12'},
        'FINALIZADA': {'icon': '✅', 'color': 'rgba(52, 152, 219, 0.3)', 'border': '#3498db'},
        'RECUSADA': {'icon': '❌', 'color': 'rgba(231, 76, 60, 0.3)', 'border': '#e74c3c'}
    }

    # Atualização automática
    if 'ultima_atualizacao' not in st.session_state:
        st.session_state.ultima_atualizacao = time.time()
    
    if time.time() - st.session_state.ultima_atualizacao > 60:
        st.session_state.requisicoes = carregar_requisicoes()
        st.session_state.ultima_atualizacao = time.time()
        st.rerun()

    # Inicializar paginação
    if 'pagina_atual' not in st.session_state:
        st.session_state.pagina_atual = 1
    if 'itens_por_pagina' not in st.session_state:
        st.session_state.itens_por_pagina = 10

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
            background-color: #fff9c4;
            color: #000000;
            padding: 4px;
            border-radius: 8px;
            margin-bottom: 4px;
            border-left: 4px solid;
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
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }
        .status-aberta { background-color: #e3f2fd; color: #1976d2; }
        .status-andamento { background-color: #fff3e0; color: #f57c00; }
        .status-finalizada { background-color: #e8f5e9; color: #2e7d32; }
        .status-recusada { background-color: #ffebee; color: #c62828; }
        .requisicao-info {
            color: #000000;
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
        .paginacao-container {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 15px;
            margin-top: 20px;
            padding: 12px;
            background-color: #f8f9fa;
            border-radius: 8px;
        }
        .item-resposta {
            background-color: #f0f8ff;
            padding: 10px;
            border-radius: 4px;
            margin: 5px 0;
        }
        .resposta-grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 10px;
            margin-bottom: 10px;
        }
        .justificativa-box {
            background-color: #ffebee;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
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
                produto_busca = st.text_input("📦 PRODUTO", key="busca_produto")
            with col4:
                st.markdown("<br>", unsafe_allow_html=True)
                buscar = st.button("🔎 BUSCAR", type="primary", use_container_width=True)

            # Segunda linha de filtros
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            with col1:
                status_opcoes = {
                    "ABERTA": "🗒️ ABERTA",
                    "EM ANDAMENTO": "⏳ EM ANDAMENTO",
                    "FINALIZADA": "✅ FINALIZADA",
                    "RECUSADA": "❌ RECUSADA"
                }
                selected_status = st.multiselect(
                    "STATUS",
                    options=list(status_opcoes.keys()),
                    default=["ABERTA", "EM ANDAMENTO"] if st.session_state['perfil'] != 'vendedor' else list(status_opcoes.keys()),
                    format_func=lambda x: status_opcoes[x]
                )
            with col2:
                data_inicial = st.date_input("📅 DE", value=None, key="data_inicial")
            with col3:
                data_final = st.date_input("📅 ATÉ", value=None, key="data_final")
            with col4:
                if st.button("🔄 LIMPAR", type="secondary", use_container_width=True):
                    st.session_state.pagina_atual = 1
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)

        # Lógica de filtragem e exibição
        requisicoes_visiveis = []
        if st.session_state['perfil'] == 'vendedor':
            requisicoes_visiveis = [r for r in st.session_state.requisicoes if r['vendedor'] == st.session_state['usuario']]
            st.info(f"Visualizando requisições do vendedor: {st.session_state['usuario']}")
        else:
            requisicoes_visiveis = st.session_state.requisicoes

        # Aplicar filtros
        if numero_busca:
            requisicoes_visiveis = [r for r in requisicoes_visiveis if str(numero_busca) in str(r['numero'])]
        if cliente_busca:
            requisicoes_visiveis = [r for r in requisicoes_visiveis if cliente_busca.upper() in r['cliente'].upper()]
        if produto_busca:
            requisicoes_visiveis = [r for r in requisicoes_visiveis 
                                  if any(produto_busca.upper() in item.get('descricao', '').upper() 
                                        or produto_busca.upper() in item.get('codigo', '').upper()
                                        for item in r['items'])]
        if data_inicial and data_final:
            data_inicial_str = data_inicial.strftime('%d/%m/%Y')
            data_final_str = data_final.strftime('%d/%m/%Y')
            requisicoes_visiveis = [r for r in requisicoes_visiveis if data_inicial_str <= r['data_hora'].split()[0] <= data_final_str]

        # Filtro de status
        requisicoes_visiveis = [r for r in requisicoes_visiveis if r['status'] in selected_status]

        # Ordenação por número em ordem decrescente
        requisicoes_visiveis.sort(key=lambda x: x['numero'], reverse=True)

        # Paginação
        total_paginas = max(1, (len(requisicoes_visiveis) + st.session_state.itens_por_pagina - 1) // st.session_state.itens_por_pagina)
        inicio = (st.session_state.pagina_atual - 1) * st.session_state.itens_por_pagina
        fim = min(inicio + st.session_state.itens_por_pagina, len(requisicoes_visiveis))
        requisicoes_paginadas = requisicoes_visiveis[inicio:fim]

        # Exibição das requisições paginadas
        for req in requisicoes_paginadas:
            with st.form(key=f"form_{req['numero']}"):  # Envolve cada requisição em um form
                status_info = status_config.get(req['status'], {})
                st.markdown(f"""
                    <div class="requisicao-card" style="border-left-color: {status_info.get('border', '#2D2C74')}; 
                                                      background-color: {status_info.get('color', 'white')}">
                        <div class="requisicao-info">
                            <div>
                                <span class="requisicao-numero">{req['numero']}</span>
                                <span class="requisicao-cliente">{req['cliente']}</span>
                            </div>
                            <div>
                                <span class="status-badge" style="background-color: {status_info.get('color', '#f8f9fa')}; 
                                                                  border: 1px solid {status_info.get('border', '#ddd')};">
                                    {status_info.get('icon', '')} {req['status']}
                                </span>
                            </div>
                        </div>
                        <div class="requisicao-data" style="display: flex; justify-content: space-between;">
                            <div>
                                <span>📅 {req['data_hora'].split()[0]}</span>
                                <span style="margin-left: 15px;">🕒 {req['data_hora'].split()[1]}</span>
                                <span style="margin-left: 15px;">👤 {req['vendedor']}</span>
                            </div>
                            <span>👥 {req.get('comprador_responsavel', '-')}</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                is_open = st.session_state.get(f'mostrar_detalhes_{req["numero"]}', False)
                if st.form_submit_button(
                    f"🔽 DETALHES" if is_open else f"▶️ DETALHES",
                    help="Clique para expandir/recolher"
                ):
                    st.session_state[f'mostrar_detalhes_{req["numero"]}'] = not is_open
                    st.rerun()

            if st.session_state.get(f'mostrar_detalhes_{req["numero"]}', False):
                with st.container():
                    st.markdown("""
                        <div class="detalhes-container">
                    """, unsafe_allow_html=True)

                    # Cabeçalho com informações e botão FINALIZAR
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"""
                            <div class="header-info">
                                <div class="header-group">
                                    <p><strong>CRIADO EM:</strong> {req['data_hora']}</p>
                                    <p><strong>VENDEDOR:</strong> {req['vendedor']}</p>
                                </div>
                                <div class="header-group">
                                    <p><strong>RESPONDIDO EM:</strong> {req.get('data_hora_resposta','-')}</p>
                                    <p><strong>COMPRADOR:</strong> {req.get('comprador_responsavel', '-')}</p>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        if req['status'] == 'EM ANDAMENTO' and st.session_state['perfil'].lower() in ['comprador', 'administrador']:
                            # Container com margem negativa para alinhar à direita
                            st.markdown("""
                                <div style="display: flex; justify-content: flex-end; margin-right: -20px;">
                            """, unsafe_allow_html=True)
                            if st.button("✅ FINALIZAR", 
                                      key=f"finalizar_{req['numero']}",
                                      help="Concluir esta requisição (não será mais editável)"):
                                req['status'] = 'FINALIZADA'
                                req['data_hora_finalizacao'] = get_data_hora_brasil()
                                if salvar_requisicao(req):
                                    st.success(f"Requisição {req['numero']} finalizada com sucesso!")
                                    st.rerun()
                            st.markdown("</div>", unsafe_allow_html=True)

                    # Exibir itens da requisição
                    if req.get('items'):
                        # Botões de aceitar ou recusar (somente para compradores/admins quando status for ABERTA)
                        if req['status'] == 'ABERTA' and st.session_state['perfil'].lower() in ['comprador', 'administrador']:
                            col1, col2 = st.columns([1, 1])
                            with col1:
                                if st.button("✅ ACEITAR", key=f"aceitar_{req['numero']}"):
                                    req['status'] = 'EM ANDAMENTO'
                                    req['comprador_responsavel'] = st.session_state['usuario']
                                    req['data_hora_aceite'] = get_data_hora_brasil()
                                    st.session_state[f'mostrar_responder_{req["numero"]}'] = True
                                    if salvar_requisicao(req):
                                        st.success(f"Requisição {req['numero']} aceita com sucesso!")
                                        st.rerun()
                            with col2:
                                if st.button("❌ RECUSAR", key=f"recusar_{req['numero']}"):
                                    st.session_state[f'mostrar_justificativa_{req["numero"]}'] = True

                        # Exibir tabela de itens
                        items_df = pd.DataFrame([{
                            'ITEM': i + 1,
                            'Código': item.get('codigo', '-'),
                            'Cód. Fabricante': item.get('cod_fabricante', '-'),
                            'Descrição': item.get('descricao', '-'),
                            'Marca': item.get('marca', '-'),
                            'QTD': item.get('quantidade', 0),
                            'R$ Venda Unit': f"R$ {item.get('custo_unit', 0) * (1 + item.get('markup', 0) / 100):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                            'R$ Total': f"R$ {item.get('custo_unit', 0) * (1 + item.get('markup', 0) / 100) * item.get('quantidade', 0):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                            'Prazo': item.get('prazo_entrega', '-'),
                        } for i, item in enumerate(req['items'])])

                        st.dataframe(
                            items_df,
                            use_container_width=True,
                            column_config={
                                "ITEM": st.column_config.TextColumn('ITEM', width='small'),
                                "Código": st.column_config.TextColumn('CÓDIGO', width='medium'),
                                "Cód. Fabricante": st.column_config.TextColumn('CÓD. FABRICANTE', width='medium'),
                                "Descrição": st.column_config.TextColumn('DESCRIÇÃO', width='large'),
                                "Marca": st.column_config.TextColumn('MARCA', width='small'),
                                "QTD": st.column_config.NumberColumn('QUANTIDADE', width='small'),
                                "R$ Venda Unit": st.column_config.TextColumn('R$ VENDA UNIT', width='medium'),
                                "R$ Total": st.column_config.TextColumn('R$ TOTAL', width='medium'),
                                "Prazo": st.column_config.TextColumn('PRAZO', width='medium')
                            }
                        )

                        # Exibir observações do vendedor se existirem
                        if req.get('observacoes_vendedor'):
                            st.markdown(f"""
                                <div style="margin-top: 0.5cm;"></div>
                                <div class="observacao-box">
                                    <strong>Observações do Vendedor:</strong><br>
                                    {req['observacoes_vendedor']}
                                </div>
                            """, unsafe_allow_html=True)
                        
                        # Exibir observações do comprador se existirem
                        observacoes_comprador = [f"<b>Item {i+1}:</b> {item.get('observacoes', '')}" 
                                               for i, item in enumerate(req['items']) if item.get('observacoes')]
                        if observacoes_comprador:
                            st.markdown(f"""
                                <div style="margin-top: 0.5cm;"></div>
                                <div class="observacao-box" style="background-color: #f0f8ff;">
                                    <strong>Observações do Comprador:</strong><br>
                                    {"<br>".join(observacoes_comprador)}
                                </div>
                            """, unsafe_allow_html=True)
                        
                        st.markdown("""<div style="margin-bottom: 1cm;"></div>""", unsafe_allow_html=True)

                    # Campos para responder itens (aparece ao aceitar ou em andamento)
                    if req["status"] == "EM ANDAMENTO":
                        for i, item in enumerate(req["items"]):
                            with st.expander(f"ITEM {i + 1}: {item['descricao']}"):
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    custo_input = st.text_input("R$ UNIT", value=f"{item.get('custo_unit', 0):,.2f}".replace('.', ','), key=f"custo_unit_{req['numero']}_{i}")
                                    try:
                                        item["custo_unit"] = float(custo_input.replace('.', '').replace(',', '.'))
                                    except ValueError:
                                        pass
                                with col2:
                                    markup_input = st.number_input("% MARKUP", value=int(item.get("markup", 0)), step=1, format="%d", key=f"markup_{req['numero']}_{i}")
                                    item["markup"] = markup_input
                                with col3:
                                    item["prazo_entrega"] = st.text_input("PRAZO", value=item.get("prazo_entrega", ""), key=f"prazo_{req['numero']}_{i}")

                                incluir_obs = st.checkbox("INCLUIR OBSERVAÇÕES", key=f"incluir_obs_{req['numero']}_{i}")
                                if incluir_obs:
                                    item["observacoes"] = st.text_area("Observações do Comprador", value=item.get("observacoes", ""), key=f"obs_{req['numero']}_{i}")

                                if st.button(f"SALVAR ITEM {i + 1}", key=f"salvar_item_{req['numero']}_{i}"):
                                    salvar_requisicao(req)
                                    st.success(f"Item {i + 1} salvo com sucesso!")

                    # Campo de justificativa para recusa
                    if st.session_state.get(f'mostrar_justificativa_{req["numero"]}', False):
                        justificativa = st.text_area(
                            "Digite o motivo da recusa",
                            key=f"justificativa_recusa_{req['numero']}"
                        )
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(f"CONFIRMAR RECUSA {req['numero']}", key=f"confirmar_recusa_{req['numero']}"):
                                if not justificativa.strip():
                                    st.error("Por favor, informe o motivo da recusa.")
                                else:
                                    req['status'] = 'RECUSADA'
                                    req['justificativa_recusa'] = justificativa
                                    req['comprador_responsavel'] = st.session_state['usuario']
                                    req['data_hora_resposta'] = get_data_hora_brasil()
                                    if salvar_requisicao(req):
                                        st.success(f"Requisição {req['numero']} recusada com sucesso!")
                                        st.rerun()
                
                        with col2:
                            if st.button("CANCELAR", key=f"cancelar_recusa_{req['numero']}"):
                                st.session_state.pop(f'mostrar_justificativa_{req["numero"]}')
                                st.rerun()

        # Controles de paginação
        if len(requisicoes_visiveis) > 0:
            with st.container():
                st.markdown('<div class="paginacao-container">', unsafe_allow_html=True)
                
                col1, col2, col3, col4, col5 = st.columns([1,1,2,1,1])
                
                with col1:
                    novo_valor = st.selectbox(
                        "Itens por página:",
                        [10, 25, 50],
                        index=[10, 25, 50].index(st.session_state.itens_por_pagina),
                        key="itens_por_pagina_select"
                    )
                    if novo_valor != st.session_state.itens_por_pagina:
                        st.session_state.itens_por_pagina = novo_valor
                        st.session_state.pagina_atual = 1
                        st.rerun()
                
                with col2:
                    if st.session_state.pagina_atual > 1:
                        if st.button("⏮️ Anterior", key="anterior"):
                            st.session_state.pagina_atual -= 1
                            st.rerun()
                
                with col3:
                    st.markdown(f"**📄 Página {st.session_state.pagina_atual} de {total_paginas}**", unsafe_allow_html=True)
                
                with col4:
                    if st.session_state.pagina_atual < total_paginas:
                        if st.button("Próximo ⏭️", key="proximo"):
                            st.session_state.pagina_atual += 1
                            st.rerun()
                
                with col5:
                    st.markdown(f"**📊 Total: {len(requisicoes_visiveis)} requisições**", unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.warning("NENHUMA REQUISIÇÃO ENCONTRADA COM OS FILTROS SELECIONADOS.")

def get_permissoes_perfil(perfil):
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
    return permissoes_padrao.get(perfil, permissoes_padrao['vendedor'])

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
        
        perfil_selecionado = st.selectbox("Selecione o perfil para editar", ['vendedor', 'comprador', 'administrador'])
        
        st.markdown("#### Permissões de Acesso")
        st.markdown("Defina as telas que este perfil poderá acessar:")
        
        col1, col2 = st.columns(2)
        
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
                    value=st.session_state.get('perfis', {}).get(perfil_selecionado, {}).get(tela, valor_padrao),
                    key=key
                )
        
        with col2:
            st.markdown("##### Permissões Administrativas")
            for permissao, icone in [
                ('editar_usuarios', '👥 Editar Usuários'),
                ('excluir_usuarios', '❌ Excluir Usuários'),
                ('editar_perfis', '🔑 Editar Perfis')
            ]:
                valor_padrao = True if perfil_selecionado == 'administrador' else False
                key = f"{perfil_selecionado}_{permissao}"
                permissoes[permissao] = st.toggle(
                    icone,
                    value=st.session_state.get('perfis', {}).get(perfil_selecionado, {}).get(permissao, valor_padrao),
                    key=key
                )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Salvar Permissões", type="primary", use_container_width=True):
                try:
                    if 'perfis' not in st.session_state:
                        st.session_state.perfis = {}
                    
                    st.session_state.perfis[perfil_selecionado] = permissoes
                    save_perfis_permissoes(perfil_selecionado, permissoes)
                    st.success(f"Permissões do perfil {perfil_selecionado} atualizadas com sucesso!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar permissões: {str(e)}")
            
    # Seção de Sistema
    if st.session_state.get('config_modo') == 'sistema':
        st.markdown("### Configurações do Sistema")
        
        if st.session_state['perfil'] == 'administrador':
            tab1, tab2 = st.tabs(["📊 Monitoramento", "⚙️ Personalizar"])
            
            with tab1:
                st.markdown("#### Monitoramento do Sistema")
                
                # Configuração de Backups Automáticos
                st.markdown("##### Configuração de Backups Automáticos")
                config_backup = carregar_config_backup()
                
                col1, col2 = st.columns(2)
                with col1:
                    frequencia = st.selectbox(
                        "Frequência do Backup",
                        ["diario", "horario", "personalizado"],
                        index=["diario", "horario", "personalizado"].index(config_backup['frequencia']),
                        format_func=lambda x: {
                            "diario": "Diário",
                            "horario": "Horário",
                            "personalizado": "Personalizado"
                        }[x]
                    )
                    
                    if frequencia == "diario":
                        hora = st.time_input("Hora do backup diário", value=datetime.strptime(config_backup['hora'], '%H:%M').time())
                        config_backup['hora'] = hora.strftime('%H:%M')
                    
                    elif frequencia == "horario":
                        intervalo = st.number_input("Intervalo em horas", min_value=1, max_value=24, value=config_backup['intervalo_horas'])
                        config_backup['intervalo_horas'] = intervalo
                    
                    elif frequencia == "personalizado":
                        dias_semana = st.multiselect(
                            "Dias da semana",
                            options=["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"],
                            default=[["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"][i] for i in config_backup['dias_semana']]
                        )
                        config_backup['dias_semana'] = [["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"].index(d) for d in dias_semana]
                        hora = st.time_input("Hora do backup", value=datetime.strptime(config_backup['hora'], '%H:%M').time())
                        config_backup['hora'] = hora.strftime('%H:%M')
                
                with col2:
                    enviar_email = st.checkbox("Enviar backup por email", value=config_backup['enviar_email'])
                    config_backup['enviar_email'] = enviar_email
                    
                    email_destino = st.text_input("Email destino", value=config_backup['email_destino'])
                    config_backup['email_destino'] = email_destino
                    
                    if st.button("💾 Salvar Configurações", type="primary"):
                        config_backup['frequencia'] = frequencia
                        salvar_config_backup(config_backup)
                        st.success("Configurações de backup salvas com sucesso!")
                    
                    if config_backup.get('ultimo_backup'):
                        st.markdown(f"**Último backup:** {config_backup['ultimo_backup']}")
                    else:
                        st.markdown("**Nenhum backup automático realizado ainda**")
                    
                    if st.button("🔄 Executar Backup Agora", type="secondary"):
                        backup_automatico()
                        st.success("Backup executado com sucesso!")
                        st.rerun()
                
                # Banco de Dados e Importação (mantido igual)
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("##### Banco de Dados")
                    try:
                        conn = sqlite3.connect('database/requisicoes.db')
                        cursor = conn.cursor()
                        cursor.execute("SELECT COUNT(*) FROM requisicoes")
                        total_requisicoes = cursor.fetchone()[0]
                        
                        db_size = os.path.getsize('database/requisicoes.db') / (1024 * 1024)
                        
                        st.metric("Total de Requisições", total_requisicoes)
                        st.metric("Tamanho do Banco", f"{db_size:.2f} MB")
                        conn.close()
                    except Exception as e:
                        st.error("Erro ao acessar banco de dados")
                
                with col2:
                    st.markdown("##### Importação de Backup")
                    uploaded_file = st.file_uploader(
                        "Selecione o arquivo de backup",
                        type=['json', 'txt', 'py'],
                        help="Arquivos suportados: JSON, TXT, PY"
                    )
                    
                    if uploaded_file is not None:
                        if st.button("📥 Restaurar Backup", type="primary"):
                            try:
                                # Backup preventivo
                                if os.path.exists('database/requisicoes.db'):
                                    shutil.copy2('database/requisicoes.db', 'backups/pre_restore.db')
                                
                                # Processar arquivo baseado na extensão
                                if uploaded_file.name.endswith('.json'):
                                    dados = json.loads(uploaded_file.getvalue().decode('utf-8'))
                                elif uploaded_file.name.endswith('.txt'):
                                    dados = pd.read_csv(uploaded_file, sep='\t').to_dict('records')
                                elif uploaded_file.name.endswith('.py'):
                                    conteudo = uploaded_file.getvalue().decode('utf-8')
                                    dados_str = conteudo.replace('dados = ', '')
                                    dados = eval(dados_str)
                                
                                # Conectar e inserir dados
                                conn = sqlite3.connect('database/requisicoes.db')
                                cursor = conn.cursor()
                                
                                for req in dados:
                                    cursor.execute('''
                                        INSERT OR REPLACE INTO requisicoes 
                                        (numero, cliente, vendedor, data_hora, status, items, 
                                        observacoes_vendedor, comprador_responsavel, data_hora_resposta,
                                        justificativa_recusa, observacao_geral)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    ''', (
                                        str(req['numero']),
                                        req['cliente'],
                                        req['vendedor'],
                                        req['data_hora'],
                                        req['status'],
                                        req['items'] if isinstance(req['items'], str) else json.dumps(req['items']),
                                        req.get('observacoes_vendedor', ''),
                                        req.get('comprador_responsavel', ''),
                                        req.get('data_hora_resposta', ''),
                                        req.get('justificativa_recusa', ''),
                                        req.get('observacao_geral', '')
                                    ))
                                
                                conn.commit()
                                conn.close()
                                st.success(f"Backup restaurado com sucesso! {len(dados)} requisições importadas.")
                                st.rerun()
                                
                            except Exception as e:
                                st.error(f"Erro na restauração: {str(e)}")
                                if os.path.exists('backups/pre_restore.db'):
                                    shutil.copy2('backups/pre_restore.db', 'database/requisicoes.db')
                
                # Visualização de Dados e Backup Manual (mantido igual)
                st.markdown("#### Visualização de Dados")
                if st.button("🔍 Visualizar Dados do Banco", type="primary"):
                    try:
                        conn = sqlite3.connect('database/requisicoes.db')
                        df = pd.read_sql_query("SELECT * FROM requisicoes", conn)
                        st.dataframe(df)
                        conn.close()
                    except Exception as e:
                        st.error("Erro ao visualizar dados")
                
                if st.button("💾 Backup Manual", type="primary"):
                    try:
                        backup_dir = "backups"
                        if not os.path.exists(backup_dir):
                            os.makedirs(backup_dir)
                        
                        sp_tz = pytz.timezone('America/Sao_Paulo')
                        timestamp = datetime.now(sp_tz).strftime("%d%m%Y_%H%M%S")
                        
                        conn = sqlite3.connect('database/requisicoes.db')
                        df = pd.read_sql_query("SELECT * FROM requisicoes", conn)
                        
                        backup_filename = f'backup_manual_{timestamp}.json'
                        with open(f'{backup_dir}/{backup_filename}', 'w', encoding='utf-8') as f:
                            json.dump(df.to_dict('records'), f, ensure_ascii=False, indent=2)
                        
                        conn.close()
                        st.success("Backup realizado com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao criar backup: {str(e)}")
                
                # Lista de Backups (mantido igual)
                st.markdown("#### Backups Disponíveis")
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
                                'data_criacao': creation_datetime
                            })
                        
                        backup_info.sort(key=lambda x: x['data_criacao'], reverse=True)
                        
                        for backup in backup_info:
                            col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 1, 1])
                            
                            with col1:
                                st.text(backup['arquivo'])
                            
                            with col2:
                                st.text(backup['data_criacao'].strftime('%d/%m/%Y %H:%M:%S'))
                            
                            with col3:
                                tipo = 'AUTOMÁTICO' if 'auto' in backup['arquivo'].lower() else 'MANUAL'
                                st.text(tipo)
                            
                            with col4:
                                if backup['tamanho'] < 1024:
                                    tamanho_fmt = f"{backup['tamanho']} B"
                                elif backup['tamanho'] < 1024**2:
                                    tamanho_fmt = f"{backup['tamanho']/1024:.1f} KB"
                                else:
                                    tamanho_fmt = f"{backup['tamanho']/1024**2:.1f} MB"
                                st.text(tamanho_fmt)
                            
                            with col5:
                                col5_1, col5_2 = st.columns(2)
                                with col5_1:
                                    with open(backup['caminho'], "rb") as f:
                                        bytes_data = f.read()
                                        st.download_button(
                                            label="⬇️",
                                            data=bytes_data,
                                            file_name=backup['arquivo'],
                                            mime="application/octet-stream",
                                            key=f"download_{backup['arquivo']}"
                                        )
                                with col5_2:
                                    if st.button("🗑️", key=f"delete_{backup['arquivo']}"):
                                        try:
                                            os.remove(backup['caminho'])
                                            st.success("Backup removido com sucesso!")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Erro ao remover backup: {str(e)}")
                    else:
                        st.info("Nenhum arquivo de backup encontrado.")
                else:
                    st.warning("Diretório de backup não encontrado.")
                    
def main():
    # Inicializar o banco de dados
    inicializar_banco()
    
    # Carregar configurações de backup
    carregar_config_backup()
    
    # Adiciona atualização automática a cada 1 minuto para verificar backups
    st_autorefresh(interval=60000, key="backup_refresh")
    
    # Verificar se precisa fazer backup automático
    verificar_backup_automatico()
    
    if 'usuario' not in st.session_state:
        tela_login()
    else:
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
