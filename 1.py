import asyncio
import requests
import cv2
from bleak import BleakClient

# ---------------- CONFIG ----------------
MAC_ADDRESS = "48:87:2D:6C:FB:0C"
CHAR_UUID = "0000FFE1-0000-1000-8000-00805F9B34FB"

DISTANCE_THRESHOLD = 30                 # soglia cm per scattare foto
ESP32_CAM_IP = "192.168.1.50"          # IP ESP32-CAM
PHOTO_PATH = "foto.jpg"

TELEGRAM_TOKEN = "8270696186:AAEHRIPXbWpc_MnZ9kjMTmPDE2XO85Kbud0"
CHAT_ID = 7178902327

# ---------------- FUNZIONE FOTO ----------------
def scatta_foto():
    try:
        url = f"http://{ESP32_CAM_IP}/capture"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            with open(PHOTO_PATH, "wb") as f:
                f.write(r.content)
            img = cv2.imread(PHOTO_PATH)
            cv2.imshow("Foto ESP32-CAM", img)
            cv2.waitKey(1)
            print("Foto scattata e visualizzata!")
            invia_telegram(PHOTO_PATH)
        else:
            print("Errore: ESP32-CAM non ha risposto correttamente")
    except Exception as e:
        print("Errore richiesta ESP32-CAM:", e)

# ---------------- FUNZIONE TELEGRAM ----------------
def invia_telegram(foto_path):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
        files = {'photo': open(foto_path, 'rb')}
        data = {'chat_id': CHAT_ID}
        r = requests.post(url, files=files, data=data)
        if r.status_code == 200:
            print("Foto inviata su Telegram!")
        else:
            print("Errore invio Telegram:", r.text)
    except Exception as e:
        print("Errore Telegram:", e)

# ---------------- CALLBACK BLE ----------------
foto_scattata = False
def ble_callback(sender: int, data: bytearray):
    global foto_scattata
    try:
        text = data.decode().strip()
        if text == '':
            return  # ignora pacchetti vuoti
        distance = float(text)
        print(f"Distanza BLE: {distance:.1f} cm")

        if distance < DISTANCE_THRESHOLD and not foto_scattata:
            print("Soglia raggiunta, attendo 2 secondi...")
            asyncio.create_task(asyncio.sleep(2))
            scatta_foto()
            foto_scattata = True
        elif distance >= DISTANCE_THRESHOLD:
            foto_scattata = False

    except Exception as e:
        print("Errore decodifica BLE:", e)

# ---------------- LOOP ASINCRONO ----------------
async def main():
    async with BleakClient(MAC_ADDRESS) as client:
        print("Connesso al BLE!")
        await client.start_notify(CHAR_UUID, ble_callback)
        while True:
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
