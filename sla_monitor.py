from datetime import datetime, timedelta
import sqlite3
from models import get_db_connection


class SLAMonitor:
    """SLA monitoring and escalation logic"""
    
    ESCALATION_THRESHOLDS = {
        'critical': [30, 60, 120],  # Escalate at 30, 60, 120 minutes
        'high': [120, 240, 480],
        'medium': [480, 960, 1440],
        'low': [1440, 2880, 4320]
    }
    
    def __init__(self, db_path):
        self.db_path = db_path
    
    def check_sla_violations(self):
        """Check for SLA violations on open incidents"""
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, title, severity, created_at, sla_response_time, sla_resolution_time
            FROM incidents 
            WHERE status = 'open'
        """)
        
        violations = []
        now = datetime.now()
        
        for row in cursor.fetchall():
            incident = dict(row)
            created_at = datetime.strptime(incident['created_at'], '%Y-%m-%d %H:%M:%S')
            age_minutes = (now - created_at).total_seconds() / 60
            
            violation = {
                'incident_id': incident['id'],
                'title': incident['title'],
                'severity': incident['severity'],
                'age_minutes': int(age_minutes),
                'violations': []
            }
            
            if age_minutes > incident['sla_response_time']:
                violation['violations'].append('response_time')
            
            if age_minutes > incident['sla_resolution_time']:
                violation['violations'].append('resolution_time')
            
            if violation['violations']:
                violations.append(violation)
        
        conn.close()
        return violations
    
    def check_escalations(self):
        """Check which incidents need escalation"""
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, title, severity, created_at, escalation_level
            FROM incidents 
            WHERE status = 'open'
        """)
        
        escalations = []
        now = datetime.now()
        
        for row in cursor.fetchall():
            incident = dict(row)
            created_at = datetime.strptime(incident['created_at'], '%Y-%m-%d %H:%M:%S')
            age_minutes = (now - created_at).total_seconds() / 60
            
            severity = incident['severity'].lower()
            thresholds = self.ESCALATION_THRESHOLDS.get(severity, self.ESCALATION_THRESHOLDS['medium'])
            current_level = incident['escalation_level']
            
            if current_level < len(thresholds) and age_minutes >= thresholds[current_level]:
                escalations.append({
                    'incident_id': incident['id'],
                    'title': incident['title'],
                    'severity': incident['severity'],
                    'current_level': current_level,
                    'new_level': current_level + 1,
                    'age_minutes': int(age_minutes)
                })
        
        conn.close()
        return escalations
    
    def escalate_incidents(self):
        """Perform escalation on incidents that need it"""
        escalations = self.check_escalations()
        
        conn = get_db_connection(self.db_path)
        cursor = conn.cursor()
        
        escalated = []
        
        for escalation in escalations:
            incident_id = escalation['incident_id']
            new_level = escalation['new_level']
            
            cursor.execute(
                'UPDATE incidents SET escalation_level = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                (new_level, incident_id)
            )
            
            cursor.execute('''
                INSERT INTO incident_history (incident_id, action, details)
                VALUES (?, ?, ?)
            ''', (incident_id, 'escalated', f'Escalated to level {new_level}'))
            
            escalated.append(escalation)
        
        conn.commit()
        conn.close()
        
        return escalated
