import rclpy
from rclpy.node import Node
from qcar2_interfaces.msg import MotorCommands
import sys, select, termios, tty

settings = termios.tcgetattr(sys.stdin)

class QCar2Teleop(Node):
    def __init__(self):
        super().__init__('qcar2_manual_teleop')
        self.pub = self.create_publisher(MotorCommands, '/qcar2_motor_speed_cmd', 10)
        self.speed = 0.0
        self.angle = 0.0
        self.timer = self.create_timer(0.1, self.publish_cmd)
        print("Control QCar2: W/S (Velocidad), A/D (Giro), Espacio (Freno), CTRL+C (Salir)")

    def getKey(self):
        tty.setraw(sys.stdin.fileno())
        rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
        key = sys.stdin.read(1) if rlist else ''
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        return key

    def publish_cmd(self):
        key = self.getKey()
        if key == 'w': self.speed += 0.1
        elif key == 's': self.speed -= 0.1
        elif key == 'a': self.angle += 0.05
        elif key == 'd': self.angle -= 0.05
        elif key == ' ': self.speed = 0.0; self.angle = 0.0
        elif key == '\x03': rclpy.shutdown() # CTRL+C

        msg = MotorCommands()
        msg.motor_names = ['motor_throttle', 'steering_angle']
        msg.values = [float(self.angle), float(self.speed)]
        self.pub.publish(msg)
        sys.stdout.write(f"\rVel: {self.speed:.2f} m/s | Ang: {self.angle:.2f} rad   ")

def main():
    rclpy.init()
    node = QCar2Teleop()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()

