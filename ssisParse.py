from numpy import full
import xmltodict
import os,json
import pandas as pd
import yaml
from typing import Dict

def loadParserConfig():
    config_path = os.path.join(os.path.realpath(os.path.dirname(__file__)),"config.yml")
    configuration = None
    with open(config_path) as config_file:
        configuration = yaml.safe_load(config_file)
    #print("yaml config:", configuration)
    return configuration

def cleanKey(rawKey:str):
    return rawKey.replace("[","").replace("]","")

def returnValueFromConfig(configuration:dict, key:str):
    keysTree = key.split("].[")
    #print(f"keysTree: {keysTree}, data: {configuration}")
    data = configuration
    for key in keysTree:        
        cleanedKey = cleanKey(key)
        #print("cleaned Key: {}".format(cleanedKey))
        #print("inner data: ", data)
        data = data.get(cleanedKey)

    return data

def extractModelMeta(configuration, modelname):
    modelKey = "[analysisModels]"
    modelMeta = None
    analysisModels = returnValueFromConfig(configuration,modelKey)
    for model in analysisModels:
        #print("model: ", model)
        if model.get('name') == modelname:
            modelMeta = model
        if modelname is None:
            modelMeta.append(model)
    return modelMeta

def getModelDataAsPd(data, modelMeta):
    parentPath =  cleanKey(modelMeta.get("parent"))
    parentData = data.get(parentPath)
    if not isinstance(parentData,list):
        parentData = [parentData]
    rows = []
    for row in parentData:
        out=dict()
        #print("row: ", row) 
        for column in modelMeta.get('columns'):
            #print("column: ", column)
            out[column.get("name")] = row.get(cleanKey(column.get("path")))
        #print("out: ", out)
        rows.append(out)
    
    df = pd.DataFrame.from_records(rows)
    return df
             
def xmlToDict(ssis_file):
    data_dict = None
    with open(ssis_file) as dtsx_file:
        data_dict = xmltodict.parse(dtsx_file.read())
    return data_dict
    
CONFIG = loadParserConfig()

ssis_path = returnValueFromConfig(CONFIG,"[parserConfig].[ssisFolder]")

ssis_files = []

for filename in os.listdir(ssis_path):
    full_path = os.path.join(ssis_path, filename) 
    if os.path.isfile(full_path):
        if os.path.splitext(full_path)[1] == ".dtsx":
            ssis_files.append(full_path)

modelMeta = extractModelMeta(CONFIG,"connections")
#print("ModelMeta: ", modelMeta)
#print(f"SSIS Files: {ssis_files}")
for dtsx_file in ssis_files:
    ssis_dict = xmlToDict(dtsx_file)
    ssis_json_path = os.path.splitext(dtsx_file)[0] + ".json"
    with open(ssis_json_path,"w") as out_file:
        out_file.write(json.dumps(ssis_dict, indent=3))
    
    if not isinstance(modelMeta,list):
        modelMeta = [modelMeta]
    for modelM in modelMeta:
        outDF = getModelDataAsPd(ssis_dict, modelM)
        outfile = os.path.splitext(dtsx_file)[0] + "_" + modelM.get("name") + ".csv"
        print("outDF: ", outDF)
        outDF.to_csv(outfile, index = False)
    
   

