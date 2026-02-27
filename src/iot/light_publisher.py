import paho.mqtt.client as mqtt
import time

# -----------------------------
# CONFIGURATION
# -----------------------------
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC_LIGHT = "traffic/light"

# -----------------------------
# MAIN
# -----------------------------

def main():

    client = mqtt.Client()
    client.connect(BROKER, PORT, 60)

    print("🚦 Traffic Light Publisher Started")
    print("Press Ctrl+C to stop")

    try:
        while True:

            print("🟢 GREEN")
            client.publish(TOPIC_LIGHT, "GREEN")
            time.sleep(10)

            print("🟡 YELLOW")
            client.publish(TOPIC_LIGHT, "YELLOW")
            time.sleep(3)

            print("🔴 RED")
            client.publish(TOPIC_LIGHT, "RED")
            time.sleep(10)

    except KeyboardInterrupt:
        print("\n🛑 Publisher stopped.")
        client.disconnect()


if __name__ == "__main__":
    main()
