import re
import json
from typing import Dict, Any
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage, FunctionMessage
from langchain.chains import RetrievalQA
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from agent.states import ChatState
from agent.services import (
    consultar_saldo, 
    realizar_transferencia, 
    buscar_transacoes, 
    pagar_boleto, 
    pagar_cartao, 
    analisar_comportamento
)

def classificar_intencao(state: ChatState) -> ChatState:
    """Versão aprimorada baseada em regras com melhor extração de entidades."""
    # Obtém a última mensagem do usuário
    mensagem = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            mensagem = msg.content.lower()
            break
    
    # Padrões mais sofisticados de dúvidas/perguntas
    padrao_duvida = any(palavra in mensagem for palavra in [
        "?", "como", "o que é", "explique", "qual", "quando", "por que", 
        "dúvida", "pergunta", "pode me informar", "gostaria de saber",
        "necessário", "necessarios", "documentos", "documentação"
    ]) or mensagem.isupper()
    
    # Regex mais precisos para extração de valores
    valor_regex = r'R?\$?\s?(\d+(?:[.,]\d+)?)'
    periodo_regex = r'últim[oa]s?\s+(\d+)'
    
    # Classificação baseada em padrões de linguagem natural
    if any(palavra in mensagem for palavra in ["saldo", "quanto tenho", "disponível", "sobrou", "restante"]):
        intencao = "consulta_saldo"
        parametros = {}
    elif any(palavra in mensagem for palavra in ["transferir", "transferência", "enviar", "mandar", "depositar", "passar", "pix"]):
        valor_match = re.search(valor_regex, mensagem)
        valor = float(valor_match.group(1).replace(',', '.')) if valor_match else 100
        
        # Busca por destinatário com melhor reconhecimento
        destino_id = "2"  # Default: Maria
        if "maria" in mensagem:
            destino_id = "2"
        elif "carlos" in mensagem or "oliveira" in mensagem:
            destino_id = "3"
        
        parametros = {"valor": valor, "destino_id": destino_id}
        intencao = "transferencia"
    elif any(palavra in mensagem for palavra in ["transações", "extrato", "movimentações", "histórico", "atividade"]):
        limite = 5
        limite_match = re.search(periodo_regex, mensagem)
        if limite_match:
            limite = int(limite_match.group(1))
        
        parametros = {"limite": limite}
        intencao = "extrato"
    elif any(palavra in mensagem for palavra in ["boleto", "conta", "fatura", "água", "luz", "energia", "internet", "telefone"]) and not padrao_duvida:
        valor_match = re.search(valor_regex, mensagem)
        valor = float(valor_match.group(1).replace(',', '.')) if valor_match else 150
        
        # Identificação mais inteligente do tipo de boleto
        codigo = "12345678901234567890"
        if "água" in mensagem:
            codigo = "76543210987654321098"
        elif "luz" in mensagem or "energia" in mensagem:
            codigo = "89123456789012345678"
        elif "internet" in mensagem:
            codigo = "45678901234567890123"
        elif "telefone" in mensagem or "celular" in mensagem:
            codigo = "32109876543210987654"
        
        parametros = {"valor": valor, "codigo_barras": codigo}
        intencao = "pagamento_boleto"
    elif any(palavra in mensagem for palavra in ["cartão", "comprar", "compra", "crédito", "débito"]) and not padrao_duvida:
        valor_match = re.search(valor_regex, mensagem)
        valor = float(valor_match.group(1).replace(',', '.')) if valor_match else 80
        
        # Identificar estabelecimento com mais variações
        estabelecimento = "Estabelecimento"
        if any(palavra in mensagem for palavra in ["restaurante", "lanchonete", "comida"]):
            estabelecimento = "Restaurante"
        elif any(palavra in mensagem for palavra in ["mercado", "supermercado", "compras"]):
            estabelecimento = "Supermercado"
        elif any(palavra in mensagem for palavra in ["farmácia", "remédio", "medicamento"]):
            estabelecimento = "Farmácia"
        elif any(palavra in mensagem for palavra in ["posto", "gasolina", "combustível"]):
            estabelecimento = "Posto de Combustível"
        
        parametros = {"valor": valor, "estabelecimento": estabelecimento, "cartao_id": "1"}
        intencao = "pagamento_cartao"
    elif any(palavra in mensagem for palavra in ["perfil", "comportamento", "análise", "gastos", "financeiro"]):
        intencao = "perfil"
        parametros = {}
    # Priorizar dúvidas sobre outras intenções
    elif padrao_duvida:
        intencao = "duvida"
        parametros = {"query": mensagem}
    else:
        intencao = "outro"
        parametros = {}
    
    # Adiciona o resultado ao estado
    result = {"intencao": intencao, "parametros": parametros}
    state["messages"].append(
        FunctionMessage(
            content=json.dumps(result),
            name="classificador_intencao"
        )
    )
    
    # Define o próximo nó
    state["next"] = intencao
    
    # Adicionar logs para debugging
    print(f"MENSAGEM CLASSIFICADA: '{mensagem}'")
    print(f"INTENÇÃO DETECTADA: {intencao} com parametros: {parametros}")
    
    return state

