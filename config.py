#!/usr/bin/env python3

import yaml
import os



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
           'routers' ]
  site = dict.fromkeys ( keys, None )         
  site [ 'root' ]    = root
  site [ 'routers' ] = []
  return site



def read_site ( network, dir ) :
  site = new_site ( dir )
  print ( f"\nread_site at {dir}" )
  config_dir = dir + '/configmaps'
  file_name = config_dir + '/skupper-site.yaml'
  with open (file_name, 'r') as file:
    yaml_data = yaml.safe_load ( file )
    yaml_data_data = yaml_data['data']

    if 'name' in yaml_data_data :
      site['name'] = yaml_data_data['name']
    else :
      print ( "read_site error: name not found" )
    
    if 'ingress-host' in yaml_data_data:
      site['ingress-host'] = yaml_data_data['ingress-host']
    else :
      print ( "read_site error: ingress-host not found" )
      
      



def read_network ( network ) :
  root = network['root']
  print ( f"Reading config at root {root}" )
  for dir in os.listdir ( root ) :
    site_path = os.path.join (root, dir)
    if os.path.isdir ( site_path ) :
      read_site ( network, site_path )



