# raspberry_ble_cam.py
import time
import requests
import cv2
from bluepy.btle import Peripheral

# ---------------- CONFIGURAZIONE ----------------
MAC_ADDRESS = "48:87:2D:6C:FB:0C"       # MAC del modulo BLE
CHAR_UUID = "0000FFE1-0000-1000-8000-00805F9B34FB"  # UUID caratteristica distanza
DISTANCE_THRESHOLD = 30                 # soglia in cm per scattare foto
ESP32_CAM_IP = "192.168.1.36"          # IP della tua ESP32-CAM
PHOTO_PATH = "foto.jpg"

TELEGRAM_TOKEN = "8270696186:AAEHRIPXbWpc_MnZ9kjMTmPDE2XO85Kbud0"
CHAT_ID = 7178902327

# ---------------- FUNZIONE PER SCATTARE FOTO ----------------
def scatta_foto():
    try:
        url = f"http://{ESP32_CAM_IP}/capture"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            with open(PHOTO_PATH, "wb") as f:
                f.write(r.content)
            # Mostra la foto con OpenCV
            img = cv2.imread(PHOTO_PATH)
            cv2.imshow("Foto ESP32-CAM", img)
            cv2.waitKey(1)
            print("Foto scattata e visualizzata!")
            invia_telegram(PHOTO_PATH)
        else:
            print("Errore: ESP32-CAM non ha risposto correttamente")
    except Exception as e:
        print("Errore richiesta ESP32-CAM:", e)

# ---------------- FUNZIONE INVIO TELEGRAM ----------------
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

# ---------------- CONNESSIONE BLE ----------------
print("Connettendo al modulo BLE...")
try:
    peripheral = Peripheral(MAC_ADDRESS)
    char = peripheral.getCharacteristics(uuid=CHAR_UUID)[0]
    print("Connesso al BLE!")
except Exception as e:
    print("Errore connessione BLE:", e)
    exit()

# ---------------- LOOP PRINCIPALE ----------------
foto_scattata = False

while True:
    try:
        data = char.read()
        distance = float(data.decode().strip())
        print(f"Distanza: {distance:.1f} cm")

        if distance < DISTANCE_THRESHOLD and not foto_scattata:
            print("Soglia raggiunta, attendo 2 secondi...")
            time.sleep(2)
            scatta_foto()
            foto_scattata = True

        elif distance >= DISTANCE_THRESHOLD:
            foto_scattata = False

        time.sleep(0.2)

    except Exception as e:
        print("Errore durante la lettura BLE:", e)
        time.sleep(1)

