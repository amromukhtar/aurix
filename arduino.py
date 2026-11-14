#!/usr/bin/env python3
import serial
import time
import re


class MotorController:
    def __init__(self, serial_port='/dev/ttyACM0', baud_rate=9600):
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.arduino = None
        self.setup_serial()

    def setup_serial(self):
        """Initialize serial connection to Arduino"""
        try:
            self.arduino = serial.Serial(
                self.serial_port, self.baud_rate, timeout=1)
            time.sleep(2)  # Wait for Arduino to reset
            print(f"Connected to Arduino on {self.serial_port}")
        except serial.SerialException as e:
            print(f"Error connecting to Arduino: {e}")

    def send_command(self, command):
        """Send command to Arduino"""
        if self.arduino and self.arduino.is_open:
            try:
                self.arduino.write(f"{command}\n".encode())
                response = self.arduino.readline().decode().strip()
                return response
            except Exception as e:
                print(f"Error sending command: {e}")
                return None
        return None

    def parse_llm_text(self, llm_text):
        """Parse LLM output to extract motor commands"""
        llm_text = llm_text.upper()

        if "STOP" in llm_text:
            return ["STOP"]

        pattern = r"MOVE\s+(FORWARD|BACKWARD|LEFT|RIGHT)\s+(\d+(?:\.\d+)?)\s+(\d+)"
        matches = re.findall(pattern, llm_text)
        commands = []

        if not matches:
            return ["STOP"]

        for direction, duration, speed in matches:
            direction = direction.upper() if direction.upper() is not None else "FORWARD"
            duration = int(duration)
            speed = int(speed)

            commands.append(f"MOVE {direction} {duration} {speed}")

        return commands

    def execute_llm_command(self, llm_text):
        """Execute commands parsed from LLM output"""
        commands = self.parse_llm_text(llm_text)
        print(f"Parsed commands: {commands}")

        responses = []
        for command in commands:
            self.send_command(command)
            # if response:
            #     responses.append(response)
            #     print(f"Command: {command} -> Response: {response}")
            time.sleep(0.04)

        return responses

    def close(self):
        """Close the serial connection"""
        if self.arduino and self.arduino.is_open:
            self.arduino.close()
            print("Closed Arduino connection")
