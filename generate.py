import requests
import xmltodict
import simplejson
import csv
import re
import Levenshtein
import sys
import os
import time
from datetime import datetime


def downloadBreviarData():

    print("Downloading data from breviar.kbs.sk", end='')
    sys.stdout.flush()
    # get breviarData from url
    current_year = datetime.now().year
    url = f"https://breviar.kbs.sk/cgi-bin/l.cgi?qt=pxml&d=*&m=*&r={current_year}&j=hu"
    response = requests.get(url)
    breviarData = xmltodict.parse(response.content)
    next_year = current_year + 1
    url_next_year = f"https://breviar.kbs.sk/cgi-bin/l.cgi?qt=pxml&d=*&m=*&r={next_year}&j=hu"
    response_next_year = requests.get(url_next_year)
    breviarData_next_year = xmltodict.parse(response_next_year.content)

    # Merge the two datasets
    breviarData['LHData']['CalendarDay'].extend(breviarData_next_year['LHData']['CalendarDay'])

    # now write output to a file
    with open("breviarData.json", "w") as breviarDataFile:
        print("...", end='')
        sys.stdout.flush()
        # magic happens here to make it pretty-printed
        breviarDataFile.write(
            simplejson.dumps(breviarData, indent=4, sort_keys=True)
        )
    print(" OK")

def loadBreviarData():
    print("Loading breviarData.json...", end='')
    sys.stdout.flush()
    f = open("breviarData.json")
    data = simplejson.load(f)
    print(" OK")
    return data

def loadKatolikusData():
    print("Loading katolikusData from jsons: ", end='')
    sys.stdout.flush()
    katolikusData = {}
    sources = [ "vasA", "vasB", "vasC","olvasmanyok", "szentek","custom"]
    for name in sources:
        print("." + name + ".", end='')
        sys.stdout.flush()
        data = {}
        with open('readings/' + name + '.json', 'r',encoding="utf8") as file:
            data = simplejson.load(file)


        if name == "vasA" or name == "vasB" or name == "vasC":
            tmp = {}
            for keyId, key in enumerate(data):
                if name == "vasA":
                    data[key]['igenaptarId'] = "A" + key
                    tmp["A" + key] = data[key]
                if name == "vasB":
                    data[key]['igenaptarId'] = "B" + key
                    tmp["B" + key] = data[key]
                if name == "vasC":
                    data[key]['igenaptarId'] = "C" + key
                    tmp["C" + key] = data[key]
            data = tmp

        for key in data:
            if key in katolikusData:
                if isinstance(katolikusData[key],dict) and isinstance(data[key],dict):
                    katolikusData[key] = [ katolikusData[key] , data[key] ]
                elif isinstance(katolikusData[key],dict) and not isinstance(data[key],dict):
                    katolikusData[key] = data[key].append(katolikusData[key])
                elif not isinstance(katolikusData[key],dict) and isinstance(data[key],dict):
                    katolikusData[key] = katolikusData[key].append(data[key])
                elif not isinstance(katolikusData[key],dict) and not isinstance(data[key],dict):
                    katolikusData[key] = katolikusData[key] | data[key]
            else:
                katolikusData[key] = data[key]


    # commentaries
    name = 'commentaries'
    with open('readings/' + name + '.json', 'r',encoding="utf8") as file:
            data = simplejson.load(file)
    katolikusData['commentaries'] = data

    print(" OK")
    return katolikusData

