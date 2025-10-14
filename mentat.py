#!/usr/bin/env python3

import sys
import os
import re
from   datetime import datetime, timezone
import pprint

import new
import commands
import config



def get_dirs ( root ) :
  return [
    dir for dir in os.listdir ( root )
      if os.path.isdir ( os.path.join (root, dir) )
  ]



def read_router_log ( mentat, router, log_file_path, line_list, router_name_prefix ) :
  if router_name_prefix :
    router_name = router_name_prefix + ' ' + router['name']
  else :
    router_name = router['name']

  print ( f"mentat info: read_router_log: router: {router_name} file: {log_file_path}" )
  timestamp_regex = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{6})'
  line_count = 0
  with open(log_file_path) as f:
    content = f.readlines()
    for line_str in content :
      line_str = line_str.rstrip()
      match = re.match ( timestamp_regex, line_str )
      if match :
        line_count += 1
        line = new.new_event ( 'log_line', match.group(1) )
        line['line']        = line_str
        line['file_path']   = log_file_path
        line['line_number'] = line_count
        line['router']      = router_name
        line['site']        = router['site']
        line_list.append ( line )
        # Also append this line to the grand top-level list
        mentat['events'].append ( line )
  print ( f"mentat info: read_router_log: read {line_count} lines" )



def print_router_events ( mentat ) :
  print ( "\n\n\n" )
  for site in mentat['sites'] :
    print ( "========================================================" )
    print (   site['name']  )
    print ( "========================================================" )
    for router in site['routers'] :
      print ( f"  router:  {router['name']}" )
  
      print ( "\n\nprevious events: " )
      for event in router['previous_events'] :
        pprint.pprint ( event )
  
      print ( "\n\ncurrent events: " )
      for event in router['current_events'] :
        pprint.pprint ( event )
  

  
def read_events ( mentat ) :
  site_names = get_dirs(mentat['root'])
  for site_name in site_names :
    site_root = f"{mentat['root']}/{site_name}"
    print ( f"site_root == {site_root}" )
    site = new.new_site ( site_name, site_root )
    mentat['sites'].append(site)
    pods_path = f"{root}/{site_name}/pods"
    pod_names = get_dirs(pods_path)
    for pod_name in pod_names :
      if pod_name.startswith('skupper-router') :
        router = new.new_router ( pod_name, site_name )
        site['routers'].append ( router )
        logs_path = f"{pods_path}/{pod_name}/logs"
        file_names = os.listdir(logs_path)
        for basename in file_names :
          if basename.startswith ( 'router-logs' ) :
            file_name = f"{logs_path}/{basename}"
            # There may be two files that both start with 
            # this prefix:
            #   router-logs-previous.txt, and
            #   router-logs.txt
            # We want both.
            # It doesn't matter in which order we read them,
            # since the events will all eventually be sorted
            # into chronological order.
            if basename == 'router-logs-previous.txt' :
              print ( f"mentat info: main: reading previous events for router {router['name']}" )
              read_router_log ( mentat, router, file_name, router['previous_events'], 'previous' )  
            elif basename == 'router-logs.txt' :
              print ( f"mentat info: main: reading latest events for router {router['name']}" )
              read_router_log ( mentat, router, file_name, router['current_events'], None )  

  # Sort the unified list in chronological order
  print ( f"mentat info: sorting events" )
  sorted_events = sorted(mentat['events'], key=lambda x: x['micros'])
  mentat['events'] = sorted_events

  # And assign IDs to them all
  id = 1
  for event in mentat['events'] :
    event['id'] = id
    id += 1
  

    
#================================================================
#  Main
#================================================================
root   =  sys.argv[1]
mentat = new.new_mentat ( root )

config.read_network ( mentat )
read_events ( mentat )
print ( f"mentat now has {len(mentat['events'])} total events" )
#print_router_events ( mentat )

commands.accept_commands ( mentat )

