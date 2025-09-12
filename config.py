#!/usr/bin/env python3

import yaml
import os
import json
import pprint



def new_network ( root ) :
  keys = [ 'root',
           'sites' ]
  network = dict.fromkeys ( keys, None )         
  network [ 'root' ]  = root
  network [ 'sites' ] = []
  return network



def new_site ( root ) :
  keys = [ 'name',
           'ingress-host',
           'root',
           'routers',
           'listeners',
           'connectors' ]
  site = dict.fromkeys ( keys, None )         
  site [ 'root' ]       = root
  site [ 'routers' ]    = []
  site [ 'listeners' ]  = []
  site [ 'connectors' ] = []
  return site



def new_listener ( ) :
  keys     = [ 'name', 'port', 'role' ]
  listener = dict.fromkeys ( keys, None )
  listener['role'] = 'normal'   # Assume this is the default
  return listener



def new_connector ( ) :  
  keys     = [ 'host', 'name', 'port', 'role' ]
  connector = dict.fromkeys ( keys, None )
  connector['role'] = 'normal'   # Assume this is the default
  return connector



def read_skupper_site_yaml ( site, file_name ) :
  with open (file_name, 'r') as file:
    yaml_data = yaml.safe_load ( file )
    yaml_data_data = yaml_data['data']

    #if 'name' in yaml_data_data :
      #site['name'] = yaml_data_data['name']
    #else :
      #print ( "read_site error: name not found" )
    
    if 'ingress-host' in yaml_data_data:
      site['ingress-host'] = yaml_data_data['ingress-host']
    else :
      print ( "read_site error: ingress-host not found" )
      


def read_skupper_internal_yaml ( site, file_name ) :
  print ( f"reading file {file_name}" )
  with open (file_name, 'r') as file:
    yaml_data = yaml.safe_load ( file )
    yaml_data_data = yaml_data['data']
    for key in yaml_data_data :
      router_json_str  = yaml_data_data['skrouterd.json']
      router_json_data = json.loads(router_json_str)
      for i in range(len(router_json_data)) :
        # Each element of this list is itself a list with 2 places:
        # the name of the item, and a dictionary with all its data. 
        match router_json_data[i][0] :
          case 'listener' :
            listener = new_listener()
            listener_data = router_json_data[i][1]
            listener.update ( { k: listener_data[k] for k in ['name', 'port', 'role'] if k in listener_data } )
            site['listeners'].append(listener)
            #print ( f"listener: {listener}" )
          case 'connector' :
            connector = new_connector()
            connector_data = router_json_data[i][1]
            connector.update ( { k: connector_data[k] for k in ['host', 'name', 'port', 'role'] if k in connector_data } )
            site['connectors'].append(connector)
            #print ( f"connector: {connector}" )

          #case _:
            #print ( f"something else {router_json_data[i]}" )



def read_site ( network, dir_name ) :
  site = new_site ( dir_name )
  site['name'] = dir_name.split('/')[-1]
  print ( f"\nread_site at {dir_name}" )
  config_dir = dir_name + '/configmaps'

  # skupper-site.yaml ----------------------------------------
  file_name = config_dir + '/skupper-site.yaml'
  read_skupper_site_yaml ( site, file_name )

  # skupper-internal.yaml ----------------------------------------
  file_name = config_dir + '/skupper-internal.yaml'
  read_skupper_internal_yaml ( site, file_name )

  print ( "read_site: " )
  pprint.pprint ( site )

  network['sites'].append(site)

      



def read_network ( network ) :
  root = network['root']
  print ( f"Reading config at root {root}" )
  for dir in os.listdir ( root ) :
    site_path = os.path.join (root, dir)
    if os.path.isdir ( site_path ) :
      read_site ( network, site_path )



