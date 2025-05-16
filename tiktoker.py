# Um gerador de roteiros para o TikTok
import os
import asyncio # Added for asynchronous operations
from google import genai
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
from google.genai import types  # Para criar conteúdos (Content e Part)
from datetime import date
import textwrap # Para formatar melhor a saída de texto
# from IPython.display import display, Markdown # Removed: Not for terminal
import requests # Para fazer requisições HTTP
import warnings

warnings.filterwarnings("ignore")

# It's generally recommended to set API keys via environment variables
# before running the script, rather than hardcoding them.
# For example, in your terminal: export GOOGLE_API_KEY="YOUR_API_KEY"
# However, to keep the script as close to your original, I'm leaving this line,
# but be mindful of security implications.
os.environ['GOOGLE_API_KEY'] = 'sua chave' # Replace with your actual key if needed

# This client initialization might not be directly used by the ADK agents below,
# as they define their models internally. It can be kept if you have other uses for it.
client = genai.Client()
MODEL_ID = "gemini-2.0-flash" # Try with other models

# Função auxiliar que envia uma mensagem para um agente via Runner e retorna a resposta final
async def call_agent(agent: Agent, message_text: str) -> str: # Made async
    """
    Sends a message to an agent asynchronously and returns the final response.
    """
    # Cria um serviço de sessão em memória
    session_service = InMemorySessionService()
    # Cria uma nova sessão (você pode personalizar os IDs conforme necessário)
    session = session_service.create_session(app_name=agent.name, user_id="user1", session_id="session1")
    # Cria um Runner para o agente
    runner = Runner(agent=agent, app_name=agent.name, session_service=session_service)
    # Cria o conteúdo da mensagem de entrada
    content = types.Content(role="user", parts=[types.Part(text=message_text)])

    final_response = ""
    # Itera assincronamente pelos eventos retornados durante a execução do agente
    # Changed to runner.run_async and 'async for'
    async for event in runner.run_async(user_id="user1", session_id="session1", new_message=content):
        if event.is_final_response():
          for part in event.content.parts:
            if part.text is not None:
              final_response += part.text
              final_response += "\n"
    return final_response

# Função auxiliar para exibir texto formatado em Markdown no Colab
# This function is no longer returning a Markdown object, just formatted text.
# If you don't need special formatting for terminal, you can print directly.
def format_text_for_terminal(text: str) -> str:
  """
  Basic text formatting for terminal output.
  """
  text = text.replace('•', '  *')
  return textwrap.indent(text, '> ', predicate=lambda _: True)

##########################################
# --- Agente 1: Buscador de Notícias --- #
##########################################

async def agente_buscador(topico: str, data_de_hoje: str) -> str: # Made async
    """
    Agent that searches for news on the given topic.
    """
    buscador = Agent(
        name="agente_buscador",
        model="gemini-2.0-flash", # Model specified here
        description="Agente que busca notícias sobre o tópico indicado",
        tools=[google_search],
        instruction='''
        Você é um assistente de pesquisa. A sua tarefa é usar a busca do Google (google_search)
        para encontrar notícias muito relevantes relacionadas ao tópico especificado.
        Foque em, no máximo, cinco notícias relevantes, com base na quantidade e entusiasmo das
        notícias sobre ele.
        Se o termo tiver poucas notícias ou reações entusiasmadas, é possível que ele não seja
        tão relevante e pode ser substituído por outro termo que tenha mais.
        As notícias relevantes devem ser atuais (máximo um mês de diferença da data de hoje).
        '''
      # Adeque as instruções de acordo com o que deseja
    )
    entrada_do_agente_buscador = f"Tópico: {topico}\nData de hoje: {data_de_hoje}"
    # Executa o agente
    noticias = await call_agent(buscador, entrada_do_agente_buscador) # Used await
    return noticias

################################################
# --- Agente 2: Planejador de posts --- #
################################################
async def agente_planejador(topico: str, lancamentos_buscados: str) -> str: # Made async
    """
    Agent that plans posts based on searched news.
    """
    planejador = Agent(
        name="agente_planejador",
        model="gemini-2.0-flash", # Model specified here
        description="Agente que planeja posts",
        tools=[google_search],
        instruction="""
        Você é um planejador de conteúdo especialista em redes sociais. Com base na lista de notícias
        mais recentes e relevantes já buscadas, você deve
        1. usar a busca do Google (google_search) para criar um plano sobre quais os pontos mais
        relevantes que poderíamos abordar em um post sobre essas notícias
        2. usar a busca do Google (google_search) para encontrar mais informações sobre os temas
        em questão e aprofundar o conteúdo do post.
        3. Ao final, escolha o tema mais relevante entre os disponíveis, com base nas suas pesquisas, e
        retorne esse tema, seus pontos mais relevantes e o plano com os assuntos a serem abordados
        no post que será escrito posteriormente.
        4. Se fizer sentido, você pode combinar mais de um tema relevante em um único post.
        """,
      # Adeque as instruções de acordo com o que deseja
      
    )

    entrada_do_agente_planejador = f"Tópico:{topico}\nLançamentos buscados: {lancamentos_buscados}"
    # Executa o agente
    plano_do_post = await call_agent(planejador, entrada_do_agente_planejador) # Used await
    return plano_do_post

