import streamlit as st
import firebase_admin
from firebase_admin import credentials, initialize_app, db
import hashlib
import pandas as pd
import time
import zipfile
import matplotlib.pyplot as plt
import gzip
import tarfile
import logging
from datetime import datetime, timedelta
import pytz
import json
import os
import smtplib
import locale
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import plotly.graph_objects as go
import shutil
import glob
from streamlit_autorefresh import st_autorefresh

def inicializar_firebase():
    if not firebase_admin._apps:
        try:
            # Carregar credenciais do secrets
            firebase_credentials = json.loads(st.secrets["FIREBASE_CREDENTIALS"])
            cred = credentials.Certificate(firebase_credentials)
            initialize_app(cred, {
                'databaseURL': 'https://portal-26466-default-rtdb.firebaseio.com'
            })
            st.success("Firebase inicializado com sucesso!")
        except Exception as e:
            st.error(f"Erro ao inicializar Firebase: {str(e)}")
            return False
    return True

if not inicializar_firebase():
    st.stop()

def verificar_conexao():
    try:
        ref = db.reference('.info/connected')
        return ref.get() is True
    except BaseException:
        return False

def processar_arquivo_requisicoes(uploaded_file):
    try:
        dados = json.loads(uploaded_file.getvalue().decode('utf-8'))
        ref_requisicoes = db.reference('requisicoes')
        ultimo_numero = max(int(req['numero']) for req in dados.values())

        for numero, req in dados.items():
            ref_requisicoes.child(numero).set(req)

        # Atualizar o último número de requisição
        db.reference('ultimo_numero').set(ultimo_numero)

        st.success(f"{len(dados)} requisições importadas com sucesso!")
        return True
    except Exception as e:
        st.error(f"Erro ao processar arquivo: {str(e)}")
        return False
    
def formatar_moeda(valor):
    """Formata um número no padrão brasileiro (R$ 1.000,00)."""
    return f"{valor:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')

def converter_para_float(valor_str):
    """Converte uma string no formato brasileiro para float."""
    try:
        return float(valor_str.replace('.', '').replace(',', '.'))
    except ValueError:
        return None

def calcular_totais():
    try:
        ref_requisicoes = db.reference('requisicoes')
        requisicoes = ref_requisicoes.get()
        totais = {
            "abertas": 0,
            "em_andamento": 0,
            "finalizadas": 0,
            "recusadas": 0
        }
        if requisicoes:
            for req in requisicoes.values():
                status = req.get("status", "").upper()
                if status == "ABERTA":
                    totais["abertas"] += 1
                elif status == "EM ANDAMENTO":
                    totais["em_andamento"] += 1
                elif status == "FINALIZADA":
                    totais["finalizadas"] += 1
                elif status == "RECUSADA":
                    totais["recusadas"] += 1
        return totais
    except Exception as e:
        st.error(f"Erro ao calcular totais: {str(e)}")
        return {}

def gerar_hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()  # Mantido igual

def inicializar_banco_usuarios():
    try:
        ref = db.reference('usuarios')
        usuarios = ref.get()

        # Cria usuário administrador personalizado (Zaqueu Souza)
        if not usuarios or 'ZAQUEU SOUZA' not in usuarios:
            admin_data = {
                'nome': 'ZAQUEU SOUZA',
                'email': 'Importacao@jetfrio.com.br',
                # Hash da senha fornecida
                'senha': gerar_hash_senha('Za@031162'),
                'perfil': 'administrador',
                'ativo': True,
                'primeiro_acesso': False,
                'token_sessao': None,
                'data_ultimo_acesso': None,
                'data_criacao': datetime.now(pytz.timezone('America/Sao_Paulo')).isoformat(),
                'data_modificacao': None
            }
            # ID 'zaqueu' para fácil identificação
            ref.child('ZAQUEU SOUZA').set(admin_data)

    except Exception as e:
        st.error(f"Erro ao inicializar usuários: {str(e)}")

def inicializar_sistema():
    try:
        # Mantido para compatibilidade com backups locais
        os.makedirs('backups', exist_ok=True)

        # Inicializações do Firebase
        inicializar_banco_usuarios()
        inicializar_banco()

        return True
    except Exception as e:
        st.error(f"Falha crítica na inicialização: {str(e)}")
        return False

def migrar_usuarios_json_para_firebase():  # Nome alterado
    try:
        with open('usuarios.json', 'r', encoding='utf-8') as f:
            usuarios_json = json.load(f)

        ref = db.reference('usuarios')  # Conexão Firebase

        for usuario_id, dados in usuarios_json.items():
            # Mantém todos os campos originais
            ref.child(usuario_id).set({
                'nome': dados['nome'],
                'email': dados['email'],
                'senha': dados['senha'],
                'perfil': dados['perfil'],
                'ativo': dados['ativo'],
                'primeiro_acesso': dados.get('primeiro_acesso', True),
                'data_criacao': dados.get('data_criacao', datetime.now(pytz.timezone('America/Sao_Paulo')).isoformat())
            })

        return True
    except Exception as e:
        st.error(f"Erro na migração: {str(e)}")  # Melhor tratamento de erro
        return False

def inicializar_banco():
    try:
        # Firebase não precisa criar tabelas, apenas verifica/incializa a
        # referência
        ref = db.reference('requisicoes')
        if not ref.get():
            ref.set({'ultimo_numero': 0})  # Inicializa se necessário
    except Exception as e:
        st.error(f"Falha crítica ao iniciar banco: {str(e)}")

