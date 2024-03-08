import requests
import xmltodict
import simplejson


def downloadBreviarData():

    # get breviarData from url
    url = "https://breviar.kbs.sk/cgi-bin/l.cgi?qt=pxml&d=*&m=3&r=2024&j=hu"
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



#downloadBreviarData()
#breviarData = loadBreviarData()
#print(breviarData)

print("Hello World")
