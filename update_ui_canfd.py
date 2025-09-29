#!/usr/bin/env python3
import sys
from PyQt6.QtWidgets import QApplication,  QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import QTimer, QObject, pyqtSignal, Qt
from PyQt6.QtGui import QPixmap, QFont, QColor
import cantools.database
from vehicle_ui import MainWindow
import threading
import can  
import cantools
from theme_tokens import _theme, ColorToken, dark_theme, creme_theme


active_warning = None
last_warning_time = 0

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
        
        # Store message and image path for theme updates
        self.message_text = message
        self.image_path = image_path
        
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
        self.setup_image()
        
        # Create message label with larger text
        self.message_label = QLabel(message)
        font = QFont()
        font.setPointSize(24)  # Increase font size
        font.setBold(True)
        self.message_label.setFont(font)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setWordWrap(True)
        
        # Add widgets to layout
        layout.addWidget(self.image_label)
        layout.addWidget(self.message_label)
        
        # Apply initial theme
        self.updateTheme()
        
    def setup_image(self):
        """Setup the warning image"""
        pixmap = QPixmap(self.image_path)
        if not pixmap.isNull():
            # Scale the image to a larger size while maintaining aspect ratio
            pixmap = pixmap.scaled(400, 400, Qt.AspectRatioMode.KeepAspectRatio, 
                                  Qt.TransformationMode.SmoothTransformation)
            self.image_label.setPixmap(pixmap)
            self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        else:
            self.image_label.setText("Warning Image Not Found")
            self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    
    def updateTheme(self):
        """Update colors when theme changes - THIS IS THE KEY FIX"""
        print("Updating warning overlay theme...")
        
        # Update text color
        warning_text = _theme.get_hex(ColorToken.TEXT_PRIMARY)
        self.message_label.setStyleSheet(f"color: {warning_text};")
        
        # Update background color
        warning_background = _theme.get_hex(ColorToken.BACKGROUND)
        self.setStyleSheet(f"background-color: {warning_background};")
        
        # Update image label style for "not found" text if needed
        if self.image_label.pixmap() is None:
            self.image_label.setStyleSheet(f"color: {warning_text}; font-size: 32px;")
        
        # FORCE the UI to update immediately
        self.message_label.update()
        self.image_label.update()
        self.update()
        self.repaint()
        
        print(f"Warning overlay updated - text color: {warning_text}, bg color: {warning_background}")
        
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
        global active_warning
        active_warning = None
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
        global active_warning
        active_warning = None
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
    
