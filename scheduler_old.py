# -
import os 
import csv
from gateway import Gateway_Aloha
from Channel import Channel
from Node import NodeAloha
from Node import Node_states


def make_ready_nodes(nodes_list, now_time, ready_list):
    ready_list.clear()
    for index in range(len(nodes_list)):
        if nodes_list[index].next_event_time == now_time:
            ready_list.append(nodes_list[index].node_id)


# -------------  start of scheduling ---------------------
# new 3 nodes
#No_nodes = 9

# making nodes ----------------
nodes = []
# get nodes from a csv file
dir = r'D:\Course\PHD\UT\Papers\LoRa\Tool\Python\TimeCompTDMA_Aloha\TaskGenerator\TaskGenerator_same_exeTime\sampleTasks-SG0.1'
files = os.listdir(dir)
file = '\\001-5_tasks_util_0.05_1.csv'
in_path = dir + file 
with open(in_path, 'r') as input_nodes:
    node_reader = csv.reader(input_nodes, delimiter=',')
    No_nodes = 0
    for row in node_reader:
        if len(row) == 0:
            break
        N_id = int(row[0])
        exe = int(float(row[5]))
        period = int(row[6])
        nodes.append(NodeAloha(N_id, period, exe))
        No_nodes += 1

# nodes.append(NodeAloha(0, 1028, 20))  # (node_id, period in ms, exe in ms is based on 50B payload and 16B ack time)
# nodes.append(NodeAloha(1, 1270, 20))
# nodes.append(NodeAloha(2, 1452, 20))


No_nodes = len(nodes)
# making channel ---------------
ch = Channel(1)

# making gateway ---------------
gw = Gateway_Aloha(1)

nodes_life_state = [True for j in range(len(nodes))]  # this list present life state of nodes
Next_active_nodes = []  # this maintain list of next active nodes which must be triggered
Nodes_next_event_time_list = [nodes[i].next_event_time for i in range(No_nodes)]
nodes_output_list = {}

time_now = 0

# 1 - for all active nodes send clock
while False not in nodes_life_state:  # main loop until network life time
    # ---- modify simulation time of system
    time_now = min(Nodes_next_event_time_list)  # this variable maintain time of network
    # ----------  operation in nodes  ----------------
    # --- nodes send output to channel
    make_ready_nodes(nodes, time_now, Next_active_nodes)
    ch.clear_channel()
    for i in Next_active_nodes:
        nodes[i].wakeup(time_now)
        Nodes_next_event_time_list[i] = nodes[i].next_event_time
        node_out = nodes[i].output_signal
        ch.rec_from_node(i, node_out)
    for j in range(No_nodes):
        nodes_life_state[j] = nodes[j].alive

    # ----------- operation in channel ----------------
    # --- channel sends output of nodes to gateway
    nodes_to_channel = ch.send_to_gw()

    # ----------- operation in gateway ----------------
    # --- gateway receive output of nodes from channel
    gw.update_node_sent_and_get_respond(nodes_to_channel)
    # --- gateway make ack of previous messages
    ack_res = gw.ack_result()

    # ----------- operation in channel ----------------
    # --- channel receives ack output of nodes from gateway
    ch.rec_from_gw(ack_res)
    channel_ack_to_nodes = ch.send_to_node()
    for node_id in channel_ack_to_nodes:  # these node are those in receive.stop state and are getting sleep state
        ack_result = channel_ack_to_nodes[node_id]
        nodes[node_id].ack_int(ack_result)
        # plus_time = nodes[node_id].next_event_time_plus(time_now, Node_states.sleep)
        # nodes[node_id].next_event_time = time_now + plus_time
        # Nodes_next_event_time_list[node_id] = nodes[node_id].next_event_time

collision_list = []
correct_msg_list = []
Nodes_time = []
Nodes_life_time = []


for i in range(No_nodes):
    collision_list.append(nodes[i].total_collision_occurred)
    correct_msg_list.append(nodes[i].total_correct_sent_msg)
    Nodes_time.append("{:.2f}".format(nodes[i].time / 86400000))
    Nodes_life_time.append("{:.2f}".format(nodes[i].total_life))


out_path = dir + "\\Aloha_out\\out1.csv"
# with open("D:\\Course\\PHD\\UT\\Papers\\LoRa\\Tool\\Python\\TimeCompTDMA_Aloha\\System\\Aloha_output_nodes.csv", 'w') as output_nodes:
with open(out_path, 'w') as output_nodes:
    node_writer = csv.writer(output_nodes, delimiter=',')
    header = ['node id', 'total No of correct sent msg', 'life time of node', 'No of collision ']
    print("header is : ", header)
    node_writer.writerow(header)
    row = []
    for i in range(len(nodes)):
        row.append(i)
        row.append(correct_msg_list[i])
        row.append(Nodes_time[i])
        row.append(collision_list[i])
        node_writer.writerow(row)
        row.clear()




print("number of collisions are: ", collision_list)
print("number of correct messages by nodes are: ", correct_msg_list)
print("life time of nodes are: ", Nodes_life_time)
print("state of nodes are : ", nodes_life_state)
print("time of nodes are : ", Nodes_time)
print("time of simulation is : ", time_now)

