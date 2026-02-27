import paho.mqtt.client as mqtt
import json

# -----------------------------
# CONFIGURATION
# -----------------------------
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC_VIOLATION = "traffic/violation"

# -----------------------------
# CALLBACK FUNCTIONS
# -----------------------------

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT Broker")
        client.subscribe(TOPIC_VIOLATION)
        print("👮 Police Monitoring System Active...")
    else:
        print("❌ Failed to connect, return code:", rc)


def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())

        print("\n🚨 RED LIGHT VIOLATION ALERT 🚨")
        print("Event:", data.get("event"))
        print("Timestamp:", data.get("timestamp"))
        print("Vehicle ID:", data.get("vehicle_id"))
        print("Plate Number:", data.get("plate_number"))
        print("Image Path:", data.get("image_path"))
        print("Location:", data.get("location"))
        print("System ID:", data.get("system_id"))
        print("--------------------------------------------------")

    except Exception as e:
        print("⚠️ Error processing message:", e)


# -----------------------------
# MAIN
# -----------------------------

def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    print("📡 Connecting to broker...")
    client.connect(BROKER, PORT, 60)

    client.loop_forever()


if __name__ == "__main__":
    main()
