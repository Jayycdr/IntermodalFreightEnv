---
title: Intermodal Freight Environment
emoji: 🚚
colorFrom: blue
colorTo: indigo
sdk: docker
sdk_version: "1.0"
app_file: app/main.py
pinned: false
---

# Intermodal Freight Environment

An AI-powered multi-agent reinforcement learning environment for optimizing intermodal freight transportation.

**Project by:** Jay, Harsh and Aryan

## Overview

This project simulates a complex transportation network where multiple agents learn to optimize freight routing and mode selection across different transportation methods (road, rail, air, sea).

## Features

- 🤖 Multi-agent reinforcement learning environment
- 🚛 Multiple transportation modes (truck, train, plane, ship)
- 📊 Real-time analytics and visualization
- 🎯 Reward-based optimization
- 📈 Performance metrics and grading

## Quick Start

### Using Docker

```bash
docker-compose up
```

The application will be available at `http://localhost:7860`

### Local Development

```bash
python -m pip install -r requirements.txt
python app/main.py
```

## Project Structure

- `app/` - Main application and API
- `engine/` - Core environment logic
- `baseline/` - Baseline agent implementations
- `tests/` - Test suite
- `frontend/` - Dashboard and analytics

## Documentation

See the [docs/](docs/) folder for detailed documentation on:
- [API Infrastructure](docs/API_INFRASTRUCTURE.md)
- [Core Systems](docs/CORE_SYSTEMS.md)
- [Testing Guide](docs/TESTING_GUIDE.md)

## License

Project submission for Scaler School of Technology Hackathon