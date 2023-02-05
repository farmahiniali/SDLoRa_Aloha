# -----------------
# -----------------
import LoRa_time_Power 
import random
from enum import Enum


class states(Enum):
    not_arrived = 1
    sleep = 2
    sending = 3
    collision = 4
    dead = 5


class NodeAloha(object):
    def __init__(self, node_id, node_period, exe_time):
        # TP is 17 as a default
        self.node_id = node_id
        self.node_period = node_period
        self.exe_time = exe_time
        self.TP = 17
        self.BW = 125000
        self.SF = 7
        self.arrival_time = random.randrange(0, node_period)
        self.node_battery = LoRa_time_Power.Battery(1000, 3)
        self.time = self.arrival_time
        self.next_event_time = self.arrival_time  # this property will assign with sens_msg method
        self.stat = states.not_arrived  # this property will only assign with time trigger
        self.next_event = states.sending # this property will only assign with time trigger


    def time_trigger(self, global_time):  # this function has the task of changing state of node and report it and set time
        if self.next_event_time < global_time:
            if self.stat == states.dead:
                return self.stat, -1 # -1 means node is dead
        elif self.next_event_time == global_time:
            if (self.stat == states.sleep or self.stat == states.not_arrived) and self.next_event == states.sending:
                self.battery_charge_update(global_time)
                self.stat = states.sending
                sent_result = self.send_msg(self, global_time)
                if sent_result == -1:
                    return  self.stat, -1
                else:
                    self.time = global_time
                    return self.stat, 0 # 0 means node is alive and state of node has been sent
            elif self.stat == states.sending and self.next_event == states.sleep:
                self.stat = states.sleep
                self.next_event = states.sending
                self.time = global_time
        elif self.next_event_time > global_time:
            if self.stat == states.sleep:
                self.battery_charge_update(global_time)
                self.time = global_time
                return self.stat, 0
            elif self.stat == states.sending:
                self.stat = states.collision
                self.time = global_time




        return self.stat, self.next_event_time


# ----- Battery current usage ------------------------
    def battery_charge_update(self, global_time):
        if self.stat == states.sleep:
            self.node_battery.bat_charge -= LoRa_time_Power.sleep_energy_consumption_curr(self.time, global_time)
        elif self.stat == states.sending:
            self.node_battery.bat_charge -= LoRa_time_Power.sending_data_energy_consumption_curr(self.TP)

# ----- send the message  ------------------------
    def send_msg(self, global_time):  # this method return -1 when node is dead and end time of send message otherwise
        if self.node_battery.bat_charge < LoRa_time_Power.sending_data_energy_consumption_curr(self.TP):
            self.stat = states.dead
            return -1  # -1 means cannot send a message because node has been dead
        else:
            self.battery_charge_update(global_time)
            self.next_event_time = LoRa_time_Power.time_on_air + LoRa_time_Power.Ack_time_on_air  # here node time update to end of sending message
            self.next_event = states.sleep
            return 0  # 0 means sent was successful