def transformCelebration(celebration: dict):


    transformedCelebration = {
        'dateISO' : calendarDay['DateISO'],
        'yearLetter': celebration['LiturgicalYearLetter'],
        'yearParity': yearIorII(celebration['LiturgicalYearLetter'], calendarDay['DateYear']),
        'week': celebration['LiturgicalWeek'],
        'dayofWeek': int(calendarDay["DayOfWeek"]['@Id']),
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
    print(celebration['LiturgicalSeason']['@Id'])
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
    if transformedCelebration['name'] == None:
        napok = { 0: "vasárnap", 1: "hétfő", 2: "kedd", 3: "szerda", 4: "csütörtök", 5: "péntek", 6: "szombat"}
        transformedCelebration['name'] = celebration['LiturgicalSeason']['#text'] + " " + celebration['LiturgicalWeek'] + ". hét, " + napok[int(calendarDay["DayOfWeek"]['@Id'])]
        if int(calendarDay["DayOfWeek"]['@Id']) == 0:
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


def createReadingIds(celebration: dict):

    seasons = { '0' :"ADV", '1' : "ADV", '2': "KAR", '3': "KAR", '4': "KAR", '5' : "EVK", "6": "NAB", "10" : "HUS", "11" : "HUS" }


#<LiturgicalSeason Id="7" Value="nagyböjti idő II (Nagyhét)">nagyhét</LiturgicalSeason>
#<LiturgicalSeason Id="8" Value="szent három nap">szent három nap</LiturgicalSeason>
#<LiturgicalSeason Id="9" Value="húsvét nyolcada">húsvét nyolcada</LiturgicalSeason>
#<LiturgicalSeason Id="10" Value="húsvéti idő I (Urunk mennybemeneteléig)">húsvéti idő</LiturgicalSeason>
#<LiturgicalSeason Id="11" Value="húsvéti idő II (Urunk mennybem

    days = { 1: "Hetfo", 2: "Kedd", 3: "Szerda", 4: "Csutortok", 5: "Pentek", 6: "Szombat"}

    katolikusDataKod = "False"

    if celebration['readingsBreviarId'] is None:
        celebration['readingsBreviarId'] = calendarDay['DateDay'] + '.' + calendarDay['DateMonth'] + '.'

    # Évközi (C), húsvéti (V), nagyböjti (P), adventi (A), idő vasárnapjai ill. köznapjai
    result = re.search("^(\d{1,2})([ACVPK]{1})(\d{0,1})$", celebration['readingsBreviarId'])
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
    result = re.search("^(\d{1,2})\.(\d{1,2})\.$", celebration['readingsBreviarId'])
    if result:
        katolikusDataKod = result.group(2).zfill(2) + "-" + result.group(1).zfill(2)


    #Szentcsalád vasárnapja
    if celebration['readingsBreviarId'] == 'SvR':
        katolikusDataKod = "KAR01"

    #  Egy két egyedink mert az jól
    if celebration['name'] == "Szűz Mária az Egyház Anyja":
        katolikusDataKod = "PUNK01"
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
        if ( int(calendarDay['DateMonth']) == 1 and int(calendarDay['DateDay']) <= 12 ) or int(calendarDay['DateMonth']) == 12 and int(calendarDay['DateDay']) >= 25 :
            ferialReadingsId = calendarDay['DateMonth'].zfill(2) + "-" + calendarDay['DateDay'].zfill(2)

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

def findReadings(celebration: dict):

    readingHasFound = False

    if not celebration['readingsId'] in katolikusData:

        if not ( celebration['yearLetter'] + celebration['readingsId'] ) in katolikusData:

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
                [ "^adventi idő ([0-9]{1})\. hét, vasárnap$", "^Advent ([0-9]{1})\. vasárnapja" ],
                [ "^nagyböjti idő ([0-9]{1})\. hét, vasárnap$", "^Nagyböjt ([0-9]{1})\. vasárnapja" ],
                [ "Rózsafüzér Királynője", "Rózsafüzér Királynője" ],
                [ "Kármelhegyi Boldogasszony", "Kármelhegyi Boldogasszony" ],
                [ "Krisztus Király", "Évközi 34. vasárnap – Krisztus, a Mindenség Királya"],
                [ "karácsony nyolcada 1. hét","Karácsonyi idő - december"],
                [ "karácsonyi idő 1. hét", "Karácsonyi idő - január"],
                [ "^(évközi idő ([0-9]{1,2})\. hét, vasárnap)", "^(Évközi ([0-9]{1,2})\. vasárnap)"],
                ["Vasárnap Húsvét nyolcadában", "Húsvét 2. vasárnapja"],
                ["Virágvasárnap", "Virágvasárnap"],
                ["\nKrisztus feltámadása$", "Húsvétvasárnap"],
                ["nagyböjti idő 0\. hét", "hamvazószerda után"],
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
def addreadingstolevel10(celebration: dict):
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
            celebration['parts2'] = celebration['parts'];
        else:
            celebration['parts2'] = [{
                "teaser" : "Saját olvasmányokat nem találtunk. Elnézést.",
                "text" : "Saját olvasmányokat nem találtunk. Elnézést."
            }]
            error("Kéne legyen saját olvasmánya is, de csak a közös olvasmányoakt találtunk meg.")

        celebration['parts2cause'] = "(Vagy) saját olvasmányok";
        celebration['parts'] = ferialReadings["parts"];

        return



# Köznapokon az I és II éve szerint szétszedni az olvasmányokat!
def clearYearIorII(celebration: dict):
    if 'parts' in celebration:
        for kid, k in enumerate(celebration['parts']):

            if type(k) != dict:
                for possibility in k:
                    if "cause" in possibility and ( (  possibility["cause"] == 'II. évben' and celebration['yearParity'] == 'I' ) or  ( possibility["cause"] == 'I. évben' and celebration['yearParity'] == 'II' ) ) :
                        k.remove(possibility)
                        if len(k) == 1:
                            celebration['parts'][kid] = k[0]
                            celebration['parts'][kid].pop("cause")


def yearIorII(ABC, year):
    if year == '2023':
        if ABC == 'A':
            return "I"
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
    exit()

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

        #print(celebration['name'])

        if celebration['name'] == "Pünkösd":
            toAdd = [ {"name": "Pünkösd, vigília mise" }, {"name" : "Pünkösdvasárnap" } ]

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


    return

# Bűnbánati napok
def day_of_penance(celebration):
    day_of_penance = 0

    # minden péntek
    date_obj = datetime.strptime(celebration['dateISO'], '%Y-%m-%d')
    if date_obj.weekday() == 4:
        # kivételek a kötelező ünnepek ÉS az alábbiak:
        exceptions = ["02-02", "03-25", "05-01", "08-20", "09-08", "12-24", "12-31", "10-23"]
        month_day = date_obj.strftime('%m-%d')
        if month_day in exceptions or int(celebration['level']) < 10:
            day_of_penance = 0
        else:
            day_of_penance = 1

        # nagyböjt péntekjei
        if celebration['season'] == "6":
            day_of_penance = 2

    print(celebration)
    #nagypéntek és hamvazószerda
    if celebration['readingsId'] == "NAB065Pentek" or celebration['readingsId'] == "NAB003Szerda":
        day_of_penance = 3

    return day_of_penance




def is_file_old_or_missing(file_path):
    if not os.path.exists(file_path):
        return True
    file_mod_time = os.path.getmtime(file_path)
    current_time = time.time()
    # Check if file is older than 1 hour (3600 seconds)
    if (current_time - file_mod_time) > 3600:
        return True
    return False


if is_file_old_or_missing("breviarData.json"):
    downloadBreviarData()

breviarData = loadBreviarData()

katolikusData = loadKatolikusData()

lelkiBatyuk = {}
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
    if not isinstance(calendarDay['Celebration'], dict):
        for celebration in calendarDay['Celebration']:
            lelkiBatyu['celebration'].append(transformCelebration(celebration))
    else:
        lelkiBatyu['celebration'].append(transformCelebration(calendarDay['Celebration']))

    addCustomCelebrationstoBreviarData(lelkiBatyu)


    #find LiturgicalReadings by readingsBreviarId/LiturgicalReadingsId
    for key in range(len(lelkiBatyu['celebration'])):
        celebration = lelkiBatyu['celebration'][key]
        celebration['celebrationKey'] = key
        print("", end='\r', flush=True)
        sys.stdout.flush()

        createReadingIds(celebration)


        findReadings(celebration)


        addreadingstolevel10(celebration)
        clearYearIorII(celebration)





    #find LiturgicalReadings by readingsBreviarId/LiturgicalReadingsId
   # for celebration in lelkiBatyu['celebration']:
        findCommentaries(celebration)


        # egyéb dolgok
        celebration['dayOfPenance'] = day_of_penance(celebration)

        print("  OK                                  ", end="\r",flush=True)

        #sys.stdout.flush()


    #if calendarDay['DateISO'] == "2024-05-19":
    #    exit()

    # now write output to a file
    with open("batyuk/" + calendarDay['DateISO'] + ".json", "w", encoding='utf8') as breviarDataFile:
        # magic happens here to make it pretty-printed
        breviarDataFile.write(
            simplejson.dumps(lelkiBatyu, indent=4, sort_keys=False, ensure_ascii=False)
        )
    lelkiBatyuk[calendarDay['DateISO']] = lelkiBatyu

exit
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

        if 'parts2' in lelkiBatyukComplex[day]['celebration'][cid]:
            for pid, part in enumerate(lelkiBatyukComplex[day]['celebration'][cid]['parts2']):
                # lista
                if type(part) == dict:
                    lelkiBatyukComplex[day]['celebration'][cid]['parts2'][pid]['type'] = 'object'
                else:
                    tmp = {}
                    tmp['type'] = 'array'
                    tmp['content'] = part

                    for contentid, cont in enumerate(tmp['content']):
                        tmp['content'][contentid]['type'] = 'object'

                    lelkiBatyukComplex[day]['celebration'][cid]['parts2'][pid] = tmp

def save_filtered_lelkiBatyukComplex(year):
    with open(f"batyuk/{year}.json", "w", encoding='utf8') as breviarDataFile:
        filtered_lelkiBatyukComplex = {k: v for k, v in lelkiBatyukComplex.items() if k.startswith(str(year))}
        breviarDataFile.write(
            simplejson.dumps(filtered_lelkiBatyukComplex, indent=4, sort_keys=False, ensure_ascii=False)
        )

save_filtered_lelkiBatyukComplex(datetime.now().year)
save_filtered_lelkiBatyukComplex(datetime.now().year + 1)


print("készen vagyunk")
