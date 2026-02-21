from flask import Flask, jsonify, request, render_template
from datetime import datetime
import sqlite3
from models import init_db
from incident_manager import IncidentManager
from sla_monitor import SLAMonitor

app = Flask(__name__)
app.config['DATABASE'] = 'incidents.db'

init_db(app.config['DATABASE'])
incident_manager = IncidentManager(app.config['DATABASE'])
sla_monitor = SLAMonitor(app.config['DATABASE'])


@app.route('/')
def dashboard():
    """Render the main dashboard"""
    return render_template('dashboard.html')


@app.route('/api/incidents', methods=['GET', 'POST'])
def incidents():
    """List all incidents or create a new one"""
    if request.method == 'POST':
        data = request.json
        incident_id = incident_manager.create_incident(
            title=data['title'],
            description=data['description'],
            severity=data['severity'],
            assigned_to=data.get('assigned_to', 'unassigned')
        )
        return jsonify({'id': incident_id, 'status': 'created'}), 201
    
    status = request.args.get('status')
    severity = request.args.get('severity')
    incidents = incident_manager.get_incidents(status=status, severity=severity)
    return jsonify(incidents)


@app.route('/api/incidents/<int:incident_id>', methods=['GET', 'PUT'])
def incident_detail(incident_id):
    """Get or update a specific incident"""
    if request.method == 'PUT':
        data = request.json
        incident_manager.update_incident(incident_id, data)
        return jsonify({'status': 'updated'})
    
    incident = incident_manager.get_incident(incident_id)
    if not incident:
        return jsonify({'error': 'Incident not found'}), 404
    return jsonify(incident)


@app.route('/api/incidents/<int:incident_id>/resolve', methods=['POST'])
def resolve_incident(incident_id):
    """Resolve an incident with RCA"""
    data = request.json
    incident_manager.resolve_incident(
        incident_id=incident_id,
        root_cause=data.get('root_cause', ''),
        corrective_action=data.get('corrective_action', '')
    )
    return jsonify({'status': 'resolved'})


@app.route('/api/metrics', methods=['GET'])
def metrics():
    """Get dashboard metrics"""
    metrics = incident_manager.get_metrics()
    return jsonify(metrics)


@app.route('/api/sla-status', methods=['GET'])
def sla_status():
    """Check SLA compliance for all active incidents"""
    violations = sla_monitor.check_sla_violations()
    escalations = sla_monitor.check_escalations()
    
    return jsonify({
        'violations': violations,
        'escalations': escalations,
        'total_violations': len(violations)
    })


@app.route('/api/escalate', methods=['POST'])
def escalate():
    """Manually run escalation check"""
    escalated = sla_monitor.escalate_incidents()
    return jsonify({
        'escalated_count': len(escalated),
        'escalated_incidents': escalated
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
