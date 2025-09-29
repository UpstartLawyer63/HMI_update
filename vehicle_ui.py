import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QStackedWidget, QLabel, 
                             QFrame, QSpacerItem, QSizePolicy)
from PyQt6.QtCore import Qt, QSize, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QIcon, QColor, QAction
from PyQt6.QtWidgets import QGesture, QSwipeGesture
import traceback
from theme_tokens import _theme, ColorToken, dark_theme, creme_theme

# Import your view classes
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

try:
    from vehicle_dashboard import VehicleDashboard
    print("Successfully imported VehicleDashboard from vehicle_dashboard.py")
except ImportError:
    print("Error importing VehicleDashboard - please check the file name and class name")
    VehicleDashboard = None

class NavButton(QPushButton):
    """Custom button class for sidebar navigation"""
    
    def __init__(self, icon_path_active, icon_path_inactive, parent=None):
        super(NavButton, self).__init__(parent)
        self.setFixedSize(80, 80)
        
        # Store icon paths
        self.icon_path_active = icon_path_active
        self.icon_path_inactive = icon_path_inactive
        
        # Set default inactive state
        self.setActive(False)
    
    def updateThemeColors(self):
        """Update colors when theme changes"""
        self.background_color = _theme.get_hex(ColorToken.BOX)
        self.border_color = _theme.get_hex(ColorToken.BORDER)
        # Refresh the current state
        current_active = hasattr(self, '_is_active') and self._is_active
        self.setActive(current_active)
    
    def setActive(self, active):
        """Set the button's active state with proper icon and style"""
        self._is_active = active  # Store state for theme updates
        
        if active:
            self.setIcon(QIcon(self.icon_path_active))
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {_theme.get_hex(ColorToken.ACCENT)};
                    border-radius: 0px 20px 20px 0px;
                    border: none;
                }}
            """)
        else:
            self.setIcon(QIcon(self.icon_path_inactive))
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {_theme.get_hex(ColorToken.BOX)};
                    border-radius: 0px 10px 10px 0px;
                    border: none; 
                }}
                QPushButton:hover {{
                    background-color: {_theme.get_hex(ColorToken.BORDER)};
                }}
            """)
        
        # Set icon size
        self.setIconSize(QSize(45, 45))

