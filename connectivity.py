#!/usr/bin/env python3

import sys
import os
import pprint
import re
from   datetime import datetime, timezone

import debug
import new
import utils


def parse_configured_connector ( line: str ) -> dict:
    # example line: 2025-09-16 04:22:22.964858 +0000 CONN_MGR (info) Configured  Connector: skupper-silm-mongodb.legacy.ocp-prd-wyn.bell.corp.bce.ca:31266 proto=any, role=inter-router, sslProfile=link1-profile
    pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+ \+\d{4}) .*?Connector:\s*([^:]+):(\d+).*?role=([^,\s]+)'

    match        = re.search(pattern, line)
    timestamp    = match.group(1)
    microseconds = utils.string_to_microseconds_since_epoch ( timestamp )
    if match:
        return {
            'type'           : 'configured_connector',
            'timestamp'      : timestamp,            # e.g. '2025-09-16 04:22:22.964858 +0000'
            'microseconds'   : microseconds,         # since the epoch
            'connector_name' : match.group(2),       # e.g. 'skupper-silm-mongodb.legacy.ocp-prd-wyn.bell.corp.bce.ca'
            'port'           : int(match.group(3)),  # e.g. 31266 (as integer for easier use)
            'role'           : match.group(4),       # e.g. 'inter-router'
        }
    return None  # Line didn't match the expected format




def parse_configured_listener(line: str) -> dict:
    # example: 2025-09-16 04:22:22.965823 +0000 CONN_MGR (info) Configured  Listener: :55671 proto=any, role=inter-router, sslProfile=skupper-internal
    # regex handles both listener styles (empty-host ":port" and "hostname:port")
    pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+(?: \+\d{4})?).*?Listener:\s*[^:\s]*:(\d+).*?role=([^,\s]+)'
    match = re.search(pattern, line)

    timestamp    = match.group(1)
    microseconds = utils.string_to_microseconds_since_epoch ( timestamp )

    if match:
        return {
            'type'           : 'configured_listener',
            'timestamp'      : timestamp,      
            'microseconds'   : microseconds,
            'port'           : int(match.group(2)),      # e.g. 55671 or 5672 (as integer)
            'role'           : match.group(3)            # e.g. 'inter-router' or 'normal'
        }
    return None  # Line didn't match the expected listener format



# Only call this after the events from all sites have already been read.
def read_connectivity_events ( mentat ) :
  print ( "EXTRACT CONNECTIVITY" )
  for site in mentat['sites'] :
    print ( f"site: {site['name']}" )
    for router in site['routers'] :
      print ( f"  router: {router['nickname']} ({router['name']}) " )
      n_previous_events = len(router['previous_events'])
      n_current_events  = len(router['current_events'])
      #print ( f"    previous events: {n_previous_events}" )
      #print ( f"    current events:  {n_current_events}" )

      for e in router['previous_events'] :
        line = e['line']
        if "Configured  Connector" in line :
          data = parse_configured_connector ( line )
          if data == None :
            print ( "read_connectivity_events error: parse failure on line {line}" )
            continue
          data [ 'site'   ] = site['name']
          data [ 'router' ] = router['name']
          mentat['connectivity_events'].append ( data )
          #pprint.pprint ( data )
        elif "Configured  Listener" in line :
          data = parse_configured_listener ( line )
          if data == None :
            print ( "read_connectivity_events error: parse failure on line {line}" )
            continue
          data [ 'site'   ] = site['name']
          data [ 'router' ] = router['name']
          mentat['connectivity_events'].append ( data )

