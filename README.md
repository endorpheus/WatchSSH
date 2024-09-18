# WatchSSH

**v1.4**

**Monitor SSH Login and Logout Activity**

**WatchSSH** is a Python application designed to monitor SSH login and logout activity on your system. It provides a user-friendly interface and informative notifications, making it a valuable tool for system administrators and security professionals.

**Benefits**

* **Enhanced Security:** Gain real-time awareness of SSH activity on your system, helping you to detect unauthorized access attempts.
* **Improved Monitoring:** Streamline your monitoring workflow by centralizing SSH login and logout information.
* **User Convenience:** Receive clear notifications about SSH activity, including the username and action (login or logout).
* **Optional GUI:**  View and manage active SSH connections through a user-friendly graphical interface.
* **Customization:**  Specify the log file to monitor and choose how notifications are displayed.

**Requirements**

* Python 3.x
* PySide6 library (`pip install pyside6`)
* Optional: `notify-send` command-line tool (for desktop notifications)
* Permissions to read the SSH log file (typically `/var/log/auth.log`)

**Running WatchSSH**

1.  Install the required libraries:

     ```bash
     pip install pyside6
     ```

2.  Run WatchSSH from the command line:

     ```bash
     python watch_ssh.py
     ```

    This will run WatchSSH in command-line mode, printing notifications to the console.

3.  Run WatchSSH with a graphical user interface (optional):

     ```bash
     python watch_ssh.py
     ```

    This will display a system tray icon and provide desktop notifications.

**Command-Line Arguments**

* `-c`, `--command-line-only`: Run WatchSSH in command-line mode only (no GUI).
* `-v`, `--version`: Print version information.
* `-f`, `--log-file`: Specify the log file to monitor (defaults to `/var/log/auth.log`).

**Customizing Notifications**

WatchSSH can use the `notify-send` command-line tool to display desktop notifications with icons. If available on your system, WatchSSH will attempt to use any user profile picture (`.face` file) located in the user's home directory as the notification icon.  

**About**

Feel free to test this and get back to me with any feedback or suggestions.

**TODO**

- Make command line more user friendly
- what do you have in mind?
