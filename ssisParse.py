import xmltodict
import os,json
import yaml
import duckdb

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
    modelMeta = []
    analysisModels = returnValueFromConfig(configuration,modelKey)
    for model in analysisModels:
        #print("model: ", model)
        if model.get('name') == modelname:
            modelMeta = model
        if modelname is None:
            modelMeta.append(model)
    return modelMeta
             
def xmlToDict(ssis_file):
    data_dict = None
    with open(ssis_file) as dtsx_file:
        data_dict = xmltodict.parse(dtsx_file.read())
    return data_dict
    
CONFIG = loadParserConfig()

ssis_path = returnValueFromConfig(CONFIG,"[parserConfig].[ssisFolder]")

ssis_files = []

modelMeta = extractModelMeta(CONFIG,None)
duckdb.sql("install json")
duckdb.sql("load json")

for filename in os.listdir(ssis_path):
    full_path = os.path.join(ssis_path, filename) 
    if os.path.isfile(full_path):
        if os.path.splitext(full_path)[1] == ".dtsx":
            ssis_files.append(full_path)


for dtsx_file in ssis_files:
    ssis_dict = xmlToDict(dtsx_file)
    ssis_json_path = os.path.splitext(dtsx_file)[0] + ".json"
    with open(ssis_json_path,"w") as out_file:
        out_file.write(json.dumps(ssis_dict, indent=3))  

    data = duckdb.sql('select * from read_json_auto("{}",auto_detect=true, json_format="auto",maximum_depth=-1)'.format(ssis_json_path))
    print(data.columns)
    if not isinstance(modelMeta,list):
        modelMeta = [modelMeta]
        
    for modelM in modelMeta:
        sqltext = None
        for col in modelM.get("columns"):
            if sqltext is None:
                sqltext = "select "  + col.get("path") + " as " + col.get("name") 
            else:
                sqltext = sqltext + "," + col.get("path") + " as " + col.get("name") 
    
        if sqltext is not None:
            duckdb.sql("{} from data".format(sqltext)).to_csv("{}.csv".format(modelM.get("name")),header=True)
