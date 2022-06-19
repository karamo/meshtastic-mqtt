# python3.6

import meshtastic_mqtt.portnums_pb2 as portnums_pb2
import random
import json
import time

import meshtastic_mqtt.mesh_pb2 as mesh_pb2
import meshtastic_mqtt.mqtt_pb2 as mqtt_pb2
import meshtastic_mqtt.environmental_measurement_pb2 as env_meas_pb2

from paho.mqtt import client as mqtt_client

class MeshtasticMQTT():

    broker = '192.168.1.111'
    port = 1883
    username = 'user'
    password = 'public'
    
    topic = "msh/1/c/LauraKG/#"
    # generate client ID with pub prefix randomly
    client_id = f'meshtastic-mqtt-{random.randint(0, 100)}'
    prefix = "meshtastic/"

    def connect_mqtt(self) -> mqtt_client:
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                print("Connected to MQTT Broker! WZ V0.12")
            else:
                print("Failed to connect, return code %d\n", rc)

        client = mqtt_client.Client(self.client_id)
        client.username_pw_set(self.username, self.password)
        client.on_connect = on_connect
        client.connect(self.broker, self.port)
        return client


    def subscribe(self, client: mqtt_client):
        def on_message(client, userdata, msg):
            try:
                print("=====================================")
                se = mqtt_pb2.ServiceEnvelope()
                se.ParseFromString(msg.payload)
                print(se)
                mp = se.packet
    
                if mp.decoded.portnum == portnums_pb2.POSITION_APP:
                    pos = mesh_pb2.Position()
                    pos.ParseFromString(mp.decoded.payload)
                    print("===== pos - payload =====")
                    print(pos)
                    print("=====================================")
                    node = hex(getattr(mp, "from"))
                    tonode = getattr(mp, "to")
                    if tonode == 4294967295:
                        tonode = "^all"
                    else:
                        tonode = "!"+hex(tonode[2:])
                    owntracks_payload = {
                        "_type": "location",
                        "from": "!"+node[2:],
                        "to": tonode,
                        "lat": round(pos.latitude_i * 1e-7, 7),
                        "lon": round(pos.longitude_i * 1e-7, 7),
                        "alt": pos.altitude,
                        "pos_time": time.strftime("%H:%M:%S %d.%m.%Y", time.localtime(pos.pos_timestamp)),
                        "sats": pos.sats_in_view,
                        "batt": pos.battery_level,
                        "hop_limit": mp.hop_limit,
                        "snr": mp.rx_snr,
                        "rssi": mp.rx_rssi
                    }
                    #print(owntracks_payload)
                    client.publish(self.prefix+str(getattr(mp, "from"))+"/position", json.dumps(owntracks_payload))
    
                elif mp.decoded.portnum == portnums_pb2.NODEINFO_APP:
                    nodeinf = mesh_pb2.User()
                    nodeinf.ParseFromString(mp.decoded.payload)
                    print("===== nodeinf - payload =====")
                    print(nodeinf)
                    print("=====================================")
                    node = hex(getattr(mp, "from"))
                    tonode = getattr(mp, "to")
                    if tonode == 4294967295:
                        tonode = "^all"
                    else:
                        tonode = "!"+hex(tonode[2:])
                    owntracks_payload = {
                        "_type": "nodeinfo",
                        "from": "!"+node[2:],
                        "to": tonode,
                        "id": nodeinf.id,
                        "long_name": nodeinf.long_name,
                        "short_name": nodeinf.short_name,
                        "hop_limit": mp.hop_limit,
                        "rx_time": time.strftime("%H:%M:%S %d.%m.%Y", time.localtime(mp.rx_time))
                    }
                    #print(owntracks_payload)
                    client.publish(self.prefix+str(getattr(mp, "from"))+"/nodeinfo", json.dumps(owntracks_payload))

                elif mp.decoded.portnum == portnums_pb2.TEXT_MESSAGE_APP:
                    text = mp.decoded.payload
                    print("===== text - payload =====")
                    print(text)
                    print("=====================================")
                    node = hex(getattr(mp, "from"))
                    tonode = getattr(mp, "to")
                    if tonode == 4294967295:
                        tonode = "^all"
                    else:
                        tonode = "!"+hex(tonode[2:])
                    owntracks_payload = {
                        "_type": "text",
                        "from": "!"+node[2:],
                        "to": tonode,
                        "text": text.decode('utf-8'),
                        "rx_time": time.strftime("%H:%M:%S %d.%m.%Y", time.localtime(mp.rx_time)),
                        "hop_limit": mp.hop_limit,
                        "snr": mp.rx_snr,
                        "rssi": mp.rx_rssi
                    }
                    #print(owntracks_payload)
                    client.publish(self.prefix+str(getattr(mp, "from"))+"/text", json.dumps(owntracks_payload))
                    #print("===== text published =====")
    
                elif mp.decoded.portnum == portnums_pb2.ENVIRONMENTAL_MEASUREMENT_APP:
                    env = env_meas_pb2.EnvironmentalMeasurement()
                    env.ParseFromString(mp.decoded.payload)
                    print(env)
                    client.publish(self.prefix+str(getattr(mp, "from"))+"/temperature", env.temperature)
                    client.publish(self.prefix+str(getattr(mp, "from"))+"/relative_humidity", env.relative_humidity)
            except:
                print("=====Exception=====")

        client.subscribe(self.topic)
        client.on_message = on_message


    def run(self): #on appdaemon remove the argument here
        client = self.connect_mqtt()
        self.subscribe(client)
        client.loop_forever()

    def initialize(self):
        self.run(self)

def main():
    mm = MeshtasticMQTT()
    mm.run()


#in appdaemon comment this block out
if __name__ == '__main__':
    main()
