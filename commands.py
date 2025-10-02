#!/usr/bin/env python3

import sys
import os



# Commands cannot be run until after the events 
# have all been loaded and sorted.
def time_range_command ( mentat ) :
  n_events        = len(mentat['events'])
  first_timestamp = mentat['events'][0]['timestamp']
  last_timestamp  = mentat['events'][n_events - 1]['timestamp']
  print ( f"  {first_timestamp} to {last_timestamp}" )


  
def list_command():
  print("Executing 'list' command")

def load_command():
  print("Executing 'load' command")

def save_command():
  print("Executing 'save' command")

def quit_command ( mentat ) :
  print ( "quitting..." )
  sys.exit ( 0 )
  


# Don't forget to put new commands in here!
commands = [
    {'name': 'list',       'func': list_command},
    {'name': 'load',       'func': load_command},
    {'name': 'save',       'func': save_command},
    {'name': 'quit',       'func': quit_command},
    {'name': 'time_range', 'func': time_range_command},
]


def resolve_and_execute ( prefix, commands, mentat ) :
    matches = [cmd for cmd in commands if cmd['name'].startswith(prefix)]

    if len(matches) == 0:
        print(f"No command starts with '{prefix}'")
    elif len(matches) == 1:
        matches[0]['func'] ( mentat )  # Execute the function
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
    resolve_and_execute ( command_name, commands, mentat )


