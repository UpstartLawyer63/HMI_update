import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QFrame, QPushButton, QSizePolicy)
from PyQt6.QtGui import QPixmap, QFont, QColor, QPainter, QPen, QBrush
from PyQt6.QtCore import Qt, QTimer, pyqtSlot, QSize, pyqtSignal, QPropertyAnimation


class ACCView(QWidget):
    """Adaptive Cruise Control View"""
    
    def __init__(self):
        super(ACCView, self).__init__()
        
        # Initialize state variables
        self.traffic_light_seen = True
        self.traffic_light_index = 1  # Start with Yellow (index 1)
        self.acc_enabled = True
        self.dyno_active = False
        
        self.initUI()
    
    def initUI(self):
        # Create the main layout
        main_layout = QVBoxLayout(self)
        
        # Top section for car and traffic light
        top_section = QHBoxLayout()
        top_section.setSpacing(15)  # Gap between items
        
        # Add the horizontal layout to the main layout
        main_layout.addLayout(top_section)
        
        # Store reference to top section layout
        self.main_layout = top_section
        
        # Create car status display
        self.create_car_status()
        
        # Create traffic light display
        self.create_traffic_light()
        
        # Create toggle switch container
        toggle_container = QWidget()
        toggle_layout = QHBoxLayout(toggle_container)
        
        # DYNO test label
        dyno_label = QLabel("DYNO Test")
        dyno_label.setFont(QFont("Arial", 14))
        
        # Create normal button instead of toggle switch
        self.dyno_button = QPushButton("Start Test")
        self.dyno_button.setMinimumSize(100, 40)  # Make button bigger and easier to click
        self.dyno_button.setFont(QFont("Arial", 12))
        self.dyno_button.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border-radius: 8px;
                border: 1px solid #d0d0d0;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #c0c0c0;
            }
        """)
        self.dyno_button.clicked.connect(self.toggle_dyno_test)
        
        # Add to layout with some spacing
        toggle_layout.addStretch()
        toggle_layout.addWidget(dyno_label)
        toggle_layout.addWidget(self.dyno_button)
        toggle_layout.addStretch()
        
        # Add the toggle container to main layout
        main_layout.addWidget(toggle_container)
        # Set some margins to the main layout
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Update initial states
        self.update_acc(True)
        self.update_traffic_light("Yellow")
    
    def toggle_dyno_test(self):
        """Toggle DYNO test state with normal button"""
        self.dyno_active = not self.dyno_active
        
        if self.dyno_active:
            self.dyno_button.setText("Stop Test")
            self.dyno_button.setStyleSheet("""
                QPushButton {
                    background-color: #ff6b6b;
                    color: white;
                    border-radius: 8px;
                    border: 1px solid #d63031;
                    padding: 6px;
                }
                QPushButton:hover {
                    background-color: #ff5252;
                }
                QPushButton:pressed {
                    background-color: #e03e3e;
                }
            """)
            print("DYNO test activated")
            # Add your DYNO test start code here
        else:
            self.dyno_button.setText("Start Test")
            self.dyno_button.setStyleSheet("""
                QPushButton {
                    background-color: #f0f0f0;
                    border-radius: 8px;
                    border: 1px solid #d0d0d0;
                    padding: 6px;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
                QPushButton:pressed {
                    background-color: #c0c0c0;
                }
            """)
            print("DYNO test deactivated")
            # Add your DYNO test stop code here
            
    def create_car_status(self):
        # Create car status widget
        self.car_stat = QFrame()
        self.car_stat.setObjectName("acc_car-stat")
        self.car_stat.setStyleSheet("""
            #acc_car-stat {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
            }
        """)
        # Size settings
        self.car_stat.setMinimumSize(270, 350)
        
        # Car status layout
        car_layout = QVBoxLayout(self.car_stat)
        car_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Total ACC distance display
        self.total_acc_dist = QLabel("Total ACC: 50m")
        self.total_acc_dist.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.total_acc_dist.setFont(QFont("Arial", 12, QFont.Weight.Bold))

        # Car SVG display
        self.car_svg = QLabel()
        self.car_svg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.car_svg.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Car distance display
        self.car_dist = QLabel("Distance: 50m")
        self.car_dist.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.car_dist.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        
        # Add widgets to layout
        car_layout.addWidget(self.total_acc_dist, 1)  # 20% of space
        car_layout.addWidget(self.car_svg, 3)  # 80% of space
        car_layout.addWidget(self.car_dist, 1)  # 20% of space
        
        # Add car status to main layout with a stretch factor
        self.main_layout.addWidget(self.car_stat, 3)
        
        # Make car SVG clickable
        # self.car_svg.mousePressEvent = self.toggle_acc
    
    def create_traffic_light(self):
        # Create traffic light widget
        self.traffic_stat = QFrame()
        self.traffic_stat.setObjectName("traffic-stat")
        self.traffic_stat.setStyleSheet("""
            #traffic-stat {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
            }
        """)
        # Size settings
        self.traffic_stat.setMinimumSize(180, 350)
        
        # Traffic light layout
        traffic_layout = QVBoxLayout(self.traffic_stat)
        traffic_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Traffic light SVG display
        self.traffic_svg = QLabel()
        self.traffic_svg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.traffic_svg.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        
        # Traffic light status text
        self.traffic_status = QLabel("Traffic: Yellow")
        self.traffic_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.traffic_status.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        
        # Add widgets to layout
        traffic_layout.addWidget(self.traffic_svg, 4)  # 80% of space
        traffic_layout.addWidget(self.traffic_status, 1)  # 20% of space
        
        # Add traffic light to main layout with stretch factors
        self.main_layout.addWidget(self.traffic_stat, 2)
        
        # Make traffic light SVG clickable
        self.traffic_svg.mousePressEvent = self.cycle_traffic_light
    
    def update_traffic_light(self, color):
        """Update the traffic light display with SVG files"""
        try:
            # Try to load SVG file based on color
            if self.traffic_light_seen:
                filename = f"/home/uwaft/Desktop/HMI/img/acc/Traffic_lights_dark_{color.lower()}.svg"
            else:
                filename = "/home/uwaft/Desktop/HMI/img/acc/Traffic_lights_dark_all-off.svg"
                
            # Handle both relative and absolute paths
            if not os.path.exists(filename):
                # Try looking in current directory
                basename = os.path.basename(filename)
                if os.path.exists(basename):
                    filename = basename
                else:
                    print(f"Traffic light SVG file not found: {filename}")
                    self.traffic_svg.setText(f"Traffic Light: {color}")
                    return
                    
            pixmap = QPixmap(filename)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(
                    self.traffic_svg.width(),
                    self.traffic_svg.height(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.traffic_svg.setPixmap(pixmap)
                self.traffic_status.setText(f"Traffic: {color}")
            else:
                self.traffic_svg.setText(f"Failed to load: {filename}")
        except Exception as e:
            print(f"Error loading traffic light image: {e}")
            self.traffic_svg.setText(f"Error: {str(e)}")
    
    def update_acc(self, enabled):
        """Update the ACC status display with SVG files"""
        try:
            # Try to load SVG file based on ACC state
            if enabled:
                filename = "/home/uwaft/Desktop/HMI/img/acc/acc_car.svg"
            else:
                filename = "/home/uwaft/Desktop/HMI/img/acc/disabled-acc-car.svg"
            
            # Handle both relative and absolute paths
            if not os.path.exists(filename):
                # Try looking in current directory
                basename = os.path.basename(filename)
                if os.path.exists(basename):
                    filename = basename
                else:
                    print(f"ACC car SVG file not found: {filename}")
                    self.car_svg.setText("ACC Car: " + ("Enabled" if enabled else "Disabled"))
                    return
            
            pixmap = QPixmap(filename)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(
                    self.car_svg.width(),
                    self.car_svg.height(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.car_svg.setPixmap(pixmap)
                
                # Show/hide distance display
                if enabled:
                    self.car_dist.show()
                else:
                    self.car_dist.hide()
            else:
                self.car_svg.setText(f"Failed to load: {filename}")
        except Exception as e:
            print(f"Error loading ACC car image: {e}")
            self.car_svg.setText(f"Error: {str(e)}")
    
    def set_acc_status(self, enabled):
        """Set ACC enabled/disabled state based on input"""
        self.acc_enabled = enabled
        self.update_acc(self.acc_enabled)

    def update_hw_distance(self, hw_distance):
        self.hw_distance = hw_distance
        self.car_dist.setText(f"Distance: {self.hw_distance}")
    
    def update_total_acc_distance(self, total_acc_distance):
        """Update the total ACC distance display"""
        self.total_acc_distance = total_acc_distance
        self.total_acc_dist.setText(f"Total ACC: {self.total_acc_distance}m")

    def toggle_acc(self, event):
        """Toggle ACC enabled/disabled state"""
        self.acc_enabled = not self.acc_enabled
        self.update_acc(self.acc_enabled)
    
    def cycle_traffic_light(self, event):
        """Cycle through traffic light colors"""
        colors = ["Green", "Yellow", "Red"]
        self.traffic_light_index = (self.traffic_light_index + 1) % 3
        self.update_traffic_light(colors[self.traffic_light_index])
    
    def run_dyno_test(self, state):
        """Toggle DYNO test state"""
        self.dyno_active = state
        
        if state:
            print("DYNO test activated")
            # Add your DYNO test start code here
        else:
            print("DYNO test deactivated")
            # Add your DYNO test stop code here
    
    def resizeEvent(self, event):
        """Handle resize events"""
        super().resizeEvent(event)
        
        # Update displays on resize
        colors = ["Green", "Yellow", "Red"]
        if hasattr(self, 'traffic_light_index'):
            self.update_traffic_light(colors[self.traffic_light_index])
            
        if hasattr(self, 'acc_enabled'):
            self.update_acc(self.acc_enabled)


# For testing the ACC view directly
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = QMainWindow()
    window.setWindowTitle("Adaptive Cruise Control")
    window.setGeometry(100, 100, 800, 600)
    
    acc_view = ACCView()
    window.setCentralWidget(acc_view)
    
    window.show()
    
    sys.exit(app.exec_())
