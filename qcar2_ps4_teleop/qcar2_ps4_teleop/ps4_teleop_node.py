#!/usr/bin/env python3
"""
PS4 DualShock 4 → QCar2 Teleop (all-in-one)
────────────────────────────────────────────
Connects to PS4 controller via Bluetooth, reads D-pad arrows
via pygame, and publishes MotorCommands directly to the QCar2.

D-Pad mapping:
  ↑  → increase speed   (+0.1)
  ↓  → decrease speed   (-0.1)
  ←  → steer left       (+0.05 rad)
  →  → steer right      (-0.05 rad)
  L1             → reset ALL to zero (speed + angle)
  × (Cross)      → brake / stop
  △ (Triangle)   → reset angle to 0

Also supports keyboard fallback:
  W/S = speed, A/D = steer, Space = brake, Ctrl+C = exit
"""

import rclpy
from rclpy.node import Node
from qcar2_interfaces.msg import MotorCommands
import pygame
import subprocess
import time
import sys
import signal
import select
import termios
import tty

# Only grab terminal settings if stdin is a real TTY (not when launched via ros2 launch)
HAS_TTY = sys.stdin.isatty()
settings = termios.tcgetattr(sys.stdin) if HAS_TTY else None


class PS4TeleopNode(Node):
    """Reads PS4 D-pad via pygame and publishes MotorCommands to QCar2."""

    def __init__(self):
        super().__init__("ps4_teleop_node")

        self.declare_parameter("btn_brake", 0)      # × (Cross)
        self.declare_parameter("btn_reset_all", 4)   # L1 — reset all to zero
        self.declare_parameter("btn_reset_angle", 3) # △ (Triangle)
        self.declare_parameter("poll_rate", 20.0)    # Hz
        self.declare_parameter("ps4_mac", "00:1F:E2:9D:C5:0E")

        self.pub = self.create_publisher(
            MotorCommands, '/qcar2_motor_speed_cmd', 10
        )

        self.speed = 0.0
        self.angle = 0.0

        # Debounce: only act on rising edge of D-pad
        self._prev_up = False
        self._prev_down = False
        self._prev_left = False
        self._prev_right = False

        # Auto-connect PS4 controller via Bluetooth
        self._auto_connect_bluetooth()

        # Init pygame + joystick
        pygame.init()
        pygame.joystick.init()

        if pygame.joystick.get_count() == 0:
            self.get_logger().error(
                "🎮 No se detectó ningún mando después de conectar. "
                "Asegúrate de que el mando esté encendido (pulsa PS)."
            )
            raise RuntimeError("No joystick found")

        self._joy = pygame.joystick.Joystick(0)
        self._joy.init()
        self.get_logger().info(
            f"🎮 Mando detectado: {self._joy.get_name()} — usa las flechas (D-Pad) + L1"
        )

        # Timer: poll joystick + keyboard, then publish
        self.timer = self.create_timer(0.1, self._tick)

        self.get_logger().info(
            "🎮 QCar2 Teleop listo — usa D-Pad del PS4 o teclado W/S/A/D"
        )

    # ─────────────────────────────────────────────────────────────────
    # Auto-connect Bluetooth
    # ─────────────────────────────────────────────────────────────────
    def _bt_cmd(self, command: str) -> str:
        """Run a single bluetoothctl command and return output."""
        try:
            result = subprocess.run(
                ["bluetoothctl", command,
                 self.get_parameter("ps4_mac").value],
                capture_output=True, text=True, timeout=10
            )
            return result.stdout + result.stderr
        except Exception as e:
            return str(e)

    def _auto_connect_bluetooth(self):
        """Try to connect to the PS4 controller via bluetoothctl."""
        mac = self.get_parameter("ps4_mac").value
        self.get_logger().info(f"🔵 Conectando al mando PS4 ({mac})...")

        # Power on
        subprocess.run(
            ["bluetoothctl", "power", "on"],
            capture_output=True, timeout=5
        )

        # Trust + connect (retry up to 3 times)
        for attempt in range(1, 4):
            self.get_logger().info(f"   Intento {attempt}/3...")

            self._bt_cmd("trust")
            out = self._bt_cmd("connect")

            if "successful" in out.lower() or "already connected" in out.lower():
                self.get_logger().info(f"✅ Mando PS4 conectado ({mac})")
                time.sleep(1)  # Give time for /dev/input to appear
                return

            self.get_logger().warn(f"   No conectó aún: {out.strip()}")
            time.sleep(2)

        self.get_logger().warn(
            "⚠️ No se pudo conectar automáticamente. "
            "Intentando continuar de todas formas..."
        )

    # ─────────────────────────────────────────────────────────────────
    # Poll joystick D-pad
    # ─────────────────────────────────────────────────────────────────
    def _btn(self, name: str) -> int:
        return self.get_parameter(name).value

    def _poll_dpad(self):
        """Read D-pad and buttons from PS4 controller."""
        pygame.event.pump()

        # ── D-Pad (hat 0) ───────────────────────────────────────────
        up = False
        down = False
        left = False
        right = False
        if self._joy.get_numhats() > 0:
            hat_x, hat_y = self._joy.get_hat(0)
            up    = hat_y > 0.5
            down  = hat_y < -0.5
            left  = hat_x < -0.5
            right = hat_x > 0.5

        # ── Buttons ──────────────────────────────────────────────────
        brake     = self._joy.get_button(self._btn("btn_brake"))
        reset_all = self._joy.get_button(self._btn("btn_reset_all"))
        reset_a   = self._joy.get_button(self._btn("btn_reset_angle"))

        # L1 = reset all to zero
        if reset_all:
            self.speed = 0.0
            self.angle = 0.0

        # Brake (× button)
        if brake:
            self.speed = 0.0
            self.angle = 0.0

        # Reset angle (△ button)
        if reset_a:
            self.angle = 0.0

        # Rising edge detection for D-pad (so holding doesn't spam)
        if up and not self._prev_up:
            self.speed += 0.1
        if down and not self._prev_down:
            self.speed -= 0.1
        if left and not self._prev_left:
            self.angle += 0.05
        if right and not self._prev_right:
            self.angle -= 0.05

        self._prev_up = up
        self._prev_down = down
        self._prev_left = left
        self._prev_right = right

    # ─────────────────────────────────────────────────────────────────
    # Timer tick: poll joystick + keyboard, then publish
    # ─────────────────────────────────────────────────────────────────
    def _tick(self):
        # Poll PS4 D-pad
        self._poll_dpad()

        # Keyboard fallback
        key = self._getKey()
        if key == 'w':
            self.speed += 0.1
        elif key == 's':
            self.speed -= 0.1
        elif key == 'a':
            self.angle += 0.05
        elif key == 'd':
            self.angle -= 0.05
        elif key == ' ':
            self.speed = 0.0
            self.angle = 0.0
        elif key == '\x03':
            rclpy.shutdown()
            return

        # Clamp steering angle to ±0.6 rad
        self.angle = max(-0.6, min(0.6, self.angle))
        self.speed = max(-0.7, min(0.7, self.speed))

        # Publish motor commands
        msg = MotorCommands()
        msg.motor_names = ['motor_throttle', 'steering_angle']
        msg.values = [float(self.angle), float(self.speed)]
        self.pub.publish(msg)

        sys.stdout.write(f"\rVel: {self.speed:.2f} | Ang: {self.angle:.2f}   ")
        sys.stdout.flush()

    def _getKey(self):
        if not HAS_TTY:
            return ''
        tty.setraw(sys.stdin.fileno())
        rlist, _, _ = select.select([sys.stdin], [], [], 0.01)
        key = sys.stdin.read(1) if rlist else ''
        if HAS_TTY:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        return key


def main(args=None):
    rclpy.init(args=args)
    node = None

    def _stop_car(signum, frame):
        """SIGINT handler: send zeros while the node is still alive."""
        nonlocal node
        if node is not None:
            try:
                msg = MotorCommands()
                msg.motor_names = ['motor_throttle', 'steering_angle']
                msg.values = [0.0, 0.0]
                for _ in range(15):
                    node.pub.publish(msg)
                    time.sleep(0.05)
                print("\n🛑 Teleop detenido — QCar2 parado")
            except Exception:
                pass
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, _stop_car)

    try:
        node = PS4TeleopNode()
        rclpy.spin(node)
    except (KeyboardInterrupt, RuntimeError):
        pass
    finally:
        try:
            node.destroy_node()
        except Exception:
            pass
        if HAS_TTY:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        pygame.quit()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
