#!/usr/bin/env python3
"""
PS4 DualShock 4 → D-Pad Teleop Publisher
─────────────────────────────────────────
Reads the PS4 controller via pygame and publishes D-pad arrow
commands as a Twist message on /ps4_dpad_cmd so that
fast_teleop.py can subscribe instead of reading the keyboard.

D-Pad mapping (PS4 DualShock 4 hat 0):
  ↑  hat(0, 1)   → increase speed   (like W)
  ↓  hat(0,-1)   → decrease speed   (like S)
  ←  hat(-1,0)   → steer left       (like A)
  →  hat(1, 0)   → steer right      (like D)

  × (Cross, btn 0) → brake / stop   (like Space)
  L1 (btn 4)      → reset ALL to zero (speed + angle)
  △ (btn 3)       → reset angle to 0

Publishes geometry_msgs/Twist on /ps4_dpad_cmd:
  linear.x  =  +1 (up), -1 (down), 0 (none)
  angular.z =  +1 (left), -1 (right), 0 (none)
  linear.y  =  1.0 if brake button pressed
  linear.z  =  1.0 if L1 pressed (reset all)
  angular.x =  1.0 if reset-angle (△) pressed
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import pygame
import subprocess
import time


class PS4DpadPublisher(Node):
    """Reads PS4 D-pad and publishes direction commands."""

    def __init__(self):
        super().__init__("ps4_teleop_node")

        self.declare_parameter("btn_brake", 0)      # × (Cross)
        self.declare_parameter("btn_reset_all", 4)   # L1 — reset all to zero
        self.declare_parameter("btn_reset_angle", 3) # △ (Triangle)
        self.declare_parameter("poll_rate", 20.0)    # Hz
        self.declare_parameter("ps4_mac", "00:1F:E2:9D:C5:0E")

        self._pub = self.create_publisher(Twist, "/ps4_dpad_cmd", 10)

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

        rate = self.get_parameter("poll_rate").value
        self._timer = self.create_timer(1.0 / rate, self._poll)

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

    def _btn(self, name: str) -> int:
        return self.get_parameter(name).value

    def _poll(self):
        pygame.event.pump()

        msg = Twist()

        # ── D-Pad (hat 0) ───────────────────────────────────────────
        if self._joy.get_numhats() > 0:
            hat_x, hat_y = self._joy.get_hat(0)
            msg.linear.x = float(hat_y)
            msg.angular.z = float(-hat_x)

        # ── Buttons ──────────────────────────────────────────────────
        brake    = self._joy.get_button(self._btn("btn_brake"))
        reset_all = self._joy.get_button(self._btn("btn_reset_all"))
        reset_a  = self._joy.get_button(self._btn("btn_reset_angle"))

        msg.linear.y = 1.0 if brake else 0.0
        msg.linear.z = 1.0 if reset_all else 0.0
        msg.angular.x = 1.0 if reset_a else 0.0

        self._pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    try:
        node = PS4DpadPublisher()
        rclpy.spin(node)
    except (KeyboardInterrupt, RuntimeError):
        pass
    finally:
        pygame.quit()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
