# !/usr/bin/env python
# thanks to https://github.com/ros-visualization/rqt_common_plugins/blob/groovy-devel/rqt_action/src/rqt_action/action_plugin.py
import random
from pydoc import locate

import actionlib
import rospy
from opcua import ua, common
from opcua import uamethod

import ros_server
import ros_topics


def present_in_actions_dict(actionsdict, name):
    for opc_name in actionsdict:
        if opc_name == name:
            return True

    return False


def get_correct_name(topic_name):
    splits = topic_name.split("/")
    counter = 0
    counter2 = 0
    result = ""
    while counter < len(splits):
        if splits[-1] == splits[counter] and not counter == 1:
            while counter2 <= counter - 1:
                if counter2 != counter - 1:
                    result += splits[counter2] + '/'
                else:
                    result += splits[counter2]
                counter2 += 1
            return result
        counter += 1


class OpcUaROSAction:
    def __init__(self, server, parent, idx, name):
        self.server = server
        self.idx = idx
        self.name = name
        pkg = rospy.get_param("/rosopcua/actionpackage")
        msg_name = self.get_msg_name()
        class_name = msg_name.replace("_", "")
        goal_name = self.get_goal_name()
        try:
            actionspec = locate(pkg + "." + msg_name)
            goalspec = locate(pkg + "." + goal_name)
            self.goal_class = getattr(goalspec, goal_name.replace("_", ""))
            self.client = actionlib.SimpleActionClient(self.get_ns_name(), getattr(actionspec, class_name))
            self.client.wait_for_server()
            self.parent = self.recursive_create_objects(name, idx, parent)
            self.result = self.parent.add_object(ua.NodeId("result", self.parent.nodeid.NamespaceIndex, ua.NodeIdType.String),
                                                 ua.QualifiedName("result", parent.nodeid.NamespaceIndex))
            self.result_node = ros_topics._create_node_with_type(self.result, self.idx, "result_value", "result_value", "string", -1)

            self.result_node.set_value(repr("No goal sent yet"))
            self.goal = self.parent.add_object(ua.NodeId("goal", self.parent.nodeid.NamespaceIndex, ua.NodeIdType.String),
                                      ua.QualifiedName("goal", parent.nodeid.NamespaceIndex))

            # if self.goal_class._slot_types is not None:
            #     self.goal_node = self.goal.add_method(idx, "send_goal", self.send_goal, self.goal_class._slot_types, [])
            # else:
            self.goal_node = self.goal.add_method(idx, "send_goal", self.send_goal, [], [])

        except (ValueError, TypeError, AttributeError) as e:
            rospy.logerr("Error while creating Action Objects %s", e)
            return

    def recursive_create_objects(self, name, idx, parent):
        hierachy = name.split('/')
        if len(hierachy) == 0 or len(hierachy) == 1:
            return parent
        for name in hierachy:
            if name != '':
                try:
                    nodewithsamename = self.server.get_node(ua.NodeId(name, idx))
                    if nodewithsamename is not None and nodewithsamename.get_parent() == parent:
                        return self.recursive_create_objects(ros_server.nextname(hierachy, hierachy.index(name)), idx, nodewithsamename)
                    else:
                        newparent = parent.add_object(
                            ua.NodeId(name + str(random.randint(0, 10000)), parent.nodeid.NamespaceIndex, ua.NodeIdType.String),
                            ua.QualifiedName(name, parent.nodeid.NamespaceIndex))
                        return self.recursive_create_objects(ros_server.nextname(hierachy, hierachy.index(name)), idx, newparent)
                except IndexError, common.uaerrors.UaError:
                    newparent = parent.add_object(
                        ua.NodeId(name, parent.nodeid.NamespaceIndex, ua.NodeIdType.String),
                        ua.QualifiedName(name, parent.nodeid.NamespaceIndex))
                    return self.recursive_create_objects(ros_server.nextname(hierachy, hierachy.index(name)), idx, newparent)
        return parent

    def get_msg_name(self):
        return "_" + str(self.name.split("/")[-1]).capitalize() + "Action"

    def get_goal_name(self):
        return "_" + str(self.name.split("/")[-1]).capitalize() + "Goal"

    def get_ns_name(self):
        return str(self.name.split("/")[1])

    @uamethod
    def send_goal(self, parent, *inputs):
        print("sending goal")
        try:
            self.client.send_goal(self.goal_class())
            self.client.wait_for_result()
            self.result_node.set_value(repr(self.client.get_result()))
        except rospy.ROSException as e:
            rospy.logwarn(e)

    def recursive_delete_items(self, item):
        self.client.cancel_all_goals()
        for child in item.get_children():
            self.recursive_delete_items(child)
            self.server.delete_nodes([child])
        self.server.delete_nodes([self.result, self.result_node, self.goal_node, self.goal, self.parent])
        ros_server.own_rosnode_cleanup()


def refresh_dict(namespace_ros, actionsdict, server, idx_actions):
    topics = rospy.get_published_topics(namespace_ros)
    tobedeleted = []
    for actionNameOPC in actionsdict:
        found = False
        for topicROS, topic_type in topics:
            if actionNameOPC in topicROS:
                found = True
        if not found:
            actionsdict[actionNameOPC].recursive_delete_items(actionsdict[actionNameOPC].parent)
            tobedeleted.append(actionNameOPC)
            ros_server.own_rosnode_cleanup()
    for name in tobedeleted:
        del actionsdict[name]
