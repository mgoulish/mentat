#!/usr/bin/env python3

import yaml
import os
import json
import pprint
import sys

import debug
import new



def get_dirs ( root ) :
    return [
        dir for dir in os.listdir ( root )
        if os.path.isdir ( os.path.join (root, dir) )
    ]



def get_site ( mentat, site_name ) :
  for s in mentat['sites'] :
    if s.get('name') == site_name:
      return s
  return None


def get_router ( mentat, site_name, pod_name ) :
  for site in mentat['sites'] : 
    if site['name'] == site_name :
      for router in site['routers'] :
        if router['name'] == pod_name :
          return router
  return NULL
  


def get_site_routers ( mentat ) :
  router_count = 0
  site_names = get_dirs(mentat['root'])
  for site_name in site_names :
    site_root = f"{mentat['root']}/{site_name}"

    site = get_site ( mentat, site_name )
    if site == None :
      print ( f"mentat error: get_site_routers: Can't find site {site_name}" )
      sys.exit ( 1 )

    pods_path = f"{mentat['root']}/{site_name}/pods"
    pod_names = get_dirs(pods_path)
    for pod_name in pod_names :
      if pod_name.startswith('skupper-router') :
        debug.debug ( f"Making new router {pod_name}" )
        router_count += 1
        nickname = f"R{router_count}"
        router = new.new_router ( pod_name, site_name, nickname )
        site['routers'].append ( router )
        logs_path = f"{pods_path}/{pod_name}/logs"



def get_service_controller ( site_path, site_name ) :
  service_controller = new.new_service_controller()
  site_subdirs = get_dirs ( site_path )
  if "pods" in site_subdirs :
    pods_path = f"{site_path}/pods"
    for sc_path in get_dirs(pods_path) :
      if sc_path.startswith('skupper-service-controller') :
        pod_yaml_path = f"{pods_path}/{sc_path}/pod.yaml"
        with open (pod_yaml_path, 'r') as file:
          pod_yaml_data = yaml.safe_load ( file )
          if 'status' in pod_yaml_data :
            status_data = pod_yaml_data['status']
            if 'podIP' in status_data :
              service_controller['pod_ip']   = status_data['podIP']
              service_controller['pod_path'] = pod_yaml_path
              service_controller['name']     = f"{sc_path} {site_name}"

  return service_controller



def read_skupper_site_yaml ( site, file_name ) :
  with open (file_name, 'r') as file:
    yaml_data = yaml.safe_load ( file )
    yaml_data_data = yaml_data['data']

    if 'ingress-host' in yaml_data_data:
      site['ingress-host'] = yaml_data_data['ingress-host']
    else :
      print ( f"read_skupper_site_yaml info: ingress-host not found in file {file_name}" )
      


def read_skupper_internal_yaml ( site, file_name ) :
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
            listener = new.new_listener()
            listener_data = router_json_data[i][1]
            listener.update ( { k: listener_data[k] for k in ['name', 'port', 'role'] if k in listener_data } )
            site['listeners'].append(listener)
          case 'connector' :
            connector = new.new_connector()
            connector_data = router_json_data[i][1]
            connector.update ( { k: connector_data[k] for k in ['host', 'name', 'port', 'role'] if k in connector_data } )
            site['connectors'].append(connector)



def read_site ( mentat, path ) :
  debug.debug ( f"called with path {path}" )
  site_name = path.split('/')[-1]
  site = new.new_site ( site_name, path )

  config_dir = path + '/configmaps'

  # skupper-site.yaml ----------------------------------------
  file_name = config_dir + '/skupper-site.yaml'
  read_skupper_site_yaml ( site, file_name )

  # skupper-internal.yaml ----------------------------------------
  file_name = config_dir + '/skupper-internal.yaml'
  read_skupper_internal_yaml ( site, file_name )

  #site['service_controller'] = get_service_controller ( path, site['name'] )

  mentat['sites'].append(site)

      



def read_network ( mentat ) :
  root = mentat['root']
  for dir in os.listdir ( root ) :
    site_path = os.path.join (root, dir)
    if os.path.isdir ( site_path ) :
      read_site ( mentat, site_path )
  get_site_routers ( mentat )