def processar_saldo(state: ChatState) -> ChatState:
    """Processa consultas de saldo com personalização."""
    cliente_id = state["cliente_id"]
    resultado = consultar_saldo(cliente_id)
    
    state["messages"].append(
        FunctionMessage(
            content=json.dumps(resultado),
            name="consultar_saldo"
        )
    )
    
    # Gera resposta personalizada com base no resultado
    if resultado["status"] == "sucesso":
        # Verificar se o saldo está baixo para dar um aviso
        saldo = float(resultado["saldo"])
        if saldo < 500:
            resposta = f"O saldo atual da conta {resultado['conta']} de {resultado['nome']} é de R$ {saldo:.2f}. Atenção: seu saldo está baixo."
        elif saldo > 5000:
            resposta = f"Boas notícias! O saldo atual da conta {resultado['conta']} é de R$ {saldo:.2f}. Você tem um bom valor disponível."
        else:
            resposta = f"O saldo atual da conta {resultado['conta']} de {resultado['nome']} é de R$ {saldo:.2f}."
    else:
        resposta = f"Desculpe, não foi possível consultar o saldo: {resultado['mensagem']}"
    
    state["messages"].append(AIMessage(content=resposta))
    
    return state

def processar_transferencia(state: ChatState) -> ChatState:
    """Processa transferências com validações aprimoradas."""
    messages = state["messages"]
    cliente_id = state["cliente_id"]
    
    # Extrai parâmetros da classificação de intenção
    for msg in reversed(messages):
        if isinstance(msg, FunctionMessage) and msg.name == "classificador_intencao":
            dados = json.loads(msg.content)
            parametros = dados["parametros"]
            break
    
    valor = float(parametros.get("valor", 0))
    destino_id = parametros.get("destino_id", "")
    
    # Validações adicionais
    if valor <= 0:
        state["messages"].append(AIMessage(
            content="Por favor, informe um valor válido para a transferência maior que zero."
        ))
        return state
    
    # Verificar se o destino existe
    from agent.services import clientes
    if destino_id not in clientes:
        state["messages"].append(AIMessage(
            content="Desculpe, não encontrei o destinatário especificado. Por favor, verifique se o nome está correto."
        ))
        return state
    
    # Realiza a transferência
    resultado = realizar_transferencia(cliente_id, destino_id, valor)
    
    state["messages"].append(
        FunctionMessage(
            content=json.dumps(resultado),
            name="realizar_transferencia"
        )
    )
    
    # Gera resposta final com base no resultado
    if resultado["status"] == "sucesso":
        nome_destino = clientes.get(destino_id, {}).get("nome", "destinatário")
        resposta = f"Transferência de R$ {valor:.2f} para {nome_destino} realizada com sucesso. Seu novo saldo é R$ {resultado['novo_saldo']:.2f}."
    else:
        resposta = f"Desculpe, não foi possível realizar a transferência: {resultado['mensagem']}"
    
    state["messages"].append(AIMessage(content=resposta))
    
    return state