def mostrar_espaco_armazenamento():
    import plotly.graph_objects as go

    try:
        # Simulação dos valores (substitua pelos dados reais do Firebase Storage)
        espaco_usado_mb = 1200  # Espaço usado em MB
        espaco_total_mb = 5120  # Espaço total em MB (exemplo: plano gratuito)

        espaco_disponivel_mb = espaco_total_mb - espaco_usado_mb

        fig = go.Figure(data=[go.Pie(
            labels=['Disponível', 'Usado'],
            values=[espaco_disponivel_mb, espaco_usado_mb],
            hole=.6,
            marker_colors=['#66b3ff', '#ff9999'],
            textinfo='label+percent',
        )])

        fig.update_layout(
            title=dict(
                text="Armazenamento do Firebase",
                font=dict(size=16),
                x=0.5
            ),
            annotations=[dict(
                text=f"{espaco_usado_mb:.1f}MB usados",
                x=0.5,
                y=0.5,
                font_size=12,
                showarrow=False
            )],
        )

        return fig

    except Exception as e:
        raise Exception(f"Erro ao gerar gráfico: {str(e)}")

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
        msg['Subject'] = f"SUA REQUISIÇÃO Nº{
            requisicao['numero']} FOI {
            tipo_notificacao.upper()}"

        # Define destinatários
        vendedor_email = st.session_state.usuarios[requisicao['vendedor']]['email']
        comprador_email = st.session_state.usuarios.get(
            requisicao.get(
                'comprador_responsavel', ''), {}).get(
            'email', '')

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

def save_perfis_permissoes(perfil, permissoes):
    try:
        # Referência para o nó 'perfis' no Firebase
        ref = db.reference('perfis')

        # Salva ou atualiza as permissões do perfil no Firebase
        ref.child(perfil).set(permissoes)

        return True
    except Exception as e:
        st.error(f"Erro ao salvar permissões: {str(e)}")
        return False

def verificar_diretorios():
    # Não é mais necessário verificar diretórios locais para o banco de dados
    # Mas mantemos a verificação para backups
    diretorios = ['backups']  # Apenas para backups locais
    for dir in diretorios:
        if not os.path.exists(dir):
            os.makedirs(dir)
    return True

def importar_dados_antigos():
    # Define timestamp no início da função
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    try:
        # Referência para o nó de requisições no Firebase
        ref_requisicoes = db.reference('requisicoes')

        # Obter o último número de requisição
        ultimo_numero_ref = db.reference('ultimo_numero')
        # Se não existir, começa em 4999
        ultimo_numero_atual = ultimo_numero_ref.get() or 4999

        # Carregar dados do JSON
        with open('requisicoes.json', 'r', encoding='utf-8') as file:
            requisicoes_antigas = json.load(file)

        # Backup preventivo (opcional, mas mantido para segurança)
        backup_ref = db.reference('backups').child(f'pre_import_{timestamp}')
        # Salva o estado atual das requisições no Firebase
        backup_ref.set(ref_requisicoes.get())

        # Inserir dados formatados no Firebase
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

            nova_requisicao = {
                'numero': req.get('REQUISIÇÃO'),
                'cliente': req.get('CLIENTE'),
                'vendedor': req.get('VENDEDOR'),
                'data_hora': req.get('Data/Hora Criação:'),
                'status': req.get('STATUS'),
                'items': items,
                'observacoes_vendedor': '',
                'comprador_responsavel': req.get('COMPRADOR', ''),
                'data_hora_resposta': req.get('Data/Hora Resposta:'),
                'justificativa_recusa': '',
                'observacao_geral': req.get('OBSERVAÇÕES DO COMPRADOR', '')
            }

            ref_requisicoes.child(
                str(req.get('REQUISIÇÃO'))).set(nova_requisicao)

        # Atualizar último número no Firebase
        ultimo_numero_ref.set(ultimo_numero_atual)

        return True
    except Exception as e:
        st.error(f"Erro na importação: {str(e)}")
        return False

def verificar_arquivos():
    try:
        os.makedirs('backup', exist_ok=True)
        return True
    except Exception as e:
        st.error(f"Erro ao verificar diretórios: {str(e)}")
        return False

def carregar_usuarios():
    try:
        ref = db.reference('usuarios')
        usuarios = ref.get()
        if not usuarios:
            usuario_padrao = {
                'ZAQUEU SOUZA': {
                    'senha': gerar_hash_senha('Za@031162'),
                    'perfil': 'administrador',
                    'email': 'Importacao@jetfrio.com.br',
                    'ativo': True,
                    'primeiro_acesso': False
                }
            }
            ref.set(usuario_padrao)
            return usuario_padrao
        return usuarios
    except Exception as e:
        st.error(f"Erro ao carregar usuários: {str(e)}")
        return {}

def salvar_usuarios():
    try:
        ref = db.reference('usuarios')

        backup_ref = db.reference('backups/usuarios')
        backup_ref.set(ref.get())

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
        ref.set(usuarios_para_salvar)

        return True
    except Exception as e:
        st.error(f"Erro ao salvar usuários: {str(e)}")
        return False

def migrar_dados_json_para_firebase():
    try:
        with open('requisicoes.json', 'r', encoding='utf-8') as f:
            requisicoes_json = json.load(f)

        ref = db.reference('requisicoes')

        for req in requisicoes_json:
            # Converter para estrutura do Firebase
            nova_requisicao = {
                'numero': req['REQUISIÇÃO'],
                'cliente': req['CLIENTE'],
                'vendedor': req['VENDEDOR'],
                'data_hora': req['Data/Hora Criação:'],
                'status': req['STATUS'],
                'items': [{
                    'codigo': req['CÓDIGO'],
                    'descricao': req['DESCRIÇÃO'],
                    'marca': req['MARCA'],
                    'quantidade': float(req['QUANTIDADE']),
                    'venda_unit': float(req[' R$ UNIT '].replace('R$ ', '').replace(',', '.').strip()),
                    'prazo_entrega': req['PRAZO']
                }],
                'observacoes_vendedor': '',
                'comprador_responsavel': req['COMPRADOR'],
                'data_hora_resposta': req['Data/Hora Resposta:'],
                'justificativa_recusa': '',
                'observacao_geral': req['OBSERVAÇÕES DO COMPRADOR']
            }

            # Salvar no Firebase usando o número como chave
            ref.child(str(req['REQUISIÇÃO'])).set(nova_requisicao)

        return True
    except Exception as e:
        st.error(f"Erro na migração: {str(e)}")
        return False

