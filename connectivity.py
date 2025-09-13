#!/usr/bin/env python3


def new_connection ( ) :
  keys = [ 'from',
           'to', 
           'start',
           'end',
           'duration',
           'type',   # i.e. client, router, DB
           'disconnect_reason' ]
  connection = dict.from_keys ( keys, None )
  return connection



def make_connections ( network ) :
  for site in network['sites'] :
    # First, make sure that the events in this site are all sorted timewise.
    sorted_events = sorted(site['events'], key=lambda x: x['epoch_micros'])
    site['events'] = sorted_events
    print ( f"\nmake_connections for site {site['name']} --------------------------" )
    #print ( f"  there are {len(site['events'])} events in this site" )
    previous = 0
    for event in site['events'] :
      if event['epoch_micros'] < previous :
        print ( "out of order" )
        sys.exit(1)
      print ( f"time {event['epoch_micros']}" )
      previous = event['epoch_micros']



