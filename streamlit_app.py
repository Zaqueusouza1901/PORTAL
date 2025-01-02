import streamlit as st
import pandas as pd
    if 'items_temp' not in st.session_state:
        st.session_state.items_temp = []

def nova_requisicao():
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

        with tab3:
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

def main():
    if 'usuario' not in st.session_state:
        tela_login()
    else:
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

        with tab3:
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

def main():
    if 'usuario' not in st.session_state:
        tela_login()
    else:
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
                    'numero': st.session_state.next_req_number,
                    'cliente': cliente,
                    'vendedor': st.session_state['usuario'],
                    'data_hora': get_data_hora_brasil(),
                    'status': 'ABERTA',
                    'items': st.session_state.items_temp.copy()
                }
                st.session_state.requisicoes.append(nova_requisicao)
                salvar_requisicoes()
                st.session_state.next_req_number += 1
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
    st.markdown("""
        <style>
        .stTextInput input, .stNumberInput input {
            border: 2px solid #2D2C74 !important;
            border-radius: 4px !important;
            padding: 8px 12px !important;
        }
        .stExpander {
            background-color: white !important;
            border: 1px solid #e0e0e0 !important;
            border-radius: 8px !important;
            margin-bottom: 1rem !important;
        }
        .item-container {
            background-color: #f1f8ff;
            padding: 15px;
            border-radius: 6px;
            margin: 10px 0;
            border-left: 4px solid #1B81C5;
        }
        .item-saved {
            background-color: #e8f5e9;
            border-left: 4px solid #4caf50;
        }
        .requisicao-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 15px;
        }
        .requisicao-table th, .requisicao-table td {
            padding: 8px;
            text-align: left;
            border: 1px solid #e0e0e0;
        }
        .requisicao-table th {
            background-color: #f8f9fa;
            font-weight: 500;
            color: #2D2C74;
            white-space: nowrap;
            text-align: center;
        }
        .requisicao-table td {
            background-color: #ffffff;
            text-align: center;
        }
        .valor-cell {
            text-align: right;
            white-space: nowrap;
        }
        .items-title {
            font-size: 16px;
            font-weight: 600;
            margin: 15px 0;
            color: #2D2C74;
        }
        </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([4,1])
    with col2:
        if st.button("📝 Nova Requisição", key="nova_req", type="primary"):
            st.session_state['modo_requisicao'] = 'nova'
            st.rerun()

    if st.session_state.get('modo_requisicao') == 'nova':
        nova_requisicao()
    else:
        st.write("Filtrar por Status")
        if st.session_state['perfil'] == 'vendedor':
            default_status = ["ABERTA", "EM ANDAMENTO", "FINALIZADA", "RECUSADA"]
        else:
            default_status = ["ABERTA", "EM ANDAMENTO"]
        
        selected_status = st.multiselect(
            "",
            ["ABERTA", "EM ANDAMENTO", "FINALIZADA", "RECUSADA"],
            default=default_status,
            label_visibility="collapsed"
        )

        requisicoes_visiveis = []
        for req in st.session_state.requisicoes:
            if st.session_state['perfil'] == 'vendedor':
                if req['vendedor'] == st.session_state['usuario']:
                    requisicoes_visiveis.append(req)
            elif st.session_state['perfil'] in ['comprador', 'administrador']:
                requisicoes_visiveis.append(req)
            else:
                if req['vendedor'] == st.session_state['usuario']:
                    requisicoes_visiveis.append(req)

        # Ordena as requisições pelo número em ordem decrescente
        requisicoes_visiveis.sort(key=lambda x: x['numero'], reverse=True)

        for idx, req in enumerate(requisicoes_visiveis):
            if req['status'] in selected_status:
                with st.expander(f"📋 #{req['numero']} - {req['cliente']} ({req['status']})"):
                    st.markdown(f"""
                        <div class="requisicao-container">
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
                        </div>
                    """, unsafe_allow_html=True)

                    st.markdown('<div class="items-title">Itens da Requisição</div>', unsafe_allow_html=True)
                    if req['items']:
                        st.markdown("""
                            <table class="requisicao-table">
                                <thead>
                                    <tr>
                                        <th style="width: 7%">CÓDIGO</th>
                                        <th style="width: 15%">CÓD. FABRICANTE</th>
                                        <th style="width: 35%">DESCRIÇÃO</th>
                                        <th style="width: 12%">MARCA</th>
                                        <th style="width: 4%">QUANTIDADE</th>
                                    </tr>
                                </thead>
                                <tbody>
                        """, unsafe_allow_html=True)
                        
                        for item in req['items']:
                            st.markdown(f"""
                                <tr>
                                    <td>{item.get('codigo', '-')}</td>
                                    <td>{item.get('cod_fabricante', '-')}</td>
                                    <td>{item['descricao']}</td>
                                    <td>{item.get('marca', 'PC')}</td>
                                    <td class="valor-cell">{item['quantidade']}</td>
                                </tr>
                            """, unsafe_allow_html=True)
                        st.markdown("</tbody></table>", unsafe_allow_html=True)

                    # Botões de Aceitar/Recusar para requisições ABERTAS
                    if st.session_state['perfil'] in ['administrador', 'comprador'] and req['status'] == 'ABERTA':
                        col1, col2 = st.columns([1,1])
                        with col1:
                            if st.button("✅ Aceitar", key=f"aceitar_{req['numero']}", type="primary", use_container_width=True):
                                req['status'] = 'EM ANDAMENTO'
                                req['comprador_responsavel'] = st.session_state['usuario']
                                req['data_hora_aceite'] = get_data_hora_brasil()
                                salvar_requisicoes()
                                st.success("Requisição aceita com sucesso!")
                                st.rerun()
                        
                        with col2:
                            if st.button("❌ Recusar", key=f"recusar_{req['numero']}", type="secondary", use_container_width=True):
                                st.session_state[f'mostrar_justificativa_{req["numero"]}'] = True
                                st.rerun()

                        if st.session_state.get(f'mostrar_justificativa_{req["numero"]}', False):
                            justificativa = st.text_area("Motivo da Recusa", key=f"justificativa_{req['numero']}")
                            if st.button("Confirmar Recusa", key=f"confirmar_recusa_{req['numero']}", type="secondary"):
                                if justificativa.strip():
                                    req['status'] = 'RECUSADA'
                                    req['justificativa_recusa'] = justificativa
                                    req['data_hora_recusa'] = get_data_hora_brasil()
                                    req['comprador_responsavel'] = st.session_state['usuario']
                                    salvar_requisicoes()
                                    st.success("Requisição recusada com sucesso!")
                                    st.rerun()
                                else:
                                    st.error("Por favor, insira uma justificativa para a recusa.")

                    # Campos de resposta apenas para requisições EM ANDAMENTO
                    if st.session_state['perfil'] in ['administrador', 'comprador'] and req['status'] == 'EM ANDAMENTO':
                        for item_idx, item in enumerate(req['items']):
                            with st.container():
                                item_class = 'item-container item-saved' if item.get('salvo') else 'item-container'
                                st.markdown(f"""
                                    <div class='{item_class}'>
                                        <h4>Item {item['item']}: {item['descricao']} - Quantidade: {item['quantidade']}</h4>
                                    </div>
                                """, unsafe_allow_html=True)

                                col1, col2, col3 = st.columns([1,1,1])
                                with col1:
                                    item['custo_unit'] = st.number_input(
                                        f"R$ UNIT Item {item['item']} *",
                                        value=item.get('custo_unit', 0.0),
                                        format="%.2f",
                                        key=f"custo_{req['numero']}_{item['item']}_{idx}"
                                    )
                                with col2:
                                    item['markup'] = st.number_input(
                                        f"% MARKUP Item {item['item']} *",
                                        value=item.get('markup', 0.0),
                                        format="%.2f",
                                        key=f"markup_{req['numero']}_{item['item']}_{idx}"
                                    )
                                with col3:
                                    item['venda_unit'] = item['custo_unit'] * (1 + item['markup']/100)
                                    st.text_input(
                                        "R$ VENDA UNIT",
                                        value=f"R$ {item['venda_unit']:.2f}",
                                        disabled=True,
                                        key=f"venda_{req['numero']}_{item['item']}_{idx}"
                                    )

                                col1, col2 = st.columns([2,1])
                                with col2:
                                    if st.button("💾 Salvar Item", key=f"salvar_item_{req['numero']}_{item['item']}_{idx}"):
                                        if item['custo_unit'] > 0 and item['markup'] > 0:
                                            item['salvo'] = True
                                            salvar_requisicoes()
                                            st.success(f"Item {item['item']} salvo com sucesso!")
                                            st.rerun()
                                        else:
                                            st.error("Preencha o valor unitário e markup antes de salvar")

                        todos_itens_salvos = all(item.get('salvo', False) for item in req['items'])
                        if todos_itens_salvos:
                            if st.button("✅ Finalizar", key=f"finalizar_{req['numero']}", type="primary", use_container_width=True):
                                req['status'] = 'FINALIZADA'
                                req['data_hora_resposta'] = get_data_hora_brasil()
                                salvar_requisicoes()
                                st.success("Requisição finalizada com sucesso!")
                                st.rerun()
                        else:
                            st.info("Complete o preenchimento de todos os itens para finalizar")
                        
                        with col2:
                            if st.button("❌ Recusar", key=f"recusar_{req['numero']}", type="secondary", use_container_width=True):
                                st.session_state[f'mostrar_justificativa_{req["numero"]}'] = True
                                st.rerun()

                            if st.session_state.get(f'mostrar_justificativa_{req["numero"]}', False):
                                justificativa = st.text_area("Motivo da Recusa", key=f"justificativa_{req['numero']}")
                                if st.button("Confirmar Recusa", key=f"confirmar_recusa_{req['numero']}", type="secondary"):
                                    if justificativa.strip():
                                        req['status'] = 'RECUSADA'
                                        req['justificativa_recusa'] = justificativa
                                        req['data_hora_recusa'] = get_data_hora_brasil()
                                        salvar_requisicoes()
                                        st.success("Requisição recusada com sucesso!")
                                        st.rerun()
                                    else:
                                        st.error("Por favor, insira uma justificativa para a recusa.")

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
        
        if st.session_state['perfil'] == 'administrador':
            with col3:
                if st.button("⚙️ Sistema", type="primary", use_container_width=True):
                    st.session_state['config_modo'] = 'sistema'
                    st.rerun()

    # Seção de Usuários
    if st.session_state.get('config_modo') == 'usuarios':
        st.markdown("### Gerenciamento de Usuários")
        if st.button("➕ Cadastrar Novo Usuário", type="primary"):
            st.session_state['usuario_modo'] = 'cadastrar'
            st.rerun()
        
        # Tabela de usuários
        st.markdown("#### Usuários Cadastrados")
        usuarios_df = pd.DataFrame([{
            'Usuário': usuario,
            'Email': dados['email'],
            'Perfil': dados['perfil'],
            'Status': '🟢 Ativo' if dados['ativo'] else '🔴 Inativo'
        } for usuario, dados in st.session_state.usuarios.items()])
        
        st.dataframe(usuarios_df, hide_index=True, use_container_width=True)

        # Seção de edição de usuário
        st.markdown("#### Editar Usuário")
        usuario_editar = st.selectbox("Selecione o usuário para editar", options=list(st.session_state.usuarios.keys()))
        
        if usuario_editar:
            dados_usuario = st.session_state.usuarios[usuario_editar]
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                novo_nome = st.text_input("Nome do Usuário", value=usuario_editar, key=f"nome_{usuario_editar}").upper()
            
            with col2:
                novo_email = st.text_input("Email", value=dados_usuario['email'], key=f"email_{usuario_editar}")
            
            with col3:
                novo_perfil = st.selectbox("Perfil", options=['vendedor', 'comprador', 'administrador'], 
                                            index=['vendedor', 'comprador', 'administrador'].index(dados_usuario['perfil']), 
                                            key=f"perfil_{usuario_editar}")
            
            with col4:
                status_atual = dados_usuario['ativo']
                novo_status = st.toggle("Ativo", value=status_atual, key=f"status_{usuario_editar}")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("💾 Salvar Alterações", type="primary", use_container_width=True):
                    if novo_nome != usuario_editar:
                        if novo_nome not in st.session_state.usuarios:
                            st.session_state.usuarios[novo_nome] = st.session_state.usuarios.pop(usuario_editar)
                        else:
                            st.error("Já existe um usuário com este nome.")
                            return
                    
                    st.session_state.usuarios[novo_nome].update({
                        'email': novo_email,
                        'perfil': novo_perfil,
                        'ativo': novo_status,
                        'permissoes': get_permissoes_perfil(novo_perfil)
                    })
                    salvar_usuarios()
                    st.success("Usuário atualizado com sucesso!")
                    st.rerun()
            
            with col2:
                if st.button("🔄 Reset Senha", type="primary", use_container_width=True):
                    st.session_state.usuarios[novo_nome]['senha'] = None
                    salvar_usuarios()
                    st.success("Senha resetada com sucesso!")
                    st.rerun()
            
            with col3:
                if st.button("❌ Excluir Usuário", type="primary", use_container_width=True):
                    if st.session_state.usuarios[novo_nome]['perfil'] != 'administrador':
                        st.session_state.usuarios.pop(novo_nome)
                        salvar_usuarios()
                        st.success("Usuário excluído com sucesso!")
                        st.rerun()
                    else:
                        st.error("Não é possível excluir um usuário administrador")

        if st.session_state.get('usuario_modo') == 'cadastrar':
            with st.form("cadastro_usuario"):
                st.subheader("Cadastrar Novo Usuário")
                novo_usuario = st.text_input("Nome do Usuário").upper()
                email = st.text_input("Email")
                perfil = st.selectbox("Perfil", ['vendedor', 'comprador', 'administrador'])
                
                if st.form_submit_button("Cadastrar"):
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
                            st.session_state['usuario_modo'] = None
                            st.rerun()
                        else:
                            st.error("Usuário já existe")
                    else:
                        st.error("Preencha todos os campos")

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
        
        tab1, tab2, tab3 = st.tabs(["🎨 Cores", "📝 Fontes", "📐 Layout"])
        
        with tab1:
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

        with tab2:
            col1, col2 = st.columns(2)
            with col1:
                familia_fonte = st.selectbox(
                    "Fonte",
                    ["Inter", "Roboto", "Open Sans", "Lato", "Montserrat"]
                )
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
                    'numero': st.session_state.next_req_number,
                    'cliente': cliente,
                    'vendedor': st.session_state['usuario'],
                    'data_hora': get_data_hora_brasil(),
                    'status': 'ABERTA',
                    'items': st.session_state.items_temp.copy()
                }
                st.session_state.requisicoes.append(nova_requisicao)
                salvar_requisicoes()
                st.session_state.next_req_number += 1
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
    st.markdown("""
        <style>
        .stTextInput input, .stNumberInput input {
            border: 2px solid #2D2C74 !important;
            border-radius: 4px !important;
            padding: 8px 12px !important;
        }
        .stExpander {
            background-color: white !important;
            border: 1px solid #e0e0e0 !important;
            border-radius: 8px !important;
            margin-bottom: 1rem !important;
        }
        .item-container {
            background-color: #f1f8ff;
            padding: 15px;
            border-radius: 6px;
            margin: 10px 0;
            border-left: 4px solid #1B81C5;
        }
        .item-saved {
            background-color: #e8f5e9;
            border-left: 4px solid #4caf50;
        }
        .requisicao-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 15px;
        }
        .requisicao-table th, .requisicao-table td {
            padding: 8px;
            text-align: left;
            border: 1px solid #e0e0e0;
        }
        .requisicao-table th {
            background-color: #f8f9fa;
            font-weight: 500;
            color: #2D2C74;
            white-space: nowrap;
            text-align: center;
        }
        .requisicao-table td {
            background-color: #ffffff;
            text-align: center;
        }
        .valor-cell {
            text-align: right;
            white-space: nowrap;
        }
        .items-title {
            font-size: 16px;
            font-weight: 600;
            margin: 15px 0;
            color: #2D2C74;
        }
        </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([4,1])
    with col2:
        if st.button("📝 Nova Requisição", key="nova_req", type="primary"):
            st.session_state['modo_requisicao'] = 'nova'
            st.rerun()

    if st.session_state.get('modo_requisicao') == 'nova':
        nova_requisicao()
    else:
        st.write("Filtrar por Status")
        if st.session_state['perfil'] == 'vendedor':
            default_status = ["ABERTA", "EM ANDAMENTO", "FINALIZADA", "RECUSADA"]
        else:
            default_status = ["ABERTA", "EM ANDAMENTO"]
        
        selected_status = st.multiselect(
            "",
            ["ABERTA", "EM ANDAMENTO", "FINALIZADA", "RECUSADA"],
            default=default_status,
            label_visibility="collapsed"
        )

        requisicoes_visiveis = []
        for req in st.session_state.requisicoes:
            if st.session_state['perfil'] == 'vendedor':
                if req['vendedor'] == st.session_state['usuario']:
                    requisicoes_visiveis.append(req)
            elif st.session_state['perfil'] in ['comprador', 'administrador']:
                requisicoes_visiveis.append(req)
            else:
                if req['vendedor'] == st.session_state['usuario']:
                    requisicoes_visiveis.append(req)

        # Ordena as requisições pelo número em ordem decrescente
        requisicoes_visiveis.sort(key=lambda x: x['numero'], reverse=True)

        for idx, req in enumerate(requisicoes_visiveis):
            if req['status'] in selected_status:
                with st.expander(f"📋 #{req['numero']} - {req['cliente']} ({req['status']})"):
                    st.markdown(f"""
                        <div class="requisicao-container">
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
                        </div>
                    """, unsafe_allow_html=True)

                    st.markdown('<div class="items-title">Itens da Requisição</div>', unsafe_allow_html=True)
                    if req['items']:
                        st.markdown("""
                            <table class="requisicao-table">
                                <thead>
                                    <tr>
                                        <th style="width: 7%">CÓDIGO</th>
                                        <th style="width: 15%">CÓD. FABRICANTE</th>
                                        <th style="width: 35%">DESCRIÇÃO</th>
                                        <th style="width: 12%">MARCA</th>
                                        <th style="width: 4%">QUANTIDADE</th>
                                    </tr>
                                </thead>
                                <tbody>
                        """, unsafe_allow_html=True)
                        
                        for item in req['items']:
                            st.markdown(f"""
                                <tr>
                                    <td>{item.get('codigo', '-')}</td>
                                    <td>{item.get('cod_fabricante', '-')}</td>
                                    <td>{item['descricao']}</td>
                                    <td>{item.get('marca', 'PC')}</td>
                                    <td class="valor-cell">{item['quantidade']}</td>
                                </tr>
                            """, unsafe_allow_html=True)
                        st.markdown("</tbody></table>", unsafe_allow_html=True)

                    # Botões de Aceitar/Recusar para requisições ABERTAS
                    if st.session_state['perfil'] in ['administrador', 'comprador'] and req['status'] == 'ABERTA':
                        col1, col2 = st.columns([1,1])
                        with col1:
                            if st.button("✅ Aceitar", key=f"aceitar_{req['numero']}", type="primary", use_container_width=True):
                                req['status'] = 'EM ANDAMENTO'
                                req['comprador_responsavel'] = st.session_state['usuario']
                                req['data_hora_aceite'] = get_data_hora_brasil()
                                salvar_requisicoes()
                                st.success("Requisição aceita com sucesso!")
                                st.rerun()
                        
                        with col2:
                            if st.button("❌ Recusar", key=f"recusar_{req['numero']}", type="secondary", use_container_width=True):
                                st.session_state[f'mostrar_justificativa_{req["numero"]}'] = True
                                st.rerun()

                        if st.session_state.get(f'mostrar_justificativa_{req["numero"]}', False):
                            justificativa = st.text_area("Motivo da Recusa", key=f"justificativa_{req['numero']}")
                            if st.button("Confirmar Recusa", key=f"confirmar_recusa_{req['numero']}", type="secondary"):
                                if justificativa.strip():
                                    req['status'] = 'RECUSADA'
                                    req['justificativa_recusa'] = justificativa
                                    req['data_hora_recusa'] = get_data_hora_brasil()
                                    req['comprador_responsavel'] = st.session_state['usuario']
                                    salvar_requisicoes()
                                    st.success("Requisição recusada com sucesso!")
                                    st.rerun()
                                else:
                                    st.error("Por favor, insira uma justificativa para a recusa.")

                    # Campos de resposta apenas para requisições EM ANDAMENTO
                    if st.session_state['perfil'] in ['administrador', 'comprador'] and req['status'] == 'EM ANDAMENTO':
                        for item_idx, item in enumerate(req['items']):
                            with st.container():
                                item_class = 'item-container item-saved' if item.get('salvo') else 'item-container'
                                st.markdown(f"""
                                    <div class='{item_class}'>
                                        <h4>Item {item['item']}: {item['descricao']} - Quantidade: {item['quantidade']}</h4>
                                    </div>
                                """, unsafe_allow_html=True)

                                col1, col2, col3 = st.columns([1,1,1])
                                with col1:
                                    item['custo_unit'] = st.number_input(
                                        f"R$ UNIT Item {item['item']} *",
                                        value=item.get('custo_unit', 0.0),
                                        format="%.2f",
                                        key=f"custo_{req['numero']}_{item['item']}_{idx}"
                                    )
                                with col2:
                                    item['markup'] = st.number_input(
                                        f"% MARKUP Item {item['item']} *",
                                        value=item.get('markup', 0.0),
                                        format="%.2f",
                                        key=f"markup_{req['numero']}_{item['item']}_{idx}"
                                    )
                                with col3:
                                    item['venda_unit'] = item['custo_unit'] * (1 + item['markup']/100)
                                    st.text_input(
                                        "R$ VENDA UNIT",
                                        value=f"R$ {item['venda_unit']:.2f}",
                                        disabled=True,
                                        key=f"venda_{req['numero']}_{item['item']}_{idx}"
                                    )

                                col1, col2 = st.columns([2,1])
                                with col2:
                                    if st.button("💾 Salvar Item", key=f"salvar_item_{req['numero']}_{item['item']}_{idx}"):
                                        if item['custo_unit'] > 0 and item['markup'] > 0:
                                            item['salvo'] = True
                                            salvar_requisicoes()
                                            st.success(f"Item {item['item']} salvo com sucesso!")
                                            st.rerun()
                                        else:
                                            st.error("Preencha o valor unitário e markup antes de salvar")

                        todos_itens_salvos = all(item.get('salvo', False) for item in req['items'])
                        if todos_itens_salvos:
                            if st.button("✅ Finalizar", key=f"finalizar_{req['numero']}", type="primary", use_container_width=True):
                                req['status'] = 'FINALIZADA'
                                req['data_hora_resposta'] = get_data_hora_brasil()
                                salvar_requisicoes()
                                st.success("Requisição finalizada com sucesso!")
                                st.rerun()
                        else:
                            st.info("Complete o preenchimento de todos os itens para finalizar")
                        
                        with col2:
                            if st.button("❌ Recusar", key=f"recusar_{req['numero']}", type="secondary", use_container_width=True):
                                st.session_state[f'mostrar_justificativa_{req["numero"]}'] = True
                                st.rerun()

                            if st.session_state.get(f'mostrar_justificativa_{req["numero"]}', False):
                                justificativa = st.text_area("Motivo da Recusa", key=f"justificativa_{req['numero']}")
                                if st.button("Confirmar Recusa", key=f"confirmar_recusa_{req['numero']}", type="secondary"):
                                    if justificativa.strip():
                                        req['status'] = 'RECUSADA'
                                        req['justificativa_recusa'] = justificativa
                                        req['data_hora_recusa'] = get_data_hora_brasil()
                                        salvar_requisicoes()
                                        st.success("Requisição recusada com sucesso!")
                                        st.rerun()
                                    else:
                                        st.error("Por favor, insira uma justificativa para a recusa.")

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
        
        if st.session_state['perfil'] == 'administrador':
            with col3:
                if st.button("⚙️ Sistema", type="primary", use_container_width=True):
                    st.session_state['config_modo'] = 'sistema'
                    st.rerun()

    # Seção de Usuários
    if st.session_state.get('config_modo') == 'usuarios':
        st.markdown("### Gerenciamento de Usuários")
        if st.button("➕ Cadastrar Novo Usuário", type="primary"):
            st.session_state['usuario_modo'] = 'cadastrar'
            st.rerun()
        
        # Tabela de usuários
        st.markdown("#### Usuários Cadastrados")
        usuarios_df = pd.DataFrame([{
            'Usuário': usuario,
            'Email': dados['email'],
            'Perfil': dados['perfil'],
            'Status': '🟢 Ativo' if dados['ativo'] else '🔴 Inativo'
        } for usuario, dados in st.session_state.usuarios.items()])
        
        st.dataframe(usuarios_df, hide_index=True, use_container_width=True)

        # Seção de edição de usuário
        st.markdown("#### Editar Usuário")
        usuario_editar = st.selectbox("Selecione o usuário para editar", options=list(st.session_state.usuarios.keys()))
        
        if usuario_editar:
            dados_usuario = st.session_state.usuarios[usuario_editar]
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                novo_nome = st.text_input("Nome do Usuário", value=usuario_editar, key=f"nome_{usuario_editar}").upper()
            
            with col2:
                novo_email = st.text_input("Email", value=dados_usuario['email'], key=f"email_{usuario_editar}")
            
            with col3:
                novo_perfil = st.selectbox("Perfil", options=['vendedor', 'comprador', 'administrador'], 
                                            index=['vendedor', 'comprador', 'administrador'].index(dados_usuario['perfil']), 
                                            key=f"perfil_{usuario_editar}")
            
            with col4:
                status_atual = dados_usuario['ativo']
                novo_status = st.toggle("Ativo", value=status_atual, key=f"status_{usuario_editar}")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("💾 Salvar Alterações", type="primary", use_container_width=True):
                    if novo_nome != usuario_editar:
                        if novo_nome not in st.session_state.usuarios:
                            st.session_state.usuarios[novo_nome] = st.session_state.usuarios.pop(usuario_editar)
                        else:
                            st.error("Já existe um usuário com este nome.")
                            return
                    
                    st.session_state.usuarios[novo_nome].update({
                        'email': novo_email,
                        'perfil': novo_perfil,
                        'ativo': novo_status,
                        'permissoes': get_permissoes_perfil(novo_perfil)
                    })
                    salvar_usuarios()
                    st.success("Usuário atualizado com sucesso!")
                    st.rerun()
            
            with col2:
                if st.button("🔄 Reset Senha", type="primary", use_container_width=True):
                    st.session_state.usuarios[novo_nome]['senha'] = None
                    salvar_usuarios()
                    st.success("Senha resetada com sucesso!")
                    st.rerun()
            
            with col3:
                if st.button("❌ Excluir Usuário", type="primary", use_container_width=True):
                    if st.session_state.usuarios[novo_nome]['perfil'] != 'administrador':
                        st.session_state.usuarios.pop(novo_nome)
                        salvar_usuarios()
                        st.success("Usuário excluído com sucesso!")
                        st.rerun()
                    else:
                        st.error("Não é possível excluir um usuário administrador")

        if st.session_state.get('usuario_modo') == 'cadastrar':
            with st.form("cadastro_usuario"):
                st.subheader("Cadastrar Novo Usuário")
                novo_usuario = st.text_input("Nome do Usuário").upper()
                email = st.text_input("Email")
                perfil = st.selectbox("Perfil", ['vendedor', 'comprador', 'administrador'])
                
                if st.form_submit_button("Cadastrar"):
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
                            st.session_state['usuario_modo'] = None
                            st.rerun()
                        else:
                            st.error("Usuário já existe")
                    else:
                        st.error("Preencha todos os campos")

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
        
        tab1, tab2, tab3 = st.tabs(["🎨 Cores", "📝 Fontes", "📐 Layout"])
        
        with tab1:
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

        with tab2:
            col1, col2 = st.columns(2)
            with col1:
                familia_fonte = st.selectbox(
                    "Fonte",
                    ["Inter", "Roboto", "Open Sans", "Lato", "Montserrat"]
                )
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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

