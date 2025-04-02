from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from agent.states import ChatState
from agent.nodes import (
    classificar_intencao,
    processar_saldo,
    processar_transferencia,
    processar_extrato,
    processar_pagamento_boleto,
    processar_pagamento_cartao,
    processar_perfil,
    processar_duvida,
    responder_generico
)

# from agent.mcp_client import MCPAgent
from agent.mcp_node_client import MCPAgent

def create_agent_graph(vectorstore=None):
    """Cria o grafo do agente de banking."""
    # Configuração do modelo LLM usando Groq
    llm = ChatGroq(
        model="llama3-70b-8192",
        temperature=0
    )
    
    # Inicializa o cliente MCP
    mcp_agent = MCPAgent(vectorstore)
    
    # Função para processar consultas via MCP
    def process_with_mcp(state: ChatState):
        return mcp_agent.process_state(state)
    
    # Roteador baseado na intenção
    def router(state: ChatState):
        return state["next"]
    
    # Função para processar dúvidas com o vectorstore
    def process_duvida_with_vectorstore(state: ChatState):
        return processar_duvida(state, vectorstore)
    
    # Configuração do grafo
    builder = StateGraph(ChatState)
    
    # Define os nós do grafo
    builder.add_node("classificador_intencao", classificar_intencao)
    builder.add_node("consulta_saldo", processar_saldo)
    builder.add_node("transferencia", processar_transferencia)
    builder.add_node("extrato", processar_extrato)
    builder.add_node("pagamento_boleto", processar_pagamento_boleto)
    builder.add_node("pagamento_cartao", processar_pagamento_cartao)
    builder.add_node("perfil", processar_perfil)
    builder.add_node("duvida", process_duvida_with_vectorstore)
    builder.add_node("outro", responder_generico)
    builder.add_node("mcp", process_with_mcp)  # Adiciona o nó MCP para integração com a API bancária
    
    # Define o fluxo do grafo
    builder.set_entry_point("classificador_intencao")
    builder.add_conditional_edges(
        "classificador_intencao",
        router,
        {
            "consulta_saldo": "consulta_saldo",
            "transferencia": "transferencia",
            "extrato": "extrato",
            "pagamento_boleto": "pagamento_boleto",
            "pagamento_cartao": "pagamento_cartao",
            "perfil": "perfil",
            "duvida": "duvida",
            "outro": "outro",
            "mcp": "mcp"     # Rota para o processamento MCP
        }
    )
    
    # Define os nós finais
    builder.add_edge("consulta_saldo", END)
    builder.add_edge("transferencia", END)
    builder.add_edge("extrato", END)
    builder.add_edge("pagamento_boleto", END)
    builder.add_edge("pagamento_cartao", END)
    builder.add_edge("perfil", END)
    builder.add_edge("duvida", END)
    builder.add_edge("outro", END)
    builder.add_edge("mcp", END)
    
    # Constrói o grafo
    graph = builder.compile()
    
    return graph

def create_agent(cliente_id, vectorstore=None):
    """Cria um agente para um cliente específico."""
    from agent.services import clientes
    from langchain_core.messages import AIMessage
    import uuid
    from datetime import datetime
    
    # Configuração da classe ChatAgent para encapsular o grafo
    class ChatAgent:
        def __init__(self, cliente_id, vectorstore):
            self.graph = create_agent_graph(vectorstore)
            self.initial_state = {
                "messages": [
                    AIMessage(content=f"Olá, {clientes[cliente_id]['nome']}! Como posso ajudar você hoje?")
                ],
                "cliente_id": cliente_id,
                "next": "",
                "context": {
                    "last_access": datetime.now().isoformat(),
                    "session_id": str(uuid.uuid4()),
                    "conversation_topics": []
                }
            }
            
        def invoke(self, message):
            # Criar uma cópia do estado inicial
            state = dict(self.initial_state)
            
            # Adicionar a mensagem atual
            from langchain_core.messages import HumanMessage
            state["messages"].append(HumanMessage(content=message))
            
            # Atualizar contexto de conversa
            topics = self._extract_topics(message)
            if topics:
                state["context"]["conversation_topics"].extend(topics)
                # Manter apenas os 5 tópicos mais recentes
                state["context"]["conversation_topics"] = state["context"]["conversation_topics"][-5:]
            
            # Executar o grafo
            result = self.graph.invoke(state)
            
            # Atualizar o estado para a próxima iteração
            self.initial_state = result
            
            # Retornar a última mensagem do assistente
            for msg in reversed(result["messages"]):
                if isinstance(msg, AIMessage):
                    return msg.content
            
            return "Desculpe, não consegui processar sua solicitação."
        
        def _extract_topics(self, message):
            """Extrai tópicos básicos da mensagem do usuário."""
            topics = []
            message_lower = message.lower()
            
            # Palavras-chave para identificar tópicos
            topic_keywords = {
                "saldo": ["saldo", "disponível", "conta"],
                "transferencia": ["transferir", "transferência", "enviar"],
                "extrato": ["extrato", "transações", "histórico"],
                "boleto": ["boleto", "conta", "fatura"],
                "cartao": ["cartão", "crédito", "compra"],
                "perfil": ["perfil", "financeiro", "análise"],
                "emprestimo": ["empréstimo", "crédito", "financiamento", "consignado", "taxa"],
                "api": ["api", "integração", "sistema", "ferramenta", "consulta"]
            }
            
            for topic, keywords in topic_keywords.items():
                if any(keyword in message_lower for keyword in keywords):
                    topics.append(topic)
            
            return topics
            
        def get_messages(self):
            return self.initial_state["messages"]
    
    return ChatAgent(cliente_id, vectorstore)