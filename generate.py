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
    sources = ["olvasmanyok", "vasA", "vasB", "vasC","szentek","commentaries"]
    for name in sources:
        with open('readings/' + name + '.json', 'r',encoding="utf8") as file:
            katolikusData[name] = simplejson.load(file)
    return katolikusData

def transformCelebration(celebration: dict):
    print(celebration['LiturgicalCelebrationName'])
    transformedCelebration = {
        'yearLetter': celebration['LiturgicalYearLetter'],
        'yearParity': yearIorII(celebration['LiturgicalYearLetter'], calendarDay['DateYear']),
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

    if transformedCelebration['name']:
        transformedCelebration['title'] = transformedCelebration['name'] + " - " + celebration['LiturgicalCelebrationType']['#text']
    else:
        transformedCelebration['title'] = celebration['LiturgicalCelebrationType']['#text']


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


def findCommentaries(celebration: dict):

    commentaryHasFound = False

    for commentary in katolikusData['commentaries']:
        if 'readingsBreviarId' in katolikusData['commentaries'][commentary]:
            if katolikusData['commentaries'][commentary]['readingsBreviarId'] == celebration['readingsBreviarId']:
                if 'teaser' in katolikusData['commentaries'][commentary]:
                    celebration['teaser'] = katolikusData['commentaries'][commentary]['teaser']['text']
                if 'commentary' in katolikusData['commentaries'][commentary]:
                    celebration['commentary'] = {
                        "type" : "object",
                        "short_title" : "Gondolatok a mai napról",
                        "text" : katolikusData['commentaries'][commentary]['commentary']['text']
                    }
                commentaryHasFound = True
                return True


def findReadings(celebration: dict):

    readingHasFound = False

    if celebration['readingsBreviarId'] is None:
        print(str(calendarDay['DateISO']) + " ERROR: readingsBreviarId == None")
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
        if katolikusDataTable in katolikusData:
            if katolikusDataKod in katolikusData[katolikusDataTable]:
                if 'parts' in katolikusData[katolikusDataTable][katolikusDataKod]:
                    celebration['parts'] = katolikusData[katolikusDataTable][katolikusDataKod]['parts']
                    readingHasFound = True
                else:
                    print( str(calendarDay['DateISO']) + " ERROR: Nincs 'parts' in katolikusData['" + katolikusDataTable + "']['" + katolikusDataKod + "']")
                    return False
            else:
                print( str(calendarDay['DateISO']) + " ERROR: Nincs '" + katolikusDataKod + "' in katolikusData['" + katolikusDataTable + "']")
                return False
        else:
            print( str(calendarDay['DateISO']) + " ERROR: Nincs '" + katolikusDataTable + "' in katolikusData")
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
            print(str(calendarDay['DateISO']) + " ERROR: Nincs 'szentek' in katolikusData")
            return False

        if not datum in katolikusData['szentek']:
            print( str(calendarDay['DateISO']) + " ERROR: Nincs '" + datum + "' in katolikusData['szentek']")
            return False

        if  type(katolikusData['szentek'][datum]) == dict:
            possibilities = [katolikusData['szentek'][datum]]
        else:
            possibilities = katolikusData['szentek'][datum]


        for possibility in possibilities:
            #print(str(Levenshtein.ratio(str(celebration['name']), possibility['name'])) + " " + celebration['name'] + " ? " + possibility['name'])
            if Levenshtein.ratio(str(celebration['name']), possibility['name']) > 0.5:
                celebration['parts'] = possibility['parts']

                if 'excerpt' in possibility:
                    celebration['teaser'] = possibility['excerpt']
                if 'content' in possibility:
                    celebration['commentary'] = {
                        "type": "object",
                        "short_title" : "Élete",
                        "text": possibility['content']
                    }
                if 'image' in possibility:
                    celebration['image'] = possibility['image']

                readingHasFound = True
                return True

        tmp = ""
        for row in possibilities:
            if celebration['name']:
                tmp1 = celebration['name']
            else:
                tmp1 = "névtelen"
            tmp += row['name'] + ", "
        print(str(calendarDay['DateISO']) + " ERROR: Nincs eléggé jól passzoló olvasmány. Amit keresünk: '" + tmp1 + "'. Amik vannak: " + tmp)

        return False

    if not readingHasFound:
        print(str(calendarDay['DateISO']) + " ERROR: Nincs '" + celebration['readingsBreviarId'] + "'")
        return False

# Köznapokon az I és II éve szerint szétszedni az olvasmányokat!
def clearYearIorII(celebration: dict):
    if 'parts' in celebration:
        for kid, k in enumerate(celebration['parts']):
            
            if type(k) != dict:
                for possibility in k:
                    if "cause" in possibility and ( (  possibility["cause"] == 'II. évben' and celebration['yearParity'] == 'I' ) or  ( possibility["cause"] == 'I. évben' and celebration['yearParity'] == 'II' ) ) :                        
                        k.remove(possibility)
                        print(len(k))
                        print(k)
                        if len(k) == 1:
                            celebration['parts'][kid] = k[0]
                            celebration['parts'][kid].pop("cause")
                                                    

def yearIorII(ABC, year):
    if year == '2023':
        if ABC == 'A':
            return "II"
        else:
            return "I"
    elif year == '2024':
        if ABC == 'B':
            return "I"
        else:
            return "II"
    if year == '2025':
        if ABC == 'C':
            return "II"
        else:
            return "I"

    #print(ABC)
    #print(year)
    print("Hát ezt bizony meg kéne csinálni még...")
    exit()


downloadBreviarData()
breviarData = loadBreviarData()
katolikusData = loadKatolikusData()

lelkiBatyuk = {}
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

        clearYearIorII(celebration)

    #find LiturgicalReadings by readingsBreviarId/LiturgicalReadingsId
    for celebration in lelkiBatyu['celebration']:
        findCommentaries(celebration)

    # now write output to a file
    with open("batyuk/" + calendarDay['DateISO'] + ".json", "w", encoding='utf8') as breviarDataFile:
        # magic happens here to make it pretty-printed
        breviarDataFile.write(
            simplejson.dumps(lelkiBatyu, indent=4, sort_keys=False, ensure_ascii=False)
        )
    lelkiBatyuk[calendarDay['DateISO']] = lelkiBatyu

with open("batyuk/2024_simple.json", "w", encoding='utf8') as breviarDataFile:
        # magic happens here to make it pretty-printed
        breviarDataFile.write(
            simplejson.dumps(lelkiBatyuk, indent=4, sort_keys=False, ensure_ascii=False)
        )


lelkiBatyukComplex = lelkiBatyuk
# print(lelkiBatyuk['2024-03-31'])

for day in lelkiBatyukComplex:
    for cid, celebration in enumerate(lelkiBatyukComplex[day]['celebration']):
        if 'parts' in lelkiBatyukComplex[day]['celebration'][cid]:
            for pid, part in enumerate(lelkiBatyukComplex[day]['celebration'][cid]['parts']):
                # lista
                if type(part) == dict:
                    lelkiBatyukComplex[day]['celebration'][cid]['parts'][pid]['type'] = 'object'
                else:
                    tmp = {}
                    tmp['type'] = 'array'
                    tmp['content'] = part

                    for contentid, cont in enumerate(tmp['content']):
                        tmp['content'][contentid]['type'] = 'object'

                    lelkiBatyukComplex[day]['celebration'][cid]['parts'][pid] = tmp


with open("batyuk/2024.json", "w", encoding='utf8') as breviarDataFile:
        # magic happens here to make it pretty-printed
        breviarDataFile.write(
            simplejson.dumps(lelkiBatyukComplex, indent=4, sort_keys=False, ensure_ascii=False)
        )

print("Hello World")