def processar_extrato(state: ChatState) -> ChatState:
    """Processa consultas de extrato com melhor formatação."""
    messages = state["messages"]
    cliente_id = state["cliente_id"]
    
    # Extrai parâmetros da classificação de intenção
    for msg in reversed(messages):
        if isinstance(msg, FunctionMessage) and msg.name == "classificador_intencao":
            dados = json.loads(msg.content)
            parametros = dados["parametros"]
            break
    
    limite = int(parametros.get("limite", 5))
    
    # Busca as transações
    resultado = buscar_transacoes(cliente_id, limite)
    
    state["messages"].append(
        FunctionMessage(
            content=json.dumps(resultado),
            name="buscar_transacoes"
        )
    )
    
    # Gera resposta final com base no resultado
    if resultado["status"] == "sucesso" and resultado["transacoes"]:
        transacoes = resultado["transacoes"]
        num_transacoes = len(transacoes)
        
        resposta = f"Aqui estão suas últimas {num_transacoes} transações:\n\n"
        
        # Função para formatar transações de forma mais clara
        def formatar_transacao(t):
            data = datetime.fromisoformat(t["data"]).strftime("%d/%m/%Y %H:%M")
            
            if t.get("tipo") == "transferência" and "destino" in t and "valor" in t:
                from agent.services import clientes
                if t["destino"] in clientes:
                    return f"- {data}: Transferência de R$ {t['valor']:.2f} para {clientes[t['destino']]['nome']}"
                else:
                    return f"- {data}: Transferência de R$ {t['valor']:.2f} para conta não identificada"
            elif t.get("tipo") == "pagamento_boleto" and "valor" in t:
                return f"- {data}: Pagamento de boleto no valor de R$ {t['valor']:.2f}"
            elif t.get("tipo") == "pagamento_cartao" and "valor" in t and "estabelecimento" in t:
                return f"- {data}: Compra de R$ {t['valor']:.2f} em {t['estabelecimento']}"
            else:
                resultado = f"- {data}: {t.get('tipo', 'Transação').capitalize()} "
                if "valor" in t:
                    resultado += f"de R$ {t['valor']:.2f}"
                return resultado
        
        # Formatar cada transação
        transacoes_formatadas = [formatar_transacao(t) for t in transacoes]
        resposta += "\n".join(transacoes_formatadas)
        
        # Adicionar resumo
        total_gastos = sum(t.get("valor", 0) for t in transacoes)
        resposta += f"\n\nTotal movimentado: R$ {total_gastos:.2f}"
        
    elif resultado["status"] == "sucesso" and not resultado["transacoes"]:
        resposta = "Você ainda não possui transações registradas."
    else:
        resposta = "Desculpe, não foi possível recuperar seu extrato."
    
    state["messages"].append(AIMessage(content=resposta))
    
    return state

def processar_pagamento_boleto(state: ChatState) -> ChatState:
    messages = state["messages"]
    cliente_id = state["cliente_id"]
    
    # Extrai parâmetros da classificação de intenção
    for msg in reversed(messages):
        if isinstance(msg, FunctionMessage) and msg.name == "classificador_intencao":
            dados = json.loads(msg.content)
            parametros = dados["parametros"]
            break
    
    codigo_barras = parametros.get("codigo_barras", "")
    valor = float(parametros.get("valor", 0))
    
    # Validações adicionais
    if valor <= 0:
        state["messages"].append(AIMessage(
            content="Por favor, informe um valor válido para o pagamento maior que zero."
        ))
        return state
    
    # Determinar o tipo de conta a partir do código de barras
    tipo_conta = "boleto"
    if codigo_barras.startswith("765"):
        tipo_conta = "água"
    elif codigo_barras.startswith("891"):
        tipo_conta = "energia"
    elif codigo_barras.startswith("456"):
        tipo_conta = "internet"
    elif codigo_barras.startswith("321"):
        tipo_conta = "telefone"
    
    # Realiza o pagamento
    resultado = pagar_boleto(cliente_id, codigo_barras, valor)
    
    state["messages"].append(
        FunctionMessage(
            content=json.dumps(resultado),
            name="pagar_boleto"
        )
    )
    
    # Gera resposta final com base no resultado
    if resultado["status"] == "sucesso":
        resposta = f"Pagamento da conta de {tipo_conta} no valor de R$ {valor:.2f} realizado com sucesso. Seu novo saldo é R$ {resultado['novo_saldo']:.2f}."
    else:
        resposta = f"Desculpe, não foi possível realizar o pagamento: {resultado['mensagem']}"
    
    state["messages"].append(AIMessage(content=resposta))
    
    return state

