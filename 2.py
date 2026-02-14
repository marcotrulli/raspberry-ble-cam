import asyncio
import requests
from bleak import BleakClient
from datetime import datetime
from io import BytesIO
from PIL import Image

# ================= CONFIGURAZIONE =================
MAC_ADDRESS = "48:87:2D:6C:FB:0C"   # MAC del modulo BLE
CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"  # Caratteristica BLE
CAMERA_IP = "http://192.168.1.36"   # ESP32-CAM
BOT_TOKEN = "8521151536:AAFt0cQMCeH5nEr5L-lqx5rkm6UqgSeduEo"
CHAT_ID = 7178902327

# ================= FUNZIONI =================
async def read_ble_data():
    """Legge e fa la media ponderata dei dati BLE"""
    values = []
    async with BleakClient(MAC_ADDRESS) as client:
        print("Connesso al BLE!")
        for _ in range(5):  # campionamento ogni 0.2s, 5 volte → 1 secondo
            try:
                data = await client.read_gatt_char(CHAR_UUID)
                text = data.decode().strip()
                if text:
                    values.append(float(text))
            except Exception as e:
                print(f"Errore durante lettura BLE: {e}")
            await asyncio.sleep(0.2)
    if values:
        # media ponderata semplice (più pesanti i valori più recenti)
        weights = list(range(1, len(values)+1))
        weighted_avg = sum(v*w for v, w in zip(values, weights)) / sum(weights)
        return weighted_avg
    return None

def capture_cam_image():
    """Cattura immagine dalla ESP32-CAM"""
    try:
        url = f"{CAMERA_IP}/stream"
        resp = requests.get(url, stream=True, timeout=5)
        if resp.status_code == 200:
            img = Image.open(BytesIO(resp.content))
            return img
        else:
            print("Errore nel fetch immagine CAM")
            return None
    except Exception as e:
        print(f"Errore connessione CAM: {e}")
        return None

def send_to_telegram(message, image=None):
    """Invia messaggio e immagine al bot Telegram"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.get(url, params={"chat_id": CHAT_ID, "text": message})

    if image:
        url_photo = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        with BytesIO() as img_buf:
            image.save(img_buf, format="JPEG")
            img_buf.seek(0)
            requests.post(url_photo, files={"photo": img_buf}, data={"chat_id": CHAT_ID})

# ================= MAIN =================
async def main():
    while True:
        ble_value = await read_ble_data()
        if ble_value is not None:
            message = f"Dati BLE mediati: {ble_value:.2f}\nOra: {datetime.now().strftime('%H:%M:%S')}"
            print(message)
            cam_image = capture_cam_image()
            send_to_telegram(message, cam_image)
        else:
            print("Nessun dato BLE disponibile")
        await asyncio.sleep(0.1)  # pausa breve prima del prossimo ciclo

# ================= RUN =================
if __name__ == "__main__":
    asyncio.run(main())
