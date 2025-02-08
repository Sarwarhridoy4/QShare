# QShare - A PyQt6-Based Local File Sharing Application

## Overview

QShare is a Python-based file-sharing application built using **PyQt6** for the graphical user interface and **sockets** for network communication. It facilitates seamless peer-to-peer file transfers over a local network by utilizing TCP sockets and a UDP-based broadcasting mechanism for device discovery.

## Features

- **Peer-to-Peer File Transfer**: Send and receive files over the local network.
- **Device Discovery**: Automatically detects available devices using UDP broadcast.
- **Elegant UI**: Built using PyQt6 with a modern UI theme and enhanced usability.
- **Progress Tracking**: Displays file transfer progress in real-time.
- **Customizable Save Path**: Received files are stored in a designated directory.
- **Theme Support**: Choose from multiple themes (Dark, Light, Blue, High Contrast).
- **Automatic Device Detection**: Lists all available devices dynamically based on network broadcasts.
- **Retry Mechanism**: Handles transfer failures gracefully with retry options.
- **Custom Fonts**: Supports custom fonts for UI consistency.
- **Padded Input Fields**: Improved UI with properly spaced and styled input fields for better user experience.
- **Enhanced Device Details**: Displays additional device details such as MAC address, device name, and model.
- **Prevent UI Freezing**: Optimized UI to ensure smooth operation without unresponsiveness.

## How It Works

1. **Device Discovery**

   - A server broadcasts its presence over UDP.
   - Clients listen for active servers and list available devices.

2. **File Transfer**
   - The sender selects files and chooses a recipient from the list of available devices.
   - The recipient receives a confirmation prompt before accepting the file.
   - If accepted, the transfer begins, and progress is displayed.

## Installation

### Requirements

Ensure you have Python 3 installed along with the following dependencies:

```bash
pip install -r requirements.txt
```

The `requirements.txt` file includes:

- PyQt6

### Running the Application

1. **Start the File Sharing Client**:
   ```bash
   python QShare.py
   ```
2. **Select Files**: Click the `Select Files` button to choose files for transfer.
3. **Discover Devices**: Available devices will be listed automatically.
4. **Send Files**: Select a device and click `Send Files` to initiate a transfer.
5. **Receive Files**: A confirmation prompt will appear when an incoming file is detected.

### Creating an Executable with PyInstaller

To create an executable for QShare using PyInstaller, follow these steps:

1. **Install PyInstaller**: Ensure PyInstaller is installed in your Python environment.
   ```bash
   pip install pyinstaller
   ```

2. **Generate the Executable**: Use the provided `QShare.spec` file to create the executable.
   ```bash
   pyinstaller QShare.spec
   ```

3. **Locate the Executable**: After the build process completes, the executable will be located in the `dist` directory.

4. **Run the Executable**: Navigate to the `dist` directory and run the `QShare` executable to start the application.

## Network Details

- **TCP Server**: Listens for incoming file transfer requests.
- **UDP Broadcast**: Used to discover active servers on the local network.
- **Port Configuration**:
  - **Broadcast Port**: `5002`
  - **TCP File Transfer**: Dynamically assigned at runtime

## Testing Locally

To test the application on a single device:

- Run two instances of the application on the same computer.
- Ensure both instances are connected to the same local network.
- Use different network adapters (e.g., Wi-Fi and Ethernet) if required.

## Hosting the Application

### Local Network Usage

This application is designed for LAN usage. For hosting over the Internet, consider:

- Using a **cloud VPS** (e.g., AWS, DigitalOcean) with port forwarding.
- Implementing **WebSockets** or a **Flask/Django API** for better compatibility with online hosting platforms.
- Deploying the frontend separately via **Heroku, Replit, or Vercel**.

## Future Enhancements

- **Cross-Platform Support** (Windows, macOS, Linux)
- **Internet-Based Transfers** (Cloud support, WebRTC, or HTTP-based transfer)
- **Encryption** for secure file sharing

## License

This project is licensed under the MIT License. Feel free to modify and distribute it.

## Author

Developed by [Sarwar Hossain](https://github.com/Sarwarhridoy4).

## Contributions

Pull requests are welcome! If you'd like to contribute, please submit an issue or fork the repository.

For more details and the latest updates, visit the [QShare GitHub repository](https://github.com/Sarwarhridoy4/QShare).
