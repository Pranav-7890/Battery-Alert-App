from PyQt5 import QtWidgets, QtCore, QtGui
import sys
import psutil
from config.settings import low_battery, full_battery, set_battery_thresholds
from notifications.notifier import send_notification

class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # Get screen size and set window size to half, but increase vertical height by 60%
        screen = QtWidgets.QApplication.primaryScreen().geometry()
        half_width = int(screen.width() / 2)
        half_height = int(screen.height() / 2)
        increased_height = int(half_height * 1.6)  # Increase vertical height by 60%
        self.setMinimumSize(half_width, increased_height)
        self.resize(half_width, increased_height)
        self.setWindowTitle("Battery Monitor Settings")

        # Set dark background and white text
        self.setStyleSheet("""
            QWidget {
                background-color: #181818;
                color: #FFFFFF;
            }
            QLabel {
                color: #FFFFFF;
            }
            QSpinBox, QPushButton {
                background-color: #222222;
                color: #FFFFFF;
                border: 1px solid #444444;
                border-radius: 8px;
            }
            QPushButton:checked {
                background-color: #444444;
            }
        """)

        # Font for all widgets
        try:
            label_font = QtGui.QFont("Montserrat", 18)
            input_font = QtGui.QFont("Montserrat", 18)
            button_font = QtGui.QFont("Montserrat", 18)
            status_font = QtGui.QFont("Montserrat", 28, QtGui.QFont.Bold)
        except:
            label_font = QtGui.QFont("Segoe UI", 18)
            input_font = QtGui.QFont("Segoe UI", 18)
            button_font = QtGui.QFont("Segoe UI", 18)
            status_font = QtGui.QFont("Segoe UI", 28, QtGui.QFont.Bold)

        # Main vertical layout
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.setSpacing(32)  # Increased spacing for more gap
        self.layout.setContentsMargins(half_width // 8, increased_height // 8, half_width // 8, increased_height // 8)

        # Status label at the top, big, bold, colored, centered
        self.status_label = QtWidgets.QLabel("Status: Not monitoring")
        self.status_label.setFont(status_font)
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)
        self.status_label.setMinimumHeight(70)
        self.status_label.setStyleSheet("color: #00BFFF;")  # DeepSkyBlue
        self.layout.addWidget(self.status_label)

        # --- Battery health and estimated time remaining label ---
        self.battery_health_label = QtWidgets.QLabel("Health: N/A   |   Time left: N/A")
        health_font = QtGui.QFont("Montserrat", 20)
        self.battery_health_label.setFont(health_font)
        self.battery_health_label.setAlignment(QtCore.Qt.AlignCenter)
        self.battery_health_label.setStyleSheet("color: orange;")
        self.battery_health_label.setMinimumHeight(50)
        self.layout.addWidget(self.battery_health_label)
        # --- End battery health label ---

        # --- Add spacing after status label ---
        self.layout.addSpacing(24)

        # Grid layout for thresholds with extra vertical spacing
        threshold_layout = QtWidgets.QGridLayout()
        threshold_layout.setVerticalSpacing(24)
        threshold_layout.setHorizontalSpacing(30)

        # Low battery threshold
        self.low_battery_label = QtWidgets.QLabel("Low Battery Threshold (%):")
        self.low_battery_label.setFont(label_font)
        self.low_battery_input = QtWidgets.QSpinBox()
        self.low_battery_input.setRange(0, 99)
        self.low_battery_input.setValue(low_battery)
        self.low_battery_input.setFont(input_font)
        self.low_battery_input.setMinimumHeight(40)
        threshold_layout.addWidget(self.low_battery_label, 0, 0)
        threshold_layout.addWidget(self.low_battery_input, 0, 1)

        # Full battery threshold
        self.full_battery_label = QtWidgets.QLabel("Full Battery Threshold (%):")
        self.full_battery_label.setFont(label_font)
        self.full_battery_input = QtWidgets.QSpinBox()
        self.full_battery_input.setRange(1, 100)
        self.full_battery_input.setValue(full_battery)
        self.full_battery_input.setFont(input_font)
        self.full_battery_input.setMinimumHeight(40)
        threshold_layout.addWidget(self.full_battery_label, 1, 0)
        threshold_layout.addWidget(self.full_battery_input, 1, 1)

        self.layout.addLayout(threshold_layout)

        # --- Add spacing after thresholds ---
        self.layout.addSpacing(24)

        # Notification Cooldown Controls
        self.cooldown_label = QtWidgets.QLabel("Notification Cooldown:")
        self.cooldown_label.setFont(label_font)
        self.layout.addWidget(self.cooldown_label)

        cooldown_layout = QtWidgets.QHBoxLayout()
        cooldown_layout.setSpacing(16)
        self.cooldown_minutes = QtWidgets.QSpinBox()
        self.cooldown_minutes.setRange(0, 30)
        self.cooldown_minutes.setValue(0)
        self.cooldown_minutes.setSuffix(" min")
        self.cooldown_minutes.setFont(input_font)
        self.cooldown_minutes.setMinimumHeight(40)
        cooldown_layout.addWidget(self.cooldown_minutes)

        self.cooldown_seconds = QtWidgets.QSpinBox()
        self.cooldown_seconds.setRange(0, 59)
        self.cooldown_seconds.setValue(30)
        self.cooldown_seconds.setSuffix(" sec")
        self.cooldown_seconds.setFont(input_font)
        self.cooldown_seconds.setMinimumHeight(40)
        cooldown_layout.addWidget(self.cooldown_seconds)

        self.layout.addLayout(cooldown_layout)

        # --- Add spacing after cooldown controls ---
        self.layout.addSpacing(24)

        # Apply Settings button
        self.apply_button = QtWidgets.QPushButton("Apply Settings")
        self.apply_button.setFont(button_font)
        self.apply_button.setMinimumHeight(50)
        self.apply_button.clicked.connect(self.apply_settings)
        self.layout.addWidget(self.apply_button)

        # Start/Stop Monitoring button
        self.monitor_button = QtWidgets.QPushButton("Start Monitoring")
        self.monitor_button.setCheckable(True)
        self.monitor_button.setEnabled(False)
        self.monitor_button.setFont(button_font)
        self.monitor_button.setMinimumHeight(50)
        self.monitor_button.clicked.connect(self.toggle_monitoring)
        self.layout.addWidget(self.monitor_button)

        self.setLayout(self.layout)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.check_battery)
        self.monitoring_enabled = False

        self.low_battery_input.valueChanged.connect(self.sync_min_max)
        self.full_battery_input.valueChanged.connect(self.sync_max_min)

        self.last_low_notification = 0
        self.last_full_notification = 0

        self.notification_cooldown = self.get_cooldown_seconds()

        # Prevent resizing smaller than half screen
        self.setMinimumSize(half_width, increased_height)

    def get_cooldown_seconds(self):
        return self.cooldown_minutes.value() * 60 + self.cooldown_seconds.value()

    def sync_min_max(self, value):
        # Ensure min < max
        max_val = self.full_battery_input.value()
        if value >= max_val:
            self.full_battery_input.setValue(value + 1)
        self.full_battery_input.setMinimum(value + 1)

    def sync_max_min(self, value):
        # Ensure max > min
        min_val = self.low_battery_input.value()
        if value <= min_val:
            self.low_battery_input.setValue(value - 1)
        self.low_battery_input.setMaximum(value - 1)

    def apply_settings(self):
        new_low_battery = self.low_battery_input.value()
        new_full_battery = self.full_battery_input.value()
        if new_low_battery >= new_full_battery:
            QtWidgets.QMessageBox.warning(self, "Invalid Thresholds", "Minimum must be less than maximum.")
            return
        set_battery_thresholds(new_low_battery, new_full_battery)
        QtWidgets.QMessageBox.information(self, "Settings Applied", "Battery thresholds updated.")
        self.monitor_button.setEnabled(True)
        self.monitoring_enabled = True
        # Update cooldown value
        self.notification_cooldown = self.get_cooldown_seconds()

    def toggle_monitoring(self):
        if not self.monitoring_enabled:
            QtWidgets.QMessageBox.warning(self, "Apply Settings", "Please apply settings before monitoring.")
            self.monitor_button.setChecked(False)
            return
        if self.monitor_button.isChecked():
            self.monitor_button.setText("Stop Monitoring")
            self.status_label.setText("Status: Monitoring...")
            self.timer.start(5000)  # check every 5 seconds
            self.check_battery()
        else:
            self.monitor_button.setText("Start Monitoring")
            self.status_label.setText("Status: Not monitoring")
            self.timer.stop()

    def check_battery(self):
        import time
        battery = psutil.sensors_battery()
        if battery is None:
            self.status_label.setText("Status: Battery info not available")
            self.status_label.setStyleSheet("color: #FF6347;")  # Red
            self.battery_health_label.setText("Health: N/A   |   Time left: N/A")
            return

        percent = int(battery.percent)
        plugged = battery.power_plugged
        low = self.low_battery_input.value()
        full = self.full_battery_input.value()

        # Determine color based on battery status
        if plugged and percent < full:
            color = "#00FF00"  # Green when charging and below max threshold
        elif not plugged:
            color = "#00BFFF"  # Blue when discharging
        else:
            color = "#FF6347"  # Red for all other alert cases

        self.status_label.setText(
            f"Status: {percent}% {'(Charging)' if plugged else '(Discharging)'}"
        )
        self.status_label.setStyleSheet(f"color: {color};")

        # --- Battery health and estimated time remaining ---
        # Health: Show "Good" if battery.percent > 70, "Moderate" if > 40, else "Low"
        if percent > 70:
            health = "Good"
        elif percent > 40:
            health = "Moderate"
        else:
            health = "Low"
        # Estimated time remaining
        secsleft = battery.secsleft
        if secsleft == psutil.POWER_TIME_UNLIMITED:
            time_left = "Unlimited"
        elif secsleft == psutil.POWER_TIME_UNKNOWN or secsleft < 0:
            time_left = "Unknown"
        else:
            hours = secsleft // 3600
            minutes = (secsleft % 3600) // 60
            time_left = f"{hours}h {minutes}m"
        self.battery_health_label.setText(f"Health: {health}   |   Time left: {time_left}")
        # --- End battery health and estimated time remaining ---

        now = time.time()
        cooldown = self.notification_cooldown
        if percent <= low and not plugged:
            if now - self.last_low_notification > cooldown:
                send_notification("⚠️ Low BATTERY ALERT !!!", f"Battery is at {percent}%. Please plug the charger.")
                self.last_low_notification = now
        elif percent >= full and plugged:
            if now - self.last_full_notification > cooldown:
                send_notification("Battery is full", "Unplug for long battery health 😊")
                self.last_full_notification = now

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()