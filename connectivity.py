#!/usr/bin/env python3


import pprint
from   datetime import datetime, timezone
import re



def new_skstat_file ( ) :
  keys = [ 'path',
           'lines',
           'pod_name',
           'site_name' ]
  skstat_file = dict.fromkeys ( keys, None )
  skstat_file['lines'] = []
  return skstat_file



def new_skstat_line ( ) :
  keys = [ 'role',
           'host',
           'port' ]
  skstat_line = dict.fromkeys ( keys, None )
  return skstat_line



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
  if from_host == 'localhost' :
    return None

  for site in network['sites'] :
    for router in site['routers'] :
      ip_list = router['ip']
      for ip in ip_list :
        if ip == from_host :
          return router['pod_name']
    # This site's router didn't match -- try the service controller.
    if site['service_controller']['pod_ip'] == from_host :
      return site['service_controller']['name']
  return None



def ip_to_router_from_skstat ( network, event ) :
  #print ( "ip_to_router_from_skstat" )
  for skstat in network['skstats'] :
    #print ( f"site {skstat['site_name']} pod {skstat['pod_name']}" ) 
    for line in skstat['lines'] : 
      if line['host'] == event['from_host'] :
        #print ( "match !" )
        print ( f"ip_to_router_from_skstat I see role of:  {line['role']}" )
        event['from_host_name']  = skstat['pod_name']
        event['connection_type'] = line['role']
        return 



# A connection came in on this port, and we want to find the 
# mode of the port so we can tell what kind of connection this is.
def find_port_role ( site, port ) : 
  for listener in site['listeners'] :
    if str(listener['port']) == str(port) :
      return listener['role']
  return None



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
  cnx_count = 0
  for site in network['sites'] :
    # First, make sure that the events in this site are all sorted timewise.
    sorted_events = sorted(site['raw_events'], key=lambda x: x['epoch_micros'])
    site['raw_events'] = sorted_events

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
            cnx['disconnect_event'] = re_2
            cnx['duration_usec']    = re_2['epoch_micros'] - cnx['micros']
            cnx["duration_hms"]     = usec_to_duration ( cnx['duration_usec'] )
            cnx['lines'].extend(re_2['lines'])

        # In my training data, there was never more than 1
        # event with the same connection ID, after the initial
        # connection accepted event.
        site['events'].append ( cnx )
        cnx_count += 1
  print ( f"make_connections info: made {cnx_count} connections" )



# Example of the path to the files:  ./wynford/pods/skupper-router-7f4bf489d5-lmzhp/skstat/skstat-c.txt
def read_skstat ( network ) :
  skstat_files = []
  #print ( "\nread_skstat -----------------------" )
  for site in network['sites'] :
    for router in site['routers'] :
      skstat_file_name = f"{site['root']}/pods/{router['pod_name']}/skstat/skstat-c.txt"
      skstat_file = new_skstat_file()
      skstat_file['path']      = skstat_file_name
      skstat_file['pod_name']  = router['pod_name']
      skstat_file['site_name'] = site['name']
      with open(skstat_file_name) as f:
        content = f.readlines()
        #print ( f"got {len(content)} lines" )
        read = False
        line_count = 0
        for line in content :
          line_count += 1
          if read :
            words = line.split()
            # Here are the field names of each line:
            #  (taken from the file) 
            #  1   id     
            #  2   host                                         
            #  3   container                                               
            #  4   role               
            #  5   proto  
            #  6   dir  
            #  7   security                         
            #  8   authentication                  
            #  9   meshId  
            #  10  last 
            #  11  dlv      
            #  12  uptime
            role = words[3]
            if role.startswith('inter-router') :
              skstat_line = new_skstat_line()
              skstat_line['role'] = role
              skstat_line['host'] = words[1].split(':')[0]
              skstat_line['port'] = words[1].split(':')[1]
              skstat_file['lines'].append ( skstat_line )

          if '=====' in line :
            read = True
            #print ( f"Start reading after line {line_count}" )
      skstat_files.append(skstat_file)

  return skstat_files

          



def find_connection_origins ( network ) :
  find_count   = 0
  total_count  = 0
  for site in network['sites'] :
    for event in site['events'] :
      if event['type'] == 'connection' :
        total_count += 1
        # If the connection came from localhost check
        # the mode of the port it came in on.
        # that will serve as a confirmation that it is a client 
        # connection.
        if event['to_port'].startswith("localhost") :
          event['from_host_name'] = 'localhost'
          port = event['to_port'].split(':')[1]
          if port == None :
            print ( f"find_connection_origins error: can't get port from {event['to_port']}" )
            sys.exit(1)
          role = find_port_role ( site, port )
          print ( f"find_connection_origins role == {role}" )
          if role == None :
            print ( f"find_connection_origins error: can't get role from {site['name']} {port}" )
            sys.exit(1)
          if role == 'normal' :
            event['connection_type'] = 'client'
            find_count += 1

        else :
          # for example: 254.18.23.2
          pattern = r'^\d+\.\d+\.\d+\.\d+$'
          match = re.match ( pattern, event['from_host'] )
          if match :
            event['from_host_name'] = ip_to_router ( network, event['from_host'] )
            if event['from_host_name'] != None :
              find_count += 1
            else : 
              #print ( f"find_connection_origins: can't find {event['from_host']}" )
              #event['from_host_name'], event['type'] = ip_to_router_from_skstat ( network, event['from_host'] )
              ip_to_router_from_skstat ( network, event )
              if event['from_host_name'] != None :
                print ( f"found {event['from_host_name']} using skstat" )
                print ( f"also found type {event['type']} using skstat" )
                find_count += 1
 
  print ( f"find_connection_origins info: found origins for {find_count} connections." )
  print ( f"find_connection_origins info: failed on {total_count - find_count}." )



