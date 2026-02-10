"""Az input XML és JSON adatokból generálja a batyu JSON fájlokat a batyuk/ mappában."""

import argparse
from datetime import datetime, timedelta
import json
import os
import re
import sys
import time

import requests
import xmltodict
import Levenshtein

def writeDataFormattedJSONfile(data, filename, sort_keys=False, ensure_ascii=True):
    with open(filename, "w", encoding='utf8') as dataFile:
        print(f"Write {filename}...", end='')
        sys.stdout.flush()
        # magic happens here to make it pretty-printed
        dataFile.write(
            json.dumps(data, indent=4, sort_keys=sort_keys, ensure_ascii=ensure_ascii)
        )
    print(" OK")

def downloadBreviarData(year):
    """
    Letölti az adatokat adott évre a breviar.kbs.sk helyről.

    Kimenet: breviarData_yyyy.json
    """

    print("Downloading data from breviar.kbs.sk", end='')
    sys.stdout.flush()
    # get breviarData from url
    url = f"https://breviar.kbs.sk/cgi-bin/l.cgi?qt=pxml&d=*&m=*&r={year}&j=hu"
    response = requests.get(url)
    breviarData = xmltodict.parse(response.content)

    # now write output to a file
    writeDataFormattedJSONfile(breviarData, f"breviarData_{year}.json", sort_keys=True)

def loadBreviarData(year):
    """
    Betölti az adott évi adatokat a breviarData_yyyy.json fájlból és Python dict objektumként adja vissza.
    """
    print(f"Loading breviarData_{year}.json...", end='')
    sys.stdout.flush()
    with open(f"breviarData_{year}.json", encoding='utf8') as f:
        data = json.load(f)
        print(" OK")
        return data

def loadKatolikusData():
    """
    Betölti az adatokat a readings/.*json fájlokból és Python dict  objektumként adja.
    """

    print("Loading katolikusData from jsons: ", end='')
    sys.stdout.flush()
    katolikusData = {}
    sources = [ "vasA", "vasB", "vasC", "olvasmanyok", "szentek", "custom"]
    for name in sources:
        print("." + name + ".", end='')
        sys.stdout.flush()
        data = {}
        with open(f'readings/{name}.json', 'r', encoding="utf8") as file:
            data = json.load(file)

        if name in ["vasA", "vasB", "vasC"]:
            _tmp = {}
            evKod = name[3:4] # A, B vagy C
            for key, value in data.items():
                evKodKey = evKod + key
                _tmp[evKodKey] = value
                _tmp[evKodKey]['igenaptarId'] = evKodKey
            data = _tmp

        for key, dataValue in data.items():
            if key in katolikusData:
                if isinstance(katolikusData[key],dict) and isinstance(dataValue,dict):
                    katolikusData[key] = [ katolikusData[key] , dataValue ]
                elif isinstance(katolikusData[key],dict) and isinstance(dataValue,list):
                    katolikusData[key] = dataValue.append(katolikusData[key])
                elif isinstance(katolikusData[key],list) and isinstance(dataValue,dict):
                    katolikusData[key] = katolikusData[key].append(dataValue)
                elif isinstance(katolikusData[key],list) and isinstance(dataValue,list):
                    katolikusData[key] = katolikusData[key] | dataValue
            else:
                katolikusData[key] = data[key]


    # commentaries
    name = 'commentaries'
    with open(f'readings/{name}.json', 'r', encoding="utf8") as file:
        data = json.load(file)
    katolikusData['commentaries'] = data

    print(" OK")
    return katolikusData

