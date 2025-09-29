import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QStackedWidget, QLabel, 
                             QFrame, QSpacerItem, QSizePolicy)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QColor, QAction

# Import your view classes
try:
    from vehicle_dashboard import VehicleDashboard
    print("Successfully imported VehicleDashboard from vehicle_dashboard.py")
except ImportError as e:
    print(f"Error importing Dashboard View: {str(e)}")
    VehicleDashboard = None

try:
    from acc_view import ACCView
    print("Successfully imported ACCView from acc_view.py")
except ImportError:
    print("Error importing ACC View - please check the file name and class name")
    ACCView = None

try: 
    from camera_view import CameraView
    print("Successfully imported CameraView from camera_view.py")
except ImportError:
    print("Error importing Camera View - please check the file name and class name")
    CameraView = None

try: 
    from autopark_view import ParkView
    print("Successfully imported ParkView from autopark_view.py")
except ImportError:
    print("Error importing Autopark View - please check the file name and class name")
    ParkView = None

class NavButton(QPushButton):
    """Custom button class for sidebar navigation"""
    def __init__(self, icon_path_active, icon_path_inactive, parent=None):
        super(NavButton, self).__init__(parent)
        self.setFixedSize(60, 60)
        
        # Store icon paths
        self.icon_path_active = icon_path_active
        self.icon_path_inactive = icon_path_inactive
        
        # Set default inactive state
        self.setActive(False)
        
        # Style the button
        self.setStyleSheet("""
            QPushButton {
                border-radius: 0px 10px 10px 0px;
                border: none;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
    
    def setActive(self, active):
        """Set the button's active state with proper icon and style"""
        if active:
            self.setIcon(QIcon(self.icon_path_active))
            self.setStyleSheet("""
                QPushButton {
                    background-color: #313131;
                    border-radius: 0px 10px 10px 0px;
                    border: none;
                }
            """)
        else:
            self.setIcon(QIcon(self.icon_path_inactive))
            self.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    border-radius: 0px 10px 10px 0px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
            """)
        
        # Set icon size
        self.setIconSize(QSize(30, 30))


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Vehicle Interface")
        self.setGeometry(100, 100, 1000, 700)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create menu bar
        self.createMenuBar()
        
        # Create sidebar
        sidebar_frame = QFrame()
        sidebar_frame.setFixedWidth(80)
        sidebar_frame.setStyleSheet("background-color: white;")
        sidebar_layout = QVBoxLayout(sidebar_frame)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(20)
        
        # Create stacked widget for content
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet("background-color: white;")
        
        # Create navigation buttons with proper icons
        self.nav_buttons = []
        
        # Add top spacer to push buttons to center
        top_spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        sidebar_layout.addItem(top_spacer)
        
        # Home button
        self.home_btn = NavButton("img/icons/home-white.svg", "img/icons/home-black.svg")
        self.home_btn.clicked.connect(lambda: self.change_view(0))
        sidebar_layout.addWidget(self.home_btn)
        self.nav_buttons.append(self.home_btn)
        
        # ACC button
        self.acc_btn = NavButton("img/icons/acc-white.svg", "img/icons/acc-black.svg")
        # self.acc_btn.clicked.connect(lambda: self.change_view(1))
        sidebar_layout.addWidget(self.acc_btn)
        self.nav_buttons.append(self.acc_btn)
        
        # Camera button
        self.camera_btn = NavButton("img/icons/camera-white.svg", "img/icons/camera-black.svg")
        self.camera_btn.clicked.connect(lambda: self.change_view(2))
        sidebar_layout.addWidget(self.camera_btn)
        self.nav_buttons.append(self.camera_btn)
        
        # Parking button
        self.parking_btn = NavButton("img/icons/parking-white.svg", "img/icons/parking-black.svg")
        # self.parking_btn.clicked.connect(lambda: self.change_view(3))
        sidebar_layout.addWidget(self.parking_btn)
        self.nav_buttons.append(self.parking_btn)
        
        # Add bottom spacer to push buttons to center
        bottom_spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        sidebar_layout.addItem(bottom_spacer)
        
        # Add sidebar and content stack to main layout
        main_layout.addWidget(sidebar_frame)
        main_layout.addWidget(self.content_stack)
        
        # Add views to the stacked widget
        # 1. Dashboard view
        if VehicleDashboard:
            self.dashboard_view = VehicleDashboard()
            self.content_stack.addWidget(self.dashboard_view)
        else:
            # Placeholder if view is missing
            self.content_stack.addWidget(self.createPlaceholder("Dashboard View"))
            
        # 2. ACC view
        if ACCView:
            self.acc_view = ACCView()
            self.content_stack.addWidget(self.acc_view)
        else:
            self.content_stack.addWidget(self.createPlaceholder("ACC View"))
        
        # 3. Camera view
        if CameraView:
            self.camera_view = CameraView()
            self.content_stack.addWidget(self.camera_view)
            print("Added CameraView to content stack")
        else:
            self.content_stack.addWidget(self.createPlaceholder("Camera View"))
        
        # 4. Parking view
        if ParkView:
            self.park_view = ParkView()
            self.content_stack.addWidget(self.park_view)
        else:
            self.content_stack.addWidget(self.createPlaceholder("Parking View"))
        
        # Set initial active button and view
        self.change_view(0)
        
        # Apply HMI styled border
        self.setStyleSheet("""
            MainWindow {
                border-top: 20px solid rgb(37, 37, 37);
                border-bottom: 20px solid rgb(31, 30, 30);
                border-left: 30px solid black;
                border-right: 30px solid black;
                border-radius: 10px;
            }
        """)
    
    def createPlaceholder(self, name):
        """Create a placeholder widget for missing views"""
        placeholder = QWidget()
        layout = QVBoxLayout(placeholder)
        label = QLabel(f"{name} not available")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 20px; color: gray;")
        layout.addWidget(label)
        return placeholder
    
    def change_view(self, index):
        """Change the active view and update button styles"""
        print(f"Changing view to index {index}")
        
        # Update nav buttons
        for i, btn in enumerate(self.nav_buttons):
            btn.setActive(i == index)
        
        # # Handle special case for camera view - turn off camera when switching away
        # if hasattr(self, 'camera_view') and index != 2:  # 2 is camera index
        #     if hasattr(self.camera_view, 'camera_active') and self.camera_view.camera_active:
        #         print("Turning off camera when switching to another view")
        #         self.camera_view.toggleCamera(False)
        
        # Change view
        self.content_stack.setCurrentIndex(index)
    
    def keyPressEvent(self, event):
        """Handle key press events for full screen toggle"""
        if event.key() == Qt.Key_F11:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
        elif event.key() == Qt.Key_Escape and self.isFullScreen():
            self.showNormal()
        else:
            super().keyPressEvent(event)
    
    def createMenuBar(self):
        """Create menu bar with view options"""
        menubar = self.menuBar()
        viewMenu = menubar.addMenu('View')
        
        # Full screen action
        fullScreenAction = QAction('Toggle Full Screen', self)
        fullScreenAction.setShortcut('F11')
        fullScreenAction.triggered.connect(self.toggleFullScreen)
        viewMenu.addAction(fullScreenAction)
    
    def toggleFullScreen(self):
        """Toggle fullscreen mode"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())
