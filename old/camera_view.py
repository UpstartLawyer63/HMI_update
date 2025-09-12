import os
import sys
import cv2
import numpy as np
import time
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, 
                             QFrame, QHBoxLayout, QSizePolicy, 
                             QPushButton, QMainWindow, QMessageBox)
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt, QTimer, pyqtSlot

class CameraView(QMainWindow):
    def __init__(self):
        super(CameraView, self).__init__()
        print("Initializing CameraView")
        self.setWindowTitle("Driver Monitoring System")
        
        # Create central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Main layout
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Initialize UI components
        self.initUI()
        
        # Initialize camera variables
        self.cap = None
        self.camera_active = False
        
        # Initialize timer for camera updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.updateFrame)
        
        # Initialize face detector from OpenCV
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Calibration variables
        self.calibrated_h_angle = None
        self.calibrated_v_angle = None
        self.last_direction = None
        self.start_time = time.time()
        self.angle_threshold = 5  # Degrees deviation for gaze shift
        self.perform_calibration = False
        
        # Direction tracking variables
        self.sustained_reported = False
        self.center_gaze_time = time.time()
        self.temp_direction = None
        self.temp_direction_start = time.time()
        self.last_warning_time = 0
        self.is_looking_center = False

        # Touch sensor variables
        self.hands_on_wheel = True  # Initially assume hands are on wheel
        self.hands_off_time = None  # Time when hands were removed
        self.first_warning_issued = False  # Flag for first warning
        self.second_warning_issued = False  # Flag for second warning
        
        # Show initial state
        self.showCameraOffMessage()
    
    def initUI(self):
        # Create camera view frame
        self.camera_frame = QFrame()
        self.camera_frame.setObjectName("camera-frame")
        self.camera_frame.setStyleSheet("""
            #camera-frame {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
            }
        """)
        
        # Camera frame layout
        camera_layout = QVBoxLayout(self.camera_frame)
        camera_layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QLabel("Driver Monitoring System")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 5px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        camera_layout.addWidget(title)
        
        # Camera display
        self.camera_label = QLabel()
        self.camera_label.setMinimumHeight(400)
        self.camera_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.camera_label.setStyleSheet("""
            background-color: black;
            border-radius: 5px;
        """)
        self.camera_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        camera_layout.addWidget(self.camera_label)
        
        # Status indicators
        self.status_frame = QFrame()
        status_layout = QHBoxLayout(self.status_frame)
        status_layout.setContentsMargins(5, 5, 5, 5)
        
        # Gaze direction indicator
        self.direction_indicator = QLabel("Gaze Direction: ")
        self.direction_status = QLabel("Unknown")
        self.direction_status.setStyleSheet("color: gray; font-weight: bold;")
        status_layout.addWidget(self.direction_indicator)
        status_layout.addWidget(self.direction_status)
        
        status_layout.addStretch()

        # Wheel status indicator
        self.wheel_indicator = QLabel("Hands: ")
        self.wheel_status = QLabel("On Wheel")
        self.wheel_status.setStyleSheet("color: green; font-weight: bold;")
        status_layout.addWidget(self.wheel_indicator)
        status_layout.addWidget(self.wheel_status)
        
        # Attention indicator
        self.attention_indicator = QLabel("Attention: ")
        self.attention_status = QLabel("Unknown")
        self.attention_status.setStyleSheet("color: gray; font-weight: bold;")
        status_layout.addWidget(self.attention_indicator)
        status_layout.addWidget(self.attention_status)
        
        camera_layout.addWidget(self.status_frame)
        self.status_frame.setVisible(False)  # Hide initially
        
        # Add camera frame to main layout
        self.main_layout.addWidget(self.camera_frame)
        
        # Control buttons
        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        
        # Camera button
        self.camera_button = QPushButton("Turn On Camera")
        self.camera_button.setCheckable(True)
        self.camera_button.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                color: white;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:checked {
                background-color: #f44336;
            }
            QPushButton:hover {
                background-color: #0d8aee;
            }
            QPushButton:checked:hover {
                background-color: #d32f2f;
            }
        """)
        self.camera_button.clicked.connect(self.toggleCamera)
        control_layout.addWidget(self.camera_button)
        
        # Add spacer
        control_layout.addStretch()
        
        # Calibrate button
        self.calibrate_button = QPushButton("Calibrate")
        self.calibrate_button.setEnabled(False)  # Disabled until camera is on
        self.calibrate_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #888888;
            }
        """)
        self.calibrate_button.clicked.connect(self.calibrateSystem)
        control_layout.addWidget(self.calibrate_button)
        
        # Add control frame to main layout
        self.main_layout.addWidget(control_frame)
    
    def showCameraOffMessage(self):
        """Show the Camera Off message in the camera label"""
        # Get dimensions of the camera label
        width = max(640, self.camera_label.width())
        height = max(480, self.camera_label.height())
        
        # Create a black image with text
        black_image = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Calculate text position and size
        font_scale = max(1.0, min(width, height) / 400)
        thickness = max(2, int(font_scale * 2))
        text = "Camera Off"
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)[0]
        
        # Center the text
        text_x = (width - text_size[0]) // 2
        text_y = (height + text_size[1]) // 2
        
        # Draw the text
        cv2.putText(black_image, text, (text_x, text_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), thickness)
        
        # Convert to QImage and then QPixmap
        q_img = QImage(black_image.data, width, height, width*3, QImage.Format.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(q_img)
        
        # Show in the label
        self.camera_label.setPixmap(pixmap)
    
    def toggleCamera(self, checked):
        print(f"Toggle camera button clicked, checked: {checked}")
        if isinstance(checked, bool):
            self.camera_active = checked
            # self.camera_button.setChecked(self.camera_active)
        else:
            # self.camera_active = not self.camera_active
            self.camera_button.setChecked(self.camera_active)
        
        if self.camera_active:
            # Update button text
            self.camera_button.setText("Turn Off Camera")
            
            print("Attempting to activate camera...")
            try:
                # Try to open the camera
                self.cap = cv2.VideoCapture(0)
                if not self.cap.isOpened():
                    print("Failed to open camera")
                    self.camera_active = False
                    self.camera_button.setChecked(False)
                    self.camera_button.setText("Turn On Camera")
                    self.showCameraOffMessage()
                    QMessageBox.critical(self, "Camera Error", "Failed to open camera device.")
                    return
                
                print("Camera opened successfully, starting timer")
                self.timer.start(30)  # Update every 30ms (approx. 33 fps)
                
                # Enable calibration button
                self.calibrate_button.setEnabled(True)
                
                # Show status indicators
                self.status_frame.setVisible(True)
            except Exception as e:
                print(f"Error opening camera: {e}")
                self.camera_active = False
                self.camera_button.setChecked(False)
                self.camera_button.setText("Turn On Camera")
                self.showCameraOffMessage()
                QMessageBox.critical(self, "Camera Error", f"Error initializing camera: {str(e)}")
        else:
            # Update button text
            self.camera_button.setText("Turn On Camera")
            
            print("Deactivating camera...")
            # Stop the camera
            if self.timer.isActive():
                self.timer.stop()
            
            if self.cap and self.cap.isOpened():
                self.cap.release()
                self.cap = None
            
            # Disable calibration button
            self.calibrate_button.setEnabled(False)
            
            # Hide status indicators
            self.status_frame.setVisible(False)
            
            # Show camera off message
            self.showCameraOffMessage()
    
    def calibrateSystem(self):
        """Start calibration for gaze detection"""
        if not self.camera_active or not self.cap or not self.cap.isOpened():
            return
        
        # Show calibration instructions
        QMessageBox.information(self, "Calibration", 
                                "Please look straight ahead at the road.\n\n"
                                "Calibration will begin when you click OK.\n\n"
                                "Keep looking forward until calibration completes.")
        
        # Set flag to perform calibration on next frame
        self.perform_calibration = True
    
    def detect_iris(self, eye_roi):
        """Detect iris position using thresholding and contour detection"""
        # Apply histogram equalization to enhance contrast
        eye_roi = cv2.equalizeHist(eye_roi)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(eye_roi, (7, 7), 0)
        
        # Use adaptive thresholding to handle different lighting conditions
        _, thresh = cv2.threshold(blurred, 45, 255, cv2.THRESH_BINARY_INV)
        
        # Morphological operations to clean up the thresholded image
        kernel = np.ones((3, 3), np.uint8)
        thresh = cv2.erode(thresh, kernel, iterations=1)
        thresh = cv2.dilate(thresh, kernel, iterations=2)
        
        # Find contours in the thresholded image
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None, None, thresh
        
        # Find the largest contour - this should be the iris/pupil
        largest_contour = max(contours, key=cv2.contourArea)
        
        # Filter based on contour area to eliminate small noise
        if cv2.contourArea(largest_contour) < 20:
            return None, None, thresh
        
        # Calculate the centroid of the largest contour
        M = cv2.moments(largest_contour)
        if M["m00"] == 0:
            return None, None, thresh
        
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
        
        return (cx, cy), largest_contour, thresh
    
    def detect_eyes(self, face_roi, face_rect):
        """Detect eye regions using facial landmarks and region segmentation"""
        x, y, w, h = face_rect
        
        # Define eye regions based on facial proportions
        # Left eye region (from the person's perspective)
        eye_w = int(w * 0.3)
        eye_h = int(h * 0.2)
        eye_y = int(y + h * 0.25)
        
        left_eye_x = int(x + w * 0.2)
        right_eye_x = int(x + w * 0.55)
        
        left_eye_rect = (left_eye_x, eye_y, eye_w, eye_h)
        right_eye_rect = (right_eye_x, eye_y, eye_w, eye_h)
        
        # Extract eye regions
        left_eye_roi = face_roi[eye_y:eye_y+eye_h, left_eye_x:left_eye_x+eye_w]
        right_eye_roi = face_roi[eye_y:eye_y+eye_h, right_eye_x:right_eye_x+eye_w]
        
        # Ensure ROIs are valid
        if left_eye_roi.size == 0 or right_eye_roi.size == 0:
            return None, None, None, None
        
        return left_eye_roi, right_eye_roi, left_eye_rect, right_eye_rect
    
    def calculate_gaze_angle(self, iris_position, eye_rect):
        """Calculate gaze angle based on iris position relative to eye rect"""
        if iris_position is None:
            return None, None
        
        iris_x, iris_y = iris_position
        ex, ey, ew, eh = eye_rect
        
        # Calculate the relative position of the iris within the eye
        # 0.5 is the center, values < 0.5 mean looking left/up, > 0.5 mean looking right/down
        rel_x = iris_x / ew
        rel_y = iris_y / eh
        
        # Exaggerate the effect for better sensitivity
        # Map the 0.3-0.7 range (typical iris movement range) to -30 to +30 degrees
        h_angle = (rel_x - 0.5) * 120
        
        # Adjust vertical angle calculation to be more sensitive to downward gaze
        # Bias the center point upward slightly (0.4 instead of 0.5) to better detect downward gaze
        v_angle = (rel_y - 0.4) * 150  # Increased multiplier for more sensitivity
        
        return h_angle, v_angle
    
    def get_gaze_direction(self, h_angle, v_angle, h_calib, v_calib, threshold):
        """Determine gaze direction based on calibrated angles"""
        if h_calib is None or v_calib is None:
            return "UNCALIBRATED"
        
        h_direction = "CENTER"
        v_direction = "CENTER"
        
        # Calculate deviation from calibration
        h_dev = h_angle - h_calib
        v_dev = v_angle - v_calib
        
        # Determine horizontal direction with increased sensitivity
        if h_dev < -threshold:
            h_direction = "LEFT"
        elif h_dev > threshold:
            h_direction = "RIGHT"
        
        # Determine vertical direction with increased sensitivity
        # Use a lower threshold for downward gaze detection
        down_threshold = threshold * 0.7  # More sensitive for downward detection
        if v_dev < -threshold:
            v_direction = "UP"
        elif v_dev > down_threshold:  # Reduced threshold for DOWN detection
            v_direction = "DOWN"
        
        # Combine directions
        if h_direction == "CENTER" and v_direction == "CENTER":
            return "CENTER"
        elif h_direction == "CENTER":
            return v_direction
        elif v_direction == "CENTER":
            return h_direction
        else:
            return f"{v_direction}-{h_direction}"
    
    def update_direction(self, new_direction):
        """Update direction tracking and indicators"""
        current_time = time.time()
        
        # Immediate update for distraction tracking
        if new_direction == "CENTER":
            if not self.is_looking_center:
                self.is_looking_center = True
                self.center_gaze_time = current_time
                print("Driver looking at center")
                self.attention_status.setText("On Road")
                self.attention_status.setStyleSheet("color: green; font-weight: bold;")
        else:
            if self.is_looking_center:
                self.is_looking_center = False
                print(f"Driver looking away from center ({new_direction})")
                self.attention_status.setText(f"Looking {new_direction}")
                self.attention_status.setStyleSheet("color: red; font-weight: bold;")
        
        # Check for distraction warning - issue immediately when threshold reached
        if not self.is_looking_center:
            distracted_time = current_time - self.center_gaze_time
            if new_direction == "UNCALIBRATED":
                print(f'WARNING: DMS system is not calibrated!')
            elif distracted_time >= 3 and current_time - self.last_warning_time >= 2.5:
                # Warning if not looking at center for more than 3 seconds
                print(f'WARNING: Driver distraction detected! Looking {new_direction} for {int(distracted_time)} seconds')
                self.last_warning_time = current_time
                
                # Update attention status with time
                self.attention_status.setText(f"Distracted ({int(distracted_time)}s)")
                self.attention_status.setStyleSheet("color: red; font-weight: bold;")
        
        # Direction change tracking (for stable direction reporting)
        if new_direction != self.temp_direction:
            self.temp_direction = new_direction
            self.temp_direction_start = current_time
            
            # Update direction status immediately but indicate it's preliminary
            self.direction_status.setText(f"{new_direction}")
            
            return
        
        # Only consider it a real direction change if it persists for 1 second (reduced from 2.5)
        if current_time - self.temp_direction_start >= 1:
            if self.temp_direction != self.last_direction:
                # Confirmed direction change after 1 second
                print(f'Gaze direction changed to: {self.temp_direction}')
                self.direction_status.setText(f"{self.temp_direction}")
                
                # Color code direction status
                if self.temp_direction == "CENTER":
                    self.direction_status.setStyleSheet("color: green; font-weight: bold;")
                else:
                    self.direction_status.setStyleSheet("color: orange; font-weight: bold;")
                
                self.last_direction = self.temp_direction
                self.start_time = current_time
                self.sustained_reported = False
            elif current_time - self.start_time >= 5 and not self.sustained_reported:
                # Only report sustained gaze once after 5 seconds
                print(f'SUSTAINED GAZE DETECTED: {self.temp_direction} (5+ seconds)')
                self.sustained_reported = True
                
                # Update direction status to show sustained gaze
                self.direction_status.setText(f"{self.temp_direction} (Sustained)")
                
                # If not CENTER, make it red for sustained non-center gaze
                if self.temp_direction != "CENTER":
                    self.direction_status.setStyleSheet("color: red; font-weight: bold;")
    
    def updateFrame(self):
        if not self.cap or not self.cap.isOpened():
            return
            
        ret, frame = self.cap.read()
        if ret:
            # Flip the frame horizontally for mirror effect
            frame = cv2.flip(frame, 1)
            frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(frame_gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100))
            
            h_angles = []
            v_angles = []
            
            for (x, y, w, h) in faces:
                face_rect = (x, y, w, h)
                face_roi = frame_gray[y:y+h, x:x+w]
                
                # Draw face rectangle
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                
                # Detect eye regions
                left_eye_roi, right_eye_roi, left_eye_rect, right_eye_rect = self.detect_eyes(frame_gray, face_rect)
                
                if left_eye_roi is None or right_eye_roi is None:
                    continue
                
                # Extract eye rectangle coordinates
                lex, ley, lew, leh = left_eye_rect
                rex, rey, rew, reh = right_eye_rect
                
                # Draw eye rectangles
                cv2.rectangle(frame, (lex, ley), (lex+lew, ley+leh), (0, 255, 0), 2)
                cv2.rectangle(frame, (rex, rey), (rex+rew, rey+reh), (0, 255, 0), 2)
                
                # Detect iris in both eyes
                left_iris, left_contour, left_thresh = self.detect_iris(left_eye_roi)
                right_iris, right_contour, right_thresh = self.detect_iris(right_eye_roi)
                
                # Calculate gaze angles
                if left_iris is not None:
                    left_h, left_v = self.calculate_gaze_angle(left_iris, (0, 0, lew, leh))
                    if left_h is not None and left_v is not None:
                        h_angles.append(left_h)
                        v_angles.append(left_v)
                        # Draw iris center on the frame
                        cv2.circle(frame, (lex + left_iris[0], ley + left_iris[1]), 3, (0, 0, 255), -1)
                
                if right_iris is not None:
                    right_h, right_v = self.calculate_gaze_angle(right_iris, (0, 0, rew, reh))
                    if right_h is not None and right_v is not None:
                        h_angles.append(right_h)
                        v_angles.append(right_v)
                        # Draw iris center on the frame
                        cv2.circle(frame, (rex + right_iris[0], rey + right_iris[1]), 3, (0, 0, 255), -1)
            
            # Average the angles from both eyes if available
            if len(h_angles) > 0 and len(v_angles) > 0:
                avg_h_angle = sum(h_angles) / len(h_angles)
                avg_v_angle = sum(v_angles) / len(v_angles)
                
                # Handle calibration if needed
                if hasattr(self, 'perform_calibration') and self.perform_calibration:
                    self.calibrated_h_angle = avg_h_angle
                    self.calibrated_v_angle = avg_v_angle
                    print(f'Calibration set: H={self.calibrated_h_angle:.2f}, V={self.calibrated_v_angle:.2f}')
                    
                    # Reset flag
                    self.perform_calibration = False
                    
                    # Show confirmation
                    QMessageBox.information(self, "Calibration Complete", 
                                           f"Calibration completed successfully!\n\n"
                                           f"Reference values:\n"
                                           f"Horizontal: {self.calibrated_h_angle:.2f}\n"
                                           f"Vertical: {self.calibrated_v_angle:.2f}")
                
                # Get gaze direction
                direction = self.get_gaze_direction(avg_h_angle, avg_v_angle, 
                                                 self.calibrated_h_angle, 
                                                 self.calibrated_v_angle, 
                                                 self.angle_threshold)
                
                # Update direction tracking
                self.update_direction(direction)
                
                # Display gaze info on frame
                cv2.putText(frame, f"Gaze: {direction}", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            else:
                current_time = time.time()
                distracted_time = current_time - self.center_gaze_time
                print(f'No face detected for {distracted_time}. Please pay attention to the road!')
                
                # Update UI to show no face detected
                self.direction_status.setText("No Face")
                self.direction_status.setStyleSheet("color: red; font-weight: bold;")
                self.attention_status.setText("Unknown")
                self.attention_status.setStyleSheet("color: gray; font-weight: bold;")
            
            # Convert the frame to QImage and QPixmap
            h, w, c = frame.shape
            q_img = QImage(frame.data, w, h, w*c, QImage.Format.Format_RGB888).rgbSwapped()
            pixmap = QPixmap.fromImage(q_img)
            
            # Scale pixmap to fit the label while maintaining aspect ratio
            label_size = self.camera_label.size()
            pixmap = pixmap.scaled(label_size, 
                                  Qt.AspectRatioMode.KeepAspectRatio, 
                                  Qt.TransformationMode.SmoothTransformation)
            
            # Show in the label
            self.camera_label.setPixmap(pixmap)

            if hasattr(self, 'hands_on_wheel') and not self.hands_on_wheel:
                self.check_hands_warnings()
        else:
            print("Failed to capture frame")
            self.showCameraOffMessage()
    
    def update_hands_status(self, status):
        """Update the status of driver's hands on the steering wheel
        
        Args:
            status (int): 1 if hands are on the wheel, 0 if hands are off
        """
        current_time = time.time()
        
        if status == 1:
            # Hands are on the wheel
            if not self.hands_on_wheel:
                print("Driver's hands returned to the wheel")
                # Reset all tracking variables
                self.hands_on_wheel = True
                self.hands_off_time = None
                self.first_warning_issued = False
                self.second_warning_issued = False
                
                # Update UI if needed
                if hasattr(self, 'wheel_status'):
                    self.wheel_status.setText("On Wheel")
                    self.wheel_status.setStyleSheet("color: green; font-weight: bold;")
        
        elif status == 0:
            # Hands are off the wheel
            if self.hands_on_wheel:
                print("Driver's hands removed from the wheel")
                # Start tracking hands-off time
                self.hands_on_wheel = False
                self.hands_off_time = current_time
                
                # Update UI if needed
                if hasattr(self, 'wheel_status'):
                    self.wheel_status.setText("Off Wheel")
                    self.wheel_status.setStyleSheet("color: red; font-weight: bold;")
        
        # Check for warnings if hands are off
        if not self.hands_on_wheel and self.hands_off_time is not None:
            self.check_hands_warnings()

    def check_hands_warnings(self):
        """Check if warnings should be issued for hands off steering wheel"""
        if self.hands_on_wheel or self.hands_off_time is None:
            return
        
        current_time = time.time()
        hands_off_duration = current_time - self.hands_off_time
        
        # First warning after 7 seconds (no later than)
        if not self.first_warning_issued and hands_off_duration >= 7.0:
            self.issue_hands_warning(1, hands_off_duration)
            self.first_warning_issued = True
        
        # Second warning between 9-11 seconds
        if self.first_warning_issued and not self.second_warning_issued and hands_off_duration >= 9.0 and hands_off_duration <= 11.0:
            self.issue_hands_warning(2, hands_off_duration)
            self.second_warning_issued = True

    def issue_hands_warning(self, warning_level, duration):
        """Issue a warning about hands off the steering wheel
        
        Args:
            warning_level (int): 1 for first warning, 2 for second warning
            duration (float): Time in seconds that hands have been off the wheel
        """
        if warning_level == 1:
            print(f"WARNING LEVEL 1: Driver's hands off the wheel for {duration:.1f} seconds!")
            # Here you could add code to play a sound, flash UI elements, etc.
            
            # Update UI if needed
            if hasattr(self, 'wheel_status'):
                self.wheel_status.setText(f"Off Wheel ({int(duration)}s) - WARNING")
        else:
            print(f"WARNING LEVEL 2: Driver's hands off the wheel for {duration:.1f} seconds! CRITICAL!")
            # Here you could add code for a more urgent warning
            
            # Update UI if needed
            if hasattr(self, 'wheel_status'):
                self.wheel_status.setText(f"Off Wheel ({int(duration)}s) - CRITICAL")
                self.wheel_status.setStyleSheet("color: red; font-weight: bold; background-color: yellow;")
        
    def resizeEvent(self, event):
        """Handle resize events to update camera display size"""
        super().resizeEvent(event)
        
        # If camera is active, update the frame to fit the new size
        if self.camera_active and self.cap and self.cap.isOpened():
            self.updateFrame()
        else:
            # Update the "Camera Off" overlay
            self.showCameraOffMessage()
    
    def closeEvent(self, event):
        """Clean up resources when closing the application"""
        print("Closing CameraView and releasing resources")
        
        # Stop timer if active
        if self.timer.isActive():
            self.timer.stop()
        
        # Release camera if open
        if self.cap and self.cap.isOpened():
            self.cap.release()
        
        # Accept the close event
        event.accept()


# For standalone testing
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = CameraView()
    window.show()
    
    sys.exit(app.exec())
