

def new_connection ( ) :
  keys = [ 'from',
           'to', 
           'start',
           'end',
           'duration',
           'type',   # i.e. client, router, DB
           'disconnect_reason' ]
  connection = dict.from_keys ( keys, None )
  return connection



def make_connections ( sites ) :
  for site in sites :
    print ( f"\nmake_connections for site {site['name']} --------------------------" )