def transformCelebration(celebration: dict, day: dict):

    transformedCelebration = {
        'dateISO' : day['DateISO'],
        'yearLetter': celebration['LiturgicalYearLetter'],
        'yearParity': yearIorII(celebration['LiturgicalYearLetter'], day['DateYear']),
        'week': celebration['LiturgicalWeek'],
        'dayofWeek': int(day["DayOfWeek"]['@Id']),
        'weekOfPsalter': celebration['LiturgicalWeekOfPsalter'],
        'season': celebration['LiturgicalSeason']['@Id'],
        'seasonText': celebration['LiturgicalSeason']['#text'],
        'typeLocal': celebration['LiturgicalCelebrationTypeLocal'],
        'level': celebration['LiturgicalCelebrationLevel'],
        'required': celebration['LiturgicalCelebrationRequired'],
        'name': celebration['LiturgicalCelebrationName'],
        'readingsBreviarId': celebration['LiturgicalReadingsId']
    }

    #Volume of the volumeOfBreviary
    #print(celebration['LiturgicalSeason']['@Id'])
    if celebration['LiturgicalSeason']['@Id'] in ['0','1','2','3','4']:
        transformedCelebration['volumeOfBreviary'] = "I"
    elif celebration['LiturgicalSeason']['@Id'] in ['6','7','8','9','10','11']:
        transformedCelebration['volumeOfBreviary'] = "II"
    elif int(celebration['LiturgicalWeek']) > 17:
        transformedCelebration['volumeOfBreviary'] = "IV"
    else:
        transformedCelebration['volumeOfBreviary'] = "III"

    # LiturgicalCelebrationName can contain HTML
    if celebration['LiturgicalCelebrationName'] and "#text" in celebration['LiturgicalCelebrationName']:
        transformedCelebration['name'] = celebration['LiturgicalCelebrationName']['#text']

    # Create name if it is necessary
    if transformedCelebration['name'] is None:
        napok = { 0: "vasárnap", 1: "hétfő", 2: "kedd", 3: "szerda", 4: "csütörtök", 5: "péntek", 6: "szombat"}
        transformedCelebration['name'] = celebration['LiturgicalSeason']['#text'] + " " + celebration['LiturgicalWeek'] + ". hét, " + napok[int(day["DayOfWeek"]['@Id'])]
        if int(day["DayOfWeek"]['@Id']) == 0:
            if celebration['LiturgicalSeason']['#text'] == "évközi idő":
                transformedCelebration['name'] = "évközi " + celebration['LiturgicalWeek'] + ". vasárnap"
            else:
                transformedCelebration['name'] = celebration['LiturgicalSeason']['#text'][:-5] + " " + celebration['LiturgicalWeek'] + ". vasárnapja"

    #print(transformedCelebration['name'])

    if celebration['LiturgicalCelebrationType']['#text'] == "féria":
        celebration['LiturgicalCelebrationType']['#text'] = "köznap"

    if transformedCelebration['name']:
        transformedCelebration['title'] = transformedCelebration['name'] # + " - " + celebration['LiturgicalCelebrationType']['#text']
    else:
        transformedCelebration['title'] = celebration['LiturgicalCelebrationType']['#text']

    transformedCelebration['celebrationType'] = celebration['LiturgicalCelebrationType']['#text']

    # LiturgicalCelebrationColor can be without text if it's in special season
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


def findCommentaries(celebration: dict, katolikusData: dict):

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

                break


def createReadingIds(celebration: dict, day: dict):

    seasons = { '0' :"ADV", '1' : "ADV", '2': "KAR", '3': "KAR", '4': "KAR", '5' : "EVK", "6": "NAB", "10" : "HUS", "11" : "HUS" }


