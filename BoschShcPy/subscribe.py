"""Listen to polling events."""
import threading
import time
import collections

from BoschShcPy.polling_service import PollingService

class Subscription():
    def __init__(self, client):
        self.devices = None
        self.client = client
        self.poll_thread = None
        self.exiting = None
        self.polling_service = None
        self.registered_devices = collections.defaultdict(list)
        self.registered_callbacks = collections.defaultdict(list)
        
    def event(self, query_result):
        """First check for deviceId, then check for id. Otherwise return."""
        device_id = None
        if '@type' in query_result and query_result['@type'] == "DeviceServiceData":
            device_id = query_result['deviceId']
        elif '@type' in query_result and query_result['@type'] == "device":
            device_id = query_result['id']
        else:
            return
         
        for device in self.registered_devices.get(device_id, ()):
            self.event_device(device, query_result)
        pass
    
    def event_device(self, device, query_result):
#         print("Updating device %s by event..." % device.get_id)
        device.update_from_query(query_result)
        for callback in self.registered_callbacks.get(device, ()):
            try:
                callback(device)
            except Exception:
                pass
#         print(device)
        pass
    
    def register(self, device, callback):
        self.registered_devices[device.id].append(device)   
        self.registered_callbacks[device].append(callback)
    
    def subscribe_polling(self):
        """Initialize long polling by subscription."""
        params=["com/bosch/sh/remote/*", None]
        data=[{'jsonrpc': '2.0', 'method': 'RE/subscribe', 'id': 'boschshcpy', 'params': params}]
        self.polling_service = PollingService().load(self.client.request("remote/json-rpc", method='POST', params=data))
        return

    def unsubscribe_polling(self):
        """Unsubscribe from long polling."""
        params=[self.polling_service.result]
        data=[{'jsonrpc': '2.0', 'method': 'RE/unsubscribe', 'id': 'boschshcpy', 'params': params}]
        self.client.request("remote/json-rpc", method='POST', params=data)
        self.polling_service = None
        return

    def polling(self, duration=20):
        """Query long polling."""
        
        while not self.exiting:
            params=[self.polling_service.result, duration]
            data=[{'jsonrpc': '2.0', 'method': 'RE/longPoll', 'id': 'boschshcpy', 'params': params}]
            query_result = self.client.request("remote/json-rpc", method='POST', params=data)
            
            for elem in list(query_result):
                if 'result' in elem.keys():
                    for result in elem['result']:
#                         print (result)
                        if not self.exiting:
                            self.event(result)
                            time.sleep(0.2)
            
            continue

    def join(self):
        self.poll_thread.join()
         
    def start(self):
        if self.polling_service == None:
            self.subscribe_polling()
        self.poll_thread = threading.Thread(target=self.polling,
                                             name='BoschShcPy Polling Thread')
        self.poll_thread.deamon = True
        self.poll_thread.start()
        
    def stop(self):
        self.exiting = True
        self.unsubscribe_polling()
        self.join()
                