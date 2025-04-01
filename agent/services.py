import uuid
from datetime import datetime

# Dados simulados - Na implementação real, seriam APIs do banco
clientes = {
    "1": {"nome": "João Silva", "saldo": 5000.00, "conta": "12345-6"},
    "2": {"nome": "Maria Santos", "saldo": 8500.00, "conta": "65432-1"},
    "3": {"nome": "Carlos Oliveira", "saldo": 2300.00, "conta": "98765-4"}
}

transacoes = []

cartoes = {
    "1": {"numero": "**** **** **** 1234", "limite": 10000.00, "fatura_atual": 1200.00},
    "2": {"numero": "**** **** **** 5678", "limite": 15000.00, "fatura_atual": 3500.00},
    "3": {"numero": "**** **** **** 9012", "limite": 5000.00, "fatura_atual": 800.00}
}

def consultar_saldo(cliente_id: str) -> dict:
    """Consulta o saldo da conta do cliente."""
    if cliente_id in clientes:
        return {
            "status": "sucesso",
            "saldo": clientes[cliente_id]["saldo"],
            "conta": clientes[cliente_id]["conta"],
            "nome": clientes[cliente_id]["nome"]
        }
    return {"status": "erro", "mensagem": "Cliente não encontrado"}

def realizar_transferencia(cliente_id: str, destino_id: str, valor: float) -> dict:
    """Realiza transferência entre contas."""
    if cliente_id not in clientes or destino_id not in clientes:
        return {"status": "erro", "mensagem": "Cliente de origem ou destino não encontrado"}
    
    if clientes[cliente_id]["saldo"] < valor:
        return {"status": "erro", "mensagem": "Saldo insuficiente"}
    
    # Realiza a transferência
    clientes[cliente_id]["saldo"] -= valor
    clientes[destino_id]["saldo"] += valor
    
    # Registra a transação
    transacao = {
        "id": str(uuid.uuid4()),
        "data": datetime.now().isoformat(),
        "tipo": "transferência",
        "origem": cliente_id,
        "destino": destino_id,
        "valor": valor
    }
    transacoes.append(transacao)
    
    return {
        "status": "sucesso",
        "mensagem": f"Transferência de R$ {valor:.2f} realizada com sucesso",
        "novo_saldo": clientes[cliente_id]["saldo"],
        "transacao_id": transacao["id"]
    }

def buscar_transacoes(cliente_id: str, limite: int = 5) -> dict:
    """Busca as últimas transações do cliente."""
    transacoes_cliente = []
    
    for t in transacoes:
        # Verifica diferentes tipos de transações
        if (("origem" in t and t["origem"] == cliente_id) or 
            ("destino" in t and t["destino"] == cliente_id) or 
            ("cliente_id" in t and t["cliente_id"] == cliente_id)):
            transacoes_cliente.append(t)
            
    transacoes_cliente.sort(key=lambda x: x["data"], reverse=True)
    
    return {
        "status": "sucesso",
        "transacoes": transacoes_cliente[:limite]
    }

def pagar_boleto(cliente_id: str, codigo_barras: str, valor: float) -> dict:
    """Simula o pagamento de um boleto."""
    if cliente_id not in clientes:
        return {"status": "erro", "mensagem": "Cliente não encontrado"}
    
    if clientes[cliente_id]["saldo"] < valor:
        return {"status": "erro", "mensagem": "Saldo insuficiente"}
    
    # Realiza o pagamento
    clientes[cliente_id]["saldo"] -= valor
    
    # Registra a transação
    transacao = {
        "id": str(uuid.uuid4()),
        "data": datetime.now().isoformat(),
        "tipo": "pagamento_boleto",
        "origem": cliente_id,
        "codigo_barras": codigo_barras,
        "valor": valor
    }
    transacoes.append(transacao)
    
    return {
        "status": "sucesso",
        "mensagem": f"Pagamento de R$ {valor:.2f} realizado com sucesso",
        "novo_saldo": clientes[cliente_id]["saldo"],
        "transacao_id": transacao["id"]
    }