def processar_pagamento_cartao(state: ChatState) -> ChatState:
    messages = state["messages"]
    cliente_id = state["cliente_id"]
    
    # Extrai parâmetros da classificação de intenção
    for msg in reversed(messages):
        if isinstance(msg, FunctionMessage) and msg.name == "classificador_intencao":
            dados = json.loads(msg.content)
            parametros = dados["parametros"]
            break
    
    estabelecimento = parametros.get("estabelecimento", "")
    valor = float(parametros.get("valor", 0))
    cartao_id = parametros.get("cartao_id", "1")  # Default para o primeiro cartão
    
    # Validações adicionais
    if valor <= 0:
        state["messages"].append(AIMessage(
            content="Por favor, informe um valor válido para a compra maior que zero."
        ))
        return state
    
    # Verifica limite do cartão
    from agent.services import cartoes
    cartao = cartoes.get(cartao_id, {})
    limite_disponivel = cartao.get("limite", 0) - cartao.get("fatura_atual", 0)
    
    if valor > limite_disponivel:
        state["messages"].append(AIMessage(
            content=f"Desculpe, seu limite disponível de R$ {limite_disponivel:.2f} é insuficiente para esta compra de R$ {valor:.2f}."
        ))
        return state
    
    # Realiza o pagamento
    resultado = pagar_cartao(cliente_id, estabelecimento, valor, cartao_id)
    
    state["messages"].append(
        FunctionMessage(
            content=json.dumps(resultado),
            name="pagar_cartao"
        )
    )
    
    # Gera resposta final com base no resultado
    if resultado["status"] == "sucesso":
        # Calcular novo limite disponível
        novo_limite_disponivel = cartao.get("limite", 0) - resultado["fatura_atual"]
        
        resposta = (
            f"Compra de R$ {valor:.2f} em {estabelecimento} realizada com sucesso.\n"
            f"Sua fatura atual é de R$ {resultado['fatura_atual']:.2f}.\n"
            f"Limite disponível: R$ {novo_limite_disponivel:.2f}"
        )
    else:
        resposta = f"Desculpe, não foi possível realizar o pagamento: {resultado['mensagem']}"
    
    state["messages"].append(AIMessage(content=resposta))
    
    return state

def processar_perfil(state: ChatState) -> ChatState:
    """Processa análise de perfil com recomendações personalizadas."""
    cliente_id = state["cliente_id"]
    
    # Analisa o comportamento do cliente
    resultado = analisar_comportamento(cliente_id)
    
    state["messages"].append(
        FunctionMessage(
            content=json.dumps(resultado),
            name="analisar_comportamento"
        )
    )
    
    # Gera resposta final com base no resultado
    if resultado["status"] == "sucesso":
        resposta = f"# Análise do seu Perfil Financeiro\n\n"
        
        # Adiciona o perfil descritivo gerado com mais detalhes
        resposta += f"## Perfil do Cliente\n{resultado['perfil_descritivo']}\n\n"
        
        # Resumo financeiro
        resposta += f"## Resumo Financeiro\n"
        resposta += f"- Total gasto: R$ {resultado['total_gastos']:.2f}\n"
        resposta += f"- Número de transações: {resultado['num_transacoes']}\n"
        resposta += f"- Valor médio por transação: R$ {resultado['valor_medio_transacao']:.2f}\n\n"
        
        # Adiciona informações sobre as contas pagas com análise
        if 'principais_categorias_boletos' in resultado and resultado['principais_categorias_boletos']:
            resposta += "## Despesas Fixas\n"
            for categoria, info in resultado['principais_categorias_boletos'].items():
                resposta += f"- {categoria}: {info['quantidade']} pagamentos, total de R$ {info['valor']:.2f}\n"
            resposta += "\n"
        
        # Adiciona informações sobre os estabelecimentos frequentados com análise
        if 'principais_categorias_estabelecimentos' in resultado and resultado['principais_categorias_estabelecimentos']:
            resposta += "## Compras com Cartão\n"
            for categoria, info in resultado['principais_categorias_estabelecimentos'].items():
                resposta += f"- {categoria}: {info['quantidade']} compras, total de R$ {info['valor']:.2f}\n"
            resposta += "\n"
        
        # Adicionar recomendações personalizadas
        resposta += "## Recomendações Personalizadas\n"
        
        # Valor médio de transação
        if resultado['valor_medio_transacao'] > 500:
            resposta += "- Suas transações têm valor médio alto. Considere avaliar cada gasto maior para garantir que está dentro do orçamento.\n"
        
        # Frequência de uso
        if resultado['num_transacoes'] > 10:
            resposta += "- Você realiza muitas transações. Considere agrupar pagamentos para ter melhor controle.\n"
        
        # Baseado no perfil
        if "elevado" in resultado["perfil_descritivo"]:
            resposta += "- Seu perfil de gastos é elevado. Recomendamos avaliar oportunidades de investimento para maximizar seus recursos.\n"
        elif "conservador" in resultado["perfil_descritivo"]:
            resposta += "- Seu perfil conservador indica potencial para investimentos de maior rendimento. Consulte nosso gerente de investimentos.\n"
        
    else:
        resposta = resultado["mensagem"]
    
    state["messages"].append(AIMessage(content=resposta))
    
    return state

