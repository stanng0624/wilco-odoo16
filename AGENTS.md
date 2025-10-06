# Odoo 16.0 "Wilco ERP" Project Context

This document provides a comprehensive overview of the Wilco ERP project, a custom Enterprise Resource Planning system built on Odoo 16.0. It outlines the project structure, development workflows, and key conventions to follow.

## 1. Project Overview

Wilco ERP is designed for project-based businesses, providing integrated project management, advanced financial tracking, and custom reporting.

- **Core Technology**: Odoo 16.0 (Python, XML, PostgreSQL).
- **Main Custom Module**: `wilco_project` located in `custom_addons/`. This module contains the primary business logic for project management, financial tracking, and custom reports.
- **Third-Party Modules**: The project utilizes various third-party addons for functionalities like enhanced PDF reports, UI themes, and advanced accounting. These are located in `third_party_addons/`.
- **Core Odoo**: The base Odoo 16.0 framework is included as a submodule in the `odoo/` directory.

## 2. Development Environment

This project uses a Conda environment for managing Python dependencies.

- **Environment Name**: `wilco-odoo16`
- **Activation**: Before running any scripts or starting the server, you **MUST** activate the conda environment:
  ```bash
  conda activate wilco-odoo16
  ```

## 3. Building and Running the Project

There are two primary methods for running the application: Docker (recommended for a consistent environment) and manual local execution (for development on macOS).

### Method 1: Running with Docker (Recommended)

The Docker setup uses `docker-compose` to orchestrate the Odoo application, PostgreSQL database, and an Nginx proxy.

- **Configuration File**: `conf/docker/dock-compose.yml`
- **Command to Start**:
  ```bash
  # Note: The README mentions stack.yaml, but the file is dock-compose.yml
  docker-compose -f conf/docker/dock-compose.yml up -d
  ```
- **Web Access**: [http://localhost:8069](http://localhost:8069) (via Nginx proxy on port 10204)

### Method 2: Running Manually (macOS)

This method is suitable for direct development and debugging on a macOS environment.

1.  **Activate Conda Environment**:
    ```bash
    conda activate wilco-odoo16
    ```
2.  **Install Dependencies**: Ensure Python dependencies are installed from the custom addons directory.
    ```bash
    pip install -r custom_addons/requirements.txt
    ```
3.  **Run the Odoo Server**: Use the `odoo-bin` executable with the macOS-specific configuration file.
    ```bash
    ./odoo/odoo-bin -c conf/odoo16-macos.conf
    ```
- **Configuration**: The `conf/odoo16-macos.conf` file is pre-configured to use the `wilco-odoo-dev` database and sets the correct `addons_path`.

### Method 3: Odoo Shell for Development & Debugging

For backend development, testing model methods, or running scripts, the Odoo shell is the primary tool.

- **Key Command**:
  ```bash
  # First, activate the environment
  conda activate wilco-odoo16

  # Then, run the shell
  ./odoo/odoo-bin shell -c conf/odoo16-macos.conf -d wilco-odoo-dev --no-http
  ```
- **CRITICAL**: You **MUST** specify a database with `-d <database_name>` (e.g., `wilco-odoo-dev`). Otherwise, the `env` object required to interact with models will not be available, resulting in a `NameError`.

## 4. Development Conventions

### Git Commit Guidelines

The project enforces strict commit message guidelines. Adhering to this format is mandatory.

- **Structure**: `[TAG] module: Short description (<50 chars)`
- **Body**: The commit body must explain the **WHY** of the change, not just the "what". The "what" can be seen in the diff.
- **Tags**: Use one of the prescribed tags, such as:
  - `[FIX]`: For bug fixes.
  - `[REF]`: For refactoring.
  - `[ADD]`: For adding new modules.
  - `[IMP]`: For incremental improvements.
  - `[REM]`: For removing resources.
- **Example**:
  ```
  [IMP] project: add budget tracking to analytic accounts

  This change introduces a direct link between projects and their budgets
  to facilitate real-time profitability analysis. This was necessary
  because the previous method of manual calculation was error-prone.
  ```

### Project Structure

- `custom_addons/`: All bespoke code for this project resides here. The main module is `wilco_project`.
- `third_party_addons/`: Contains external Odoo modules. Avoid modifying files in this directory directly.
- `conf/`: Holds configuration files for different environments (macOS, Docker, Ubuntu).
- `odoo/`: The core Odoo 16 source code, managed as a Git submodule.
- `docs/`: Project-related documentation.
- `memory-bank/`: Internal development notes and context.

### Dependency Management

- **Odoo Dependencies**: Declared in the `depends` key within a module's `__manifest__.py` file.
- **Python Dependencies**: Managed in `custom_addons/requirements.txt`.