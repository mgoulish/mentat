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
def time_range_command ( mentat ) :
  n_events        = len(mentat['events'])
  first_timestamp = mentat['events'][0]['timestamp']
  last_timestamp  = mentat['events'][n_events - 1]['timestamp']
  print ( f"  {first_timestamp} to {last_timestamp}" )


  
def quit_command ( mentat ) :
  print ( "quitting..." )
  sys.exit ( 0 )
  


# Don't forget to put new commands in here!
commands = [
    {'name': 'list',       'fn': filters.list_filtered_results },
    {'name': 'count',      'fn': filters.count },
    {'name': 'quit',       'fn': quit_command },
    {'name': 'time_range', 'fn': time_range_command },
    {'name': 'start',      'fn': filters.start },
    {'name': 'stop',       'fn': filters.stop },
]



def resolve_command ( prefix, command_line, commands, mentat ) :
    matches = [cmd for cmd in commands if cmd['name'].startswith(prefix)]

    if len(matches) == 0:
        print(f"No command starts with '{prefix}'")
    elif len(matches) == 1:
        if matches[0]['name'] == 'start' or matches[0]['name'] == 'stop' :
          matches[0]['fn'] ( mentat, command_line )
        else:
          matches[0]['fn'] ( mentat )  # Execute the function
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


