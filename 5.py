import asyncio
from bleak import BleakClient
from collections import deque
import requests
from io import BytesIO
from PIL import Image
import time

# ===== CONFIGURAZIONE =====
MAC_ADDRESS = "48:87:2D:6C:FB:0C"   # MAC del BLE Arduino
CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"  # UUID della caratteristica BLE

CAM_IP = "192.168.1.36"   # ESP32-CAM IP
TELEGRAM_TOKEN = "8521151536:AAFt0cQMCeH5nEr5L-lqx5rkm6UqgSeduEo"
CHAT_ID = "7178902327"

ble_buffer = deque(maxlen=5)  # buffer per media ponderata

# ===== Funzione per inviare foto e testo a Telegram =====
def send_telegram(photo: bytes, caption: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    files = {"photo": photo}
    data = {"chat_id": CHAT_ID, "caption": caption}
    try:
        r = requests.post(url, files=files, data=data)
        if r.status_code != 200:
            print(f"Errore invio Telegram: {r.text}")
    except Exception as e:
        print(f"Eccezione invio Telegram: {e}")

# ===== Callback BLE =====
def ble_callback(sender: int, data: bytearray):
    try:
        value_str = data.decode().strip()
        # Estrae solo il numero dalla stringa
        number_part = value_str.split(":")[-1].replace("cm", "").strip()
        value = float(number_part)
        ble_buffer.append(value)
        print(f"Dato ricevuto: {value} cm")
    except Exception as e:
        print(f"Errore parsing BLE: {e}, raw={data}")

# ===== Lettura dati BLE =====
async def read_ble_data():
    async with BleakClient(MAC_ADDRESS) as client:
        await client.start_notify(CHAR_UUID, ble_callback)
        print("Connesso al BLE! Inizio lettura dati...")
        # Legge dati per 1 secondo
        await asyncio.sleep(1)
        await client.stop_notify(CHAR_UUID)
    if ble_buffer:
        # Media ponderata (più recenti hanno più peso)
        weights = list(range(1, len(ble_buffer)+1))
        weighted_avg = sum(v*w for v,w in zip(ble_buffer, weights)) / sum(weights)
        return weighted_avg
    else:
        return None

# ===== Prendi foto dalla CAM =====
def capture_cam():
    url = f"http://{CAM_IP}/stream"
    try:
        r = requests.get(url, stream=True, timeout=5)
        r.raise_for_status()
        return BytesIO(r.content)
    except Exception as e:
        print(f"Errore cattura immagine: {e}")
        return None

# ===== Main =====
async def main():
    while True:
        try:
            # Legge BLE e calcola media ponderata
            distance = await read_ble_data()
            if distance is not None:
                print(f"Media ponderata: {distance:.2f} cm")
                # Cattura immagine
                img_bytes = capture_cam()
                if img_bytes:
                    caption = f"Distanza media ponderata: {distance:.2f} cm"
                    send_telegram(img_bytes, caption)
            else:
                print("Nessun dato ricevuto in questo intervallo")
            await asyncio.sleep(1)  # pausa tra un invio e l'altro
        except Exception as e:
            print(f"Errore loop principale: {e}")
            await asyncio.sleep(2)

# ===== Avvio =====
if __name__ == "__main__":
    asyncio.run(main())
