import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Float64, Bool
import pygame
import math


class PS4ControllerNode(Node):
    def __init__(self):
        super().__init__('ps4_controller_node')
        # Publishers
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.relay1_pub = self.create_publisher(Bool, '/relay1_control', 10)
        self.relay2_pub = self.create_publisher(Bool, '/relay2_control', 10)

        # Publishers for steering joints
        self.steering_pubs = {
            "joint_st1l": self.create_publisher(Float64, '/joint_st1l/cmd_pos', 10),
            "joint_st1r": self.create_publisher(Float64, '/joint_st1r/cmd_pos', 10),
            "joint_st2l": self.create_publisher(Float64, '/joint_st2l/cmd_pos', 10),
            "joint_st2r": self.create_publisher(Float64, '/joint_st2r/cmd_pos', 10),
        }

        # Timer
        self.timer = self.create_timer(0.1, self.publish_twist)

        self.twist = Twist()

        # Init pygame + joystick
        pygame.init()
        pygame.joystick.init()
        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()

        self.threshold = 0.08
        self.get_logger().info("PS4 Controller Node Initialized!")

    def publish_twist(self):
        # Solo publica si supera el umbral
        if abs(self.twist.linear.x) > self.threshold or abs(self.twist.angular.z) > self.threshold:
            self.cmd_vel_pub.publish(self.twist)
        else:
            stop_twist = Twist()
            self.cmd_vel_pub.publish(stop_twist)

    def update_controller(self):
        pygame.event.pump()

        # Joystick izquierdo → movimiento cmd_vel
        axis_left_y = -self.joystick.get_axis(1)*7  # adelante/atrás
        axis_left_x = -self.joystick.get_axis(0)*3.7   # izquierda/derecha

        self.twist.linear.x = axis_left_y if abs(axis_left_y) > self.threshold else 0.0
        self.twist.angular.z = axis_left_x if abs(axis_left_x) > self.threshold else 0.0

        # Joystick derecho → dirección de las ruedas
        right_x = -self.joystick.get_axis(3)/5
        right_y = -self.joystick.get_axis(2)/5

        msg = Float64()

        # Si hay entrada significativa, calculamos el ángulo
        if abs(right_x) > self.threshold or abs(right_y) > self.threshold:
            angle = math.atan2(right_y, right_x)  # radianes
            msg.data = angle
        else:
            # Joystick en reposo → volver a 0 rad
            msg.data = 0.0

        # Publicamos a todos los joints de dirección
        for pub in self.steering_pubs.values():
            pub.publish(msg)

        # Relays
        relay1_state = Bool()
        relay2_state = Bool()
        relay1_state.data = bool(self.joystick.get_button(0))
        relay2_state.data = bool(self.joystick.get_button(1))
        self.relay1_pub.publish(relay1_state)
        self.relay2_pub.publish(relay2_state)


def main(args=None):
    rclpy.init(args=args)
    node = PS4ControllerNode()

    try:
        while rclpy.ok():
            node.update_controller()
            rclpy.spin_once(node, timeout_sec=0.01)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
        pygame.quit()


if __name__ == '__main__':
    main()
