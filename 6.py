import asyncio
from bleak import BleakClient
import requests
from PIL import Image
from io import BytesIO

# ----------- CONFIGURAZIONE -----------
MAC_ADDRESS = "48:87:2D:6C:FB:0C"  # BLE Arduino
CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"

ESP32_CAM_IP = "192.168.1.36"  # IP ESP32-CAM
DISTANCE_THRESHOLD = 40.0  # cm

# ----------- LETTURA BLE -----------
async def read_ble_data():
    async with BleakClient(MAC_ADDRESS) as client:
        try:
            raw = await client.read_gatt_char(CHAR_UUID)
            line = raw.decode('utf-8').strip()
            # Prendi solo il numero dalla stringa tipo "Distanza media ponderata: 6.66 cm"
            if "cm" in line:
                value = float(line.split(":")[1].replace("cm", "").strip())
                return value
        except Exception as e:
            print("Errore lettura BLE:", e)
    return None

# ----------- SCATTO FOTO SULLA CAM -----------
def take_camera_photo():
    try:
        url = f"http://{ESP32_CAM_IP}/capture"  # endpoint scatto singolo
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        img.save("last_frame.jpg")  # salva l'immagine localmente
        print("Foto scattata e salvata!")
        return img
    except Exception as e:
        print("Errore cattura immagine:", e)
        return None

# ----------- LOOP PRINCIPALE -----------
async def main():
    while True:
        try:
            # 1. Leggi distanza BLE
            dist = await read_ble_data()
            if dist is not None:
                print(f"Distanza ricevuta: {dist:.2f} cm")
                
                # 2. Se la distanza supera il limite, scatta foto
                if dist > DISTANCE_THRESHOLD:
                    print(f"Distanza > {DISTANCE_THRESHOLD} cm → Scatto foto!")
                    take_camera_photo()
            else:
                print("Nessun dato disponibile")

            # Attendi 1 secondo prima della prossima lettura
            await asyncio.sleep(1)
        except Exception as e:
            print("Errore loop principale:", e)
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
