'''

 Title  : Webscrapper for the line view of the website 
          http://mmdatraffic.interaksyon.com
 Author : Felan Carlo Garcia
 email  : felancarlogarcia@gmail.com
          felan@asti.dost.gov.ph

'''

from bs4  import BeautifulSoup
from ftfy import fix_text
from copy import copy
from re   import sub
import requests as rq
import pprint
import time


# http://mmdatraffic.interaksyon.com urls and indexes according to
# the line-view of the website
interaksyon_urls = [
  {'index': 1,  'url':'http://mmdatraffic.interaksyon.com/line-view-edsa.php'           },
  {'index': 2,  'url':'http://mmdatraffic.interaksyon.com/line-view-commonwealth.php'   },
  {'index': 3,  'url':'http://mmdatraffic.interaksyon.com/line-view-quezon-ave.php'     },
  {'index': 4,  'url':'http://mmdatraffic.interaksyon.com/line-view-espana.php'         },
  {'index': 5,  'url':'http://mmdatraffic.interaksyon.com/line-view-c5.php'             },
  {'index': 6,  'url':'http://mmdatraffic.interaksyon.com/line-view-ortigas.php'        },
  {'index': 7,  'url':'http://mmdatraffic.interaksyon.com/line-view-marcos-highway.php' },
  {'index': 8,  'url':'http://mmdatraffic.interaksyon.com/line-view-roxas-blvd.php'     },
  {'index': 9,  'url':'http://mmdatraffic.interaksyon.com/line-view-slex.php'           },
  {'index': 10, 'url':'http://mmdatraffic.interaksyon.com/nlex/line-view-nlex.php'      }
]



def getLocationNames(html_content):
  
  loc = []
  # remove all <a> tags and isolate the  road names 
  for div in html_content.find_all('div', class_='line-name'):
    for aref in div.find_all('a'):
      aref.replaceWith('')

    # ftfy.fix_text() is used in order to prevent mojibake
    # since certain road names have special characters
    loc.append(fix_text(div.text))

  return loc


def getRoadStatus(html_content):

  dir_selector =  1
  sbstats      = []
  nbstats      = [] 

  for div in html_content.find_all('div', class_='line-col'):
    # remove uncessary tabs and split the text every newline
    info_raw   = sub('\t','', str(div.text)).split('\n')
    info       = filter(None, info_raw)[1:]

    # the Update time of the traffic info contains the following
    # string: "Updated: 12:59 pm (last 5 seconds ago)" 
    # In this line, we remove the "(last n times ago)"
    # strings.
    info[-1]   = info[-1].split('(')[0]
  
    # Since the div column of the northbound and southbound
    # information are ordered, we employ a simple modulo
    # trick to determine which line is southbound and northbound
    #   * northbound - if the order is divisible by 2
    #   * southbound - if the order is not divisible by 2
    if((dir_selector % 2) == 0):
      nbstats.append(info)
    else: 
      sbstats.append(info)
    dir_selector = dir_selector + 1

  return {'nb': nbstats, 'sb': sbstats}


def aggregateData(location, sbstats, nbstats):

  data              = {}
  data['details']   = {}
  road_status       = []

  for i in range(0, len(location)):

    data['road_name']      =  location[i]
    data['details']['SB']  =  sbstats[i][0] 
    data['details']['NB']  =  nbstats[i][0]
 
    # Since not all roads have a service road info
    # we first check if the list contains the service 
    # road info. If an info exists, place the service
    # road info on the correspoding road direction. if
    # none is found, place the value 'none' on the 
    # dictionary 
    if(len(nbstats[i]) > 2):
      data['details']['NB_service_road'] = nbstats[i][2]
      data['details']['SB_service_road'] = sbstats[i][2]
    else:
      data['details']['NB_service_road'] = 'none'
      data['details']['SB_service_road'] = 'none'

    road_status.append(copy(data))

  return road_status


def webscrap(webinfo):
  # Get html content and start BeautifulSoup instance
  response     = rq.get(webinfo['url'])
  html_content = BeautifulSoup(response.content)
 
  # get region and road names
  location     = getLocationNames(html_content)
  boundary     = location[0]
  location     = location[1:]

  # get the road status and combine the data
  stats        = getRoadStatus(html_content)
  road_status  = aggregateData(location, stats['sb'], stats['nb'])
  
  # initial time format for the update time is
  # ex: "Updated: 12:14 pm"
  # we remove the "Updated:" string and isolate the time.
  updated      = sub(' ', '',(stats['sb'][0][-1]).split('d:')[-1])

  # return the following dictionary, up to the user to insert to various db's
  # (ex. MongoDB, MySQL, PostgreSQL)
  return {
    '_id'           : webinfo['index'], 
    'region'        : boundary ,
    'roads'         : road_status, 
    'update_time'   : updated, 
    'datetime_read' : time.strftime("%Y-%m-%d %H:%M:%S")
  }



def main():
  pp         = pprint.PrettyPrinter(indent=4)
  info       = webscrap(interaksyon_urls[0])
  pp.pprint(info)


if __name__ == '__main__': 
  main()