def pagar_cartao(cliente_id: str, estabelecimento: str, valor: float, cartao_id: str) -> dict:
    """Simula um pagamento com cartão."""
    if cliente_id not in clientes or cartao_id not in cartoes:
        return {"status": "erro", "mensagem": "Cliente ou cartão não encontrado"}
    
    # Adiciona à fatura do cartão
    cartoes[cartao_id]["fatura_atual"] += valor
    
    # Registra a transação
    transacao = {
        "id": str(uuid.uuid4()),
        "data": datetime.now().isoformat(),
        "tipo": "pagamento_cartao",
        "cliente_id": cliente_id,
        "cartao_id": cartao_id,
        "estabelecimento": estabelecimento,
        "valor": valor
    }
    transacoes.append(transacao)
    
    return {
        "status": "sucesso",
        "mensagem": f"Pagamento de R$ {valor:.2f} em {estabelecimento} realizado com sucesso",
        "fatura_atual": cartoes[cartao_id]["fatura_atual"],
        "transacao_id": transacao["id"]
    }

def analisar_comportamento(cliente_id: str) -> dict:
    """Analisa o comportamento do cliente com base nas transações."""
    # Filtro mais seguro para transações
    transacoes_cliente = []
    for t in transacoes:
        # Verifica transações com origem
        if t.get("tipo") in ["transferência", "pagamento_boleto"] and t.get("origem") == cliente_id:
            transacoes_cliente.append(t)
        # Verifica transações com cliente_id
        elif t.get("tipo") == "pagamento_cartao" and t.get("cliente_id") == cliente_id:
            transacoes_cliente.append(t)
    
    if not transacoes_cliente:
        return {
            "status": "info",
            "mensagem": "Não há transações suficientes para análise."
        }
    
    # Cálculo de totais
    total_gastos = 0
    categorias_boletos = {}
    categorias_estabelecimentos = {}
    
    # Processa cada transação
    for t in transacoes_cliente:
        valor = t.get("valor", 0)
        total_gastos += valor
        
        if t.get("tipo") == "pagamento_boleto":
            # Identifica a categoria do boleto (simulado)
            categoria = "Outros"
            codigo = t.get("codigo_barras", "")
            if codigo.startswith("765"):
                categoria = "Água"
            elif codigo.startswith("891"):
                categoria = "Energia"
            
            if categoria not in categorias_boletos:
                categorias_boletos[categoria] = {"quantidade": 0, "valor": 0}
            
            categorias_boletos[categoria]["quantidade"] += 1
            categorias_boletos[categoria]["valor"] += valor
            
        elif t.get("tipo") == "pagamento_cartao":
            estabelecimento = t.get("estabelecimento", "Desconhecido")
            
            if estabelecimento not in categorias_estabelecimentos:
                categorias_estabelecimentos[estabelecimento] = {"quantidade": 0, "valor": 0}
            
            categorias_estabelecimentos[estabelecimento]["quantidade"] += 1
            categorias_estabelecimentos[estabelecimento]["valor"] += valor
    
    # Cálculo de médias
    valor_medio = total_gastos / len(transacoes_cliente) if transacoes_cliente else 0
    
    # Classificação para ordenação
    categorias_boletos_sorted = sorted(
        categorias_boletos.items(),
        key=lambda x: x[1]["valor"],
        reverse=True
    )
    
    categorias_estabelecimentos_sorted = sorted(
        categorias_estabelecimentos.items(),
        key=lambda x: x[1]["valor"],
        reverse=True
    )
    
    # Perfil descritivo (simulado)
    perfil_descritivo = "Cliente com perfil de gastos moderado."
    if total_gastos > 1000:
        perfil_descritivo = "Cliente com perfil de gastos elevado."
    elif total_gastos < 200:
        perfil_descritivo = "Cliente com perfil de gastos conservador."
    
    return {
        "status": "sucesso",
        "total_gastos": total_gastos,
        "num_transacoes": len(transacoes_cliente),
        "principais_categorias_boletos": dict(categorias_boletos_sorted[:3]),
        "principais_categorias_estabelecimentos": dict(categorias_estabelecimentos_sorted[:3]),
        "valor_medio_transacao": valor_medio,
        "perfil_descritivo": perfil_descritivo
    }