import paho.mqtt.client as mqtt
from typing import Optional, Callable

class ClientHandler:
    def __init__(
            self, 
            broker_host: str,
            topic_send: str,
            topic_receive: Optional[str] = None,
            on_message: Optional[Callable] = None
        ):
        self._broker_host = broker_host
        self._topic_send = topic_send
        self._topic_receive = topic_receive
        self.on_message = on_message
        self._client = mqtt.Client()
        self._is_connected = False
    
    @property
    def is_connected(self) -> bool:
        return self._is_connected

    def connect(self):
        if self.on_message:
            self._client.on_message = self.on_message
        self._client.on_connect = self._on_connect 
        self._client.on_disconnect = self._on_disconnect
        
        print(f"Connecting to broker: {self._broker_host}")

        try:
            self._client.connect(self._broker_host)
            self._client.loop_start()
        except Exception as e:
            print(f"Error while connecting to the broker: {e}")

    def disconnect(self):
        self._client.loop_stop()
        self._client.disconnect()
        self._is_connected = False
        print("Disconnected from broker")

    def publish(self, message: str):
        if not self._is_connected:
            print("Cannot publish: not connected to broker")
            return
        
        self._client.publish(self._topic_send, message)

    def _on_connect(self, client, userdata, flags, rc) -> None:
        if rc == 0:
            self._is_connected = True
            print("Connected to broker successfully")
            if self._topic_receive:
                print(f"Subscribing to {self._topic_receive}")
                self._client.subscribe(self._topic_receive)
        else:
            print(f"Connection failed with code: {rc}")
    
    def _on_disconnect(self, client, userdata, rc) -> None:
        self._is_connected = False
        if rc != 0:
            print(f"Unexpected disconnection (code: {rc})")

