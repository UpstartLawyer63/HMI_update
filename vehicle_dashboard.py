import sys
import json
import time
from datetime import datetime
import requests
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QGridLayout, 
                             QLabel, QFrame, QVBoxLayout, QHBoxLayout, QSizePolicy, QLabel, QGraphicsBlurEffect)
from PyQt6.QtGui import QFont, QPixmap, QColor, QPainter, QResizeEvent, QRadialGradient, QPen
from PyQt6.QtCore import Qt, QTimer, pyqtSlot, QObject, QThread, pyqtSignal, QRect

from theme_tokens import _theme, ColorToken, dark_theme, creme_theme


class ThermometerWidget(QFrame):
    def __init__(self, parent=None):
        super(ThermometerWidget, self).__init__(parent)
        self.temperature = 25  # Default temperature in Celsius
        self.min_temp = 0
        self.max_temp = 100
        self.setMinimumSize(50, 150)
        self.setMaximumSize(80, 300)
        self.setStyleSheet("background-color: transparent;")
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        
    def setTemperature(self, temperature):
        self.temperature = max(self.min_temp, min(self.max_temp, temperature))
        self.update()
  
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate sizes relative to widget dimensions
        width = self.width()
        height = self.height()
        
        # Thermometer tube dimensions
        tube_width = width * 0.3
        tube_x = (width - tube_width) / 2
        tube_height = height * 0.7
        tube_y = height * 0.15
        
        # Bulb dimensions
        bulb_radius = width * 0.4
        bulb_x = width / 2
        bulb_y = height - bulb_radius
        
        # Draw thermometer tube outline
        tube_rect = QRect(int(tube_x), int(tube_y), int(tube_width), int(tube_height))
        painter.setPen(QPen(_theme.get_qcolor(ColorToken.BORDER), 2))
        painter.setBrush(_theme.get_qcolor(ColorToken.BOX))
        painter.drawRoundedRect(tube_rect, tube_width//4, tube_width//4)
        
        # Draw bulb
        painter.setPen(QPen(_theme.get_qcolor(ColorToken.BORDER), 2))
        painter.setBrush(_theme.get_qcolor(ColorToken.BOX))
        painter.drawEllipse(int(bulb_x - bulb_radius/2), int(bulb_y - bulb_radius/2), 
                          int(bulb_radius), int(bulb_radius))
        
        # Calculate mercury/fluid level
        temp_ratio = (self.temperature - self.min_temp) / (self.max_temp - self.min_temp)
        fluid_height = tube_height * temp_ratio
        fluid_y = tube_y + tube_height - fluid_height
        
        # Choose color based on temperature
        if self.temperature <= 30:
            fluid_color = QColor('#4CAF50')  # Green - cool
        elif self.temperature <= 60:
            fluid_color = QColor('#ffbb33')  # Yellow - warm
        elif self.temperature <= 80:
            fluid_color = QColor('#ff9933')  # Orange - hot
        else:
            fluid_color = QColor('#ff4444')  # Red - very hot
        
        # Draw fluid in tube
        if fluid_height > 0:
            fluid_rect = QRect(int(tube_x + 2), int(fluid_y), int(tube_width - 4), int(fluid_height))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(fluid_color)
            painter.drawRoundedRect(fluid_rect, (tube_width-4)//4, (tube_width-4)//4)
        
        # Draw bulb fluid
        painter.setBrush(fluid_color)
        painter.drawEllipse(int(bulb_x - bulb_radius/2 + 2), int(bulb_y - bulb_radius/2 + 2), 
                          int(bulb_radius - 4), int(bulb_radius - 4))
        
        # Draw temperature marks and text
        painter.setPen(_theme.get_qcolor(ColorToken.TEXT_SECONDARY))
        font = QFont()
        font.setPointSize(max(6, min(10, width // 8)))
        painter.setFont(font)
        
        # Draw a few temperature marks
        for i, temp_mark in enumerate([0, 25, 50, 75, 100]):
            mark_ratio = (temp_mark - self.min_temp) / (self.max_temp - self.min_temp)
            mark_y = tube_y + tube_height - (tube_height * mark_ratio)
            mark_x = tube_x + tube_width + 2
            
            # Draw tick mark
            painter.drawLine(int(mark_x), int(mark_y), int(mark_x + 5), int(mark_y))
            
        # Draw current temperature text at bottom
        temp_text = f"{int(self.temperature)}°C"
        text_rect = QRect(0, int(height - 15), width, 15)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, temp_text)


class BatteryWidget(QFrame):
    def __init__(self, parent=None):
        super(BatteryWidget, self).__init__(parent)
        self.percentage = 0
        self.setMinimumSize(100, 40)
        self.setStyleSheet("background-color: transparent;")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
    def setPercentage(self, percentage):
        self.percentage = percentage
        self.update()
  
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate sizes relative to widget dimensions
        width = self.width()
        height = self.height()
        
        margin_h = int(width * 0.05)  # 5% horizontal margin

        # Draw battery container - dimensions adapt to widget size
        painter.setPen(_theme.get_qcolor(ColorToken.TEXT_PRIMARY))
        painter.setBrush(_theme.get_qcolor(ColorToken.BOX))
        rect = QRect(margin_h, 0, 
                     width - (2 * margin_h) - int(width * 0.05), 
                     height)
        painter.drawRoundedRect(rect, 5, 5)
        
        # Draw battery tip
        tip_width = int(width * 0.03)  # 3% of widget width
        tip_height = int(rect.height() * 0.6)  # 60% of battery height
        tip_y_offset = (rect.height() - tip_height) // 2
        
        tip_rect = QRect(rect.right(), rect.top() + tip_y_offset, 
                         tip_width, tip_height)
        painter.drawRoundedRect(tip_rect, 2, 2)
        
        # Draw battery fill
        padding = int(width * 0.01)  # 1% of widget width
        fill_width = int((rect.width() - (2 * padding)) * (self.percentage / 100))
        fill_rect = QRect(rect.left() + padding, rect.top() + padding, 
                          fill_width, rect.height() - (2 * padding))
        
        # Change color based on battery level, do not change these to color token.
        if self.percentage <= 20:
            painter.setBrush(QColor('#ff4444'))  # red 
        elif self.percentage <= 50:
            painter.setBrush(QColor('#ffbb33'))  # yellow
        else:
            painter.setBrush(QColor('#4CAF50'))  # green
            
        painter.drawRect(fill_rect)
        
        # Draw percentage text - font size scales with widget
        painter.setPen(_theme.get_qcolor(ColorToken.TEXT_SECONDARY))
        font = QFont()
        font_size = max(8, min(16, int(width / 15)))  # Scale font with widget width
        font.setPointSize(font_size)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{self.percentage}%")


class StatTile(QFrame):
    def __init__(self, title1="", title2="", value="", parent=None):
        super(StatTile, self).__init__(parent)
        self.setObjectName("stat")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(f"""
    #stat {{
        background-color: {_theme.get_hex(ColorToken.BOX)};
        border: 1px solid {_theme.get_hex(ColorToken.BORDER)};
    }}
    """)
        
        # Create layout
        self.tile_layout = QVBoxLayout(self)
        self.tile_layout.setContentsMargins(10, 10, 10, 10)
        
        # Title layout
        self.title_label = QLabel()
        if title2:
            self.title_label.setText(f"{title1}\n{title2}")
        else:
            self.title_label.setText(title1)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.title_label.setWordWrap(True)
        
        # Value
        self.value_label = QLabel(value)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # Add to layout
        self.tile_layout.addWidget(self.title_label)
        self.tile_layout.addWidget(self.value_label)
        
        # Size policies
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.value_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Initial font sizing
        self.updateFontSizes()
    
    def updateTheme(self):
        """Update theme colors for this tile"""
        # Update the stylesheet
        self.setStyleSheet(f"""
    #stat {{
        background-color: {_theme.get_hex(ColorToken.BOX)};
        border: 1px solid {_theme.get_hex(ColorToken.BORDER)};
    }}
    """)
        # Update font colors
        self.updateFontSizes()
        
    def updateValue(self, value):
        self.value_label.setText(value)
        self.updateFontSizes()
        
    def setValueColor(self, color):
        self.value_label.setStyleSheet(f"color: {_theme.get_hex(ColorToken.TEXT_PRIMARY)};")
        self.updateFontSizes()
        
    def setValueBackgroundColor(self, color_token):
        background_color = _theme.get_hex(color_token)
        text_color = _theme.get_hex(ColorToken.TEXT_PRIMARY)
    
        self.value_label.setStyleSheet(f"background-color: {background_color}; border-radius: 15px; padding: 5px 10px; color: {text_color};")
        self.updateFontSizes()
        
    def resizeEvent(self, event):
        super(StatTile, self).resizeEvent(event)
        self.updateFontSizes()
        
    def updateFontSizes(self):
        """Update font sizes based on the current tile size"""
        # Calculate appropriate font sizes based on tile dimensions
        title_size = max(8, min(16, self.width() / 20))
        value_size = max(14, min(18, self.width() / 10))
        
        # Update fonts and colors
        title_font = self.title_label.font()
        title_font.setPointSizeF(title_size)
        title_font.setWeight(QFont.Weight.Medium)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet(f"color: {_theme.get_hex(ColorToken.TEXT_SECONDARY)};")
        
        value_font = self.value_label.font()
        value_font.setPointSizeF(value_size)
        value_font.setWeight(QFont.Weight.Bold)
        self.value_label.setFont(value_font)
        # Only set color if no specific background color is set
        if not self.value_label.styleSheet() or 'background-color' not in self.value_label.styleSheet():
            self.value_label.setStyleSheet(f"color: {_theme.get_hex(ColorToken.TEXT_PRIMARY)};")


class TemperatureTile(StatTile):
    """StatTile with integrated thermometer widget"""
    def __init__(self, title1="", title2="", value="", parent=None):
        super(TemperatureTile, self).__init__(title1, title2, value, parent)
        
        # Create thermometer widget
        self.thermometer = ThermometerWidget()
        
        # Create horizontal layout for value and thermometer
        temp_container = QHBoxLayout()
        temp_container.addWidget(self.value_label)
        temp_container.addWidget(self.thermometer)
        
        # Remove value_label from original layout and add container
        self.tile_layout.removeWidget(self.value_label)
        
        # Create container widget
        temp_widget = QWidget()
        temp_widget.setLayout(temp_container)
        self.tile_layout.addWidget(temp_widget)
    
    def updateTemperature(self, temperature):
        """Update both text and thermometer"""
        self.updateValue(f"{temperature}°C")
        self.thermometer.setTemperature(temperature)


class AQITile(StatTile):
    def __init__(self, parent=None):
        super(AQITile, self).__init__("Air Quality", "Index", "", parent)    
     
    def updateAQI(self, aqi):
        self.updateValue(str(aqi))
        
        # Set color based on AQI and do not change to color token
        if 0 <= aqi <= 50:
            color = _theme.get_hex(ColorToken.ACCENT)  # good (green)
        elif 51 <= aqi <= 100:
            color = _theme.get_hex(ColorToken.TEXT_SECONDARY)  # moderate (yellow)
        elif 101 <= aqi <= 150:
            color = _theme.get_hex(ColorToken.ACCENT)  # unhealthy for sensitive groups (orange)
        elif 151 <= aqi <= 200:
            color = _theme.get_hex(ColorToken.TEXT_PRIMARY)  # unhealthy (red)
        elif 201 <= aqi <= 300:
            color = _theme.get_hex(ColorToken.ACCENT)  # very unhealthy (purple)
        else:
            color = _theme.get_hex(ColorToken.TEXT_PRIMARY)  # hazardous (magenta)
        
        self.setValueBackgroundColor(color)


class AQIWorker(QObject):
    finished = pyqtSignal(int)
    
    def getAQI(self):
        try:
            api_key = "32b5be779a42161718091ef0b02e792e8e7e782a"
            api_url = f"https://api.waqi.info/feed/Waterloo/?token={api_key}"
            response = requests.get(api_url)
            if response.status_code == 200:
                data = response.json()
                aqi = data["data"]["aqi"]
                self.finished.emit(aqi)
        except Exception as e:
            print(f"Error fetching AQI data: {e}")


class VehicleDashboard(QMainWindow):
    def __init__(self):
        super(VehicleDashboard, self).__init__()
        
        self.setWindowTitle("Vehicle Dashboard")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.showMaximized()
        
        # Handle window resize events
        self.resizeEvent = self.on_resize
        
        # Apply shadow effects after widgets are created
        self.shadow_effects = []
        
        # Main widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout for dashboard
        grid_layout = QGridLayout(central_widget)
        grid_layout.setSpacing(10)
        
        # Create battery display area
        self.battery_tile = StatTile("Vehicle", "Battery", "")
        battery_container = QVBoxLayout()
        self.battery_widget = BatteryWidget()
        battery_container.addWidget(self.battery_widget)
        
        # Create a container widget to hold the battery widget
        battery_container_widget = QWidget()
        battery_container_widget.setLayout(battery_container)
        
        # Add the container widget to the battery tile layout
        self.battery_tile.tile_layout.addWidget(battery_container_widget)
        
        # Create temperature tiles with thermometers
        self.batt_temp_tile = TemperatureTile("Battery", "Temperature", "-")
        self.front_motor_temp_tile = TemperatureTile("Front Motor", "Temperature", "-")
        self.rear_motor_temp_tile = TemperatureTile("Rear Motor", "Temperature", "-")
        
        # Regular tiles
        self.clock_tile = StatTile("Current", "Time", self.get_current_time())
        self.powerflow_tile = StatTile("Power Flow", "Direction", "-")
        
        # Create car display area
        self.car_display = QLabel()
        background_color = _theme.get_hex(ColorToken.BOX)

        self.car_display.setStyleSheet(f"""
        background-color: {background_color};
        border-radius: 10px;
        padding: 10px;
        """)
        self.car_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.car_display.setMinimumSize(400, 300)
        self.car_display.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Load car image
        self.car_pixmap = QPixmap("img/lyriq.png")
        if not self.car_pixmap.isNull():
            self.update_car_image()
        else:
            self.car_display.setText("Car Image")
        
        # Add tiles to grid with car on far left
        grid_layout.addWidget(self.car_display, 0, 0, 3, 1)  # Car spans 3 rows in column 0
        grid_layout.addWidget(self.battery_tile, 0, 1)
        grid_layout.addWidget(self.batt_temp_tile, 1, 1)
        grid_layout.addWidget(self.front_motor_temp_tile, 2, 1)
        grid_layout.addWidget(self.rear_motor_temp_tile, 0, 2)
        grid_layout.addWidget(self.powerflow_tile, 1, 2)
        grid_layout.addWidget(self.clock_tile, 2, 2)

        # Set column stretch factors with car on left
        grid_layout.setColumnStretch(0, 3)    # Car column (largest)
        grid_layout.setColumnStretch(1, 2)    # Middle column
        grid_layout.setColumnStretch(2, 2)    # Right column

        # Set up timers
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(60000)  # Update every minute
    
        self.glow_timer = QTimer(self)
        self.glow_timer.timeout.connect(self.update_wheel_glow)
        self.glow_timer.start(500)
        self.glow_on = True
        
        # Apply shadow effects programmatically instead of using CSS
        self.apply_shadows()
    
    def update_wheel_glow(self):
        self.glow_on = not self.glow_on
        self.update_car_image()

    @pyqtSlot(str)
    def update_battery(self, data):
        battery_data = json.loads(data)
        self.battery_widget.setPercentage(battery_data["percentage"])
        self.batt_temp_tile.updateTemperature(battery_data['temperature'])
    
    def update_battery_percentage(self, percentage):
        """Update only the dashboard's battery percentage display"""
        # Get the current temperature if available, otherwise use a placeholder
        current_temp = 25
        if hasattr(self, 'batt_temp_tile') and hasattr(self.batt_temp_tile, 'thermometer'):
            current_temp = self.batt_temp_tile.thermometer.temperature
        
        # Format data as JSON string
        battery_data = json.dumps({
            "percentage": percentage,
            "temperature": current_temp
        })
        
        # Call the existing update method
        self.update_battery(battery_data)

    def update_battery_temperature(self, temperature):
        """Update only the dashboard's battery temperature display"""
        # Get the current percentage if available, otherwise use a placeholder
        current_percentage = 0
        if hasattr(self, 'battery_widget'):
            current_percentage = self.battery_widget.percentage
        
        # Format data as JSON string
        battery_data = json.dumps({
            "percentage": current_percentage,
            "temperature": temperature
        })
        
        # Call the existing update method
        self.update_battery(battery_data)

    @pyqtSlot(str)
    def update_front_motor(self, data):
        motor_data = json.loads(data)
        self.front_motor_temp_tile.updateTemperature(motor_data['temperature'])

    @pyqtSlot(str)
    def update_rear_motor(self, data):
        motor_data = json.loads(data)
        self.rear_motor_temp_tile.updateTemperature(motor_data['temperature'])
            
    def update_front_motor_temperature(self, temperature):
        """Update the dashboard's motor temperature display"""
        motor_data = json.dumps({"temperature": temperature})
        self.update_front_motor(motor_data)
            
    def update_powerflow(self, powerflow_dir):
        if powerflow_dir == 0:
            self.powerflow_tile.updateValue("NO POWERFLOW")
        else:
            self.powerflow_tile.updateValue("Battery to Front EDU")
        
    def update_rear_motor_temperature(self, temperature):
        """Update the dashboard's motor temperature display"""
        motor_data = json.dumps({"temperature": temperature})
        self.update_rear_motor(motor_data)

    def apply_shadows(self):
        """Apply shadow effects to all tiles programmatically"""
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        
        # Find all StatTile instances (including TemperatureTile)
        for tile in self.findChildren(StatTile):
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(15)
            shadow.setColor(QColor(_theme.get_hex(ColorToken.TEXT_SECONDARY)))
            shadow.setOffset(3, 3)
            tile.setGraphicsEffect(shadow)
            self.shadow_effects.append(shadow)
            
        # Apply shadow to car display
        car_shadow = QGraphicsDropShadowEffect(self)
        car_shadow.setBlurRadius(15)
        car_shadow.setColor(QColor(_theme.get_hex(ColorToken.TEXT_SECONDARY)))
        car_shadow.setOffset(3, 3)
        self.car_display.setGraphicsEffect(car_shadow)
        self.shadow_effects.append(car_shadow)
    
    def get_current_time(self):
        now = datetime.now()
        period = "PM" if now.hour >= 12 else "AM"
        hours = now.hour % 12
        if hours == 0:
            hours = 12
        return f"{hours}:{now.minute:02d}{period}"
    
    def update_clock(self):
        self.clock_tile.updateValue(self.get_current_time())
        
    def update_car_image(self):
        """Scale the car image to fit the narrower container while maintaining proper ratio"""
        if hasattr(self, 'car_pixmap') and not self.car_pixmap.isNull():
            scaled_car = self.car_pixmap.scaled(1100, 750, 
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation)
            
            final_pixmap = QPixmap(scaled_car.size())
            final_pixmap.fill(Qt.GlobalColor.transparent)
            
            painter = QPainter(final_pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            if hasattr(self, 'glow_on') and self.glow_on:
                positions = [
                    (20,90,50,150),
                    (291,90,50,150)
                ]
                for x, y, rx, ry in positions:
                    gradient = QRadialGradient(x, y, 60)
                    gradient.setColorAt(1, QColor(_theme.get_hex(ColorToken.BACKGROUND)))
                    gradient.setColorAt(0.5, QColor(_theme.get_hex(ColorToken.BORDER)))
                    gradient.setColorAt(0, QColor(_theme.get_hex(ColorToken.TEXT_SECONDARY)))
                    
                    painter.setBrush(gradient)
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawEllipse(x, y, rx, ry)
                    
            painter.drawPixmap(0,0,scaled_car)
            painter.end()
            
            self.car_display.setPixmap(final_pixmap)
        else:
            self.car_display.setText("car image")
                
    def on_resize(self, event):
        """Handle window resize events"""
        # Update the car image when the window is resized
        self.update_car_image()
        
        # Force update of all tile font sizes
        for child in self.findChildren(StatTile):
            child.updateFontSizes()
        
        # Call the parent class's resize event handler
        super(VehicleDashboard, self).resizeEvent(event)
    
    def updateAllThemeColors(self):
        """Update all theme colors when theme changes"""
        # Update all StatTile instances
        for tile in self.findChildren(StatTile):
            tile.updateTheme()
        
        # Update car display background
        background_color = _theme.get_hex(ColorToken.BOX)
        self.car_display.setStyleSheet(f"""
        background-color: {background_color};
        border-radius: 10px;
        padding: 10px;
        """)
        
        # Re-apply shadows with new colors
        self.apply_shadows()
        
        # Update thermometers (they'll repaint automatically)
        if hasattr(self, 'batt_temp_tile'):
            self.batt_temp_tile.thermometer.update()
        if hasattr(self, 'front_motor_temp_tile'):
            self.front_motor_temp_tile.thermometer.update()
        if hasattr(self, 'rear_motor_temp_tile'):
            self.rear_motor_temp_tile.thermometer.update()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    background_color = _theme.get_hex(ColorToken.BACKGROUND)
    border_color = _theme.get_hex(ColorToken.BORDER)

    # Set application style
    app.setStyle("Fusion")
    
    # Apply custom styling without box-shadow
    app.setStyleSheet(f"""
        QMainWindow {{
            background-color: {background_color};
        }}
        QFrame#stat {{
            background-color: {background_color};
            border-radius: 10px;
            min-height: 120px;
            min-width: 160px;
            border: 1px solid {border_color};
        }}
    """)
    
    dashboard = VehicleDashboard()
    dashboard.show()
    
    sys.exit(app.exec())