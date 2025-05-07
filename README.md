# Grok Proxy

A lightweight proxy tool designed to streamline interactions with Grok services, offering enhanced control over data flow and security.

---

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Environment Setup](#environment-setup)
- [Usage](#usage)
  - [Running with Python](#running-with-python)
  - [Using Docker](#using-docker)
  - [Using Docker Compose](#using-docker-compose)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

Grok Proxy acts as an intermediary for requests to Grok services. It provides a simple yet effective way to manage data flow and ensure security during interactions.

---

## Installation

Follow these steps to install Grok Proxy on your system:

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/zheng/grok_proxy.git
   cd grok_proxy
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## Environment Setup

To configure your environment variables, copy the provided `.env.example` file to `.env` by running the following command:

```bash
cp .env.example .env
```

After copying, open the `.env` file and update the values to match your environment settings.

---

## Usage

### Running with Python

To start the Grok Proxy application directly using Python:

```bash
python app.py
```

Ensure that all necessary environment variables are configured before launching the application.

### Using Docker

To run Grok Proxy in a Docker container:

1. **Build the Docker Image**:
   ```bash
   docker build -t grok-proxy .
   ```

2. **Run the Container**:
   ```bash
   docker run -p 8080:8080 --env-file .env grok-proxy
   ```

Make sure the `.env` file is in the directory from which you run the Docker command to provide the necessary environment variables.

### Using Docker Compose

To build the Docker image for Grok Proxy using Docker Compose:

1. **Build the Image**:
   ```bash
   docker-compose build
   ```

This command builds the Docker image for Grok Proxy as defined in the `docker-compose.yml` file. Note that this configuration is solely for building the image and does not start the service.

---

## Contributing

Contributions to Grok Proxy are welcome! If you have suggestions or improvements, please submit a Pull Request. For major changes, open an issue first to discuss your ideas.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
