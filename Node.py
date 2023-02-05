import LoRa_time_Power 
import random
from enum import Enum


# ************   constants and definitions  *******************
max_collision_allowed = 3


# ************   end of definitions    ************************


class Node_states(Enum):
    sleep = 1
    sending = 2
    receiving = 3
    receive_stop = 4
    dead = 5

class ack_stat(Enum):
    ack = 0
    nak = 1
    time_out = 2
    nothing = 3

class output_stat(Enum):
    nothing = 0
    send_start = 1
    receive_start = 2
    receive_stop = 3


class NodeAloha(object):
    def __init__(self, node_id, node_period, exe_time):
        # TP is 17 as a default
        self.node_id = node_id
        self.node_period = node_period
        self.exe_time = exe_time
        self.alive = True
        self.TP = 17
        self.BW = 125000
        self.SF = 7
        self.arrival_time = random.randrange(0, node_period)  #this is the first sending time
        self.ack = ack_stat.ack
        self.collision_count_in_one_period = 0  # this number can be up to 3
        self.last_period = self.arrival_time
        self.total_collision_occurred = 0
        self.total_correct_sent_msg = 0
        self.total_life = 0  # this variable is in days


        self.node_battery = LoRa_time_Power.Battery(100, 3)
        self.time = 0
        # self.next_event = Node_states.sending # this property will only assign with time trigger
        self.stat = Node_states.sleep  # this property will only assign with time trigger
        self.next_event_time = self.arrival_time  # this property will assign with sens_msg method
        self.output_signal = output_stat.nothing


# ----- wake up method ----------- Input interface -------------------
    def wakeup(self, global_time):
        # if global_time == self.next_event_time:
        if self.stat == Node_states.dead or self.alive == False:
            return -1
        elif self.stat == Node_states.sleep:
            self.total_life = float(global_time/(24 * 60 * 60 * 1000))
            if self.node_battery.bat_charge < LoRa_time_Power.sending_data_energy_consumption_curr(self.TP) + \
                    LoRa_time_Power.receiving_energy_consumption_curr(self.BW):
                self.alive = False
                nx_t_plus = self.next_event_time_plus(global_time, Node_states.dead)
                self.node_modify(global_time, Node_states.dead, nx_t_plus, output_stat.nothing)
            else:
                nx_t_plus = self.next_event_time_plus(global_time, Node_states.sending)
                self.node_modify(global_time, Node_states.sending, nx_t_plus, output_stat.send_start)
        elif self.stat == Node_states.sending:
            self.total_life = float(global_time / (24 * 60 * 60 * 1000))
            nx_t_plus = self.next_event_time_plus(global_time, Node_states.receiving)
            self.node_modify(global_time, Node_states.receiving, nx_t_plus, output_stat.receive_start)
        elif self.stat == Node_states.receiving:
            self.total_life = float(global_time / (24 * 60 * 60 * 1000))
            nx_t_plus = self.next_event_time_plus(global_time, Node_states.receive_stop)
            self.node_modify(global_time, Node_states.receive_stop, nx_t_plus, output_stat.receive_stop)
        elif self.stat == Node_states.receive_stop:
            self.total_life = float(global_time / (24 * 60 * 60 * 1000))
            nx_t_plus = self.next_event_time_plus(global_time, Node_states.sleep)
            self.node_modify(global_time, Node_states.sleep, nx_t_plus, output_stat.nothing)


# ------ ack interface -------------- Input interface -----------------
    def ack_int(self, ack_resp):
        self.ack = ack_resp
        if ack_resp == ack_stat.ack:
            self.collision_count_in_one_period = 0
            self.total_correct_sent_msg += 1
        elif ack_resp == ack_stat.nak or ack_resp == ack_stat.time_out:
            self.collision_count_in_one_period += 1
            self.total_collision_occurred += 1


# ----- Battery current usage ------------------------
    def battery_charge_update(self, global_time):
        if self.stat == Node_states.sleep:
            self.node_battery.bat_charge -= LoRa_time_Power.sleep_energy_consumption_curr(self.time, global_time)
        elif self.stat == Node_states.sending:
            self.node_battery.bat_charge -= LoRa_time_Power.sending_data_energy_consumption_curr(self.TP)
        elif self.stat == Node_states.receiving:
            self.node_battery.bat_charge -= LoRa_time_Power.receiving_energy_consumption_curr(self.BW)
        elif self.stat == Node_states.receive_stop:
            self.node_battery.bat_charge = self.node_battery.bat_charge


# ----- Modify node state --------------------------
    def node_modify(self, glob_time, stat, next_event_time_plus, output):
        self.battery_charge_update(glob_time)
        self.time = glob_time
        self.stat = stat
        self.next_event_time = glob_time + next_event_time_plus
        self.output_signal = output


# ------ Calculating next event time ------------------
    def next_event_time_plus(self, global_time, current_state):
        if current_state == Node_states.dead:
            return LoRa_time_Power.time_on_air
        elif current_state == Node_states.sending:
            return LoRa_time_Power.time_on_air
        elif current_state == Node_states.receiving:
            return LoRa_time_Power.ack_time_on_air
        elif current_state == Node_states.receive_stop:
            # return min([time_on_air, ack_time_on_air]) / 1000
            return 0
        elif current_state == Node_states.sleep:
            if self.ack == ack_stat.ack:
                plus_time = self.node_period - ((global_time - self.arrival_time) % self.node_period)
                return plus_time
            elif self.ack == (ack_stat.nak or ack_stat.time_out):
                backoff_time = self.backoff(global_time)
                return backoff_time




