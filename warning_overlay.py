from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication
from PyQt6.QtGui import QPixmap, QFont, QColor
from PyQt6.QtCore import Qt, QTimer, pyqtSignal



class WarningOverlay(QWidget):
    """
    A full-screen warning overlay with an image and warning message.
    This overlay will completely cover the entire screen when triggered.
    """
    closed = pyqtSignal()  # Signal emitted when overlay is closed
    
    def __init__(self, image_path, message, parent=None):
        """
        Initialize the warning overlay.
        
        Args:
            image_path (str): Path to the warning image to display
            message (str): Warning message to display below the image
            auto_close_ms (int, optional): If provided, auto-close after this many milliseconds
            parent (QWidget, optional): Parent widget
        """
        super().__init__(parent)
        # Set window flags to ensure it stays on top and covers everything
        self.setWindowFlags(Qt.WindowType.Window | 
                           Qt.WindowType.FramelessWindowHint | 
                           Qt.WindowType.WindowStaysOnTopHint |
                           Qt.WindowType.Tool)  # Tool window flag helps ensure it covers everything
        
        # Ensure the window is a full-screen window that captures all input
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_AlwaysStackOnTop, True)
        
        # Set up the layout
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(30)  # Increase spacing between image and text
        
        # Create image label
        self.image_label = QLabel()
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            # Scale the image to a larger size while maintaining aspect ratio
            pixmap = pixmap.scaled(400, 400, Qt.AspectRatioMode.KeepAspectRatio, 
                                  Qt.TransformationMode.SmoothTransformation)
            self.image_label.setPixmap(pixmap)
            self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        else:
            self.image_label.setText("Warning Image Not Found")
            self.image_label.setStyleSheet("color: black; font-size: 32px;")
            self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Create message label with larger text
        self.message_label = QLabel(message)
        font = QFont()
        font.setPointSize(24)  # Increase font size
        font.setBold(True)
        self.message_label.setFont(font)
        self.message_label.setStyleSheet("color: black;")
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setWordWrap(True)
        
        # Add widgets to layout
        layout.addWidget(self.image_label)
        layout.addWidget(self.message_label)
        
        # Set bright yellow background
        self.setStyleSheet("background-color: #FFDD00;")  # Bright yellow
        
    
    def showFullScreen(self):
        """Show the overlay in full screen mode, covering everything"""
        # Get screen geometry to cover entire screen
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)
        
        # Make sure we're on top of everything
        self.raise_()
        self.activateWindow()
        
        # Show in full screen mode
        super().showFullScreen()
    
    def mousePressEvent(self, event):
        """Close when clicked"""
        print("ok caught touch event")
        self.close()
        
    def keyPressEvent(self, event):
        """Close when Q or Escape key are pressed"""
        # event.ignore()
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        elif event.key() == Qt.Key.Key_Q:
            self.close()
    
    def closeEvent(self, event):
        """Normal closing"""
        event.accept()
        
def show_warning_overlay(main_window, image_path, message):
    """
    Show a warning overlay that completely covers the entire screen.
    
    Args:
        main_window: The main application window
        image_path (str): Path to the warning image
        message (str): Warning message to display
        auto_close_ms (int, optional): Auto-close time in milliseconds
        
    Returns:
        WarningOverlay: The created overlay widget
    """
    # Create the overlay as a top-level window
    overlay = WarningOverlay(image_path, message)  
    
    # Show it in full screen mode, covering everything
    overlay.showFullScreen()
    
    return overlay
