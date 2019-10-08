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
        self.registered_devices = {}
        self.registered_callbacks = {}
        
    def event(self, query_result):
        if 'deviceId' not in query_result:
            return
            
        if query_result['deviceId'] in self.registered_devices:
            self.event_device(self.registered_devices[query_result['deviceId']], query_result)
        pass
    
    def event_device(self, device, query_result):
#         print("Updating device by event...")
        device.update_from_query(query_result)
        self.registered_callbacks[device](device)
#         print(device)
        pass
    
    def register(self, device, callback):
        self.registered_devices[device.id] = device        
        self.registered_callbacks[device] = callback
    
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
                