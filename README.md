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
# Initialize in the current directory (interactive wizard)
uvx arkitekt-server init --wizard

# Initialize with a specific template (default, dev, minimal)
uvx arkitekt-server init --template default

# Initialize in a specific directory
uvx arkitekt-server init --template dev ./my-server
```



### 2. Set Up Users and Organizations
```bash
# Add a user
uvx arkitekt-server user add

# Add an organization
uvx arkitekt-server organization add
```

### 3. Build and Start
```bash
# Generate deployment files (auto-detects backend)
uvx arkitekt-server build

# Start the services (using docker compose directly for now)
docker compose up -d
```

### 4. Access Your Server
Wait for services to initialize, then access via the Arkitekt Orkestrator interface at the configured URL (usually http://localhost:8000).

## Temporary Server (Ephemeral Mode)

For quick testing, demos, or development without leaving any trace, you can use the ephemeral mode. This creates a temporary server instance in a temporary directory, starts it, and cleans everything up when you stop it.

```bash
# Start a temporary server on port 23489 (default)
uvx arkitekt-server ephemeral

# Start on a specific port
uvx arkitekt-server ephemeral --port 8080
```

This is perfect for trying out Arkitekt or running integration tests.

## Command Reference

### Core Commands

- **`init`**: Initializes a new Arkitekt server configuration.
  - `--wizard`: Runs an interactive wizard to guide you through setup.
  - `--template [default|dev|minimal]`: Uses a predefined template.
  - `[path]`: Specifies the directory to initialize (default: current directory).

- **`build`**: Generates the deployment files (e.g., `docker-compose.yaml`) based on your configuration.
  - `--dry-run`: Shows what would be generated without writing files.

- **`start`**: Starts the server services using the generated deployment files.
  - Equivalent to running `docker compose up -d`.

- **`update`**: Updates the server images and restarts services.
  - Pulls the latest Docker images and runs `up -d`.

- **`ephemeral`**: Starts a temporary, disposable server instance.
  - `--port`: Sets the HTTP port.
  - `--defaults`: Skips prompts and uses default settings.

### Management Commands

- **`service`**: Manage individual Arkitekt services (Rekuest, Mikro, etc.).
  - `[service_name] --enable/--disable`: Enable or disable a service.
  - `list`: List all available services and their status.

- **`user`**: Manage users for the Arkitekt deployment.
  - `add`: Create a new user (interactive).
  - `list`: List all configured users.
  - `delete`: Remove a user.

- **`organization`**: Manage organizations.
  - `add`: Create a new organization.
  - `list`: List all configured organizations.

- **`inspect`**: Inspect the current state and configuration.
  - `config`: Displays the current configuration and enabled services.

## Detailed Documentation

For comprehensive documentation, see the `docs/` folder:

- **[📚 Getting Started Guide](docs/starting.md)** - Step-by-step setup instructions
- **[⚙️ Configuration Guide](docs/configuration.md)** - Detailed configuration options
- **[🔧 Services Overview](docs/services.md)** - Complete service descriptions  
- **[🏗️ Architecture Guide](docs/architecture.md)** - Deployment patterns and architecture

## Oh my god, I forgot all of my passwords!

If you forget your preconfiugred user passwords, you can reset them by running:

```bash
uvx arkitekt-server user list
```

This command will list all users and their roles, that you have configured previously.
Of course you would never use this in production, but it is a useful command for development and testing purposes.


### Non-UVX Usage

If you prefer not to use UVX, you can run the tool directly with:

```bash
pip install arkitekt-server
arkitekt-server init --template default
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
- **Elektro**: Electrophysiology data handling
- **Alpaka**: AI/ML model management with Ollama integration

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

Arkitekt Server uses a self-contained service architecture with:

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


## License

MIT License
