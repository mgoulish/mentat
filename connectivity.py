#!/usr/bin/env python3


import pprint
from   datetime import datetime, timezone
import re



def microseconds_to_timestamp ( microseconds ) :
    seconds = microseconds / 1_000_000
    dt = datetime.fromtimestamp(seconds, tz=timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M:%S.%f")


def usec_to_duration ( microseconds ) :
    if microseconds < 0:
        raise ValueError("Microseconds must be non-negative")

    total_seconds = microseconds // 1_000_000
    hours         = total_seconds // 3600
    minutes       = (total_seconds % 3600) // 60
    seconds       = total_seconds % 60
    remaining_microseconds = microseconds % 1_000_000
    milliseconds = remaining_microseconds // 1000

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"



# returns host pod name and site name
def ip_to_router ( site, host ) :
  if host == 'localhost' :
    print ( "ip_to_router: Localhost --> None, None ") 
    return None, None

  for router in site['routers'] :
    ip_list = router['ip']
    for ip in ip_list :
      if ip == host :
        print ( f"ip_to_router: found: {router['pod_name']} {site['name']}  ")
        return router['pod_name'], site['name']
  print ( "ip_to_router: default --> None, None ")
  return None, None



# Here is what a connection_accepted event looks like
#{
#  'connection_id': 'C65142', 
#  'epoch_micros': 1754053638335298, 
#  'type': 'connection_accepted', 
#  'from': '127.0.0.1:51198', 
#  'id': None, 
#  'message': None, 
#  'name': None, 
#  'parent': None, 
#  'router_pod_name': 'skupper-router-7f4bf489d5-lmzhp', 
#  'timestamp': '2025-08-01 13:07:18.335298', 
#  'to': 'localhost:5672'
#}
def new_connection ( raw_event ) :
  keys = [ 'id',
           'from_host',
           'from_port',
           'from_host_name',
           'from_site',
           'to_router', 
           'to_port',
           'timestamp',
           'micros',
           'duration_usec',
           'duration_hms',
           'type', 
           'disconnect_event' ]   # This is the raw event that caused the disconnect
  cnx = dict.fromkeys ( keys, None )
  cnx['type']      = raw_event['type']
  cnx['id']        = raw_event['connection_id']
  #cnx['from_host'] = raw_event['from'].split(':')[0]
  #cnx['from_port'] = raw_event['from'].split(':')[1]
  cnx['to_router'] = raw_event['router_pod_name']
  cnx['to_port']   = raw_event['to']
  cnx['micros']    = raw_event['epoch_micros']
  cnx['timestamp'] = microseconds_to_timestamp ( cnx['micros'] )

  # Check for loopback form of 'from' address
  pattern = r'^::1:(\d{1,5})$'
  match = re.match ( pattern, raw_event['from'] )
  if match :
    cnx['from_host'] = 'localhost'
    cnx['from_port'] = match.group(1)
  else :
    # non-loopback form of 'from' address
    pattern = r'^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5})$'
    match = re.match ( pattern, raw_event['from'] )
    if match :
      cnx['from_host'] = match.group(1)
      cnx['from_port'] = match.group(2)
    else: 
      print ( f"new_connection error: unknown form of 'from' address: {raw_event['from']}" )

  return cnx



# This makes 'cooked' events, each one of which consists
# of two raw events: a connection-accepted event, and a 
# corresponding connection termination event, if any.
def make_connections ( network ) :
  for site in network['sites'] :
    # First, make sure that the events in this site are all sorted timewise.
    sorted_events = sorted(site['raw_events'], key=lambda x: x['epoch_micros'])
    site['raw_events'] = sorted_events

    print ( f"\nmake_connections for site {site['name']} ==========================\n" )
    cnx_count = 0
    for re in site['raw_events'] :
      if re['type'] == 'connection_accepted' :
        cnx = new_connection ( re )
        # Now for each connection accepted, go through 
        # all the raw events in this site looking for 
        # events with the same connection id, looking 
        # for the connection's termination.
        #count = 0
        for re_2 in site['raw_events'] :
          if re_2['type'] != 'connection_accepted' and re_2['connection_id'] == re['connection_id']  :
            # In my training data, these were the reasons for all the disconnects:
            # 24 no_cert
            # 1 no_route_to_host
            # 24 unknown_protocol
            #count += 1
            cnx['disconnect_event'] = re_2
            cnx['duration_usec'] = re_2['epoch_micros'] - cnx['micros']
            cnx["duration_hms"]= usec_to_duration ( cnx['duration_usec'] )

        # In my training data, there was never more than 1
        # event with the same connection ID, after the initial
        # connection accepted event.
        site['events'].append ( cnx )
        cnx_count += 1
    print ( f"make_connections: made {cnx_count} connections" )



def find_connection_origins ( network ) :
  print ( "\n\nfind_connection_origins *******************************************\n" )
  for site in network['sites'] :
    print ( f"  site: {site['name']}" )
    for event in site['events'] :
      if event['type'] == 'connection_accepted' :
        event['from_host_name'], event['site_name'] = ip_to_router ( site, event['from_host'] ) 
        if event['from_host_name'] != None and event['site_name'] != None :
          pprint.pprint ( event )



