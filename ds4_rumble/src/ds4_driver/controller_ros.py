from .controller import Controller

import rospy
from sensor_msgs.msg import BatteryState
from sensor_msgs.msg import Joy
from sensor_msgs.msg import JoyFeedback
from sensor_msgs.msg import JoyFeedbackArray
from sensor_msgs.msg import Imu
from ds4_driver.msg import Feedback
from ds4_driver.msg import Report
from ds4_driver.msg import Status

import copy
import math


class ControllerRos(Controller):
    last_status=Status()

    def __init__(self):
        super(ControllerRos, self).__init__()
        #获取是否使用ros标准消息类型的参数
        self.use_standard_msgs = rospy.get_param('~use_standard_msgs', False)
        #获取摇杆死区大小的参数
        self.deadzone = rospy.get_param('~deadzone', 0.1)
        self.frame_id = rospy.get_param('~frame_id', 'ds4')
        self.imu_frame_id = rospy.get_param('~imu_frame_id', 'ds4_imu')
        # Only publish Joy messages on change
        self._autorepeat_rate = rospy.get_param('~autorepeat_rate', 0)
        self._prev_joy = None

        # Use ROS-standard messages (like sensor_msgs/Joy)
        if self.use_standard_msgs:
            self.pub_report = rospy.Publisher('raw_report', Report, queue_size=1)
            self.pub_battery = rospy.Publisher('battery', BatteryState, queue_size=1)
            self.pub_joy = rospy.Publisher('joy', Joy, queue_size=1)
            self.pub_imu = rospy.Publisher('imu', Imu, queue_size=1)
            self.sub_feedback = rospy.Subscriber('set_feedback', JoyFeedbackArray, self.cb_joy_feedback, queue_size=1)

            if self._autorepeat_rate != 0:
                period = 1.0 / self._autorepeat_rate
                rospy.Timer(rospy.Duration.from_sec(period), self.cb_joy_pub_timer)
        else:
            #声明发布按键状态的话题
            self.pub_status = rospy.Publisher('status', Status, queue_size=1)
            #订阅反馈控制的话题
            self.sub_feedback = rospy.Subscriber('set_feedback', Feedback, self.cb_feedback, queue_size=1)


        #获取震动配置参数
        self.rumble_button_dpad_up_t     = rospy.get_param('~button_dpad_up/duration', 0.0)
        self.rumble_button_dpad_up_b     = rospy.get_param('~button_dpad_up/rumble_big', 0.0)
        self.rumble_button_dpad_up_s     = rospy.get_param('~button_dpad_up/rumble_small', 0.0)

        self.rumble_button_dpad_down_t   = rospy.get_param('~button_dpad_down/duration', 0.0)
        self.rumble_button_dpad_down_b   = rospy.get_param('~button_dpad_down/rumble_big', 0.0)
        self.rumble_button_dpad_down_s   = rospy.get_param('~button_dpad_down/rumble_small', 0.0)

        self.rumble_button_dpad_left_t   = rospy.get_param('~button_dpad_left/duration', 0.0)
        self.rumble_button_dpad_left_b   = rospy.get_param('~button_dpad_left/rumble_big', 0.0)
        self.rumble_button_dpad_left_s   = rospy.get_param('~button_dpad_left/rumble_small', 0.0)

        self.rumble_button_dpad_right_t  = rospy.get_param('~button_dpad_right/duration', 0.0)
        self.rumble_button_dpad_right_b  = rospy.get_param('~button_dpad_right/rumble_big', 0.0)
        self.rumble_button_dpad_right_s  = rospy.get_param('~button_dpad_right/rumble_small', 0.0)

        self.rumble_button_cross_t       = rospy.get_param('~button_cross/duration', 0.0)
        self.rumble_button_cross_b       = rospy.get_param('~button_cross/rumble_big', 0.0)
        self.rumble_button_cross_s       = rospy.get_param('~button_cross/rumble_small', 0.0)

        self.rumble_button_circle_t      = rospy.get_param('~button_circle/duration', 0.0)
        self.rumble_button_circle_b      = rospy.get_param('~button_circle/rumble_big', 0.0)
        self.rumble_button_circle_s      = rospy.get_param('~button_circle/rumble_small', 0.0)

        self.rumble_button_square_t      = rospy.get_param('~button_square/duration', 0.0)
        self.rumble_button_square_b      = rospy.get_param('~button_square/rumble_big', 0.0)
        self.rumble_button_square_s      = rospy.get_param('~button_square/rumble_small', 0.0)

        self.rumble_button_triangle_t    = rospy.get_param('~button_triangle/duration', 0.0)
        self.rumble_button_triangle_b    = rospy.get_param('~button_triangle/rumble_big', 0.0)
        self.rumble_button_triangle_s    = rospy.get_param('~button_triangle/rumble_small', 0.0)

        self.rumble_button_l1_t          = rospy.get_param('~button_l1/duration', 0.0)
        self.rumble_button_l1_b          = rospy.get_param('~button_l1/rumble_big', 0.0)
        self.rumble_button_l1_s          = rospy.get_param('~button_l1/rumble_small', 0.0)

        self.rumble_button_l2_t          = rospy.get_param('~button_l2/duration', 0.0)
        self.rumble_button_l2_b          = rospy.get_param('~button_l2/rumble_big', 0.0)
        self.rumble_button_l2_s          = rospy.get_param('~button_l2/rumble_small', 0.0)

        self.rumble_button_l3_t          = rospy.get_param('~button_l3/duration', 0.0)
        self.rumble_button_l3_b          = rospy.get_param('~button_l3/rumble_big', 0.0)
        self.rumble_button_l3_s          = rospy.get_param('~button_l3/rumble_small', 0.0)

        self.rumble_button_r1_t          = rospy.get_param('~button_r1/duration', 0.0)
        self.rumble_button_r1_b          = rospy.get_param('~button_r1/rumble_big', 0.0)
        self.rumble_button_r1_s          = rospy.get_param('~button_r1/rumble_small', 0.0)

        self.rumble_button_r2_t          = rospy.get_param('~button_r2/duration', 0.0)
        self.rumble_button_r2_b          = rospy.get_param('~button_r2/rumble_big', 0.0)
        self.rumble_button_r2_s          = rospy.get_param('~button_r2/rumble_small', 0.0)

        self.rumble_button_r3_t          = rospy.get_param('~button_r3/duration', 0.0)
        self.rumble_button_r3_b          = rospy.get_param('~button_r3/rumble_big', 0.0)
        self.rumble_button_r3_s          = rospy.get_param('~button_r3/rumble_small', 0.0)

        self.rumble_button_share_t       = rospy.get_param('~button_share/duration', 0.0)
        self.rumble_button_share_b       = rospy.get_param('~button_share/rumble_big', 0.0)
        self.rumble_button_share_s       = rospy.get_param('~button_share/rumble_small', 0.0)

        self.rumble_button_options_t     = rospy.get_param('~button_options/duration', 0.0)
        self.rumble_button_options_b     = rospy.get_param('~button_options/rumble_big', 0.0)
        self.rumble_button_options_s     = rospy.get_param('~button_options/rumble_small', 0.0)

        self.rumble_button_trackpad_t    = rospy.get_param('~button_trackpad/duration', 0.0)
        self.rumble_button_trackpad_b    = rospy.get_param('~button_trackpad/rumble_big', 0.0)
        self.rumble_button_trackpad_s    = rospy.get_param('~button_trackpad/rumble_small', 0.0)

        self.rumble_button_ps_t          = rospy.get_param('~button_ps/duration', 0.0)
        self.rumble_button_ps_b          = rospy.get_param('~button_ps/rumble_big', 0.0)
        self.rumble_button_ps_s          = rospy.get_param('~button_ps/rumble_small', 0.0)

    #震动控制函数 传入参数为当前的按键状态
    def rumble_ctr(self, status):
        #定义震动控制消息对象
        fb = Feedback()
        fb.set_rumble = True
        #每次按下只震动一次
        if self._once_judge(status.button_dpad_up,self.last_status.button_dpad_up) :
            #将对应按键震动反馈参数对应赋值 rumble_big对应手柄握持部分的振动器，rumble_small对应触摸板下方振动器，rumble_duration对应震动时长
            fb.rumble_big = self.rumble_button_dpad_up_b
            fb.rumble_small = self.rumble_button_dpad_up_s
            fb.rumble_duration = self.rumble_button_dpad_up_t
            #cb_feedback函数是实现按照参数调用震动控制的函数
            self.cb_feedback(fb)
        if self._once_judge(status.button_dpad_down,self.last_status.button_dpad_down) :
            fb.rumble_big = self.rumble_button_dpad_down_b
            fb.rumble_small = self.rumble_button_dpad_down_s
            fb.rumble_duration = self.rumble_button_dpad_down_t
            self.cb_feedback(fb)
        if self._once_judge(status.button_dpad_left,self.last_status.button_dpad_left) :
            fb.rumble_big = self.rumble_button_dpad_left_b
            fb.rumble_small = self.rumble_button_dpad_left_s
            fb.rumble_duration = self.rumble_button_dpad_left_t
            self.cb_feedback(fb)
        if self._once_judge(status.button_dpad_right,self.last_status.button_dpad_right) :
            fb.rumble_big = self.rumble_button_dpad_right_b
            fb.rumble_small = self.rumble_button_dpad_right_s
            fb.rumble_duration = self.rumble_button_dpad_right_t
            self.cb_feedback(fb)
        if self._once_judge(status.button_cross,self.last_status.button_cross) :
            fb.rumble_big = self.rumble_button_cross_b
            fb.rumble_small = self.rumble_button_cross_s
            fb.rumble_duration = self.rumble_button_cross_t
            self.cb_feedback(fb)
        if self._once_judge(status.button_circle,self.last_status.button_circle) :
            fb.rumble_big = self.rumble_button_circle_b
            fb.rumble_small = self.rumble_button_circle_s
            fb.rumble_duration = self.rumble_button_circle_t
            self.cb_feedback(fb)
        if self._once_judge(status.button_square,self.last_status.button_square) :
            fb.rumble_big = self.rumble_button_square_b
            fb.rumble_small = self.rumble_button_square_s
            fb.rumble_duration = self.rumble_button_square_t
            self.cb_feedback(fb)
        if self._once_judge(status.button_triangle,self.last_status.button_triangle) :
            fb.rumble_big = self.rumble_button_triangle_b
            fb.rumble_small = self.rumble_button_triangle_s
            fb.rumble_duration = self.rumble_button_triangle_t
            self.cb_feedback(fb)
        if self._once_judge(status.button_l1,self.last_status.button_l1) :
            fb.rumble_big = self.rumble_button_l1_b
            fb.rumble_small = self.rumble_button_l1_s
            fb.rumble_duration = self.rumble_button_l1_t
            self.cb_feedback(fb)
        if self._once_judge(status.button_l2,self.last_status.button_l2) :
            fb.rumble_big = self.rumble_button_l2_b
            fb.rumble_small = self.rumble_button_l2_s
            fb.rumble_duration = self.rumble_button_l2_t
            self.cb_feedback(fb)
        if self._once_judge(status.button_l3,self.last_status.button_l3) :
            fb.rumble_big = self.rumble_button_l3_b
            fb.rumble_small = self.rumble_button_l3_s
            fb.rumble_duration = self.rumble_button_l3_t
            self.cb_feedback(fb)
        if self._once_judge(status.button_r1,self.last_status.button_r1) :
            fb.rumble_big = self.rumble_button_r1_b
            fb.rumble_small = self.rumble_button_r1_s
            fb.rumble_duration = self.rumble_button_r1_t
            self.cb_feedback(fb)
        if self._once_judge(status.button_r2,self.last_status.button_r2) :
            fb.rumble_big = self.rumble_button_r2_b
            fb.rumble_small = self.rumble_button_r2_s
            fb.rumble_duration = self.rumble_button_r2_t
            self.cb_feedback(fb)
        if self._once_judge(status.button_r3,self.last_status.button_r3) :
            fb.rumble_big = self.rumble_button_r3_b
            fb.rumble_small = self.rumble_button_r3_s
            fb.rumble_duration = self.rumble_button_r3_t
            self.cb_feedback(fb)
        if self._once_judge(status.button_share,self.last_status.button_share) :
            fb.rumble_big = self.rumble_button_share_b
            fb.rumble_small = self.rumble_button_share_s
            fb.rumble_duration = self.rumble_button_share_t
            self.cb_feedback(fb)
        if self._once_judge(status.button_options,self.last_status.button_options) :
            fb.rumble_big = self.rumble_button_options_b
            fb.rumble_small = self.rumble_button_options_s
            fb.rumble_duration = self.rumble_button_options_t
            self.cb_feedback(fb)
        if self._once_judge(status.button_trackpad,self.last_status.button_trackpad) :
            fb.rumble_big = self.rumble_button_trackpad_b
            fb.rumble_small = self.rumble_button_trackpad_s
            fb.rumble_duration = self.rumble_button_trackpad_t
            self.cb_feedback(fb)
        if self._once_judge(status.button_ps,self.last_status.button_ps) :
            fb.rumble_big = self.rumble_button_ps_b
            fb.rumble_small = self.rumble_button_ps_s
            fb.rumble_duration = self.rumble_button_ps_t
            self.cb_feedback(fb)

        ControllerRos.last_status = status

    # 此函数为获取按键状态以及imu数据
    def cb_report(self, report):
        """
        Callback method for ds4drv event loop
        :param report:
        :return:
        """
        report_msg = Report()
        report_msg.header.frame_id = self.frame_id
        report_msg.header.stamp = rospy.Time.now()
        for attr in dir(report):
            if attr.startswith('_'):
                continue
            if hasattr(report_msg, attr):
                val = getattr(report, attr)
                setattr(report_msg, attr, val)
        # Fix (potentially) incorrect data reported from device
        imu_data = Controller.get_imu_data(report)
        report_msg.lin_acc_x = imu_data['lin_acc']['x']
        report_msg.lin_acc_y = imu_data['lin_acc']['y']
        report_msg.lin_acc_z = imu_data['lin_acc']['z']
        report_msg.ang_vel_x = imu_data['ang_vel']['x']
        report_msg.ang_vel_y = imu_data['ang_vel']['y']
        report_msg.ang_vel_z = imu_data['ang_vel']['z']

        status_msg = self._report_to_status_(report_msg, self.deadzone)
        status_msg.imu.header.frame_id = self.imu_frame_id

        if self.use_standard_msgs:
            battery_msg = self._status_to_battery_(status_msg)
            joy_msg = self._status_to_joy_(status_msg)
            imu_msg = self._status_to_imu_(status_msg)
            self.pub_report.publish(report_msg)
            self.pub_battery.publish(battery_msg)
            if self._prev_joy is None \
                    or joy_msg.axes != self._prev_joy.axes \
                    or joy_msg.buttons != self._prev_joy.buttons:
                self.pub_joy.publish(joy_msg)
            self.pub_imu.publish(imu_msg)

            self._prev_joy = joy_msg
        else:
            self.pub_status.publish(status_msg)

        self.rumble_ctr(status_msg)

    def cb_feedback(self, msg):
        """
        Callback method for ds4_driver/Feedback
        :param msg:
        :type msg: Feedback
        :return:
        """
        if self.device is None:
            return

        def to_int(v): return int(v * 255)
        #control函数为执行灯光与震动控制的函数
        self.control(
            # LED color
            led_red=to_int(msg.led_r) if msg.set_led else None,
            led_green=to_int(msg.led_g) if msg.set_led else None,
            led_blue=to_int(msg.led_b) if msg.set_led else None,
            # Rumble
            rumble_small=to_int(msg.rumble_small) if msg.set_rumble else None,
            rumble_big=to_int(msg.rumble_big) if msg.set_rumble else None,
            # Flash LED
            flash_on=to_int(msg.led_flash_on / 2.5) if msg.set_led_flash else None,
            flash_off=to_int(msg.led_flash_off / 2.5) if msg.set_led_flash else None,
        )

        # Timer to stop rumble
        # 按照定义的震动时长来下发停止震动的命令
        if msg.set_rumble and msg.rumble_duration != 0:
            rospy.Timer(rospy.Duration(msg.rumble_duration),
                        self.cb_stop_rumble,
                        oneshot=True)

    def cb_stop_rumble(self, event):
        try:
            self.control(rumble_small=0, rumble_big=0)
        except AttributeError:
            # The program exited and self.device was set to None
            pass

    def cb_joy_feedback(self, msg):
        """
        Callback method for sensor_msgs/JoyFeedbackArray
        The message contains the following feedback:
        LED0: red
        LED1: green
        LED2: blue
        RUMBLE0: rumble small
        RUMBLE1: rumble big
        :param msg:
        :type msg: JoyFeedbackArray
        :return:
        """
        feedback = Feedback()
        for jf in msg.array:
            if jf.type == JoyFeedback.TYPE_LED:
                feedback.set_led = True
                if jf.id == 0:
                    feedback.led_r = jf.intensity
                elif jf.id == 1:
                    feedback.led_g = jf.intensity
                elif jf.id == 2:
                    feedback.led_b = jf.intensity
            elif jf.type == JoyFeedback.TYPE_RUMBLE:
                feedback.set_rumble = True
                if jf.id == 0:
                    feedback.rumble_small = jf.intensity
                elif jf.id == 1:
                    feedback.rumble_big = jf.intensity

        self.cb_feedback(feedback)

    def cb_joy_pub_timer(self, _):
        if self._prev_joy is not None:
            self.pub_joy.publish(self._prev_joy)

    @staticmethod
    def _report_to_status_(report_msg, deadzone=0.05):
        status_msg = Status()
        status_msg.header = copy.deepcopy(report_msg.header)

        # Sticks (signs are flipped for consistency with other joypads)
        status_msg.axis_left_x = -ControllerRos._normalize_axis_(report_msg.left_analog_x, deadzone)
        status_msg.axis_left_y = -ControllerRos._normalize_axis_(report_msg.left_analog_y, deadzone)
        status_msg.axis_right_x = -ControllerRos._normalize_axis_(report_msg.right_analog_x, deadzone)
        status_msg.axis_right_y = -ControllerRos._normalize_axis_(report_msg.right_analog_y, deadzone)

        # Shoulder buttons
        status_msg.axis_l2 = report_msg.l2_analog / 255.0
        status_msg.axis_r2 = report_msg.r2_analog / 255.0

        # Buttons
        status_msg.button_dpad_up = report_msg.dpad_up
        status_msg.button_dpad_down = report_msg.dpad_down
        status_msg.button_dpad_left = report_msg.dpad_left
        status_msg.button_dpad_right = report_msg.dpad_right
        plug_attrs = [attr for attr in dir(report_msg) if attr.startswith('button_')]
        for attr in plug_attrs:
            val = getattr(report_msg, attr)
            setattr(status_msg, attr, val)

        # IMU (X: right, Y: up, Z: towards user)
        status_msg.imu.header = copy.deepcopy(status_msg.header)
        # To m/s^2: 0.98 mg/LSB (BMI055 data sheet Chapter 5.2.1)
        def to_mpss(v): return float(v) / (2**13 - 1) * 9.80665 * 0.98
        # To rad/s: 32767: 2000 deg/s (BMI055 data sheet Chapter 7.2.1)
        def to_radps(v): return float(v) / (2**15 - 1) * math.pi / 180 * 2000
        # Convert
        status_msg.imu.linear_acceleration.x = to_mpss(report_msg.lin_acc_x)
        status_msg.imu.linear_acceleration.y = to_mpss(report_msg.lin_acc_y)
        status_msg.imu.linear_acceleration.z = to_mpss(report_msg.lin_acc_z)
        status_msg.imu.angular_velocity.x = to_radps(report_msg.ang_vel_x)
        status_msg.imu.angular_velocity.y = to_radps(report_msg.ang_vel_y)
        status_msg.imu.angular_velocity.z = to_radps(report_msg.ang_vel_z)
        # No orientation reported
        status_msg.imu.orientation_covariance[0] = -1

        # Trackpads
        status_msg.touch0.id = report_msg.trackpad_touch0_id
        status_msg.touch0.active = report_msg.trackpad_touch0_active
        status_msg.touch0.x = report_msg.trackpad_touch0_x / float(Controller.TOUCHPAD_MAX_X)
        status_msg.touch0.y = report_msg.trackpad_touch0_y / float(Controller.TOUCHPAD_MAX_Y)
        status_msg.touch1.id = report_msg.trackpad_touch1_id
        status_msg.touch1.active = report_msg.trackpad_touch1_active
        status_msg.touch1.x = report_msg.trackpad_touch1_x / float(Controller.TOUCHPAD_MAX_X)
        status_msg.touch1.y = report_msg.trackpad_touch1_y / float(Controller.TOUCHPAD_MAX_Y)

        # Battery
        if report_msg.battery == Controller.BATTERY_FULL_CHARGING:
            status_msg.battery_full_charging = True
            status_msg.battery_percentage = 1.0
        else:
            status_msg.battery_full_charging = False
            status_msg.battery_percentage = float(report_msg.battery) / Controller.BATTERY_MAX

        # Plugs
        plug_attrs = [attr for attr in dir(report_msg) if attr.startswith('plug_')]
        for attr in plug_attrs:
            val = getattr(report_msg, attr)
            setattr(status_msg, attr, val)

        return status_msg

    #判断是否重新按下
    @staticmethod
    def _once_judge(a,b):
        if a:
            if a != b:
                return True
            else :
                return False
        else :
            return False

    @staticmethod
    def _normalize_axis_(val, deadzone=0.0):
        """
        Convert a value of [0, 255] to [-1.0, 1.0]
        :param val:
        :param deadzone:
        :return:
        """
        norm_val = 2 * (val - 127.5) / 255
        if abs(norm_val) < deadzone:
            return 0.0
        else:
            return norm_val

    @staticmethod
    def _status_to_joy_(status):
        """
        Converts a ds4_driver/Status message to sensor_msgs/Joy
        :param status:
        :type status: Status
        :return:
        """
        msg = Joy()
        msg.header = copy.deepcopy(status.header)
        msg.axes = [
            status.axis_left_x,
            status.axis_left_y,
            status.axis_right_x,
            status.axis_right_y,
            status.axis_l2,
            status.axis_r2,
        ]
        msg.buttons = [
            status.button_square,
            status.button_triangle,
            status.button_circle,
            status.button_cross,
            status.button_l1,
            status.button_l2,
            status.button_r1,
            status.button_r2,
            status.button_share,
            status.button_options,
            status.button_ps,
            status.button_trackpad,
            status.button_l3,
            status.button_r3,
            status.button_dpad_left,
            status.button_dpad_up,
            status.button_dpad_right,
            status.button_dpad_down,
        ]
        return msg

    @staticmethod
    def _status_to_battery_(status):
        """
        Converts a ds4_driver/Status to sensor_msgs/BatteryState
        Reference: https://www.psdevwiki.com/ps4/DualShock_4#Specifications
        :param status:
        :type status: Status
        :return:
        """
        msg = BatteryState()
        msg.header = status.header
        msg.percentage = status.battery_percentage
        msg.voltage = Controller.MAX_VOLTAGE * msg.percentage
        msg.current = float('NaN')
        msg.charge = float('NaN')
        msg.capacity = float('NaN')
        msg.design_capacity = 1.0
        if not status.plug_usb:
            msg.power_supply_status = BatteryState.POWER_SUPPLY_STATUS_NOT_CHARGING
        elif not status.battery_full_charging:
            msg.power_supply_status = BatteryState.POWER_SUPPLY_STATUS_CHARGING
        elif status.battery_full_charging:
            msg.power_supply_status = BatteryState.POWER_SUPPLY_STATUS_FULL
        msg.power_supply_technology = BatteryState.POWER_SUPPLY_TECHNOLOGY_LION
        return msg

    @staticmethod
    def _status_to_imu_(status):
        """
        Converts a ds4_driver/Status to sensor_msgs/Imu
        :param status:
        :type status: Status
        :return:
        """
        return status.imu

