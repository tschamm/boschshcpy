#!/usr/bin/env python

import sys, os 
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import boschshc

ACCESS_CERT = 'keystore/aps-cert.pem'
ACCESS_KEY = 'keystore/aps-key.pem'

SMART_PLUG_ID = "hdm:HomeMaticIP:3014F711A0000496D858ACC5"

try:
  # Create a BoschSHC client with the specified ACCESS_CERT and ACCESS_KEY.
  client = boschshc.Client(ACCESS_CERT, ACCESS_KEY)

  shc_info = client.shc_information()
  print('  version        : %s' % shc_info.version)
  print('  updateState    : %s' % shc_info.updateState)

  device = client.device(SMART_PLUG_ID)
  print('  id        : %s' % device.id)
  print('  name      : %s' % device.name)
  print('  status    : %s' % device.status)

  device_list = client.device_list()
#   print('  version        : %s\n' % shc_info.version)
#   print('  updateState    : %s\n' % shc_info.updateState)


  # Fetch the smart plug object.
  smart_plug = client.smart_plug(SMART_PLUG_ID)

  # Print the object information.
  print('\nThe following information was returned as a SmartPlug object:\n')
#   print('  id  : %d' % smart_plug.\@type)
  print('  state    : %s\n' % smart_plug.switchState)

except boschshc.client.ErrorException as e:
  print('\nAn error occured while requesting a SmartPlug object:\n')

  for error in e.errors:
    print('  code        : %d' % error.code)
    print('  description : %s' % error.description)
    print('  parameter   : %s\n' % error.parameter)
