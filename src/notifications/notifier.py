def send_notification(title, message, timeout=5):
    from plyer import notification
    notification.notify(
        title=title,
        message=message,
        timeout=timeout
    )