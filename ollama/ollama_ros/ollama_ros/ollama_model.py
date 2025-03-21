import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Int32
from geometry_msgs.msg import Twist
import subprocess

class OllamaModelNode(Node):
    def __init__(self):
        super().__init__('ollama_model_node')

        # 입력을 받을 구독자
        self.subscription = self.create_subscription(
            String, 'ollama_input', self.process_input_callback, 10)

        # 숫자 명령을 발행할 퍼블리셔
        self.command_publisher = self.create_publisher(Int32, 'robot_command', 10)

        # Twist 메시지를 발행할 퍼블리셔
        self.cmd_vel_publisher = self.create_publisher(Twist, '/cmd_vel', 10)

        # 현재 동작 상태 저장
        self.current_twist = Twist()
        self.is_moving = False

        # 0.1초마다 Twist 발행 (현재 명령 유지)
        self.timer = self.create_timer(0.1, self.publish_twist)

        self.get_logger().info("Ollama Model Node started. Listening on 'ollama_input' topic.")

    def process_input_callback(self, msg):
        """Ollama에서 받은 명령어를 숫자로 변환 후 처리"""
        user_input = msg.data.strip()
        self.get_logger().info(f"Received input: {user_input}")

        try:
            # Ollama 실행 명령어
            command = f'echo "{user_input}" | ollama run command_bot'
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            output = result.stdout.strip()

            # 응답이 숫자인지 확인 후 발행
            if output.isdigit():
                command_number = int(output)
                if command_number in [1, 2, 3, 4, 5]:
                    # 숫자 명령을 퍼블리시
                    msg = Int32()
                    msg.data = command_number
                    self.command_publisher.publish(msg)
                    self.get_logger().info(f"Published command: {command_number}")

                    # 해당 명령어에 따라 로봇 제어
                    self.process_command(command_number)
                else:
                    self.get_logger().warn(f"Invalid number received from Ollama: {output}")
            else:
                self.get_logger().warn(f"Non-numeric response from Ollama: {output}")

        except Exception as e:
            self.get_logger().error(f"Error processing command: {e}")

    def process_command(self, command_number):
        """숫자 명령을 받아 Twist 메시지를 생성"""
        twist = Twist()

        if command_number == 1:  # 앞으로 가기
            twist.linear.x = 0.5
            twist.angular.z = 0.0
        elif command_number == 2:  # 뒤로 가기
            twist.linear.x = -0.5
            twist.angular.z = 0.0
        elif command_number == 3:  # 오른쪽 회전
            twist.linear.x = 0.0
            twist.angular.z = 0.5
        elif command_number == 4:  # 왼쪽 회전
            twist.linear.x = 0.0
            twist.angular.z = -0.5
        elif command_number == 5:  # 정지 (즉시 멈춤)
            self.stop_robot()
            return  # 정지 후 더 이상 진행하지 않음

        # 1~4 명령어는 계속 유지됨 (새로운 명령이 들어올 때까지)
        self.current_twist = twist
        self.is_moving = True
        self.get_logger().info(f"Command '{command_number}' received. Executing until new command arrives.")

    def publish_twist(self):
        """Twist 메시지를 계속 발행 (새 명령이 올 때까지 유지)"""
        if self.is_moving:
            self.cmd_vel_publisher.publish(self.current_twist)

    def stop_robot(self):
        """로봇 정지"""
        self.is_moving = False
        stop_twist = Twist()
        self.cmd_vel_publisher.publish(stop_twist)
        self.get_logger().info("Stop command received. Robot stopped immediately.")

def main(args=None):
    rclpy.init(args=args)
    node = OllamaModelNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
