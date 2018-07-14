import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import datetime
from time import sleep
from datetime import date
from random import randint
import re

pfad="Immobilienscout\\"
bundeslaender = ["Berlin"] #,"Mecklenburg-Vorpommern","Brandenburg","Sachsen"]

"""------------------------------------------------------------------"""
"""------------------------------------------------------------------"""
"""Erstellung von Methoden und Klassen"""

def suchrundenErmittlung(bundesland):
    anzahlSuchergebnisseProSeite=20
    source=requests.get(f"https://www.immobilienscout24.de/Suche/S-34/P-1/Haus-Kauf/{bundesland}/-/-/-/-/EURO--750000,00/-/-/-/-/3,4").text
    soup=BeautifulSoup(source,"lxml")
    suchrunden = round(int(str(str(soup.find("h1")).split("resultlist-resultCount\">")[1].split("<!-- -->")[0]).replace(".",""))/anzahlSuchergebnisseProSeite)+1
    return suchrunden

class RegionsKennzahlen:

    def einheiten_eliminieren(self,betragmiteinheit):
        betragmiteinheit = betragmiteinheit.replace(".", "")
        betragOHNEeinheit=re.findall("\d+\,\d+|\d+", betragmiteinheit)
        return betragOHNEeinheit[0]


    def __init__(self,link_expose):

        source_link_zielregion = requests.get(link_expose).text
        soup=BeautifulSoup(source_link_zielregion,"lxml")

        zielregion=soup.find_all("div",attrs={"class":"border-bottom"})

        for link in zielregion:
            try:
                linkextract=(link.span.a["href"].split("?referrer=expose"))[0]
                link_zielregion= f"https://www.immobilienscout24.de{linkextract}"
                source_immobilienpreise=requests.get(link_zielregion).text
                soup_immobilienpreise=BeautifulSoup(source_immobilienpreise,"lxml")
            except:
                pass

        try:
            kennzahlen_region=soup_immobilienpreise.find_all("div", attrs={"class": "cockpit-value"})
        except:
            pass

        try:
            self.qm_wohnung_miete=kennzahlen_region[0].text
            self.qm_wohnung_miete=self.einheiten_eliminieren(self.qm_wohnung_miete)
            return qm_wohnung_miete
        except:
            pass

        try:
            self.qm_wohnung_kauf=kennzahlen_region[1].text
            self.qm_wohnung_kauf=self.einheiten_eliminieren(self.qm_wohnung_kauf)
            return qm_wohnung_kauf
        except:
            pass

        try:
            self.haeuser_kauf=kennzahlen_region[2].text
            self.haeuser_kauf=self.einheiten_eliminieren(self.haeuser_kauf)
            return haeuser_kauf
        except:
            pass

"""------------------------------------------------------------------"""
"""------------------------------------------------------------------"""


