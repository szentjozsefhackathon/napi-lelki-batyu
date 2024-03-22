import requests
import xmltodict
import simplejson
import csv
import re
import Levenshtein


def loadKatolikusData():

    katolikusData = {}
    sources = ["konyorgesek", "konyorgesekszentek", "olvasmanyok", "saint", "szentek", "vasA", "vasB", "vasC"]
    sources = ["olvasmanyok", "vasA", "vasB", "vasC","szentek"]
    for name in sources:        
        with open('sources/' + name + '.csv', 'r',encoding="utf8") as file:
            csv_reader = csv.DictReader(file,delimiter=",")
            katolikusData[name] = [row for row in csv_reader]            
    return katolikusData

katolikusData = loadKatolikusData()

def partFromReading(text):
    
    firstLine = text.split('\n', 1)[0]
    

    if firstLine == "<i>Hosszabb forma:</i>":
        text = text.split('\n', 2)[2]
    elif firstLine == "<i>Hosszabb forma:</i><br>":
        text = text.split('\n', 1)[1]


    title = text.split('\n', 1)[0]
    
    
    if title.split(' ', 1)[0] == "SZENTLECKE":
        type = "szentlecke"
    elif title.split(' ', 1)[0] == "OLVASMÁNY":
        type = "olvasmány"
    elif title.split(' ', 2)[1] == "EVANGÉLIUM":
        type = "evangélium"
    elif title.startswith("A MI URUNK JÉZUS KRISZTUS KÍNSZENVEDÉSE"):
        type = "passió"
    else:
        print("!!! Ez vajon mi lehet? " + title)
        type = None


    print(row["kod"])

    teaser = text.split('\n', 3)[2]
    if teaser.startswith('<i>'):        
        if re.match(r'(.*)</i>(<br>|)$', teaser):
            teaser = teaser
            delete = 2
        elif re.match(r'(.*)</i>(<br>|)$', text.split('\n', 4)[3]):
            teaser = text.split('\n', 4)[2] + text.split('\n', 4)[3]
            delete = 3            
        elif re.match(r'(.*)</i>(<br>|)$', text.split('\n', 5)[4]):
            teaser = text.split('\n', 5)[2] + text.split('\n', 5)[3]  + text.split('\n', 5)[4]
            delete = 4
        else:            
            delete = 1
                        

        pattern = r'^<i>(.*)</i>(<br>|)$'
        if re.match(pattern, teaser.strip()):
            teaser = re.sub(pattern, r'\1', teaser.strip())
        else:
            print("!!! A teasert jól átkéne nézni, mert gond van itt majmócák! " + teaser)
        
    else:
        delete = 1
        teaser = None

    text = text.split("\n",delete + 1)[delete + 1 ]

    # Amikor van hosszabb - rövidebb forma, akkor megzakkanunk, ha nem így csináljuk
    if( type == "passió" ):
        ending = None    
    else:
        ending = text[text.rfind('\n') + 1 :].strip()

    if type == "evangélium" and ending != "Ezek az evangélium igéi.":
        print("!!! Az evangéliumot kézzel át kell nézni! " + ending)
    if ( type == "szentlecke" or type == "olvasmány" ) and ending != "Ez az Isten igéje.":
        print("!!! Az olvasmányt/szentleckét kézzel át kell nézni! " + ending)
    else:        
        text = text[:text.rfind('\n')].strip()

    text = re.sub(r'^<br>',r'',text)
    text = re.sub(r'^<br>',r'',text)
    text = re.sub(r'<br>$',r'',text)
    text = re.sub(r'<br>$',r'',text)
   
    return {
        "type" : type,
        "ref" : None,
        "teaser" : teaser,
        "title" : title,
        "text" : text,
        "ending" :  ending
    }


def partFromPsalm(text):

    teaser = "mm"
    title = None


    return {
        "type" : "zsoltár",
        "ref" : None,
        "teaser" : text.split('\n')[0],
        "text" : text        
    }


sources = ["vasA", "vasB", "vasC"]
for name in sources:        
    print("XXXX " + name)
    print("XXXX " + name)
    print("XXXX " + name)
    datas = []
    for row in katolikusData[name]:

        data = {
            'id' : row["kod"],
            'name' : row["nev"],
            'parts' : []
            }

        part = partFromReading(row['elsoolv'])
        part['ref'] = row['elsoolvhely']
        data["parts"].append(part)

        part = partFromPsalm(row['zsoltar'])
        part['ref'] = row['zsoltarhely']
        data["parts"].append(part)

        part = partFromReading(row['masodikolv'])
        part['ref'] = row['masodikolvhely']
        data["parts"].append(part)    

        part = {
            'type': None,
            'ref' : None,
            'teaser' : row['alleluja'],
            'text' : row['alleluja']
        }
        if row["kod"].startswith("NAB"):
            part['type'] = "evangélium előtti vers"
        else:
            part['type'] = "alleluja"
        data["parts"].append(part)     
        
        part = partFromReading(row['evangelium'])
        part['ref'] = row['evhely']
        data["parts"].append(part)   

        datas.append(data)

    #"azonosito","nev","kod","datum","egyetemeskonyorgesek","idezet"

    with open(name + ".json", "w") as breviarDataFile:
            # magic happens here to make it pretty-printed
            breviarDataFile.write(
                simplejson.dumps(datas, indent=4, sort_keys=False)
            )



#print(katolikusData['szentek'])