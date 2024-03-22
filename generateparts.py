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
    
    print(id)

    #tOdO
    if id == "08-06":
        print("YYY Urunk színeváltozása 08-06-ra van berakva hibásan. És ezt kézzel kéne megcsinálni.")
        return {
            "type" : None,
            "ref" : None,
            "teaser" : None,
            "title" : None,
            "text" : text,
            "ending" :  None
        }

    if id == "11-02":
        print("YYY Halottak napján 11-02-re az evangélium mindenféle és bármi. És ezt kézzel kéne megcsinálni.")
        return {
            "type" : None,
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
        print("!!! Itt többféle lehetőség van, ezért fontos lenne majd kézzel megcsinálni")
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


    if len(text) < 300 and type == None:        
        return {
            "type" : None,
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


sources = ["vasA", "vasB", "vasC","olvasmanyok","szentek"]
for name in sources:        
    print("XXXX " + name)
    print("XXXX " + name)
    print("XXXX " + name)
    datas = []
    for row in katolikusData[name]:
        if name == "szentek":
            id = row["datum"]
        else:
            id = row["kod"]

        data = {
            'id' : id,
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


        part = {
            'type': None,
            'ref' : None,
            'teaser' : row['alleluja'],
            'text' : row['alleluja']
        }
        if id.startswith("NAB"):
            part['type'] = "evangélium előtti vers"
        else:
            part['type'] = "alleluja"
        data["parts"].append(part)     
        
        if row['evangelium'] != '':
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