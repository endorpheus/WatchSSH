import sys
import argparse
import os
import subprocess
from PySide6.QtCore import QThread, Signal, Qt, QPoint
from PySide6.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, QMessageBox, QDialog, 
                               QVBoxLayout, QListWidget, QPushButton, QHBoxLayout, QLabel)
from PySide6.QtGui import QIcon, QAction, QMouseEvent

VERSION = "v1.4"

def parse_args():
    parser = argparse.ArgumentParser(description="WatchSSH - An SSH Login/Logout Monitor")
    parser.add_argument("-c", "--command-line-only", action="store_true", help="Run in command-line mode only")
    parser.add_argument("-v", "--version", action="version", version=f"WatchSSH {VERSION}", help="Show version information")
    parser.add_argument("-f", "--log-file", default="/var/log/auth.log", help="Specify the log file to monitor")
    return parser.parse_args()

class SSHActivityMonitor(QThread):
    activity_detected = Signal(str, str)  # Signal to emit username and action (login/logout)

    def __init__(self, log_file):
        super().__init__()
        self.log_file = log_file
        self.running = True

    def run(self):
        try:
            with open(self.log_file, "r") as f:
                f.seek(0, 2)  # Move to the end of the file
                while self.running:
                    line = f.readline().strip()
                    if line:
                        if "Accepted" in line and "ssh2" in line:
                            parts = line.split()
                            if len(parts) > 8:
                                username = parts[8]
                                self.activity_detected.emit(username, "login")
                        elif "session closed for user" in line:
                            parts = line.split()
                            if len(parts) > 5:
                                username = parts[-1]
                                self.activity_detected.emit(username, "logout")
                    else:
                        self.msleep(100)  # Sleep for 100ms if no new line
        except FileNotFoundError:
            print(f"Error: Log file '{self.log_file}' not found.")
        except PermissionError:
            print(f"Error: Permission denied to read '{self.log_file}'.")

    def stop(self):
        self.running = False