def carregar_requisicoes():
    try:
        ref_requisicoes = db.reference('requisicoes')
        requisicoes = ref_requisicoes.get()

        # Verificar se os dados são válidos
        if isinstance(requisicoes, dict):
            requisicoes_processadas = []
            for key, req in requisicoes.items():
                if isinstance(req, dict):
                    # Garantir que 'items' seja uma lista de dicionários
                    try:
                        req['items'] = json.loads(
                            req.get(
                                'items',
                                '[]')) if isinstance(
                            req.get('items'),
                            str) else req.get(
                'items',
                            [])
                    except json.JSONDecodeError:
                        req['items'] = []
                    requisicoes_processadas.append(req)
            return requisicoes_processadas
        else:
            st.error("Os dados das requisições não estão no formato esperado.")
            return []
    except Exception as e:
        st.error(f"Erro ao carregar requisições: {str(e)}")
        return []

def renumerar_requisicoes():
    try:
        ref = db.reference('requisicoes')
        todas_requisicoes = ref.get()

        if not todas_requisicoes:
            return False

        # Ordenar por data/hora
        requisicoes_ordenadas = sorted(
            todas_requisicoes.values(),
            key=lambda x: x['data_hora']
        )

        # Novo sistema de numeração
        novo_numero = 5092
        novas_requisicoes = {}

        for req in requisicoes_ordenadas:
            nova_chave = str(novo_numero)
            req['numero'] = nova_chave
            novas_requisicoes[nova_chave] = req
            novo_numero += 1

        # Atualizar Firebase
        ref.set(novas_requisicoes)
        return True

    except Exception as e:
        st.error(f"Falha na renumerção: {str(e)}")
        return False

def backup_requisicoes():
    try:
        # Referência ao nó 'requisicoes' no Firebase
        ref = db.reference('requisicoes')
        dados = ref.get()

        # Verifica se há dados antes de prosseguir
        if not dados or not isinstance(dados, dict):
            raise ValueError("Nenhuma requisição encontrada ou dados inválidos.")

        # Gera o timestamp para nomear o arquivo
        timestamp = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime("%Y%m%d_%H%M%S")
        backup_dir = 'backups'
        os.makedirs(backup_dir, exist_ok=True)
        backup_file = os.path.join(backup_dir, f'requisicoes_backup_{timestamp}.json')

        # Salva os dados em um arquivo JSON
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=4)

        # Retorna o caminho do arquivo gerado
        return backup_file

    except Exception as e:
        st.error(f"FALHA NO BACKUP: {str(e)}")
        return None

def verificar_integridade_db():
    try:
        # Verifica conexão e carrega dados básicos
        usuarios = db.reference('usuarios').get()
        requisicoes = db.reference('requisicoes').get()
        return bool(usuarios is not None and requisicoes is not None)
    except Exception as e:
        st.error(f"Falha na verificação de integridade: {str(e)}")
        return False

def verificar_conteudo_backup(arquivo_backup):
    try:
        # Abre e verifica o conteúdo do arquivo JSON
        with open(arquivo_backup, 'r', encoding='utf-8') as f:
            dados = json.load(f)

        # Verifica se os campos principais estão presentes
        if not isinstance(dados, dict) or not all(isinstance(req, dict) for req in dados.values()):
            raise ValueError("Estrutura de dados inválida no backup.")

        return True

    except Exception as e:
        st.error(f"Backup corrompido ou incompleto: {str(e)}")
        return False

def backup_automatico():
    try:
        timestamp = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime('%Y%m%d_%H%M%S')
        backup_dir = f'backups/firebase_backup_{timestamp}'
        os.makedirs(backup_dir, exist_ok=True)

        # Coletar dados do Firebase
        dados_backup = {
            'usuarios': db.reference('usuarios').get(),
            'requisicoes': db.reference('requisicoes').get(),
            'perfis': db.reference('perfis').get(),
            'ultimo_numero': db.reference('ultimo_numero').get()
        }

        # Salvar em arquivo JSON
        backup_file = os.path.join(backup_dir, f'backup_{timestamp}.json')
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(dados_backup, f, ensure_ascii=False, indent=4)

        # Comprimir usando a abordagem do arquivo antigo (mais confiável)
        with open(backup_file, 'rb') as f_in:
            with gzip.open(f'{backup_file}.gz', 'wb') as f_out:
                f_out.writelines(f_in)
        
        # Remover arquivo original não comprimido
        os.remove(backup_file)
        shutil.rmtree(backup_dir)  # Remove diretório temporário

        # Verificação de integridade
        if not verificar_conteudo_backup(f'{backup_file}.gz'):
            raise Exception("Backup corrompido ou incompleto")

        limpar_backups_antigos('backups')
        return f'{backup_file}.gz'

    except Exception as e:
        st.error(f"FALHA NO BACKUP: {str(e)}")
        # Limpeza em caso de erro
        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir)
        if os.path.exists(f'{backup_file}.gz'):
            os.remove(f'{backup_file}.gz')
        return None

def comprimir_backup(backup_dir):
    try:
        saida = f'{backup_dir}.tar.gz'
        with tarfile.open(saida, "w:gz") as tar:
            tar.add(backup_dir, arcname=os.path.basename(backup_dir))
        shutil.rmtree(backup_dir)  # Remove diretório original
        return saida
    except Exception as e:
        raise Exception(f"Falha na compressão: {str(e)}")

def limpar_backups_antigos(backup_dir, dias_manter=7):
    try:
        agora = datetime.now(pytz.timezone('America/Sao_Paulo'))
        limite = agora - timedelta(days=dias_manter)

        for item in os.listdir(backup_dir):
            if item.startswith('firebase_backup_') and item.endswith('.gz'):
                caminho = os.path.join(backup_dir, item)
                data_criacao = datetime.fromtimestamp(os.path.getctime(caminho))
                data_criacao = data_criacao.replace(tzinfo=pytz.timezone('America/Sao_Paulo'))
                
                if data_criacao < limite:
                    os.remove(caminho)
    except Exception as e:
        st.error(f"Erro na limpeza de backups: {str(e)}")

