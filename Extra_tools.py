"""
Auto-converted from Extra_tools.ipynb.
Generated for code-first workflow (.py).
"""

# # Extra tools
# 
# In this notebook we are going to build a tool that taken as input a medical prescription in pdf,jpg format or a string gives me as output the list of facilities that perform medical analysis.
# 
# To extract information from prescriptions we will use OCR technology while to match the words in the prescription with those in the dataset we will use the fuzzywuzzy library.
# 
# OCR pdf: https://pypi.org/project/PyPDF2/
# 
# OCR jpg: https://www.jaided.ai/easyocr/tutorial/
# 
# FuzzyWuzzy: https://pypi.org/project/fuzzywuzzy/

# # Preliminary operations
# 
# Load libraries and dataset

#pip install  pypdf langchain tika typing fuzzywuzzy pymupdf easyocr

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
import gradio as gr

#max display
#pd.set_option('display.max_rows', None)

dataset = pd.read_csv('https://github.com/SimoneFarallo/public_and_social_services/raw/main/data/final_data_cleaned.csv')
dataset = dataset.drop(dataset.columns[0], axis=1)
dataset.head()

# # Automatic OCR Search
# 
# Taking the functions created earlier as a reference, we create a function that takes both pdf and png as input, also modify the output to be a dataframe so that it can be filtered later

reader = easyocr.Reader(['it'])

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


cd C:\Users\Simone\Documents\Desktop\public_and_social_services\ricette

output_ricetta_1_png = automatic_ocr_search('ricetta_1.png', dataset)
output_ricetta_1_png.head(10)

output_ricetta_2_pdf = automatic_ocr_search('ricetta_2.pdf', dataset)
output_ricetta_2_pdf.head(10)

output_ricetta_3_png = automatic_ocr_search('ricetta_3.png', dataset)
output_ricetta_3_png.head(10)

output_ricetta_3_pdf = automatic_ocr_search('ricetta_3.pdf', dataset)
output_ricetta_3_pdf.head(10)

output_ricetta_4_pdf = automatic_ocr_search('ricetta_4.pdf', dataset)
output_ricetta_4_pdf.head(10)

# # Search tool with fuzzy
# 
# This function does the same thing as the others, but as input it takes a string 

#Function to search structures directly with performance names
def search_facilities(words):
    matches = []
    data = {}

    for word in words:
        if not isinstance(word, str): #Check if the word is a string, otherwise raise a TypeError
            raise TypeError("The word of interest must be a string.")
        scores = process.extract(word, dataset['Codice prestazione ambulatoriale'], scorer=fuzz.token_set_ratio, limit=1) #Extract matching scores between the word and the dataset
        filtered_scores = [score for score in scores if score[1] >= 80] #Filter scores based on a threshold of 80%
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
    return df

output_query = search_facilities(['calcitonina','emocromo'])
output_query.head()

# # Filter dataset
# 
# This function allows the dataset to be filtered by city and facility type, ideally other filters can be added

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

#Filter for Brescia city
filter_data(output_ricetta_3_png,'BRESCIA')

#Filter for Bergamo city  and private structure
filter_data(output_ricetta_4_pdf,'BERGAMO','SÃ¬')

#Filter for Como city and private strcture
filter_data(output_query,'COMO','SÃ¬')

# # Interface gradio

import gradio as gr

# Define the function to be included in the interface
def automatic_ocr_search_interface(
    file: gr.inputs.File,
    comune: str = None,
    risposta_strutt: str = None
):
    # Get the path to the file
    file_path = file.name

    # Run your original function with the file path (string) and the DataFrame
    df = automatic_ocr_search(file_path, dataset)

    # Filters DataFrame if the filtering parameters are specified
    if comune is not None or risposta_strutt is not None:
        df = filter_data(df, comune, risposta_strutt)

    
    return df

# Define the inputs for the user interface
file_input = gr.inputs.File(label="File")
comune_input = gr.inputs.Textbox(label="Comune")
risposta_strutt_input = gr.inputs.Textbox(label="Struttura privata")

# Define the user interface using your Gradio function and the defined inputs
interface = gr.Interface(
    fn=automatic_ocr_search_interface,
    inputs=[file_input, comune_input, risposta_strutt_input],
    outputs=["dataframe"],
    title="Matching Recipe to Dataset",
    description="Insert here your recipe and discover structure in Lombardy.",
    outputs_labels=["Matched Data", "Filtered Data"]
)

# Run interface
interface.launch(share=True)

#Define the function to be included in the interface
def search_facilities_interface(words):
    try:
        df = search_facilities(words)
        unique_values = df
        return unique_values
    except TypeError as e:
        return str(e)

# Define the user interface using your Gradio function and the defined inputs
iface = gr.Interface(fn=search_facilities_interface, inputs="text", outputs="dataframe")

# Run interface
iface.launch()

