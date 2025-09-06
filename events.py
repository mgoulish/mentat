#!/usr/bin/env python3

import sys
import os
import re
import yaml
import json
import pprint
from   datetime import datetime, timezone


# Pattern-Matching Elements ============================================
date       = r'(\d{4}-\d{2}-\d{2})'
time       = r'(\d{2}:\d{2}:\d{2}\.\d{6})'
date_time  = date + ' ' + time
skip       = r'.*?'
name       = r'name=([^ ]+)'
parent     = r'parent=([^ ]+)'
brackets   = r'\[([^ ]+)\]'
endpoint   = r'(\d+\.\d+\.\d+\.\d+:\d+)'    # 254.12.22.23:55671
host_port  = r'([a-zA-Z\.-]+:\d+)'          # skupper-silm-mongodb.legacy.ocp-prd-wyn.bell.corp.bce.ca:30411
port_only  = r'to (:\d+)'
message    = r'(.*?)'

 


def string_to_microseconds_since_epoch ( s ):
    dt = datetime.strptime(s, "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1_000_000)



def get_matching_lines ( file_name, word ) :
    matching_lines = []
    with open ( file_name, 'r') as file:
      for line in file:
        if word in line:
          matching_lines.append ( line )
    return matching_lines



def new_event ( ) :
  keys = [ 'connection_id',
           'epoch_micros',
           'type', 
           'from',
           'id',
           'line',
           'message',
           'name',
           'parent',
           'timestamp',
           'to' ]
  event = dict.fromkeys ( keys, None )
  return event



def parse_connection_accepted_line (line):
    event = new_event ( )
    pattern = r'^(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2}\.\d{6} \+\d{4}) SERVER \(info\) \[(\w+)\] Accepted connection to (\S+) from ([0-9a-fA-F:.]+:\d+)$'
    match = re.match(pattern, line)
    if match:
        timestamp_str = f"{match.group(1)} {match.group(2)}"
    #print ( f"parse_connection_accepted_line   {event}" )
    return event
        


def find_router_connections_accepted ( root_path, sites ) :
  print ( "looking for connections accepted lines -------------------------------------")
  for site in sites :
    site_name = site['name']
    site['router_log_files'] = []
    print ( f"site: {site_name}" )
    routers = site['routers']

    for router in routers :
      # Find all the "Connection accepted" lines
      connection_accepted_dicts = []
      router_pod_name = router['pod_name']
      print ( f"read log for {router_pod_name} ")
      router_log_file = f"{root_path}/{site_name}/pods/{router_pod_name}/logs/router-logs.txt"
      site['router_log_files'].append ( router_log_file )
      #print ( f"log file: {router_log_file}" )
      accepted_lines = get_matching_lines ( router_log_file, "Accepted" )
      #print ( f"There are {len(accepted_lines)} matching lines." )
      for line in accepted_lines :
        #print ( line )
        event = parse_connection_accepted_line ( line )
        event['router_pod_name'] = router_pod_name
        #connection_accepted_dicts.append ( parsed_line )
        site ['events'].append ( event )
      #print ( f"read_router_connections_accepted: There are {len(connection_accepted_dicts)} parsed lines" )
      #sorted_connection_accepted_dicts = sorted(connection_accepted_dicts, key=lambda x: x['epoch_micros'])
      #router['connections_accepted'] = sorted_connection_accepted_dicts
  print ( "\n" )



# done
def parse_unknown_protocol ( log_line ) :
    # example log line :
    # 2025-07-31 20:05:54.645959 +0000 FLOW_LOG (info) LOG [lmzhp:2305] BEGIN END parent=lmzhp:0 logSeverity=3 logText=LOG_SERVER: [C20045] Connection from 254.12.22.1:32886 (to :55671) failed: amqp:connection:framing-error Unknown protocol detected: 'OPTIONS / HTTP/1.1\x0d\x0aHost: 254.12.22.23:55671\x0d\x0aUser-Agent: Go-http-client/1.1\x0d\x0aAccept-Encoding: gzip\x0d\x0aConnection: close\x0d\x0a\x0d\x0a' sourceFile=/remote-source/skupper-router/app/src/server.c sourceLine=1107
  pattern = date + ' ' + time + skip + brackets + skip + parent + skip + brackets + " Connection from " + endpoint + skip + port_only

  event = new_event ( )
  match = re.match ( pattern, log_line)
  if match:
    event['type']          = 'connection_failed'
    event['line']          = log_line
    event['timestamp']     = match.group(1) + ' ' + match.group(2)
    event['brackets']      = match.group(3)
    event['parent']        = match.group(4)
    event['connection_id'] = match.group(5)
    event['from']          = match.group(6)
    event['to']            = match.group(7)
    event['epoch_micros']  = string_to_microseconds_since_epoch ( f"{match.group(1)} {match.group(2)}" )
    #print ( f"match: unknown protocol: |{log_line}|" )
    #pprint.pprint ( event )
  return event



# done
def parse_no_route_to_host ( log_line ) :
  # example :
  # 2025-07-31 13:25:17.088145 +0000 FLOW_LOG (info) LOG [lmzhp:1686] BEGIN END parent=lmzhp:0 logSeverity=3 logText=LOG_SERVER: [C1718] Connection to 254.14.21.121:55671 failed: proton:io No route to host - disconnected 254.14.21.121:55671 sourceFile=/remote-source/skupper-router/app/src/server.c sourceLine=1102
  pattern = date_time + skip + brackets + skip + parent + skip + brackets + skip + "Connection to " + endpoint + message + " sourceFile"
  event = new_event ( )
  event['type']         = 'connection_failed'

  match = re.match ( pattern, log_line)
  if match :
    event['timestamp']     = match.group(1) + ' ' + match.group(2)
    event['epoch_micros']  = string_to_microseconds_since_epoch(event['timestamp']) 
    event['id']            = match.group(3)
    event['parent']        = match.group(4)
    event['connection_id'] = match.group(5)
    event['to']            = match.group(6)
    event['message']       = match.group(7)
  
  #print ( f"match: no route to host   |{log_line}|" )
  #pprint.pprint ( event )
  return event



# done
def parse_connection_timed_out ( log_line ) :
  # example :
  # 2025-08-01 00:03:18.158108 +0000 FLOW_LOG (info) LOG [lmzhp:2357] BEGIN END parent=lmzhp:0 logSeverity=3 logText=LOG_SERVER: [C30497] Connection to 254.14.10.83:55671 failed: proton:io Connection timed out - disconnected 254.14.10.83:55671 sourceFile=/remote-source/skupper-router/app/src/server.c sourceLine=1102
  event = new_event ( )

  pattern = date_time + skip + brackets + skip + "Connection to " + endpoint
  match = re.match ( pattern, log_line)
  if match :
    event['type']          = 'connection_timed_out'
    event['timestamp']     = match.group(1) + ' ' + match.group(2)
    event['epoch_micros']  = string_to_microseconds_since_epoch(event['timestamp']) 
    event['id']            = match.group(3)
    event['to']            = match.group(4)

  #print ( f"\nmatch: connection timed out |{log_line}|" )
  #pprint.pprint ( event )
  return event



# done
def parse_connection_reset_by_peer ( log_line ) :
  # example :
  # 2025-07-31 13:23:31.033934 +0000 FLOW_LOG (info) LOG [lmzhp:297] BEGIN END parent=lmzhp:0 logSeverity=3 logText=LOG_SERVER: [C8] Connection to 254.14.10.83:55671 failed: proton:io Connection reset by peer - disconnected 254.14.10.83:55671 (SSL Failure: error:0A000126:SSL routines::unexpected eof while reading) sourceFile=/remote-source/skupper-router/app/src/server.c sourceLine=1102
  # print ( f"match: Connection reset by peer |{log_line}|" )
  event = new_event ( )

  pattern = date_time + skip + brackets + skip + parent + skip + brackets + skip + "Connection to " + endpoint
  match = re.match ( pattern, log_line)
  if match :
    event['type']          = 'connection_reset_by_peer'
    event['timestamp']     = match.group(1) + ' ' + match.group(2)
    event['epoch_micros']  = string_to_microseconds_since_epoch(event['timestamp']) 
    event['id']            = match.group(3)
    event['parent']        = match.group(4)
    event['connection_id'] = match.group(5)
    event['to']            = match.group(6)

  #print ( f"\nmatch: connection timed out |{log_line}|" )
  #pprint.pprint ( event )

  return event



# done
def parse_unexpected_eof ( log_line ) :
  # example :
  # 2025-07-31 13:22:58.374561 +0000 FLOW_LOG (info) LOG [lmzhp:20] BEGIN END parent=lmzhp:0 logSeverity=3 logText=LOG_SERVER: [C7] Connection to 254.14.21.121:55671 failed: amqp:connection:framing-error SSL Failure: error:0A000126:SSL routines::unexpected eof while reading sourceFile=/remote-source/skupper-router/app/src/server.c sourceLine=1102
  #print ( f"unexpected eof |{log_line}|" )
  event = new_event ( )

  pattern = date_time + skip + brackets + skip + parent + skip + brackets + skip + "Connection to " + endpoint
  match = re.match ( pattern, log_line)
  if match :
    event['type']          = 'unexpected_eof'
    event['timestamp']     = match.group(1) + ' ' + match.group(2)
    event['epoch_micros']  = string_to_microseconds_since_epoch(event['timestamp']) 
    event['id']            = match.group(3) 
    event['parent']        = match.group(4)
    event['connection_id'] = match.group(5)
    event['to']            = match.group(6)

  #print ( f"\nmatch: unexpected eof |{log_line}|" )
  #pprint.pprint ( event )

  return event



# done
def parse_configuration_failed ( log_line ) :
  # example :
  # 2025-07-31 13:22:08.033962 +0000 FLOW_LOG (info) LOG [dv879:13] BEGIN END parent=dv879:0 logSeverity=3 logText=LOG_SERVER: SSL CA configuration failed for connection [C11] to skupper-silm-mongodb.legacy.ocp-prd-wyn.bell.corp.bce.ca:30411 sourceFile=/remote-source/skupper-router/app/src/server.c sourceLine=1277
  #print ( f"configuration failed |{log_line}|" )
  event = new_event ( )

  pattern = date_time + skip + brackets + skip + parent + skip + "configuration failed for connection " + brackets
  match = re.match ( pattern, log_line)
  if match :
    event['type']          = 'configuration_failed'
    event['timestamp']     = match.group(1) + ' ' + match.group(2)
    event['epoch_micros']  = string_to_microseconds_since_epoch(event['timestamp']) 
    event['id']            = match.group(3)
    event['parent']        = match.group(4)
    event['connection_id'] = match.group(5)

  #print ( f"\nmatch: configuration failed |{log_line}|" )
  #pprint.pprint ( event )

  return event



# done
def parse_no_protocol_header_found ( log_line ) :
  # example :
  # 2025-07-31 13:22:08.033996 +0000 FLOW_LOG (info) LOG [dv879:16] BEGIN END parent=dv879:0 logSeverity=3 logText=LOG_SERVER: [C11] Connection to skupper-silm-mongodb.legacy.ocp-prd-wyn.bell.corp.bce.ca:30411 failed: amqp:connection:framing-error Expected AMQP protocol header: no protocol header found (connection aborted) sourceFile=/remote-source/skupper-router/app/src/server.c sourceLine=1102
  #print ( f"no protocol header found |{log_line}|" )
  event = new_event ( )

  pattern = date_time + skip + brackets + skip + parent + skip + brackets + skip + "Connection to " + host_port
  match = re.match ( pattern, log_line)
  if match :
    event['type']          = 'no_protocol_header'
    event['timestamp']     = match.group(1) + ' ' + match.group(2)
    event['epoch_micros']  = string_to_microseconds_since_epoch(event['timestamp']) 
    event['id']            = match.group(3)
    event['parent']        = match.group(4)
    event['connection_id'] = match.group(5)
    event['to']            = match.group(6)

  #print ( f"\nmatch: no protocol header |{log_line}|" )
  #pprint.pprint ( event )

  return event



# done
def parse_no_cert ( log_line ) :
  # example :
  # 2025-07-31 20:05:51.844516 +0000 FLOW_LOG (info) LOG [lmzhp:2286] BEGIN END parent=lmzhp:0 logSeverity=3 logText=LOG_SERVER: [C20023] Connection from 254.12.22.1:36680 (to :45671) failed: amqp:connection:framing-error SSL Failure: error:0A0000C7:SSL routines::peer did not return a certificate sourceFile=/remote-source/skupper-router/app/src/server.c sourceLine=1107
  #print ( f"no cert |{log_line}|" )
  event = new_event ( )

  pattern = date_time + skip + brackets + skip + parent + skip + brackets + skip + "Connection from " + endpoint + skip + port_only
  match = re.match ( pattern, log_line)
  if match :
    event['type']          = 'no_cert'
    event['timestamp']     = match.group(1) + ' ' + match.group(2)
    event['epoch_micros']  = string_to_microseconds_since_epoch(event['timestamp']) 
    event['id']            = match.group(3)
    event['parent']        = match.group(4)
    event['connection_id'] = match.group(5)
    event['from']          = match.group(6)
    event['to']            = match.group(7)

  #print ( f"\nmatch: no cert |{log_line}|" )
  #pprint.pprint ( event )

  return event



# done
def parse_setup_error ( log_line ) :
  # example :
  # 2025-07-31 13:22:08.033985 +0000 FLOW_LOG (info) LOG [dv879:15] BEGIN END parent=dv879:0 logSeverity=3 logText=LOG_SERVER: [C11] Connection aborted due to internal setup error sourceFile=/remote-source/skupper-router/app/src/server.c sourceLine=766
  #print ( f"setup error |{log_line}|" )
  event = new_event ( )

  pattern = date_time + skip + brackets + skip + parent + skip + brackets
  match = re.match ( pattern, log_line)
  if match :
    event['type']          = 'setup_error'
    event['timestamp']     = match.group(1) + ' ' + match.group(2)
    event['epoch_micros']  = string_to_microseconds_since_epoch(event['timestamp']) 
    event['id']            = match.group(3)
    event['parent']        = match.group(4)
    event['connection_id'] = match.group(5)

  #print ( f"\nmatch: internal setup error |{log_line}|" )
  #pprint.pprint ( event )

  return event



def parse_direction_outgoing ( log_line ) :
  # example :
  # 2025-07-31 13:23:31.032207 +0000 FLOW_LOG (info) LINK [lmzhp:11] BEGIN END parent=lmzhp:0 mode=interior name=skupper-prd-wyn-skupper-router-78979fc89c-jfhn8 linkCost=1 direction=outgoing
  #print ( f"direction outgoing |{log_line}|" )
  event = new_event ( )

  pattern = date_time 
  match = re.match ( pattern, log_line)
  if match :
    event['type']          = 'direction_outgoing'
    event['timestamp']     = match.group(1) + ' ' + match.group(2)
    event['epoch_micros']  = string_to_microseconds_since_epoch(event['timestamp']) 

  #print ( f"\nmatch: connection timed out |{log_line}|" )
  #pprint.pprint ( event )

  return event



def parse_BEGIN_END_line ( log_line ) :

  #print ( f"pre-match: line: {log_line}" )

  error_handlers = {
    "Unknown protocol"             : parse_unknown_protocol,
    "No route to host"             : parse_no_route_to_host,
    "Connection timed out"         : parse_connection_timed_out,
    "Connection reset by peer"     : parse_connection_reset_by_peer,
    "routines::unexpected eof"     : parse_unexpected_eof,
    "configuration failed"         : parse_configuration_failed,
    "no protocol header found"     : parse_no_protocol_header_found,
    "did not return a certificate" : parse_no_cert,
    "internal setup error"         : parse_setup_error,
    "direction=outgoing"           : parse_direction_outgoing,
  }

  for error, handler in error_handlers.items():
    if error in log_line:
      return handler ( log_line )

  return None



def find_begin_end_lines ( sites ) :
  print ( "lookig for BEGIN END lines -------------------------------------")
  for site in sites :
    print ( f"site {site['name']} " )
  
    for router_log_file in site['router_log_files'] :
      #print ( f"router log  {router_log_file} " )
      print ( f"router name: {router_log_file.split('/')[-3]}" )
      lines = get_matching_lines ( router_log_file, "BEGIN END" )
      #print ( f"    There are {len(lines)} lines" )
      for line in lines :
        event = parse_BEGIN_END_line ( line )
        if event == None :
          print ( f"bad line: {line}" )
        else:
          event['line'] = line
          event['router_pod_name'] = router_log_file.split('/')[-3]
          site ['events'].append ( event )


    
  



