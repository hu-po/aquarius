https://github.com/elephantrobotics/pymycobot/blob/main/pymycobot/mycobot280.py

```python
class MyCobot280(CommandGenerator):
    """MyCobot280 Python API Serial communication class.

    Supported methods:

        # Overall status
            set_free_mode()
            is_free_mode()
            get_error_information()
            clear_error_information()
            set_fresh_mode()
            get_fresh_mode()
            read_next_error()
            Other at parent class: `CommandGenerator`.

        # MDI mode and operation
            get_radians()
            send_radians()
            sync_send_angles() *
            sync_send_coords() *
            get_angles_coords()
            Other look at parent class: `CommandGenerator`.

        # JOG mode and operation
            jog_rpy()
            set_HTS_gripper_torque()
            get_HTS_gripper_torque()
            get_gripper_protect_current()
            init_gripper()
            set_gripper_protect_current()
            Other at parent class: `CommandGenerator`.

        # Running status and Settings
            set_joint_max()
            set_joint_min()
            Look at parent class: `CommandGenerator`.

        # Servo control
            move_round()
            set_four_pieces_zero()
            Other at parent class: `CommandGenerator`.

        # Atom IO
            set_pin_mode()
            get_gripper_value()
            is_gripper_moving()
            set_pwm_output()
            Other at parent class: `CommandGenerator`.

        # Basic
            set_transponder_mode()
            get_transponder_mode()
            Other at parent class: `CommandGenerator`.

        # Servo state value
            get_servo_speeds()
            get_servo_voltages()
            get_servo_status()
            get_servo_temps()

        # Coordinate transformation
            set_tool_reference()
            get_tool_reference()
            set_world_reference()
            get_world_reference()
            set_reference_frame()
            get_reference_frame()
            set_movement_type()
            get_movement_type()
            set_end_type()
            get_end_type()

        # Other
            close()
            open()
            wait() *
    """
```

https://github.com/elephantrobotics/pymycobot/blob/main/pymycobot/mycobotsocket.py

```python
class MyCobotSocket(CommandGenerator):
    """MyCobot Python API Serial communication class.
    Note: Please use this class under the same network

    Supported methods:

        # Overall status
            Look at parent class: `CommandGenerator`.

        # MDI mode and operation
            get_radians()
            send_radians()
            sync_send_angles() *
            sync_send_coords() *
            Other look at parent class: `CommandGenerator`.

        # JOG mode and operation
            Look at parent class: `CommandGenerator`.

        # Running status and Settings
            Look at parent class: `CommandGenerator`.

        # Servo control
            Look at parent class: `CommandGenerator`.

        # Atom IO
            Look at parent class: `CommandGenerator`.

        # Basic
            Look at parent class: `CommandGenerator`.

        # Other
            wait() *
    """
```