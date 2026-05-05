"""
Auto-converted from Interface.ipynb.
Generated for code-first workflow (.py).
"""

# # Preliminary operations
# Load libaries and dataset

#pip install  pypdf langchain tika typing fuzzywuzzy pymupdf easyocr
#pip install langchain wikipedia openai tika gradio
#pip install google-search-results

import pandas as pd
from langchain.document_loaders import PyPDFLoader
from tika import parser
from typing import List
import re
from typing import List, Tuple
from fuzzywuzzy import fuzz, process
import fitz
import easyocr
import numpy as np
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
import gradio as gr

# # Extra tool

dataset = pd.read_csv('https://github.com/SimoneFarallo/public_and_social_services/raw/main/data/final_data_cleaned.csv')
dataset = dataset.drop(dataset.columns[0], axis=1)
dataset.head()

# function to match  prescriptions with a dataset and create a new dataframe
def automatic_ocr_search(file: str, dataset: pd.DataFrame) -> pd.DataFrame:
    # raise error if file path is not a string
    if not isinstance(file, str):
        raise TypeError("File path must be a string.")
    # raise error if dataset is not a pandas DataFrame
    if not isinstance(dataset, pd.DataFrame):
        raise TypeError("Dataset must be a pandas.DataFrame.")

    # if file is a pdf, extract text from file
    if file.endswith(".pdf"):
        pdf_file = fitz.open(file) # open pdf file
        text = ''
        for page in pdf_file:
            text += page.get_text() # extract text from each page

        # identify words of interest using regular expression
        words = re.findall(r' - ([A-Za-z\s]+)', text)

    # if file is a png, read text from image using OCR
    elif file.endswith(".png"):
        ricetta = reader.readtext(file) # use tesseract to read text
        result_string = ""
        for i in range(len(ricetta)):
            elemento = ricetta[i][1] #string values are stored in this position in the tuple
            result_string += elemento # concatenate all strings
            result_string += " " # add space between each string
        
        result_string = result_string.replace(".","") # remove dots
        regex = r"\((\d\w*)\)([A-Z ]+)"
        matches = re.findall(regex, result_string) # identify string patterns using regex
        output = []
        for match in matches:
            output.append(match[1]) # append string to output list

        words = output

    # raise error if file format is not supported
    else:
        raise ValueError("File format not supported. Please use a pdf or png file.")

    # match words with values in Codice prestazione ambulatoriale column of dataset using fuzzywuzzy library
    matches = []
    for word in words:
        if not isinstance(word, str):
            raise TypeError("Word of interest must be a string.")
        scores = process.extract(word, dataset['Codice prestazione ambulatoriale'], scorer=fuzz.token_set_ratio, limit=1)
        filtered_scores = [score for score in scores if score[1] >= 90]
        for score in filtered_scores:
            rows = dataset[dataset['Codice prestazione ambulatoriale'] == score[0]].iterrows()
            matches.extend([(word,row[1], score[1]) for row in rows])

    # sort matches by score in descending order
    matches_sorted = sorted(matches, key=lambda x: x[2], reverse=True)
    
    # create empty dictionary to populate with data
    data = {}

    # iterate through list of tuples
    for row in matches_sorted:
        # extract category name and associated row data
        category, row_data, _ = row
        # iterate through columns in row data
        for col, val in row_data.items():
            # create key in dictionary if it doesn't exist already
            if col not in data:
                data[col] = []
            # append value to list of values associated with key
            data[col].append(val)
        # if a column is missing from current row, add a None value
        for col in data.keys():
            if col not in row_data:
                data[col].append(None)

    # create new DataFrame from dictionary
    df = pd.DataFrame(data)

    return df

#Function to filter the dataset
#Is possible add more columns to filter, for now we use only 2
def filter_data(data_frame, comune=None, risposta_strutt= None):
    if comune is not None and risposta_strutt is not None:
        filtered_df = data_frame[(data_frame['Comune struttura'] == comune) & (data_frame['Struttura privata'] == risposta_strutt)]
    elif comune is not None:
        filtered_df = data_frame[data_frame['Comune struttura'] == comune]
    elif risposta_strutt is not None:
        filtered_df = data_frame[data_frame['Struttura privata'] == risposta_strutt]
    else:
        filtered_df = data_frame.copy()

    return filtered_df

