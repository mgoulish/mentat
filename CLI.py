#!/usr/bin/env python3

import cmd
import copy
from   datetime import datetime, timedelta
#import datetime
import os
from   pathlib import Path
import pprint
import sys
from   typing import Dict, Any



import debug
import context
import new



class MentatCLI(cmd.Cmd):
  def __init__(self, mentat_dict: Dict[str, Any]):
    super().__init__()
    self.mentat = mentat_dict
    self.prompt = '(mentat) '
    self.intro = 'Mentat CLI started. Type help for commands.'
    self.mentat['cli'] = self



  def do_echo ( self, args ) :
    print ( args )
    

  def do_errors ( self, arg ) :
    mentat = self.mentat
    timestamps = []
    for event in mentat['events'] :
      if 'error' in event['line'].lower() :
        timestamps.append ( (event['timestamp'], event) )
    clumps = find_clumps ( timestamps )
    print ( f"\nThere are {len(clumps)} error clumps\n" )
    clump_count = 1
    for clump in clumps :
      print ( f"  Clump {clump_count} has {len(clump)} errors" )
      start_str = clump[0][0]
      end_str   = clump[-1][0]
      duration = calculate_duration ( start_str, end_str )
      #print ( f"duration: {duration}" )
      #print ( f"start {start_str}  end {end_str}" )
      #formatted_duration = format_duration ( duration )
      formatted_duration = humanize_duration ( duration )
      print ( f"    duration: {formatted_duration}" )
      print ( f"    from  {start_str}  to  {end_str}\n" )
      clump_count += 1
    #context.add ( mentat, "errors", arg, result )
    print ( " " )



  def do_overview ( self, arg ) :
    '''Show an overview of the current data set'''
    mentat = self.mentat
    print ( "\n----------------------------" )
    print ( "Data Overview" )
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
        print ( f"  router: {router['nickname']} ({router['name']}) " )
        n_current_events  = len(router['current_events'])
        n_previous_events = len(router['previous_events'])
        debug.debug ( f"current events: {n_current_events}  previous events: {n_previous_events}" )
        #if n_previous_events > 0 :
          #start =  router['previous_events'] [0]['timestamp']
          #stop  =  router['previous_events'][-1]['timestamp']
          #print ( f"    {n_previous_events} events from {start.split('.')[0]} to {stop.split('.')[0]} " )
        #
        #if n_current_events > 0 :
          #start =  router['current_events'] [0]['timestamp']
          #stop  =  router['current_events'][-1]['timestamp']
          #print ( f"    {n_current_events} events from {start.split('.')[0]} to {stop.split('.')[0]} " )
    print ( "End Overview ----------------------------" )
    print ( " " )
  
  

  def do_events ( self, arg ) :
    mentat = self.mentat
    print ( "\n----------------------------" )
    print ( "Events" )
    print ( "----------------------------" )

    n_events = len(mentat['events'])
    print ( f"\nThere are {n_events} events." )
    print ( f"Starting at {mentat['events'] [0]['timestamp'].split('.')[0]}" )
    print ( f"Ending   at {mentat['events'][-1]['timestamp'].split('.')[0]}" )
    print ( " " )
  
    for site in mentat['sites'] :
      print ( f"site: {site['name']}" )
      for router in site['routers'] :
        print ( f"  router: {router['nickname']} ({router['name']}) " )
        n_previous_events = len(router['previous_events'])
        n_current_events  = len(router['current_events'])
        print ( f"    previous events: {n_previous_events}" )
        print ( f"    current events:  {n_current_events}" )
        if n_previous_events > 0 :
          for event in router['previous_events'] :
            pprint.pprint ( event )
    print ( " " )
  


  def do_q ( self, arg ) :
    self.do_quit ( arg )



  def do_quit ( self, arg ) :
    """exit the program"""
    mentat = self.mentat
    print ( "quitting..." )
    sys.exit ( 0 )

  

  # Abbreviation
  def do_so ( self, arg ) :
    self.do_source ( arg )



  def do_source ( self, arg ) :
    '''Source a file of commands'''
    file_path = arg

    if not Path(file_path).is_file() :
      print ( f"Can't find file {file_path}" )
      return

    with open(file_path, 'r') as file:
      for line in file:
        self.onecmd ( line.strip() )



  def do_sites ( self, arg ) :
    mentat = self.mentat
    print(' ')
    print ( f"in do_sites: there are now {len(mentat['sites'])} sites" )
    for site in mentat['sites'] :
      print ( '\nsite :', site['name'], '\n' )

      print ( "  routers :" )
      for router in site['routers'] :
        print ( f"    {router['nickname']} ({router['name']})" )
      print(' ')

      print ( "  listeners :" )
      for listener in site['listeners'] :
        print ( '    ', listener['name'] )
      print(' ')

      print ( "  connectors :" )
      for connector in site['connectors'] :
        print ( '    ', connector['name'] )
      print(' ')

    print(' ')



  # This just shows the user the start and stop times 
  # for the current data set.
  def do_range ( self, arg ) :
    '''Show start amd stop times for entire data set'''
    mentat = self.mentat
    n_events        = len(mentat['events'])
    first_timestamp = mentat['events'][0]['timestamp']
    last_timestamp  = mentat['events'][n_events - 1]['timestamp']
    print ( f"  {first_timestamp} to {last_timestamp}" )



  def do_wait ( self, arg ) :
    print ( "Hit 'enter' to continue..." )
    input ( )


  def default(self, line):
    """Called for unknown commands."""
    print(f"Unknown command: '{line}'. Try 'help' for available commands.")


