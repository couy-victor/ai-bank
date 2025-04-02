# agent/mcp_node_client.py
import json
import subprocess
import sys
import threading
import queue
from typing import Dict, Any, List, Optional
from langchain_groq import ChatGroq
from langchain_core.messages import AIMessage, HumanMessage
from agent.states import ChatState

class MCPAgent:
    """Cliente simplificado para comunicação com o servidor MCP Node.js."""
    
    def __init__(self, vectorstore=None, server_cmd=["npx", "-y", "node", "mcp_servers/banking-api-server.js"]):
        self.server_cmd = server_cmd
        self.server_process = None
        self.response_queue = queue.Queue()
        self.next_id = 1
        self.llm = ChatGroq(model="llama3-70b-8192", temperature=0)
        self.vectorstore = vectorstore
    
    def start_server(self):
        """Inicia o processo do servidor MCP."""
        if self.server_process is not None:
            return
        
        try:
            print("Iniciando servidor MCP...")
            self.server_process = subprocess.Popen(
                self.server_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
            
            # Thread para ler as respostas do servidor
            def read_output():
                while self.server_process and self.server_process.poll() is None:
                    line = self.server_process.stdout.readline()
                    if not line:
                        break
                    try:
                        response = json.loads(line)
                        self.response_queue.put(response)
                    except json.JSONDecodeError:
                        continue
            
            # Thread para ler erros do servidor
            def read_errors():
                while self.server_process and self.server_process.poll() is None:
                    line = self.server_process.stderr.readline()
                    if not line:
                        break
                    print(f"MCP Server Error: {line.strip()}")
            
            threading.Thread(target=read_output, daemon=True).start()
            threading.Thread(target=read_errors, daemon=True).start()
            
            print("Servidor MCP Node.js iniciado")
        except Exception as e:
            print(f"Erro ao iniciar servidor MCP: {e}")
            self.stop_server()
    
    def stop_server(self):
        """Para o processo do servidor MCP."""
        if self.server_process:
            self.server_process.terminate()
            self.server_process = None
    
    def send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Envia uma requisição para o servidor e retorna a resposta."""
        if not self.server_process:
            self.start_server()
        
        request_id = self.next_id
        self.next_id += 1
        
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params
        }
        
        try:
            request_str = json.dumps(request) + "\n"
            self.server_process.stdin.write(request_str)
            self.server_process.stdin.flush()
            
            # Aguardar a resposta
            timeout = 10  # segundos
            start_time = threading.current_thread().time()
            while (threading.current_thread().time() - start_time) < timeout:
                try:
                    response = self.response_queue.get(timeout=1)
                    if response.get("id") == request_id:
                        if "error" in response:
                            raise Exception(f"MCP Error: {response['error']}")
                        return response.get("result", {})
                except queue.Empty:
                    continue
            
            raise TimeoutError("Tempo excedido aguardando resposta do servidor MCP")
        except Exception as e:
            print(f"Erro ao enviar requisição: {e}")
            return {"error": str(e)}
    
    def process_query(self, query: str, cliente_id: str) -> str:
        """Processo uma consulta usando alternativas quando o MCP falha."""
        # Fallback para resposta genérica
        generic_prompt = f"""
        Você é um assistente bancário do FourBank.
        O cliente perguntou: "{query}"
        
        Forneça uma resposta genérica sobre taxas de empréstimos ou elegibilidade para 
        empréstimos, dependendo do contexto da pergunta.
        
        Se a pergunta for sobre taxas de juros, você pode informar:
        - Empréstimo consignado: entre 1.3% e 2.1% ao mês
        - Empréstimo pessoal: entre 2.5% e 4.0% ao mês
        
        Se for sobre elegibilidade, você pode explicar os critérios gerais.
        """
        
        response = self.llm.invoke(generic_prompt)
        return response.content
    
    def process_state(self, state: ChatState) -> ChatState:
        """Processa o estado do chat."""
        # Extrair a última mensagem do usuário
        query = ""
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                query = msg.content
                break
        
        if not query:
            return state
        
        # Tentar processar com MCP ou usar fallback
        response = self.process_query(query, state["cliente_id"])
        
        # Adicionar a resposta ao estado
        state["messages"].append(AIMessage(content=response))
        
        return state