import sys
import json
import time
from datetime import datetime
import requests
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QGridLayout, 
                             QLabel, QFrame, QVBoxLayout, QHBoxLayout, QSizePolicy)
from PyQt6.QtGui import QFont, QPixmap, QColor, QPainter, QResizeEvent
from PyQt6.QtCore import Qt, QTimer, pyqtSlot, QObject, QThread, pyqtSignal, QRect
from PyQt6.QtGui import QFont, QPixmap, QColor, QPainter
from PyQt6.QtCore import Qt, QTimer, pyqtSlot, QObject, QThread, pyqtSignal, QRect

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
        painter.setPen(Qt.GlobalColor.black)
        painter.setBrush(Qt.GlobalColor.white)
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
        
        # Change color based on battery level
        if self.percentage <= 20:
            painter.setBrush(QColor('#ff4444'))  # red
        elif self.percentage <= 50:
            painter.setBrush(QColor('#ffbb33'))  # yellow
        else:
            painter.setBrush(QColor('#4CAF50'))  # green
            
        painter.drawRect(fill_rect)
        
        # Draw percentage text - font size scales with widget
        painter.setPen(Qt.GlobalColor.black)
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
        self.setStyleSheet("""
            #stat {
                background-color: white;
                border-radius: 10px;
                padding: 10px;
                border: 1px solid #e0e0e0;
            }
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
        
    def updateValue(self, value):
        self.value_label.setText(value)
        self.updateFontSizes()
        
    def setValueColor(self, color):
        self.value_label.setStyleSheet(f"color: {color};")
        self.updateFontSizes()
        
    def setValueBackgroundColor(self, color):
        self.value_label.setStyleSheet(f"background-color: {color}; border-radius: 15px; padding: 5px 10px; color: white;")
        self.updateFontSizes()
        
    def resizeEvent(self, event):
        super(StatTile, self).resizeEvent(event)
        self.updateFontSizes()
        
    def updateFontSizes(self):
        """Update font sizes based on the current tile size"""
        # Calculate appropriate font sizes based on tile dimensions
        title_size = max(8, min(12, self.width() / 20))
        value_size = max(14, min(32, self.width() / 10))
        
        # Update fonts
        title_font = self.title_label.font()
        title_font.setPointSizeF(title_size)
        title_font.setWeight(QFont.Weight.Medium)
        self.title_label.setFont(title_font)
        
        value_font = self.value_label.font()
        value_font.setPointSizeF(value_size)
        value_font.setWeight(QFont.Weight.Bold)
        self.value_label.setFont(value_font)


class AQITile(StatTile):
    def __init__(self, parent=None):
        super(AQITile, self).__init__("Air Quality", "Index", "", parent)
        
    def updateAQI(self, aqi):
        self.updateValue(str(aqi))
        
        # Set color based on AQI
        if 0 <= aqi <= 50:
            color = "#009966"  # good (green)
        elif 51 <= aqi <= 100:
            color = "#FFDE33"  # moderate (yellow)
        elif 101 <= aqi <= 150:
            color = "#FF9933"  # unhealthy for sensitive groups (orange)
        elif 151 <= aqi <= 200:
            color = "#CC0033"  # unhealthy (red)
        elif 201 <= aqi <= 300:
            color = "#660099"  # very unhealthy (purple)
        else:
            color = "#7E0023"  # hazardous (magenta)
        
        self.setValueBackgroundColor(color)


# class WeatherWorker(QObject):
#     finished = pyqtSignal(int)
    
#     def getWeather(self):
#         try:
#             api_url = "https://api.weatherapi.com/v1/current.json?key=f45da337f5894b59877165507241206&q=Waterloo"
#             response = requests.get(api_url)
#             if response.status_code == 200:
#                 data = response.json()
#                 temp = round(data["current"]["temp_c"])
#                 self.finished.emit(temp)
#         except Exception as e:
#             print(f"Error fetching weather data: {e}")


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
        self.setGeometry(100, 100, 800, 600)
        
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
        
        self.batt_temp_tile = StatTile("Battery", "Temperature", "-")
        self.front_motor_temp_tile = StatTile("Front Motor", "Temperature", "-")
        self.clock_tile = StatTile("Current", "Time", self.get_current_time())
        self.aqi_tile = AQITile()
        self.rear_motor_temp_tile = StatTile("Rear Motor", "Temperature", "-")
        
        # Create car display area
        self.car_display = QLabel()
        self.car_display.setStyleSheet("""
            background-color: white;
            border-radius: 10px;
            padding: 10px;
        """)
        self.car_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.car_display.setMinimumSize(400, 300)
        self.car_display.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Load car image
        self.car_pixmap = QPixmap("/home/uwaft/Desktop/HMI/img/lyriq.png")  # You'll need to provide this image
        if not self.car_pixmap.isNull():
            self.update_car_image()
        else:
            self.car_display.setText("Car Image")
        
        # Add tiles to grid with more balanced layout
        grid_layout.addWidget(self.battery_tile, 0, 0)
        grid_layout.addWidget(self.batt_temp_tile, 1, 0)
        grid_layout.addWidget(self.front_motor_temp_tile, 2, 0)
        grid_layout.addWidget(self.car_display, 0, 1, 3, 1)  # Changed to span just 1 column
        grid_layout.addWidget(self.rear_motor_temp_tile, 0, 2)
        grid_layout.addWidget(self.aqi_tile, 1, 2)
        grid_layout.addWidget(self.clock_tile, 2, 2)
        
        # Set more balanced column stretch factors using integers
        grid_layout.setColumnStretch(0, 2)    # Left column
        grid_layout.setColumnStretch(1, 3)    # Car column (1.5x the side columns, but using integers)
        grid_layout.setColumnStretch(2, 2)    # Right column
        
        # Set up timers
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(60000)  # Update every minute
    
        # Start weather and AQI updates
        # self.setup_weather_worker()
        self.setup_aqi_worker()
        
        # Apply shadow effects programmatically instead of using CSS
        self.apply_shadows()
    
    # def setup_weather_worker(self):
    #     self.weather_thread = QThread()
    #     self.weather_worker = WeatherWorker()
    #     self.weather_worker.moveToThread(self.weather_thread)
        
    #     self.weather_thread.started.connect(self.weather_worker.getWeather)
    #     self.weather_worker.finished.connect(self.update_outside_temp)
        
    #     # Setup timer for regular updates
    #     self.weather_timer = QTimer(self)
    #     self.weather_timer.timeout.connect(self.start_weather_update)
    #     self.weather_timer.start(60000)  # every minute
        
    #     # Initial update
    #     self.start_weather_update()
    
    def setup_aqi_worker(self):
        self.aqi_thread = QThread()
        self.aqi_worker = AQIWorker()
        self.aqi_worker.moveToThread(self.aqi_thread)
        
        self.aqi_thread.started.connect(self.aqi_worker.getAQI)
        self.aqi_worker.finished.connect(self.update_aqi)
        
        # Setup timer for regular updates
        self.aqi_timer = QTimer(self)
        self.aqi_timer.timeout.connect(self.start_aqi_update)
        self.aqi_timer.start(60000)  # every minute
        
        # Initial update
        self.start_aqi_update()
    
    # def start_weather_update(self):
    #     self.weather_thread.start()
    
    def start_aqi_update(self):
        self.aqi_thread.start()
    
    @pyqtSlot(str)
    def update_battery(self, data):
        battery_data = json.loads(data)
        self.battery_widget.setPercentage(battery_data["percentage"])
        self.batt_temp_tile.updateValue(f"{battery_data['temperature']}°C")
    
    def update_battery_percentage(self, percentage):
        """
        Update only the dashboard's battery percentage display
        
        Args:
            percentage: Battery percentage (0-100)
        """
        # Get the current temperature if available, otherwise use a placeholder
        current_temp = 0
        if hasattr(self, 'batt_temp_tile'):
            current_text = self.batt_temp_tile.value_label.text()
            if current_text and "°C" in current_text:
                try:
                    current_temp = float(current_text.replace("°C", ""))
                except ValueError:
                    pass
        
        # Format data as JSON string
        battery_data = json.dumps({
            "percentage": percentage,
            "temperature": current_temp
        })
        
        # Call the existing update method
        self.update_battery(battery_data)

    def update_battery_temperature(self, temperature):
        """
        Update only the dashboard's battery temperature display
        
        Args:
            temperature: Battery temperature in Celsius
        """
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
        self.front_motor_temp_tile.updateValue(f"{motor_data['temperature']}°C")

    @pyqtSlot(str)
    def update_rear_motor(self, data):
        motor_data = json.loads(data)
        self.rear_motor_temp_tile.updateValue(f"{motor_data['temperature']}°C")
    
    def update_front_motor_temperature(self, temperature):
        """
        Update the dashboard's motor temperature display
        
        Args:
            temperature: Motor temperature in Celsius
        """
        # Format data as JSON string
        motor_data = json.dumps({
            "temperature": temperature
        })
        
        # Call the existing update method
        self.update_front_motor(motor_data)

    def update_rear_motor_temperature(self, temperature):
        """
        Update the dashboard's motor temperature display
        
        Args:
            temperature: motor temperature in Celsius
        """
        # Format data as JSON string
        motor_data = json.dumps({
            "temperature": temperature
        })
        
        # Call the existing update method
        self.update_rear_motor(motor_data)

    @pyqtSlot(int)
    def update_outside_temp(self, temp):
        self.outside_temp_tile.updateValue(f"{temp}°C")
        self.weather_thread.quit()
    
    @pyqtSlot(int)
    def update_aqi(self, aqi):
        self.aqi_tile.updateAQI(aqi)
        self.aqi_thread.quit()
        
    def apply_shadows(self):
        """Apply shadow effects to all tiles programmatically"""
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        
        # Find all StatTile instances
        for tile in self.findChildren(StatTile):
            shadow = QGraphicsDropShadowEffect(self)
            shadow.setBlurRadius(15)
            shadow.setColor(QColor(0, 0, 0, 50))  # Semi-transparent black
            shadow.setOffset(3, 3)
            tile.setGraphicsEffect(shadow)
            self.shadow_effects.append(shadow)  # Keep reference to prevent garbage collection
            
        # Apply shadow to car display
        car_shadow = QGraphicsDropShadowEffect(self)
        car_shadow.setBlurRadius(15)
        car_shadow.setColor(QColor(0, 0, 0, 50))
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
            # Calculate original aspect ratio of the car image
            original_ratio = self.car_pixmap.width() / self.car_pixmap.height()
            
            # Get the container dimensions with padding
            container_width = self.car_display.width() - 60  # More padding (30px on each side)
            container_height = self.car_display.height() - 60
            
            # Calculate a width that maintains the proper aspect ratio within the container
            target_height = container_height
            target_width = target_height * original_ratio
            
            # If the calculated width is too large, scale it down
            if target_width > container_width:
                target_width = container_width
                target_height = target_width / original_ratio
            
            # Scale the image with proper ratio
            scaled_pixmap = self.car_pixmap.scaled(
                int(target_width), 
                int(target_height),
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            
            self.car_display.setPixmap(scaled_pixmap)
    
    def on_resize(self, event):
        """Handle window resize events"""
        # Update the car image when the window is resized
        self.update_car_image()
        
        # Force update of all tile font sizes
        for child in self.findChildren(StatTile):
            child.updateFontSizes()
        
        # Call the parent class's resize event handler
        super(VehicleDashboard, self).resizeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    # Apply custom styling without box-shadow
    app.setStyleSheet("""
        QMainWindow {
            background-color: #f0f0f0;
        }
        QFrame#stat {
            background-color: white;
            border-radius: 10px;
            min-height: 120px;
            min-width: 160px;
            border: 1px solid #cccccc;
        }
    """)
    
    dashboard = VehicleDashboard()
    dashboard.show()
    
    sys.exit(app.exec_())
