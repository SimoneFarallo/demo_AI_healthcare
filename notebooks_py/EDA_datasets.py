"""
Auto-converted from EDA_datasets.ipynb.
Generated for code-first workflow (.py).
"""

# # Exporation & cleaning dataset
# 
# In this notebook we are going to analyze all the possible datasets that will then be merged to be used as a knowledge base for information on "outpatient facilities"(prestazioni ambulatoriali)  and services.
# 
# We are going to clean and format each dataset, and then merge them

pip  install --quiet

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

#max display
pd.set_option('display.max_rows', None)

#Let's create a function to better analyze, unique values, null values and duplicates
def contatore(dataset):
    """
    Count the number of duplicates, null values, and unique values for each column in a dataset.
    
    :param dataset: The dataset to be analyzed (pandas DataFrame).
    :return: A dictionary containing the results for each column.
    """
    risultati = {}
    for colonna in dataset.columns:
        duplicati = dataset.duplicated(subset=colonna).sum()
        nulli = dataset[colonna].isnull().sum()
        unici = dataset[colonna].nunique()
        risultati[colonna] = {
            'duplicates:': duplicati,
            'null values': nulli,
            'unique values ': unici
        }
    return risultati

# ## Prestazioni ambulatoriali Lombardia
# 
# The dataset refers to all facilities in Lombardy that can perform outpatient services.
# 
# Reference link: https://www.dati.lombardia.it/Sanit-/Prestazioni-Ambulatoriali/d4mg-9zw3
# 
# Columns description https://github.com/SimoneFarallo/public_and_social_services/blob/main/dataset/prest_amb_documentation.pdf

prest_amb = pd.read_csv('https://raw.githubusercontent.com/SimoneFarallo/public_and_social_services/main/data/prest_amb.csv')
prest_amb.head()

prest_amb.info()

contatore(prest_amb)

##Analyze price column
plt.hist(prest_amb['TARIFFA_PREST_EURO'], bins=5)
plt.xlabel('Price')
plt.ylabel('Frequency')
plt.title('Distribution of price')
plt.show()



sns.boxplot(x=prest_amb['TARIFFA_PREST_EURO'])
plt.xlabel('Price')
plt.title('Distribution of price')
plt.show()

# The information regarding the price is unclear, the documentation does not help us and we are unable to inetrpret the values, we decide not to use this information, but to look for another price list

#Let's take only the columns that might be useful.
prest_amb = prest_amb[['COD_PREST_AMBLE','BRANCA_REGLE','COD_BRANCA_MINSLE','COD_BRANCA_REGLE','TIPO_PREST','STRUT','COD_STRUT','INDIRIZZO','COMUNE_STRUT','PROV_STRUT','COD_ASL','ASL','ENTE',]]
prest_amb.head()

# ## Strutture accreditate
# 
# This dataset refers to the list of accredited healthcare facilities in Lombardy.
# 
# Accredited facilities are defined as: An accredited facility is a private facility that has, however, entered into an agreement with the National Health System (NHS), and therefore provides health services by asking the citizen to pay only the co-payment.
# 
# Reference link: https://www.regione.lombardia.it/wps/portal/istituzionale/HP/DettaglioServizio/servizi-e-informazioni/Cittadini/salute-e-prevenzione/strutture-sanitarie-e-sociosanitarie/strutture-sanitarie-accreditate/strutture-sanitarie-accreditate
# 
# There is no documentation regarding the columns.

strut_accr = pd.read_excel('https://github.com/SimoneFarallo/public_and_social_services/raw/main/data/elenco_strutture_sanitare.xlsx',skiprows = 2)
strut_accr.head()

strut_accr.info()

contatore(strut_accr)

#Let's take only the columns that might be useful.
strut_accr = strut_accr[['Codice Struttura',' Ente','Tipo Struttura','TEL','FAX','Privata']]
strut_accr.head()

# ## Transcodifica codice e nomenclatura
# 
# This dataset refers to performance codes, plus there are small descriptions for each type of performance; 
# It is used by the Lombardy region to code outpatient benefit codes from other regions.
# 
# The two datasets will refer to the nomenclature of outpatient specialty analysis, the difference between the two datasets is that the former refers to the SISS/SAR.
# The SISS/SAR provides the services to support the prescription of dematerialized electronic prescriptions by ensuring synchronous transmission with MEF's SAC system and applying the appropriate controls to ensure the formal and content correctness of prescriptions. The dematerialized prescription in the prescription and dispensing stages is based solely on the electronic data available on the SISS and the Central Acceptance System (SAC) of the Ministry of Economy and Finance (MEF).
# 
# Taking into consideration the following reference:
# 
#  https://www.lavoro.gov.it/strumenti-e-servizi/Sistema-informativo-servizi-sociali/Pagine/default.aspx.
#  
#  So we keep in consideration the first dataset obtained.
# 
# Link reference: https://www.dati.lombardia.it/Sanit-/Transcodifica-Codici-prestazioni/7ugz-vcug.
# 
# There is no documentation regarding the columns.