class CANFDReader(QObject):
    # Define signals to emit when new CAN data is received
    can0_signal = pyqtSignal(dict)
    can1_signal = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.can2_db = cantools.database.load_file('GM_GB_DWCAN2.dbc')
        self.evc_can_db = cantools.database.load_file('EVC_DataLogging_Rev3_EDITED_Rev2.dbc')

    def start_reading(self):
        # Start the CAN reading thread
        self.thread = threading.Thread(target=self.read_can_bus, daemon=True)
        self.thread.start()
        
    def read_can_bus(self):
        try:
            # Set up CAN FD bus interfaces
            # TODO: Connect CAN0 on the board to EVC on the vehicle.
            bus0 = can.interface.Bus(
                channel='can0', 
                bustype='socketcan',
                fd=False,          # Enable CAN FD
                bitrate=500000   # Arbitration phase bitrate (standard 500kbps)
            )
            
            # TODO: Connect CAN1 on the board to can2 on the vehicle.
            bus1 = can.interface.Bus(
                channel='can1', 
                bustype='socketcan',
                fd=True,
                bitrate=500000, # TODO: Make sure bitrate matches EVC CAN bus settings.
                dbitrate=200000
            )   
            
            while self.running:
                # Read from CAN0
                msg0 = bus0.recv(timeout=0.1)
                if msg0:
                    # Process the message and emit signal
                    data = self.process_can_message(msg0)
                    self.can0_signal.emit(data)
                
                # Read from CAN1
                msg1 = bus1.recv(timeout=0.1)
                if msg1:
                    # Process the message and emit signal
                    data = self.process_can_message(msg1)
                    self.can1_signal.emit(data)
                    
        except Exception as e:
            print(f"CAN reading error: {e}")
            
    def process_can_message(self, msg):
        # Extract the relevant data from CAN FD message
        # CAN FD messages can be up to 64 bytes (compared to 8 bytes in classic CAN)
        data = {}
        
        if msg.arbitration_id == 0x3B8:  # touch sensor information
            decoded_data = self.can2_db.decode_message(msg.arbitration_id, msg.data)
            data['hands_on_signal'] = decoded_data['StrgWhlTchSnsHndsOnStat']
        if msg.arbitration_id == 0x501:  # front engine info
            decoded_data = self.evc_can_db.decode_message(msg.arbitration_id, msg.data)
            data['front_engine_temp'] = decoded_data['F_MotTmp']
            data['powerflow'] = decoded_data['F_InvCurr_DC']
        if msg.arbitration_id == 0x502:  # rear engine info
            decoded_data = self.evc_can_db.decode_message(msg.arbitration_id, msg.data)
            data['rear_engine_temp'] = decoded_data['R_MotTmp']
        if msg.arbitration_id == 0x504:  # battery info
            decoded_data = self.evc_can_db.decode_message(msg.arbitration_id, msg.data)
            data['battery_temp'] = decoded_data['RESS_Temp']
            data['battery_SOC'] = decoded_data['RESS_SOC']
        if msg.arbitration_id == 0x750:
            decoded_data = self.evc_can_db.decode_message(msg.arbitration_id, msg.data)
            data['750_FEDU'] = decoded_data['FEDU_InsideDrtThrshld']
            data['750_REDU'] = decoded_data['REDU_InsideDrtThrshld']
        if msg.arbitration_id == 0x751:
            decoded_data = self.evc_can_db.decode_message(msg.arbitration_id, msg.data)
            data['751_FEDU'] = decoded_data['FEDU_MaxDrtTemp']
            data['751_REDU'] = decoded_data['REDU_MaxDrtTemp']
        if msg.arbitration_id == 0x752:
            decoded_data = self.evc_can_db.decode_message(msg.arbitration_id, msg.data)
            data['HVFault'] = decoded_data['IsltnFault_VICM']
        if msg.arbitration_id == 0x753:
            decoded_data = self.evc_can_db.decode_message(msg.arbitration_id, msg.data)
            data['LossComms_VICM'] = decoded_data['LossComms_VICM']
            data['LossComms_EBCM'] = decoded_data['LossComms_EBCM']
            data['LossComms_F_EDU'] = decoded_data['LossComms_F_EDU']
            data['LossComms_R_EDU'] = decoded_data['LossComms_R_EDU']
            
        return data
    
    def stop(self):
        self.running = False
        if hasattr(self, 'thread'):
            self.thread.join(timeout=1.0)

def main():
    global active_warning
    app = QApplication(sys.argv)

    # Create the main UI window
    window = MainWindow()
    window.show()
    
    # Create CAN FD reader
    can_reader = CANFDReader()
    
    # Connect signals from CAN reader to UI update methods
    can_reader.can0_signal.connect(lambda data: update_ui_from_can0(window, data))
    can_reader.can1_signal.connect(lambda data: update_ui_from_can1(window, data))
    
    # Start CAN reading in a separate thread
    can_reader.start_reading()
        
    # Make sure to clean up properly on exit
    app.aboutToQuit.connect(can_reader.stop)
    
    sys.exit(app.exec())

def update_ui_from_can1(window, data):
    if 'hands_on_signal' in data and hasattr(window, 'camera_view'):
        window.camera_view.update_hands_status(data['hands_on_signal'])