#<LiturgicalSeason Id="7" Value="nagyböjti idő II (Nagyhét)">nagyhét</LiturgicalSeason>
#<LiturgicalSeason Id="8" Value="szent három nap">szent három nap</LiturgicalSeason>
#<LiturgicalSeason Id="9" Value="húsvét nyolcada">húsvét nyolcada</LiturgicalSeason>
#<LiturgicalSeason Id="10" Value="húsvéti idő I (Urunk mennybemeneteléig)">húsvéti idő</LiturgicalSeason>
#<LiturgicalSeason Id="11" Value="húsvéti idő II (Urunk mennybem

    days = { 1: "Hetfo", 2: "Kedd", 3: "Szerda", 4: "Csutortok", 5: "Pentek", 6: "Szombat"}

    katolikusDataKod = "False"

    if celebration['readingsBreviarId'] is None:
        celebration['readingsBreviarId'] = day['DateDay'] + '.' + day['DateMonth'] + '.'

    # Évközi (C), húsvéti (V), nagyböjti (P), adventi (A), idő vasárnapjai ill. köznapjai
    result = re.search(r"^(\d{1,2})([ACVPK]{1})(\d{0,1})$", celebration['readingsBreviarId'])
    if result:
        # mi a 'kod' azaz az adott nap rövidítése
        kodok = { "A" : "ADV", "C" : "EVK", "P": "NAB", "V" : "HUS", "K" : "KAR" }
        katolikusDataKod = kodok[result.group(2)] + str(result.group(1)).zfill(2)
        if not result.group(3) == "":
            katolikusDataKod += result.group(3) + days[ int(result.group(3))]

    #
    # Egyes dátumokhoz tartozó ünnepek olvasmányainak kikeresése, figyelve arra, hogy egy napra több minden is juthat. Uuuupsz.
    # Dec 25 extra :D
    #
    result = re.search(r"^(\d{1,2})\.(\d{1,2})\.$", celebration['readingsBreviarId'])
    if result:
        katolikusDataKod = result.group(2).zfill(2) + "-" + result.group(1).zfill(2)


    #Szentcsalád vasárnapja
    if celebration['readingsBreviarId'] == 'SvR':
        katolikusDataKod = "KAR01"

    #  Egy két egyedink mert az jól
    if celebration['name'] == "Szűz Mária az Egyház Anyja":
        katolikusDataKod = "PUNK01"
    if celebration['name'] == "Votív mise a Szentlélekről":
        katolikusDataKod = "PUNKOSDHetfo"
    if celebration['name'] == "A mi Urunk, Jézus Krisztus, az Örök Főpap":
        katolikusDataKod = "OrokFopap"
    if celebration['name'] == "Krisztus Szent Teste és Vére":
        katolikusDataKod = "HUS10"
    if celebration['name'] == "Jézus Szent Szíve":
        katolikusDataKod = "HUS105Pentek"
    if celebration['name'] == "A Boldogságos Szűz Mária Szeplőtelen Szíve":
        katolikusDataKod = "HUS106Szombat"
    if celebration['name'] == "A Boldogságos Szűz Mária Szeplőtelen Szíve":
        katolikusDataKod = "HUS106Szombat"
    if celebration['name'] == "Pannonhalma: a bazilika felszentelése":
        katolikusDataKod = "SzekesegyhazFelszentelése"
    if celebration['name'] == "A Boldogságos Szűz Mária szeplőtelen fogantatása":
        katolikusDataKod = "12-08"


    celebration['readingsId'] = katolikusDataKod
    print("  ReadingsId: " +  katolikusDataKod, end="\r", flush=True)

    #
    # Köznapi olvasmányok is kellenek, ha nem nagy ünnepről van szó
    #
    if int(celebration['level']) >= 10:
        #általában
        ferialReadingsId = seasons[celebration['season']] + str(celebration['week']).zfill(2) + str(celebration['dayofWeek']) + days[celebration['dayofWeek']]
        # Karácsony után másképp jön létre a kód!
        if ( int(day['DateMonth']) == 1 and int(day['DateDay']) <= 12 ) or int(day['DateMonth']) == 12 and int(day['DateDay']) >= 25 :
            ferialReadingsId = day['DateMonth'].zfill(2) + "-" + day['DateDay'].zfill(2)

        #Ha ő már eleve köznap, akkor minek legyenek duplán köznapi olvasmányok
        if ferialReadingsId != katolikusDataKod:
            celebration['ferialReadingsId'] = ferialReadingsId
        #De karácsony nyolcadában ünnepek és köznapok találkoznak
        if int(celebration['season']) == 2 or int(celebration['season']) == 3:
            celebration['ferialReadingsId'] = ferialReadingsId
        #De Szűz Mária szombati emléknapján is van munka
        if celebration['name'].startswith("Szűz Mária szombati emléknapja"):
            celebration['ferialReadingsId'] = ferialReadingsId



    if katolikusDataKod != 'False':
        return True
    else:
        error(celebration['readingsBreviarId'])
        return False

def error(text):
    print("  ERROR: " + text.ljust(80))
    # exit()

