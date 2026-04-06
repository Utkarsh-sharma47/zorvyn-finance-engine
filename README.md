# Zorvyn Finance Engine

An enterprise-grade, high-performance financial ledger and analytics platform. Built with a decoupled microservice architecture, the system features an ACID-compliant FastAPI backend and a highly optimized, data-driven React frontend.

## System Architecture & Technology Stack

**Backend Services:**
* Framework: Python, FastAPI
* Database: PostgreSQL (Relational Data), SQLAlchemy ORM
* Caching Layer: Redis 
* Infrastructure: Docker & Docker Compose
* Security: JWT (JSON Web Tokens), OAuth2 Password Flow, Argon2 Password Hashing

**Client Application:**
* Framework: React 18, Vite
* Styling: Tailwind CSS (Strict UI/UX Standards)
* Routing & State Management: React Router DOM, React Context API
* Data Visualization: Recharts
* Network Client: Axios (Interceptor-driven Authentication)

---

## Core System Features

This platform was architected with a focus on data integrity, security, and high-performance querying.

### 1. ACID-Compliant Financial Ledger
Engineered a double-entry bookkeeping system to handle fund transfers. The system utilizes strict database transaction blocks to ensure atomicity; if a transfer fails at any computational stage, the entire operation rolls back to prevent orphaned funds or data corruption.

### 2. Advanced Role-Based Access Control (RBAC)
Implemented a hierarchical authorization system across both the API and client levels.
* Tiers: Admin, Dev_Admin, Analyst, and Viewer.
* Dynamic UI Routing: The frontend client restricts access to specific components, views, and actions based on the JWT payload.

### 3. High-Performance Analytics Caching
Integrated a Redis caching layer to handle computationally expensive data aggregation endpoints. Financial summaries and KPI metrics are pre-calculated and served from memory, drastically reducing database load and delivering dashboard data in milliseconds.

### 4. Immutable Audit Trails
Developed an automated, database-level hook system to maintain an immutable audit log. Every destructive or modifying action (INSERT, UPDATE, DELETE) automatically logs the timestamp, executing user ID, and affected table records. Access to this ledger is strictly restricted to Admin roles.

### 5. Secure Client Gateway
Built a robust frontend network layer using Axios interceptors. The client automatically manages JWT Bearer token attachment and handles token expiration by intercepting 401 Unauthorized responses, clearing session state, and executing secure redirects.

### 6. Complex Data Visualization Pipelines
Designed client-side data transformation pipelines that convert raw, paginated transaction arrays into formatted time-series data, enabling real-time rendering of complex charts (Revenue over Time, Expense Categorization) without over-fetching from the backend.

---

## Local Development Environment

The development environment is heavily containerized to ensure parity across local and production deployments.

### Prerequisites
* Docker Desktop
* Node.js (v18 or higher)
* Git

### Starting the Backend Services
The backend relies entirely on Docker Compose to orchestrate the PostgreSQL database, Redis instance, and FastAPI server.

Navigate to the project root and execute:
```bash
docker compose up -d