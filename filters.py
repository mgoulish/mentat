#!/usr/bin/env python3

import sys
import os
import pprint
import re
from   datetime import datetime, timezone

import new



filter_chains = []
current_filter_chain = new.new_filter_chain()


replacing_filter = -1


# Pattern-Matching Elements ============================================
leading_whitespace    = r'^\s*'
whitespace            = r'\s*'
skip                  = r'.*?'
date                  = r'(\d{4}-\d{2}-\d{2})'
time                  = r'(\d{2}:\d{2}:\d{2})'
date_time             = date + whitespace + time



#def new_filter ( name ) :
  #keys = [ 'name',
           #'args' ]
  #data_filter = dict.fromkeys ( keys, None )
  #data_filter['name'] = name
  #data_filter['args'] = []
  #return data_filter



# Expected format: 2025-09-16 04:22:22.956513
def string_to_microseconds_since_epoch ( s ):
    #dt = datetime.strptime(s, "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=timezone.utc)
    dt = datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1_000_000)



def list_filtered_results ( mentat, _ ) :
  if len(current_filter_chain['filters']) == 0 :
    for event in mentat['events'] :
      print ( '\n' )
      pprint.pprint ( event )
  else :
    for index in current_filter_chain['results'] :
      print ( '\n' )
      pprint.pprint ( mentat['events'][index] )



def start ( mentat, command_line ) :
  pattern = leading_whitespace + "start" + skip + date_time

  match = re.match ( pattern, command_line )
  if not match :
    print ( f"filters start error: could not match |{command_line}|" )
    return
  timestamp = f"{match.group(1)} {match.group(2)}" 
  start_filter = new.new_filter ( 'start' )
  start_filter['args'].append ( timestamp )

  if replacing_filter == -1 :   # We are not replacing a filter
    current_filter_chain['filters'].append ( start_filter )
    run_filter ( mentat, start_filter )
  else :
    current_filter_chain['filters'][replacing_filter] = start_filter
    current_filter_chain['results'] = []
    for f in current_filter_chain['filters'] :
      run_filter ( mentat, f )
      


def stop ( mentat, command_line ) :
  pattern = leading_whitespace + "stop" + skip + date_time

  match = re.match ( pattern, command_line )
  if not match :
    print ( f"filters stop error: could not match |{command_line}|" )
    return
  timestamp = f"{match.group(1)} {match.group(2)}" 
  stop_filter = new.new_filter ( 'stop' )
  stop_filter['args'].append(timestamp)

  if replacing_filter == -1 :   # We are not replacing a filter
    current_filter_chain['filters'].append ( stop_filter )
    run_filter ( mentat, stop_filter )
  else :
    current_filter_chain['filters'][replacing_filter] = stop_filter
    current_filter_chain['results'] = []
    for f in current_filter_chain['filters'] :
      run_filter ( mentat, f )



def grep ( mentat, command_line ) :
  words = command_line.split()
  if len(words) < 2 :
    print ( "put a word on the commad line to grep for" )
    return
  search_word = words[1]
  grep_filter = new.new_filter ( 'grep' )
  grep_filter['args'].append(search_word)

  if replacing_filter == -1 :   # We are not replacing a filter
    current_filter_chain['filters'].append ( grep_filter )
    run_filter ( mentat, grep_filter )
  else :
    current_filter_chain['filters'][replacing_filter] = grep_filter
    current_filter_chain['results'] = []
    for f in current_filter_chain['filters'] :
      run_filter ( mentat, f )



# This runs only the latest filter defined by the user.
# Previous ones in the current chain have already been run
# and the cumulative result is already in the current result list.
def run_filter ( mentat, f ) :
  # If we have no current result list, that means we 
  # have not run any filters yet.
  # In that case, the current result is the entire 
  # list of Mentat events in this data set.
  current_result_list = current_filter_chain['results']
  if len(current_result_list) == 0 :
    current_result_list = list(range(len(mentat['events'])))
  
  new_result_list = []

  match f['name'] :
    case 'start' :
      print ( "running filter 'start'" )
      start_micros = string_to_microseconds_since_epoch(f['args'][0])
      for i in current_result_list :   
        event = mentat['events'][i]
        if event['micros'] >= start_micros :
          new_result_list.append(i)        
      print ( f"after start filter: {len(new_result_list)} events" )

    case 'stop' :
      print ( "running filter 'stop'" )
      stop_micros = string_to_microseconds_since_epoch(f['args'][0])
      for i in current_result_list :    
        event = mentat['events'][i]
        if event['micros'] < stop_micros :
          new_result_list.append(i)        
      print ( f"after stop filter: {len(new_result_list)} events" )

    case 'grep' :
      print ( "running filter 'grep'" )
      search_word = f['args'][0]
      print (f"case grep search word {search_word}")
      for i in current_result_list :
        event = mentat['events'][i]
        line = event['line']
        if search_word.lower() in line.lower() :
          new_result_list.append(i)        
      print ( f"after grep filter: {len(new_result_list)} events" )

    case _ :
      print (f"unknown filter name: {f['name']}")
      sys.exit(0)

  # The results we just got from this filter 
  # become the new current results list.
  current_filter_chain['results'] = new_result_list