def findReadings(celebration: dict, katolikusData: dict, lelkiBatyu: dict):

    readingHasFound = False

    if celebration['readingsId'] not in katolikusData:

        if celebration['yearLetter'] + celebration['readingsId'] not in katolikusData:

            if re.search("székesegyház felszentelése", celebration['name']) or re.search("bazilika felszentelése", celebration['name']):
                celebration['readingsId'] = "SzekesegyhazFelszentelése"

            else:
                error("Ez az olvasmánykód (" + celebration['readingsId'] + ") hiányzik a kulcsok között. Pedig csak van ilyen ünnep/emléknap '" + celebration['name'] + "' nem?")
                return
        else:
            celebration['readingsId'] = celebration['yearLetter'] + celebration['readingsId']

    if isinstance(katolikusData[celebration['readingsId']], dict):
        possibilities = [ katolikusData[celebration['readingsId']] ]
    else:
        possibilities = katolikusData[celebration['readingsId']]

    #Add Szűz Mária szombatja as a possibility
    if celebration['dayofWeek'] == 6 and int(celebration['level']) > 9:
        possibilities.append(katolikusData['SzuzMariaSzombatja'])

    #Székesegyházak felszentelése
    if re.search("székesegyház felszentelése", celebration['name']):
        possibilities.append(katolikusData['SzekesegyhazFelszentelése'])

    ratio = 0.65
    tryout = False
    tmp1 = ""
    tmp = ""

    if possibilities is None:
        possibilities = []

    for possibility in possibilities:

        currentRatio = Levenshtein.ratio(str(celebration['name']), possibility['name'])

        if currentRatio > ratio:
            ratio = currentRatio
            tryout = possibility


        tmp = ""
        for row in possibilities:
            if celebration['name']:
                tmp1 = celebration['name']
            else:
                tmp1 = "névtelen"
            tmp += row['name'] + " ("+ str( round(Levenshtein.ratio(str(celebration['name']), row['name']),2)) +") , "

    if tryout:
        readingHasFound = tryout


    if not readingHasFound:
        for possibility in possibilities:

            pairs = [
                ["^A Szent Család", "^Szent Család"],
                [ "^adventi idő", "^Adventi köznapok - december", ],
                [ r"^adventi idő ([0-9]{1})\. hét, vasárnap$", r"^Advent ([0-9]{1})\. vasárnapja" ],
                [ r"^nagyböjti idő ([0-9]{1})\. hét, vasárnap$", r"^Nagyböjt ([0-9]{1})\. vasárnapja" ],
                [ "Rózsafüzér Királynője", "Rózsafüzér Királynője" ],
                [ "Kármelhegyi Boldogasszony", "Kármelhegyi Boldogasszony" ],
                [ "Krisztus Király", "Évközi 34. vasárnap – Krisztus, a Mindenség Királya"],
                [ "karácsony nyolcada 1. hét","Karácsonyi idő - december"],
                [ "karácsonyi idő 1. hét", "Karácsonyi idő - január"],
                [ r"^(évközi idő ([0-9]{1,2})\. hét, vasárnap)", r"^(Évközi ([0-9]{1,2})\. vasárnap)"],
                ["Vasárnap Húsvét nyolcadában", "Húsvét 2. vasárnapja"],
                ["Virágvasárnap", "Virágvasárnap"],
                ["\nKrisztus feltámadása$", "Húsvétvasárnap"],
                [r"nagyböjti idő 0\. hét", "hamvazószerda után"],
                ["a bazilika felszentelése", "Székesegyház felszentelése"],
                ["főszékesegyház felszentelése", "Székesegyház felszentelése"]
            ]

            for first, second in pairs:
                if re.search(first, celebration['name']) and re.search(second, possibility['name']):
                    readingHasFound = possibility
                    break



    if not readingHasFound:
        error("Nincs eléggé jól passzoló olvasmány. Amit keresünk (breviar): '" + tmp1 + "'. Amik vannak (igenaptar): " + tmp)

        return False
    #  szóval megvan az aranybogárka
    else:
        possibility = readingHasFound
        #print(readingHasFound['name'])

        if 'name' in possibility and possibility['name'] != "":
            #print(possibility['name'] + " <-- " + celebration['name'])
            #celebration['name'] = possibility['name']
            if lelkiBatyu['date']['dayofWeek'] != '0' or  celebration['celebrationType'] != 'köznap':
                celebration['title'] = celebration['name'] + " (" + celebration['celebrationType'] + ")"
            else:
                celebration['title'] = celebration['name']

        celebration['parts'] = possibility['parts']
        hasMultipleParts = False
        for part in celebration['parts']:
            if 'parts' in part:
                hasMultipleParts = True
                break
        if hasMultipleParts:
            celebration['parts'] = possibility['parts'][0]['parts']
            celebration['parts2'] = possibility['parts'][1]['parts']
            if 'cause' in possibility['parts'][1]:
                celebration['parts2cause'] = possibility['parts'][1]['cause']


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

        return True



