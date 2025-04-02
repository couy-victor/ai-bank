#!/usr/bin/env node
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';

class BankingAPIServer {
    constructor() {
        this.server = new Server(
            {
                name: 'banking-api-server',
                version: '0.1.0'
            },
            {
                capabilities: {
                    tools: {}
                }
            }
        );

        this.setupToolHandlers();
        
        // Error handling
        this.server.onerror = (error) => console.error('[MCP Error]', error);
    }

    setupToolHandlers() {
        this.server.setRequestHandler('ListTools', async () => ({
            tools: [
                {
                    name: 'check_loan_eligibility',
                    description: 'Verifica a elegibilidade para empréstimo consignado',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            cpf: {
                                type: 'string',
                                description: 'CPF do cliente'
                            },
                            valor_solicitado: {
                                type: 'number',
                                description: 'Valor do empréstimo solicitado'
                            }
                        },
                        required: ['cpf', 'valor_solicitado']
                    }
                },
                {
                    name: 'get_loan_rates',
                    description: 'Obtém as taxas de juros disponíveis',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            tipo_emprestimo: {
                                type: 'string',
                                description: 'Tipo de empréstimo (consignado, pessoal, etc)'
                            }
                        },
                        required: ['tipo_emprestimo']
                    }
                }
            ]
        }));

        this.server.setRequestHandler('CallTool', async (request) => {
            const { name, arguments: args } = request.params;

            if (name === 'check_loan_eligibility') {
                return await this.checkLoanEligibility(args);
            } else if (name === 'get_loan_rates') {
                return await this.getLoanRates(args);
            } else {
                throw new Error(`Ferramenta desconhecida: ${name}`);
            }
        });
    }

    async checkLoanEligibility(args) {
        // Simula verificação de elegibilidade para empréstimo
        return {
            content: [
                {
                    type: 'text',
                    text: {
                        eligible: true,
                        max_amount: 50000.00,
                        reason: 'Cliente com bom histórico e margem consignável disponível'
                    }
                }
            ]
        };
    }

    async getLoanRates(args) {
        // Simula obtenção de taxas de juros
        const rates = {
            consignado: {
                taxa_minima: 1.3,
                taxa_maxima: 2.1,
                prazo_maximo: 84
            },
            pessoal: {
                taxa_minima: 2.5,
                taxa_maxima: 4.0,
                prazo_maximo: 48
            }
        };
        
        return {
            content: [
                {
                    type: 'text',
                    text: rates[args.tipo_emprestimo] || {
                        error: 'Tipo de empréstimo não encontrado'
                    }
                }
            ]
        };
    }

    async run() {
        const transport = new StdioServerTransport();
        await this.server.connect(transport);
        console.error('Servidor BankingAPI MCP rodando em stdio');
    }
}

const server = new BankingAPIServer();
server.run().catch(console.error);
