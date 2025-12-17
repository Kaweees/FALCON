import time

from ..base import BasicCommandSender


class UnitreeCommandSender(BasicCommandSender):
    """Unitree command sender implementation."""

    def _init_sdk_components(self):
        """Initialize Unitree SDK-specific components."""
        from unitree_sdk2py.core.channel import ChannelPublisher, ChannelSubscriber
        from unitree_sdk2py.utils.crc import CRC
        from unitree_sdk2py.comm.motion_switcher.motion_switcher_client import MotionSwitcherClient

        robot_type = self.config["ROBOT_TYPE"]

        if (
            "g1" in robot_type
            or "h1-2" in robot_type
        ):
            from unitree_sdk2py.idl.default import unitree_hg_msg_dds__LowCmd_
            from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowCmd_, LowState_

            self.low_cmd = unitree_hg_msg_dds__LowCmd_()
        elif "h1" in robot_type or "go2" in robot_type:
            from unitree_sdk2py.idl.default import unitree_go_msg_dds__LowCmd_
            from unitree_sdk2py.idl.unitree_go.msg.dds_ import LowCmd_, LowState_

            self.low_cmd = unitree_go_msg_dds__LowCmd_()
        else:
            raise NotImplementedError(f"Robot type {robot_type} is not supported yet")

        # Initialize motion switcher to take control of low-level interface
        # This mirrors the official `g1_low_level_example.py` behavior.
        self.motion_switcher = MotionSwitcherClient()
        self.motion_switcher.SetTimeout(5.0)
        self.motion_switcher.Init()

        status, result = self.motion_switcher.CheckMode()
        # Release any existing mode until low-level control is free.
        while result and result.get("name"):
            self.motion_switcher.ReleaseMode()
            time.sleep(1.0)
            status, result = self.motion_switcher.CheckMode()

        # Initialize low command publisher
        self.lowcmd_publisher_ = ChannelPublisher("rt/lowcmd", LowCmd_)
        self.lowcmd_publisher_.Init()

        # Subscribe to lowstate to mirror the robot's current mode_machine,
        # similar to the official low-level example.
        self.low_state = None
        self.mode_machine = None
        self.lowstate_subscriber = ChannelSubscriber("rt/lowstate", LowState_)
        self.lowstate_subscriber.Init(self._low_state_handler, 10)

        self.InitUnitreeLowCmd()
        self.crc = CRC()

    def _low_state_handler(self, msg):
        """Callback for low-level state; cache mode_machine like the Unitree example."""
        self.low_state = msg
        if self.mode_machine is None:
            # Use the robot's current mode_machine as the baseline control mode.
            self.mode_machine = getattr(msg, "mode_machine", None)

    def InitUnitreeLowCmd(self):
        """Initialize Unitree low-level command."""
        robot_type = self.config["ROBOT_TYPE"]

        # Set head for h1/go2
        if robot_type == "h1" or robot_type == "go2":
            self.low_cmd.head[0] = 0xFE
            self.low_cmd.head[1] = 0xEF

        self.low_cmd.level_flag = 0xFF
        self.low_cmd.gpio = 0

        for i in range(self.robot.NUM_MOTORS):
            # Default to disabled; we will set mode=1 per send once mode_machine is known.
            self.low_cmd.motor_cmd[i].mode = 0
            self.low_cmd.motor_cmd[i].q = self.robot.UNITREE_LEGGED_CONST["PosStopF"]
            self.low_cmd.motor_cmd[i].kp = 0
            self.low_cmd.motor_cmd[i].dq = self.robot.UNITREE_LEGGED_CONST["VelStopF"]
            self.low_cmd.motor_cmd[i].kd = 0
            self.low_cmd.motor_cmd[i].tau = 0

    def send_command(self, cmd_q, cmd_dq, cmd_tau, dof_pos_latest=None):
        """Send command to Unitree robot."""

        # Wait until we have seen at least one lowstate message so that
        # mode_machine is populated from the robot, like in g1_low_level_example.
        if self.mode_machine is None:
            return

        # Mirror Unitree example: ensure mode_machine and mode_pr are set each cycle.
        self.low_cmd.mode_machine = self.mode_machine
        # Use the MODE_PR from config (typically 0) each send, analogous to Mode.PR.
        self.low_cmd.mode_pr = self.config["UNITREE_LEGGED_CONST"]["MODE_PR"]

        motor_cmd = self.low_cmd.motor_cmd
        # Enable all motors (mode=1) before filling commands, as in the low-level demo.
        for i in range(self.robot.NUM_MOTORS):
            motor_cmd[i].mode = 1

        self._fill_motor_commands(motor_cmd, cmd_q, cmd_dq, cmd_tau)

        # Add CRC and send
        self.low_cmd.crc = self.crc.Crc(self.low_cmd)
        self.lowcmd_publisher_.Write(self.low_cmd)
