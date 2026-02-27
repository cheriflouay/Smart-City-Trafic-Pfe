import paho.mqtt.client as mqtt

# ==========================================
# MQTT CONFIGURATION
# ==========================================
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "traffic/light"

# ==========================================
# Callback when connected
# ==========================================
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT Broker")
        client.subscribe(TOPIC)
        print(f"📡 Subscribed to topic: {TOPIC}")
    else:
        print("❌ Failed to connect")

# ==========================================
# Callback when message received
# ==========================================
def on_message(client, userdata, msg):
    state = msg.payload.decode()
    print(f"\n📩 Received Light State: {state}")

    if state == "GREEN":
        print("🟢 GREEN LED ON")
        print("🔴 RED LED OFF")
    elif state == "RED":
        print("🔴 RED LED ON")
        print("🟢 GREEN LED OFF")
    else:
        print("⚠ Unknown state")

# ==========================================
# MQTT Client Setup
# ==========================================
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

print("🔄 Connecting to broker...")
client.connect(BROKER, PORT, 60)

print("🚦 Simulated ESP32 Listening...")
client.loop_forever()
