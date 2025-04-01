from typing import TypedDict, Annotated, Sequence, Any, Dict, Optional

class ChatState(TypedDict):
    """Estado do grafo do agente de chat bancário."""
    messages: Annotated[Sequence[Any], "Mensagens na conversa"]
    cliente_id: Annotated[str, "ID do cliente ativo"]
    next: Annotated[str, "Próximo nó para execução"]
    context: Annotated[Optional[Dict[str, Any]], "Contexto adicional da conversa"] = None