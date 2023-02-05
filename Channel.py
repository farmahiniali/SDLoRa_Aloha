

# this module (in one direction) get the output of nodes and send them to gateway and
# in opposite direction get the gateway output and send it to appropriate nodes

from Node import output_stat, ack_stat


class Channel(object):
    def __init__(self, channel_id):
        self.channel_id = channel_id
        self.toggled_node_list = {}
        self.toggled_ack_list = {}


    def clear_channel(self):
        self.toggled_node_list.clear()

    def rec_from_node(self, node_id, output):  # channel receives node_id and output from nodes
        self.toggled_node_list[node_id] = output

    def send_to_gw(self):
        return self.toggled_node_list

    def rec_from_gw(self, node_ack_res):  # node_ack_res is a dictionary form gateway
        self.toggled_ack_list.clear()
        self.toggled_ack_list = node_ack_res.copy()

    def send_to_node(self):
        return self.toggled_ack_list

