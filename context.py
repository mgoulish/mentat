#!/usr/bin/env python3

import new

def add ( mentat, command, arg, result ) :
  e = new.new_context_event ( command, arg, result )
  print ( f"Here is the event to be added: {e}" )
