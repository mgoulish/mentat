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
def ip_to_router ( network, from_host ) :
  #print ( f"ip_to_router looking for from_host {from_host}" )
  if from_host == 'localhost' :
    #print ( "ip_to_router fail can't do localhost")
    return None

  for site in network['sites'] :
    #print ( f"ip_to_router checking site {site['name']}" )
    for router in site['routers'] :
      #print ( f"ip_to_router: checking router {router['pod_name']}" )
      #print ( f"   here is the whole router:  {router} " )
      ip_list = router['ip']
      #print ( f"from_host router has ips: {ip_list}" )
      for ip in ip_list :
        #print ( f"ip_to_router: checking ip {ip} against from_host {from_host}" )
        if ip == from_host :
          #print ( f"ip_to_router success: {from_host} --> {router['pod_name']} " )
          return router['pod_name']
        #else:
          #print ( "nope" )

  #print ( f"ip_to_router: fail finding {from_host} " )
  return None



# TODO make this do something
def find_port_mode ( site, port ) :
  return 'normal'



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
           'duration_hms',      # That stands for "Hours Minutes Seconds"
           'connection_type',
           'type', 
           'disconnect_event',  # This is the raw event that caused the disconnect
           'lines' ]            # file lines that contributed to this event
  cnx = dict.fromkeys ( keys, None )
  cnx['type']      = 'connection'
  cnx['id']        = raw_event['connection_id']
  cnx['to_router'] = raw_event['router_pod_name']
  cnx['to_port']   = raw_event['to']
  cnx['micros']    = raw_event['epoch_micros']
  cnx['timestamp'] = microseconds_to_timestamp ( cnx['micros'] )
  cnx['lines']     = []

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
        # This is the 'cooked' event that will
        # include one or more raw events, like
        # the connection-accepted event and the 
        # disconnect event.
        cnx = new_connection ( re )
        cnx['lines'].extend ( re['lines'] )
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
            cnx['lines'].extend ( re_2['lines'] )

        # In my training data, there was never more than 1
        # event with the same connection ID, after the initial
        # connection accepted event.
        site['events'].append ( cnx )
        cnx_count += 1
    print ( f"make_connections: made {cnx_count} connections" )




def find_connection_origins ( network ) :
  print ( "\n\nfind_connection_origins *******************************************\n" )
  fail_count  = 0
  total_count = 0
  for site in network['sites'] :
    #print ( f"  site: {site['name']}" )
    for event in site['events'] :
      if event['type'] == 'connection' :
        #print ( "\n\n\n")
        #pprint.pprint(event)  # TEMP
        total_count += 1

        # If the connection came from localhost check
        # the mode of the port it came in on.
        # that will serve as a confirmation that it is a client 
        # connection.
        if event['to_port'].startswith("localhost") :
          event['from_host_name'] = 'localhost'
          port = event['to_port'].split(':')[1]
          #print ( f"   port == {port}" )
          if port == None :
            #print ( f"find_connection_origins error: can't get port from {event['to_port']}" )
            sys.exit(1)
          mode = find_port_mode ( site, port )
          if mode == None :
            #print ( f"find_connection_origins error: can't get mode from {site['name']} {port}" )
            sys.exit(1)
          #print ( f"mode == {mode}" )
          if mode == 'normal' :
            #print ( "MATCH localhost" )
            event['connection_type'] = 'client'
          else :
            print ( f"find_connection_origins: case 1 FAILURE" )
            fail_count += 1
            #pprint.pprint ( event )

        else :
          # 254.18.23.2
          pattern = r'^\d+\.\d+\.\d+\.\d+$'
          match = re.match ( pattern, event['from_host'] )
          if match :
            #print ( f"MATCH  from host:  254.18.23.2  from port: {event['from_port']}" )
            event['from_host_name']  = 'TEMP'
            event['connection_type'] = 'TEMP'
            router_name = ip_to_router ( network, event['from_host'] )
            #print ( f"     ip_to_router returns {router_name}")
          else :
            fail_count += 1
            #pprint.pprint ( event )


  print ( f"\n\nfind_connection_origins failed on {fail_count} out of {total_count} events\n\n" )



