#!/usr/bin/env python3

import sys
import os
import pprint
import re
from   datetime import datetime, timezone




# The result list is not a copy of all the filtered events.
# It is just their index numbers in the Mentat list of all events.
current_filter_chain = { 'name' : None, 
                         'filters' : [],
                         'result'  : [] }




# Pattern-Matching Elements ============================================
leading_whitespace    = r'^\s*'
whitespace            = r'\s*'
skip                  = r'.*?'
date                  = r'(\d{4}-\d{2}-\d{2})'
time                  = r'(\d{2}:\d{2}:\d{2})'
date_time             = date + whitespace + time




# Expected format: 2025-09-16 04:22:22.956513
def string_to_microseconds_since_epoch ( s ):
    #dt = datetime.strptime(s, "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=timezone.utc)
    dt = datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1_000_000)



def list_filtered_results ( mentat ) :
  if len(current_filter_chain['filters']) == 0 :
    for event in mentat['events'] :
      print ( '\n' )
      pprint.pprint ( event )
  else :
    for index in current_filter_chain['result'] :
      print ( '\n' )
      pprint.pprint ( mentat['events'][index] )



def count ( mentat ) :
  # TODO  make this handle case where there is a current results list
  if len(current_filter_chain['filters']) == 0 :
    event_count = 0
    for event in mentat['events'] :
      event_count += 1
  print ( f'\n {event_count} events' )



def start ( mentat, command_line ) :
  pattern = leading_whitespace + "start" + skip + date_time

  match = re.match ( pattern, command_line )
  if not match :
    print ( f"filters start error: could not match |{command_line}|" )
    sys.exit ( 0 )
  timestamp = f"{match.group(1)} {match.group(2)}" 
  micros = string_to_microseconds_since_epoch ( timestamp )
  new_filter = { 'name' : 'start', 'micros' : micros }
  current_filter_chain['filters'].append ( new_filter )
  run_current_filter ( mentat, new_filter )



def stop ( mentat, command_line ) :
  pattern = leading_whitespace + "stop" + skip + date_time

  match = re.match ( pattern, command_line )
  if not match :
    print ( f"filters stop error: could not match |{command_line}|" )
    sys.exit ( 0 )
  timestamp = f"{match.group(1)} {match.group(2)}" 
  micros = string_to_microseconds_since_epoch ( timestamp )
  new_filter = { 'name' : 'stop', 'micros' : micros }
  current_filter_chain['filters'].append ( new_filter )
  run_current_filter ( mentat, new_filter )



# This runs only the latest filter defined by the user.
# Previous ones in the current chain have already been run
# and the cumulative result is already in the current result list.

def run_current_filter ( mentat, new_filter ) :
  # If we have no current result list, that means we 
  # have not run any filters yet.
  # In that case, the current result is the entire 
  # list of Mentat events in this data set.
  current_result_list = current_filter_chain['result']
  if len(current_result_list) == 0 :
    current_result_list = list(range(len(mentat['events'])))
  
  new_result_list = []

  match new_filter['name'] :
    case 'start' :
      print ( "running filter 'start'" )
      start_micros = new_filter['micros']
      for i in current_result_list :   
        event = mentat['events'][i]
        if event['micros'] >= start_micros :
          new_result_list.append(i)        
      print ( f"after start filter: {len(new_result_list)} events" )

    case 'stop' :
      print ( "running filter 'stop'" )
      stop_micros = new_filter['micros']
      for i in current_result_list :    
        event = mentat['events'][i]
        if event['micros'] < stop_micros :
          new_result_list.append(i)        
      print ( f"after stop filter: {len(new_result_list)} events" )

    case _ :
      print (f"unknown filter name: {new_filter['name']}")
      sys.exit(0)

  # The results we just got from this filter 
  # become the new current results list.
  current_filter_chain['result'] = new_result_list




  