for bundesland in bundeslaender:

    linkdateiname = "linkdatei_aktuelles.txt"
    exposeliste = []
    exposeErgebnisListe = []
    suchseite = 1
    #suchRunden=1
    suchRunden = suchrundenErmittlung(bundesland)
    print(f"Zu durchsuchende Suchseiten für {bundesland}: ", suchRunden)
    schreibrundenZaehler = 0
    schreibbatchgroesse = 5
    aktuelle_woche = f"{date.isocalendar(datetime.datetime.now())[0]}{date.isocalendar(datetime.datetime.now())[1]}"  # Format: YYYYWW
    aktueller_tag = f"{datetime.datetime.now()}"  # Format: YYYYWW

    while suchseite <=suchRunden:
        print(f"Start mit Suchseite: {suchseite}, {bundesland}, Woche {aktuelle_woche}")

        "Kurz warten, dann weitermachen"
        pausenZeit = randint(0, 1000) / 1000
        sleep(pausenZeit)

        #https://www.immobilienscout24.de/Suche/S-T/P-{suchseite}/Haus-Kauf/archiv/Brandenburg/-/-/-/-/EURO--750000,00/-/-/-/-/3,4
        source=requests.get(f"https://www.immobilienscout24.de/Suche/S-34/P-{suchseite}/Wohnung-Kauf/{bundesland}/-/-/-/-/EURO--750000,00/-/-/-/-/3,4").text
        soup=BeautifulSoup(source,"lxml")

        """Abgreifen der Immoscout-Suchliste"""
        for link in soup.find_all("li",class_="result-list__listing"):
            link=link.find("div",class_="result-list-entry__data").a["href"]
            link_komplett=f"https://www.immobilienscout24.de{link}"

            """Exposedoppel in Linkdatei prüfen und nur fehlende mit aufnehmen"""
            with open(pfad+linkdateiname,"r+") as linkdatei:
                if link_komplett in linkdatei.read():
                    print(f"Link {link_komplett} schon in Datei")
                    pass

                else:
                    """linkliste auffüllen mit den neuen Exposelinks"""
                    exposeliste.append(link_komplett)
                    linkdatei.write(link_komplett + "\n")

        suchseite=suchseite+1

    """Einzelexposes durchsuchen"""
    if len(exposeliste) >0:
        print (f"{str(datetime.datetime.now())} {len(exposeliste)} Neue Exposes gefunden: {exposeliste}")

        rundenZaehler=1
        for expose in exposeliste:
            schreibrundenZaehler = schreibrundenZaehler + 1
            exposesource=requests.get(expose).text

            "Kurz warten, dann weitermachen, Runde ansagen"
            #sleep(randint(1000,4000)/1000)
            print(f"Exposeeinzelrunde: {rundenZaehler} - {expose}")
            #print(f"Pausiert für {pausenZeit}s")

            """Altes Dataframes und Listen leeren"""
            #exposeErgebnisListe=[]

            """Regionskennzahlen MIETE, WOHNUNGSKAUF, HAEUSERKAUF ermitteln. Ergebnisse werden weiter unten ins Dataframe eingetragen"""
            regionskennzahl=RegionsKennzahlen(expose)

            try:
                """Alle benötigten Einzelfelder zusammensuchen und als dictionary in die exposeErgebnisliste schreiben"""
                exposesoup=BeautifulSoup(exposesource,"lxml")
                data = json.loads(str(exposesoup.find_all("script", {"type": "text/javascript"})).split("var keyValues = ")[1].split("}")[0] + str("}"))

            except:
                print("Fehler beim json.loads")
            try:
                data["URL"]=str(expose) #URL dem dict übergeben
            except:
                print("Fehler beim URL Einfügen")
            try:
                data["Datum"]=aktueller_tag
            except:
                print("Fehler beim Datum Einfügen")
            try:
                data["Objektbeschreibung"] = str('"'+exposesoup.find("pre",class_="is24qa-objektbeschreibung text-content short-text").text+'"')
            except:
                print("Fehler beim Objektbeschreibung Einfügen")
                data["Objektbeschreibung"]=None
            try:
                data["Ausstattung"] = str('"'+exposesoup.find("pre", class_="is24qa-ausstattung text-content short-text").text+'"')
            except:
                print("Fehler beim Ausstattung Einfügen")
                data["Ausstattung"]=None
            try:
                data["Lage"] = str('"'+exposesoup.find("pre", class_="is24qa-lage text-content short-text").text+'"')
            except:
                print("Fehler beim Lage Einfügen")
                data["Lage"]=None
            try:
                mieteMITeinheit= exposesoup.find("dd",class_="is24qa-mieteinnahmen-pro-monat grid-item three-fifths").text
                mieteMITeinheit=mieteMITeinheit.replace(".","")
                mieteMITeinheit=mieteMITeinheit.replace(",",".")
                data["Monatsmiete"]=re.findall("\d+\,\d+|\d+", mieteMITeinheit)[0]
            except:
                pass
            try:
                data["Region Wohnungsmiete qm"]=regionskennzahl.qm_wohnung_miete
            except:
               # print("Fehler bei Region Wohnungsmiete qm eintragen")
                pass
            try:
                data["Region Wohnungskauf qm"]=regionskennzahl.qm_wohnung_kauf
            except:
                print("Fehler bei Region Wohnungskauf qm eintragen")
                pass
            try:
                data["Region Haeuserkauf"]=regionskennzahl.haeuser_kauf
            except:
                print("Fehler bei Region Haeuserkauf eintragen")
                pass


            exposeErgebnisListe.append(data)
            rundenZaehler=rundenZaehler+1

            """Alle [schreibbatchgrösse] Datensätze werden diese in CSV geschrieben"""
            outputdateiname = f"AktuellesWebscraper 01_{bundesland}.csv"
            if schreibrundenZaehler%schreibbatchgroesse==0:

                """Neues Dataframe: Spalten sortieren, Umwandeln in Zahl, Berechnete Spalten ergänzen"""

                dfErgebnis = pd.DataFrame(exposeErgebnisListe,columns=["Datum", "URL", "obj_immotype", "obj_livingSpace", "obj_lotArea","obj_yearConstructed", "obj_purchasePrice", "obj_rented","Monatsmiete","IST-Monats-/Marktmiete", "Region Haeuserkauf", "Region Wohnungskauf qm","Region Wohnungsmiete qm", "Mietrendite bei Marktmiete","IST/Markt qm-Preis", "geo_bln","geo_krs", "obj_regio3","geo_plz", "obj_street", "obj_buildingType", "obj_noRooms","obj_condition", "obj_interiorQual", "obj_lastRefurbish","obj_numberOfFloors", "obj_cellar", "obj_noParkSpaces","obj_courtage", "obj_heatingType", "obj_firingTypes", "Ausstattung","Lage", "Objektbeschreibung"])

                try:
                    dfErgebnis["Region Wohnungsmiete qm"] = dfErgebnis["Region Wohnungsmiete qm"].str.replace(",",".").astype(dtype="float64")
                except:
                    print("Fehler bei Region Wohnungsmiete als Numwert definieren")
                    pass
                try:
                    dfErgebnis["obj_purchasePrice"] = pd.to_numeric(dfErgebnis["obj_purchasePrice"])#.replace(to_replace=".", value=",")
                except:
                    pass
                try:
                    dfErgebnis["obj_livingSpace"]=pd.to_numeric(dfErgebnis["obj_livingSpace"])#.replace(to_replace=".",value=",")
                except:
                    pass
                try:
                    dfErgebnis["obj_yearConstructed"] = pd.to_numeric(dfErgebnis["obj_yearConstructed"])#.replace(to_replace=".",value=",")
                except:
                    pass
                try:
                    dfErgebnis["Region Haeuserkauf"] = pd.to_numeric(dfErgebnis["Region Haeuserkauf"])#.replace(to_replace=".",value=",")
                except:
                    pass
                try:
                    dfErgebnis["Region Wohnungskauf qm"] = pd.to_numeric(dfErgebnis["Region Wohnungskauf qm"])#.replace(to_replace=".", value=",")
                except:
                    pass
                try:
                    dfErgebnis["obj_noParkSpaces"] = pd.to_numeric(dfErgebnis["obj_noParkSpaces"])#.replace(to_replace=".",value=",")
                except:
                    pass
                try:
                    dfErgebnis["Mietrendite bei Marktmiete"]=dfErgebnis["Region Wohnungsmiete qm"]*dfErgebnis["obj_livingSpace"]*12/dfErgebnis["obj_purchasePrice"]/1.15
                except:
                    pass
                try:
                    dfErgebnis["IST-Monats-/Marktmiete"]=(dfErgebnis["Monatsmiete"]/dfErgebnis["obj_livingSpace"])/dfErgebnis["Region Wohnungsmiete qm"]
                except:
                    pass
                try:
                    dfErgebnis["IST/Markt qm-Preis"]=(dfErgebnis["obj_purchasePrice"]/dfErgebnis["obj_livingSpace"])/dfErgebnis["Region Wohnungskauf qm"]
                except:
                    pass


                schreibrundenZaehler=0
                exposeErgebnisListe=[]

                try:
                    dfCSV=pd.read_csv(pfad+outputdateiname,sep=";",index_col=0)
                    dfCSVneu=pd.concat([dfErgebnis, dfCSV], ignore_index=True)
                    dfCSVneu=dfCSVneu.dropna(subset=["URL"])
                    dfCSVneu.to_csv(pfad+outputdateiname, sep=";",decimal=".")
                    print("Datensätze in bestehende CSV geschrieben")

                except:
                    dfErgebnis.to_csv(pfad+outputdateiname,sep=";",decimal=".")
                    print("Neue Datei erstellt und Datensätze in CSV geschrieben")