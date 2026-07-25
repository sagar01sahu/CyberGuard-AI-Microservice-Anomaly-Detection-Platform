# Synthetic Cybersecurity Log Generator

## Overview

The **Synthetic Cybersecurity Log Generator** is a Python-based simulation framework that continuously generates realistic cybersecurity access logs and streams them to a REST API.

The primary goal of this project is to create realistic enterprise authentication and access logs that can later be used for:

* SIEM testing
* Threat detection research
* Machine Learning anomaly detection
* UEBA (User Entity Behavior Analytics)
* Spring Boot backend development
* Dashboard visualization
* Security analytics

---

# Project Objective

Generate realistic enterprise user activities including:

* Normal user login behavior
* Session management
* Resource access
* User logout
* Cyber attack simulation

and continuously send those logs to

```
POST http://localhost:8080/api/v1/logs/ingest
```

using HTTP POST requests.

---

# Technology Stack

### Language

Python 3.10+

### Libraries

* Faker
* Requests
* NumPy
* Pandas
* Dataclasses
* Logging
* Random
* Time
* JSON
* Datetime

---

# Current Project Structure

```
synthetic-log-generator/

│
├── config.py
├── constants.py
├── models.py
├── utils.py
├── profile_generator.py
├── session_manager.py
├── state_machine.py
├── anomaly_injector.py
├── dispatcher.py
├── simulation.py
├── synthetic_log_generator.py
├── fake_server.py
├── verify_project.py
├── requirements.txt
├── README.md
└── __init__.py
```

---

# Module Description

---

## config.py

Contains every configurable value used across the project.

Examples

* API URL
* Retry count
* Timeout
* User pool size
* Tick interval
* Time acceleration
* Anomaly probability

No business logic should be placed here.

---

## constants.py

Stores static constants used by multiple modules.

Examples

* Roles
* Operating systems
* Browsers
* Countries
* Resource lists
* Authentication methods

---

## models.py

Contains the application's data models.

Currently

### UserProfile

Represents a synthetic employee.

Fields include

* entity_id
* role
* primary_ip
* home_geo
* device_id
* operating system
* browser
* work schedule
* allowed resources

This class acts as the single source of truth for user identity.

---

## profile_generator.py

Responsible for generating synthetic users.

Uses

* Faker
* NumPy distributions
* Randomized work schedules

Generates

```
500 UserProfile objects
```

Each user has

* Home location
* Office hours
* Primary device
* Browser
* IP
* Allowed resources

---

## session_manager.py

Maintains user sessions.

Responsibilities

* Login
* Logout
* Active session tracking

Acts as the in-memory session database.

---

## state_machine.py

Simulates realistic employee behavior.

Possible states include

```
OFFLINE

↓

AUTHENTICATING

↓

ACTIVE_SESSION

↓

IDLE

↓

LOGGED_OUT
```

The state machine decides

* when users login
* when users logout
* which resource they access
* idle periods

---

## anomaly_injector.py

Injects malicious activities into normal traffic.

Current supported attacks

1. Brute Force

Generates

15–30 failed password attempts
within a few seconds.

---

2. Impossible Travel

Two successful logins

Example

India

↓

Germany

within 2–5 minutes.

---

3. Lateral Movement

Attempts to access resources outside the user's department.

Example

Marketing user

↓

Finance Payroll

---

4. Device Spoofing

Changes

* Device ID
* Browser
* Operating System

during an active session.

---

5. Credential Stuffing

Multiple users

↓

One attacker IP

↓

Failed login attempts.

---

6. Low and Slow Exfiltration

Accesses sensitive resources

during

03:15 AM

using small repeated requests.

---

## dispatcher.py

Responsible for sending logs.

Uses

```
requests.post()
```

Features

* Retry mechanism
* Exponential Backoff
* Timeout
* Error handling
* Logging

The dispatcher should never terminate the simulation.

---

## simulation.py

The main orchestration engine.

Responsible for

* creating users
* advancing simulated time
* executing the state machine
* generating logs
* injecting anomalies
* dispatching logs

Everything passes through this module.

---

## synthetic_log_generator.py

Application entry point.

Responsibilities

* configure logging
* initialize modules
* start simulation
* graceful shutdown

Executed using

```
python synthetic_log_generator.py
```

---

## fake_server.py

A lightweight HTTP server used before the Spring Boot backend is available.

Implements

```
POST /api/v1/logs/ingest
```

Useful for

* local testing
* debugging
* payload verification

---

## verify_project.py

Runs a complete verification of the current project.

Checks

* profile generation
* state machine
* anomaly injector
* dispatcher
* integration flow

---

# Data Flow

```
Profile Generator
        │
        ▼
Session Manager
        │
        ▼
State Machine
        │
        ▼
Create Base Log
        │
        ▼
Anomaly Injector
        │
        ▼
Dispatcher
        │
        ▼
Spring Boot REST API
```

---

# JSON Schema

Each generated log follows the schema below.

```json
{
  "entity_id": "user_123",
  "auth_method": "password",
  "auth_status": "success",
  "timestamp": "2026-07-25T08:00:00.000Z",
  "source_ip": "192.168.1.25",
  "geo_location": {
    "lat": 19.076,
    "lon": 72.8777
  },
  "device_id": "device_xyz",
  "os_version": "Windows 11",
  "user_agent": "Chrome/126",
  "resource_accessed": "/api/v1/hr/employees"
}
```

---

# Running the Project

Install dependencies

```bash
pip install -r requirements.txt
```

Run the fake server

```bash
python fake_server.py
```

Start the generator

```bash
python synthetic_log_generator.py
```

---

# Current Status

Implemented

* User generation
* Session handling
* State machine
* Six anomaly types
* Dispatcher
* Simulation runner
* Fake server
* Project verification

Planned

* Spring Boot integration
* Kafka streaming
* Elasticsearch
* Kibana dashboards
* Machine Learning anomaly detection
* Docker support
* Kubernetes deployment

---

# Notes

This project is being developed incrementally. The architecture is modular so individual components can be replaced or extended with minimal impact on the rest of the system.

For a detailed explanation of every class, method, design decision, and extension point, refer to the forthcoming `DEVELOPER_GUIDE.md`.
