### This script scrapes all the "Mountains & Rocks" pages on www.summitpost.org and creates a KML file which plots them in  ###
### Google Earth. Each placemark in Google Earth contains the name and altitude of the mountain or rock and a link to its   ###
### summitpost page.                                                                                                        ###
###                                                                                                                         ###
### The coordinates are provided by users on the website and accuracy varies. Some are clearly wrong.                       ###
### For documentation on the main libraries used, see:                                                                      ###
###     BeautifulSoup     www.crummy.com/software/BeautifulSoup/bs4/doc/                                                    ###
###     pykml             www.pythonhosted.org/pykml/index.html                                                             ###

from bs4 import BeautifulSoup as bs
import requests
import re
from lxml import etree
from pykml.factory import KML_ElementMaker as KML

### first loop creates lists of mountain page names, URLs, and altitudes  
URLs = []
alt = []
names = []
for i in range(1,269):
    ### The while clause repeats iterations in case of phantom errors in which an element is not added to one of the lists.
    successful = False
    x = 0
    while not successful and x < 5:
        summit = requests.get("http://www.summitpost.org/object_list.php?search_in=name_only&order_type=DESC&object_type=1&orderby=object_name&page="+str(i),allow_redirects = False)
        if summit.status_code == 301:
            continue
        URLupdate = [x.split(' ')[0][:-1] for x in str(bs(summit.text).findAll('a', {'style':'font-weight: bold; font-size: 12px; font-family: arial black;'})).split('href="')][1:]
        altupdate = [str(x)[95:-12].replace("<br/>","") for x in bs(summit.text).findAll('td',{'class':'srch_results_rht'})[2::7]]
        namesupdate = [x.split('>, <')[0][:-3].replace("</","") for x in str(bs(summit.text).findAll('a', {'style':'font-weight: bold; font-size: 12px; font-family: arial black;'})).split('">')][1:]  
        if len(URLupdate) != len(altupdate) or len (altupdate) != len(namesupdate):
            successful = False
            x += 1
        else:
            successful = True
            print(i) # to count iterations
            URLs = URLs + URLupdate
            alt = alt + altupdate
            names = names + namesupdate
            
### second loop uses URLs to scrape mountain pages and add lists of latitude, longitude, and total page hits.               
### I don't report the page hits in the KML file. I may use them in a future update as a proxy for climb popularity.        
lat = []
lon = []
hits = []
for URL in URLs[0:len(URLs)]:
    successful = False
    x = 0
    while not successful and x < 5:
        print(URLs.index(URL))
        summitpage = requests.get("http://www.summitpost.org"+URL,allow_redirects = True)
        if summitpage.status_code == 301:
            continue
        coordinates = str(bs(summitpage.text).findAll('a', {'style':'color: #249;'})).split(' ')[4:7]
        pagehits = [x for x in str(bs(summitpage.text).findAll('p')).split(' ') if '\xa0\n' in x]
        ### The coordinates == [] or pagehits == [] conditions are because of the same phantom errors as in the first loop. 
        if coordinates == [] or pagehits == []:
            successful = False
            if x == 4:
                lat.append('')
                lon.append('')
                hits.append('')
            x += 1
        else:
            successful = True
            if coordinates[0][0] != '#': 
                ### The coordinates[0][0] != '#' condition is because some pages do not have listed coordinates.            
                lat.append('')
                lon.append('')
                hits.append('')
            else:
                if coordinates[0][-1] == "S":
                    lat.append("-"+coordinates[0][7:-2])
                else:
                    lat.append(coordinates[0][7:-2])
                if coordinates[2][-6] == "W":
                    lon.append("-"+coordinates[2][:-7])
                else:
                    lon.append(coordinates[2][:-7])
                hits.append(pagehits[0][:-2])
            #print(URLs.index(URL)) # to count iterations

### KML file                                                                                                                
### Defines a document style that hides names until mouse-over.                                                              
### With 12,000+ points, this makes viewing the file much smoother.                                                         
### Based on http://stackoverflow.com/questions/13378030/displaying-names-on-the-map-using-kml                              
kmlobj = KML.kml(
            KML.Document(
                KML.Style(
                    KML.LabelStyle(
                        KML.scale(0)),id = "sn_hide"),
                KML.Style(
                    KML.LabelStyle(
                        KML.scale(1)),id = "sh_style"),
                KML.StyleMap(
                    KML.Pair(
                        KML.key("normal"),
                        KML.styleUrl('#sn_hide')),
                    KML.Pair(
                        KML.key("highlight"),
                        KML.styleUrl('#sh_style')),id = "msn_hide")))
### Places the results of the loops into the KML document as points.                                                        
for i in range(0,len(lat)):
    if lat[i] != '':
        kmlobj.Document.append(           
            KML.Placemark(
                KML.Style(
                    KML.IconStyle(
                        KML.scale(0.5),
                        KML.Icon(
                            KML.href("http://crec.unl.edu/images/Icons/OA%20Mountain%201%20Red.png"),))), 
                            KML.name(names[i]),
                            KML.description(alt[i]+" "+"www.summitpost.org"+URLs[i]),
                            KML.styleUrl('#msn_hide'),
                            KML.Point(
                                KML.extrude(1),
                                KML.altitudeMode('relativeToGround'),
                                KML.coordinates('{lon},{lat},{alt}'.format(lon=lon[i],lat=lat[i],alt=10,),),),))
### saves the KML document as a file on the hard drive.                                                                     
KML = open('summitpost.kml', 'w')
KML.write(str(etree.tostring(etree.ElementTree(kmlobj),pretty_print=False))[2:-1])
KML.close()
