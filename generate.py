import requests
import xmltodict
import simplejson
import csv
import re
import Levenshtein


def downloadBreviarData():

    # get breviarData from url
    url = "https://breviar.kbs.sk/cgi-bin/l.cgi?qt=pxml&d=*&m=*&r=2024&j=hu"
    response = requests.get(url)
    breviarData = xmltodict.parse(response.content)

    # now write output to a file
    with open("breviarData.json", "w") as breviarDataFile:
        # magic happens here to make it pretty-printed
        breviarDataFile.write(
            simplejson.dumps(breviarData, indent=4, sort_keys=True)
        )

def loadBreviarData():
    f = open("breviarData.json")
    data = simplejson.load(f)
    return data

def loadKatolikusData():
    katolikusData = {}
    sources = ["konyorgesek", "konyorgesekszentek", "olvasmanyok", "saint", "szentek", "vasA", "vasB", "vasC"]
    sources = ["olvasmanyok", "vasA", "vasB", "vasC","szentek"]
    for name in sources:
        with open('sources/' + name + '.csv', 'r',encoding="utf8") as file:
            csv_reader = csv.DictReader(file)
            katolikusData[name] = [row for row in csv_reader]
    return katolikusData    

def transformCelebration(celebration: dict):
    transformedCelebration = {
        'yearLetter': celebration['LiturgicalYearLetter'],
        'week': celebration['LiturgicalWeek'],
        'weekOfPsalter': celebration['LiturgicalWeekOfPsalter'],
        'season': celebration['LiturgicalSeason']['@Id'],
        'seasonText': celebration['LiturgicalSeason']['#text'],
        'typeLocal': celebration['LiturgicalCelebrationTypeLocal'],
        'level': celebration['LiturgicalCelebrationLevel'],
        'required': celebration['LiturgicalCelebrationRequired'],
        'name': celebration['LiturgicalCelebrationName'],
        'readingsBreviarId': celebration['LiturgicalReadingsId']    
    }

    # LiturgicalCelebrationName can contain HTML 
    if celebration['LiturgicalCelebrationName'] and "#text" in celebration['LiturgicalCelebrationName']:
        transformedCelebration['name'] = celebration['LiturgicalCelebrationName']['#text']
        
    # LiturgicalCelebrationColor can be without text if it's in special seasion
    transformedCelebration['colorId'] = celebration['LiturgicalCelebrationColor']['@Id']
    if "#text" in  celebration['LiturgicalCelebrationColor']:
        transformedCelebration['colorText'] = celebration['LiturgicalCelebrationColor']['#text']

    # LiturgicalCelebrationCommunia can be absent, or list, or one (dict) 
    if "LiturgicalCelebrationCommunia" in celebration:
        if not isinstance(celebration['LiturgicalCelebrationCommunia'], dict):
            transformedCelebration['comunia'] = celebration['LiturgicalCelebrationCommunia']
        else:
            transformedCelebration['comunia'] = [ celebration['LiturgicalCelebrationCommunia'] ]        
    else:
        transformedCelebration['comunia'] = None


    return transformedCelebration

