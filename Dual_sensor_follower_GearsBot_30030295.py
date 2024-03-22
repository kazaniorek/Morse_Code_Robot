import time
# Import libraries for motor control, sound output, and sensor input.
from ev3dev2.motor import LargeMotor, MoveTank, OUTPUT_A, OUTPUT_B, SpeedPercent
from ev3dev2.sound import Sound
from ev3dev2.sensor.lego import ColorSensor, UltrasonicSensor
from ev3dev2.sensor import INPUT_1, INPUT_2, INPUT_4

class MorseCodeDecoderRobot:
    def __init__(self):
        # Initialize motors for driving: left motor connected to output A, right motor to output B.
        self.drive_motor_left = LargeMotor(OUTPUT_A)
        self.drive_motor_right = LargeMotor(OUTPUT_B)

        # Setting up a drive system using both motors for coordinated movements.
        self.drive_system = MoveTank(OUTPUT_A, OUTPUT_B)

        # Initialising the speaker for audible feedback and announcements.
        self.speaker = Sound()

        # Initialising sensors: One color sensor for Morse code reading and navigation,
        # an ultrasonic sensor for detecting obstacles, and another color sensor dedicated to line following.
        self.path_color_sensor = ColorSensor(INPUT_1)
        self.obstacle_detector = UltrasonicSensor(INPUT_2)
        self.line_color_sensor = ColorSensor(INPUT_4)

        # Defining Morse code symbols for decoding.
        self.code_symbols = {'dot': '.', 'dash': '-', 'gap': ' '}

        # Map Morse code symbols to their alphanumeric equivalents for translation.
        self.morse_to_alpha_numeric = {
            '.-': 'A', '-...': 'B', '-.-.': 'C', '-..': 'D', '.': 'E', '..-.': 'F',
            '--.': 'G', '....': 'H', '..': 'I', '.---': 'J', '-.-': 'K', '.-..': 'L',
            '--': 'M', '-.': 'N', '---': 'O', '.--.': 'P', '--.-': 'Q', '.-.': 'R',
            '...': 'S', '-': 'T', '..-': 'U', '...-': 'V', '.--': 'W', '-..-': 'X',
            '-.--': 'Y', '--..': 'Z', '-----': '0', '.----': '1', '..---': '2',
            '...--': '3', '....-': '4', '.....': '5', '-....': '6', '--...': '7',
            '---..': '8', '----.': '9'
        }

        # Calling the initialize method to set up initial states for robot operation.
        self.initialize()

    def initialize(self):
        # Reset or Initialise the robot's state for a new decoding session.
        # This is important for ensuring that the robot starts with a clean state for each operation.
        
        # Initialise the current and last detected color to None. This will help in determining changes in the detected colors.
        self.current_detected_color = None
        self.last_detected_color = None
        
        # Record the start time of a signal. This is crucial for calculating the duration of signals, which is needed for decoding Morse code.
        self.signal_start_time = time.time()
        
        # Initialise the duration of the first signal to None. The first signal's duration is used as a reference for interpreting subsequent signals.
        self.first_signal_duration = None
        
        # Initialise the variable to hold the duration of the signal gap. This is used in determining spaces between Morse code symbols.
        self.signal_gap_duration = None
        
        # Initialise an empty string to hold the decoded message. As the robot decodes signals, it will append to this string.
        self.decoded_message = ""
        
    def announce_start(self):
        # This method uses the robot's speaker to audibly announce the start of the program.
        # It's a simple auditory cue to indicate that the robot is beginning its operations.
    
        # Use the speaker to announce the commencement of the decoding process.
        self.speaker.speak("Program starting")

    def decode_path(self):
        # Announce the start of the decoding process using the speaker.
        self.announce_start()
    
        # Begin an infinite loop to continuously check for and decode Morse code signals.
        while True:
            # Detect the current color under the path_color_sensor.
            detected_color = self.path_color_sensor.color
    
            # Check if there's an obstacle nearby using the ultrasonic sensor's distance reading.
            obstacle_nearby = self.obstacle_detector.distance_centimeters < 10
    
            # Treat yellow (color code 4) and brown (color code 7) as red (color code 5) for uniform decoding.
            # This adjustment simplifies the decoding process by reducing the number of color conditions to check.
            if detected_color in [4, 7]:
                detected_color = 5
    
            # Adjust the robot's heading based on detected colors to maintain its course along a path.
            self.adjust_heading(detected_color)
    
            # Process decoding if the detected color changes, signifying a potential Morse code symbol.
            if detected_color != self.last_detected_color:
                # If the last detected color was relevant for decoding (red or white),
                # calculate the duration of the signal.
                if self.last_detected_color is not None and self.last_detected_color in [5, 6]:
                    signal_duration = time.time() - self.signal_start_time
    
                    # If the previously detected color was white, use the signal's duration to determine gaps between Morse code symbols.
                    if self.last_detected_color == 6:  # White
                        if self.first_signal_duration is None:
                            self.first_signal_duration = signal_duration
                        else:
                            # Determine the number of gaps based on the signal's duration relative to the first signal's duration.
                            self.decoded_message += self.code_symbols['gap'] * int(
                                round(signal_duration / self.first_signal_duration))
    
                    # If the previously detected color was red, use the signal's duration to differentiate between dots and dashes.
                    elif self.last_detected_color == 5:  # Red
                        if signal_duration < 1 * self.first_signal_duration:
                            self.decoded_message += self.code_symbols['dot']
                        else:
                            self.decoded_message += self.code_symbols['dash']
    
                    # Reset the signal start time for the next detection.
                    self.signal_start_time = time.time()
    
                # Update the last detected color for the next iteration of the loop.
                self.last_detected_color = detected_color
    
            # If an obstacle is detected nearby or a certain sequence indicating the end of the message is encountered, stop the robot.
            if obstacle_nearby or self.decoded_message.endswith(self.code_symbols['gap'] * 7):
                self.drive_system.off(brake=True)
                break

    def adjust_heading(self, color):
        # This method adjusts the robot's heading based on colors detected by both the path and line color sensors.
        # It ensures the robot maintains its course along a path and reacts appropriately to color-coded instructions.
        
        # Get colors detected by each sensor
        path_color = self.path_color_sensor.color  # Color detected by the Morse code/obstacle sensor
        line_color = self.line_color_sensor.color  # Color detected by the line following sensor
        
        # Base speeds for each motor
        base_speed_left = 25
        base_speed_right = 25.1  # Setting a slightly different base speed for the right motor
        
        
        # Adjust right motor speed if path_color_sensor sees green
        if path_color == 3:  # Assuming 3 represents green
            # Increase right motor speed slightly
            base_speed_right += 1  # Adjust speed difference as needed

        # Adjust left motor speed if line_color_sensor sees black
        if line_color == 1:  # Assuming 1 represents black
            # Increase left motor speed slightly to correct position
            base_speed_left += 1  # Adjust speed difference as needed

        # Apply the adjusted speeds
        self.drive_motor_left.on(SpeedPercent(base_speed_left), brake=False)
        self.drive_motor_right.on(SpeedPercent(base_speed_right), brake=False)

    def display_results(self):
        # This method is responsible for communicating the decoded Morse code and its translation.
        # It utilizes both print statements for debugging and the speaker for auditory feedback.
    
        # Print the Morse code message to the console for debugging and verification purposes.
        print(f"Morse code message: {self.decoded_message}")
    
        # Prepare the decoded Morse code message for translation by stripping any leading or trailing whitespace.
        self.decoded_message = self.decoded_message.strip()
    
        # Translate the Morse code message into alphanumeric text.
        translated_message = self.translate_to_text(self.decoded_message)
    
        # Use the robot's speaker to audibly announce the translated alphanumeric message.
        self.speaker.speak("Decoded message: " + translated_message)
    
        # Print the translated message to the console for debugging and to provide a text-based output.
        print("_" * 50, "\n")
        print(f"Decoded message: {translated_message}")
        print("_" * 50)


    def translate_to_text(self, morse_code_message):
        # This method translates a Morse code string into its equivalent alphanumeric text.
        # It's a critical part of the robot's functionality, allowing it to convey the decoded message in a human-readable format.
    
        # Initialize an empty string to hold the final translated text message.
        text_message = ""
    
        # Split the Morse code message into words based on a specific number of 'gap' symbols,
        # which in this context acts as a delimiter for words in Morse code.
        for word in morse_code_message.split(self.code_symbols['gap'] * 3):
            # Initialize an empty string for the decoded word.
            decoded_word = ""
    
            # Split each word into its Morse code symbols (dots and dashes) based on the 'gap' symbol,
            # which acts as a delimiter for individual characters within a word.
            for symbol in word.split(self.code_symbols['gap']):
                # Append the alphanumeric character corresponding to the Morse code symbol to the decoded word.
                # If the symbol doesn't have a corresponding character (not found in the mapping), ignore it.
                decoded_word += self.morse_to_alpha_numeric.get(symbol, '')
    
            # Append the translated word followed by a space to the final text message.
            text_message += decoded_word + ' '
    
        # Return the final translated text message, trimming any trailing spaces for neatness.
        return text_message.strip()


if __name__ == "__main__":
    decoder_robot = MorseCodeDecoderRobot()
    decoder_robot.decode_path()
    decoder_robot.display_results()
