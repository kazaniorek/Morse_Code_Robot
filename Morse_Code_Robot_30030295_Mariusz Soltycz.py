#!/usr/bin/env python3
# Import necessary libraries for motor control, sound output, display management, and sensor input
import time
from ev3dev2.motor import LargeMotor, MoveTank, OUTPUT_C, OUTPUT_B, SpeedPercent
from ev3dev2.sound import Sound
from ev3dev2.display import Display
from ev3dev2.sensor.lego import ColorSensor, InfraredSensor
from ev3dev2.sensor import INPUT_1, INPUT_2, INPUT_3
from PIL import ImageFont

class MorseCodeDecoderRobot:
    def __init__(self):
        # Initialize motors for driving: left motor connected to output C, right motor to output B.
        self.drive_motor_left = LargeMotor(OUTPUT_C)
        self.drive_motor_right = LargeMotor(OUTPUT_B)

        # Setting up a drive system using both motors for coordinated movements.
        self.drive_system = MoveTank(OUTPUT_C, OUTPUT_B)

        # Initialising the display for outputting information on the robot's screen.
        self.display = Display()

        # Initialising the speaker for audible feedback and announcements.
        self.speaker = Sound()

        # Initialising sensors: One color sensor for decoding Morse code and another for line following,
        # Initialising an infrared sensor for detecting obstacles.
        self.path_color_sensor = ColorSensor(INPUT_1) # Used for Morse code decoding.
        self.line_color_sensor = ColorSensor(INPUT_3)  # Used for following a line.
        self.obstacle_detector = InfraredSensor(INPUT_2)  # Used for obstacle detection.

        # Defining the Morse code representation for easier reference throughout the code.
        self.morse_code = {'dot': '.', 'dash': '-', 'gap': ' ', 'word_gap':'|' }

        # Map Morse code symbols to their alphanumeric equivalents.
        self.morse_to_alpha_numeric = {
            '.-': 'A', '-...': 'B', '-.-.': 'C', '-..': 'D', '.': 'E', '..-.': 'F',
            '--.': 'G', '....': 'H', '..': 'I', '.---': 'J', '-.-': 'K', '.-..': 'L',
            '--': 'M', '-.': 'N', '---': 'O', '.--.': 'P', '--.-': 'Q', '.-.': 'R',
            '...': 'S', '-': 'T', '..-': 'U', '...-': 'V', '.--': 'W', '-..-': 'X',
            '-.--': 'Y', '--..': 'Z', '-----': '0', '.----': '1', '..---': '2',
            '...--': '3', '....-': '4', '.....': '5', '-....': '6', '--...': '7',
            '---..': '8', '----.': '9'
        }

        # Calling the initialise method to reset or set initial states for the robot's operation.
        self.initialise()

    def announce_start(self):
        # This method uses the robot's speaker to audibly announce the start of the program.
        self.speaker.speak("Program starting")

    def initialise(self):
        # Reset or Initialise the robot's state for a new decoding session.
        # This is important for ensuring that the robot starts with a clean state for each operation.

        # Initialise the current and last detected color to None. This will help in determining changes in the detected colors.
        self.current_detected_color = None
        self.last_detected_color = None

        # Record the start time of a signal. This is crucial for calculating the duration of signals, which is needed for decoding Morse code.
        self.signal_start_time = time.time()

        # Initialise the duration of the first signal to None. The first signal's duration is used as a reference for interpreting subsequent signals.
        self.first_signal_duration = None
        # Initialise the variable to hold the duration of the current signal. This is used in conjunction with the first signal to decode Morse code.
        self.signal_duration = None

        # Initialise an empty string to hold the decoded message. As the robot decodes signals, it will append to this string.
        self.decoded_message = ""

    def decode_path(self):
        # This method contains the main loop for decoding Morse code signals detected by the robot as it moves along a path.

        # Announce the start of the decoding process using the speaker.
        self.announce_start()

        # Begin an infinite loop to continuously check for and decode Morse code signals.
        while True:
            # Detect the current color under the path_color_sensor.
            detected_color = self.path_color_sensor.color
            # Check if there's an obstacle nearby using the infrared sensor's proximity reading.
            obstacle_nearby = self.obstacle_detector.proximity < 5
            
            # Treat yellow and brown colors as red for the purpose of decoding.
            if detected_color in [4, 7]:  # Yellow and brown color codes.
                detected_color = 5 # Red color code.

            # Adjust the robot's heading based on detected colors.
            self.adjust_heading(detected_color)

            # Check if the detected color has changed since the last loop iteration.
            if detected_color != self.last_detected_color:
                # If there was a previous color detected and it was relevant for decoding,
                # calculate the duration of the signal.
                if self.last_detected_color is not None and self.last_detected_color in [5, 6]:
                    signal_duration = time.time() - self.signal_start_time
                    # Handle the decoding based on the color and duration of the signal.
                    # This includes differentiating between dots, dashes, gaps, and word gaps in Morse code.
                    # The logic applies to determine these based on the signal duration and the first signal's duration.
                    # A short duration represent a dot, while a longer one represent a dash.
                    if self.last_detected_color == 6:  # White
                        if self.first_signal_duration is None:
                            self.first_signal_duration = signal_duration

                    # If the previously detected color was red, interpret the signal's length
                    # to decode Morse code symbols: a short duration indicates a dot, and a longer duration indicates a dash.               
                    if self.last_detected_color == 5:  # Red
                        if signal_duration < 0.2 * self.first_signal_duration:
                            self.decoded_message += self.morse_code['dot']
                        elif signal_duration > 0.2 * self.first_signal_duration:# and signal_duration < 0.4 * self.first_signal_duration:
                            self.decoded_message += self.morse_code['dash']

                    # If the last detected color was white again, determine if the duration signifies a gap between symbols
                    # or a longer "word gap" between words in Morse code.
                    if self.last_detected_color == 6: # white
                        if signal_duration > 0.2 * self.first_signal_duration and signal_duration < 0.5 * self.first_signal_duration:
                            self.decoded_message += self.morse_code['gap']

                    # A longer duration than 0.5 is a "word gap," indicating a pause between words.
                    if signal_duration > 0.5 * self.first_signal_duration:  
                        self.decoded_message += self.morse_code['word_gap']

                    # Reset the timer at the end of processing each signal to accurately measure the next one.
                    self.signal_start_time = time.time()

                # Update the last detected color for reference in the next loop iteration.    
                self.last_detected_color = detected_color
            # Stop the robot if an obstacle is detected ahead or if a sequence indicating the end of the message is encountered.
            if obstacle_nearby or self.decoded_message.endswith(self.morse_code['gap'] * 7):
                self.drive_system.off(brake=True)
                break


    def adjust_heading(self, color):
        # This method adjusts the robot's heading based on the color detected by its sensors. It ensures the robot maintains its course along a path and reacts appropriately to color-coded instructions.

        # Retrieve the colors detected by the path_color_sensor and the line_color_sensor.
        # These readings help guide the robot's movement and interaction with the environment.
        path_color = self.path_color_sensor.color  # Color detected for Morse code/obstacle detection
        line_color = self.line_color_sensor.color  # Color detected for following a line.
        
        # Set base speeds for the left and right motors. These can be flexible adjusted based on sensor readings
        # to change the robot's heading.
        base_speed_left = 17
        base_speed_right = 17.5  # Slightly different speed for the right motor for fine-tuning.
        
        
        # Adjust right motor speed if path_color_sensor sees green
        if path_color == 3:  # 3 represents green
            # Increase right motor speed slightly
            base_speed_right += 1 

        # Adjust left motor speed if line_color_sensor sees black
        if line_color == 1:  # 1 represents black
            # Increase left motor speed slightly to correct position
            base_speed_left += 1.5

        # Apply the adjusted motor speeds to the motors, setting them to move with the specified speeds.
        # This dynamically adjusts the robot's heading based on the environmental conditions detected by the sensors.
        self.drive_motor_left.on(SpeedPercent(base_speed_left), brake=False)
        self.drive_motor_right.on(SpeedPercent(base_speed_right), brake=False)

    def display_results(self):
        # This method is responsible for providing the feedback on the decoded Morse code message. It utilizes both auditory (spoken) and visual (display) outputs to communicate the results.

        # Convert Morse code to a spoken format. For example, "." becomes "dot", "-" becomes "dash", and "|" becomes " word gap ".
        # This conversion makes it easier to understand the Morse code audibly.
        spoken_morse = self.decoded_message.replace('.', ' dot ').replace('-', ' dash ').replace('|', ' word gap ')

        # Use the robot's speaker to announce the Morse code message audibly.
        self.speaker.speak("Morse code message: " + spoken_morse)

        # Translate the Morse code message into alphanumeric text.
        # This is done by splitting the Morse code into words and symbols, decoding each, and then joining them back into a readable message.
        translated_message = self.translate_to_text(self.decoded_message)

        # Use the robot's speaker to announce the decoded alphanumeric message.
        self.speaker.speak("Decoded message: " + translated_message)

        # Display the alphanumeric message on the EV3 brick's screen for visual feedback.
        # This involves clearing any previous display, setting a font size, and rendering the message on the screen.
        self.display.clear()
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"  # Default font path in ev3dev.
        font_size = 20  # Change this to the desired font size.
        font = ImageFont.truetype(font_path, font_size)
        self.display.text_pixels(translated_message, 10, 20, font=font)  # Display the message at specified coordinates.
        self.display.update()
        time.sleep(20)  # Keep the message displayed for 20 seconds for readability.


    def translate_to_text(self, morse_code_message):
        # This method translates a Morse code string into its equivalent alphanumeric text.
        # It's a critical part of the robot's functionality, allowing it to convey the decoded message in a human-readable format.

        # Initialize an empty string to hold the final translated text message.
        text_message = ""

        # Split the Morse code message into words based on the 'word gap' symbol ('|').
        # Then iterate over each Morse code word to translate it into text.
        for word in morse_code_message.split(self.morse_code['word_gap']):
            # Initialize an empty string for the decoded word.
            decoded_word = ""
            # Split each word into its Morse code symbols (dots and dashes) based on the 'gap' symbol (' ').
            # Then iterate over each symbol to translate it into its alphanumeric equivalent.
            for symbol in word.split(self.morse_code['gap']):
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