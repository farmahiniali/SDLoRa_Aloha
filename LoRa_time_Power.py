# this module is about LoRa time on air calculation and power consumption in sleep or sending situation

from math import ceil

# ------ time on air calculation -----------------------

Node_PL = 50  # node_payload_size in byte
node_sleep_cur = 0.0001  # mA  --> node sleep current is 100nA
SF = 7
BW = 125000
CR = 1  # coding rate can be 5/4 to 8/4 CR=1 means 5/4 and CR=4 means 8/4
time_symbol = (2**SF)/BW
H = 0  # header is 0 when there isn't header and is 1 when there is header
N_payload_symbol = 8 + max(ceil(((8 * Node_PL) - (4 * SF) + 16 + 28 - 20 * H)/(4 * SF)) * (CR + 4), 0)  # N stands for Node


T_PL = N_payload_symbol * time_symbol  # time unit is  second
No_preamble_symbol = 2
T_Preamble = (No_preamble_symbol + 4.25) * time_symbol  # time unit is  second
time_on_air = (T_PL + T_Preamble) * 1000  # time unit is milli second

# ------ Time of giving ack ------------------------------

Ack_PL = 16
G_payload_symbol = 8 + max(ceil((8 * Ack_PL - 4 * SF + 16 + 28 - 20 * H)/(4 * SF)) * (CR + 4), 0)  # G stands for Gateway
G_PL = G_payload_symbol * time_symbol  # time unit is second
ack_time_on_air = (G_PL + T_Preamble) * 1000  # time unit is milli second


# ------ Time of sending ready header to receive synchronization ------------------------------

sync_ready_PL = 7
sync_ready_payload_symbol = 8 + max(ceil((8 * sync_ready_PL - 4 * SF + 16 + 28 - 20 * H)/(4 * SF)) * (CR + 4), 0)  # G stands for Gateway
s_ready_PL = sync_ready_payload_symbol * time_symbol  # time unit is second
sync_ready_time_on_air = (s_ready_PL + T_Preamble) * 1000  # time unit is milli second


# ------ Time of just receiving synchronization ------------------------------

sync_PL = 16
sync_payload_symbol = 8 + max(ceil((8 * sync_PL - 4 * SF + 16 + 28 - 20 * H)/(4 * SF)) * (CR + 4), 0)  # G stands for Gateway
s_PL = sync_payload_symbol * time_symbol  # time unit is second
sync_rec_time_on_air = (s_PL + T_Preamble) * 1000  # time unit is milli second


# -------- Semtec SX1272 receiving energy consumption ----------------
# -------- this items are based on LoRa modem calculator tool -----


def lora_transmit_current(TP):  # unit is mA
    if 0 <= TP <= 20:
        transmit_cur = [22, 23, 24, 24, 24, 25, 25, 25, 25, 26, 31, 32, 34, 35, 44, 82, 85, 90, 105, 115, 125]
        return transmit_cur[int(TP)]
    else:
        return -1


def lora_receive_current(BW):  # unit is mA
    if int(BW) == 125000:
        return 10.8
    elif int(BW) == 250000:
        return 11.6
    elif int(BW) == 500000:
        return 13
    else:
        return -1


node_sleep_current_usage = 0.0000001  # unit is Amper
node_transmission_power_17dbm = 50  # transmission unit is mW and is equivalent to 17 dbm
node_transmission_power_20dbm = 100  # transmission unit is mW and is equivalent to 20 dbm


# ------- power consumption ---------------------------

Battery_volt = 3  # default battery voltage is 3 volt


class Battery:
    def __init__(self, bat_cap=1000, bat_volt=3):  # capacity unit is mAH and bat_volt unit is volt
        self.bat_cap = bat_cap
        self.bat_volt = bat_volt
        self.bat_charge = self.bat_cap * 3600 * 1000  # unit is turned into milli amper mili second
        # self.bat_energy = self.bat_charge * self.bat_volt  # energy unit is milli joule


def sleep_energy_consumption_curr(sleep_start_time, sleep_end_time):  # time unit is ms and sleep mode is bool
    duration = sleep_end_time - sleep_start_time
    energy_usage_curr = duration * node_sleep_cur  # the unit is milli amper milli second
    return energy_usage_curr


def sending_data_energy_consumption_curr(TP):
    energy_usage_curr = time_on_air * lora_transmit_current(TP)  # energy unit is milli amper
    return energy_usage_curr  # energy unit is milli joule


def sending_ready_energy_consumption_curr(TP):
    energy_usage_curr = sync_ready_time_on_air * lora_transmit_current(TP)  # energy unit is milli amper
    return energy_usage_curr  # energy unit is milli joule


def receiving_energy_consumption_curr(BW):
    return lora_receive_current(BW) * ack_time_on_air


def receiving_ready_energy_consumption_curr(BW):
    return lora_receive_current(BW) * sync_rec_time_on_air