#!/usr/bin/env python3

import sys
import os
import pprint

import filters



#-------------------------------------------------
# Commands cannot be run until after the events 
# have all been loaded and sorted.
#-------------------------------------------------


# This just shows the user the start and stop times 
# for the current data set.
def time_range_command ( mentat, _ ) :
  n_events        = len(mentat['events'])
  first_timestamp = mentat['events'][0]['timestamp']
  last_timestamp  = mentat['events'][n_events - 1]['timestamp']
  print ( f"  {first_timestamp} to {last_timestamp}" )


  
def quit_command ( mentat, _ ) :
  print ( "quitting..." )
  sys.exit ( 0 )


def count_command ( mentat, _ ) :
  # TODO  make this handle case where there is a current results list
  if len(filters.current_filter_chain['filters']) == 0 :
    event_count = 0
    for event in mentat['events'] :
      event_count += 1
  print ( f'\n {event_count} events' )


def show_filter_command ( mentat, _ ) :
  if len(filters.current_filter_chain['filters']) == 0 :
    print ( '\nThere is no current filter chain.\n' )
    return

  print ( f"\nCurrent Filter Chain", end='' )
  if filters.current_filter_chain['name'] == None :
    print ( ': (no name yet)' )
  else :
    print ( f": {filters.current_filter_chain['name']}" )
  
  count = 0
  for mfilter in filters.current_filter_chain['filters'] :
    print ( f"Filter {count}: {mfilter['name']}", end='' )
    for arg in mfilter['args'] :
      print ( f" {arg} ", end='' )
    print (' ')
    count += 1
  print ( ' ' )



def show_help ( mentat, _ ) :
  for command in commands :
    print ( f"{command['name']} {command['args']}")
    print ( f"    {command['description']}" )
  print ( '\n' )
  print ( "It is not necessary to type the entire command name." )
  print ( "Just enough characters to disambiguate." )
  print ( "Entering an ambiguous prefix displays all matching commands." )
  print ( '\n' )
  

  
# Don't forget to put new commands in here!
commands = [
    {'name': 'count',
     'fn': count_command,
     'args' : ' ',
     'description' : 'show count of results of current filter chain',
    },
    {'name': 'grep',
     'fn'  : filters.grep,
     'args' : 'string',
     'description' : 'match lines that contain string',
    },
    {'name': 'help',       
     'fn':    show_help,
     'args' :  ' ',
     'description' : 'show all commands and their args',
    },
    {'name': 'list',       
     'fn': filters.list_filtered_results,
     'args' :  ' ',
     'description' : 'show results of current filter chain',
    },
    {'name': 'quit',       
     'fn': quit_command,
     'args' : ' ',
     'description' : 'exit program'
    },
    {'name': 'show_filter_chain',
     'fn'  : show_filter_command,
     'args' : ' ',
     'description' : 'show each filter in the current filter chain',
    },
    {'name': 'start',      
     'fn': filters.start,
     'args' : 'YYYY-MM-DD HH:MM:SS',
     'description' : 'Set the start of the visible time window.',
    },
    {'name': 'stop',       
     'fn': filters.stop,
     'args' : 'YYYY-MM-DD HH:MM:SS',
     'description' : 'Set the end of the visible time window.',
    },
    {'name': 'time_range', 
     'fn': time_range_command,
     'args' : ' ',
     'description' : 'show start and end of entire data set (unfiltered)',
    },
]



def resolve_command ( prefix, command_line, commands, mentat ) :
  matches = [cmd for cmd in commands if cmd['name'].startswith(prefix)]

  if len(matches) == 0:
    print(f"No command starts with '{prefix}'")
  elif len(matches) == 1:
    matches[0]['fn'] ( mentat, command_line )
  else:
    print(f"Multiple commands match '{prefix}':")
    for cmd in matches:
      print(f"- {cmd['name']}")



def accept_commands ( mentat ) :
  print ( "\n\n\n" )
  while True:
    command_line  = input("command: ")
    command_words = command_line.split()
  
    if len(command_words) == 0 :
      continue
  
    command_name = command_words[0]
    resolve_command ( command_name, command_line, commands, mentat )


