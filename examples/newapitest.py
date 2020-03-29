import boschshcpy

# Create session
session = boschshcpy.BoschSHCPySession(
    controller_ip="192.168.1.6", certificate='keystore/boschshcpy-cert.pem', key='keystore/boschshcpy-key.pem')
device = session.device('roomClimateControl_hz_5')
service = device.device_service('TemperatureLevel')
print(service.temperature)

# # Update this service's state
# service.short_poll()

# # Start long polling thread in background
# session.start_polling()

# # Do work here

# # Stop polling
# session.stop_polling()
