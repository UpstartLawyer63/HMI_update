from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel, 
                             QHBoxLayout, QGraphicsOpacityEffect)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QPixmap, QIcon, QColor
from PyQt6.QtSvg import QSvgWidget

class ParkView(QWidget):
    def __init__(self, parent=None):
        super(ParkView, self).__init__(parent)
        
        # Constants for parking messages (similar to JS version)
        self.PARKING_MESSAGE = {
            "AVAILABLE": "Auto Park Available!",
            "NOT_AVAILABLE": "Auto Park Not Available",
            "SEARCHING": "Searching for Parking Space",
            "DETECTED": "Parking Space Detected!",
            "NOT_DETECTED": "No Parking Space Detected",
            "READY": "Auto Parking Ready!",
            "IN_PROGRESS": "Auto Parking",
            "FINISHED": "Auto Parking Finished!",
            "ERROR": "Something went wrong..."
        }
        
        # Initialize state
        self.current_status = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_loading_animation)
        self.loading_state = 0
        
        # Create main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        self.main_layout.setAlignment(Qt.AlignCenter)
        
        # Create UI elements (analogous to the HTML elements)
        self.setup_ui()
        
        # Set initial status
        self.update_auto_park("NOT_AVAILABLE")
    
    def setup_ui(self):
        """Create all UI components for the parking view"""
        
        # Status text label
        self.status_label = QLabel()
        self.status_label.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            margin: 15px;
            color: #333;
        """)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.status_label)
        
        # Activate button container
        self.activate_container = QWidget()
        activate_layout = QVBoxLayout(self.activate_container)
        activate_layout.setContentsMargins(10, 10, 10, 10)
        
        self.activate_button = self.create_circular_button("Activate")
        self.activate_button.clicked.connect(self.activate_auto_park)
        activate_layout.addWidget(self.activate_button, 0, Qt.AlignCenter)
        
        self.main_layout.addWidget(self.activate_container)
        
        # Parking off warning
        self.parking_off = QWidget()
        parking_off_layout = QVBoxLayout(self.parking_off)
        
        self.parking_off_label = QLabel("Stop Completely or Wait to Activate")
        self.parking_off_label.setStyleSheet("""
            background-color: rgb(237, 232, 232);
            color: #333;
            padding: 5px 20px;
            border-radius: 8px;
            font-size: 18px;
            font-weight: bold;
        """)
        parking_off_layout.addWidget(self.parking_off_label, 0, Qt.AlignCenter)
        
        # Add striped background effect
        self.parking_off.setStyleSheet("""
            background: repeating-linear-gradient(-45deg, rgba(0, 0, 0, 0.3), 
                                                rgba(0, 0, 0, 0.3), 
                                                transparent 2px, 
                                                transparent 4px);
            border-radius: 10px;
        """)
        
        self.main_layout.addWidget(self.parking_off)
        
        # SVG displays
        self.parking_search_svg = QSvgWidget("img/autopark/parking-search.svg")
        self.parking_search_svg.setFixedHeight(300)
        self.main_layout.addWidget(self.parking_search_svg)
        
        self.parking_found_svg = QLabel()
        self.parking_found_svg.setPixmap(QPixmap("img/autopark/parking-found.svg"))
        self.parking_found_svg.setAlignment(Qt.AlignCenter)
        self.parking_found_svg.setFixedHeight(300)
        self.main_layout.addWidget(self.parking_found_svg)
        
        self.parking_not_found_svg = QLabel()
        self.parking_not_found_svg.setPixmap(QPixmap("img/autopark/parking-not-found.svg"))
        self.parking_not_found_svg.setAlignment(Qt.AlignCenter)
        self.parking_not_found_svg.setFixedHeight(300)
        self.main_layout.addWidget(self.parking_not_found_svg)
        
        # Start button container
        self.start_container = QWidget()
        start_layout = QVBoxLayout(self.start_container)
        start_layout.setContentsMargins(10, 10, 10, 10)
        
        self.start_button = self.create_circular_button("Start")
        self.start_button.clicked.connect(self.start_auto_park)
        start_layout.addWidget(self.start_button, 0, Qt.AlignCenter)
        
        self.main_layout.addWidget(self.start_container)
        
        # In progress indicator
        self.in_progress = QLabel("In Progress")
        self.in_progress.setStyleSheet("""
            font-size: 40px;
            font-weight: bold;
            margin: 20px;
            padding: 20px;
            text-align: center;
        """)
        self.in_progress.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.in_progress)
        
        # Finished container
        self.finished = QWidget()
        finished_layout = QVBoxLayout(self.finished)
        
        self.finish_button = QPushButton("Please hit the brakes and push this button.")
        self.finish_button.clicked.connect(self.finish_auto_park)
        self.finish_button.setStyleSheet("""
            width: 80%;
            height: 100%;
            color: black;
            font-weight: bold;
            text-align: center;
            font-size: 20px;
            border: none;
            border-radius: 40px;
            background: linear-gradient(to bottom, #24e424, #228b22);
            padding: 30px;
        """)
        finished_layout.addWidget(self.finish_button)
        
        self.main_layout.addWidget(self.finished)
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_auto_park)
        self.cancel_button.setStyleSheet("""
            background-color: #d10000;
            color: white;
            font-size: 16px;
            font-weight: bold;
            padding: 15px 20px;
            border: none;
            border-radius: 8px;
            margin-top: 20px;
        """)
        
        self.main_layout.addWidget(self.cancel_button)
        
    def create_circular_button(self, text):
        """Create a circular button with styling similar to CSS"""
        button = QPushButton(text)
        button.setFixedSize(225, 225)
        button.setStyleSheet("""
            QPushButton {
                border-radius: 112px;
                border: 13px solid #888;
                font-size: 35px;
                font-weight: bold;
                color: #fff;
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5, 
                                         stop:0 #666, stop:1 #333);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #aaa, stop:1 #444);
            }
        """)
        return button
    
    def hide_all_elements(self):
        """Hide all parking elements"""
        self.activate_container.hide()
        self.parking_off.hide()
        self.parking_search_svg.hide()
        self.parking_found_svg.hide()
        self.parking_not_found_svg.hide()
        self.start_container.hide()
        self.in_progress.hide()
        self.finished.hide()
        
        # Cancel button is shown by default but should be hidden in some states
        self.cancel_button.show()
    
    def update_auto_park(self, status_key):
        """Update the UI based on the current status"""
        if hasattr(self, 'delay_timer'):
            self.delay_timer.stop()
        
        self.current_status = status_key
        status_text = self.PARKING_MESSAGE[status_key]
        
        # Hide all elements first
        self.hide_all_elements()
        
        # Update status text
        self.status_label.setText(status_text)
        
        # Stop loading animation if it's running
        if self.timer.isActive():
            self.timer.stop()
            self.loading_state = 0
        
        # Show relevant elements based on status
        if status_key == "AVAILABLE":
            self.activate_container.show()
            self.cancel_button.hide()
            
        elif status_key == "NOT_AVAILABLE":
            self.parking_off.show()
            self.cancel_button.hide()
            
        elif status_key == "SEARCHING":
            self.parking_search_svg.show()
            # Start loading animation
            self.timer.start(500)  # Update every 500ms
            
        elif status_key == "DETECTED":
            self.parking_found_svg.show()
            # Delay before showing ready state
            self.delay_timer = QTimer(self)
            self.delay_timer.timeout.connect(lambda: self.update_auto_park("READY"))
            self.delay_timer.setSingleShot(True)
            self.delay_timer.start(2000)  # 2 second delay
            
        elif status_key == "NOT_DETECTED":
            self.parking_not_found_svg.show()
            # Delay before showing not available state
            self.delay_timer = QTimer(self)
            self.delay_timer.timeout.connect(lambda: self.update_auto_park("NOT_AVAILABLE"))
            self.delay_timer.setSingleShot(True)
            self.delay_timer.start(2000)  # 2 second delay
            
        elif status_key == "READY":
            self.start_container.show()
            
        elif status_key == "IN_PROGRESS":
            self.in_progress.show()
            # Start loading animation for "In Progress..."
            self.timer.start(500)
            
        elif status_key == "FINISHED":
            self.finished.show()
            self.cancel_button.hide()
    
    def update_loading_animation(self):
        """Update the loading animation for texts that need ellipsis animation"""
        dots = ["", ".", "..", "..."]
        
        if self.current_status == "SEARCHING":
            self.status_label.setText(f"{self.PARKING_MESSAGE['SEARCHING']}{dots[self.loading_state]}")
        elif self.current_status == "IN_PROGRESS":
            self.in_progress.setText(f"In Progress{dots[self.loading_state]}")
        
        self.loading_state = (self.loading_state + 1) % 4
    
    @pyqtSlot(str)
    def update_moving_status(self, message):
        """Update status based on vehicle movement"""
        try:
            data = eval(message)  # Convert JSON-like string to dict
            if not data.get('moving', True):
                self.update_auto_park("AVAILABLE")
            else:
                self.update_auto_park("NOT_AVAILABLE")
        except Exception as e:
            print(f"Error parsing moving status: {e}")
    
    def activate_auto_park(self):
        """Handler for Activate button click"""
        self.update_auto_park("SEARCHING")
        # Simulate a search process - in real app, this would connect to actual sensors
        QTimer.singleShot(3000, lambda: self.update_auto_park("DETECTED"))
    
    def start_auto_park(self):
        """Handler for Start button click"""
        self.update_auto_park("IN_PROGRESS")
        # Simulate parking process - in real app, this would connect to actual parking system
        QTimer.singleShot(5000, lambda: self.update_auto_park("FINISHED"))
    
    def finish_auto_park(self):
        """Handler for Finish button click"""
        self.update_auto_park("AVAILABLE")
    
    def cancel_auto_park(self):
        """Handler for Cancel button click"""
        self.update_auto_park("AVAILABLE")
