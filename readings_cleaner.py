import json

def loadKatolikusData():
    katolikusData = {}
    sources = ["olvasmanyok", "vasA", "vasB", "vasC","szentek","commentaries"]
    for name in sources:
        with open('readings/' + name + '.json', 'r',encoding="utf8") as file:
            katolikusData[name] = json.load(file)
    return katolikusData

def saveKatolikusData(katolikusData):
    for key, name in enumerate(katolikusData):
        with open("readings/" + name + ".json", "w", encoding='utf8') as katolikusDataFile:        
            katolikusDataFile.write(
                json.dumps(katolikusData[name], indent=4, sort_keys=False, ensure_ascii=False)
            )

def recursive(data, function):    
    if isinstance(data, str):
        return eval(function + '(data)')
    elif isinstance(data, list):
        returnList = []
        for item in data:
            returnList.append(recursive(item, function))
        return returnList
    elif isinstance(data, dict):
        returnDict = {}
        for key, name in enumerate(data):
            returnDict[name] = recursive(data[name], function)
        return returnDict
    elif data is None:
        return None
        
    raise Exception("Sorry, do not know this type")

def remove_rlnewline(data):
    return data.rstrip('\n').lstrip('\n').removeprefix("<br>").removesuffix("<br>")



   
katolikusData = loadKatolikusData()




katolikusData = recursive(katolikusData, "remove_rlnewline")
print(katolikusData)

saveKatolikusData(katolikusData)
