# Peer-To-Peer Chat Application

## Overview

This project is a simple Peer-To-Peer (P2P) chat application implemented using Python. It features a client-server architecture with data compression and decompression functionalities. The application uses the observer pattern to manage the state of the connection between the client and server, and supports basic message exchange over a network.

The compression is done using Predictor algorithm (it can be referred from [here](https://datatracker.ietf.org/doc/rfc1978/) and [here](https://dl.acm.org/doi/10.1145/42005.42031)).

The project is designed for a course named "Software Design and Analysis" and demonstrates principles of software design, including network communication, data compression, and design patterns.

Python 3.11 was used for the implementation.
## Features

- **Client-Server Communication**: Implements a basic chat system where a client can send messages to a server.
- **Data Compression**: Utilizes custom compression algorithms to minimize the size of transmitted data.
- **Observer Pattern**: Uses the observer pattern to manage connection state changes between the client and server.
- **Network Handling**: Includes error handling for network operations, ensuring robust communication.

## Components

### Observer and Observable

- **Observer**: An abstract base class for implementing observers in the observer pattern.
- **Observable**: An abstract base class for implementing observables in the observer pattern.

### Compression and Decompression

- **Compression**: Provides functionality to compress messages before sending them over the network.
- **Decompression**: Handles decompression of received messages.

### Network Components

- **Client**: Connects to a server and sends messages.
- **Server**: Listens for incoming connections and handles received messages.
- **Connection**: Manages the state of the network connection between client and server.
- **NetworkComponent**: An abstract base class for network components.

### Node

- **Node**: Manages the overall chat session by setting up the client and server and managing their connection.

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/chat-application.git
   cd chat-application
   ```

2. **Install dependencies:**
   Ensure you have Python 3.x installed. Install the required packages using pip:
   ```bash
   pip install bitarray
   ```

## Usage

1. **Prepare the Configuration File:**
   Create a JSON file, e.g `config.json` with the following structure:
   ```json
   {
       "address": "127.0.0.1",
       "port": 5000,
       "peer_address": "127.0.0.1",
       "peer_port": 5001
   }
   ```
   The ```address``` and ```peer_address``` keys are optional and can be ommited, when the application runs in localhost.

2. **Run the Node:**
   ```bash
   py main.py config.json
   ```

## Project Structure

- `observer.py`: Contains the abstract base classes `Observer` and `Observable`.
- `Compression.py`: Implements data compression functionality.
- `Decompression.py`: Implements data decompression functionality.
- `network_component.py`: Defines the `NetworkComponent` abstract base class.
- `connection.py`: Implements the `Connection` class to manage connection states.
- `client.py`: Implements the `Client` class for the client-side operations.
- `server.py`: Implements the `Server` class for the server-side operations.
- `node.py`: Orchestrates the client-server interaction.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
