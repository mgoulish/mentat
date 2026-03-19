#!/usr/bin/env python3

from   datetime import datetime, timezone
import argparse
import cmd
import os
import pprint
import re
import sys

import debug
import new
import config
from CLI import MentatCLI



def get_dirs ( root ) :
  return [
    dir for dir in os.listdir ( root )
      if os.path.isdir ( os.path.join (root, dir) )
  ]



def read_router_log ( args, mentat, router, log_file_path, line_list, router_name_prefix ) :
  if router_name_prefix :
    router_name = router_name_prefix + ' ' + router['name']
  else :
    router_name = router['name']

  debug.info ( f"router: {router_name} file: {log_file_path}" )
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
  debug.info ( f"read {line_count} lines" )



def print_router_events ( mentat ) :
  print ( "\n\n\n" )
  for site in mentat['sites'] :
    print ( "========================================================" )
    print (   site['name']  )
    print ( "========================================================" )
    for router in site['routers'] :
      print (  "\n----------------------------------------" )
      print ( f"  router:  {router['name']}" )
  
      print ( "\n\nprevious events: " )
      for event in router['previous_events'] :
        pprint.pprint ( event )
  
      print ( "\n\ncurrent events: " )
      for event in router['current_events'] :
        pprint.pprint ( event )
  

  
def read_events ( args, mentat ) :
  site_names = get_dirs(mentat['root'])
  for site_name in site_names :
    site_root = f"{mentat['root']}/{site_name}"
    debug.info ( f"site_root == {site_root}" )

    site = config.get_site ( mentat, site_name )
    if site == None :
      print ( f"mentat error: read_events: Can't find site {site_name}" )
      sys.exit ( 1 )

    pods_path = f"{mentat['root']}/{site_name}/pods"
    pod_names = get_dirs(pods_path)
    for pod_name in pod_names :
      if pod_name.startswith('skupper-router') :
        debug.debug ( f"Making new router {pod_name}" )
        router = config.get_router ( mentat, site_name, pod_name )
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
              debug.debug ( f"reading previous events for router {router['name']}" )
              read_router_log ( args, mentat, router, file_name, router['previous_events'], 'previous' )  
            elif basename == 'router-logs.txt' :
              debug.debug ( f"reading latest events for router {router['name']} from file {file_name}" )
              read_router_log ( args, mentat, router, file_name, router['current_events'], None )  
              debug.debug ( f"read {len(router['current_events'])} current events" )
          #print ( "\n\nvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv" )
          #print ( f"router {pod_name} : {router}" )

  # Sort the unified list in chronological order
  debug.info ( "sorting events" )
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

def main ( ) :
  parser = argparse.ArgumentParser ( description="Mentat helps you investigate large Skupper log files" )
  parser.add_argument("--root", type=str, help="root dir for the network run. should contain site dirs")
  parser.add_argument("--info",  action="store_true", help="Print info messages")
  parser.add_argument("--debug", action="store_true", help="Print debug messages")
  parser.add_argument("--script", type=str, help="Print debug messages")

  args = parser.parse_args()

  debug.show_info  = args.info
  debug.show_debug = args.debug


  mentat = new.new_mentat ( args.root )

  config.read_network ( mentat )
  read_events ( args, mentat )
  debug.info ( f"mentat now has {len(mentat['events'])} total events" )

  cli = MentatCLI(mentat)

  if args.script :
    debug.info ( f"running script {args.script}" )
    try:
      with open(args.script, 'r') as f:
        for line in f:
          # Strip whitespace and skip empty lines or comments
          cmd_line = line.strip()
          if cmd_line and not cmd_line.startswith('#'):
          # pass each line to the command executer
            cli.onecmd ( cmd_line )
    except FileNotFoundError:
      print(f"Error: Script file '{args.script}' not found.")
      sys.exit(1)


  try:
    cli.cmdloop()
  except KeyboardInterrupt:
    print("\nInterrupted. Exiting...")
  except EOFError:
    print("\nGoodbye!")



if __name__ == '__main__':
  main()