# Kötelező emléknapokon (level 10 és 11) köznapi olvasmányok a default érték!
def addreadingstolevel10(celebration: dict, katolikusData: dict):
    if celebration['level'] == '10' or celebration['level'] == '11'  or celebration['level'] == '12':

        ferialReadings = False

        if not 'ferialReadingsId' in celebration:
            error("Köznapi olvasmányoknak is kéne lenniük, de nem találjuk az azonosítójukat.")
            return False

        if not celebration['ferialReadingsId'] in katolikusData:
            error("A köznapi olvasmányok (" + celebration['ferialReadingsId'] + ") nem találhatók meg az adatbázisunkban.")
            return False


        if not isinstance(katolikusData[celebration['ferialReadingsId']], dict):
            for item in katolikusData[celebration['ferialReadingsId']]:
                if re.search("^Karácsonyi idő - január", item['name']):
                    ferialReadings = item

            if ferialReadings is False:
                error("Több köznapi olvasmányos csookor van itt, vagy csak nehéz megtalálni?")
                return False
        else:
            ferialReadings = katolikusData[celebration['ferialReadingsId']]

        # Fixme! Attól még hogy egyet talált lehet az hibás. Mi mégsem ellenőrizzük.

        # Tehát a fakultatív saját olvasmányok mennek a parts2-ben. Persze ha vannak...
        if 'parts' in celebration:
            celebration['parts2'] = celebration['parts']
        else:
            celebration['parts2'] = [{
                "teaser" : "Saját olvasmányokat nem találtunk. Elnézést.",
                "text" : "Saját olvasmányokat nem találtunk. Elnézést."
            }]
            error("Kéne legyen saját olvasmánya is, de csak a közös olvasmányoakt találtunk meg.")

        celebration['parts2cause'] = "(Vagy) saját olvasmányok"
        celebration['parts'] = ferialReadings["parts"]

        return



# Köznapokon az I és II éve szerint szétszedni az olvasmányokat!
def clearYearIorII(celebration: dict):
    if 'parts' in celebration:
        for kid, k in enumerate(celebration['parts']):

            if not isinstance(k, dict):
                for possibility in k:
                    if "cause" in possibility and ( (  possibility["cause"] == 'II. évben' and celebration['yearParity'] == 'I' ) or  ( possibility["cause"] == 'I. évben' and celebration['yearParity'] == 'II' ) ) :
                        k.remove(possibility)
                        if len(k) == 1:
                            celebration['parts'][kid] = k[0]
                            celebration['parts'][kid].pop("cause")


def yearIorII(ABC, year):
    if year == '2026':
        if ABC == 'A':
            return "II"
        else:
            return "I"
    elif year == '2024':
        if ABC == 'B':
            return "II"
        else:
            return "I"
    if year == '2025':
        if ABC == 'C':
            return "I"
        else:
            return "II"

    #print(ABC)
    #print(year)
    print("Hát ezt bizony meg kéne csinálni még...")
    sys.exit()

