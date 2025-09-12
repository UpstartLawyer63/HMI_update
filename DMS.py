

class DriverMonitoringSystem:
    """Driver monitoring system for detecting drowsiness and distraction"""
    
    def __init__(self):
        # Initialize MediaPipe Face Mesh
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        self.mp_drawing = mp.solutions.drawing_utils
        self.drawing_spec = self.mp_drawing.DrawingSpec(thickness=1, circle_radius=1)
        
        # Constants
        self.EYE_AR_THRESH = 0.20     # Eye aspect ratio threshold for drowsiness detection
        self.EYE_AR_CONSEC_FRAMES = 15  # Number of consecutive frames for drowsiness detection
        self.GAZE_THRESH_LEFT = 20     # Gaze threshold for looking left
        self.GAZE_THRESH_RIGHT = 20    # Gaze threshold for looking right
        self.HEAD_POSE_THRESH_LEFT = 10  # Head pose threshold for looking left
        self.HEAD_POSE_THRESH_RIGHT = 15  # Head pose threshold for looking right
        self.BLINK_THRESH = 0.21       # Threshold for detecting a blink
        self.BLINK_TIME_THRESH = 0.15  # Maximum time for a normal blink (seconds)
        self.DROWSY_TIME_THRESH = 1.5  # Time threshold for drowsiness detection (seconds)
        self.ALARM_COOLDOWN = 3.0      # Seconds between alerts
        
        # Define eye landmarks for MediaPipe Face Mesh
        # Left eye indices
        self.LEFT_EYE = [362, 385, 387, 263, 373, 380]
        # Right eye indices
        self.RIGHT_EYE = [33, 160, 158, 133, 153, 144]
        
        # Face direction landmarks (nose, left ear, right ear)
        self.NOSE_TIP = 4
        self.LEFT_EAR = 234
        self.RIGHT_EAR = 454
        
        # Initialize variables
        self.counter = 0
        self.blink_start_time = 0
        self.blink_durations = []
        self.is_blinking = False
        self.drowsy_start_time = 0
        self.is_eyes_closed = False
        self.alarm_on = False
        self.last_alarm_time = 0
        
        # Reference values when driver is looking at road
        # These should be calibrated for each driver and camera setup
        self.road_gaze_ref = -50  # Default value - will be updated with calibration
        self.road_pose_ref = 85   # Default value - will be updated with calibration
        
        # Calibration mode
        self.calibration_mode = False
        self.calibration_data = {"gaze": [], "head_pose": []}
        
        print("DriverMonitoringSystem initialized successfully")
    
    def calculate_EAR(self, eye_landmarks):
        """
        Calculate the Eye Aspect Ratio (EAR)
        A ratio of eye height to width that indicates open vs closed eyes
        """
        # Convert MediaPipe landmarks to coordinate points
        eye_points = [(landmark.x, landmark.y) for landmark in eye_landmarks]
        
        # Vertical eye landmarks (top to bottom)
        A = distance.euclidean(eye_points[1], eye_points[5])
        B = distance.euclidean(eye_points[2], eye_points[4])
        
        # Horizontal eye landmarks (left to right)
        C = distance.euclidean(eye_points[0], eye_points[3])
        
        # Eye Aspect Ratio
        ear = (A + B) / (2.0 * C)
        return ear
    
    def calculate_gaze_direction(self, landmarks, image_shape):
        """Calculate the approximate gaze direction based on eye landmarks"""
        # Get landmarks for both eyes
        left_eye_landmarks = [landmarks[i] for i in self.LEFT_EYE]
        right_eye_landmarks = [landmarks[i] for i in self.RIGHT_EYE]
        
        # Calculate centers of both eyes
        left_eye_center = np.mean(np.array([(pt.x * image_shape[1], pt.y * image_shape[0]) 
                                            for pt in left_eye_landmarks]), axis=0)
        right_eye_center = np.mean(np.array([(pt.x * image_shape[1], pt.y * image_shape[0]) 
                                            for pt in right_eye_landmarks]), axis=0)
        
        # Get pupil landmarks (approximated from iris points)
        left_pupil = (landmarks[474].x * image_shape[1], landmarks[474].y * image_shape[0])
        right_pupil = (landmarks[475].x * image_shape[1], landmarks[475].y * image_shape[0])
        
        # Calculate the displacement of pupils from eye centers
        left_displacement = np.array(left_pupil) - left_eye_center
        right_displacement = np.array(right_pupil) - right_eye_center
        
        # Average displacement
        avg_displacement = (left_displacement + right_displacement) / 2
        
        # Normalize the displacement to get direction
        angle = np.degrees(np.arctan2(avg_displacement[1], avg_displacement[0]))
        
        # Adjust for the front-right camera position (camera is to the driver's right side)
        # A positive offset helps account for the driver naturally looking slightly left relative to camera
        camera_offset = 30.0  # appropriate for front-right position
        adjusted_angle = angle - camera_offset
        
        return adjusted_angle
    
    def calculate_head_pose(self, landmarks, image_shape):
        """Calculate the head pose based on nose and ears"""
        # Get 3D coordinates of landmarks
        nose = np.array([landmarks[self.NOSE_TIP].x, landmarks[self.NOSE_TIP].y, landmarks[self.NOSE_TIP].z])
        left_ear = np.array([landmarks[self.LEFT_EAR].x, landmarks[self.LEFT_EAR].y, landmarks[self.LEFT_EAR].z])
        right_ear = np.array([landmarks[self.RIGHT_EAR].x, landmarks[self.RIGHT_EAR].y, landmarks[self.RIGHT_EAR].z])
        
        # Calculate ear-to-ear vector
        ear_vector = right_ear - left_ear
        
        # Calculate vector from midpoint of ears to nose
        mid_ear = (left_ear + right_ear) / 2
        nose_to_mid_ear = nose - mid_ear
        
        # Normalize vectors
        ear_vector = ear_vector / np.linalg.norm(ear_vector)
        nose_to_mid_ear = nose_to_mid_ear / np.linalg.norm(nose_to_mid_ear)
        
        # Cross product gives a vector perpendicular to the face plane
        face_normal = np.cross(ear_vector, nose_to_mid_ear)
        face_normal = face_normal / np.linalg.norm(face_normal)
        
        # Dot product with camera direction adjusted for front-right camera position
        # The camera is positioned at the front-right of the driver
        camera_angle_rad = np.radians(30.0)  # horizontal angle
        camera_y_angle_rad = np.radians(5.0)  # slight vertical angle if camera is higher/lower than eye level
        camera_direction = np.array([np.sin(camera_angle_rad), np.sin(camera_y_angle_rad), -np.cos(camera_angle_rad)])
        
        # Calculate angle between face normal and camera direction
        angle = np.arccos(np.clip(np.dot(face_normal, camera_direction), -1.0, 1.0))
        angle_deg = np.degrees(angle)
        
        return angle_deg
    
    def process_frame(self, frame):
        """
        Process a frame to detect drowsiness and distraction
        Returns: processed_frame, status_dict
        """
        try:
            # Create a copy of the frame to draw on
            processed_frame = frame.copy()
            
            # Convert the BGR image to RGB
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # To improve performance, mark the image as not writeable
            rgb_image.flags.writeable = False
            results = self.face_mesh.process(rgb_image)
            
            # Initialize status dictionary
            status = {
                "drowsy": False,
                "looking_away": False,
                "direction": None,
                "face_detected": False,
                "ear": 0.0,
                "gaze": 0.0,
                "head_pose": 0.0
            }
            
            # Process if face landmarks were detected
            if results.multi_face_landmarks:
                status["face_detected"] = True
                face_landmarks = results.multi_face_landmarks[0].landmark
                h, w, c = processed_frame.shape
                
                # Extract eye landmarks
                left_eye_landmarks = [face_landmarks[i] for i in self.LEFT_EYE]
                right_eye_landmarks = [face_landmarks[i] for i in self.RIGHT_EYE]
                
                # Convert normalized coordinates to pixel coordinates
                left_eye_points = [(int(pt.x * w), int(pt.y * h)) for pt in left_eye_landmarks]
                right_eye_points = [(int(pt.x * w), int(pt.y * h)) for pt in right_eye_landmarks]
                
                # Draw eye contours
                cv2.polylines(processed_frame, [np.array(left_eye_points)], True, (0, 255, 0), 1)
                cv2.polylines(processed_frame, [np.array(right_eye_points)], True, (0, 255, 0), 1)
                
                # Calculate EAR for both eyes
                left_ear = self.calculate_EAR(left_eye_landmarks)
                right_ear = self.calculate_EAR(right_eye_landmarks)
                ear = (left_ear + right_ear) / 2.0
                status["ear"] = ear
                
                # Calculate gaze direction and head pose
                gaze_angle = self.calculate_gaze_direction(face_landmarks, (h, w))
                head_pose = self.calculate_head_pose(face_landmarks, (h, w))
                status["gaze"] = gaze_angle
                status["head_pose"] = head_pose
                
                current_time = time.time()
                
                # Handle calibration if in calibration mode
                if self.calibration_mode:
                    self.calibration_data["gaze"].append(gaze_angle)
                    self.calibration_data["head_pose"].append(head_pose)
                    if len(self.calibration_data["gaze"]) > 100:  # Collect 100 samples
                        self.road_gaze_ref = np.mean(self.calibration_data["gaze"])
                        self.road_pose_ref = np.mean(self.calibration_data["head_pose"])
                        self.calibration_mode = False
                        return processed_frame, {**status, "calibration_complete": True}
                    else:
                        # Draw calibration progress
                        progress = len(self.calibration_data["gaze"])
                        cv2.putText(processed_frame, f"Calibrating: {progress}/100", (10, 30),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        return processed_frame, {**status, "calibrating": True, "progress": progress}
                
                # Calculate deviations from "looking at road" position
                gaze_deviation = gaze_angle - self.road_gaze_ref
                pose_deviation = head_pose - self.road_pose_ref
                
                # Visual indicators
                cv2.putText(processed_frame, f"EAR: {ear:.2f}", (10, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(processed_frame, f"Gaze: {gaze_angle:.2f} deg", (10, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(processed_frame, f"Head: {head_pose:.2f} deg", (10, 90),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Enhanced drowsiness detection using blink duration
                if not self.is_blinking and ear < self.BLINK_THRESH:
                    # Blink started
                    self.is_blinking = True
                    self.blink_start_time = current_time
                    
                    # Drowsiness tracking - start tracking if eyes remain closed
                    if not self.is_eyes_closed:
                        self.is_eyes_closed = True
                        self.drowsy_start_time = current_time
                
                elif self.is_blinking and ear >= self.BLINK_THRESH:
                    # Blink ended
                    self.is_blinking = False
                    blink_duration = current_time - self.blink_start_time
                    
                    # Reset drowsiness tracking
                    self.is_eyes_closed = False
                    
                    # Store normal blinks for analysis
                    if blink_duration < self.BLINK_TIME_THRESH:
                        self.blink_durations.append(blink_duration)
                        # Keep only the most recent 30 blinks
                        if len(self.blink_durations) > 30:
                            self.blink_durations.pop(0)
                
                # Check if eyes have been closed for too long
                if self.is_eyes_closed and (current_time - self.drowsy_start_time) > self.DROWSY_TIME_THRESH:
                    status["drowsy"] = True
                
                # Check if looking away, using separate thresholds for left and right
                if gaze_deviation > self.GAZE_THRESH_RIGHT or pose_deviation > self.HEAD_POSE_THRESH_RIGHT:
                    # Looking to the right
                    status["looking_away"] = True
                    status["direction"] = "right"
                elif gaze_deviation < -self.GAZE_THRESH_LEFT or pose_deviation < -self.HEAD_POSE_THRESH_LEFT:
                    # Looking to the left
                    status["looking_away"] = True
                    status["direction"] = "left"
                
                # Determine alert status and display warning
                alert_cooldown_passed = (current_time - self.last_alarm_time) > self.ALARM_COOLDOWN
                
                if status["drowsy"]:
                    cv2.putText(processed_frame, "DROWSINESS ALERT!", (10, 180),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    if alert_cooldown_passed:
                        self.last_alarm_time = current_time
                
                if status["looking_away"]:
                    direction_text = f"EYES ON ROAD! (Looking {status['direction']})"
                    cv2.putText(processed_frame, direction_text, (10, 210),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    if alert_cooldown_passed:
                        self.last_alarm_time = current_time
                        
            return processed_frame, status
            
        except Exception as e:
            print(f"Error in DMS process_frame: {e}")
            # Return original frame and empty status in case of error
            return frame, {"face_detected": False, "error": str(e)}
    
    def start_calibration(self):
        """Start the calibration process"""
        self.calibration_mode = True
        self.calibration_data = {"gaze": [], "head_pose": []}
        print("DMS calibration started")
        
    def release(self):
        """Release resources"""
        print("DMS resources released")
        pass