def findReadings(celebration: dict):
    
    readingHasFound = False

    if celebration['readingsBreviarId'] is None:
        print(calendarDay['DateISO'])
        print("ERROR: None")
        return False
    
    
    #
    # Évközi (C), húsvéti (V), nagyböjti (P), adventi (A),  idő vasárnapjai ill. napjai    
    #
    result = re.search("^(\d{1,2})([ACVP]{1})(\d{0,1})$", celebration['readingsBreviarId'])    
    if result:
        # melyik táblázatban vannak az adatok: vasA, vasB, vasC, olvasmanyok
        if result.group(3) == "":
            if result.group(2) == "C":
                katolikusDataTable = 'vas' + celebration['yearLetter']                
            else:
                # Mivel most B év van, ezért az a táblázat a legfrissebb, upsz
                katolikusDataTable = 'vasB'
        else:
            katolikusDataTable = "olvasmanyok"
        
        # mi a 'kod' azaz az adott nap rövidítése
        kodok = { "A" : "ADV", "C" : "EVK", "P": "NAB", "V" : "HUS" }
        katolikusDataKod = kodok[result.group(2)] + str(result.group(1)).zfill(2)
        napok = { 1: "Hetfo", 2: "Kedd", 3: "Szerda", 4: "Csutortok", 5: "Pentek", 6: "Szombat"}
        if not result.group(3) == "":
            katolikusDataKod += result.group(3) + napok[ int(result.group(3))]
        celebration['readingsId'] = katolikusDataKod


        #Megkeressük a megfelelő adatokat        
        if not katolikusDataTable in katolikusData:
            print(calendarDay['DateISO'])
            print("ERROR: Nincs '" + katolikusDataTable + "'")
            return False
        
        rowFound = False
        for row in katolikusData[katolikusDataTable]:
            if row['kod'] == katolikusDataKod:
                rowFound = True
                readingHasFound = True
                ## IDE JÖN BE A CUCC!
                celebration['readings'] = row
                return True
                ## EDDIG
        if not rowFound:
            print(calendarDay['DateISO'])
            print("ERROR: Nincs '" + katolikusDataKod + "' a '" + katolikusDataTable +"'-ban/ben")
            return False
        
    #
    # Egyes dátumokhoz tartozó ünnepek olvasmányainak kikeresése, figyelve arra, hogy egy napra több minden is juthat. Uuuupsz.
    # Dec 25 extra :D
    #                  
    result = re.search("^(\d{1,2})\.(\d{1,2})\.$", celebration['readingsBreviarId'])    
    if result:
        datum = result.group(2).zfill(2) + "-" + result.group(1).zfill(2)
        
        #Megkeressük a megfelelő adatokat        
        if not "szentek" in katolikusData:
            print(calendarDay['DateISO'])
            print("ERROR: Nincs 'szentek'")
            return False

        possibilities = []
        for row in katolikusData['szentek']:
            if re.search("^" + datum,row['datum']):
                possibilities.append(row)                                
        if len(possibilities) < 1:
            print(calendarDay['DateISO'])
            print("ERROR: Nincs '" + datum + "'-hoz ( " + celebration['name'] + ") egyáltalán olvasmány")
            return False
        if len(possibilities) == 1:
            ## IDE JÖN BE A CUCC!
            celebration['readings'] = possibilities[0]
            celebration['readingsId'] = possibilities[0]['datum']
            readingHasFound = True
            return True
        
        if len(possibilities) > 1 and datum == '12-25':
            ## IDE JÖN BE A CUCC!
            celebration['readings'] = possibilities
            celebration['readingsId'] = '12-25'
            readingHasFound = True
            return True

        for possibility in possibilities:
            if Levenshtein.ratio(str(celebration['name']), possibility['nev']) > 0.8:
                ## IDE JÖN BE A CUCC!
                celebration['readings'] = possibility
                celebration['readingsId'] = possibility['datum']
                readingHasFound = True
                return True
            
        print(calendarDay['DateISO'])
        tmp = ""
        for row in possibilities:
            if celebration['name']:
                tmp1 = celebration['name']
            else:
                tmp1 = "névtelen"
            tmp += row['nev'] + ", "            
        print("ERROR: Nincs eléggé jól passzoló olvasmány. Amit keresünk: '" + tmp1 + "'. Amik vannak: " + tmp)
        
        return False

    if not readingHasFound:
        print(calendarDay['DateISO'])
        print("ERROR: Nincs '" + celebration['readingsBreviarId'] + "'")

downloadBreviarData()
breviarData = loadBreviarData()
katolikusData = loadKatolikusData()

for calendarDay in breviarData['LHData']['CalendarDay']:
    lelkiBatyu = {}
    lelkiBatyu['date'] = {
        'ISO': calendarDay['DateISO'],
        'dayOfYear' : calendarDay['DayOfYear'],
        'dayofWeek' : calendarDay['DayOfWeek']['@Id'],
        'dayofWeekText' : calendarDay['DayOfWeek']['#text']
    }

    #for celebration in calendarDay
    lelkiBatyu['celebration'] = []
    if not isinstance(calendarDay['Celebration'], dict):        
        for celebration in calendarDay['Celebration']:
            lelkiBatyu['celebration'].append(transformCelebration(celebration))
    else:
        lelkiBatyu['celebration'].append(transformCelebration(calendarDay['Celebration']))


    #find LiturgicalReadings by readingsBreviarId/LiturgicalReadingsId
    for celebration in lelkiBatyu['celebration']:
        findReadings(celebration)

    # now write output to a file
    with open("batyuk/" + calendarDay['DateISO'] + ".json", "w") as breviarDataFile:
        # magic happens here to make it pretty-printed
        breviarDataFile.write(
            simplejson.dumps(lelkiBatyu, indent=4, sort_keys=True)
        )


print("Hello World")
