#!/usr/bin/env python3

import sys
import os
import re
import yaml
import json
import pprint
from   datetime import datetime

import raw_events
import config
import connectivity as conn




#================================================================
#  Main 
#================================================================

root_path =  sys.argv[1] 
network   = config.new_network ( root_path )

print ( "main: reading network" )
config.read_network ( network )

print ( "main: reading raw events" )
raw_events.find_router_connections_accepted ( root_path, network['sites'] )
raw_events.find_begin_end_lines ( network['sites'] )

#print ( "\nmain: network:" )
#pprint.pprint ( network )

print ( "\nmain: make connections:\n" )
conn.make_connections        ( network )
conn.find_connection_origins ( network )


sys.exit(0)   # TEMP

print ( "\n\nmain: events:\n" )

for site in network['sites'] :
  print ( f"\n\n\n  events for site: {site['name']} ---------------------------------------" )
  for event in site['events'] :
    print ( "\n" )
    pprint.pprint ( event )
  print ( "\n\nend site events ---------------------------------------------------------------\n\n\n" )


