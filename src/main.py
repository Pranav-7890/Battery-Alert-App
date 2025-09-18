import psutil
import time
from notifications.notifier import send_notification
from config.settings import low_battery, full_battery
import sys
from ui.main_window import main
from PyQt5.QtWidgets import QApplication

def check_battery():
    battery = psutil.sensors_battery()
    percent = battery.percent
    plugged = battery.power_plugged
    
    if not plugged and percent <= low_battery:
        send_notification("⚠️ Low BATTERY ALERT !!!", f"Battery is at {percent}%. Please plug the charger.")
    elif plugged and percent >= full_battery:
        send_notification("Battery is full", "Unplug for long battery health 😊")

if __name__ == "__main__":
    main()
    while True:
        check_battery()
        time.sleep(60)