# Esta é uma versão parcial do arquivo nodes.py focada apenas na correção da função processar_duvida
# Substitua apenas esta função, mantendo o resto do arquivo como está

def processar_duvida(state: ChatState, vectorstore=None) -> ChatState:
    """Processa dúvidas usando RAG aprimorado com a base de FAQs."""
    from langchain.chains import RetrievalQA
    from langchain_core.prompts import ChatPromptTemplate
    
    messages = state["messages"]
    cliente_id = state["cliente_id"]
    
    # Obter informações do cliente para personalização
    from agent.services import clientes
    cliente_info = clientes.get(cliente_id, {})
    
    # Extrai a última mensagem do usuário para usar como query
    query = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            query = msg.content
            break
    
    # Log detalhado para debugging
    print(f"QUERY PARA RAG: '{query}'")
    print(f"VECTORSTORE DISPONÍVEL: {vectorstore is not None}")
    
    try:
        # Verificar se o vectorstore existe
        if vectorstore is None:
            print("Vectorstore não disponível - não é possível processar a consulta")
            raise ValueError("Vectorstore não disponível")
        
        # Configurar o retriever com mais documentos e filtro de similaridade mais baixo
        retriever = vectorstore.as_retriever(
            search_kwargs={"k": 5, "score_threshold": 0.2}
        )
        
        # Usar um prompt que force a usar informações dos documentos
        custom_prompt = ChatPromptTemplate.from_template("""
        Você é um assistente bancário especializado. Sua tarefa é responder a perguntas dos clientes
        usando APENAS as informações fornecidas nos documentos de referência abaixo.
        
        Informações do cliente:
        Nome: {nome}
        Conta: {conta}
        
        Documentos de referência:
        {context_str}
        
        Pergunta do cliente: {question}
        
        Instruções importantes:
        1. Responda com base APENAS nas informações dos documentos fornecidos.
        2. Se a informação não estiver nos documentos, diga "Não encontrei informações sobre isso nos documentos disponíveis" e ofereça uma orientação geral.
        3. NÃO INVENTE INFORMAÇÕES que não estejam nos documentos.
        4. Cite as partes relevantes dos documentos na sua resposta.
        5. Mantenha um tom profissional e prestativo.
        
        Resposta:
        """)
        
        # Usar o modelo Groq para processamento
        llm = ChatGroq(model="llama3-70b-8192", temperature=0)
        
        # Criar chain de QA configurada para forçar o uso dos documentos
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            chain_type_kwargs={
                "prompt": custom_prompt,
                "verbose": True
            },
            return_source_documents=True
        )
        
        # Executar a consulta com parâmetros explícitos
        resultado = qa_chain.invoke({
            "question": query,
            "nome": cliente_info.get("nome", "Cliente"),
            "conta": cliente_info.get("conta", "")
        })
        
        # Verificar e formatar o resultado
        if isinstance(resultado, dict) and "result" in resultado:
            resposta = resultado["result"]
            
            # Verificar se documentos foram retornados
            docs = resultado.get("source_documents", [])
            if docs:
                # Log dos documentos recuperados
                print(f"DOCUMENTOS RECUPERADOS: {len(docs)}")
                for i, doc in enumerate(docs[:3]):
                    print(f"DOC {i+1}: {doc.page_content[:100]}...")
                
                # Adicionar referência mais explícita
                if not "não encontrei informações" in resposta.lower():
                    resposta += "\n\nEsta resposta foi baseada em documentos oficiais do banco."
            else:
                print("NENHUM DOCUMENTO RELEVANTE ENCONTRADO")
                resposta = "Não encontrei informações específicas sobre isso nos documentos disponíveis. Recomendo entrar em contato com um de nossos gerentes para obter orientações precisas."
        else:
            resposta = "Não consegui encontrar informações relevantes sobre sua pergunta. Por favor, entre em contato com um de nossos atendentes para obter orientações específicas."
    
    except Exception as e:
        import traceback
        print(f"ERRO AO PROCESSAR DÚVIDA: {e}")
        print(traceback.format_exc())
        resposta = (
            "Desculpe, ocorreu um erro técnico ao processar sua consulta. "
            "Por favor, reformule sua pergunta ou entre em contato com o suporte."
        )
    
    # Adicionar resposta ao estado
    state["messages"].append(AIMessage(content=resposta))
    
    # Log da resposta final
    print(f"RESPOSTA FINAL RAG: {resposta[:150]}...")
    
    return state