# Van pár alkalom amikor egy az ünnep de több az ünneplés: karácsony, pünkösd, húsvét, nagycsütörtök
def addCustomCelebrationstoBreviarData(data):

    toAdd = False
    for celebration in data['celebration']:
        if celebration['name'] == "Nagycsütörtök":
            toAdd = [ {"name": "Nagycsütörtök - Krizmaszentelési mise",  "colorId": "2",
                "colorText": "fehér" }, {"name" : "Nagycsütörtök, az utolsó vacsora emléknapja" } ]
        if isinstance(celebration['name'], str) and re.search("^Húsvétvasárnap", celebration['name']):
            toAdd = [ {"name": 'Húsvétvasárnap, Urunk feltámadásának ünnepe - Húsvéti vigília' }, {"name" : "Húsvétvasárnap, Urunk feltámadásának ünnepe" } ]
        if celebration['name'] == "Urunk születése (Karácsony)":
            toAdd = [ {"name": " Urunk születése: Karácsony – Vigília mise" }, {"name" : "Karácsony – Éjféli mise" }, {"name" : "Urunk születése: Karácsony – Pásztorok miséje" }, {"name" : "Urunk születése: Karácsony – Ünnepi mise" } ]


        if celebration['name'] == "Pünkösd":
            toAdd = [ {"name": "Pünkösd, vigília mise" }, {"name" : "Pünkösdvasárnap" } ]
        if celebration['name'] == "Szűz Mária az Egyház Anyja": # Pünkösdhétfő
            toAdd = [ {"name": "Szűz Mária az Egyház Anyja"}, {"name": "Votív mise a Szentlélekről", "title": "Votív mise a Szentlélekről" } ]

        if celebration['name'] == "Keresztelő Szent János születése": # 06-24
            toAdd = [ {"name": "Vigília - Keresztelő Szent János születése" }, {"name" : "Keresztelő Szent János születése"}]
        if celebration['name'] == "Szűz Mária mennybevétele (Nagyboldogasszony)": # 08-15
            toAdd = [ {"name": "Vigília - Szűz Mária mennybevétele (Nagyboldogasszony)" }, {"name" : "Szűz Mária mennybevétele (Nagyboldogasszony)" } ]

    if not toAdd is False:

        data['celebration2'] = []
        for i in (range(len(toAdd))):
            data['celebration2'].append(data['celebration'][0].copy())

        for i in (range(len(toAdd))):
            for ize in toAdd[i]:
                data['celebration2'][i][ize] = toAdd[i][ize]

        data['celebration'] = data['celebration2'].copy()
        del data['celebration2']


# Bűnbánati napok
def dayOfPenance(celebration):
    dayOfPenance = 0

    # minden péntek
    dateObj = datetime.strptime(celebration['dateISO'], '%Y-%m-%d')
    if dateObj.weekday() == 4:
        # kivételek a kötelező ünnepek ÉS az alábbiak:
        exceptions = ["02-02", "03-25", "05-01", "08-20", "09-08", "12-24", "12-31", "10-23"]
        monthDay = dateObj.strftime('%m-%d')
        if monthDay in exceptions or int(celebration['level']) < 10:
            dayOfPenance = 0
        else:
            dayOfPenance = 1

        # nagyböjt péntekjei
        if celebration['season'] == "6":
            dayOfPenance = 2

    #print(celebration)
    #nagypéntek és hamvazószerda
    if celebration['readingsId'] == "NAB065Pentek" or celebration['readingsId'] == "NAB003Szerda":
        dayOfPenance = 3

    return dayOfPenance




def isFileOldOrMissing(filePath):
    if not os.path.exists(filePath):
        return True
    fileModTime = os.path.getmtime(filePath)
    currentTime = time.time()
    # Check if file is older than 1 hour (3600 seconds)
    if (currentTime - fileModTime) > 3600:
        return True
    return False




