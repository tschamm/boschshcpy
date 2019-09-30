#!/usr/bin/env python

import sys, os 
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import BoschShcPy

ACCESS_CERT = 'keystore/aps-cert.pem'
ACCESS_KEY = 'keystore/aps-key.pem'

SMART_PLUG_ID = "hdm:HomeMaticIP:3014F711A0000496D858ACC5"

try:
  # Create a BoschSHC client with the specified ACCESS_CERT and ACCESS_KEY.
  client = BoschShcPy.Client(ACCESS_CERT, ACCESS_KEY)

  shc_info = client.shc_information()
  print('  version        : %s' % shc_info.version)
  print('  updateState    : %s' % shc_info.updateState)

#   device = client.device(SMART_PLUG_ID)
#   print(device)
# 
#   device_list = client.device_list()
#   print (device_list)
#   for item in device_list.items:
#       print (item)

  # Fetch the smart plug object.
  smart_plug = client.smart_plug(SMART_PLUG_ID)
#   smart_plug_services = client.smart_plug_services(SMART_PLUG_ID)
#   print(smart_plug_services)
#   for item in smart_plug_services.items:
#       print (item)

  smart_plugs = client.initialize_smart_plugs(client.device_list())
  for item in smart_plugs:
      print (item) 

  # Print the object information.
  print('\nThe following information was returned as a SmartPlug object:\n')
#   print('  id  : %d' % smart_plug.\@type)
  print('  state    : %s\n' % smart_plug.switchState)

except BoschShcPy.client.ErrorException as e:
  print('\nAn error occured while requesting a SmartPlug object:\n')

  for error in e.errors:
    print('  code        : %d' % error.code)
    print('  description : %s' % error.description)
    print('  parameter   : %s\n' % error.parameter)
