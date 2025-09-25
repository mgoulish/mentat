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
import connectivity 





lines = False



def write_report ( network ) :
  for site in network['sites'] :
    network['all_events'].extend ( site['events'] )
    print ( f"  site {site['name']} has {len(site['events'])} events" )
  print (f"network now has {len(network['all_events'])} total events")
  sorted_events = sorted(network['all_events'], key=lambda x: x['micros'])
  site['all_events'] = sorted_events
  event_count = 0
  for event in site['all_events'] :
    event_count += 1
    print ( f"\n{event_count} : {event['timestamp']} {event['type']}" ) 
    print ( f"   to        : {event['to_router']}:{event['to_port']} " ) 
    print ( f"   from      : {event['from_host_name']}:{event['from_port']} " ) 
    print ( f"   type      : {event['connection_type']}" ) 
    
    duration_label = event['duration_hms']
    if duration_label == None :
      duration_label = "unterminated"
    print ( f"   duration  : {duration_label} " ) 

    if duration_label != None :    # This connection was terminated before end of data
      if event['disconnect_event'] != None :
        print ( f"   error     : {event['disconnect_event']['type']}" )



def write_terminated_report ( network ) :
  for site in network['sites'] :
    network['all_events'].extend ( site['events'] )
    print ( f"  site {site['name']} has {len(site['events'])} events" )
  print (f"network now has {len(network['all_events'])} total events")
  sorted_events = sorted(network['all_events'], key=lambda x: x['micros'])
  site['all_events'] = sorted_events
  event_count = 0
  for event in site['all_events'] :
    if event['duration_hms'] == None :   # This connection did not terminate in the data
      continue
    event_count += 1
    print ( f"\n{event_count} : {event['timestamp']} {event['type']}" ) 
    print ( f"   to        : {event['to_router']}:{event['to_port']} " ) 
    print ( f"   from      : {event['from_host_name']}:{event['from_port']} " ) 
    print ( f"   type      : {event['connection_type']}" ) 
    print ( f"   duration  : {event['duration_hms']} " ) 

    if event['disconnect_event'] != None :
      print ( f"   error     : {event['disconnect_event']['type']}" )

    if lines :
      for line in event['lines'] :
        print ( f"    {line}" )
      






#================================================================
#  Main 
#================================================================

root_path =  sys.argv[1] 
network   = config.new_network ( root_path )

print ( "main info: reading network" )
config.read_network ( network )

print ( "main info: reading raw events" )
raw_events.find_router_connections_accepted ( root_path, network['sites'] )
raw_events.find_begin_end_lines ( network['sites'] )

print ( "main info: read skstat" )
network['skstats'] = connectivity.read_skstat ( network )

print ( "\nmain info: making connections" )
connectivity.make_connections        ( network )
connectivity.find_connection_origins ( network )



print ( "\n\n\n" )
while True:
    command = input("command: ")
    if command == 'help' or command == 'h' :
      print ( "q         quit" )
      print ( "report    write full report" )
      print ( "term      report terminated connections" )
      print ( "lines     toggle line display in reports" )
      continue

    if command == 'q' or command == 'quit' :
      break

    if command == 'report' :
      write_report ( network )
      continue

    if command == 'terminated' or command == 'term' :
      write_terminated_report ( network )
      continue

    if command == 'lines' :
      lines = not lines
      if lines : 
        print ( "    lines printing is now ON" )
      else:
        print ( "    lines printing is now OFF" )
      continue




#print ( "\nmain info: writing report" )
#write_report ( network )



#print ( "\n\n\n=============================  SKSTATS =============================" )
#pprint.pprint ( network['skstats'] )


#print ( "\n\nmain: events:\n" )
#
#for site in network['sites'] :
  #print ( f"\n\n\n  events for site: {site['name']} ---------------------------------------" )
  #for event in site['events'] :
    #print ( "\n" )
    #pprint.pprint ( event )
  #print ( "\n\nend site events ---------------------------------------------------------------\n\n\n" )


