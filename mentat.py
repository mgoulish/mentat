#!/usr/bin/env python3

import sys
import os
import re
import yaml
import json
import pprint
from   datetime import datetime, timezone

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
      


def timestamp_to_microseconds ( ts_str) :
    try:
        # Try parsing with full datetime format
        dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        try:
            # Try parsing with date-only format (defaults to 00:00:00)
            dt = datetime.strptime(ts_str, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Invalid timestamp format. Expected 'YYYY-MM-DD HH:MM:SS' or 'YYYY-MM-DD'.")

    # Set timezone to UTC
    dt = dt.replace(tzinfo=timezone.utc)

    # Convert to seconds since Epoch and multiply by 1,000,000 for microseconds
    return int(dt.timestamp() * 1_000_000)





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

# Get all site events into a single sorted list 
# at the network level
for site in network['sites'] :
  network['all_events'].extend ( site['events'] )
  print ( f"  site {site['name']} has {len(site['events'])} events" )
sorted_events = sorted(network['all_events'], key=lambda x: x['micros'])
site['all_events'] = sorted_events
print (f"network now has {len(network['all_events'])} total events")


# Take interactive commands to inspect the data

print ( "\n\n\n" )
while True:
    command_line  = input("command: ")
    command_words = command_line.split()

    if len(command_words) == 0 :
      continue

    command = command_words[0]

    if command == 'help' or command == 'h' :
      print ( "q         quit" )
      print ( "report    write full report" )
      print ( "term      report terminated connections" )
      print ( "lines     toggle line display in reports" )
      print ( "time      show connectivity at given time")
      print ( "          YYYY-MM-DD HH:MM:SS or YYYY-MM-DD" )
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
    
    if command == 'time' :
      if len(command_words) == 3 :
        timestamp = f"{command_words[1]} {command_words[2]}"
      elif len(command_words) == 2 :
        timestamp = command_words[1]
      else :
        print ( "  usage: time 'YYYY-MM-DD HH:MM:SS' or 'YYYY-MM-DD'" )
        continue

      mikes = timestamp_to_microseconds ( timestamp )
      print ( f"timestamp: {timestamp} {mikes}" )

      event_count        = 0
      unterminated_count = 0
      terminated_count   = 0

      connection_types   = {}

      for event in network['all_events'] :
        if event['type'] != 'connection' :
          continue

        if event['micros'] > mikes :
          break

        #print ( event['duration_usec'] )
        if event['duration_usec'] == None :
          unterminated_count += 1
        else :
          terminated_count   += 1

        #pprint.pprint ( event['connection_type'] )
        ctype = event['connection_type']
        if ctype in connection_types :
          connection_types[ctype] += 1
        else :
          connection_types[ctype] = 1


        event_count += 1
      
      print ( f"There are {event_count} events\n" )

      print ( f"At time {timestamp} ({mikes} usec), there are: " )
      print ( f"    {unterminated_count} unterminated connections" )
      print ( f"    {terminated_count} connections that have terminated.\n" )
      print (  "\nConnection Types:\n" )
      for key in connection_types : 
        first_field_length = 20
        first_field = f"{key}"
        spaces = ' ' * (first_field_length - len(first_field))
        print ( f"{first_field}{spaces}{connection_types[key]}" )
      print ( "\n\n" )