# ------ Back off time calculation ---------------------
    def backoff(self, glob_time):
        aligned_time = glob_time - ((glob_time - self.arrival_time) % self.node_period)
        col_count = self.collision_count_in_one_period - 1
        if col_count < max_collision_allowed - 1:
            back_off_offset = random.randrange(0, int(self.node_period/max_collision_allowed))
            back_off_time = (col_count * int(self.node_period / 3)) + back_off_offset
            return back_off_time
        else:
            self.collision_count_in_one_period = 0
            last_back_off = self.node_period - (glob_time - aligned_time)
            return last_back_off


# --------------------------------   TDMA Nodes -------------------------------------------------------------------

# class TDMA_Node_states(Enum):
#     sleep = 1
#     sending = 2
#     receiving = 3
#     receive_stop = 4
#     time_sync = 5
#     dead = 6


# class NodeTDMA(object):
#     def __init__(self, node_id, node_period, drift):
#         self.node_id = node_id
#         self.node_period = node_period
#         self.alive = True
#         self.TP = 17
#         self.BW = 125000
#         self.SF = 7
#         self.arrival_time = random.randrange(0, node_period)  #this is the first sending time
#         self.ack = ack_stat.ack
#         self.total_correct_sent_msg = 0
#         self.total_life = 0  # this variable is in days

#         self.node_battery = LoRa_time_Power.Battery(50, 3)
#         self.drift = drift
#         self.sync_flag = False
#         self.sync_time_add = 0
#         self.time = 0
#         self.stat = TDMA_Node_states.sleep  # this property will only assign with time trigger
#         self.next_event_time = self.arrival_time  # this property will assign with sens_msg method
#         self.output_signal = output_stat.nothing


#     def wakeup(self, global_time):
#         # if global_time == self.next_event_time:
#         if self.stat == TDMA_Node_states.dead or self.alive == False:
#             return -1
#         elif self.stat == TDMA_Node_states.sleep:
#             self.total_life = int(global_time/(24 * 60 * 60 * 1000))
#             if self.node_battery.bat_charge < LoRa_time_Power.sending_data_energy_consumption_curr(self.TP) + \
#                     LoRa_time_Power.receiving_energy_consumption_curr(self.BW):
#                 self.alive = False
#                 nx_t_plus = self.next_event_time_plus(global_time, TDMA_Node_states.dead)
#                 self.node_modify(global_time, TDMA_Node_states.dead, nx_t_plus, output_stat.nothing)
#             else:
#                 if self.sync_flag == False:
#                     nx_t_plus = self.next_event_time_plus(global_time, TDMA_Node_states.sending)
#                     self.node_modify(global_time, TDMA_Node_states.sending, nx_t_plus, output_stat.send_start)
#                 else:
#                     nx_t_plus = self.next_event_time_plus(global_time, TDMA_Node_states.receiving)
#                     self.node_modify(global_time, TDMA_Node_states.receiving, nx_t_plus, output_stat.receive_start)

#         elif self.stat == TDMA_Node_states.sending:
#             self.total_life = int(global_time / (24 * 60 * 60 * 1000))
#             nx_t_plus = self.next_event_time_plus(global_time, TDMA_Node_states.receiving)
#             self.node_modify(global_time, TDMA_Node_states.receiving, nx_t_plus, output_stat.receive_start)
#         elif self.stat == TDMA_Node_states.receiving:
#             self.total_life = int(global_time / (24 * 60 * 60 * 1000))
#             nx_t_plus = self.next_event_time_plus(global_time, TDMA_Node_states.receive_stop)
#             self.node_modify(global_time, TDMA_Node_states.receive_stop, nx_t_plus, output_stat.receive_stop)
#         elif self.stat == TDMA_Node_states.receive_stop:
#             self.total_life = int(global_time / (24 * 60 * 60 * 1000))
#             nx_t_plus = self.next_event_time_plus(global_time, TDMA_Node_states.sleep)
#             self.node_modify(global_time, TDMA_Node_states.sleep, nx_t_plus, output_stat.nothing)

#     def next_event_time_plus(self, global_time, current_state):
#         if current_state == TDMA_Node_states.dead:
#             return LoRa_time_Power.time_on_air
#         elif current_state == TDMA_Node_states.sending:
#             return LoRa_time_Power.time_on_air
#         elif current_state == TDMA_Node_states.receiving:
#             return LoRa_time_Power.ack_time_on_air
#         elif current_state == TDMA_Node_states.receive_stop:
#             return 0
#         elif current_state == Node_states.sleep:
#             if self.sync_flag == True :
#                 return self.sync_time_add
#             else:
#                 plus_time = self.node_period - ((global_time - self.arrival_time) % self.node_period)
#                 return plus_time

#     def battery_charge_update(self, global_time):
#         if self.stat == TDMA_Node_states.sleep:
#             self.node_battery.bat_charge -= LoRa_time_Power.sleep_energy_consumption_curr(self.time, global_time)
#         elif self.stat == TDMA_Node_states.sending:
#             self.node_battery.bat_charge -= LoRa_time_Power.sending_data_energy_consumption_curr(self.TP)
#         elif self.stat == TDMA_Node_states.receiving:
#             self.node_battery.bat_charge -= LoRa_time_Power.receiving_energy_consumption_curr(self.BW)

#     def node_modify(self, glob_time, stat, next_event_time_plus, output):
#         self.battery_charge_update(glob_time)
#         self.time = glob_time
#         self.stat = stat
#         self.next_event_time = glob_time + next_event_time_plus
#         self.output_signal = output

#     def sync_time(self, sync_flag, sync_addition_time):
#         self.sync_flag = sync_flag
#         self.sync_time_add = sync_addition_time