def responder_generico(state: ChatState) -> ChatState:
    """Responde a perguntas gerais que não são tratadas por outras funções, com mais personalização."""
    messages = state["messages"]
    cliente_id = state["cliente_id"]
    
    # Obter informações do cliente para personalização
    from agent.services import clientes
    cliente_info = clientes.get(cliente_id, {})
    
    llm = ChatGroq(model="llama3-70b-8192", temperature=0)
    
    # Prompt aprimorado com mais contexto e personalização
    generic_prompt = ChatPromptTemplate.from_messages([
        ("system", f"""Você é um assistente bancário amigável e profissional do FourBank. 
        Seu objetivo é atender o cliente {cliente_info.get('nome', 'Cliente')} de forma personalizada.
        
        Informações do cliente:
        - Nome: {cliente_info.get('nome', 'Cliente')}
        - Conta: {cliente_info.get('conta', 'N/A')}
        - Saldo Atual: R$ {cliente_info.get('saldo', 0):.2f}
        
        Diretrizes para suas respostas:
        1. Seja cordial e profissional, tratando o cliente pelo nome
        2. Responda às perguntas de forma clara e concisa
        3. Não forneça informações específicas sobre transações a menos que explicitamente obtidas através de funções
        4. Sugira funcionalidades relevantes do banco quando apropriado
        5. Para consultas específicas, oriente o cliente a usar comandos diretos como "Mostrar saldo" ou "Transferir para Maria"
        6. Mantenha um tom prestativo e positivo
        
        Serviços disponíveis para sugerir:
        - Consulta de saldo
        - Transferências
        - Extrato de conta
        - Pagamento de boletos
        - Compras com cartão
        - Análise de perfil financeiro
        """),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}")
    ])
    
    # Extrai a última mensagem do usuário
    ultima_mensagem = None
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            ultima_mensagem = msg.content
            break
    
    # Analisa o contexto das mensagens recentes para personalização
    temas_recentes = []
    for msg in messages[-5:]:
        if isinstance(msg, HumanMessage) and hasattr(msg, 'content'):
            content = msg.content.lower()
            # Identificar temas na conversa
            if any(word in content for word in ["investir", "investimento", "aplicar", "rendimento"]):
                temas_recentes.append("investimentos")
            elif any(word in content for word in ["empréstimo", "crédito", "financiamento", "emprestar"]):
                temas_recentes.append("empréstimos")
            elif any(word in content for word in ["cartão", "crédito", "comprar", "compra"]):
                temas_recentes.append("cartões")
    
    if ultima_mensagem:
        # Filtra as mensagens anteriores para histórico
        history = []
        for msg in messages[-5:]:  # Usar as últimas 5 mensagens para mais contexto
            if isinstance(msg, HumanMessage):
                history.append(("human", msg.content))
            elif isinstance(msg, AIMessage):
                history.append(("ai", msg.content))
        
        # Invoca o modelo para gerar uma resposta
        resposta = generic_prompt.format_messages(
            history=history,
            input=ultima_mensagem
        ) | llm
        
        conteudo_resposta = resposta.content
        
        # Adicionar sugestões personalizadas com base nos temas detectados
        if temas_recentes:
            sugestoes = "\n\nBaseado no nosso diálogo, talvez você queira saber mais sobre:"
            
            if "investimentos" in temas_recentes:
                sugestoes += "\n- Nossas opções de investimento com rendimento a partir de 100% do CDI"
            if "empréstimos" in temas_recentes:
                sugestoes += "\n- Empréstimos com taxas a partir de 1,99% ao mês"
            if "cartões" in temas_recentes:
                sugestoes += "\n- Nossos cartões sem anuidade com programa de pontos"
                
            conteudo_resposta += sugestoes
        
        # Adiciona a resposta ao estado
        state["messages"].append(AIMessage(content=conteudo_resposta))
    
    return state