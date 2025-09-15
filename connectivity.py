#!/usr/bin/env python3


from datetime import datetime, timezone



def microseconds_to_timestamp ( microseconds ) :
    seconds = microseconds / 1_000_000
    dt = datetime.fromtimestamp(seconds, tz=timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M:%S.%f")



# Here is what a connectio_accepted event looks like
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
           'to_router', 
           'to_port',
           'start_timestamp',
           'end_timestamp',
           'start_micros',
           'end_micros',
           'duration',
           'type', 
           'disconnect_reason' ]
  cnx = dict.fromkeys ( keys, None )
  cnx['type']            = raw_event['type']
  cnx['id']              = raw_event['connection_id']
  cnx['from_host']       = raw_event['from'].split(':')[0]
  cnx['from_port']       = raw_event['from'].split(':')[1]
  cnx['to_router']       = raw_event['router_pod_name']
  cnx['to_port']         = raw_event['to']
  cnx['start_micros']    = raw_event['epoch_micros']
  cnx['start_timestamp'] = microseconds_to_timestamp ( cnx['start_micros'] )
  return cnx



def make_connections ( network ) :
  for site in network['sites'] :
    # First, make sure that the events in this site are all sorted timewise.
    sorted_events = sorted(site['raw_events'], key=lambda x: x['epoch_micros'])
    site['raw_events'] = sorted_events
    print ( f"\nmake_connections for site {site['name']} --------------------------" )
    for raw_event in site['raw_events'] :
      if raw_event['type'] == 'connection_accepted' :
        cnx = new_connection ( raw_event )
        #print ( raw_event )
        site['events'].append ( cnx )
      #else:
        #print ( raw_event )



