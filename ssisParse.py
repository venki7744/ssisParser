from numpy import full
import xmltodict
import os,json
import pandas as pd
import yaml
from typing import Dict
import flatdict
import re,csv

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
    #parentPath =  cleanKey(modelMeta.get("parent"))
    #parentData = data.get(parentPath)
    if not isinstance(data,list):
        data = [data]
    rows = []
    keyList = list(data[0].keys())
    # with open("keylist.csv", "w") as keylst:
    #     csv_w = csv.DictWriter(keylst,dialect='excel',delimiter=",", fieldnames=["key"])
    #     csv_w.writeheader()
    #     for key in keyList:
    #         csv_w.writerow({"key":key})
    for row in data:
        out=dict()
        #print("row: ", row) 
        for column in modelMeta.get('columns'):
            if column["path"].find("@@List") > 0:
                col_regex = re.escape(column["path"]).replace('@@List\.',"(\d\.)?")
                r = re.compile(col_regex)
                subset_columns = list(filter(r.match,keyList))
                #print("KeyList: {} \n col_regex: {} Subset Columns: {}".format(keyList, col_regex,subset_columns))
                values = []
                for subset_column in subset_columns:
                    values.append(row.get(subset_column))
                out[column.get("name")] = values
            else:
                out[column.get("name")] = row.get(column.get("path"))
            #print("column: ", column)
            # column_parts = column.split(".@@List.")
            # column_parts_count = len(column_parts)
            # counter = [0]*column_parts_count
            
            
            #     
           
            #    if isinstance(dataset,list):
                    
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
    ssis_dict = dict(flatdict.FlatterDict(ssis_dict,delimiter = '.',))
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
    
   