def generateLelkiBatyuk(year):
    if isFileOldOrMissing(f"breviarData_{year}.json"):
        downloadBreviarData(year)

    breviarData = loadBreviarData(year)

    katolikusData = loadKatolikusData()

    lelkiBatyuk = {}
    # Index structures
    index_dayOfWeek = {}
    index_readingsId = {}
    index_name = {}
    for calendarDay in breviarData['LHData']['CalendarDay']:
        print(calendarDay['DateISO'] + ": ")

        lelkiBatyu = {}
        lelkiBatyu['date'] = {
            'ISO': calendarDay['DateISO'],
            'dayOfYear' : calendarDay['DayOfYear'],
            'dayofWeek' : calendarDay['DayOfWeek']['@Id'],
            'dayofWeekText' : calendarDay['DayOfWeek']['#text']
        }

        #for celebration in calendarDay
        lelkiBatyu['celebration'] = []
        celebrations = calendarDay['Celebration'] if isinstance(calendarDay['Celebration'], list) else [calendarDay['Celebration']]
        for celebration in celebrations:
            transformed = transformCelebration(celebration, calendarDay)
            lelkiBatyu['celebration'].append(transformed)
        addCustomCelebrationstoBreviarData(lelkiBatyu)

        #find LiturgicalReadings by readingsBreviarId/LiturgicalReadingsId
        for key in range(len(lelkiBatyu['celebration'])):
            celebration = lelkiBatyu['celebration'][key]
            celebration['celebrationKey'] = key
            print("", end='\r', flush=True)
            sys.stdout.flush()

            createReadingIds(celebration, calendarDay)

            findReadings(celebration, katolikusData, lelkiBatyu)

            addreadingstolevel10(celebration, katolikusData)
            clearYearIorII(celebration)

            # find LiturgicalReadings by readingsBreviarId/LiturgicalReadingsId
            findCommentaries(celebration, katolikusData)

            # egyéb dolgok
            celebration['dayOfPenance'] = dayOfPenance(celebration)

            print("  OK                                  ", end="\r",flush=True)

        #if calendarDay['DateISO'] == "2024-05-19":
        #    exit()

        # now write output to a file
        writeDataFormattedJSONfile(lelkiBatyu, f"batyuk/{calendarDay['DateISO']}.json", ensure_ascii=False)

        lelkiBatyuk[calendarDay['DateISO']] = lelkiBatyu
        index_celebration_data(index_dayOfWeek, index_readingsId, index_name, calendarDay, lelkiBatyu)       

    writeDataFormattedJSONfile(lelkiBatyuk, f"batyuk/{year}_simple.json", ensure_ascii=False)

    # Write index file
    index = {
        "seasonWeekDayofWeek": index_dayOfWeek,
        "readingsId": index_readingsId,
        "name": index_name
    }
    writeDataFormattedJSONfile(index, f"batyuk/{year}_index.json", ensure_ascii=False)

    lelkiBatyukComplex = lelkiBatyuk

    for dayValue in lelkiBatyukComplex.values():
        for cid, celebration in enumerate(dayValue['celebration']):
            for partsKey in ['parts', 'parts2']:
                if partsKey in dayValue['celebration'][cid]:
                    for pid, part in enumerate(dayValue['celebration'][cid][partsKey]):
                        # lista
                        if isinstance(part, dict):
                            dayValue['celebration'][cid][partsKey][pid]['type'] = 'object'
                        else:
                            tmp = {}
                            tmp['type'] = 'array'
                            tmp['content'] = part

                            for content in tmp['content']:
                                content['type'] = 'object'

                            dayValue['celebration'][cid][partsKey][pid] = tmp

    writeDataFormattedJSONfile(lelkiBatyukComplex, f"batyuk/{year}.json", ensure_ascii=False)

    return lelkiBatyukComplex

def index_celebration_data(index_dayOfWeek, index_readingsId, index_name, calendarDay, lelkiBatyu):
    celebrations = lelkiBatyu['celebration'] if isinstance(lelkiBatyu['celebration'], list) else [lelkiBatyu['celebration']]
    for celebration in celebrations:
        season = celebration.get("season")
        week = celebration.get('week')
        dayofweek = celebration.get('dayofWeek')
        if week is not None and dayofweek is not None:
            key = f"{season}-{week}-{dayofweek}"
            if key not in index_dayOfWeek:
                index_dayOfWeek[key] = []
            if calendarDay['DateISO'] not in index_dayOfWeek[key]:
                index_dayOfWeek[key].append(calendarDay['DateISO'])
        if 'readingsId' in celebration and celebration['readingsId']:
            rid = celebration['readingsId']
            if rid not in index_readingsId:
                index_readingsId[rid] = []
            if calendarDay['DateISO'] not in index_readingsId[rid]:
                index_readingsId[rid].append(calendarDay['DateISO'])
        if 'name' in celebration and celebration['name']:
            n = celebration['name']
            if n not in index_name:
                index_name[n] = []
            if calendarDay['DateISO'] not in index_name[n]:
                index_name[n].append(calendarDay['DateISO'])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Napi lelki batyuk generalasa')
    parser.add_argument(
        '--year', default=datetime.now().year, type=int, help='the year to generate')
    parser.add_argument('--no-next-year', action='store_false', help='do not generate next year', default=True, dest='next_year')

    args = parser.parse_args()

    allLelkiBatyuk = generateLelkiBatyuk(args.year)

    if args.next_year:
        allLelkiBatyuk = allLelkiBatyuk | generateLelkiBatyuk(args.year + 1)

    today = datetime.now()
    start_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')
    end_date = (today + timedelta(days=365)).strftime('%Y-%m-%d')
    filtered_allLelkiBatyuk = {k: v for k, v in allLelkiBatyuk.items() if start_date <= k <= end_date}

    writeDataFormattedJSONfile(filtered_allLelkiBatyuk, "batyuk/igenaptar.json", ensure_ascii=False)

    print("Done!")
