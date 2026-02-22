# **IoT Smart Pool Locker System**

A distributed IoT system designed to automate locker management in facilities like swimming pools. The system utilizes RFID technology, MQTT communication, and a centralized management dashboard to streamline user entry, locker assignment, and security monitoring.

---

## 🌟 **Key Features**

### 🔐 **Automated Locker Management**
* **RFID Identification:** Fast and secure user identification using MFRC522 modules.
* **Dynamic Assignment:** Automatically assigns the first available locker to a new user upon card scan.
* **Session Management:** Dedicated "Gate Terminal" to handle pool entry/exit and automatically release lockers when a user leaves the facility.

### 📡 **IoT Communication & Architecture**
* **MQTT Protocol:** Asynchronous, low-latency communication between Raspberry Pi edge devices and the central server.
* **Distributed Architecture:** Decentralized logic with an MQTT broker residing on a gateway node for high reliability.

### 🖥️ **Administrator Dashboard**
* **Real-time Monitoring:** Live view of locker occupancy status (Occupied vs. Free).
* **Remote Control:** Capability to remotely open or release any locker in case of emergencies or user errors.
* **Usage History:** Detailed logs of entries, exits, and locker transitions with timestamps.
* **Live Updates:** Powered by WebSockets (Socket.IO) for instant UI refreshes without manual reloading.

---

## 🧱 **System Architecture**


The system consists of three main layers:
1.  **Edge Layer:** Raspberry Pi devices acting as Locker and Gate Terminals, interacting with RFID readers and OLED displays.
2.  **Communication Layer:** An MQTT Broker (Mosquitto) managing message distribution.
3.  **Application Layer:** A Flask-based backend handling business logic and an SQLite database, connected to a web-based Admin Panel.


---

## 📌 **Technology Stack**
* **Backend:** Python 3, Flask, SQLite
* **Communication:** MQTT (paho-mqtt, flask-mqtt), WebSockets (Socket.IO), HTTP/REST
* **Frontend:** HTML5, CSS3 (Flexbox/Grid), Jinja2, Google Material Icons
* **Hardware:** Raspberry Pi, RFID MFRC522, OLED SSD1331
