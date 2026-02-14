import time
import requests
import cv2
from bluepy.btle import Peripheral, DefaultDelegate

# ---------------- CONFIGURAZIONE ----------------
BLE_ADDRESS = "AA:BB:CC:DD:EE:FF"  # MAC del modulo DX BT24
DISTANCE_THRESHOLD = 30            # cm, soglia per scattare foto
ESP32_CAM_IP = "192.168.1.50"      # IP della tua ESP32-CAM
PHOTO_PATH = "foto.jpg"

# ---------------- DELEGATE PER BLE ----------------
class MyDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)
        self.distance = None

    def handleNotification(self, cHandle, data):
        try:
            self.distance = float(data.decode().strip())
        except:
            pass

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
            cv2.waitKey(1)  # necessario per aggiornare la finestra
            print("Foto scattata e visualizzata!")
        else:
            print("Errore: la ESP32-CAM non ha risposto correttamente")
    except Exception as e:
        print("Errore richiesta ESP32-CAM:", e)

# ---------------- CONNESSIONE BLE ----------------
print("Connettendo al modulo BLE...")
try:
    peripheral = Peripheral(BLE_ADDRESS, "random")
    peripheral.setDelegate(MyDelegate())
    print("Connesso al BLE!")
except Exception as e:
    print("Errore connessione BLE:", e)
    exit()

# ---------------- LOOP PRINCIPALE ----------------
foto_scattata = False

while True:
    try:
        # Notifica BLE
        if peripheral.waitForNotifications(1.0):
            distance = peripheral.delegate.distance
            if distance is not None:
                print(f"Distanza: {distance:.1f} cm")

                if distance < DISTANCE_THRESHOLD and not foto_scattata:
                    print("Soglia raggiunta, attendo 2 secondi...")
                    time.sleep(2)
                    scatta_foto()
                    foto_scattata = True  # scatta una sola foto finché distanza torna sopra soglia

                elif distance >= DISTANCE_THRESHOLD:
                    foto_scattata = False  # reset per prossima foto
    except Exception as e:
        print("Errore durante la lettura BLE:", e)
        time.sleep(1)
