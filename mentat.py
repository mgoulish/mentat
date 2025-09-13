#!/usr/bin/env python3

import sys
import os
import re
import yaml
import json
import pprint
from   datetime import datetime

import events
import config
import connectivity as conn




#================================================================
#  Main 
#================================================================

root_path =  sys.argv[1] 
network   = config.new_network ( root_path )

print ( "main: reading network" )
config.read_network ( network )
events.find_router_connections_accepted ( root_path, network['sites'] )
events.find_begin_end_lines ( network['sites'] )

#print ( "\nmain: network:" )
#pprint.pprint ( network )

print ( "\nmain: make connections:\n" )
conn.make_connections ( network )

sys.exit(0)

