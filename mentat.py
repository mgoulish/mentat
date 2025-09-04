#!/usr/bin/env python3

import sys
import os
import re
import yaml
import json
import pprint
from   datetime import datetime

import events



def new_event ( ) :
  keys = [ 'connection_id',
           'date',
           'epoch_micros',
           'event', 
           'from',
           'id',
           'line',
           'message',
           'time',
           'timestamp',
           'to' ]
  event = dict.fromkeys ( keys, None )
  return event



def get_dirs ( root ) :
    return [
        dir for dir in os.listdir ( root )
        if os.path.isdir ( os.path.join (root, dir) )
    ]



def get_site_routers ( site_path ) :
  site_subdirs = get_dirs ( site_path )
  routers = []
  if "pods" in site_subdirs :
    pods_path = f"{site_path}/pods"
    pods = get_dirs ( pods_path )
    for pod in pods :
      if pod.startswith ( "skupper-router" ) :
        pod_path = f"{pods_path}/{pod}"
        pod_yaml_file = f"{pod_path}/pod.yaml" 
        with open (pod_yaml_file, 'r') as file:
          pod_yaml_data = yaml.safe_load ( file )
          if 'metadata' in pod_yaml_data :
            metadata = pod_yaml_data['metadata']
            if 'annotations' in metadata :
              annotations = metadata['annotations']
              if 'k8s.v1.cni.cncf.io/network-status' in annotations:
                network_status_str = annotations['k8s.v1.cni.cncf.io/network-status']
                network_status = json.loads(network_status_str)
                ip = next((item.get('ips', []) for item in network_status), [])
                router = { "pod_name" : pod, 
                           "pod_path" : pod_path,
                           "ip"       : ip }
                routers.append ( router )
  return routers





#================================================================
#  Main 
#================================================================

root_path =  sys.argv[1] 
print (f"main: root_path: {root_path}") 
site_dirs = get_dirs ( root_path ) 
sites = []

for site_dir in site_dirs :
  site_path = f"{root_path}/{site_dir}"
  routers = get_site_routers ( site_path )
  site = { "name"      : site_path.split('/')[-1],    # Can't this just be 'site_dir' ?
           "root_path" : root_path,
           "routers"   : routers,
           "events"    : [] }
  sites.append ( site )

#pprint.pprint ( sites, indent=2, width=60 )

events.find_router_connections_accepted ( root_path, sites )
events.find_begin_end_lines ( sites )