def listar_backups(backup_dir='backups/'):
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    backups = []
    for arquivo in os.listdir(backup_dir):
        if arquivo.startswith('requisicoes_backup_') and arquivo.endswith('.json'):
            caminho_arquivo = os.path.join(backup_dir, arquivo)
            tamanho = os.path.getsize(caminho_arquivo)
            data_criacao = datetime.fromtimestamp(os.path.getctime(caminho_arquivo))
            tamanho_fmt = f"{tamanho / 1024:.1f} KB"

            backups.append({
                'Data': data_criacao.strftime('%d/%m/%Y'),
                'Hora': data_criacao.strftime('%H:%M:%S'),
                'Tamanho': tamanho_fmt,
                'Arquivo': arquivo,
                'Caminho': caminho_arquivo
            })

    if backups:
        df = pd.DataFrame(backups)
        df = df.sort_values(by=['Data', 'Hora'], ascending=[False, False])

        for _, row in df.iterrows():
            col1, col2 = st.columns([1, 4])
            with col1:
                with open(row['Caminho'], 'rb') as file:
                    st.download_button(
                        "📥 Download",
                        file,
                        file_name=row['Arquivo'],
                        mime="application/json"
                    )
            with col2:
                if st.button("🗑️ Excluir", key=f"delete_{row['Arquivo']}"):
                    os.remove(row['Caminho'])
                    st.success(f"Backup {row['Arquivo']} removido com sucesso!")
                    st.rerun()
    else:
        st.info("Nenhum backup encontrado.")

def restaurar_backup(uploaded_file):
    try:
        # Carrega os dados do arquivo enviado pelo usuário
        dados_backup = json.loads(uploaded_file.getvalue().decode('utf-8'))

        if not isinstance(dados_backup, dict):
            raise ValueError("O arquivo de backup não contém um formato válido.")

        # Referência ao nó 'requisicoes' no Firebase
        ref_requisicoes = db.reference('requisicoes')
        
        # Substitui os dados existentes pelos novos
        ref_requisicoes.set(dados_backup)

        # Atualiza o último número de requisição
        ultimo_numero = max(int(req['numero']) for req in dados_backup.values())
        db.reference('ultimo_numero').set(ultimo_numero)

        st.success(f"Backup restaurado com sucesso! {len(dados_backup)} requisições importadas.")
    
    except Exception as e:
        st.error(f"Erro ao restaurar backup: {str(e)}")

def salvar_requisicao(requisicao):
    try:
        ref = db.reference(f'requisicoes/{requisicao["numero"]}')

        # Garante a estrutura completa dos dados
        dados_completos = {
            'numero': requisicao['numero'],
            'cliente': requisicao['cliente'],
            'vendedor': requisicao['vendedor'],
            'data_hora': requisicao['data_hora'],
            'status': requisicao['status'],
            'items': requisicao['items'],
            'observacoes_vendedor': requisicao.get('observacoes_vendedor', ''),
            'comprador_responsavel': requisicao.get('comprador_responsavel', ''),
            'data_hora_resposta': requisicao.get('data_hora_resposta', ''),
            'justificativa_recusa': requisicao.get('justificativa_recusa', ''),
            'observacao_geral': requisicao.get('observacao_geral', '')
        }

        ref.set(dados_completos)
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
        ref = db.reference('ultimo_numero')
        ultimo_numero = ref.get()
        if not ultimo_numero:
            ultimo_numero = 6148  # Começar do último número conhecido no backup
        proximo_numero = int(ultimo_numero) + 1
        ref.set(proximo_numero)
        return proximo_numero
    except Exception as e:
        st.error(f"Erro ao gerar número da requisição: {str(e)}")
        return None

def inicializar_numero_requisicao():
    ref = db.reference('ultimo_numero')
    if not ref.get():  # Se não existir no Firebase
        ref.set(4999)
    return ref.get()

# Inicialização de dados
if 'usuarios' not in st.session_state:
    st.session_state.usuarios = carregar_usuarios()
    verificar_diretorios()
    if 'requisicoes' not in st.session_state:
        st.session_state.requisicoes = carregar_requisicoes()