class ThemeToggleButton(QPushButton):
    """Theme toggle button for switching between dark and light themes"""
    
    def __init__(self, parent=None):
        super(ThemeToggleButton, self).__init__(parent)
        self.setFixedSize(80, 80)
        self.updateThemeIcon()
        self.updateStyle()
    
    def updateThemeIcon(self):
        """Update icon based on current theme"""
        # You can create theme icons or use text
        if _theme._theme == dark_theme:
            self.setText("☀️")  # Sun for switching to light
            self.setToolTip("Switch to Light Theme")
        else:
            self.setText("🌙")  # Moon for switching to dark
            self.setToolTip("Switch to Dark Theme")
        
        font = self.font()
        font.setPointSize(24)
        self.setFont(font)
    
    def updateStyle(self):
        """Update button style with current theme"""
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {_theme.get_hex(ColorToken.BOX)};
                border-radius: 10px;
                border: 2px solid {_theme.get_hex(ColorToken.BORDER)};
                color: {_theme.get_hex(ColorToken.TEXT_PRIMARY)};
            }}
            QPushButton:hover {{
                background-color: {_theme.get_hex(ColorToken.ACCENT)};
            }}
            QPushButton:pressed {{
                background-color: {_theme.get_hex(ColorToken.BORDER)};
            }}
        """)

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Vehicle Interface")
        self.setWindowFlags(Qt.WindowType.Window | 
                           Qt.WindowType.FramelessWindowHint | 
                           Qt.WindowType.WindowStaysOnTopHint |
                           Qt.WindowType.Tool)
        self.showMaximized()
        
        # Sidebar state tracking
        self.sidebar_expanded = False
        self.collapsed_width = 0
        self.expanded_width = 240
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create menu bar
        self.createMenuBar()
        
        # Create sidebar
        self.sidebar_frame = QFrame()
        self.sidebar_frame.setFixedWidth(self.collapsed_width)
        self.updateSidebarStyle()
        sidebar_layout = QVBoxLayout(self.sidebar_frame)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(20)
        
        # Create stacked widget for content
        self.content_stack = QStackedWidget()
        self.updateContentStackStyle()
        
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
        self.acc_btn.clicked.connect(lambda: self.change_view(1))
        sidebar_layout.addWidget(self.acc_btn)
        self.nav_buttons.append(self.acc_btn)
        
        # Camera button
        self.camera_btn = NavButton("img/icons/camera-white.svg", "img/icons/camera-black.svg")
        self.camera_btn.clicked.connect(lambda: self.change_view(2))
        sidebar_layout.addWidget(self.camera_btn)
        self.nav_buttons.append(self.camera_btn)
        
        # Parking button
        self.parking_btn = NavButton("img/icons/parking-white.svg", "img/icons/parking-black.svg")
        self.parking_btn.clicked.connect(lambda: self.change_view(3))
        sidebar_layout.addWidget(self.parking_btn)
        self.nav_buttons.append(self.parking_btn)
        
        # Add theme toggle button
        self.theme_btn = ThemeToggleButton()
        self.theme_btn.clicked.connect(self.toggleTheme)
        sidebar_layout.addWidget(self.theme_btn)
        
        # Add bottom spacer to push buttons to center
        bottom_spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        sidebar_layout.addItem(bottom_spacer)
        
        # Add sidebar and content stack to main layout
        main_layout.addWidget(self.sidebar_frame)
        main_layout.addWidget(self.content_stack)
        
        # Setup sidebar animation
        self.setupSidebarAnimation()
        
        # Enable gesture recognition
        self.grabGesture(Qt.GestureType.SwipeGesture)
        
        # Add views to the stacked widget
        if VehicleDashboard:
            self.dashboard_view = VehicleDashboard()
            self.content_stack.addWidget(self.dashboard_view)
        else:
            self.content_stack.addWidget(self.createPlaceholder("Dashboard View"))
            
        if ACCView:
            self.acc_view = ACCView()
            self.content_stack.addWidget(self.acc_view)
        else:
            self.content_stack.addWidget(self.createPlaceholder("ACC View"))
        
        if CameraView:
            self.camera_view = CameraView()
            self.content_stack.addWidget(self.camera_view)
            print("Added CameraView to content stack")
        else:
            self.content_stack.addWidget(self.createPlaceholder("Camera View"))
        
        if ParkView:
            self.park_view = ParkView()
            self.content_stack.addWidget(self.park_view)
        else:
            self.content_stack.addWidget(self.createPlaceholder("Parking View"))
        
        # Set initial active button and view
        self.change_view(0)
        
        # Apply HMI styled border
        self.updateMainWindowStyle()
    
    def toggleTheme(self):
        """Toggle between dark and creme themes"""
        print("Toggling theme...")
        
        # Switch theme
        if _theme._theme == dark_theme:
            _theme.set_theme(creme_theme)
            print("Switched to creme theme")
        else:
            _theme.set_theme(dark_theme)
            print("Switched to dark theme")
        
        # Update all UI elements
        self.updateAllStyles()
    
    def updateAllStyles(self):
        """Update all UI elements with new theme"""
        print("Updating all styles...")
        
        # Update main window
        self.updateMainWindowStyle()
        
        # Update sidebar
        self.updateSidebarStyle()
        
        # Update content stack
        self.updateContentStackStyle()
        
        # Update nav buttons
        for btn in self.nav_buttons:
            btn.updateThemeColors()
        
        # Update theme toggle button
        self.theme_btn.updateThemeIcon()
        self.theme_btn.updateStyle()
        
        # Update all views that have updateTheme method
        if hasattr(self, 'dashboard_view') and self.dashboard_view:
            if hasattr(self.dashboard_view, 'updateTheme'):
                self.dashboard_view.updateTheme()
            else:
                self.dashboard_view.update()
        
        if hasattr(self, 'acc_view') and self.acc_view:
            if hasattr(self.acc_view, 'updateTheme'):
                self.acc_view.updateTheme()
                print("Updated ACC view theme")
        
        if hasattr(self, 'camera_view') and self.camera_view:
            if hasattr(self.camera_view, 'updateTheme'):
                self.camera_view.updateTheme()
        
        if hasattr(self, 'park_view') and self.park_view:
            if hasattr(self.park_view, 'updateTheme'):
                self.park_view.updateTheme()
        
        # Update any placeholder views
        for i in range(self.content_stack.count()):
            widget = self.content_stack.widget(i)
            if hasattr(widget, 'findChild'):
                # Update placeholder labels
                label = widget.findChild(QLabel)
                if label:
                    label.setStyleSheet(f"font-size: 20px; color: {_theme.get_hex(ColorToken.TEXT_SECONDARY)};")
        
        # FORCE UI UPDATES - This is the key fix
        print("Forcing UI updates...")
        
        # Force repaint of main window and all children
        self.repaint()
        
        # Force update on all child widgets
        self.sidebar_frame.update()
        self.content_stack.update()
        
        # Force style refresh on central widget
        central_widget = self.centralWidget()
        if central_widget:
            central_widget.style().unpolish(central_widget)
            central_widget.style().polish(central_widget)
            central_widget.update()
        
        # Force update on the current view
        current_widget = self.content_stack.currentWidget()
        if current_widget:
            current_widget.update()
            # Also unpolish and repolish for complete style refresh
            current_widget.style().unpolish(current_widget)
            current_widget.style().polish(current_widget)
        
        # Update any warning overlays that might be active
        print("Searching for warning overlays to update...")
        for widget in QApplication.allWidgets():
            if hasattr(widget, 'updateTheme') and hasattr(widget, 'message_label'):
                # This is likely a WarningOverlay
                print("Found warning overlay, updating theme...")
                widget.updateTheme()
        
        # Process any pending events to ensure updates are applied
        QApplication.processEvents()
        
        print("Theme update complete!")
    
    def updateMainWindowStyle(self):
        """Update main window styling"""
        self.setStyleSheet(f"""
            MainWindow {{
                border-top: 20px solid {_theme.get_hex(ColorToken.BACKGROUND)};
                border-bottom: 20px solid {_theme.get_hex(ColorToken.BACKGROUND)};
                border-left: 30px solid {_theme.get_hex(ColorToken.BACKGROUND)};
                border-right: 30px solid {_theme.get_hex(ColorToken.BACKGROUND)};
                border-radius: 10px;
            }}
        """)
    
    def updateSidebarStyle(self):
        """Update sidebar styling"""
        self.sidebar_frame.setStyleSheet(f"background-color: {_theme.get_hex(ColorToken.BOX)};")
    
    def updateContentStackStyle(self):
        """Update content stack styling"""
        self.content_stack.setStyleSheet(f"background-color: {_theme.get_hex(ColorToken.BACKGROUND)};")
    
    def setupSidebarAnimation(self):
        """Setup the sidebar width animation"""
        self.sidebar_animation = QPropertyAnimation(self.sidebar_frame, b"maximumWidth")
        self.sidebar_animation.setDuration(300)  # 300ms animation
        self.sidebar_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Also animate minimum width to ensure smooth resize
        self.sidebar_min_animation = QPropertyAnimation(self.sidebar_frame, b"minimumWidth")
        self.sidebar_min_animation.setDuration(300)
        self.sidebar_min_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    def expandSidebar(self):
        """Expand the sidebar"""
        if not self.sidebar_expanded:
            print("Expanding sidebar")
            self.sidebar_expanded = True
            
            # Resize nav buttons for expanded state
            for btn in self.nav_buttons:
                btn.setFixedSize(self.expanded_width - 20, 80)  # Leave 20px margins
            
            # Resize theme button too
            self.theme_btn.setFixedSize(self.expanded_width - 20, 80)
            
            # Set animation end values
            self.sidebar_animation.setStartValue(self.collapsed_width)
            self.sidebar_animation.setEndValue(self.expanded_width)
            self.sidebar_min_animation.setStartValue(self.collapsed_width)
            self.sidebar_min_animation.setEndValue(self.expanded_width)
            
            # Start animations
            self.sidebar_animation.start()
            self.sidebar_min_animation.start()
    
    def collapseSidebar(self):
        """Collapse the sidebar"""
        if self.sidebar_expanded:
            print("Collapsing sidebar")
            self.sidebar_expanded = False
            
            # Resize nav buttons back to collapsed state
            for btn in self.nav_buttons:
                btn.setFixedSize(80, 80)  # Back to original size
            
            # Resize theme button back too
            self.theme_btn.setFixedSize(80, 80)
            
            # Set animation end values
            self.sidebar_animation.setStartValue(self.expanded_width)
            self.sidebar_animation.setEndValue(self.collapsed_width)
            self.sidebar_min_animation.setStartValue(self.expanded_width)
            self.sidebar_min_animation.setEndValue(self.collapsed_width)
            
            # Start animations
            self.sidebar_animation.start()
            self.sidebar_min_animation.start()
    
    def toggleSidebar(self):
        """Toggle sidebar open/closed"""
        if self.sidebar_expanded:
            self.collapseSidebar()
        else:
            self.expandSidebar()
    
    def event(self, event):
        """Handle events including gestures"""
        if event.type() == event.Type.Gesture:
            return self.gestureEvent(event)
        return super().event(event)
    
    def gestureEvent(self, event):
        """Handle gesture events"""
        swipe = event.gesture(Qt.GestureType.SwipeGesture)
        if swipe and swipe.state() == Qt.GestureState.GestureFinished:
            if swipe.horizontalDirection() == QSwipeGesture.SwipeDirection.Right:
                print("Swipe right detected - expanding sidebar")
                self.expandSidebar()
                return True
            elif swipe.horizontalDirection() == QSwipeGesture.SwipeDirection.Left:
                print("Swipe left detected - collapsing sidebar")
                self.collapseSidebar()
                return True
        
        return False
    
    def mousePressEvent(self, event):
        """Handle mouse/touch press events as backup to gestures"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if click is on sidebar edge for manual toggle
            if event.position().x() <= self.sidebar_frame.width() + 10:
                print("Click on sidebar area - toggling")
                self.toggleSidebar()
        super().mousePressEvent(event)
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        elif event.key() == Qt.Key.Key_Q:
            self.close()
        elif event.key() == Qt.Key.Key_S:  # 'S' key to toggle sidebar for testing
            self.toggleSidebar()
        elif event.key() == Qt.Key.Key_T:  # 'T' key to toggle theme
            self.toggleTheme()
    
    def createPlaceholder(self, name):
        """Create a placeholder widget for missing views"""
        placeholder = QWidget()
        layout = QVBoxLayout(placeholder)
        label = QLabel(f"{name} not available")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(f"font-size: 20px; color: {_theme.get_hex(ColorToken.TEXT_SECONDARY)};")
        layout.addWidget(label)
        return placeholder
    
    def change_view(self, index):
        """Change the active view and update button styles"""
        print(f"Changing view to index {index}")
        
        # Update nav buttons
        for i, btn in enumerate(self.nav_buttons):
            btn.setActive(i == index)
        
        # Change view
        self.content_stack.setCurrentIndex(index)
        
    def createMenuBar(self):
        """Create menu bar with view options"""
        menubar = self.menuBar()
        viewMenu = menubar.addMenu('View')
        
        # Full screen action
        fullScreenAction = QAction('Toggle Full Screen', self)
        fullScreenAction.setShortcut('F11')
        fullScreenAction.triggered.connect(self.toggleFullScreen)
        viewMenu.addAction(fullScreenAction)
        
        # Toggle sidebar action
        sidebarAction = QAction('Toggle Sidebar', self)
        sidebarAction.setShortcut('Ctrl+B')
        sidebarAction.triggered.connect(self.toggleSidebar)
        viewMenu.addAction(sidebarAction)
        
        # Toggle theme action
        themeAction = QAction('Toggle Theme', self)
        themeAction.setShortcut('Ctrl+T')
        themeAction.triggered.connect(self.toggleTheme)
        viewMenu.addAction(themeAction)
    
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
    
    sys.exit(app.exec())