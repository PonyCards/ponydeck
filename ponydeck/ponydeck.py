from . import cardsjson

import asyncio
from urllib.parse import urlparse
import sys
import re
import json
from xml.sax.saxutils import escape
import wsgiref
from wsgiref.util import setup_testing_defaults
from wsgiref.simple_server import make_server
import traceback

carddb = cardsjson.CardsDB()

loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.wait([carddb.load()]))

noquery = open('noquery.html', encoding='utf-8').read()

def printSection(name, cards):
  ret = '<section name="' + name + '" shared="False">\n'
  for card in cards:
    ret += '<card qty="' + card[0] + '" id="' + card[1]['octgn_guid'] + '" />\n'
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
  cards = [list(re.search('([a-zA-Z]{2})(F|PF)?(n?\d+)x(\d+)', x).groups()) for x in code.split("-")]
  manes = []
  friends = []
  resources = []
  events = []
  tms = []
  problems = []

  for x in cards:
    try:
      if x[2].startswith('n'):
        x[2] = '-' + x[2][1:]
      card = carddb.cardsByAllIDS[(x[1].lower() if x[1] else '') + x[2] + x[0].upper()]
    except:
      raise UnknownCardError(x[0] + x[1])
    count = x[2]
    {'Mane' : manes,
     'Friend' : friends,
     'Resource' : resources,
     'Event' : events,
     'Troublemaker' : tms,
     'Problem' : problems}[card['type']].append((count, card))

  ret = """<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<deck game="65656467-b709-43b2-a5c6-80c2f216adf9">
"""
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
    return [noquery.encode('utf-8')]
  
  try:
    ret = gen(url)
    status = '200 OK'
    headers = [('Content-type', 'application/xml'),
               ('Content-Disposition', 'attachment; filename="deck.o8d"')]
    start_response(status, headers)
    return [ret.encode('utf-8')]
  except UnknownCardError as e:
    start_response('400 Bad Request', [('Content-type', 'text/plain')])
    return ['Unknown card: '.encode('utf-8'), e.card.encode('utf-8')]
  except:
    traceback.print_exc(20, env['wsgi.errors'])
    start_response('400 Bad Request', [('Content-type', 'text/plain')])
    return ['Invalid request.'.encode('utf-8')]
  
def main():
  httpd = make_server('', 8000, ponydeck)
  print("Serving on port 8000...")
  httpd.serve_forever()

if __name__ == "__main__":
  main()