class FramelessDialog(QDialog):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        # self.setAttribute(Qt.WA_TranslucentBackground)
        
        # # Set opacity to 95%
        self.setWindowOpacity(0.95)

        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignCenter)
        self.layout.setContentsMargins(10, 0, 10, 5) # left, top, right, bottom?
        
        self.title_bar = QLabel(title)
        self.title_bar.setAlignment(Qt.AlignCenter)
        self.title_bar.setStyleSheet("""
            background-color: #2c3e50;
            color: white;
            padding: 10px;
            font-weight: bold;
        """)
        self.layout.addWidget(self.title_bar)

        self.setStyleSheet("""
            QDialog {
                background-color: #34495e;
                border-radius: 10px;
            }
            QLabel {
                color: white;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 5px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

class SSHConnectionDialog(FramelessDialog):
    def __init__(self, parent=None):
        super().__init__("SSH Connections", parent)
        
        self.connection_list = QListWidget()
        self.layout.addWidget(self.connection_list)

        button_layout = QHBoxLayout()
        self.refresh_button = QPushButton("Refresh")
        self.close_connection_button = QPushButton("Close Connection")
        self.close_dialog_button = QPushButton("Close")

        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.close_connection_button)
        button_layout.addWidget(self.close_dialog_button)

        self.layout.addLayout(button_layout)

        self.refresh_button.clicked.connect(self.refresh_connections)
        self.close_connection_button.clicked.connect(self.close_selected_connection)
        self.close_dialog_button.clicked.connect(self.hide)

        self.refresh_connections()

    def refresh_connections(self):
        self.connection_list.clear()
        connections = self.get_ssh_connections()
        for conn in connections:
            self.connection_list.addItem(f"{conn['user']} - PID: {conn['pid']} - {conn['ip']}")

    def get_ssh_connections(self):
        try:
            output = subprocess.check_output(["ps", "-ef"]).decode()
            connections = []
            for line in output.split('\n'):
                if 'sshd:' in line and '@' in line:
                    parts = line.split()
                    if len(parts) >= 8:
                        pid = parts[1]
                        user = parts[8].split('@')[0]
                        ip = parts[8].split('@')[1]
                        connections.append({'user': user, 'pid': pid, 'ip': ip})
            return connections
        except subprocess.CalledProcessError:
            print("Error: Unable to retrieve SSH connections.")
            return []

    def close_selected_connection(self):
        selected_items = self.connection_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select a connection to close.")
            return

        selected_item = selected_items[0]
        pid = selected_item.text().split("PID: ")[1].split(" -")[0]

        try:
            subprocess.run(["kill", pid], check=True)
            QMessageBox.information(self, "Success", f"Connection with PID {pid} has been terminated.")
            self.refresh_connections()
        except subprocess.CalledProcessError:
            QMessageBox.critical(self, "Error", f"Failed to terminate connection with PID {pid}.")

class AboutDialog(FramelessDialog):
    def __init__(self, parent=None):
        super().__init__("About WatchSSH", parent)
        
        content_layout = QVBoxLayout()
        content_layout.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(QLabel(f"WatchSSH {VERSION}", alignment=Qt.AlignCenter))
        content_layout.addWidget(QLabel("SSH Login/Logout Monitor", alignment=Qt.AlignCenter))
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.hide)
        
        content_layout.addWidget(close_button)
        self.layout.addLayout(content_layout)

class LoginNotifier(QApplication):
    def __init__(self, args):
        super().__init__(sys.argv)
        self.args = args

        if self.args.command_line_only:
            self.run_command_line_mode()
        else:
            self.setup_gui()

    def run_command_line_mode(self):
        print("Running in command-line mode. Press Ctrl+C to exit.")
        self.monitor = SSHActivityMonitor(self.args.log_file)
        self.monitor.activity_detected.connect(self.print_activity)
        self.monitor.start()

    def print_activity(self, username, action):
        print(f"SSH {action.capitalize()} Detected: {username}")

    def setup_gui(self):
        # Create system tray icon
        self.tray_icon = QSystemTrayIcon(self)
        icon_path = os.path.join(os.path.dirname(__file__), "icons", "icon.png")
        self.tray_icon.setIcon(QIcon(icon_path))
        self.tray_icon.setVisible(True)

        # Create context menu
        self.menu = QMenu()
        self.close_action = QAction("Manage Connections", self)
        self.about_action = QAction("About", self)
        self.quit_action = QAction("Quit", self)

        self.menu.addAction(self.close_action)
        self.menu.addAction(self.about_action)
        self.menu.addAction(self.quit_action)

        self.tray_icon.setContextMenu(self.menu)

        # Connect signals
        self.close_action.triggered.connect(self.close_connection)
        self.about_action.triggered.connect(self.show_about_dialog)
        self.quit_action.triggered.connect(self.quit)

        # Start monitoring
        self.monitor = SSHActivityMonitor(self.args.log_file)
        self.monitor.activity_detected.connect(self.show_notification)
        self.monitor.start()

    def show_notification(self, username, action):
        title = f"SSH {action.capitalize()} Detected"
        message = f"{username} just logged {action}"
        
        face_image_path = f"/home/{username}/.face"
        if os.path.exists(face_image_path):
            self.send_notification_with_image(title, message, face_image_path)
        else:
            self.send_notification(title, message)

    def send_notification_with_image(self, title, message, image_path):
        try:
            subprocess.run(["notify-send", "-i", image_path, title, message], check=True)
        except subprocess.CalledProcessError:
            print(f"Error: Failed to send notification with image.")
            self.send_notification(title, message)  # Fallback to notification without image

    def send_notification(self, title, message):
        try:
            subprocess.run(["notify-send", title, message], check=True)
        except subprocess.CalledProcessError:
            print(f"Error: Failed to send notification.")
            # Fallback to tray icon notification
            self.tray_icon.showMessage(title, message)

    def close_connection(self):
        dialog = SSHConnectionDialog()
        dialog.exec()

    def show_about_dialog(self):
        dialog = AboutDialog()
        dialog.exec()

    def quit(self):
        self.monitor.stop()
        self.monitor.wait()
        self.closeAllWindows()
        super().quit()  # Call the parent class's quit method

if __name__ == "__main__":
    args = parse_args()
    app = LoginNotifier(args)
    sys.exit(app.exec())