# AI-Bank 🏦

Um agente bancário inteligente desenvolvido em Python que utiliza processamento de linguagem natural para fornecer informações sobre serviços bancários, com foco em empréstimos consignados.

## 📋 Sobre o Projeto

O AI-Bank é um sistema inteligente que processa e responde perguntas sobre serviços bancários utilizando documentos FAQ como base de conhecimento. O sistema utiliza técnicas avançadas de processamento de linguagem natural para entender as perguntas dos usuários e fornecer respostas precisas.

## 🚀 Funcionalidades

- Processamento inteligente de perguntas sobre serviços bancários
- Respostas baseadas em documentos FAQ oficiais
- Sistema de estados para manter contexto das conversas
- Processamento de grafos para navegação contextual
- Armazenamento vetorial para busca semântica eficiente
- Integração com MCP (Model Context Protocol) para extensibilidade

## 🔄 Integração MCP

O projeto utiliza o Model Context Protocol (MCP) para expandir as capacidades do agente bancário através de servidores MCP especializados. Isso permite:

- Conexão com APIs externas de serviços bancários
- Acesso a dados em tempo real de produtos financeiros
- Extensibilidade através de ferramentas personalizadas
- Integração com sistemas legados do banco
- Processamento assíncrono de requisições complexas

### Servidores MCP Propostos

1. **BankingAPI Server**
   - Conexão com APIs do banco
   - Consulta de produtos e serviços
   - Verificação de elegibilidade

2. **CustomerData Server**
   - Gestão de dados do cliente
   - Histórico de transações
   - Análise de perfil

3. **RiskAnalysis Server**
   - Avaliação de crédito
   - Análise de risco
   - Prevenção a fraudes

## 🏗️ Estrutura do Projeto

```
fourbank/
├── agent/                  # Núcleo do agente inteligente
│   ├── graph.py           # Implementação de navegação em grafo
│   ├── nodes.py           # Definição dos nós de processamento
│   ├── services.py        # Serviços do agente
│   └── states.py          # Gerenciamento de estados
├── data/                   # Base de conhecimento
│   ├── faq_bancario_emprestimo_consig.pdf
│   └── FAQ-APP-FOLHA-v06.pdf
├── utils/                  # Utilitários
│   └── vectorstore.py     # Implementação de armazenamento vetorial
├── app.py                 # Aplicação principal
└── requirements.txt       # Dependências do projeto
```

## 🛠️ Tecnologias Utilizadas

- Python
- LangGraph para orquestração de agentes e fluxos conversacionais
- Model Context Protocol (MCP) para extensibilidade
- Processamento de Linguagem Natural (NLP)
- Armazenamento Vetorial para busca semântica
- Grafos para navegação contextual
- Gerenciamento de estados para manter contexto

## ⚙️ Como Executar

1. Clone o repositório
```bash
git clone [url-do-repositorio]
```

2. Instale as dependências
```bash
pip install -r requirements.txt
```

3. Execute a aplicação
```bash
python app.py
```

## 📄 Licença

Este projeto está sob a licença [inserir tipo de licença].

## 👥 Contribuição

Contribuições são bem-vindas! Por favor, sinta-se à vontade para submeter um Pull Request.

---

Desenvolvido com 💙 pelo time FourBank
