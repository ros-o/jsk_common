#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Furushchev <furushchev@jsk.imi.i.u-tokyo.ac.jp>

from dynamic_reconfigure.client import Client
import rospy
import unittest
from std_msgs.msg import String


class TestStealthRelay(unittest.TestCase):
    def out_callback(self, msg):
        self.out_msg_count += 1

    def monitor_callback(self, msg):
        self.monitor_msg_count += 1

    def test_stealth_relay(self):
        self.out_msg_count = 0
        self.monitor_msg_count = 0
        sub_out = rospy.Subscriber("/stealth_relay/output", String,
                                   self.out_callback, queue_size=1)

        rate = rospy.Rate(1)
        try:
            while not rospy.is_shutdown() and sub_out.get_num_connections() == 0:
                rate.sleep()
        except Exception as e:
            rospy.logerr('{}'.format(e))
            rospy.logerr("output topic of stealth relay was not advertised")
            sys.exit(1)

        rospy.sleep(5)
        self.assertEqual(self.out_msg_count, 0,
                         "stealth relay node published message unexpectedly.")

        sub_monitor = rospy.Subscriber("/original_topic/relay", String,
                                       self.monitor_callback, queue_size=1)
        rospy.loginfo("subscribed monitor topic")

        # wait self.monitor_msg_count
        try:
            while not rospy.is_shutdown() and self.monitor_msg_count == 0:
                rate.sleep()
        except Exception as e:
            rospy.logerr('{}'.format(e))
            rospy.logerr("monitoring topic is not published")
            sys.exit(1)

        try:
            while not rospy.is_shutdown() and self.out_msg_count == 0:
                rate.sleep()
        except Exception as e:
            rospy.logerr('{}'.format(e))
            rospy.logerr("monitoring topic is not published")
            sys.exit(1)
        sub_monitor.unregister()
        rospy.loginfo("unsubscribed monitor topic")
        self.assertGreater(self.out_msg_count, 0,
                           "output topic of stealth relay was not published even monitoring topic is published")
        cnt = self.out_msg_count
        rospy.sleep(5)

        self.assertLess(abs(cnt - self.out_msg_count), 40,
                        "It seems stealth relay node did not stop subscribing even if monitoring topic is not published any more")

        # FIXME: updating dynamic reconfigure never ends on travis?
        # client = Client("stealth_relay", timeout=3)
        # rospy.loginfo("setting 'enable_monitor' to False")
        # client.update_configuration({'enable_monitor': False, 'monitor_topic': ''})
        # cnt = self.out_msg_count
        # rospy.sleep(5)
        # self.assertGreater(abs(self.out_msg_count - cnt), 40,
        #                    "No output topic published even if 'enable_monitor' is set to False")


if __name__ == '__main__':
    import rostest
    rospy.init_node("test_stealth_relay")
    rostest.rosrun("jsk_topic_tools", "test_stealth_relay", TestStealthRelay)