def update_ui_from_can0(window, data):
    # global active_warning, last_warning_time
    # Update UI elements based on data from CAN0
    global active_warning
    if active_warning is None:
        if '751_FEDU' in data:
            if data['751_FEDU'] != 0 and data['751_REDU'] == 0:
                active_warning = show_warning_overlay(
                    window,
                    "img/MIL.png",  # Replace with your warning image path
                    f"FAULT CODE EDU03 \n Front EDU is fully derated."
                )
            if data['751_FEDU'] == 0 and data['751_REDU'] != 0:
                active_warning = show_warning_overlay(
                    window,
                    "img/MIL.png",  # Replace with your warning image path
                    f"FAULT CODE EDU04 \n Rear EDU is fully derated."
                )
            if data['751_FEDU'] != 0 and data['751_REDU'] != 0:
                active_warning = show_warning_overlay(
                    window,
                    "img/MIL.png",  # Replace with your warning image path
                    f"FAULT CODE EDU03 and EDU04 \n Both EDUs are fully derated."
                )
        elif '750_FEDU' in data:
            if data['750_FEDU'] != 0 and data['750_REDU'] == 0:
                active_warning = show_warning_overlay(
                    window,
                    "img/MIL.png",  # Replace with your warning image path
                    f"FAULT CODE EDU01 \n Front EDU is inside the 10 deg C team-added derating temperature zone and driver command torque is not being met by the combined system for > 10s."
                )
            if data['750_FEDU'] == 0 and data['750_REDU'] != 0:
                active_warning = show_warning_overlay(
                    window,
                    "img/MIL.png",  # Replace with your warning image path
                    f"FAULT CODE EDU02 \n Rear EDU is inside the 10 deg C team-added derating temperature zone and driver command torque is not being met by the combined system for > 10s."
                )
            if data['750_FEDU'] != 0 and data['750_REDU'] != 0:
                active_warning = show_warning_overlay(
                    window,
                    "img/MIL.png",  # Replace with your warning image path
                    f"FAULT CODE EDU01 and EDU02 \n Both EDUs are inside the 10 deg C team-added derating temperature zone and driver command torque is not being met by the combined system for > 10s."
                )
        
        if 'HVFault' in data:
            if data['HVFault'] != 0:
                active_warning = show_warning_overlay(
                    window,
                    "img/MIL.png",  # Replace with your warning image path
                    f"FAULT CODE HV01 \n A ground fault has been detected."
                )
        if 'LossComms_VICM' in data:
            if data['LossComms_VICM'] != 0:
                active_warning = show_warning_overlay(
                    window,
                    "img/MIL.png",  # Replace with your warning image path
                    f"FAULT CODE COMM01 \n PSC has lost communication with VICM."
                )
            elif data['LossComms_EBCM'] != 0:
                active_warning = show_warning_overlay(
                    window,
                    "img/MIL.png",  # Replace with your warning image path
                    f"FAULT CODE COMM02 \n PSC has lost communication with EBCM."
                )
            elif data['LossComms_F_EDU'] != 0:
                active_warning = show_warning_overlay(
                    window,
                    "img/MIL.png",  # Replace with your warning image path
                    f"FAULT CODE COMM03 \n PSC has lost communication with the front EDU."
                )
            elif data['LossComms_R_EDU'] != 0:
                active_warning = show_warning_overlay(
                    window,
                    "img/MIL.png",  # Replace with your warning image path
                    f"FAULT CODE COMM04 \n PSC has lost communication with rear EDU."
                )
            
    if 'battery_SOC' in data and hasattr(window, 'dashboard_view'):
        window.dashboard_view.update_battery_percentage(data['battery_SOC'])
    
    if 'battery_temp' in data and hasattr(window, 'dashboard_view'):
        window.dashboard_view.update_battery_temperature(data['battery_temp'])
    
    if 'rear_engine_temp' in data and hasattr(window, 'dashboard_view'):
        window.dashboard_view.update_rear_motor_temperature(data['rear_engine_temp'])

    if 'front_engine_temp' in data and hasattr(window, 'dashboard_view'):
        window.dashboard_view.update_front_motor_temperature(data['front_engine_temp'])
    
    if 'powerflow' in data and hasattr(window, 'dashboard_view'):
        window.dashboard_view.update_powerflow(data['powerflow'])

if __name__ == "__main__":
    main()