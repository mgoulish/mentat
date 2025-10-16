#!/usr/bin/env python3

import sys
import os
import pprint
import copy
import cmd
from typing import Dict, Any


import filters
import new


class MentatCLI(cmd.Cmd):
  def __init__(self, mentat_dict: Dict[str, Any]):
    super().__init__()
    self.mentat = mentat_dict
    self.prompt = '(mentat) '
    self.intro = 'Mentat CLI started. Type help for commands.'
    self.mentat['cli'] = self


  def do_quit ( self, arg ) :
    """exit the program"""
    mentat = self.mentat
    print ( "quitting..." )
    sys.exit ( 0 )

  # This just shows the user the start and stop times 
  # for the current data set.
  def do_time_range ( self, arg ) :
    '''Show start amd stop times for entire data set'''
    mentat = self.mentat
    n_events        = len(mentat['events'])
    first_timestamp = mentat['events'][0]['timestamp']
    last_timestamp  = mentat['events'][n_events - 1]['timestamp']
    print ( f"  {first_timestamp} to {last_timestamp}" )

  

  def do_count ( self, arg ) :
    '''Count events in current filter chain'''
    mentat = self.mentat
    print ( f"There are {len(filters.current_filter_chain['results'])} filtered events out of {len(mentat['events'])} total.")



  def do_replace ( self, arg ) :
    '''Replace a filter in your current filter chain'''
    mentat = self.mentat
    command_line = arg
    if len(filters.current_filter_chain['filters']) == 0 :
      print ( "\nThere are no filters in the current filter chain." )
      return
  
    print ( f"command line: |{command_line}|" )
    words = command_line.split()
    if len(words) < 2 :
      print ( "\nGive me an integer argument" )
      return
    s = words[1]
    n = 0
    try:
      int(s)
      n = int(s)
    except ValueError:
      print ( f"    {s} is not an integer" )
      return
    
    if n > len(filters.current_filter_chain['filters']) - 1 :
      print ( f"There are {len(filters.current_filter_chain['filters'])} filters in the current filter chain." )
      return
    
    filters.replacing_filter = n
    print ( f"Replacing filter {n} please enter a filter command" )
    print ( f"replace_command: it will replace filter {n}." )



  def do_show_filter ( self, arg ) :
    '''Show your current filter chain'''
    mentat = self.mentat
    if len(filters.current_filter_chain['filters']) == 0 :
      print ( '\nThere is no current filter chain.\n' )
      return
  
    print ( f"\nCurrent Filter Chain", end='' )
    if filters.current_filter_chain['name'] == None :
      print ( ': (no name yet)' )
    else :
      print ( f": {filters.current_filter_chain['name']}" )
    
    count = 0
    for f in filters.current_filter_chain['filters'] :
      print ( f"Filter {count}: {f['name']}", end='' )
      for arg in f['args'] :
        print ( f" {arg} ", end='' )
      print (' ')
      count += 1
    print ( ' ' )



  def do_save ( self, arg ) :
    '''Name and save the current filter chain'''
    mentat = self.mentat
    command_line = arg
    if len(filters.current_filter_chain['filters']) == 0 :
      print ( "\nThere is no current filter chain to save." )
      return
    words = command_line.split()
    if len(words) != 2 :
      print ( "\n    Usage: save NAME" )
      return
    filter_chain_name = words[1]
    print ( f"filter_chain_name: {filter_chain_name}" )
    filters.current_filter_chain['name'] = filter_chain_name
    filters.filter_chains.append(copy.deepcopy(filters.current_filter_chain))
    filters.current_filter_chain = new.new_filter_chain()
  
    print ( "\nSaved Filter Chains:" )
    for saved_filter in filters.filter_chains :
      print ( f"    {saved_filter['name']}" )
    print ( " " )
  
  
  
  def do_restore ( self, arg ) :
    '''Restore a saved filter chain to be current'''
    mentat = self.mentat
    command_line = arg
    words = command_line.split()
    if len(words) != 2 :
      print ( "\n    Usage: restore NAME" )
      return
    filter_chain_name = words[1]
    for fc in filters.filter_chains : 
      if filter_chain_name == fc['name'] :
        filters.current_filter_chain = copy.deepcopy(fc)
        print ( f"\nrestored filter chain '{fc['name']}'" )
        return
    print ( f"can't find filter chain '{fc['name']}'" )



  def do_overview ( self, arg ) :
    '''Show an overview of the current data set'''
    mentat = self.mentat
    print ( "\nData Overview" )
    print ( "----------------------------" )

    n_events = len(mentat['events'])
    print ( f"\nThere are {n_events} events." )
    print ( f"Starting at {mentat['events'] [0]['timestamp'].split('.')[0]}" )
    print ( f"Ending   at {mentat['events'][-1]['timestamp'].split('.')[0]}" )
    print ( " " )
  
    error_count = 0
    for event in mentat['events'] :
      if 'error' in event['line'].lower() :
        error_count += 1
    print ( f"There are {error_count} errors." )
    print ( " " )
  
    for site in mentat['sites'] :
      print ( f"site: {site['name']}" )
      for router in site['routers'] :
        print ( f"  router: {router['name']}" )
        n_current_events  = len(router['current_events'])
        n_previous_events = len(router['previous_events'])
        if n_previous_events > 0 :
          start =  router['previous_events'] [0]['timestamp']
          stop  =  router['previous_events'][-1]['timestamp']
          print ( f"    {n_previous_events} events from {start.split('.')[0]} to {stop.split('.')[0]} " )
  
        start =  router['current_events'] [0]['timestamp']
        stop  =  router['current_events'][-1]['timestamp']
        print ( f"    {n_current_events} events from {start.split('.')[0]} to {stop.split('.')[0]} " )
    print ( " " )
  
  
  
  def do_undo ( self, arg ) :
    '''Remove the last filter that you added to your filter chain'''
    mentat = self.mentat
    command_line = arg
    if len(filters.current_filter_chain['filters']) == 0 :
     print ( "\nundo: The filter chain is empty.\n" )
     return
  
    print ( f"\nundoing latest filter: {filters.current_filter_chain['filters'][-1]['name']}" )
  
    name = filters.current_filter_chain['filters'][-1]['name']
    filters.current_filter_chain['filters'].pop()
    print ( f"There are now {len(filters.current_filter_chain['filters'])} filters in the current chain." )
  
    # Now we must re-run the resultant current filter chain,
    # because its results are now out of date.
    filters.current_filter_chain['results'] = []
    for f in filters.current_filter_chain['filters'] :
      filters.run_filter ( mentat, f )
    
    print(f"undo: The current filter chain now has {len(filters.current_filter_chain['results'])} results.\n")
  


  def do_list ( self, arg ) :    
    '''List the filtered results of your current filter chain'''
    mentat = self.mentat
    command_line = arg
    filters.list_filtered_results ( mentat )



  def do_start ( self, arg ) :
    '''Filter out all log events that happened before this time'''
    filters.start ( self.mentat, arg )



  def do_stop ( self, arg ) :
    '''Filter out all log events that happened after this time'''
    filters.stop ( self.mentat, arg )



  def do_grep ( self, arg ) :
    '''Filter log events for the given keyword'''
    filters.grep ( self.mentat, arg )



