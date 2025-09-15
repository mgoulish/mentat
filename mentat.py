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
raw_events.find_router_connections_accepted ( root_path, network['sites'] )
raw_events.find_begin_end_lines ( network['sites'] )

#print ( "\nmain: network:" )
#pprint.pprint ( network )

print ( "\nmain: make connections:\n" )
conn.make_connections ( network )

for site in network['sites'] :
  print ( f"main: site: {site['name']}" )
  for event in site['events'] :
    id = event['id']
    print ( f"looking for: {id} -------------------------" )
    for raw_event in site['raw_events'] :
      line = raw_event['line']
      if id in line :
        print ( raw_event['line'] )


