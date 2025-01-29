# QShare - A PyQt6-Based Local File Sharing Application

## Overview
QShare is a Python-based file-sharing application built using **PyQt6** for GUI and **sockets** for network communication. It enables seamless peer-to-peer file transfer over a local network using TCP sockets and a UDP-based broadcasting mechanism for device discovery.

## Features
- **Peer-to-Peer File Transfer**: Send and receive files over the local network.
- **Device Discovery**: Automatically detects available devices using UDP broadcast.
- **Elegant UI**: Built using PyQt6 with a modern UI theme.
- **Progress Tracking**: Displays file transfer progress in real-time.
- **Customizable Save Path**: Received files are stored in a designated directory.

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
pip install PyQt6
```

### Running the Application
1. **Start the File Sharing Client**:
   ```bash
   python main.py
   ```
2. **Select Files**: Click the `Select Files` button to choose files for transfer.
3. **Discover Devices**: Available devices will be listed automatically.
4. **Send Files**: Select a device and click `Send Files` to initiate a transfer.
5. **Receive Files**: A confirmation prompt will appear when an incoming file is detected.

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
Developed by [Sarwar Hossain].

## Contributions
Pull requests are welcome! If you'd like to contribute, please submit an issue or fork the repository.