# Inicialização dos perfis
if 'perfis' not in st.session_state:
    ref_perfis = db.reference('perfis')
    perfis = ref_perfis.get()

    if not perfis:  # Cria perfis padrão se não existirem
        perfis_padrao = {
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
        ref_perfis.set(perfis_padrao)
        st.session_state.perfis = perfis_padrao
    else:
        st.session_state.perfis = perfis

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
        ref_usuarios = db.reference('usuarios')
        user_data = ref_usuarios.child(usuario).get()

        if user_data:
            if user_data.get('senha') is None or user_data.get(
                    'primeiro_acesso', True):
                st.markdown("### 😊 Primeiro Acesso - Configure sua senha")
                with st.form("primeiro_acesso_form"):
                    nova_senha = st.text_input("Nova Senha", type="password",
                                               help="Mínimo 8 caracteres, incluindo letra maiúscula, minúscula e número")
                    confirma_senha = st.text_input(
                        "Confirme a Nova Senha", type="password")

                    if st.form_submit_button("Cadastrar Senha"):
                        if len(nova_senha) < 8:
                            st.error("A senha deve ter no mínimo 8 caracteres")
                            return

                        if nova_senha != confirma_senha:
                            st.error("As senhas não coincidem")
                            return

                        user_data['senha'] = gerar_hash_senha(nova_senha)
                        user_data['primeiro_acesso'] = False
                        user_data['data_ultimo_acesso'] = get_data_hora_brasil()
                        ref_usuarios.child(usuario).update(user_data)
                        st.success("Senha cadastrada com sucesso!")
                        time.sleep(1)
                        st.rerun()

            else:
                senha = st.text_input(
                    "Senha", type="password", key="senha_input")
                col1, col2 = st.columns([1, 1])

                with col1:
                    if st.button("Entrar", use_container_width=True,
                                 type="primary"):
                        if not user_data.get('ativo', True):
                            st.error(
                                "USUÁRIO INATIVO - CONTATE O ADMINISTRADOR")
                            return

                        senha_digitada_hash = gerar_hash_senha(senha)
                        senha_armazenada = user_data['senha']

                        if senha_digitada_hash != senha_armazenada:
                            st.error("Senha incorreta")
                            return

                        st.session_state['usuario'] = usuario
                        st.session_state['perfil'] = user_data['perfil']
                        user_data['data_ultimo_acesso'] = get_data_hora_brasil()
                        ref_usuarios.child(usuario).update(user_data)
                        st.success(f"Bem-vindo, {usuario}!")
                        time.sleep(1)
                        st.rerun()
        else:
            st.error("Usuário não encontrado")

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
        perfil = st.session_state.get('perfil', '').lower()
        if perfil in ['administrador', 'comprador']:
            menu_items.insert(-1, "🛒 Cotações")
            menu_items.insert(-1, "✈️ Importação")

        menu = st.radio("", menu_items, label_visibility="collapsed")

        st.markdown(
            "<div style='flex-grow: 1;'></div>",
            unsafe_allow_html=True)

        st.markdown(
            f"""
            <div class="user-info">
                <p style='margin: 0; font-size: 0.9rem; white-space: nowrap;'>👤 <b>Usuário:</b> {st.session_state.get('usuario', '')}</p>
                <p style='margin: 0; font-size: 0.9rem;'>🔑 <b>Perfil:</b> {perfil.title()}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        with st.container():
            if st.button("🚪 Sair", key="logout_button",
                         use_container_width=False):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

        return menu.split(" ")[-1]

def dashboard():
    if not st.session_state.perfis.get(st.session_state['perfil'].lower(), {}).get('dashboard', True):
        st.warning("Você não tem permissão para acessar esta tela")
        return

    # Definição dos ícones e cores dos status com transparência
    status_config = {
        'ABERTA': {'icon': '📋', 'cor': 'rgba(46, 204, 113, 0.7)'},  # Verde
        # Amarelo
        'EM ANDAMENTO': {'icon': '⏳', 'cor': 'rgba(241, 196, 15, 0.7)'},
        'FINALIZADA': {'icon': '✅', 'cor': 'rgba(52, 152, 219, 0.7)'},  # Azul
        'RECUSADA': {'icon': '🚫', 'cor': 'rgba(231, 76, 60, 0.7)'},  # Vermelho
        'TOTAL': {'icon': '📉', 'cor': 'rgba(149, 165, 166, 0.7)'}  # Cinza
    }

    # Filtrar requisições baseado no perfil do usuário
    if st.session_state['perfil'] == 'vendedor':
        requisicoes_filtradas = [
            r for r in st.session_state.requisicoes if r['vendedor'] == st.session_state['usuario']]
        st.info(
            f"Visualizando requisições do vendedor: {
                st.session_state['usuario']}")
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
            status_counts = {
                'ABERTA': 0,
                'EM ANDAMENTO': 0,
                'FINALIZADA': 0,
                'RECUSADA': 0
            }

            for r in requisicoes_filtradas:
                status = r['status']
                if status in ['FINALIZADA', 'RESPONDIDA']:
                    status_counts['FINALIZADA'] += 1
                elif status in status_counts:
                    status_counts[status] += 1

            total = len(requisicoes_filtradas)

            for status, valor in status_counts.items():
                st.markdown(f"""
                    <div class="status-box" style="background-color: {status_config[status]['cor']};">
                        <span class="status-icon">{status_config[status]['icon']}</span>
                        <span class="status-text">{status}</span>
                        <span class="status-value">{valor}</span>
                    </div>
                """, unsafe_allow_html=True)

            # Adicionar o total
            st.markdown(f"""
                <div class="status-box" style="background-color: {status_config['TOTAL']['cor']};">
                    <span class="status-icon">{status_config['TOTAL']['icon']}</span>
                    <span class="status-text">TOTAL</span>
                    <span class="status-value">{total}</span>
                </div>
            """, unsafe_allow_html=True)

    # Coluna do gráfico
    with col_grafico:
        # Criar duas colunas dentro da coluna do gráfico
        col_vazia, col_filtro = st.columns([3, 1])

        # Coluna do filtro (direita)
        with col_filtro:
            st.markdown(
                '<div style="margin-top: 0px;">',
                unsafe_allow_html=True)
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
                dados_grafico = [
                    (status, valor, status_config[status]['cor'])
                    for status, valor in status_counts.items()
                    if valor > 0
                ]

                # Se não houver dados, incluir todos os status com valor 0
                if not dados_grafico:
                    dados_grafico = [
                        (status, 0, status_config[status]['cor'])
                        for status in status_counts.keys()
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
                st.error(
                    "Biblioteca Plotly não encontrada. Execute 'pip install plotly' para instalar.")

    # Tabela detalhada em toda a largura
    st.markdown("### Requisições Detalhadas")
    if requisicoes_filtradas:
        # Ordenar requisições por número em ordem decrescente
        requisicoes_filtradas = sorted(requisicoes_filtradas,
                                       key=lambda x: int(
                                           # Garante ordenação numérica correta
                                           x['numero']),
                                       reverse=True)

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
        col1, col2 = st.columns([4, 1])
        with col2:
            if st.button("🎯 NOVA REQUISIÇÃO", type="primary",
                         use_container_width=True):
                st.session_state['modo_requisicao'] = 'nova'
                if 'items_temp' not in st.session_state:
                    st.session_state.items_temp = []
                st.rerun()
        return

    st.title("NOVA REQUISIÇÃO")
    col1, col2 = st.columns([1.5, 1])
    with col1:
        cliente = st.text_input("CLIENTE", key="cliente").upper()
    with col2:
        st.write(f"**VENDEDOR:** {st.session_state.get('usuario', '')}")

    if st.session_state.get('show_qtd_error'):
        st.markdown(
            '<p style="color: #ff4b4b; margin: 0; padding: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">PREENCHIMENTO OBRIGATÓRIO: QUANTIDADE</p>',
            unsafe_allow_html=True)

    if 'items_temp' not in st.session_state:
        st.session_state.items_temp = []

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
                st.text_input(
                    "",
                    value=str(
                        item['item']),
                    disabled=True,
                    key=f"item_{idx}",
                    label_visibility="collapsed")
            with cols[1]:
                if editing:
                    item['codigo'] = st.text_input(
                        "",
                        value=item['codigo'],
                        key=f"codigo_edit_{idx}",
                        label_visibility="collapsed").upper()
                else:
                    st.text_input(
                        "",
                        value=item['codigo'],
                        disabled=True,
                        key=f"codigo_{idx}",
                        label_visibility="collapsed")
            with cols[2]:
                if editing:
                    item['cod_fabricante'] = st.text_input(
                        "",
                        value=item['cod_fabricante'],
                        key=f"fab_edit_{idx}",
                        label_visibility="collapsed").upper()
                else:
                    st.text_input(
                        "",
                        value=item['cod_fabricante'],
                        disabled=True,
                        key=f"fab_{idx}",
                        label_visibility="collapsed")
            with cols[3]:
                if editing:
                    item['descricao'] = st.text_input(
                        "",
                        value=item['descricao'],
                        key=f"desc_edit_{idx}",
                        label_visibility="collapsed",
                        help="desc-input").upper()
                else:
                    st.text_input(
                        "",
                        value=item['descricao'],
                        disabled=True,
                        key=f"desc_{idx}",
                        label_visibility="collapsed",
                        help="desc-input")
            with cols[4]:
                if editing:
                    item['marca'] = st.text_input(
                        "",
                        value=item['marca'],
                        key=f"marca_edit_{idx}",
                        label_visibility="collapsed").upper()
                else:
                    st.text_input(
                        "",
                        value=item['marca'],
                        disabled=True,
                        key=f"marca_{idx}",
                        label_visibility="collapsed")
            with cols[5]:
                if editing:
                    quantidade = st.text_input(
                        "",
                        value=str(
                            item['quantidade']),
                        key=f"qtd_edit_{idx}",
                        label_visibility="collapsed")
                    try:
                        quantidade_float = float(quantidade.replace(',', '.'))
                        item['quantidade'] = quantidade_float
                    except ValueError:
                        pass
                else:
                    st.text_input(
                        "",
                        value=str(
                            item['quantidade']),
                        disabled=True,
                        key=f"qtd_{idx}",
                        label_visibility="collapsed")
            with cols[6]:
                col1, col2 = st.columns([1, 1])
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
                        for i, item in enumerate(
                                st.session_state.items_temp, 1):
                            item['item'] = i
                        st.rerun()

    proximo_item = len(st.session_state.items_temp) + 1
    cols = st.columns([0.5, 1.5, 2, 3.5, 1.5, 0.5, 0.5])
    with cols[0]:
        st.text_input(
            "",
            value=str(proximo_item),
            disabled=True,
            key=f"item_{proximo_item}",
            label_visibility="collapsed")
    with cols[1]:
        codigo = st.text_input(
            "",
            key=f"codigo_{proximo_item}",
            label_visibility="collapsed").upper()
    with cols[2]:
        cod_fabricante = st.text_input("",
                                       key=f"cod_fab_{proximo_item}",
                                       label_visibility="collapsed").upper()
    with cols[3]:
        descricao = st.text_input(
            "",
            key=f"desc_{proximo_item}",
            label_visibility="collapsed",
            help="desc-input").upper()
    with cols[4]:
        marca = st.text_input(
            "",
            key=f"marca_{proximo_item}",
            label_visibility="collapsed").upper()
    with cols[5]:
        quantidade = st.text_input(
            "",
            key=f"qtd_{proximo_item}",
            label_visibility="collapsed")
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

        # Container para os botões CANCELAR e ENVIAR alinhados
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("❌ CANCELAR", type="secondary", use_container_width=True):
                st.session_state.items_temp = []
                st.session_state['modo_requisicao'] = None
                st.rerun()
        with col2:
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
                    'observacoes_vendedor': observacoes_vendedor,
                    'comprador_responsavel': '',
                    'data_hora_resposta': '',
                    'justificativa_recusa': '',
                    'observacao_geral': ''
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
        # Referência para o nó de configurações no Firebase
        ref = db.reference('configuracoes')
        # Salva as configurações no Firebase
        ref.set(st.session_state.config_sistema)
    except Exception as e:
        st.error(f"Erro ao salvar configurações: {e}")

def toggle_detalhes(numero_requisicao):
    """Alterna a exibição dos detalhes de uma requisição"""
    if st.session_state.get(f'mostrar_detalhes_{numero_requisicao}', False):
        st.session_state.pop(f'mostrar_detalhes_{numero_requisicao}')
    else:
        # Fecha qualquer outro detalhe aberto
        for key in list(st.session_state.keys()):
            if key.startswith('mostrar_detalhes_'):
                st.session_state.pop(key)
        st.session_state[f'mostrar_detalhes_{numero_requisicao}'] = True

def toggle_detalhes(numero_requisicao):
    """Alterna a exibição dos detalhes de uma requisição"""
    if st.session_state.get(f'mostrar_detalhes_{numero_requisicao}', False):
        st.session_state.pop(f'mostrar_detalhes_{numero_requisicao}')
    else:
        # Fecha qualquer outro detalhe aberto
        for key in list(st.session_state.keys()):
            if key.startswith('mostrar_detalhes_'):
                st.session_state.pop(key)
        st.session_state[f'mostrar_detalhes_{numero_requisicao}'] = True

def requisicoes():
    st.title("REQUISIÇÕES")
    
    # Configurações de cores mais saturadas
    status_config = {
        'ABERTA': {'icon': '🔓', 'color': 'rgba(46, 204, 113, 0.3)', 'border': '#2ecc71'},
        'EM ANDAMENTO': {'icon': '🔄', 'color': 'rgba(241, 196, 15, 0.3)', 'border': '#f39c12'},
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
            background-color: white;
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
                    "ABERTA": "🔓 ABERTA",
                    "EM ANDAMENTO": "🔄 EM ANDAMENTO",
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
            requisicoes_visiveis = [req for req in st.session_state.requisicoes if req['vendedor'] == st.session_state['usuario']]
        else:
            requisicoes_visiveis = st.session_state.requisicoes.copy()

        # Garantir que o campo 'numero' seja convertido para inteiro
        for req in requisicoes_visiveis:
            try:
                req['numero'] = int(req['numero'])
            except ValueError:
                st.warning(f"Número inválido na requisição: {req['numero']}")

        # Aplicar filtros
        if numero_busca:
            requisicoes_visiveis = [req for req in requisicoes_visiveis if str(numero_busca) in str(req['numero'])]
        if cliente_busca:
            requisicoes_visiveis = [req for req in requisicoes_visiveis if cliente_busca.upper() in req['cliente'].upper()]
        if produto_busca:
            requisicoes_visiveis = [req for req in requisicoes_visiveis 
                                  if any(produto_busca.upper() in item.get('descricao', '').upper() 
                                        or produto_busca.upper() in item.get('codigo', '').upper()
                                        for item in req['items'])]
        if data_inicial and data_final:
            data_inicial_str = data_inicial.strftime('%d/%m/%Y')
            data_final_str = data_final.strftime('%d/%m/%Y')
            requisicoes_visiveis = [req for req in requisicoes_visiveis if data_inicial_str <= req['data_hora'].split()[0] <= data_final_str]

        # Filtro de status
        requisicoes_visiveis = [req for req in requisicoes_visiveis if req['status'] in selected_status]

        # Ordenação por número em ordem decrescente
        requisicoes_visiveis.sort(key=lambda x: x['numero'], reverse=True)

        # Paginação
        total_paginas = max(1, (len(requisicoes_visiveis) + st.session_state.itens_por_pagina - 1) // st.session_state.itens_por_pagina)
        inicio = (st.session_state.pagina_atual - 1) * st.session_state.itens_por_pagina
        fim = min(inicio + st.session_state.itens_por_pagina, len(requisicoes_visiveis))
        requisicoes_paginadas = requisicoes_visiveis[inicio:fim]

        # Exibição das requisições paginadas
        for idx, req in enumerate(requisicoes_paginadas):
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
                            'R$ Venda Unit': formatar_moeda(item.get('custo_unit', 0) * (1 + item.get('markup', 0) / 100)),
                            'R$ Total': formatar_moeda(item.get('custo_unit', 0) * (1 + item.get('markup', 0) / 100) * item.get('quantidade', 0)),
                            'Prazo': item.get('prazo_entrega', '-'),
                        } for i, item in enumerate(req['items'])])

                        st.dataframe(
                            items_df,
                            use_container_width=True,
                            column_config={
                                "ITEM": "ITEM",
                                "Código": "CÓDIGO",
                                "Cód. Fabricante": "CÓD. FABRICANTE",
                                "Descrição": "DESCRIÇÃO",
                                "Marca": "MARCA",
                                "QTD": "QUANTIDADE",
                                "R$ Venda Unit": "R$ VENDA UNIT",
                                "R$ Total": "R$ TOTAL",
                                "Prazo": "PRAZO",
                                "Observações": "OBSERVAÇÕES"
                            }
                        )

                        # Exibir observações do vendedor e comprador
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
    """Retorna as permissões padrão para cada perfil"""
    perfis_padrao = {
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
    return perfis_padrao.get(perfil.lower(), {})

def configuracoes():
    st.title("Configurações")
    
    if st.session_state['perfil'].lower() in ['administrador', 'comprador']:
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

    if st.session_state.get('config_modo') == 'usuarios' and st.session_state['perfil'].lower() == 'administrador':
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

    elif st.session_state.get('config_modo') == 'perfis' and st.session_state['perfil'].lower() == 'administrador':
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

    elif st.session_state.get('config_modo') == 'sistema':
        st.markdown("### Configurações do Sistema")
        
        if st.session_state['perfil'].lower() == 'administrador':
            tab1, tab2, tab3 = st.tabs(["📊 Monitoramento", "⚙️ Backup", "🔍 Firebase"])
            
            # Monitoramento do Sistema
            with tab1:
                st.markdown("#### Monitoramento do Sistema")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("##### Estatísticas do Firebase")
                    try:
                        ref_requisicoes = db.reference('requisicoes')
                        requisicoes = ref_requisicoes.get()
                        total_requisicoes = len(requisicoes) if requisicoes else 0
                        
                        ref_usuarios = db.reference('usuarios')
                        usuarios = ref_usuarios.get()
                        total_usuarios = len(usuarios) if usuarios else 0
                        
                        st.metric("Total de Requisições", total_requisicoes)
                        st.metric("Total de Usuários", total_usuarios)
                        
                    except Exception as e:
                        st.error(f"Erro ao acessar Firebase: {str(e)}")
                
                with col2:
                    st.markdown("##### Status da Conexão")
                    if verificar_conexao():
                        st.success("✅ Conectado ao Firebase")
                        st.metric("Status", "Online")
                    else:
                        st.error("❌ Problema na conexão com o Firebase")
                        st.metric("Status", "Offline")

                # Gráfico de espaço disponível/consumido
                st.markdown("#### Armazenamento do Firebase")
                try:
                    fig = mostrar_espaco_armazenamento()
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Erro ao gerar gráfico: {str(e)}")

            # Gerenciamento de Backup
            with tab2:
                st.markdown("#### Gerenciamento de Backup")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("🔄 Criar Backup Agora", type="primary", use_container_width=True):
                        try:
                            with st.spinner("Criando backup..."):
                                backup_file = backup_requisicoes()
                                if backup_file and verificar_conteudo_backup(backup_file):
                                    st.success(f"Backup criado com sucesso: {os.path.basename(backup_file)}")
                                else:
                                    st.error("Falha ao criar ou verificar o backup.")
                        except Exception as e:
                            st.error(f"Erro ao criar backup: {str(e)}")
                
                with col2:
                    uploaded_file = st.file_uploader(
                        "Selecione um arquivo de backup para restaurar",
                        type=['json'],
                        help="Somente arquivos JSON são suportados."
                    )
                    if uploaded_file and st.button("📥 Restaurar Backup", type="primary"):
                        try:
                            with st.spinner("Restaurando backup..."):
                                if restaurar_backup(uploaded_file):
                                    st.success("Backup restaurado com sucesso!")
                                    st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao restaurar backup: {str(e)}")
                
                st.markdown("#### Backups Disponíveis")
                listar_backups()

            # Visualização geral do Firebase
            with tab3:
                st.markdown("#### Visualização Geral do Firebase")
                
                try:
                    ref_requisicoes = db.reference('requisicoes')
                    requisicoes = ref_requisicoes.get()
                    
                    ref_usuarios = db.reference('usuarios')
                    usuarios = ref_usuarios.get()
                    
                    # Exibição em formato JSON
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("Requisições (JSON)")
                        if requisicoes:
                            requisicoes_str = json.dumps(requisicoes, ensure_ascii=False, indent=4)
                            st.text_area("", value=requisicoes_str, height=300)
                    
                    with col2:
                        st.subheader("Usuários (JSON)")
                        if usuarios:
                            usuarios_str = json.dumps(usuarios, ensure_ascii=False, indent=4)
                            st.text_area("", value=usuarios_str, height=300)
                    
                except Exception as e:
                    st.error(f"Erro ao carregar dados: {str(e)}")

def gerenciamento_perfis():
    st.title("⚙️ Controle de Acesso por Perfil")
    
    # Carregar perfis do Firebase ou criar padrões
    ref_perfis = db.reference('perfis')
    perfis = ref_perfis.get() or {
        'vendedor': {
            'dashboard': True,
            'requisicoes': True,
            'cotacoes': True,
            'importacao': False,
            'configuracoes': False
        },
        'comprador': {
            'dashboard': True,
            'requisicoes': True,
            'cotacoes': True,
            'importacao': True,
            'configuracoes': False
        },
        'administrador': {
            'dashboard': True,
            'requisicoes': True,
            'cotacoes': True,
            'importacao': True,
            'configuracoes': True
        }
    }
    
    # Seletor de perfil
    perfil = st.selectbox(
        "SELECIONE O PERFIL:",
        options=list(perfis.keys()),
        format_func=lambda x: x.upper()
    )
    
    st.markdown("### 🔘 Habilitar/Desabilitar Telas")
    st.caption("As alterações são aplicadas instantaneamente")

    # Contêiner principal
    with st.container():
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📊 Telas Principais")
            for tela, label in [
                ('dashboard', 'Dashboard'),
                ('requisicoes', 'Requisições'),
                ('cotacoes', 'Cotações')
            ]:
                novo_valor = st.toggle(
                    label,
                    value=perfis[perfil].get(tela, False),
                    key=f"{perfil}_{tela}_toggle"
                )
                if novo_valor != perfis[perfil].get(tela, False):
                    perfis[perfil][tela] = novo_valor
                    ref_perfis.child(perfil).update({tela: novo_valor})
                    st.session_state.perfis = perfis
                    st.rerun()
        
        with col2:
            st.markdown("#### 🛠️ Telas Avançadas")
            for tela, label in [
                ('importacao', 'Importação'),
                ('configuracoes', 'Configurações')
            ]:
                novo_valor = st.toggle(
                    label,
                    value=perfis[perfil].get(tela, False),
                    key=f"{perfil}_{tela}_toggle"
                )
                if novo_valor != perfis[perfil].get(tela, False):
                    perfis[perfil][tela] = novo_valor
                    ref_perfis.child(perfil).update({tela: novo_valor})
                    st.session_state.perfis = perfis
                    st.rerun()

    # Visualização rápida
    st.divider()
    st.markdown(f"**PERFIL SELECIONADO:** `{perfil.upper()}`")
    st.markdown("**PERMISSÕES ATIVAS:**")
    
    permissoes_ativas = [tela for tela, ativa in perfis[perfil].items() if ativa]
    if permissoes_ativas:
        st.write(", ".join(permissoes_ativas))
    else:
        st.warning("Nenhuma permissão ativa para este perfil")

    # Botão de restauração
    if st.button("🔄 Restaurar Padrões", type="secondary"):
        perfis_padrao = {
            'vendedor': {
                'dashboard': True,
                'requisicoes': True,
                'cotacoes': True,
                'importacao': False,
                'configuracoes': False
            },
            'comprador': {
                'dashboard': True,
                'requisicoes': True,
                'cotacoes': True,
                'importacao': True,
                'configuracoes': False
            },
            'administrador': {
                'dashboard': True,
                'requisicoes': True,
                'cotacoes': True,
                'importacao': True,
                'configuracoes': True
            }
        }
        ref_perfis.set(perfis_padrao)
        st.session_state.perfis = perfis_padrao
        st.success("Padrões restaurados com sucesso!")
        st.rerun()
                    
def main():
    # Inicializar Firebase antes de qualquer operação
    if not inicializar_firebase():
        st.error("FALHA CRÍTICA: Não foi possível conectar ao banco de dados")
        st.stop()

    # Inicializar sistema e bancos de dados
    if not inicializar_sistema():
        st.error("Falha na inicialização do sistema")
        st.stop()

    # Atualização automática (opcional)
    st_autorefresh(interval=3600000, key="backup_refresh")  # 1 hora

    # Verificação de autenticação
    if 'usuario' not in st.session_state:
        tela_login()
    else:
        # Header com última atualização
        col1, col2 = st.columns([3, 1])
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

        # Carregar menu lateral
        menu = menu_lateral()

        # Navegação entre telas
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
        else:
            st.error("Opção de menu inválida")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Erro inesperado: {str(e)}")
        logging.error(f"Erro inesperado: {str(e)}", exc_info=True)
