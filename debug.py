
import inspect

show_info = False

def info ( s ) :
  if show_info :
    caller = inspect.stack()[1].function
    print ( f"mentat info: {caller}: {s}" )

