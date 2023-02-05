
from Node import ack_stat, output_stat
#from scheduler import No_nodes
from enum import Enum

class channel_stat(Enum):
    free = 0  # when just one signal is on air
    busy = 1  # when more than one signal is on air


class collision(Enum):
    no_col = 0
    col = 1


# class abstract_node(object):
#     def __init__(self, node_id = 0, sending_stat = output_stat.nothing, col_stat = collision.no_col):
#         self.node_id = node_id
#         self.sending_stat = sending_stat
#         self.col_stat = col_stat
#         self.channel = channel_stat.free

# No_nodes = 10


class Gateway_Aloha(object):
    # node = [0, output_stat.nothing, collision.no_col, False]  # [node_id , sent_output_status, collision_status, ack_set]

    def __init__(self, GW_id, No_nodes):
        self.GW_id = GW_id
        self.nodes = [[i, output_stat.nothing, collision.no_col, False] for i in range(No_nodes)]
        self.channel_status = channel_stat.free
        self.ack_nodes = {}  # ack of nodes in dictionary data structure {i:ack}
        self.No_nodes = No_nodes

    def update_node_sent_and_get_respond(self, channel_out):  # channel_out is a dictionary like {i:"out"} node_id, sent output
        for key in channel_out:
            self.nodes[key][1] = channel_out[key]
            #self.nodes[index][3] = False  # ack is not set yet
        self.channel_update()
        self.col_detection()
        self.ack_nodes.clear()
        for key in channel_out:
            if self.nodes[key][1] == output_stat.receive_stop:
                self.ack_nodes[key] = self.ack_making(key)

    def channel_update(self):
        chan_sent_nodes = 0
        for i in range(self.No_nodes):
            if self.nodes[i][1] == (output_stat.send_start or output_stat.receive_start):
                chan_sent_nodes += 1
            if chan_sent_nodes > 1:
                self.channel_status = channel_stat.busy
                break
        if chan_sent_nodes <= 1:
            self.channel_status = channel_stat.free

    def col_detection(self):
        for i in range(self.No_nodes):
            if self.nodes[i][1] == (output_stat.send_start or output_stat.receive_start):
                if self.nodes[i][3] == False:
                    if self.channel_status == channel_stat.busy:
                        self.nodes[i][2] = collision.col
                        self.nodes[i][3] = True  # node ack is set
                    # else:
                    #     self.nodes[i][2] = collision.no_col

    def ack_making(self, node_id):
        self.nodes[node_id][3] = False
        if self.nodes[node_id][2] == collision.col:
            out_ack = ack_stat.nak
        else:
            out_ack = ack_stat.ack
        self.nodes[node_id][2] = collision.no_col
        return out_ack

    def ack_result(self):
        return self.ack_nodes