#=======================================================
# Helper Functons
#=======================================================


def find_clumps(data, max_gap_seconds=60):
    """
    Groups a list of tuples (where the first element is a timestamp string) into clumps based on time proximity.

    Args:
    data (list[tuple]): List of tuples, with first element as timestamp string in '%Y-%m-%d %H:%M:%S.%f' format.
    max_gap_seconds (int): Maximum gap in seconds between timestamps in the same clump.

    Returns:
    list[list[tuple]]: List of lists, each sublist being a clump of the original tuples.
    """
    if not data:
        return []

    # Parse timestamps from tuples and sort by datetime, keeping original tuples
    pairs = sorted(
        [(datetime.strptime(item[0], '%Y-%m-%d %H:%M:%S.%f'), item) for item in data],
        key=lambda x: x[0]
    )

    clumps = []
    current_clump = [pairs[0][1]]  # Start with the first tuple

    for i in range(1, len(pairs)):
        delta = pairs[i][0] - pairs[i-1][0]
        if delta > timedelta(seconds=max_gap_seconds):
            clumps.append(current_clump)
            current_clump = [pairs[i][1]]
        else:
            current_clump.append(pairs[i][1])

    clumps.append(current_clump)  # Add the last clump
    return clumps


def calculate_duration(start_str, end_str):
    """
    Calculate the duration between two timestamp strings.
    
    Args:
    start_str (str): The starting timestamp in the format 'YYYY-MM-DD HH:MM:SS.mmmmmm'.
    end_str (str): The ending timestamp in the format 'YYYY-MM-DD HH:MM:SS.mmmmmm'.
    
    Returns:
    datetime.timedelta: The absolute duration between the two timestamps.
    """
    # Define the format
    fmt = '%Y-%m-%d %H:%M:%S.%f'
    
    # Parse the strings into datetime objects
    start_dt = datetime.strptime(start_str, fmt)
    end_dt   = datetime.strptime(end_str, fmt)
    
    # Calculate the absolute difference
    duration = abs(end_dt - start_dt)
    
    return duration




def humanize_duration(duration: timedelta) -> str:
    """
    Convert a datetime.timedelta object to a human-readable string.

    Args:
    duration (datetime.timedelta): The duration object to convert.

    Returns:
    str: A string like "3 hours, 5 minutes, and 12 seconds".
    """
    if duration.total_seconds() < 0:
        raise ValueError("Duration must be positive")

    # Round seconds based on microseconds
    total_seconds = int(duration.total_seconds())
    micros = duration.microseconds
    if micros >= 500000:
        total_seconds += 1

    # Break down into components
    days = total_seconds // 86400
    seconds = total_seconds % 86400
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60

    # Collect non-zero parts
    parts = []
    if days:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if seconds or not parts:  # Include seconds if non-zero or if all else zero
        parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")

    # Join parts with commas and 'and'
    if not parts:
        return "0 seconds"
    elif len(parts) == 1:
        return parts[0]
    else:
        return ", ".join(parts[:-1]) + ", and " + parts[-1]


def format_duration ( duration ) :
  seconds = duration.total_seconds()
  print ( f"in format_duration: dur: {duration}  total_seconds == {seconds}" )
  days    = 0
  hours   = 0
  minutes = 0
  seconds = 0

  result_str = ""
  print ( f"result_str {result_str}" )

  if seconds >= 86400 :
    days = seconds // 86400  
    seconds %= 86400
    result_str += f"{days} days"
    print ( f"result_str {result_str}" )
  
  if seconds >= 3600 :
    hours = seconds // 3600
    seconds %= 3600
    result_str += f" {hours} hours"
    print ( f"result_str {result_str}" )

  if seconds >= 60 :
    minutes = seconds // 60
    seconds %= 60
    result_str += f" {minutes} minutes"
    print ( f"result_str {result_str}" )
  
  seconds = round(seconds)
  if seconds > 0 :
    result_str += f" {seconds} seconds "
    print ( f"result_str {result_str}" )

  return result_str