def get_permissoes_perfil(perfil):
    # Permissões padrão do sistema
    permissoes_padrao = {
        'administrador': ['dashboard', 'requisicoes', 'cotacoes', 'importacao', 'configuracoes'],
        'comprador': ['dashboard', 'requisicoes', 'cotacoes', 'importacao', 'configuracoes'],
        'vendedor': ['dashboard', 'requisicoes']
    }
    return permissoes_padrao.get(perfil, ['dashboard'])

def save_perfis_permissoes(perfil, permissoes):
    try:
        perfis_permissoes = {}
        arquivo_permissoes = 'perfis_permissoes.json'
        
        if os.path.exists(arquivo_permissoes):
            with open(arquivo_permissoes, 'r', encoding='utf-8') as f:
                perfis_permissoes = json.load(f)
        
        perfis_permissoes[perfil] = permissoes
        
        with open(arquivo_permissoes, 'w', encoding='utf-8') as f:
            json.dump(perfis_permissoes, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar permissões: {str(e)}")
        return False

def load_users():
    usuario_padrao = {
        'ZAQUEU SOUZA': {
            'senha': 'Za@031162',
            'perfil': 'administrador',
            'email': 'zaqueu@jetfrio.com.br',
            'ativo': True,
            'primeiro_acesso': False,
            'permissoes': get_permissoes_perfil('administrador')
        }
    }
    
    try:
        if os.path.exists('usuarios.json'):
            with open('usuarios.json', 'r', encoding='utf-8') as f:
                usuarios = json.load(f)
                if usuarios:
                    return usuarios
    except Exception as e:
        st.error(f"Erro ao carregar usuários: {str(e)}")
    
    return usuario_padrao

def save_users():
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
    st.session_state.usuarios = load_users()

if 'next_req_number' not in st.session_state:
    st.session_state.next_req_number = 5000

if 'requisicoes' not in st.session_state:
    st.session_state.requisicoes = carregar_requisicoes()

def tela_login():
    st.title("PORTAL - JETFRIO")
    usuario = st.text_input("Usuário", key="usuario_input").upper()
    
    if usuario:
        if usuario in st.session_state.usuarios:
            user_data = st.session_state.usuarios[usuario]
            
            if user_data.get('primeiro_acesso', True):
                st.markdown("### 😊 Olá, Este é o seu primeiro acesso, por favor, cadastre sua senha.")
                with st.form("primeiro_acesso_form"):
                    nova_senha = st.text_input("Nova Senha", type="password")
                    confirma_senha = st.text_input("Confirme a Nova Senha", type="password")
                    
                    if st.form_submit_button("Cadastrar Senha"):
                        if nova_senha == confirma_senha:
                            st.session_state.usuarios[usuario]['senha'] = nova_senha
                            st.session_state.usuarios[usuario]['primeiro_acesso'] = False
                            save_users()
                            st.success("Senha cadastrada com sucesso! Por favor, faça login.")
                            st.session_state['modo_login'] = 'login'
                            st.rerun()
                        else:
                            st.error("As senhas não coincidem.")
            else:
                senha = st.text_input("Senha", type="password", key="senha_input")
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    if st.button("Login"):
                        if user_data['senha'] == senha and user_data['ativo']:
                            st.session_state['usuario'] = usuario
                            st.session_state['perfil'] = user_data['perfil']
                            st.success(f"Bem-vindo, {usuario}!")
                            st.rerun()
                        else:
                            st.error("Senha incorreta ou usuário inativo.")
                
                with col2:
                    if st.button("Esqueci a Senha"):
                        st.session_state['modo_login'] = 'recuperar_senha'
                        st.session_state['temp_usuario'] = usuario
                        st.rerun()
        else:
            st.error("Usuário não encontrado.")

    if st.session_state.get('modo_login') == 'recuperar_senha':
        st.markdown("### 🔑 Recuperação de Senha")
        with st.form("recuperar_senha_form"):
            email = st.text_input("Digite seu email")
            
            if st.form_submit_button("Verificar"):
                usuario = st.session_state.get('temp_usuario')
                if (usuario in st.session_state.usuarios and 
                    st.session_state.usuarios[usuario]['email'].lower() == email.lower()):
                    st.session_state['modo_login'] = 'redefinir_senha'
                    st.rerun()
                else:
                    st.error("Email não corresponde ao cadastrado.")

    elif st.session_state.get('modo_login') == 'redefinir_senha':
        st.markdown("### 🔐 Redefinir Senha")
        with st.form("redefinir_senha_form"):
            nova_senha = st.text_input("Nova Senha", type="password")
            confirma_senha = st.text_input("Confirme a Nova Senha", type="password")
            
            if st.form_submit_button("Redefinir Senha"):
                if nova_senha == confirma_senha:
                    usuario = st.session_state['temp_usuario']
                    st.session_state.usuarios[usuario]['senha'] = nova_senha
                    st.session_state.usuarios[usuario]['primeiro_acesso'] = False
                    save_users()
                    st.success("Senha redefinida com sucesso! Por favor, faça login.")
                    st.session_state.pop('modo_login')
                    st.session_state.pop('temp_usuario')
                    st.rerun()
                else:
                    st.error("As senhas não coincidem.")

def menu_lateral():
    with st.sidebar:
        st.markdown("### Menu")
        st.markdown("---")
        
        # Menu baseado no perfil
        menu_items = ["📊 Dashboard", "📝 Requisições"]
        
        # Adiciona opções extras para administrador e comprador
        if st.session_state['perfil'] in ['administrador', 'comprador']:
            menu_items.extend(["🛒 Cotações", "✈️ Importação", "⚙️ Configurações"])
        
        menu = st.radio(
            "",
            menu_items,
            label_visibility="collapsed"
        )
            
        st.markdown("---")
        st.write(f"👤 Usuário: {st.session_state.get('usuario', '')}")
        
        if st.button("🚪 Sair"):
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
        'FINALIZADA': {'icon': '✓', 'cor': 'rgba(52, 152, 219, 0.7)'},  # Azul
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
                margin-bottom: 10px;
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
            st.markdown('<div class="fixed-metrics">', unsafe_allow_html=True)
            
            # Contadores com ícones
            abertas = len([r for r in requisicoes_filtradas if r['status'] == 'ABERTA'])
            em_andamento = len([r for r in requisicoes_filtradas if r['status'] == 'EM ANDAMENTO'])
            finalizadas = len([r for r in requisicoes_filtradas if r['status'] in ['FINALIZADA', 'RESPONDIDA']])
            recusadas = len([r for r in requisicoes_filtradas if r['status'] == 'RECUSADA'])
            total = len(requisicoes_filtradas)

            st.markdown(f"""
                <div class="status-box" style="background-color: {status_config['ABERTA']['cor']};">
                    <span class="status-icon">{status_config['ABERTA']['icon']}</span>
                    <span class="status-text">Abertas</span>
                    <span class="status-value">{abertas}</span>
                </div>
                <div class="status-box" style="background-color: {status_config['EM ANDAMENTO']['cor']};">
                    <span class="status-icon">{status_config['EM ANDAMENTO']['icon']}</span>
                    <span class="status-text">Em Andamento</span>
                    <span class="status-value">{em_andamento}</span>
                </div>
                <div class="status-box" style="background-color: {status_config['FINALIZADA']['cor']};">
                    <span class="status-icon">{status_config['FINALIZADA']['icon']}</span>
                    <span class="status-text">Finalizadas</span>
                    <span class="status-value">{finalizadas}</span>
                </div>
                <div class="status-box" style="background-color: {status_config['RECUSADA']['cor']};">
                    <span class="status-icon">{status_config['RECUSADA']['icon']}</span>
                    <span class="status-text">Recusadas</span>
                    <span class="status-value">{recusadas}</span>
                </div>
                <div class="status-box" style="background-color: {status_config['TOTAL']['cor']};">
                    <span class="status-icon">{status_config['TOTAL']['icon']}</span>
                    <span class="status-text">Total</span>
                    <span class="status-value">{total}</span>
                </div>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # Coluna do gráfico
    with col_grafico:
        st.markdown("""
            <style>
                [data-testid="stSelectbox"] {
                    width: 200px !important;
                }
                div[data-baseweb="select"] > div {
                    width: 200px !important;
                }
            </style>
        """, unsafe_allow_html=True)

        periodo = st.selectbox(
            "PERÍODO",
            ["ÚLTIMOS 7 DIAS", "HOJE", "ÚLTIMOS 30 DIAS", "ÚLTIMOS 6 MESES", "ÚLTIMOS 12 MESES", "PERSONALIZADO"],
            index=0,
            key="periodo_select"
        )

        if periodo == "PERSONALIZADO":
            col1, col2 = st.columns(2)
            with col1:
                data_inicio = st.date_input(
                    "Data Inicial",
                    format="DD/MM/YYYY"
                )
            with col2:
                data_fim = st.date_input(
                    "Data Final",
                    format="DD/MM/YYYY"
                )

        # Dados para o gráfico
        dados = {
            'Status': ['Abertas', 'Em Andamento', 'Finalizadas', 'Recusadas'],
            'Quantidade': [abertas, em_andamento, finalizadas, recusadas]
        }
        df = pd.DataFrame(dados)

        # Gráfico de barras
        st.bar_chart(
            df,
            x='Status',
            y='Quantidade',
            use_container_width=True
        )

        # Tabela detalhada
        st.markdown("### Requisições Detalhadas")
        if requisicoes_filtradas:
            df_requisicoes = pd.DataFrame([{
                'Número': f"#{req['numero']}",
                'Cliente': req['cliente'],
                'Vendedor': req['vendedor'],
                'Data/Hora': req['data_hora'],
                'Status': req['status'],
                'Comprador': req.get('comprador_responsavel', '-')
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
                st.rerun()
        return

    st.title("Nova Requisição")
    
    col1, col2 = st.columns([3,1])
    with col1:
        cliente = st.text_input("Cliente", key="cliente").upper()
    with col2:
        st.write(f"**Vendedor:** {st.session_state.get('usuario', '')}")

    if 'items_temp' not in st.session_state:
        st.session_state.items_temp = []

    st.markdown("""
    <style>
    .requisicao-table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 0;
        table-layout: fixed;
    }
    .requisicao-table th, .requisicao-table td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: left;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .requisicao-table th {
        background-color: white;
        border: 1px solid #ddd;
        color: #2D2C74;
        font-weight: 500;
        height: 38px;
    }
    .stTextInput > div > div > input {
        border-radius: 4px !important;
        border: 1px solid #ddd !important;
        padding: 8px !important;
        height: 38px !important;
        background-color: white !important;
    }
    div[data-testid="column"] {
        padding: 0 !important;
        margin: 0 !important;
    }
    .stButton button {
        padding: 0 !important;
        height: 32px !important;
        width: 100% !important;
        line-height: 1;
        font-size: 12px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("### Itens da Requisição")

    st.markdown("""
    <table class="requisicao-table">
        <thead>
            <tr>
                <th style="width: 4%">ITEM</th>
                <th style="width: 7%">CÓDIGO</th>
                <th style="width: 15%">CÓDIGO DE FABRICANTE</th>
                <th style="width: 35%">DESCRIÇÃO</th>
                <th style="width: 12%">MARCA</th>
                <th style="width: 4%">QTD</th>
                <th style="width: 6%">AÇÕES</th>
            </tr>
        </thead>
    </table>
    """, unsafe_allow_html=True)

    if st.session_state.items_temp:
        for idx, item in enumerate(st.session_state.items_temp):
            cols = st.columns([0.2, 0.35, 0.75, 1.75, 0.6, 0.2, 0.3])
            editing = st.session_state.get('editing_item') == idx
            
            with cols[0]:
                st.text_input("", value=str(item['item']), disabled=True, key=f"item_show_{idx}", label_visibility="collapsed")
            with cols[1]:
                if editing:
                    item['codigo'] = st.text_input("", value=item['codigo'], key=f"codigo_edit_{idx}", label_visibility="collapsed").upper()
                else:
                    st.text_input("", value=item['codigo'], disabled=True, key=f"codigo_show_{idx}", label_visibility="collapsed")
            with cols[2]:
                if editing:
                    item['cod_fabricante'] = st.text_input("", value=item['cod_fabricante'], key=f"fab_edit_{idx}", label_visibility="collapsed").upper()
                else:
                    st.text_input("", value=item['cod_fabricante'], disabled=True, key=f"fab_show_{idx}", label_visibility="collapsed")
            with cols[3]:
                if editing:
                    item['descricao'] = st.text_input("", value=item['descricao'], key=f"desc_edit_{idx}", label_visibility="collapsed").upper()
                else:
                    st.text_input("", value=item['descricao'], disabled=True, key=f"desc_show_{idx}", label_visibility="collapsed")
            with cols[4]:
                if editing:
                    item['marca'] = st.text_input("", value=item['marca'], key=f"marca_edit_{idx}", label_visibility="collapsed").upper()
                else:
                    st.text_input("", value=item['marca'], disabled=True, key=f"marca_show_{idx}", label_visibility="collapsed")
            with cols[5]:
                if editing:
                    quantidade = st.text_input("", value=str(item['quantidade']), key=f"qtd_edit_{idx}", label_visibility="collapsed")
                    if quantidade.isdigit():
                        item['quantidade'] = int(quantidade)
                else:
                    st.text_input("", value=str(item['quantidade']), disabled=True, key=f"qtd_show_{idx}", label_visibility="collapsed")
            with cols[6]:
                if editing:
                    if st.button("✅", key=f"save_{idx}"):
                        st.session_state.pop('editing_item')
                        st.rerun()
                else:
                    col1, col2 = st.columns([1,1])
                    with col1:
                        if st.button("✏️", key=f"edit_{idx}"):
                            st.session_state['editing_item'] = idx
                            st.rerun()
                    with col2:
                        if st.button("🗑️", key=f"remove_{idx}"):
                            st.session_state.items_temp.pop(idx)
                            for i, item in enumerate(st.session_state.items_temp, 1):
                                item['item'] = i
                            st.rerun()

    # Campo para novo item
    cols = st.columns([0.2, 0.35, 0.75, 1.75, 0.6, 0.2, 0.3])
    proximo_item = len(st.session_state.items_temp) + 1
    
    with cols[0]:
        st.text_input("", value=str(proximo_item), disabled=True, key="item", label_visibility="collapsed")
    with cols[1]:
        codigo = st.text_input("", key="codigo", label_visibility="collapsed").upper()
    with cols[2]:
        cod_fabricante = st.text_input("", key="cod_fab", label_visibility="collapsed").upper()
    with cols[3]:
        descricao = st.text_input("", key="desc", label_visibility="collapsed").upper()
    with cols[4]:
        marca = st.text_input("", key="marca", label_visibility="collapsed").upper()
    with cols[5]:
        quantidade = st.text_input("", key="qtd", label_visibility="collapsed")
    with cols[6]:
        if st.button("➕", key="add"):
            if not descricao:
                st.error("PREENCHIMENTO OBRIGATÓRIO: DESCRIÇÃO")
                return
            if not quantidade or not quantidade.isdigit():
                st.error("PREENCHIMENTO OBRIGATÓRIO: Quantidade (apenas números)")
                return
            
            st.session_state.items_temp.append({
                'item': proximo_item,
                'codigo': codigo,
                'cod_fabricante': cod_fabricante,
                'descricao': descricao,
                'marca': marca,
                'quantidade': int(quantidade),
                'status': 'ABERTA'
            })
            for key in ['codigo', 'cod_fab', 'desc', 'marca', 'qtd']:
                st.session_state[key] = ""
            st.rerun()

    if st.session_state.items_temp:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Enviar Requisição", type="primary", use_container_width=True):
                if not cliente:
                    st.error("PREENCHIMENTO OBRIGATÓRIO: Cliente")
                    return
                
                nova_requisicao = {
                    'numero': st.session_state.next_req_number,
                    'cliente': cliente,
                    'vendedor': st.session_state['usuario'],
                    'data_hora': get_data_hora_brasil(),
                    'status': 'ABERTA',
                    'items': st.session_state.items_temp.copy()
                }
                
                st.session_state.requisicoes.append(nova_requisicao)
                salvar_requisicoes()
                st.session_state.next_req_number += 1
                st.session_state.items_temp = []
                st.success("Requisição enviada com sucesso!")
                st.session_state['modo_requisicao'] = None
                st.rerun()
        
        with col2:
            if st.button("❌ Cancelar Requisição", type="secondary", use_container_width=True):
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

    st.markdown("""
    <style>
    .stTextInput input, .stNumberInput input {
        border: 2px solid #2D2C74 !important;
        border-radius: 4px !important;
        padding: 8px 12px !important;
    }
    .stExpander {
        background-color: white !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 8px !important;
        margin-bottom: 1rem !important;
    }
    .stExpander > div:first-child {
        background-color: #f8f9fa !important;
        border-bottom: 1px solid #e0e0e0 !important;
        padding: 1rem !important;
    }
    .item-container {
        background-color: #f1f8ff;
        padding: 15px;
        border-radius: 6px;
        margin: 10px 0;
        border-left: 4px solid #1B81C5;
    }
    .item-saved {
        background-color: #e8f5e9;
        border-left: 4px solid #4caf50;
    }
    .item-details {
        background-color: #ffffff;
        padding: 10px;
        border-radius: 4px;
        margin-top: 10px;
    }
    .item-details p {
        margin: 5px 0;
        color: #333;
        font-weight: 500;
    }
    .vendedor-view {
        background-color: #f1f8ff;
        padding: 15px;
        border-radius: 6px;
        margin: 10px 0;
        border-left: 4px solid #1B81C5;
    }
    .header-info {
        display: flex;
        justify-content: space-between;
        padding: 15px;
        background-color: #f8f9fa;
        border-radius: 4px;
        margin-bottom: 15px;
    }
    .header-info-group {
        display: flex;
        flex-direction: column;
    }
    .header-info-group p {
        margin: 5px 0;
    }
    .requisicao-table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 15px;
    }
    .requisicao-table th, .requisicao-table td {
        padding: 8px;
        text-align: left;
        border: 1px solid #e0e0e0;
    }
    .requisicao-table th {
        background-color: #f8f9fa;
        font-weight: 500;
        color: #2D2C74;
        white-space: nowrap;
    }
    .requisicao-table td {
        background-color: #ffffff;
    }
    .valor-cell {
        text-align: right;
        white-space: nowrap;
    }
    .prazo-cell {
        text-align: center;
        white-space: nowrap;
    }
    .items-title {
        font-size: 16px;
        font-weight: 600;
        margin: 15px 0;
        color: #2D2C74;
    }
    </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([4,1])
    with col2:
        if st.button("🎯 Nova Requisição", key="nova_req", type="primary"):
            st.session_state['modo_requisicao'] = 'nova'
            st.rerun()

    if st.session_state.get('modo_requisicao') == 'nova':
        nova_requisicao()
    else:
        st.write("Filtrar por Status")
        if st.session_state['perfil'] == 'vendedor':
            default_status = ["ABERTA", "EM ANDAMENTO", "FINALIZADA", "RECUSADA"]
        else:
            default_status = ["ABERTA", "EM ANDAMENTO"]
        
        selected_status = st.multiselect(
            "",
            ["ABERTA", "EM ANDAMENTO", "FINALIZADA", "RECUSADA"],
            default=default_status,
            label_visibility="collapsed"
        )

        requisicoes_visiveis = []
        for req in st.session_state.requisicoes:
            if st.session_state['perfil'] == 'vendedor':
                if req['vendedor'] == st.session_state['usuario']:
                    requisicoes_visiveis.append(req)
            else:
                requisicoes_visiveis.append(req)

        requisicoes_visiveis.sort(key=lambda x: x['numero'], reverse=True)

        for idx, req in enumerate(requisicoes_visiveis):
            if req['status'] in selected_status:
                with st.expander(f"📋 #{req['numero']} - {req['cliente']} ({req['status']})"):
                    st.markdown(f"""
                    <div class="requisicao-container">
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
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown('<div class="items-title">Itens da Requisição</div>', unsafe_allow_html=True)
                    
                    if req['items']:
                        st.markdown("""
                        <table class="requisicao-table">
                        <thead>
                        <tr>
                            <th style="width: 7%">CÓDIGO</th>
                            <th style="width: 15%">CÓDIGO DE FABRICANTE</th>
                            <th style="width: 35%">DESCRIÇÃO</th>
                            <th style="width: 12%">MARCA</th>
                            <th style="width: 4%">QUANTIDADE</th>
                        </tr>
                        </thead>
                        <tbody>
                        """, unsafe_allow_html=True)

                        for item in req['items']:
                            st.markdown(f"""
                            <tr>
                                <td>{item.get('codigo', '-')}</td>
                                <td>{item.get('cod_fabricante', '-')}</td>
                                <td>{item['descricao']}</td>
                                <td>{item.get('marca', 'PC')}</td>
                                <td class="valor-cell">{item['quantidade']}</td>
                            </tr>
                            """, unsafe_allow_html=True)

                        st.markdown("</tbody></table>", unsafe_allow_html=True)

                    if st.session_state['perfil'] in ['administrador', 'comprador'] and req['status'] == 'ABERTA':
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("✅ Aceitar", key=f"aceitar_aberta_{req['numero']}_{idx}", type="primary", use_container_width=True):
                                req['status'] = 'EM ANDAMENTO'
                                req['comprador_responsavel'] = st.session_state['usuario']
                                req['data_hora_aceite'] = get_data_hora_brasil()
                                salvar_requisicoes()
                                st.success("Requisição aceita com sucesso!")
                                st.rerun()
                        with col2:
                            if st.button("❌ Recusar", key=f"recusar_aberta_{req['numero']}_{idx}", type="secondary", use_container_width=True):
                                st.session_state[f'mostrar_justificativa_aberta_{req["numero"]}_{idx}'] = True
                                st.rerun()

                        if st.session_state.get(f'mostrar_justificativa_aberta_{req["numero"]}_{idx}', False):
                            justificativa = st.text_area("Motivo da Recusa", key=f"justificativa_aberta_{req['numero']}_{idx}")
                            if st.button("Confirmar Recusa", key=f"confirmar_recusa_aberta_{req['numero']}_{idx}", type="secondary"):
                                if justificativa.strip():
                                    req['status'] = 'RECUSADA'
                                    req['justificativa_recusa'] = justificativa
                                    req['comprador_responsavel'] = st.session_state['usuario']
                                    req['data_hora_recusa'] = get_data_hora_brasil()
                                    salvar_requisicoes()
                                    st.success("Requisição recusada com sucesso!")
                                    st.rerun()
                                else:
                                    st.error("Por favor, insira uma justificativa para a recusa.")

                    elif st.session_state['perfil'] in ['administrador', 'comprador'] and req['status'] == 'EM ANDAMENTO':
                        for item_idx, item in enumerate(req['items']):
                            with st.container():
                                item_class = 'item-container item-saved' if item.get('salvo') else 'item-container'
                                st.markdown(f"""
                                <div class='{item_class}'>
                                    <h4>Item {item['item']}: {item['descricao']} - Quantidade: {item['quantidade']}</h4>
                                </div>
                                """, unsafe_allow_html=True)

                                col1, col2 = st.columns(2)
                                with col1:
                                    item['custo_unit'] = st.number_input(
                                        f"R$ UNIT Item {item['item']} *",
                                        value=item.get('custo_unit', 0.0),
                                        format="%.2f",
                                        key=f"custo_{req['numero']}_{item['item']}_{idx}"
                                    )
                                with col2:
                                    item['markup'] = st.number_input(
                                        f"% MARKUP Item {item['item']} *",
                                        value=item.get('markup', 0.0),
                                        format="%.2f",
                                        key=f"markup_{req['numero']}_{item['item']}_{idx}"
                                    )

                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    tipo_ipi = st.selectbox(
                                        "Tipo IPI",
                                        ["Percentual", "Valor"],
                                        key=f"tipo_ipi_{req['numero']}_{item['item']}_{idx}"
                                    )
                                    if tipo_ipi == "Percentual":
                                        item['ipi'] = st.number_input(
                                            "% IPI",
                                            value=item.get('ipi', 0.0),
                                            format="%.2f",
                                            key=f"ipi_{req['numero']}_{item['item']}_{idx}"
                                        )
                                        item['ipi_valor'] = (item['custo_unit'] * item['ipi']) / 100
                                    else:
                                        item['ipi_valor'] = st.number_input(
                                            "R$ IPI",
                                            value=item.get('ipi_valor', 0.0),
                                            format="%.2f",
                                            key=f"ipi_valor_{req['numero']}_{item['item']}_{idx}"
                                        )
                                        item['ipi'] = (item['ipi_valor'] / item['custo_unit']) * 100 if item['custo_unit'] > 0 else 0

                                with col2:
                                    tipo_st = st.selectbox(
                                        "Tipo ST",
                                        ["Percentual", "Valor"],
                                        key=f"tipo_st_{req['numero']}_{item['item']}_{idx}"
                                    )
                                    if tipo_st == "Percentual":
                                        item['st'] = st.number_input(
                                            "% ST",
                                            value=item.get('st', 0.0),
                                            format="%.2f",
                                            key=f"st_{req['numero']}_{item['item']}_{idx}"
                                        )
                                        item['st_valor'] = (item['custo_unit'] * item['st']) / 100
                                    else:
                                        item['st_valor'] = st.number_input(
                                            "R$ ST",
                                            value=item.get('st_valor', 0.0),
                                            format="%.2f",
                                            key=f"st_valor_{req['numero']}_{item['item']}_{idx}"
                                        )
                                        item['st'] = (item['st_valor'] / item['custo_unit']) * 100 if item['custo_unit'] > 0 else 0

                                with col3:
                                    item['taxas'] = st.number_input(
                                        "TAXAS",
                                        value=item.get('taxas', 0.0),
                                        format="%.2f",
                                        key=f"taxas_{req['numero']}_{item['item']}_{idx}"
                                    )

                                with col4:
                                    item['prazo_entrega'] = st.text_input(
                                        "Prazo de Entrega *",
                                        value=item.get('prazo_entrega', ''),
                                        key=f"prazo_{req['numero']}_{item['item']}_{idx}"
                                    )

                                item['final_unit'] = item['custo_unit'] + item.get('ipi_valor', 0.0) + item.get('st_valor', 0.0) + item['taxas']
                                item['venda_unit'] = item['final_unit'] * (1 + item['markup']/100)

                                col1, col2, col3 = st.columns([2,2,1])
                                with col1:
                                    st.write(f"R$ FINAL UNIT: {item['final_unit']:.2f}")
                                with col2:
                                    st.write(f"R$ VENDA UNIT: {item['venda_unit']:.2f}")
                                with col3:
                                    if st.button("💾 Salvar Item", key=f"salvar_item_{req['numero']}_{item['item']}_{idx}"):
                                        if item['custo_unit'] > 0 and item['markup'] > 0:
                                            item['salvo'] = True
                                            salvar_requisicoes()
                                            st.success(f"Item {item['item']} salvo com sucesso!")
                                            st.rerun()
                                        else:
                                            st.error("Preencha o valor unitário e markup antes de salvar")

                    if req['status'] in ['RESPONDIDA', 'FINALIZADA']:
                        st.markdown("""
                            <table class="requisicao-table">
                                <thead>
                                    <tr>
                                        <th>CÓDIGO</th>
                                        <th>CÓDIGO DE FABRICANTE</th>
                                        <th>DESCRIÇÃO</th>
                                        <th>MARCA</th>
                                        <th>QUANTIDADE</th>
                                        <th>R$ VENDA UNIT</th>
                                        <th>R$ TOTAL</th>
                                        <th>PRAZO</th>
                                    </tr>
                                </thead>
                                <tbody>
                        """, unsafe_allow_html=True)

                        total_requisicao = 0
                        for item in req['items']:
                            valor_total = item.get('venda_unit', 0) * item['quantidade']
                            total_requisicao += valor_total
                            st.markdown(f"""
                                <tr>
                                    <td>{item.get('codigo', '-')}</td>
                                    <td>{item.get('cod_fabricante', '-')}</td>
                                    <td>{item['descricao']}</td>
                                    <td>{item.get('marca', 'PC')}</td>
                                    <td class="valor-cell">{item['quantidade']}</td>
                                    <td class="valor-cell">R$ {item.get('venda_unit', 0):.2f}</td>
                                    <td class="valor-cell">R$ {valor_total:.2f}</td>
                                    <td class="prazo-cell">{item.get('prazo_entrega', '-')}</td>
                                </tr>
                            """, unsafe_allow_html=True)

                        st.markdown(f"""
                                <tr style="font-weight: bold; background-color: #f8f9fa;">
                                    <td colspan="6" style="text-align: right;">TOTAL DA REQUISIÇÃO:</td>
                                    <td class="valor-cell">R$ {total_requisicao:.2f}</td>
                                    <td></td>
                                </tr>
                            </tbody>
                        </table>
                        """, unsafe_allow_html=True)

                    if st.session_state['perfil'] in ['administrador', 'comprador'] and req['status'] == 'EM ANDAMENTO':
                        todos_itens_salvos = all(item.get('salvo', False) for item in req['items'])
                        algum_item_salvo = any(item.get('salvo', False) for item in req['items'])

                        col1, col2 = st.columns([1,1])
                        with col1:
                            if todos_itens_salvos:
                                if st.button("✅ Responder", key=f"responder_{req['numero']}", type="primary", use_container_width=True):
                                    req['status'] = 'RESPONDIDA'
                                    salvar_requisicoes()
                                    st.success("Requisição respondida com sucesso!")
                                    st.rerun()
                            elif algum_item_salvo:
                                st.info("Complete o preenchimento de todos os itens para responder")

                        with col2:
                            if st.button("❌ Recusar", key=f"recusar_{req['numero']}_{idx}", type="secondary", use_container_width=True):
                                st.rerun()

                        if st.session_state.get(f'mostrar_justificativa_{req["numero"]}', False):
                            justificativa = st.text_area("Motivo da Recusa", key=f"justificativa_{req['numero']}")
                            if st.button("Confirmar Recusa", key=f"confirmar_recusa_{req['numero']}", type="secondary"):
                                if justificativa.strip():
                                    req['status'] = 'RECUSADA'
                                    req['justificativa_recusa'] = justificativa
                                    salvar_requisicoes()
                                    st.success("Requisição recusada com sucesso!")
                                    st.rerun()
                                else:
                                    st.error("Por favor, insira uma justificativa para a recusa.")

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
        if st.session_state['perfil'] == 'administrador':
            with col3:
                if st.button("⚙️ Sistema", type="primary", use_container_width=True):
                    st.session_state['config_modo'] = 'sistema'
                    st.rerun()

        if st.session_state.get('config_modo') == 'sistema' and st.session_state['perfil'] == 'administrador':
            st.subheader("Configurações do Sistema")
            
            if 'config_sistema' not in st.session_state:
                st.session_state.config_sistema = {
                    'layout_tabelas': {
                        'item': '4%',
                        'codigo': '7%',
                        'cod_fabricante': '15%',
                        'descricao': '35%',
                        'marca': '14%',
                        'qtd': '6%'
                    }
                }

            st.markdown("### Dimensões das Colunas")
            
            # Prévia do layout atual
            st.markdown("""
            <style>
            .preview-table {
                width: 100%;
                border-collapse: collapse;
                margin: 15px 0;
                table-layout: fixed;
            }
            .preview-table th, .preview-table td {
                padding: 8px;
                text-align: left;
                border: 1px solid #ddd;
            }
            .preview-table th {
                background-color: #f8f9fa;
                color: #2D2C74;
                font-weight: 500;
            }
            </style>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                item_width = st.slider("Item", 3, 10, 4, format="%d%%", key="item_width")
                codigo_width = st.slider("Código", 5, 20, 7, format="%d%%", key="codigo_width")
                cod_fab_width = st.slider("Código Fabrficante", 10, 30, 15, format="%d%%", key="cod_fab_width")
            with col2:
                desc_width = st.slider("Descrição", 20, 50, 35, format="%d%%", key="desc_width")
                marca_width = st.slider("Marca", 10, 25, 14, format="%d%%", key="marca_width")
                qtd_width = st.slider("Quantidade", 5, 15, 6, format="%d%%", key="qtd_width")

            # Prévia da tabela
            st.markdown("### Prévia do Layout")
            st.markdown(f"""
            <table class="preview-table">
                <thead>
                    <tr>
                        <th style="width: {item_width}%">ITEM</th>
                        <th style="width: {codigo_width}%">CÓDIGO</th>
                        <th style="width: {cod_fab_width}%">CÓDIGO DE FABRICANTE</th>
                        <th style="width: {desc_width}%">DESCRIÇÃO</th>
                        <th style="width: {marca_width}%">MARCA</th>
                        <th style="width: {qtd_width}%">QTD</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>1</td>
                        <td>123</td>
                        <td>ABCD</td>
                        <td>COMPRESSOR DANFOSS</td>
                        <td>DANFOSS</td>
                        <td>12</td>
                    </tr>
                    <tr>
                        <td>2</td>
                        <td>12</td>
                        <td>1235EFFE</td>
                        <td>EFFWEWEF</td>
                        <td>1</td>
                        <td>1</td>
                    </tr>
                </tbody>
            </table>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Aplicar Alterações", type="primary", use_container_width=True):
                    st.session_state.config_sistema['layout_tabelas'] = {
                        'item': f"{item_width}%",
                        'codigo': f"{codigo_width}%",
                        'cod_fabricante': f"{cod_fab_width}%",
                        'descricao': f"{desc_width}%",
                        'marca': f"{marca_width}%",
                        'qtd': f"{qtd_width}%"
                    }
                    salvar_configuracoes()
                    st.success("Configurações aplicadas com sucesso!")
                    st.rerun()
            
            with col2:
                if st.button("↩️ Reverter para Padrão", type="secondary", use_container_width=True):
                    st.session_state.config_sistema['layout_tabelas'] = {
                        'item': '4%',
                        'codigo': '7%',
                        'cod_fabricante': '15%',
                        'descricao': '35%',
                        'marca': '14%',
                        'qtd': '6%'
                    }
                    salvar_configuracoes()
                    st.success("Configurações revertidas para o padrão!")
                    st.rerun()

        elif st.session_state.get('config_modo') == 'usuarios':
            # Código existente para gerenciamento de usuários
            pass

        elif st.session_state.get('config_modo') == 'perfis':
            # Código existente para gerenciamento de perfis
            pass

    else:
        st.info("Acesso restrito ao administrador e comprador")

def main():
    if 'usuario' not in st.session_state:
        tela_login()
    else:
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