
import paho.mqtt.client as mqtt
def on_message(client, userdata, msg):
	print(msg.topic, msg.payload.decode())
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_message = on_message
client.connect("broker.hivemq.com", 1883)
client.subscribe("topico_do_kebi")
client.loop_forever()
