import requests
import xmltodict
import simplejson
import csv
import re
import Levenshtein
import datetime


with open('readings/errors.txt', 'w', encoding='utf8') as file:
        file.write(str(datetime.datetime.now()) +  " -- generateparts.py hibaüzenete:" + '\n')

def error(text):
    message = name + " - " + id + ": " + text
    print(message)
    with open('readings/errors.txt', 'a', encoding='utf8') as file:
        file.write(message + '\n')

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
    
    #tOdO
    if id == "08-06":
        error("YYY Urunk színeváltozása 08-06-ra van berakva hibásan. És ezt kézzel kéne megcsinálni.")
        return {
            "header" : None,
            "ref" : None,
            "teaser" : None,
            "title" : None,
            "text" : text,
            "ending" :  None
        }

    if id == "11-02":
        error("YYY Halottak napján 11-02-re az evangélium mindenféle és bármi. És ezt kézzel kéne megcsinálni.")
        return {
            "header" : None,
            "ref" : None,
            "teaser" : None,
            "title" : None,
            "text" : text,
            "ending" :  None
        }

    firstLine = text.split('\n', 1)[0]
    

    if firstLine == "<i>Hosszabb forma:</i>":
        text = text.split('\n', 2)[2]
    elif firstLine == "<i>Hosszabb forma:</i><br>":
        text = text.split('\n', 1)[1]

    if firstLine == "<i>Vagy:</i><br>" or firstLine == "<i>vagy</i><br>":
        error("!!! Itt többféle lehetőség van, ezért fontos lenne majd kézzel megcsinálni")
        text = text.split('\n', 1)[1]



    title = text.split('\n', 1)[0]
    
    
    if title.split(' ', 1)[0] == "SZENTLECKE":
        header = "szentlecke"
    elif title.split(' ', 1)[0] == "OLVASMÁNY":
        header = "olvasmány"
    elif title.split(' ', 2)[1] == "EVANGÉLIUM":
        header = "evangélium"
    elif title.startswith("A MI URUNK JÉZUS KRISZTUS KÍNSZENVEDÉSE"):
        header = "passió"
    else:
        error("!!! Ez vajon mi lehet? " + title)
        header = None


    if len(text) < 300 and header == None:        
        return {
            "header" : None,
            "ref" : None,
            "teaser" : None,
            "title" : None,
            "text" : text,
            "ending" :  None
        }

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
            error("!!! A teasert jól átkéne nézni, mert gond van itt majmócák! " + teaser)
        
    else:
        delete = 1
        teaser = None

    text = text.split("\n",delete + 1)[delete + 1 ]

    # Amikor van hosszabb - rövidebb forma, akkor megzakkanunk, ha nem így csináljuk
    if( header == "passió" ):
        ending = None    
    else:
        ending = text[text.rfind('\n') + 1 :].strip()

    if header == "evangélium" and ending != "Ezek az evangélium igéi.":
        error("!!! Az evangéliumot kézzel át kell nézni! " + ending)
    if ( header == "szentlecke" or header == "olvasmány" ) and ending != "Ez az Isten igéje.":
        error("!!! Az olvasmányt/szentleckét kézzel át kell nézni! " + ending)
    else:        
        text = text[:text.rfind('\n')].strip()

    text = re.sub(r'^<br>',r'',text)
    text = re.sub(r'^<br>',r'',text)
    text = re.sub(r'<br>$',r'',text)
    text = re.sub(r'<br>$',r'',text)
   
    return {
        "header" : header,
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
        "header" : "zsoltár",
        "ref" : None,
        "teaser" : text.split('\n')[0],
        "text" : text        
    }


sources = ["vasA", "vasB", "vasC","olvasmanyok","szentek"]
for name in sources:        
   
    datas = {}
    for row in katolikusData[name]:
        if name == "szentek":
            match = re.match(r'^(\d{2})\-(\d{2})([a-z]{0,1})$',row["datum"])
            if match:                    
                id = match[1] + "-" + match[2]
            else:
                id = row["datum"]
                error("!!! Szentről van szó, de nem jó a dátum formátuma! " + id)

            data = {
                'igenaptarId' : row["datum"],
                'name' : row["nev"],
                'parts' : []
                }
                                
        else:
            id = row["kod"]

            data = {
                'igenaptarId' : row["kod"],
                'name' : row["nev"],
                'parts' : []
                }


        if name == "olvasmanyok":
            
            if row['masodikolv'] != '':
                part1 = partFromReading(row['elsoolv'])
                part1['ref'] = row['elsoolvhely']
                part1['cause'] = "I. évben"

                part2 = partFromReading(row['masodikolv'])
                part2['ref'] = row['masodikolvhely']
                part2['cause'] = "II. évben"

                data["parts"].append([part1, part2])

            else:
                part = partFromReading(row['elsoolv'])
                part['ref'] = row['elsoolvhely']
                data["parts"].append(part)
            

            if row['masodikzsoltar'] != '':
                part1 = partFromPsalm(row['zsoltar'])
                part1['ref'] = row['zsoltarhely']
                part1['cause'] = "I. évben"
                                

                part2 = partFromPsalm(row['masodikzsoltar'])
                part2['ref'] = row['masodikzsoltarhely']
                part2['cause'] = "II. évben"
                data["parts"].append([part1, part2])

            
            else:
                part = partFromPsalm(row['zsoltar'])
                part['ref'] = row['zsoltarhely']
                data["parts"].append(part)                

        if name == "vasA" or name == "vasB" or name == "vasC" or "szentek":
            if row['elsoolv'] != '':
                part = partFromReading(row['elsoolv'])
                part['ref'] = row['elsoolvhely']
                data["parts"].append(part)

            part = partFromPsalm(row['zsoltar'])
            part['ref'] = row['zsoltarhely']
            data["parts"].append(part)

            if row['masodikolv'] != '':
                part = partFromReading(row['masodikolv'])
                part['ref'] = row['masodikolvhely']
                data["parts"].append(part)    

        if row['alleluja'] != '':
            part = {
                'header': None,
                'ref' : None,
                'teaser' : row['alleluja'],
                'text' : row['alleluja']
            }
            if id.startswith("NAB"):
                part['header'] = "evangélium előtti vers"
            else:
                part['header'] = "alleluja"
            data["parts"].append(part)     
        
        if row['evangelium'] != '':
            part = partFromReading(row['evangelium'])
            part['ref'] = row['evhely']
            data["parts"].append(part)   

        if id in datas:
            if(type(datas[id]) is dict):
                tmp = datas[id]
                datas[id] = []
                datas[id].append(tmp)
                datas[id].append(data)
            else:
                datas[id].append(data)
            
        else:
            datas[id] = data


    datas = dict(sorted(datas.items()))
    #"azonosito","nev","kod","datum","egyetemeskonyorgesek","idezet"

    with open("readings/" + name + ".json", "w", encoding='utf8') as breviarDataFile:
            # magic happens here to make it pretty-printed
            breviarDataFile.write(
                simplejson.dumps(datas, indent=4, sort_keys=False, ensure_ascii=False)
            )



#print(katolikusData['szentek'])