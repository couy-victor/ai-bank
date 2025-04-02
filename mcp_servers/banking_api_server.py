#!/usr/bin/env python3
from typing import Dict, Any
from modelcontextprotocol.server import Server
from modelcontextprotocol.server.stdio import StdioServerTransport
from modelcontextprotocol.types import (
    CallToolRequestSchema,
    ErrorCode,
    ListToolsRequestSchema,
    McpError,
)

class BankingAPIServer:
    def __init__(self):
        self.server = Server(
            {
                "name": "banking-api-server",
                "version": "0.1.0",
            },
            {
                "capabilities": {
                    "tools": {},
                }
            }
        )

        self.setup_tool_handlers()
        
        # Error handling
        self.server.onerror = lambda error: print("[MCP Error]", error)

    def setup_tool_handlers(self):
        self.server.set_request_handler(ListToolsRequestSchema, self.handle_list_tools)
        self.server.set_request_handler(CallToolRequestSchema, self.handle_call_tool)

    async def handle_list_tools(self, _):
        """Lista as ferramentas disponíveis no servidor."""
        return {
            "tools": [
                {
                    "name": "check_loan_eligibility",
                    "description": "Verifica a elegibilidade para empréstimo consignado",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "cpf": {
                                "type": "string",
                                "description": "CPF do cliente"
                            },
                            "valor_solicitado": {
                                "type": "number",
                                "description": "Valor do empréstimo solicitado"
                            }
                        },
                        "required": ["cpf", "valor_solicitado"]
                    }
                },
                {
                    "name": "get_loan_rates",
                    "description": "Obtém as taxas de juros disponíveis",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "tipo_emprestimo": {
                                "type": "string",
                                "description": "Tipo de empréstimo (consignado, pessoal, etc)"
                            }
                        },
                        "required": ["tipo_emprestimo"]
                    }
                }
            ]
        }

    async def handle_call_tool(self, request):
        """Processa as chamadas de ferramentas."""
        tool_name = request.params.name
        args = request.params.arguments

        if tool_name == "check_loan_eligibility":
            return await self._check_loan_eligibility(args)
        elif tool_name == "get_loan_rates":
            return await self._get_loan_rates(args)
        else:
            raise McpError(
                ErrorCode.MethodNotFound,
                f"Ferramenta desconhecida: {tool_name}"
            )

    async def _check_loan_eligibility(self, args: Dict[str, Any]):
        """Simula verificação de elegibilidade para empréstimo."""
        # Aqui você implementaria a lógica real de verificação
        # Por enquanto, retornamos uma resposta simulada
        return {
            "content": [
                {
                    "type": "text",
                    "text": {
                        "eligible": True,
                        "max_amount": 50000.00,
                        "reason": "Cliente com bom histórico e margem consignável disponível"
                    }
                }
            ]
        }

    async def _get_loan_rates(self, args: Dict[str, Any]):
        """Simula obtenção de taxas de juros."""
        # Aqui você implementaria a integração real com a API do banco
        rates = {
            "consignado": {
                "taxa_minima": 1.3,
                "taxa_maxima": 2.1,
                "prazo_maximo": 84
            },
            "pessoal": {
                "taxa_minima": 2.5,
                "taxa_maxima": 4.0,
                "prazo_maximo": 48
            }
        }
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": rates.get(args["tipo_emprestimo"], {
                        "error": "Tipo de empréstimo não encontrado"
                    })
                }
            ]
        }

    async def run(self):
        """Inicia o servidor MCP."""
        transport = StdioServerTransport()
        await self.server.connect(transport)
        print("Servidor BankingAPI MCP rodando em stdio")

if __name__ == "__main__":
    import asyncio
    server = BankingAPIServer()
    asyncio.run(server.run())
