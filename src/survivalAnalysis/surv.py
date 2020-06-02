"""
Labeling survival data:

To label the survival data, I will do the following:
  * An HR > 2 and Cox p-value < 0.05 will be UPREG
  * An HR < 0.5 and Cox p-value < 0.05 will be DOWNREG
  * Everything else: NEUTRAL

@author: Scott Campit
"""
import os
import pandas as pd


def make_surv(input, cox, hr_up, hr_low, filename='str'):
    """
    make_surv will make a csv file containing the annotations by the Cox p-value and Hazard Ratio thresholds specified by the user. This file needs to be manually edited for multiple modes.
    """
    # Filters
    remove_col = ["TYPE", "ID_DESCRIPTION", "DATA_POSTPROCESSING", "DATASET", "SUBTYPE", "ENDPOINT", "COHORT", "CONTRIBUTOR",
                  "PROBE ID", "ARRAY TYPE", "N", "CUTPOINT", "MINIMUM P-VALUE", "CORRECTED P-VALUE", "ln(HR-high / HR-low)", "ln(HR)"]
    cancers = ["Breast cancer", "Ovarian cancer", "Colorectal cancer", "Lung cancer",
               "Prostate cancer", "Skin cancer", "Brain cancer", "Renal cell carcinoma", "Blood cancer"]

    # Process data and only get the COX P-value and Hazard ratio
    df = pd.read_excel(input)
    df = df.drop(columns=remove_col, axis=1)
    df["HR [95% CI-low CI-upp]"] = df["HR [95% CI-low CI-upp]"].str.replace(
        '\[(.*?)\]', '', regex=True)
    df = df[df["CANCER TYPE"].isin(cancers)]
    df["HR [95% CI-low CI-upp]"] = df["HR [95% CI-low CI-upp]"].apply(
        pd.to_numeric)
    df["SURV"] = ""

    # Make the actual labels
    df["SURV"].loc[(df["HR [95% CI-low CI-upp]"] >= hr_up)
                   & (df["COX P-VALUE"] <= cox)] = "UPREG"
    df["SURV"].loc[(df["HR [95% CI-low CI-upp]"] <= hr_low)
                   & (df["COX P-VALUE"] <= cox)] = "DOWNREG"
    df["SURV"].loc[(df["HR [95% CI-low CI-upp]"] >= hr_up)
                   & (df["COX P-VALUE"] > cox)] = "NEUTRAL"
    df["SURV"].loc[(df["HR [95% CI-low CI-upp]"] <= hr_low)
                   & (df["COX P-VALUE"] > cox)] = "NEUTRAL"
    df["SURV"].loc[(df["HR [95% CI-low CI-upp]"] < hr_up)
                   & (df["HR [95% CI-low CI-upp]"] > hr_low)] = "NEUTRAL"

    # Majority vote on the labels if there are multiple genes and they each have different labels
    df = df.groupby(['ID_NAME', 'CANCER TYPE'])[
                    'SURV'].agg(pd.Series.mode).to_frame()
    df = df.reset_index()

    # I physically edited the xlsx file. Need to devise conditional rule set to automatically determine labels for multiple modes
    df.to_excel(filename+'.xlsx', index=False)

# Make labels
#make_surv("./../raw/prognoscan/prognoscan.xlsx", cox=0.05, hr_up=1.1, hr_low=0.9, filename='lax')
#make_surv("./../raw/prognoscan/prognoscan.xlsx", cox=0.05, hr_up=2.0, hr_low=0.5, filename='stringent')

def count_prognoscan(input):
    """
    Another sanity check
    """
    # Filters
    remove_col = ["TYPE", "ID_DESCRIPTION", "DATA_POSTPROCESSING", "DATASET", "SUBTYPE", "ENDPOINT", "COHORT","PROBE ID", "ARRAY TYPE", "CUTPOINT", "MINIMUM P-VALUE", "CORRECTED P-VALUE", "ln(HR-high / HR-low)", "ln(HR)"]
    cancers = ["Breast cancer", "Ovarian cancer", "Colorectal cancer", "Lung cancer", "Prostate cancer", "Skin cancer", "Brain cancer", "Renal cell carcinoma", "Blood cancer"]

    # Process data and only get the COX P-value and Hazard ratio
    df = pd.read_excel(input)
    df = df.drop(columns=remove_col, axis=1)
    df = df[df["CANCER TYPE"].isin(cancers)]

    df["HR [95% CI-low CI-upp]"] = df["HR [95% CI-low CI-upp]"].str.replace(
        '\[(.*?)\]', '', regex=True)
    df["HR [95% CI-low CI-upp]"] = df["HR [95% CI-low CI-upp]"].apply(
        pd.to_numeric)
    df["SURV"] = ""

    df = df.drop_duplicates(subset='CONTRIBUTOR', keep='first')
    print(df['N'].sum())

#count_prognoscan("./raw/prognoscan/prognoscan.xlsx")

def make_model(labels, filpath, filname):
    """
    make_model makes new model and integrates the labels specified in the make_surv function.
    """
    canc_dict = {
        'Breast cancer': 'breast',
        'Brain cancer': 'cns',
        'Colorectal cancer': 'colon',
        'Blood cancer': 'leukemia',
        'Skin cancer': 'melanoma',
        'Lung cancer': 'nsclc',
        'Ovarian cancer': 'ovarian',
        'Prostate cancer': 'prostate',
        'Renal cell carcinoma': 'renal'
        }

    if filpath is None:
        filpath = r"./data/original/"

    # Skip pan cancer model
    if filname == 'complex.csv':
        pass

    df = pd.read_excel(labels)
    df = df.replace({'CANCER TYPE': canc_dict})

    # Read in the existing model and format it for our analysis
    model = pd.read_csv(filpath+fil)
    canc, _ = os.path.splitext(filname)

    # Drop existing survival labels
    model = model.drop(columns="SURV", axis=1)

    # Create new survival label as empty and populate later
    tmp = df[df["CANCER TYPE"] == canc]
    tmp = tmp.drop(columns='CANCER TYPE')

    model = pd.merge(model, tmp, how='left', left_on='Gene',
                     right_on='ID_NAME').drop(columns='ID_NAME')
    model = model.fillna('NEUTRAL')

    model = model.set_index(['Gene', 'Cell Line'])
    model = model.reset_index()
    model.to_csv('./../data/stringent/'+canc+'.csv', index=False)
    return model

#path = r"./../data/original/"
#folder = os.listdir(path)

## Make cell line specific models
#for fil in folder:
#    model = make_model(r'./stringent.xlsx', filpath=path, filname=fil)

# Make the pan cancer model
#complex = []
#for fil in folder:
#    model = make_model(path, fil)
#    complex.append(model)
#df = pd.concat(complex)
#df.to_csv('./data/lax/complex.csv', index=False)
