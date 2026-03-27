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
  match   = re.search(pattern, line)

  if match:
    timestamp    = match.group(1)
    microseconds = utils.string_to_microseconds_since_epoch ( timestamp )
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
  match   = re.search(pattern, line)

  if match:
    timestamp    = match.group(1)
    microseconds = utils.string_to_microseconds_since_epoch ( timestamp )
    return {
      'type'           : 'configured_listener',
      'timestamp'      : timestamp,      
      'microseconds'   : microseconds,
      'port'           : int(match.group(2)),      # e.g. 55671 or 5672 (as integer)
      'role'           : match.group(3)            # e.g. 'inter-router' or 'normal'
    }

  return None  # Line didn't match the expected listener format



def parse_http_listener(line: str) -> dict:
  # example:  2025-09-16 04:22:22.968875 +0000 HTTP (info) Listening for HTTP on :9090
  pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+(?: \+\d{4})?).*?Listening for HTTP on \s*[^:\s]*:(\d+)'
  match   = re.search(pattern, line)

  if match:
    timestamp    = match.group(1)
    microseconds = utils.string_to_microseconds_since_epoch ( timestamp )
    return {
      'type'      : 'http_listener',
      'timestamp' : match.group(1),      
      'microseconds' : microseconds,
      'port': int(match.group(2))       # e.g. 9090 (as integer for easier use)
    }

  return None  # Line didn't match the expected HTTP listener format


def parse_listening_for_client (line: str) -> dict | None:
    # example: 2025-09-16 04:22:22.995325 +0000 ROUTER (info) Listener prd-mc-rs-mdb-1-0-svc:27017: listening for client connections on 0.0.0.0:1024 with backlog 4096
    # Pattern matches:
    # - Timestamp (with or without +0000)
    # - Listener <service>:<target_port>
    # - listening for client connections on <ip>:<local_port>
    pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+(?: \+\d{4})?).*?Listener\s+([^:\s]+):(\d+).*?on [^:\s]*:(\d+)'
    
    match = re.search(pattern, line)
    if match:
        timestamp    = match.group(1)
        microseconds = utils.string_to_microseconds_since_epoch ( timestamp )
        return {
            'type':     'listening_for_client',
            'timestamp': timestamp,                # full timestamp as it appears
            'microseconds': microseconds,
            'service_name': match.group(2),        # e.g. 'prd-mc-rs-mdb-1-0-svc'
            'target_port': int(match.group(3)),    # e.g. 27017  (the real MongoDB port)
            'local_port': int(match.group(4))      # e.g. 1024   (the local listening port)
        }
    return None


def parse_log_line(line: str) -> dict | None:
  # The various parsers return NULL if they don't match the input line.
  # So just run each one until one matches.
  parsers = [
    parse_configured_connector,   
    parse_configured_listener,     
    parse_http_listener,          
    parse_listening_for_client,
  ]

  for parser in parsers:
    data = parser(line)
    if data is not None:
      return data
  return None   # no parser matched



# Only call this after the events from all sites have already been read.
# This is where we know what router and what site we are talking about,
# so we add that info to the connectivity dictionaries here.
def read_connectivity_events ( mentat ) :
  print ( "EXTRACT CONNECTIVITY" )
  for site in mentat['sites'] :
    print ( f"site: {site['name']}" )
    for router in site['routers'] :
      print ( f"  router: {router['nickname']} ({router['name']}) " )
      n_previous_events = len(router['previous_events'])
      n_current_events  = len(router['current_events'])

      for e in router['previous_events'] :
        data = parse_log_line ( e['line'] )
        if data == None :
          continue
        data [ 'site'   ] = site['name']
        data [ 'router' ] = router['name']
        mentat['connectivity_events'].append ( data )


