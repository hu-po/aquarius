# robot client runs inside a docker container on the agx orin
# robot server runs on the bare metal of the robot arm

# Maximum KISS principle, the only function we need of the pymycobot library is to send angles to the robot armfrom pymycobot import MyCobotSocket
from pymycobot import MyCobotSocket

def test(mycobot):
    print("\nStart check basic options\n")

    mycobot.set_color(255, 255, 0)
    print("::set_color() ==> color {}\n".format("255 255 0"))
    time.sleep(3)

    angles = [0, 0, 0, 0, 0, 0]
    mycobot.send_angles(angles, 100)
    print("::send_angles() ==> angles {}, speed 100\n".format(angles))
    time.sleep(3)

    print("::get_angles() ==> degrees: {}\n".format(mycobot.get_angles()))
    time.sleep(1)

    mycobot.send_angle(Angle.J1.value, 90, 50)
    print("::send_angle() ==> angle: joint1, degree: 90, speed: 50\n")
    time.sleep(4)

    radians = [1, 1, 1, 1, 1, 1]
    mycobot.send_radians(radians, 100)
    print("::send_radians() ==> set radians {}, speed 100\n".format(radians))
    time.sleep(3)

    print("::get_radians() ==> radians: {}\n".format(mycobot.get_radians()))
    time.sleep(1)

    print("::set_free_mode()\n")
    angles = [0, 0, 0, 0, 0, 0]
    mycobot.send_angles(angles, 100)
    print("::send_angles() ==> angles {}, speed 100\n".format(angles))
    time.sleep(3)
    mycobot.release_all_servos()

    mycobot.set_color(255, 0, 0)
    print("::set_color() ==> color {}\n".format("255 255 0"))
    time.sleep(3)

    print("=== check end ===\n")

if __name__ == "__main__":
    m = MyCobotSocket("192.168.10.10", "9000")
    # connect pi
    m.connect()
    print(m.get_coords())
    test(m)