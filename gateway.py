from time import sleep
from SX127x.LoRa import *
from SX127x.LoRaArgumentParser import LoRaArgumentParser
from SX127x.board_config import BOARD
import json
import requests

API_POST_URL = "http://192.168.113.89:5000/newdata"
BOARD.setup()

class LoRaRcvCont(LoRa):
    def __init__(self, verbose=False):
        super(LoRaRcvCont, self).__init__(verbose)
        self.set_mode(MODE.SLEEP)
        self.set_dio_mapping([0] * 6)

    def on_rx_done(self):
        BOARD.led_on()
        print("\nRxDone")
        self.clear_irq_flags(RxDone=1)
        payload = self.read_payload(nocheck=True)
        payload_string = bytes(payload).decode("utf-8",'ignore')
        print(payload_string)
        payload_json = json.loads(payload_string)
        print("[DEBUG] JSON:", payload_json)
        node_id = payload_json["NODEID"]
        print(node_id)
        try:
            update_dict = {
                "temperature": payload_json["TEMP"],
                "relative_humidity": payload_json["HUM"],
                "surface_pressure": payload_json["DEPTH"],
                "flow_rate": payload_json["FLOW"]

            }
            payload_string = json.dumps(update_dict)
            payload_json = json.loads(payload_string)
            response = requests.post(
                url=API_POST_URL,
                json=payload_json,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            print("Response:", response.json())
            pred_score = response.json()["predictions"]["24_hour"]
        except requests.exceptions.RequestException as e:
            print("\n[ERROR] Request failed:", e)
        self.set_mode(MODE.SLEEP)
        self.reset_ptr_rx()
        BOARD.led_off()
        self.set_mode(MODE.RXCONT)

    def on_rx_timeout(self):
        print("\non_RxTimeout")
        print(self.get_irq_flags())

    def start(self):
        self.reset_ptr_rx()
        self.set_mode(MODE.RXCONT)
        while True:
            sleep(.5)
            rssi_value = self.get_rssi_value()
            status = self.get_modem_status()
            sys.stdout.flush()
            sys.stdout.write("\r%d %d %d" % (rssi_value, status['rx_ongoing'], status['modem_clear']))

lora = LoRaRcvCont(verbose=False)

lora.set_mode(MODE.STDBY)
lora.set_pa_config(pa_select=1)
lora.set_freq(433)
#lora.set_rx_crc(True)
#lora.set_coding_rate(CODING_RATE.CR4_6)
#lora.set_pa_config(max_power=0, output_power=0)
#lora.set_lna_gain(GAIN.G1)
#lora.set_implicit_header_mode(False)
#lora.set_low_data_rate_optim(True)
#lora.set_pa_ramp(PA_RAMP.RAMP_50_us)
#lora.set_agc_auto_on(True)

print(lora)
assert(lora.get_agc_auto_on() == 1)

try:
    lora.start()
except KeyboardInterrupt:
    sys.stdout.flush()
    print("")
    sys.stderr.write("KeyboardInterrupt\n")
finally:
    sys.stdout.flush()
    print("")
    lora.set_mode(MODE.SLEEP)
    print(lora)
    BOARD.teardown()
