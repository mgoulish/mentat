#!/usr/bin/env python3

import sys
import os
import re
from   datetime import datetime, timezone



# Expected format: 2025-09-16 04:22:22.956513
def string_to_microseconds_since_epoch ( s ):
    dt = datetime.strptime(s, "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1_000_000)



def new_mentat ( root ) :
  keys = [ 'root',
           'sites',
           'events' ]
  mentat = dict.fromkeys ( keys, None )
  mentat['root']   = root
  mentat['sites']  = []
  mentat['events'] = []
  print ( f"mentat info: new mentat created with root {root}" )
  return mentat



def new_site ( name ) :
  keys = [ 'name',
           'routers' ]
  site = dict.fromkeys ( keys, None )
  site['routers'] = []
  site['name'] = name
  print ( f"mentat info: new site created with name {name}" )
  return site



def new_router ( name, site ) :
  keys = [ 'name',
           'current_events',
           'previous_events',
           'site' ]
  router = dict.fromkeys ( keys, None )
  router['name']            = name
  router['site']            = site
  router['current_events']  = []
  router['previous_events'] = []
  print ( f"mentat info: new router created with name {name}" )
  return router



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



