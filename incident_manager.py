from datetime import datetime
import sqlite3
from models import get_db_connection


class IncidentManager:
    """Core incident management functionality"""
    
    SLA_TIMES = {
        'critical': {'response': 15, 'resolution': 240},  # minutes
        'high': {'response': 60, 'resolution': 480},
        'medium': {'response': 240, 'resolution': 1440},
        'low': {'response': 1440, 'resolution': 4320}
    }
    
    def __init__(self, db_path):
        self.db_path = db_path
    
    def create_incident(self, title, description, severity, assigned_to='unassigned'):
        """Create a new incident"""
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()
        
        sla = self.SLA_TIMES.get(severity.lower(), self.SLA_TIMES['medium'])
        
        cursor.execute('''
            INSERT INTO incidents 
            (title, description, severity, assigned_to, sla_response_time, sla_resolution_time)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (title, description, severity, assigned_to, sla['response'], sla['resolution']))
        
        incident_id = cursor.lastrowid
        
        cursor.execute('''
            INSERT INTO incident_history (incident_id, action, details)
            VALUES (?, ?, ?)
        ''', (incident_id, 'created', f'Incident created with severity {severity}'))
        
        conn.commit()
        conn.close()
        
        return incident_id
    
    def get_incidents(self, status=None, severity=None):
        """Get all incidents with optional filters"""
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()
        
        query = 'SELECT * FROM incidents WHERE 1=1'
        params = []
        
        if status:
            query += ' AND status = ?'
            params.append(status)
        
        if severity:
            query += ' AND severity = ?'
            params.append(severity)
        
        query += ' ORDER BY created_at DESC'
        
        cursor.execute(query, params)
        incidents = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return incidents
    
    def get_incident(self, incident_id):
        """Get a specific incident by ID"""
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM incidents WHERE id = ?', (incident_id,))
        incident = cursor.fetchone()
        
        if incident:
            incident = dict(incident)
            cursor.execute(
                'SELECT * FROM incident_history WHERE incident_id = ? ORDER BY timestamp DESC',
                (incident_id,)
            )
            incident['history'] = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return incident
    
    def update_incident(self, incident_id, data):
        """Update an incident"""
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        for field in ['status', 'severity', 'assigned_to', 'description']:
            if field in data:
                updates.append(f'{field} = ?')
                params.append(data[field])
        
        if updates:
            updates.append('updated_at = CURRENT_TIMESTAMP')
            params.append(incident_id)
            
            query = f"UPDATE incidents SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            
            cursor.execute('''
                INSERT INTO incident_history (incident_id, action, details)
                VALUES (?, ?, ?)
            ''', (incident_id, 'updated', str(data)))
            
            conn.commit()
        
        conn.close()
    
    def resolve_incident(self, incident_id, root_cause, corrective_action):
        """Resolve an incident with RCA"""
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE incidents 
            SET status = 'resolved', 
                resolved_at = CURRENT_TIMESTAMP,
                root_cause = ?,
                corrective_action = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (root_cause, corrective_action, incident_id))
        
        cursor.execute('''
            INSERT INTO incident_history (incident_id, action, details)
            VALUES (?, ?, ?)
        ''', (incident_id, 'resolved', f'Root cause: {root_cause}'))
        
        conn.commit()
        conn.close()
    
    def get_metrics(self):
        """Calculate dashboard metrics"""
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as total FROM incidents')
        total = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as open FROM incidents WHERE status = 'open'")
        open_count = cursor.fetchone()['open']
        
        cursor.execute("SELECT COUNT(*) as resolved FROM incidents WHERE status = 'resolved'")
        resolved = cursor.fetchone()['resolved']
        
        cursor.execute(
            "SELECT severity, COUNT(*) as count FROM incidents WHERE status = 'open' GROUP BY severity"
        )
        by_severity = {row['severity']: row['count'] for row in cursor.fetchall()}
        
        conn.close()
        
        return {
            'total_incidents': total,
            'open_incidents': open_count,
            'resolved_incidents': resolved,
            'by_severity': by_severity
        }
