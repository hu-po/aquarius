import time
import os
import sys
import termios
import tty
import threading
import json
import serial
import serial.tools.list_ports

from pymycobot.mycobot import MyCobot

port: str
mc: MyCobot
sp: int = 80
debug: bool = False
baud: int = 1000000

def setup():
    global port, mc, debug, baud
    port = "/dev/ttyAMA0"
    mc = MyCobot(port, baud, debug=debug)
    mc.power_on()


class Raw(object):
    """Set raw input mode for device"""

    def __init__(self, stream):
        self.stream = stream
        self.fd = self.stream.fileno()

    def __enter__(self):
        self.original_stty = termios.tcgetattr(self.stream)
        tty.setcbreak(self.stream)

    def __exit__(self, type, value, traceback):
        termios.tcsetattr(self.stream, termios.TCSANOW, self.original_stty)


class Helper(object):
    def __init__(self) -> None:
        self.w, self.h = os.get_terminal_size()

    def echo(self, msg):
        print("\r{}".format(" " * self.w), end="")
        print("\r{}".format(msg), end="")


class TeachingTest(Helper):
    def __init__(self, mycobot) -> None:
        super().__init__()
        self.mc = mycobot
        self.recording = False
        self.playing = False
        self.record_list = []
        self.record_t = None
        self.play_t = None
        self.path = os.path.dirname(os.path.abspath(__file__)) + "/record.txt"

    def record(self):
        self.record_list = []
        self.recording = True
        #self.mc.set_fresh_mode(0)
        def _record():
            while self.recording:
                start_t = time.time()
                angles = self.mc.get_encoders()
                speeds = self.mc.get_servo_speeds()
                gripper_value = self.mc.get_encoder(7)
                interval_time = time.time() - start_t
                if angles and speeds:
                    record = [angles, speeds, gripper_value, interval_time]
                    self.record_list.append(record)
                    # time.sleep(0.1)
                    print("\r {}".format(time.time() - start_t), end="")

        self.echo("Start recording.")
        self.record_t = threading.Thread(target=_record, daemon=True)
        self.record_t.start()

    def stop_record(self):
        if self.recording:
            self.recording = False
            self.record_t.join()
            self.echo("Stop record")

    def play(self):
        self.echo("Start play")
        i = 0
        for record in self.record_list:
            angles, speeds, gripper_value, interval_time = record
            #print(angles)
            self.mc.set_encoders_drag(angles, speeds)
            self.mc.set_encoder(7, 80)
            if i == 0:
                time.sleep(3)
            i+=1
            time.sleep(interval_time)
        self.echo("Finish play")

    def loop_play(self):
        self.playing = True

        def _loop():
            while self.playing:
                self.play()

        self.echo("Start loop play.")
        self.play_t = threading.Thread(target=_loop, daemon=True)
        self.play_t.start()

    def stop_loop_play(self):
        if self.playing:
            self.playing = False
            self.play_t.join()
            self.echo("Stop loop play.")

    def save_to_local(self):
        if not self.record_list:
            self.echo("No data should save.")
            return
        with open(self.path, "w") as f:
            json.dump(self.record_list, f, indent=2)
            self.echo("save dir:  {}\n".format(self.path))

    def load_from_local(self):
        with open(self.path, "r") as f:
            try:
                data = json.load(f)
                self.record_list = data
                self.echo("Load data success.")
            except Exception:
                self.echo("Error: invalid data.")

    def print_menu(self):
        print(
            """\
        \r q: quit
        \r r: start record
        \r c: stop record
        \r p: play once
        \r P: loop play / stop loop play
        \r s: save to local
        \r l: load from local
        \r f: release mycobot
        \r----------------------------------
            """
        )

    def start(self):
        self.print_menu()

        while not False:
            with Raw(sys.stdin):
                key = sys.stdin.read(1)
                if key == "q":
                    break
                elif key == "r":  # recorder
                    self.record()
                elif key == "c":  # stop recorder
                    self.stop_record()
                elif key == "p":  # play
                    if not self.playing:
                        self.play()
                    else:
                        print("Already playing. Please wait till current play stop or stop loop play.")
                elif key == "P":  # loop play
                    if not self.playing:
                        self.loop_play()
                    else:
                        self.stop_loop_play()
                elif key == "s":  # save to local
                    self.save_to_local()
                elif key == "l":  # load from local
                    self.load_from_local()
                elif key == "f":  # free move
                    self.mc.release_all_servos()
                    self.echo("Released")
                else:
                    print(key)
                    continue


if __name__ == "__main__":
    setup()
    recorder = TeachingTest(mc)
    recorder.start()