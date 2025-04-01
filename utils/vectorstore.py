import os
import PyPDF2
from langchain_openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('vectorstore')

def carregar_faq(pdf_path):
    """Carrega um PDF de FAQs e cria uma base de dados vetorial com verificações de erro."""
    
    logger.info(f"Iniciando carregamento do PDF: {pdf_path}")
    
    # Verificar se o arquivo existe
    if not os.path.exists(pdf_path):
        logger.error(f"Arquivo não encontrado: {pdf_path}")
        raise FileNotFoundError(f"Arquivo não encontrado: {pdf_path}")
    
    # Verificar extensão do arquivo
    if not pdf_path.lower().endswith('.pdf'):
        logger.error(f"Formato de arquivo não suportado: {pdf_path}")
        raise ValueError("O arquivo deve ser um PDF")
    
    # Usar PyPDF2 para extrair texto com verificações de segurança
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Verificar se o PDF está protegido
            if pdf_reader.is_encrypted:
                logger.error("O PDF está protegido por senha e não pode ser processado")
                raise ValueError("PDF protegido por senha")
            
            # Extrair texto de todas as páginas
            texto_completo = ""
            total_paginas = len(pdf_reader.pages)
            
            logger.info(f"Extraindo texto de {total_paginas} páginas...")
            
            for page_num in range(total_paginas):
                try:
                    page = pdf_reader.pages[page_num]
                    texto_pagina = page.extract_text()
                    if texto_pagina:  # Verificar se o texto não está vazio
                        texto_completo += texto_pagina + "\n\n"
                    logger.debug(f"Página {page_num+1}/{total_paginas} processada")
                except Exception as e:
                    logger.warning(f"Erro ao processar página {page_num+1}: {str(e)}")
    except Exception as e:
        logger.error(f"Erro ao abrir ou processar o PDF: {str(e)}")
        raise ValueError(f"Falha ao processar o PDF: {str(e)}")
    
    # Verificar se conseguimos extrair algum texto
    if not texto_completo.strip():
        logger.error("Não foi possível extrair texto do PDF - o documento pode estar vazio ou protegido")
        raise ValueError("Não foi possível extrair texto do PDF - o documento pode estar vazio ou protegido")
    
    logger.info(f"Texto extraído com sucesso: {len(texto_completo)} caracteres")
    
    # Dividir em chunks para processamento
    logger.info("Dividindo texto em chunks...")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,  # Maior sobreposição para capturar melhor o contexto
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    chunks = text_splitter.split_text(texto_completo)
    
    # Verificar se há chunks
    if not chunks:
        logger.warning("Nenhum chunk gerado. Usando texto completo como um único chunk.")
        chunks = [texto_completo]
    
    logger.info(f"Texto dividido em {len(chunks)} chunks")
    
    # Diagnóstico de chunks
    for i, chunk in enumerate(chunks[:3]):  # Log dos primeiros 3 chunks para diagnóstico
        logger.debug(f"Chunk {i+1} (primeiros 100 caracteres): {chunk[:100]}...")
    
    # Criar embeddings e vetorizar
    logger.info("Gerando embeddings e criando vectorstore...")
    
    try:
        embeddings = OpenAIEmbeddings()
        
        # Criar embeddings para teste antes de criar o vectorstore
        logger.debug("Testando geração de embeddings...")
        test_embeddings = embeddings.embed_documents(chunks[:1])
        if not test_embeddings:
            logger.error("Falha ao gerar embeddings - verifique a chave da API OpenAI")
            raise ValueError("Falha ao gerar embeddings - verifique a chave da API OpenAI")
        
        logger.info(f"Embeddings gerados com sucesso para o primeiro chunk: {len(test_embeddings[0])} dimensões")
        
        # Criar vectorstore
        vectorstore = FAISS.from_texts(chunks, embeddings)
        
        # Verificar se o vectorstore foi criado corretamente
        if not vectorstore:
            logger.error("Falha ao criar vectorstore")
            raise ValueError("Falha ao criar vectorstore - resultado vazio")
        
        logger.info(f"Base de conhecimento criada com sucesso - {len(chunks)} chunks vetorizados")
        
        # Realizar uma pesquisa de teste
        logger.debug("Realizando pesquisa de teste no vectorstore...")
        docs = vectorstore.similarity_search("empréstimo", k=1)
        if docs:
            logger.debug(f"Pesquisa de teste bem-sucedida. Primeiro resultado: {docs[0].page_content[:50]}...")
        
        return vectorstore
        
    except Exception as e:
        logger.error(f"Erro ao gerar embeddings ou criar vectorstore: {str(e)}")
        raise ValueError(f"Falha ao criar base de conhecimento: {str(e)}")

def carregar_multiplos_faqs(pdf_paths):
    """Carrega múltiplos PDFs de FAQ e cria uma base de dados vetorial unificada."""
    
    logger.info(f"Iniciando carregamento de {len(pdf_paths)} PDFs")
    
    all_chunks = []
    
    for pdf_path in pdf_paths:
        try:
            # Verificar se o arquivo existe
            if not os.path.exists(pdf_path):
                logger.warning(f"Arquivo não encontrado: {pdf_path} - ignorando")
                continue
                
            logger.info(f"Processando arquivo: {pdf_path}")
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Extrair texto de todas as páginas
                texto_completo = ""
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    texto_pagina = page.extract_text()
                    if texto_pagina:  # Verificar se o texto não está vazio
                        texto_completo += texto_pagina + "\n\n"
            
            # Verificar se conseguimos extrair algum texto
            if not texto_completo.strip():
                logger.warning(f"Não foi possível extrair texto de: {pdf_path}")
                continue
                
            # Dividir em chunks para processamento
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
            chunks = text_splitter.split_text(texto_completo)
            
            # Adicionar identificador de origem aos metadados
            chunks_with_metadata = []
            for chunk in chunks:
                chunks_with_metadata.append({
                    "content": chunk,
                    "metadata": {
                        "source": os.path.basename(pdf_path),
                        "path": pdf_path
                    }
                })
                
            all_chunks.extend(chunks_with_metadata)
            logger.info(f"Adicionados {len(chunks)} chunks de {pdf_path}")
            
        except Exception as e:
            logger.warning(f"Erro ao processar {pdf_path}: {str(e)}")
    
    if not all_chunks:
        logger.error("Nenhum texto extraído de nenhum arquivo")
        raise ValueError("Falha ao extrair texto dos PDFs")
        
    # Criar embeddings e vetorizar
    logger.info(f"Gerando embeddings para {len(all_chunks)} chunks no total...")
    
    try:
        embeddings = OpenAIEmbeddings()
        
        # Separar conteúdo e metadados
        texts = [item["content"] for item in all_chunks]
        metadatas = [item["metadata"] for item in all_chunks]
        
        # Criar vectorstore com metadados
        vectorstore = FAISS.from_texts(texts, embeddings, metadatas=metadatas)
        
        logger.info(f"Base de conhecimento unificada criada com sucesso - {len(all_chunks)} chunks vetorizados")
        return vectorstore
        
    except Exception as e:
        logger.error(f"Erro ao gerar embeddings ou criar vectorstore: {str(e)}")
        raise ValueError(f"Falha ao criar base de conhecimento unificada: {str(e)}")

def buscar_documentos_similares(vectorstore, query, k=3):
    """Função utilitária para buscar documentos similares no vectorstore."""
    if not vectorstore:
        logger.error("Vectorstore não inicializado")
        return []
        
    try:
        docs = vectorstore.similarity_search(query, k=k)
        return docs
    except Exception as e:
        logger.error(f"Erro na busca por documentos similares: {str(e)}")
        return []