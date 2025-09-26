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
hostname   = r'([a-zA-Z0-9\.-]+)'           # skupper-silm-mongodb.legacy.ocp-prd-wyn.bell.corp.bce.ca
port_only  = r'to (:\d+)'
message    = r'(.*?)'
string     = r'(\S+)'
 


def new_raw_event ( ) :
  keys = [ 'connection_id',
           'epoch_micros',
           'type', 
           'from',
           'id',
           'lines',
           'message',
           'name',
           'parent',
           'router_pod_name',
           'timestamp',
           'to' ]
  event = dict.fromkeys ( keys, None )
  event['lines'] = []
  return event



def new_line ( ) :
  keys = [ 'type',
           'content',
           'file_name',
           'line_number' ]
  line = dict.fromkeys ( keys, None )
  return line



def string_to_microseconds_since_epoch ( s ):
    dt = datetime.strptime(s, "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1_000_000)



def get_matching_lines ( file_name, word, line_type ) :
  #print ( f"gml: file: {file_name} word: {word}" )
  matching_lines = []
  with open ( file_name, 'r') as file:
    count = 1
    for file_line in file:
      if word in file_line:
        line = new_line()
        line['type']        = line_type
        line['content']     = file_line
        line['file_name']   = file_name
        line['line_number'] = count
        matching_lines.append ( line )
        #print ( f"  {count}" )
      count += 1
  return matching_lines




# example:
#2025-08-01 13:07:22.267199 +0000 SERVER (info) [C65149] Accepted connection to localhost:5672 from 127.0.0.1:51274
def parse_connection_accepted_line ( log_line ):
  event = new_raw_event ( )
  # event['line'] = log_line   delete
  #pattern = date_time + skip + brackets + "Accepted connection " + port_only + " from " + endpoint
  pattern = date_time + skip + brackets + skip + "Accepted connection to " + string + " from " + string
  match   = re.match(pattern, log_line)
  if match:
    event['type']          = 'connection_accepted'
    event['timestamp']     = match.group(1) + ' ' + match.group(2)
    event['epoch_micros']  = string_to_microseconds_since_epoch(event['timestamp']) 
    event['connection_id'] = match.group(3)
    event['to']            = match.group(4)
    event['from']          = match.group(5)

    return event
  else :
    print ( f"connection accepted match failed on line: {log_line}" )
    sys.exit(1)
        


def find_router_connections_accepted ( root_path, sites ) :
  print ( "\nlooking for connections accepted lines -------------------------------------")
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
      accepted_lines = get_matching_lines ( router_log_file, "Accepted", 'connection' )
      for line in accepted_lines :
        event = parse_connection_accepted_line ( line['content'] )
        event['router_pod_name'] = router_pod_name
        # Store the connection-accepted line-structure to make it
        # easy to check this event by hand.
        event['lines'].append ( line )  
        site ['raw_events'].append ( event )



# done
def parse_unknown_protocol ( log_line ) :
    # example log line :
    # 2025-07-31 20:05:54.645959 +0000 FLOW_LOG (info) LOG [lmzhp:2305] BEGIN END parent=lmzhp:0 logSeverity=3 logText=LOG_SERVER: [C20045] Connection from 254.12.22.1:32886 (to :55671) failed: amqp:connection:framing-error Unknown protocol detected: 'OPTIONS / HTTP/1.1\x0d\x0aHost: 254.12.22.23:55671\x0d\x0aUser-Agent: Go-http-client/1.1\x0d\x0aAccept-Encoding: gzip\x0d\x0aConnection: close\x0d\x0a\x0d\x0a' sourceFile=/remote-source/skupper-router/app/src/server.c sourceLine=1107
  event = new_raw_event ( )
  event['line'] = log_line
  event['type'] = 'unknown_protocol'

  pattern = date + ' ' + time + skip + brackets + skip + parent + skip + brackets + " Connection from " + endpoint + skip + port_only

  match = re.match ( pattern, log_line)
  if match:
    event['line']          = log_line
    event['timestamp']     = match.group(1) + ' ' + match.group(2)
    event['brackets']      = match.group(3)
    event['parent']        = match.group(4)
    event['connection_id'] = match.group(5)
    event['from']          = match.group(6)
    event['to']            = match.group(7)
    event['epoch_micros']  = string_to_microseconds_since_epoch ( f"{match.group(1)} {match.group(2)}" )
  else :
    print ( f"parse_unknown_protocol error: {event['type']} match failed on line: {log_line}" )
    sys.exit(1)

  return event



# done
def parse_no_route_to_host ( log_line ) :
  # example :
  # 2025-07-31 13:25:17.088145 +0000 FLOW_LOG (info) LOG [lmzhp:1686] BEGIN END parent=lmzhp:0 logSeverity=3 logText=LOG_SERVER: [C1718] Connection to 254.14.21.121:55671 failed: proton:io No route to host - disconnected 254.14.21.121:55671 sourceFile=/remote-source/skupper-router/app/src/server.c sourceLine=1102
  pattern = date_time + skip + brackets + skip + parent + skip + brackets + skip + "Connection to " + endpoint + message + " sourceFile"
  event = new_raw_event ( )
  event['line'] = log_line
  event['type'] = 'no_route_to_host'

  match = re.match ( pattern, log_line)
  if match :
    event['timestamp']     = match.group(1) + ' ' + match.group(2)
    event['epoch_micros']  = string_to_microseconds_since_epoch(event['timestamp']) 
    event['id']            = match.group(3)
    event['parent']        = match.group(4)
    event['connection_id'] = match.group(5)
    event['to']            = match.group(6)
    event['message']       = match.group(7)
  else :
    print ( f"parse_no_route_to_host error: {event['type']} match failed on line: {log_line}" )
    sys.exit(1)
  
  return event



# done
def parse_connection_timed_out ( log_line ) :
  # example :
  # 2025-08-01 00:03:18.158108 +0000 FLOW_LOG (info) LOG [lmzhp:2357] BEGIN END parent=lmzhp:0 logSeverity=3 logText=LOG_SERVER: [C30497] Connection to 254.14.10.83:55671 failed: proton:io Connection timed out - disconnected 254.14.10.83:55671 sourceFile=/remote-source/skupper-router/app/src/server.c sourceLine=1102
  event = new_raw_event ( )
  event['line'] = log_line
  event['type'] = 'connection_timed_out'

  pattern = date_time + skip + brackets + skip + "Connection to " + endpoint
  match = re.match ( pattern, log_line)
  if match :
    event['timestamp']     = match.group(1) + ' ' + match.group(2)
    event['epoch_micros']  = string_to_microseconds_since_epoch(event['timestamp']) 
    event['id']            = match.group(3)
    event['to']            = match.group(4)
  else :
    print ( f"parse_connection_timed_out error: {event['type']} match failed on line: {log_line}" )
    sys.exit(1)

  return event



# done
def parse_connection_reset_by_peer ( log_line ) :
  # example :
  # 2025-07-31 13:23:31.033934 +0000 FLOW_LOG (info) LOG [lmzhp:297] BEGIN END parent=lmzhp:0 logSeverity=3 logText=LOG_SERVER: [C8] Connection to 254.14.10.83:55671 failed: proton:io Connection reset by peer - disconnected 254.14.10.83:55671 (SSL Failure: error:0A000126:SSL routines::unexpected eof while reading) sourceFile=/remote-source/skupper-router/app/src/server.c sourceLine=1102
  event = new_raw_event ( )
  event['line'] = log_line
  event['type'] = 'connection_reset_by_peer'

  pattern = date_time + skip + brackets + skip + parent + skip + brackets + skip + "Connection to " + string
  match = re.match ( pattern, log_line)
  if match :
    event['timestamp']     = match.group(1) + ' ' + match.group(2)
    event['epoch_micros']  = string_to_microseconds_since_epoch(event['timestamp']) 
    event['id']            = match.group(3)
    event['parent']        = match.group(4)
    event['connection_id'] = match.group(5)
    event['to']            = match.group(6)
  else :
    print ( f"parse_connection_reset_by_peer error: {event['type']} match failed on line: {log_line}" )
    sys.exit(1)

  return event



# done
def parse_unexpected_eof ( log_line ) :
  # example :
  # 2025-07-31 13:22:58.374561 +0000 FLOW_LOG (info) LOG [lmzhp:20] BEGIN END parent=lmzhp:0 logSeverity=3 logText=LOG_SERVER: [C7] Connection to 254.14.21.121:55671 failed: amqp:connection:framing-error SSL Failure: error:0A000126:SSL routines::unexpected eof while reading sourceFile=/remote-source/skupper-router/app/src/server.c sourceLine=1102
  # 2025-07-31 13:22:58.404151 +0000 FLOW_LOG (info) LOG [dv879:480] BEGIN END parent=dv879:0 logSeverity=3 logText=LOG_SERVER: [C13] Connection to skupper-silm-mongodb.legacy.ocp-prd-wyn.bell.corp.bce.ca:30411 failed: amqp:connection:framing-error SSL Failure: error:0A000126:SSL routines::unexpected eof while reading sourceFile=/remote-source/skupper-router/app/src/server.c sourceLine=1102

  # 2025-09-12 19:26:51.557720 +0000 FLOW_LOG (info) LOG [nnbw6:431643] BEGIN END parent=nnbw6:0 logSeverity=3 logText=LOG_SERVER: [C2764] Connection from 254.12.2.1:35829 (to :55671) failed: amqp:connection:framing-error SSL Failure: error:0A000126:SSL routines::unexpected eof while reading sourceFile=/remote-source/skupper-router/app/src/server.c sourceLine=1109

  event = new_raw_event ( )
  event['line'] = log_line
  event['type'] = 'unexpected_eof'

  if "Connection to" in log_line :
    to_pattern = date_time + skip + brackets + skip + parent + skip + brackets + skip + "Connection to " + string
    match = re.match ( to_pattern, log_line)
    if match :
      event['timestamp']     = match.group(1) + ' ' + match.group(2)
      event['epoch_micros']  = string_to_microseconds_since_epoch(event['timestamp']) 
      event['id']            = match.group(3) 
      event['parent']        = match.group(4)
      event['connection_id'] = match.group(5)
      event['to']            = match.group(6)
    else :
      print ( f"parse_unexpected_eof error: {event['type']} match failed on line: {log_line}" )
      sys.exit(1)
  elif "Connection from" in log_line :
    from_pattern = date_time + skip + brackets + skip + parent + skip + brackets + skip + "Connection from " + string
    match = re.match ( from_pattern, log_line)
    if match :
      event['timestamp']     = match.group(1) + ' ' + match.group(2)
      event['epoch_micros']  = string_to_microseconds_since_epoch(event['timestamp']) 
      event['id']            = match.group(3) 
      event['parent']        = match.group(4)
      event['connection_id'] = match.group(5)
      event['from']          = match.group(6)
  else :
    print ( f"parse_unexpected_eof error: neither to nor from in line: {log_line}" )
    sys.exit(1)

  return event



# done
def parse_configuration_failed ( log_line ) :
  # example :
  # 2025-07-31 13:22:08.033962 +0000 FLOW_LOG (info) LOG [dv879:13] BEGIN END parent=dv879:0 logSeverity=3 logText=LOG_SERVER: SSL CA configuration failed for connection [C11] to skupper-silm-mongodb.legacy.ocp-prd-wyn.bell.corp.bce.ca:30411 sourceFile=/remote-source/skupper-router/app/src/server.c sourceLine=1277
  event = new_raw_event ( )
  event['line'] = log_line
  event['type'] = 'configuration_failed'

  pattern = date_time + skip + brackets + skip + parent + skip + "configuration failed for connection " + brackets
  match = re.match ( pattern, log_line)
  if match :
    event['timestamp']     = match.group(1) + ' ' + match.group(2)
    event['epoch_micros']  = string_to_microseconds_since_epoch(event['timestamp']) 
    event['id']            = match.group(3)
    event['parent']        = match.group(4)
    event['connection_id'] = match.group(5)
  else :
    print ( f"parse_configuration_failed error: {event['type']} match failed on line: {log_line}" )
    sys.exit(1)

  return event



# done
def parse_no_protocol_header_found ( log_line ) :
  # example :
  # 2025-07-31 13:22:08.033996 +0000 FLOW_LOG (info) LOG [dv879:16] BEGIN END parent=dv879:0 logSeverity=3 logText=LOG_SERVER: [C11] Connection to skupper-silm-mongodb.legacy.ocp-prd-wyn.bell.corp.bce.ca:30411 failed: amqp:connection:framing-error Expected AMQP protocol header: no protocol header found (connection aborted) sourceFile=/remote-source/skupper-router/app/src/server.c sourceLine=1102
  event = new_raw_event ( )
  event['line'] = log_line
  event['type'] = 'no_protocol_header'

  pattern = date_time + skip + brackets + skip + parent + skip + brackets + skip + "Connection to " + host_port 

  match = re.match ( pattern, log_line)
  if match :
    event['timestamp']     = match.group(1) + ' ' + match.group(2)
    event['epoch_micros']  = string_to_microseconds_since_epoch(event['timestamp']) 
    event['id']            = match.group(3)
    event['parent']        = match.group(4)
    event['connection_id'] = match.group(5)
    event['to']            = match.group(6)
  else :
    print ( f"parse_no_protocol_header_found error: {event['type']} match failed on line: {log_line}" )
    sys.exit(1)

  return event



# done
def parse_no_cert ( log_line ) :
  # example :
  # 2025-07-31 20:05:51.844516 +0000 FLOW_LOG (info) LOG [lmzhp:2286] BEGIN END parent=lmzhp:0 logSeverity=3 logText=LOG_SERVER: [C20023] Connection from 254.12.22.1:36680 (to :45671) failed: amqp:connection:framing-error SSL Failure: error:0A0000C7:SSL routines::peer did not return a certificate sourceFile=/remote-source/skupper-router/app/src/server.c sourceLine=1107
  event = new_raw_event ( )
  event['line'] = log_line
  event['type'] = 'no_cert'

  pattern = date_time + skip + brackets + skip + parent + skip + brackets + skip + "Connection from " + endpoint + skip + port_only
  match = re.match ( pattern, log_line)
  if match :
    event['timestamp']     = match.group(1) + ' ' + match.group(2)
    event['epoch_micros']  = string_to_microseconds_since_epoch(event['timestamp']) 
    event['id']            = match.group(3)
    event['parent']        = match.group(4)
    event['connection_id'] = match.group(5)
    event['from']          = match.group(6)
    event['to']            = match.group(7)
  else :
    print ( f"parse_no_cert error: {event['type']} match failed on line: {log_line}" )
    sys.exit(1)

  return event



# done
def parse_setup_error ( log_line ) :
  # example :
  # 2025-07-31 13:22:08.033985 +0000 FLOW_LOG (info) LOG [dv879:15] BEGIN END parent=dv879:0 logSeverity=3 logText=LOG_SERVER: [C11] Connection aborted due to internal setup error sourceFile=/remote-source/skupper-router/app/src/server.c sourceLine=766
  event = new_raw_event ( )
  event['line'] = log_line
  event['type'] = 'setup_error'

  pattern = date_time + skip + brackets + skip + parent + skip + brackets
  match = re.match ( pattern, log_line)
  if match :
    event['timestamp']     = match.group(1) + ' ' + match.group(2)
    event['epoch_micros']  = string_to_microseconds_since_epoch(event['timestamp']) 
    event['id']            = match.group(3)
    event['parent']        = match.group(4)
    event['connection_id'] = match.group(5)
  else :
    print ( f"parse_setup_error error: {event['type']} match failed on line: {log_line}" )
    sys.exit(1)

  return event



def parse_direction_outgoing ( log_line ) :
  # example :
  # 2025-07-31 13:23:31.032207 +0000 FLOW_LOG (info) LINK [lmzhp:11] BEGIN END parent=lmzhp:0 mode=interior name=skupper-prd-wyn-skupper-router-78979fc89c-jfhn8 linkCost=1 direction=outgoing
  #
  event = new_raw_event ( )
  event['line'] = log_line
  event['type'] = 'direction_outgoing'
  pattern = date_time + skip + brackets + skip + parent + skip + "name=" + hostname
  match = re.match ( pattern, log_line)
  if match :
    event['timestamp']     = match.group(1) + ' ' + match.group(2)
    event['epoch_micros']  = string_to_microseconds_since_epoch(event['timestamp']) 
    event['id']            = match.group(3)
    event['parent']        = match.group(4)
    event['to']            = match.group(5)
  else :
    print ( f"parse_direction_outgoing error: {event['type']} match failed on line: {log_line}" )
    sys.exit(1)
  return event



def parse_direction_incoming ( log_line ) :
  # example :
  # 2025-09-16 04:17:08.177849 +0000 FLOW_LOG (info) LINK [nnbw6:431682] BEGIN END parent=nnbw6:0 mode=interior name=prd-dor-skupper-router-84cc4dd57b-ngtsp direction=incoming
  event = new_raw_event ( )
  event['line'] = log_line
  event['type'] = 'direction_incoming'
  pattern = date_time + skip + brackets + skip + parent + skip + "name=" + hostname
  match = re.match ( pattern, log_line)
  if match :
    event['timestamp']     = match.group(1) + ' ' + match.group(2)
    event['epoch_micros']  = string_to_microseconds_since_epoch(event['timestamp']) 
    event['id']            = match.group(3)
    event['parent']        = match.group(4)
    event['to']            = match.group(5)
  else :
    print ( f"parse_direction_incoming error: {event['type']} match failed on line: {log_line}" )
    sys.exit(1)
  return event



def parse_local_idle_timeout_expired ( log_line ) :
  # example :
  # 2025-09-16 04:17:20.782885 +0000 FLOW_LOG (info) LOG [nnbw6:1047147] BEGIN END parent=nnbw6:0 logSeverity=3 logText=LOG_SERVER: [C2762] Connection from 254.12.2.1:55324 (to :55671) failed: amqp:resource-limit-exceeded local-idle-timeout expired sourceFile=/remote-source/skupper-router/app/src/server.c sourceLine=1109
  event = new_raw_event ( )
  event['line'] = log_line
  event['type'] = 'local_idle_timeout_expired'

  to_in_parentheses = r'\(to (\:\d+)\)'
  failure_message   = r'failed: (.*?) sourceFile=/remote'

  pattern = date_time + skip + brackets + skip + parent + skip + brackets + " Connection from " + endpoint + skip + to_in_parentheses + skip + failure_message
  match = re.match ( pattern, log_line)
  if match :
    event['timestamp']     = match.group(1) + ' ' + match.group(2)
    event['epoch_micros']  = string_to_microseconds_since_epoch(event['timestamp']) 
    event['id']            = match.group(3)
    event['parent']        = match.group(4)
    event['connection_id'] = match.group(5)
    event['from']          = match.group(6)
    event['to']            = match.group(7)
    event['message']       = match.group(8)
  else :
    print ( f"local_idle_timeout_expired error: {event['type']} match failed on line: {log_line}" )
    sys.exit(1)
  return event



def parse_BEGIN_END_line ( log_line ) :

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
    "direction=incoming"           : parse_direction_incoming,
    "local-idle-timeout"           : parse_local_idle_timeout_expired,
  }

  for error, handler in error_handlers.items():
    if error in log_line:
      #print ( f"line handled by: {error}" )
      return handler ( log_line )

  print ( f"parse_BEGIN_END_line: unhandled line: {log_line}" )
  return None



def find_begin_end_lines ( sites ) :
  print ( "looking for BEGIN END lines -------------------------------------")
  for site in sites :
    print ( f"site {site['name']} " )
  
    for router_log_file in site['router_log_files'] :
      print ( f"  router name: {router_log_file.split('/')[-3]}" )
      lines = get_matching_lines ( router_log_file, "BEGIN END", 'disconnection' )
      for line in lines :
        raw_event = parse_BEGIN_END_line ( line['content'] )
        if raw_event == None :
          print ( f"bad line: {line}" )
        else:
          raw_event['router_pod_name'] = router_log_file.split('/')[-3]
          # Store the BEGIN-END line-structure to make it
          # easy to check this event by hand.
          raw_event['lines'].append ( line )  
          site ['raw_events'].append ( raw_event )
          #print ( f"found {raw_event['type']}" )


