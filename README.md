# Incident Response Dashboard

Real-time incident tracking and RCA (Root Cause Analysis) dashboard with SLA/OLA monitoring. Built with Python, Flask, and simple HTML/JavaScript for visualization.

## Features

- **Incident Management**: Create, update, and track incidents with severity levels
- **SLA/OLA Monitoring**: Automatic SLA breach detection and time-to-resolution tracking
- **Escalation Workflows**: Auto-escalate incidents based on severity and time thresholds
- **RCA Tracking**: Document root causes and corrective actions
- **Dashboard Visualization**: Real-time metrics and incident status overview
- **REST API**: Complete API for incident lifecycle management

## Tech Stack

- Python 3.8+
- Flask (Web framework)
- SQLite (Database)
- HTML/CSS/JavaScript (Frontend)

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/incident-response-dashboard.git
cd incident-response-dashboard

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Run the application
python app.py

# Access the dashboard at http://localhost:5000
```

## API Endpoints

### Incidents
- `POST /api/incidents` - Create new incident
- `GET /api/incidents` - List all incidents
- `GET /api/incidents/<id>` - Get incident details
- `PUT /api/incidents/<id>` - Update incident
- `POST /api/incidents/<id>/resolve` - Resolve incident

### Metrics
- `GET /api/metrics` - Get dashboard metrics
- `GET /api/sla-status` - Check SLA compliance

## Example Usage

```bash
# Create a new incident
curl -X POST http://localhost:5000/api/incidents \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Database connection timeout",
    "description": "Users unable to access application",
    "severity": "critical",
    "assigned_to": "oncall-team"
  }'

# Resolve an incident
curl -X POST http://localhost:5000/api/incidents/1/resolve \
  -H "Content-Type: application/json" \
  -d '{
    "root_cause": "Connection pool exhaustion",
    "corrective_action": "Increased pool size to 50"
  }'
```

## SLA Definitions

- **Critical**: Response time 15 min, Resolution time 4 hours
- **High**: Response time 1 hour, Resolution time 8 hours
- **Medium**: Response time 4 hours, Resolution time 24 hours
- **Low**: Response time 24 hours, Resolution time 72 hours

## Project Structure

```
incident-response-dashboard/
├── app.py                 # Main Flask application
├── models.py              # Database models
├── incident_manager.py    # Core incident management logic
├── sla_monitor.py         # SLA monitoring and escalation
├── templates/
│   └── dashboard.html     # Dashboard UI
├── requirements.txt
└── README.md
```

## License

MIT License