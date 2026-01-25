#!/usr/bin/env python3

import sys
import os
import re
from   datetime import datetime, timezone

import debug
import new



# Expected format: 2025-09-16 04:22:22.956513
def string_to_microseconds_since_epoch ( s ):
    dt = datetime.strptime(s, "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1_000_000)



def new_mentat ( root ) :
  keys = [ 'root',
           'sites',
           'events',
           'skstats' ]
  mentat = dict.fromkeys ( keys, None )
  mentat['root']   = root
  mentat['sites']  = []
  mentat['events'] = []
  return mentat



def new_site ( name, root ) :
  debug.debug ( f"making new site {name} at root {root}" )
  keys = [ 'name',
           'routers',
           'ingress-host',
           'root',
           'service_controller',
           'listeners',
           'connectors' ]
  site = dict.fromkeys ( keys, None )
  site [ 'routers']     = []
  site [ 'name']        = name
  site [ 'root' ]       = root
  site [ 'routers' ]    = []
  site [ 'listeners' ]  = []
  site [ 'connectors' ] = []

  return site


def call_counter():
    # Initialize count attribute if it doesn't exist
    if not hasattr(call_counter, 'count'):
        call_counter.count = 0
    # Increment the count
    call_counter.count += 1
    # Print the current count
    print(f"The function has been called {call_counter.count} times.")


def new_router ( name, site ) :
  if not hasattr(new_router, 'count'):
    new_router.count = 0
  new_router.count += 1

  debug.debug ( f"Making new router {name} number {new_router.count}" )

  keys = [ 'name',
           'number',
           'path',
           'current_events',
           'previous_events',
           'site',
           'ip' ]
  router = dict.fromkeys ( keys, None )
  router['name']            = name
  router['number']          = new_router.count
  router['site']            = site
  router['current_events']  = []
  router['previous_events'] = []
  return router



def new_listener ( ) :
  keys     = [ 'name', 'port', 'role' ]
  listener = dict.fromkeys ( keys, None )
  listener['role'] = 'normal'   # Assume this is the default
  return listener



def new_connector ( ) :
  keys     = [ 'host', 'name', 'port', 'role' ]
  connector = dict.fromkeys ( keys, None )
  connector['role'] = 'normal'   # Assume this is the default
  return connector



def new_service_controller ( ) :
  keys = [ "name",
           "pod_path",
           "pod_ip" ]
  return dict.fromkeys ( keys, None )



def new_event ( event_type, timestamp ) :
  # These are the 'mandatory' fields of the event struct.
  # Any others can be added by the code that creates the event
  # depending on event type.
  keys = [ 'type',
           'subtype',
           'timestamp',
           'micros',
           'id'  ]
  event = dict.fromkeys ( keys, None )
  event['type']        = type
  event['timestamp']   = timestamp
  event['micros']      = string_to_microseconds_since_epoch ( timestamp )
  # ID cannot be assigned yet. That is done only at the Mentat level,
  # after all events have been combined into one list.

  # Also subtype -- if used, as it is for log_lines -- will be assigned
  # after they have all been read in.
  return event


# The result list is not a copy of all the filtered events.
# It is just their index numbers in the Mentat list of all events.
def new_filter_chain():
  return {
           'name'    : None,
           'filters' : [],
           'results' : []
         }


def new_filter ( name ) :
  keys = [ 'name',
           'args' ]
  data_filter = dict.fromkeys ( keys, None )
  data_filter['name'] = name
  data_filter['args'] = []
  return data_filter