#Function to search structures directly with performance names (Fuzzy)
def search_facilities(words):
    matches = []
    data = {}

    for word in words:
        if not isinstance(word, str): #Check if the word is a string, otherwise raise a TypeError
            raise TypeError("The word of interest must be a string.")
        scores = process.extract(word, dataset['Codice prestazione ambulatoriale'], scorer=fuzz.token_set_ratio, limit=1) #Extract matching scores between the word and the dataset
        filtered_scores = [score for score in scores if score[1] >= 90] #Filter scores based on a threshold of 70%
        for score in filtered_scores:
            rows = dataset[dataset['Codice prestazione ambulatoriale'] == score[0]].iterrows() #Get the rows of the dataset that match the word
            matches.extend([(word,row[1], score[1]) for row in rows]) #Extend the matches list with a tuple of the word, the row data, and the matching score
            for row in matches:
                category, row_data, _ = row
                for col, val in row_data.items():
                    if col not in data:
                        data[col] =[]
                    data[col].append(val) #Add the values of therow to the respective column in the data dictionary
                for col in data.keys():
                    if col not in row_data:
                        data[col].append(None) #If a column is missing in the row, add None as a placeholder

    df = pd.DataFrame(data) #Create a pandas DataFrame from the data dictionary
    print(df['Codice prestazione ambulatoriale'].unique()) #Print the unique values of the 'Codice prestazione ambulatoriale' column in the DataFrame
    return df

# # Langchain

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

#agent construction
agent = initialize_agent(tools,  OpenAI(temperature=0), memory = memory, 
                         agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                         verbose=True, max_iterations = 5)

prompt_ita = PromptTemplate( 
    input_variables=["domanda"],
    template="Istruzione: Usa massimo 2 - 3 frasi per rispondere a domande relative alla sanitÃ .\n"
     "Contesto: Sei un agente AI per fornire informazioni generali all'utente legati all'ambito sanitario. Ricorda che non puoi effettuare prenotazioni o azioni simili.\n" 
     "Domanda: {domanda}\n",

)

# # Interfaccia

# Definisci la funzione di Gradio per l'interfaccia utente
def automatic_ocr_search_interface(
    file: gr.inputs.File,
    comune: str = None,
    risposta_strutt: str = None
):
    # Ottieni il percorso del file
    file_path = file.name

    # Esegui la tua funzione originale con il percorso del file (stringa) e il DataFrame
    df = automatic_ocr_search(file_path, dataset)

    # Filtra il DataFrame se i parametri di filtraggio sono specificati
    if comune is not None or risposta_strutt is not None:
        df = filter_data(df, comune, risposta_strutt)

    # Restituisci il risultato come output dell'interfaccia
    return df

# Definisci gli input per l'interfaccia utente
file_input = gr.inputs.File(label="Inserisci file pdf o png")
comune_input = gr.inputs.Textbox(label="Comune")
risposta_strutt_input = gr.inputs.Textbox(label="Struttura privata")


def output(input):
  question = prompt_ita.format(domanda = input)
  return agent.run(prompt_ita.format(domanda = input)) 

def search_words_interface(words):
    try:
        df = search_facilities(words)
        unique_values = df
        return unique_values
    except TypeError as e:
        return str(e)

Automatic_OCR_search = gr.Interface(
    fn=automatic_ocr_search_interface,
    inputs=[file_input, comune_input, risposta_strutt_input],
    outputs=["dataframe"],
    title="Automatic OCR search tool",
    description="Per cercare gli ambulatori in Lombardia, inserisci la tua ricetta, la cittÃ  (in maiuscolo) e il tipo di struttura (SÃ¬ o No)."
)
chatbot = gr.Interface(
    fn=output,
    inputs=gr.Textbox(lines=2, placeholder="Scrivi qui la tua domanda"),
    outputs="text",
    title="Chatbot",
    description="Ciao! Sono il tuo assistente sanitario virtuale. Sono qui per fornirti informazioni generali in ambito sanitario. Tuttavia, Ã¨ importante sottolineare che non posso sostituire il parere di un medico esperto. FarÃ² del mio meglio per chiarire i tuoi dubbi e offrirti informazioni affidabili."    
)



# Creazione dell'interfaccia Gradio
search_tool = gr.Interface(
    fn=search_words_interface, 
    inputs=gr.Textbox(lines=1, placeholder="Scrivi il nome dell'analisi"),
    title="Search medical facilities",
    description="Inserisci il nome delle prestazione ambulatoriale per ottenere tutte le strutture disponibli per la regione Lombardia.",
    outputs="dataframe"
    )



# Definisci l'interfaccia utente utilizzando la tua funzione di Gradio e gli input definiti

demo = gr.TabbedInterface([chatbot,Automatic_OCR_search,search_tool], ["Chatbot","Automatic OCR Search","Search medical facilities"])
if __name__ == "__main__":
    demo.launch(share=True)