xls = pd.ExcelFile('https://github.com/SimoneFarallo/public_and_social_services/raw/main/data/Transcodifica_codici.xlsx')
cod_SIIS = pd.read_excel(xls, 'Tabella complessiva cod SISS', skiprows = 1)
set_rif = pd.read_excel(xls, 'Tabella sole prestaz per set', skiprows = 1)

cod_SIIS.head()

set_rif.head()

contatore(cod_SIIS)

cod_SIIS.head()

#Let's take only the columns that might be useful.
cod_SIIS = cod_SIIS[['PRESTAZ_AMB_SET_RIFERIMENTO_ID','PRESTAZIONE_DESC','PRESTAZ_AMB_DESC']]
cod_SIIS.head()

# This dataset will be used only as a reference, preset names change and may create inconsistencies and inaccuracies

# ## Nomenclatura e prezzi prestazioni ambulatoriali NAZIONALE
# 
# This dataset refers to outpatient services nationwide, various analyses and prices for public facilities are described.
# is the only information we were able to obtain at the national level, for more details look at reference links.
# 
# Link reference: https://www.salute.gov.it/portale/temi/p2_6.jsp?id=1767&area=programmazioneSanitariaLea&menu=lea
# 
# There is no documentation regarding the columns.

nom_nazionale = pd.read_excel('https://github.com/SimoneFarallo/public_and_social_services/raw/main/data/nomenclatore_specialistica_2013_pw.xlsx', skiprows = 4)
nom_nazionale = nom_nazionale[['CODICE','DESCRIZIONE','Unnamed: 4']]
nom_nazionale = nom_nazionale.rename(columns={'Unnamed: 4': 'PREZZO'})
nom_nazionale.head()

contatore(nom_nazionale)

#Removing dots from the "Values" column.
nom_nazionale['CODICE'] = nom_nazionale['CODICE'].str.replace('.', '')
nom_nazionale.head()

# # Merging dataset
# 
# After performing an exploratory analysis and cleaning the individual datasets, we go on to merge the datasets into a single csv file

# ## Prestazioni + strutture accreditate

merg1 = prest_amb.merge(strut_accr ,how='left', left_on='COD_STRUT', right_on='Codice Struttura')
display(merg1.head(5))

contatore(merg1)

merg1.info()

merg1.columns

check_merg1 = merg1[['COD_STRUT','Codice Struttura','STRUT']]
display(check_merg1.head(20))

# ## Prestazioni + strutture accreditate + nomenclatura nazionale

nom_nazionale.head()

merg2 = merg1.merge(nom_nazionale ,how='left', left_on='BRANCA_REGLE', right_on='CODICE')
display(merg2.head(5))

merg2.info()

contatore(merg2)

# All datasets have been merged, a manual check has been done, doing several tests, there should be no inconsistencies, the data is not complete but we can't check this problem with at the documentation at our disposal

# # Dataset finale 
# 
# At this stage we recheck the final dataset and make a few changes, to make it as clear as possible.

final_data = merg2
final_data.head()

final_data.info()

final_data.columns

#Following the documentation available to us, we change the names of the columns to make them easier for the end user to interpret
final_data = final_data.rename(columns={'COD_PREST_AMBLE': 'Codice prestazione ambulatoriale',
                         'BRANCA_REGLE': 'Codice branca regionale',
                         'COD_BRANCA_MINSLE': 'Codice branca ministeriale',
                         'COD_BRANCA_REGLE': 'Branca regionale',
                         'TIPO_PREST': 'Tipo di prestazione',
                         'STRUT': 'Nome struttura',
                         'COD_STRUT': 'Codice struttura erogante',
                         'INDIRIZZO': 'Indirizzo',
                         'COMUNE_STRUT': 'Comune struttura',
                         'PROV_STRUT': 'Provincia struttura',
                         'COD_ASL': 'Codice ASL territoriale',
                         'ASL': 'Descrizione ASL',
                         'ENTE': 'Ente',
                         'Codice Struttura': 'Codice struttura',
                         'Ente': 'Ente struttura',
                         'Tipo Struttura': 'Tipo struttura',
                         'TEL': 'Telefono',
                         'FAX': 'Fax',
                         'Privata': 'Struttura privata',
                         'PRESTAZ_AMB_SET_RIFERIMENTO_ID': 'ID prestazione ambulatoriale',
                         'PRESTAZ_AMB_DESC': 'Dettagli prestazioni',
                         'COD_PRESTAZ_AMB': 'Codice prestazione ambulatoriale_1',
                         'DESCRIZIONE': 'Descrizione',
                         'PREZZO': 'Prezzo medio'})
final_data.head()

#The dataset will be used as output, so we keep only the columns that may be useful to the end user
final_data = final_data[['Codice prestazione ambulatoriale','Codice branca regionale', 'Branca regionale','Tipo di prestazione','Nome struttura','Comune struttura','Provincia struttura','Indirizzo','Descrizione ASL','Codice struttura','Tipo struttura','Telefono','Fax','Struttura privata','Prezzo medio' ]]
#I change the null values, to make the dataset clearer
final_data = final_data.fillna('Info non disponibile')
final_data.head()

contatore(final_data)

final_data.info()

#final_data.to_csv('final_data_cleaned.csv')

