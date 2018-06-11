# GLOBAL VARIABLES AND FUNCTIONS
import rosgraph
import rosnode
import rospy
import rosmsg
from rosmsg import *

from opcua import ua

object_id_dict = {'bool': ua.ObjectIds.Boolean,
                  'byte': ua.ObjectIds.Byte,
                  'int': ua.ObjectIds.Int16,
                  'int8': ua.ObjectIds.SByte,
                  'uint8': ua.ObjectIds.Byte,
                  'int16': ua.ObjectIds.Int16,
                  'uint16': ua.ObjectIds.UInt16,
                  'int32': ua.ObjectIds.Int32,
                  'uint32': ua.ObjectIds.UInt32,
                  'int64': ua.ObjectIds.Int64,
                  'uint64': ua.ObjectIds.UInt64,
                  'float': ua.ObjectIds.Float,
                  'float32': ua.ObjectIds.Float,
                  'float64': ua.ObjectIds.Float,
                  'double': ua.ObjectIds.Double,
                  'string': ua.ObjectIds.String,
                  'str': ua.ObjectIds.String,
                  'array': ua.ObjectIds.Enumeration,
                  'Time': ua.ObjectIds.Time,
                  'time': ua.ObjectIds.Time}


def get_object_ids(type_name):
    if type_name == 'int16':
        rospy.logwarn('Int16??')
    dv = object_id_dict.get(type_name, None)
    if dv is None:
        rospy.logerr('Can not create type with name ' + type_name)
    return dv


def get_ros_packages():
    """
    same as the command line 'rosmsg packages'
    :return: ROS messages as a list
    """
    return sorted([x for x in iterate_packages(rospkg.RosPack(), MODE_MSG)])


def get_ros_msg():
    """
    same as the command line 'rosmsg list'
    :return: list of [ros package, message] pairs
    """
    ret = []
    ros_packages = get_ros_packages()
    for (p, directory) in ros_packages:
        for file_name in getattr(rosmsg, '_list_types')(directory, 'msg', MODE_MSG):
            ret.append(p + '/' + file_name)
    return ret


def get_ros_package(package_name):
    return list_types(package_name, mode=MODE_MSG)


def get_ros_msg_md5(package_name):
    return rosmsg_md5(MODE_MSG, package_name)


def next_name(hierarchy, index_of_last_processed):
    """
    Returns the hierarchy as one string from the first remaining part on.
    :param hierarchy:
    :param index_of_last_processed:
    :return:
    """
    try:
        output = ''
        counter = index_of_last_processed + 1
        while counter < len(hierarchy):
            output += hierarchy[counter]
            counter += 1
        return output
    except Exception as ex:
        rospy.logerr('Error encountered ', ex)


def rosnode_cleanup():
    _, unpinged = rosnode.rosnode_ping_all()
    if unpinged:
        master = rosgraph.Master(rosnode.ID)
        # noinspection PyTypeChecker
        rosnode.cleanup_master_blacklist(master, unpinged)


def correct_type(node, type_message):
    data_value = node.get_data_value()
    result = node.get_value()
    if isinstance(data_value, ua.DataValue):
        if type_message.__name__ in ('float', 'double'):
            return float(result)
        if type_message.__name__ == 'int':
            return int(result) & 0xff
        if type_message.__name__ in ('Time', 'Duration'):
            return rospy.Time(result)
    else:
        rospy.logerr("can't convert: " + str(node.get_data_value.Value))
        return None


# created UA nodes in UA Server, only the ROS related nodes
package_node_created = {}
# retrieved ROS package names
packages = []

# ros messages  'message' --> nodeVariableType
messageExportPath = 'message.xml'
new_messageExportPath = 'new_message.xml'
messageNode = {}

# ros_messages 'message' --> nodeDataType
dataTypeNode = {}

# ros Topics  'topic_name' --> 'topic_node'
topicNode = {}

# BaseDataType
# BaseDataVariableType

# baseDataVariableType_node = ;

if __name__ == '__main__':
    print(get_ros_msg())
