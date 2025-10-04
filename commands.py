#!/usr/bin/env python3

import sys
import os

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
  print ( "show filter!" )


  


# Don't forget to put new commands in here!
commands = [
    {'name': 'list',       
     'fn': filters.list_filtered_results,
    },
    {'name': 'count',
     'fn': count_command,
    },
    {'name': 'quit',       
     'fn': quit_command,
    },
    {'name': 'time_range', 
     'fn': time_range_command,
    },
    {'name': 'start',      
     'fn': filters.filter_start,
    },
    {'name': 'stop',       
     'fn': filters.filter_stop,
    },
    {'name': 'grep',
     'fn'  : filters.filter_grep,
    },
    {'name': 'show_filter',
     'fn'  : show_filter_command,
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


