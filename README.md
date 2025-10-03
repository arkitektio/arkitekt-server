# Arkitekt Server

A command-line tool for deploying and managing an Arkitekt server deployments. Arkitekt Server provides a comprehensive platform for scientific computing and data management, with built-in support for authentication, task orchestration, data storage, and containerized application deployment.

## Overview

Arkitekt Server is a deployment configuration management tool that simplifies the setup and management of the Arkitekt ecosystem. It generates Docker Compose configurations and handles the complex orchestration of multiple services including databases, message queues, object storage, and various scientific computing services.

## Quick Start: How to Start the Server

### Prerequisites
- Python 3.12+
- Docker and Docker Compose
- UVX (recommended) or pip

### 1. Initialize Your Deployment
```bash
# Default configuration (recommended for beginners)
uvx arkitekt-server init default

# Development configuration (with hot-reload support)
uvx arkitekt-server init dev

# Minimal configuration (lightweight setup)
uvx arkitekt-server init minimal
```

### 2. Configure Services (Optional)
```bash
# Enable specific services you need
uvx arkitekt-server service rekuest --enable
uvx arkitekt-server service mikro --enable
uvx arkitekt-server service kabinet --enable
```

### 3. Set Up Users
```bash
# Add users interactively
uvx arkitekt-server auth user add
```

### 4. Build and Start
```bash
# Generate Docker Compose files
uvx arkitekt-server build docker

# Start all services
uvx arkitekt-server start
```

### 5. Access Your Server
Wait for services to initialize, then access via the Arkitekt Orkestrator interface at the configured URL.

### Additional Commands
```bash
# Update services to latest versions
uvx arkitekt-server update

# View configured users (development only)
uvx arkitekt-server inspect users

# Create temporary instance for testing
uvx arkitekt-server ephemeral --port 8080
```

## Detailed Documentation

For comprehensive documentation, see the `docs/` folder:

- **[📚 Getting Started Guide](docs/starting.md)** - Step-by-step setup instructions
- **[⚙️ Configuration Guide](docs/configuration.md)** - Detailed configuration options
- **[🔧 Services Overview](docs/services.md)** - Complete service descriptions  
- **[🏗️ Architecture Guide](docs/architecture.md)** - Deployment patterns and architecture

## Oh my god, I forgot all of my passwords!

If you forget your preconfiugred user passwords, you can reset them by running:

```bash
uvx arkitekt-server inspect users
```

This command will list all users and their roles, that you have configured previously.
Of course you would never use this in production, but it is a useful command for development and testing purposes.


### Non-UVX Usage

If you prefer not to use UVX, you can run the tool directly with:

```bash
pip install arkitekt-server
arkitekt-server init default
```

## Key Features

- **One-Command Deployment**: Generate complete Docker Compose configurations with sensible defaults
- **Service Deployment**: Deploy and manage multiple interconnected services
- **Authentication & Authorization**: Built-in user management with JWT-based authentication
- **Development Mode**: Hot-reload support for development with GitHub repository mounting (when available)

## Core Services

The Arkitekt ecosystem includes several specialized services:

- **Lok**: Authentication and authorization service with JWT token management
- **Rekuest**: Task orchestration and workflow management
- **Mikro**: Image and microscopy data management
- **Kabinet**: Container and application registry
- **Fluss**: Workflow execution engine
- **Kraph**: Knowledge graph and metadata management
- **Elektro**: Event streaming and notifications
- **Alpaka**: AI/ML model management with Ollama integration

## Quick Start

### Initialize a new deployment

```bash
# Create a default configuration
arkitekt-server init default

# Create a development configuration with GitHub mounting
arkitekt-server init dev

# Create a minimal configuration
arkitekt-server init minimal
```

### Configure services

```bash
# Enable/disable specific services
arkitekt-server service rekuest --enable
arkitekt-server service mikro --enable
arkitekt-server service kabinet --enable
```

### Manage users

```bash
# Add a new user
arkitekt-server auth user add
```

Allows you to add a new user with options for username, email, and password.


### Deploy

When ready to deploy, run:

```bash
# Generate Docker Compose files and deploy
arkitekt-server build docker
```

This command generates the necessary Docker Compose files based on your configuration and starts the services.

### Start the services

```bash
docker compose up
```

This command starts all the services defined in the generated Docker Compose files, wait for the services to be up and running, and then you can access the 
deployment though the orkestrator interface.


## Configuration

The tool generates and manages a `arkitekt_server_config.yaml` file that contains all deployment settings. This file includes:

- Service configurations and Docker images
- Database and Redis settings
- Object storage (MinIO) configuration
- Authentication keys and secrets
- User and group management
- Network and routing configuration

This file can be customized to suit your deployment needs, allowing you to specify local or remote databases, shared or dedicated storage buckets, and development or production deployment modes. This config-file is the central point for managing your Arkitekt Server deployment. And it is automatically generated based on the services you enable and the options you choose during initialization.

## Architecture

Arkitekt Server uses a self-container-service architecture with:

- **PostgreSQL**: Primary database for all services
- **Redis**: Message queuing and caching
- **MinIO**: S3-compatible object storage
- **Caddy**: Reverse proxy and gateway
- **Docker**: Container orchestration

Each service can be configured independently with options for:
- Local or remote databases
- Shared or dedicated storage buckets
- Development or production deployment modes
- Custom authentication configurations

## Development

For development workflows, the tool supports:

- GitHub repository mounting for live code reloading
- Debug mode with detailed logging
- Separate development configurations
- Hot-swappable service configurations



## License

MIT License
