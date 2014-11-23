from urlparse import urlparse
import sys
import re
import json
from xml.sax.saxutils import escape
import wsgiref
from wsgiref.util import setup_testing_defaults
from wsgiref.simple_server import make_server
import traceback

octideck = json.load(open('octideck.json'))
noquery = open('noquery.html').read()

def printSection(name, cards):
  ret = '<section name="' + name + '" shared="False">\n'
  for card in cards:
    ret += '<card qty="' + card[0] + '" id="' + card[1]['id'] + '" />\n'
  ret += '</section>\n'
  return ret

class UnknownCardError(Exception):
  def __init__(self, card):
    self.card = card

def gen(url):
  o = urlparse(url)
  d = {v.split("=")[0]:v.split("=")[1] for v in o.query.split("&")}
  code = d.get("v1code")
  if not code:
    return
  cards = [re.search('(\w+)(\d+)x(\d+)', x).groups() for x in code.split("-")]
  manes = []
  friends = []
  resources = []
  events = []
  tms = []
  problems = []

  for x in cards:
    try:
      card = octideck[x[0] + x[1]]
    except:
      raise UnknownCardError(x[0] + x[1])
    count = x[2]
    {'Mane Character' : manes,
     'Friends' : friends,
     'Resources' : resources,
     'Events' : events,
     'Troublemakers' : tms,
     'Problems' : problems}[card['type']].append((count, card))

  ret = """<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<deck game="65656467-b709-43b2-a5c6-80c2f216adf9">"""
  ret += printSection('Mane Character', manes)
  ret += printSection('Friends', friends)
  ret += printSection('Resources', resources)
  ret += printSection('Events', events)
  ret += printSection('Troublemakers', tms)
  ret += printSection('Problems', problems)
  ret += '</deck>'
  return ret
 
def ponydeck(env, start_response):
  setup_testing_defaults(env)

  url = wsgiref.util.request_uri(env)
  if not urlparse(url).query:
    start_response('200 OK', [('Content-type', 'text/html')])
    return [noquery]
  
  try:
    ret = gen(url)
    status = '200 OK'
    headers = [('Content-type', 'application/xml'),
               ('Content-Disposition', 'attachment; filename="deck.o8d"')]
    start_response(status, headers)
    return [str(ret)]
  except UnknownCardError as e:
    start_response('400 Bad Request', [('Content-type', 'text/plain')])
    return ['Unknown card: ', e.card]
  except:
    traceback.print_exc(20, env['wsgi.errors'])
    start_response('400 Bad Request', [('Content-type', 'text/plain')])
    return ['Invalid request.']
  
def main():
  httpd = make_server('', 8000, ponydeck)
  print "Serving on port 8000..."
  httpd.serve_forever()

if __name__ == "__main__":
  main()
