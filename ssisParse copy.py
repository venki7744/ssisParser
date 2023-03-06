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
        print("model: ", model)
        if model.get('name') == modelname:
            modelMeta = model
    return modelMeta

def getModelDataAsPd(data, modelMeta):
    df = pd.DataFrame()
    parentPath =  cleanKey(modelMeta.get("parent"))
    for row in data.get(parentPath): 
        for column in modelMeta:
            out[column.get("name")] = row.get(cleanKey(column.get("path")))
        df.append(out,ignore_index = True)
    
    return df
             
def xmlToJson(ssis_file):
    data_dict = None
    with open(ssis_file) as dtsx_file:
        data_dict = xmltodict.parse(dtsx_file.read())
    dtsx_json = json.dumps(data_dict, indent=3)
    #df = pd.DataFrame.from_dict(data_dict)
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
print("ModelMeta: ", modelMeta)
#print(f"SSIS Files: {ssis_files}")
for dtsx_file in ssis_files:
    ssis_json = xmlToJson(dtsx_file)
    ssis_json_path = os.path.splitext(dtsx_file)[0] + ".json"
    with open(ssis_json_path,"w") as out_file:
        out_file.write(json.dumps(ssis_json, indent=3))
    
    package_properties = ssis_json["DTS:Executable"]["DTS:Property"]
    
    if "DTS:ConnectionManager" in ssis_json["DTS:Executable"]:
        connections = ssis_json["DTS:Executable"]["DTS:ConnectionManager"]
    else:
        connections = ssis_json["DTS:Executable"]["DTS:ConnectionManagers"]
    
    if "DTS:Executable" in ssis_json["DTS:Executable"]:
        executable_components = ssis_json["DTS:Executable"]["DTS:Executable"]["DTS:ObjectData"]["pipeline"]["components"]["component"]
    else:
        executable_components = ssis_json["DTS:Executable"]["DTS:Executables"]["DTS:Executable"]
    
    # print("**************Connections***************")
    # for connection in connections:
    #     print(connection["DTS:Property"])
    #     print(connection["DTS:ObjectData"])
        
    print("**************Components***************")
    ssis_json_component_path = os.path.splitext(dtsx_file)[0] + "_components.json"
    with open(ssis_json_component_path,"w") as out_file:
        out_file.write(json.dumps(executable_components, indent=3))
    # for component in executable_components:
    #     print(component)
    
    
   

