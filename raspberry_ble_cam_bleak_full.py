# raspberry_ble_cam_bleak_full.py
import asyncio
import requests
import cv2
from bleak import BleakClient

# ---------------- CONFIGURAZIONE ----------------
MAC_ADDRESS = "48:87:2D:6C:FB:0C"       # MAC del modulo BLE
CHAR_UUID = "0000FFE1-0000-1000-8000-00805F9B34FB"  # UUID caratteristica distanza
DISTANCE_THRESHOLD = 30                 # soglia in cm per scattare foto
ESP32_CAM_IP = "192.168.1.50"          # IP della tua ESP32-CAM
PHOTO_PATH = "foto.jpg"

TELEGRAM_TOKEN = "8270696186:AAEHRIPXbWpc_MnZ9kjMTmPDE2XO85Kbud0"
CHAT_ID = 7178902327

# ---------------- FUNZIONI ----------------
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

# ---------------- MAIN ASINCRONO ----------------
async def main():
    print("Connettendo al modulo BLE...")
    foto_scattata = False
    try:
        async with BleakClient(MAC_ADDRESS) as client:
            print("Connesso al BLE!")
            while True:
                try:
                    value = await client.read_gatt_char(CHAR_UUID)
                    distance = float(value.decode().strip())
                    print(f"Distanza: {distance:.1f} cm")

                    if distance < DISTANCE_THRESHOLD and not foto_scattata:
                        print("Soglia raggiunta, attendo 2 secondi...")
                        await asyncio.sleep(2)
                        scatta_foto()
                        foto_scattata = True
                    elif distance >= DISTANCE_THRESHOLD:
                        foto_scattata = False

                    await asyncio.sleep(0.2)
                except Exception as e:
                    print("Errore durante lettura BLE:", e)
                    await asyncio.sleep(1)
    except Exception as e:
        print("Errore connessione BLE:", e)

if __name__ == "__main__":
    asyncio.run(main())
