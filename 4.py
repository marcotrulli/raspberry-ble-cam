import asyncio
from bleak import BleakClient

# MAC del modulo BLE Arduino
MAC_ADDRESS = "48:87:2D:6C:FB:0C"

# UUID della caratteristica che invia i dati
CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"

# Buffer per memorizzare i dati BLE ricevuti
ble_buffer = []

# Callback che viene chiamata quando arriva un dato dal BLE
def ble_callback(sender: int, data: bytearray):
    try:
        # Se Arduino invia una stringa tipo "42.5"
        value_str = data.decode().strip()
        value = float(value_str)
        ble_buffer.append(value)
        print(f"Dato ricevuto: {value}")
    except Exception as e:
        print(f"Errore parsing BLE: {e}, raw={data}")

async def main():
    async with BleakClient(MAC_ADDRESS) as client:
        print("Connesso al BLE!")

        # Avvia le notifiche sulla caratteristica
        await client.start_notify(CHAR_UUID, ble_callback)

        # Loop principale: ogni 1 secondo calcola la media dei dati ricevuti
        while True:
            await asyncio.sleep(1)
            if ble_buffer:
                # Media ponderata semplice: peso maggiore ai dati più recenti
                weights = list(range(1, len(ble_buffer)+1))
                weighted_sum = sum(v*w for v,w in zip(ble_buffer, weights))
                weighted_avg = weighted_sum / sum(weights)
                print(f"Media ponderata ultima 1s: {weighted_avg:.2f}")
                ble_buffer.clear()
            else:
                print("Nessun dato ricevuto in questo intervallo")

if __name__ == "__main__":
    asyncio.run(main())