######################################
# --- Agente 3: Redator do Post --- #
######################################
async def agente_redator(topico: str, plano_de_post: str) -> str: # Made async
    """
    Agent that writes a draft post.
    """
    redator = Agent(
        name="agente_redator",
        model="gemini-2.0-flash", # Model specified here
        instruction="""
            Você é um Redator Criativo especializado em criar posts virais para redes sociais.
            Você escreve posts para o Cesar Brod, agilista e entusiasta de tecnologias livres.
            Utilize o tema fornecido no plano de post e os pontos mais relevantes fornecidos e, com base nisso,
            escreva um rascunho de roteiro para um vídeo do TikTok sobre o tema indicado.
            O roteiro deve ser engajador, informativo, com linguagem simples e incluir 2 a 4 hashtags no final.
            Esse é o estilo do autor, o Cesar Brod:
            Knowledgeable but not condescending. Enthusiastic and genuinely interested in the topic. Clear, concise,
            and easy to understand, even for complex subjects. Relatable, perhaps by including brief anecdotes
            or real-world examples where appropriate. Slightly informal and conversational, potentially with touches
            of humor, while maintaining professional credibility. Encouraging and supportive, fostering a sense of learning and community.
            O texto que você gerar deve ser em português do Brasil.
            """,
      # Adeque as instruções de acordo com o que deseja
      
        description="Agente redator de posts engajadores para TikTok"
    )
    entrada_do_agente_redator = f"Tópico: {topico}\nPlano de post: {plano_de_post}"
    # Executa o agente
    rascunho = await call_agent(redator, entrada_do_agente_redator) # Used await
    return rascunho

##########################################
# --- Agente 4: Revisor de Qualidade --- #
##########################################
async def agente_revisor(topico: str, rascunho_gerado: str) -> str: # Made async
    """
    Agent that reviews the draft post.
    """
    revisor = Agent(
        name="agente_revisor",
        model="gemini-2.0-flash", # Model specified here
        instruction="""
            Você é um Editor e Revisor de roteiros meticuloso, especializado em posts para redes sociais, com foco no TikTok.
            Por ter um público jovem, entre 18 e 30 anos, use um tom de escrita adequado, sempre dando preferência ao tom do Cesar Brod.
            Revise o rascunho de roteiro para o TikTok abaixo, sobre o tópico indicado, verificando clareza, concisão, correção e tom.
            Se o rascunho estiver bom, simplesmente considere o texto revisado igual ao rascunho gerado.
            Se você tiver sugestões ou correções, gere novamente o roteiro completo de acordo com elas.
            """,
      # Adeque as instruções de acordo com o que deseja
      
        description="Agente revisor de post para redes sociais."
    )
    entrada_do_agente_revisor = f"Tópico: {topico}\nRascunho: {rascunho_gerado}"
    # Executa o agente
    texto_revisado = await call_agent(revisor, entrada_do_agente_revisor) # Used await
    return texto_revisado

async def main_script_logic(): # Wrapped main logic in an async function
    """
    Main logic for the script.
    """
    data_de_hoje = date.today().strftime("%d/%m/%Y")

    print("🚀 Iniciando o Sistema de Criação de Roteiros para vídeos do TikTok com 4 Agentes 🚀")

    # --- Obter o Tópico do Usuário ---
    topico = input("❓ Por favor, digite o TÓPICO sobre o qual você quer criar o post de tendências: ")

    if not topico:
      print("Por favor, insira um tópico válido.")
    else:
      print(f"\nVamos criar o roteiro para o TikTok sobre {topico}")
      print("\n--- Agente 1 (Buscador de Notícias) ---")
      lancamentos_buscados = await agente_buscador(topico, data_de_hoje) # Used await
      print("Buscador rodou")
      # print(format_text_for_terminal(lancamentos_buscados)) # Descomente se quiser ver os resultados intermediários
      print("-----------------------------------------")

      print("\n--- Agente 2 (Planejador de Posts) ---")
      plano_de_post = await agente_planejador(topico, lancamentos_buscados) # Used await
      print("Planejador rodou")
      # print(format_text_for_terminal(plano_de_post)) # Descomente se quiser ver os resultados intermediários
      print("-----------------------------------------")

      print("\n--- Agente 3 (Redator do Post) ---")
      rascunho_de_post = await agente_redator(topico, plano_de_post) # Used await
      print("Redator rodou")
      # print(format_text_for_terminal(rascunho_de_post)) # Descomente se quiser ver os resultados intermediários
      print("-----------------------------------------")

      print("\n--- Agente 4 (Revisor de Qualidade) ---")
      texto_revisado = await agente_revisor(topico, rascunho_de_post) # Used await
      print("Texto Final Revisado:")
      print(format_text_for_terminal(texto_revisado)) # Using print and formatter
      print("-----------------------------------------")
      print("\n✨ Processo concluído! ✨")

if __name__ == "__main__":
    try:
        asyncio.run(main_script_logic())
    except RuntimeError as e:
        # This specific check is more for Jupyter/Colab.
        # In a terminal, if asyncio.run() itself fails, it might be a different setup issue.
        if "cannot be called from a running event loop" in str(e):
            print("Erro: Tentativa de rodar asyncio.run() em um loop de eventos já existente.")
            print("Este script é desenhado para ser executado como um script Python normal, não em um notebook com loop ativo.")
        else:
            print(f"Ocorreu um erro de runtime do asyncio: {e}")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")

