"""
Auto-converted from Langchain.ipynb.
Generated for code-first workflow (.py).
"""

# # LangChain 

# LangChain is a framework for developing applications powered by language models. 
# 
# For the purpose of this project, LangChain is used to exploit the power of agents.
# More precisely, an agent is a chain in which a LLM, given a high-level directive and a set of tools, repeatedly decides an action, executes the action and observes the outcome until the high-level directive is complete.
# 
# Through a friendly interface build with *Gradio*, you can see how the agent answers to your questions.
# 
# For example, you can ask about explanations of some laboratory analyses, i.e. "*Che cos'Ã¨ la calcitonina?*"

# #### Loading libraries

import warnings
warnings.filterwarnings("ignore")

#pip install langchain wikipedia openai tika gradio
#pip install google-search-results

import openai
from langchain.agents import create_csv_agent
from langchain.llms import OpenAI
from tika import parser
from typing import List
from langchain.utilities import WikipediaAPIWrapper
from langchain.agents import load_tools
from langchain.agents import initialize_agent, Tool
from langchain.agents import AgentType
from langchain.memory import ConversationBufferMemory
from langchain.tools import WikipediaQueryRun
from langchain.tools import DuckDuckGoSearchRun
import re
import os
import pprint
import pandas as pd
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain import LLMMathChain, SerpAPIWrapper
from langchain.utilities import GoogleSerperAPIWrapper

# ### Tool customization and priorities definition

# Setting keys for OpenAI and Google Serper API

from dotenv import load_dotenv
import os

load_dotenv()
openai_key = os.getenv("OPENAI_API_KEY")
serper_key = os.getenv("SERPER_API_KEY")
if not openai_key:
    raise ValueError("Missing OPENAI_API_KEY in environment/.env")
if not serper_key:
    raise ValueError("Missing SERPER_API_KEY in environment/.env")
os.environ["OPENAI_API_KEY"] = openai_key
os.environ["SERPER_API_KEY"] = serper_key

google_search = GoogleSerperAPIWrapper()

search = WikipediaAPIWrapper(lang='it')

# A list of tools is provided to the agent.
# 
#  Each tool is defined by a name, function and its description which helps the agent to determine the tool use.

#customized tool, emphasizing priorities.
tools = [
    Tool(
        name = "Wikipedia Search", #wikipedia
        func=search.run,
        description="A Search Engine. Use this to answer questions only related to healthcare." 
         "Give priority to this."
         "Input should be a query.",
    ),
    Tool(
        name="Search",
        func= google_search.run, #google serper
        description="Use this to answer questions only related to healthcare." 
         "Use this to answer questions about current or recent events."
         "Input should be a query.",
    ),
    Tool(
        name="No answer", #my function
        func=lambda x: "Non mi Ã¨ consentito rispondere a questo tipo di domande perchÃ© non sono legate all'ambito sanitario.", 
        description="Use this to answer questions not related to healthcare. Input should be a query.",
    )
]

memory = ConversationBufferMemory(memory_key="chat_history")

# The agent decides which tool - if any - to use. 
# 
# It is defined in the following way:

#agent construction
agent = initialize_agent(tools,  OpenAI(temperature=0), memory = memory, 
                         agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                         verbose=True, max_iterations = 5)

# The temperature is set to 0; lower temperature values encourage more factual and concise responses.
# The agent uses the ReAct framework to determine which tool to use based solely on the toolâ€™s description.

# **Prompt Engineering** to guide the output generation.

prompt_ita = PromptTemplate( 
    input_variables=["domanda"],
    template="Istruzione: Usa massimo 2 - 3 frasi per rispondere a domande relative alla sanitÃ .\n"
     "Contesto: Sei un agente AI per fornire informazioni generali all'utente legati all'ambito sanitario. Ricorda che non puoi effettuare prenotazioni o azioni simili.\n" 
     "Domanda: {domanda}\n",

)

# #### Using wikipedia for definitions

print(prompt_ita.format(domanda = "Mi dai una definizione di calcitonina?"))

agent.run(prompt_ita.format(domanda = "Mi dai una definizione di calcitonina?"))

# #### Using wikipedia to provide definition and explain the purpose of the analysis

print(prompt_ita.format(domanda = "Che cos'Ã¨ l'emocromo e perchÃ¨ devo fare le analisi di sangue dell'emocromo?"))

agent.run(prompt_ita.format(domanda = "Che cos'Ã¨ l'emocromo e perchÃ¨ devo fare le analisi di sangue dell'emocromo?"))

agent.run(prompt_ita.format(domanda = "Quali sono i valori normali di emocromo per una donna sana?"))

agent.run(prompt_ita.format(domanda = "Sono una donna con valori dell'emocromo oltre il 50%. Cosa vuol dire?"))

# #### Using google search when wikipedia is not enough

agent.run(prompt_ita.format(domanda = "Cosa sono le analisi ALTRE TRAZIONI CUTANEE DEGLI ARTI?"))

# #### Using customised tool for no answering.

agent.run(prompt_ita.format(domanda = "Consigliami la migliore pizzeria di Milano"))

#Check memory
memory.load_memory_variables({})

# ### Interface - gradio

import gradio as gr

def output(input):
  question = prompt_ita.format(domanda = input)
  return agent.run(prompt_ita.format(domanda = input))

bot = gr.Interface(
    fn=output,
    inputs=gr.Textbox(lines=2, placeholder="Sono un chabot in ambito sanitario, specializzato in analisi mediche e prestazioni specialistiche ambulatoriali. Dimmi come posso aiutarti. Ricorda che Ã¨ sempre meglio fare riferimento a un medico professionista."),
    outputs="text",
)
bot.launch()

