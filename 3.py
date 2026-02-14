import asyncio
from bleak import BleakClient, BleakError
from collections import deque
import requests

# ====== CONFIG BLE ======
MAC_ADDRESS = "48:87:2D:6C:FB:0C"
CHAR_UUID = "0000FFE1-0000-1000-8000-00805F9B34FB"

BUFFER_SIZE = 5       # numero di letture da memorizzare
READ_INTERVAL = 0.2    # ogni quanto leggere dati BLE (s)
SEND_INTERVAL = 1.0    # ogni quanto inviare media al bot (s)

# ====== CONFIG TELEGRAM ======
BOT_TOKEN = "8521151536:AAFt0cQMCeH5nEr5L-lqx5rkm6UqgSeduEo"
CHAT_ID = 7178902327  # il tuo chat_id Telegram

# ====== FUNZIONE INVIO TELEGRAM ======
def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Errore invio Telegram: {e}")

# ====== FUNZIONE PER LEGGERE BLE ======
async def read_ble_data(buffer: deque):
    try:
        async with BleakClient(MAC_ADDRESS) as client:
            print("Connesso al BLE!")
            while True:
                try:
                    raw = await client.read_gatt_char(CHAR_UUID)
                    value_str = raw.decode().strip()
                    if value_str:
                        value = float(value_str)
                        buffer.append(value)
                        if len(buffer) > BUFFER_SIZE:
                            buffer.popleft()
                    await asyncio.sleep(READ_INTERVAL)
                except Exception as e:
                    print(f"Errore durante lettura BLE: {e}")
                    break
    except BleakError as e:
        print(f"Errore connessione BLE: {e}")

# ====== FUNZIONE PER PROCESSARE I DATI ======
async def process_data(buffer: deque):
    while True:
        await asyncio.sleep(SEND_INTERVAL)
        if buffer:
            weights = list(range(1, len(buffer)+1))
            weighted_avg = sum(v*w for v,w in zip(buffer, weights)) / sum(weights)
            print(f"Valore medio ponderato: {weighted_avg:.2f}")
            send_telegram(f"Valore medio ponderato: {weighted_avg:.2f}")
        else:
            print("Nessun dato disponibile")

# ====== MAIN ======
async def main():
    buffer = deque()
    while True:
        await asyncio.gather(
            read_ble_data(buffer),
            process_data(buffer)
        )
        print("Riconnessione tra 2 secondi...")
        await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())
