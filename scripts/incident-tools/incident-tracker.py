#!/usr/bin/env python3
"""
Incident Tracker - Comprehensive incident management system for SAS Corporation
"""

import json
import os
import sys
import argparse
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from enum import Enum

class IncidentSeverity(Enum):
    P0 = "Critical"
    P1 = "High"
    P2 = "Medium"
    P3 = "Low"

class IncidentStatus(Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    RECOVERING = "recovering"
    RESOLVED = "resolved"
    CLOSED = "closed"

class IncidentType(Enum):
    DATA_BREACH = "data_breach"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    MALWARE = "malware"
    VULNERABILITY = "vulnerability"
    DDOS = "ddos"
    INSIDER_THREAT = "insider_threat"
    PHISHING = "phishing"
    OTHER = "other"

class IncidentTracker:
    """Main incident tracking and management system"""
    
    def __init__(self, db_path: str = "/var/lib/incident-tracker/incidents.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self.init_database()
    
    def init_database(self):
        """Initialize the incident database"""
        self.conn = sqlite3.connect(str(self.db_path))
        cursor = self.conn.cursor()
        
        # Create incidents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS incidents (
                incident_id TEXT PRIMARY KEY,
                severity TEXT NOT NULL,
                type TEXT NOT NULL,
                status TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                affected_systems TEXT,
                reporter TEXT NOT NULL,
                assigned_to TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP,
                closed_at TIMESTAMP,
                impact_assessment TEXT,
                root_cause TEXT,
                lessons_learned TEXT
            )
        ''')
        
        # Create timeline table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS incident_timeline (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_id TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                action TEXT NOT NULL,
                performed_by TEXT NOT NULL,
                details TEXT,
                FOREIGN KEY (incident_id) REFERENCES incidents(incident_id)
            )
        ''')
        
        # Create notifications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_id TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                recipient TEXT NOT NULL,
                method TEXT NOT NULL,
                message TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                FOREIGN KEY (incident_id) REFERENCES incidents(incident_id)
            )
        ''')
        
        # Create evidence table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS evidence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_id TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                file_path TEXT NOT NULL,
                file_hash TEXT,
                description TEXT,
                collected_by TEXT NOT NULL,
                FOREIGN KEY (incident_id) REFERENCES incidents(incident_id)
            )
        ''')
        
        self.conn.commit()
    
    def create_incident(self, severity: str, incident_type: str, title: str,
                       description: str, affected_systems: str, reporter: str) -> str:
        """Create a new incident"""
        incident_id = f"INC-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO incidents (
                incident_id, severity, type, status, title, 
                description, affected_systems, reporter
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            incident_id, severity, incident_type, IncidentStatus.OPEN.value,
            title, description, affected_systems, reporter
        ))
        
        # Add initial timeline entry
        self.add_timeline_entry(
            incident_id, 
            f"Incident created with severity {severity}",
            reporter
        )
        
        # Trigger notifications based on severity
        self._trigger_notifications(incident_id, severity, "created")
        
        self.conn.commit()
        
        print(f"✅ Incident created: {incident_id}")
        return incident_id
    
    def update_incident_status(self, incident_id: str, new_status: str, 
                               updated_by: str, notes: str = None) -> bool:
        """Update incident status"""
        cursor = self.conn.cursor()
        
        # Get current status
        cursor.execute('SELECT status FROM incidents WHERE incident_id = ?', (incident_id,))
        result = cursor.fetchone()
        
        if not result:
            print(f"❌ Incident {incident_id} not found")
            return False
        
        old_status = result[0]
        
        # Update status
        cursor.execute('''
            UPDATE incidents 
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE incident_id = ?
        ''', (new_status, incident_id))
        
        # Update resolved/closed timestamps
        if new_status == IncidentStatus.RESOLVED.value:
            cursor.execute('''
                UPDATE incidents 
                SET resolved_at = CURRENT_TIMESTAMP
                WHERE incident_id = ?
            ''', (incident_id,))
        elif new_status == IncidentStatus.CLOSED.value:
            cursor.execute('''
                UPDATE incidents 
                SET closed_at = CURRENT_TIMESTAMP
                WHERE incident_id = ?
            ''', (incident_id,))
        
        # Add timeline entry
        action = f"Status changed from {old_status} to {new_status}"
        if notes:
            action += f" - {notes}"
        self.add_timeline_entry(incident_id, action, updated_by)
        
        self.conn.commit()
        
        print(f"✅ Incident {incident_id} status updated to {new_status}")
        return True
    
    def add_timeline_entry(self, incident_id: str, action: str, 
                           performed_by: str, details: str = None):
        """Add an entry to the incident timeline"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO incident_timeline (incident_id, action, performed_by, details)
            VALUES (?, ?, ?, ?)
        ''', (incident_id, action, performed_by, details))
        self.conn.commit()
    
    def add_evidence(self, incident_id: str, file_path: str, 
                    description: str, collected_by: str) -> bool:
        """Register evidence for an incident"""
        from hashlib import sha256
        
        # Calculate file hash
        file_hash = None
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                file_hash = sha256(f.read()).hexdigest()
        
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO evidence (incident_id, file_path, file_hash, description, collected_by)
            VALUES (?, ?, ?, ?, ?)
        ''', (incident_id, file_path, file_hash, description, collected_by))
        
        self.add_timeline_entry(
            incident_id, 
            f"Evidence added: {os.path.basename(file_path)}",
            collected_by
        )
        
        self.conn.commit()
        
        print(f"✅ Evidence registered for incident {incident_id}")
        return True
    
    def get_incident_details(self, incident_id: str) -> Optional[Dict]:
        """Get detailed information about an incident"""
        cursor = self.conn.cursor()
        
        # Get incident details
        cursor.execute('SELECT * FROM incidents WHERE incident_id = ?', (incident_id,))
        incident = cursor.fetchone()
        
        if not incident:
            return None
        
        # Get timeline
        cursor.execute('''
            SELECT timestamp, action, performed_by, details 
            FROM incident_timeline 
            WHERE incident_id = ? 
            ORDER BY timestamp
        ''', (incident_id,))
        timeline = cursor.fetchall()
        
        # Get evidence
        cursor.execute('''
            SELECT file_path, file_hash, description, collected_by, timestamp
            FROM evidence
            WHERE incident_id = ?
            ORDER BY timestamp
        ''', (incident_id,))
        evidence = cursor.fetchall()
        
        # Format response
        details = {
            'incident_id': incident[0],
            'severity': incident[1],
            'type': incident[2],
            'status': incident[3],
            'title': incident[4],
            'description': incident[5],
            'affected_systems': incident[6],
            'reporter': incident[7],
            'assigned_to': incident[8],
            'created_at': incident[9],
            'updated_at': incident[10],
            'resolved_at': incident[11],
            'closed_at': incident[12],
            'timeline': [
                {
                    'timestamp': t[0],
                    'action': t[1],
                    'performed_by': t[2],
                    'details': t[3]
                } for t in timeline
            ],
            'evidence': [
                {
                    'file_path': e[0],
                    'file_hash': e[1],
                    'description': e[2],
                    'collected_by': e[3],
                    'timestamp': e[4]
                } for e in evidence
            ]
        }
        
        return details
    
    def list_incidents(self, status: str = None, severity: str = None, 
                       days: int = None) -> List[Dict]:
        """List incidents with optional filters"""
        query = 'SELECT * FROM incidents WHERE 1=1'
        params = []
        
        if status:
            query += ' AND status = ?'
            params.append(status)
        
        if severity:
            query += ' AND severity = ?'
            params.append(severity)
        
        if days:
            cutoff_date = datetime.now() - timedelta(days=days)
            query += ' AND created_at >= ?'
            params.append(cutoff_date.isoformat())
        
        query += ' ORDER BY created_at DESC'
        
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        incidents = cursor.fetchall()
        
        return [
            {
                'incident_id': i[0],
                'severity': i[1],
                'type': i[2],
                'status': i[3],
                'title': i[4],
                'created_at': i[9],
                'updated_at': i[10]
            } for i in incidents
        ]
    
    def generate_report(self, incident_id: str) -> str:
        """Generate a comprehensive incident report"""
        details = self.get_incident_details(incident_id)
        
        if not details:
            return f"Incident {incident_id} not found"
        
        report = f"""
# Incident Report: {details['incident_id']}

## Summary
- **Title**: {details['title']}
- **Severity**: {details['severity']}
- **Type**: {details['type']}
- **Status**: {details['status']}
- **Reporter**: {details['reporter']}
- **Created**: {details['created_at']}
- **Last Updated**: {details['updated_at']}

## Description
{details['description'] or 'No description provided'}

## Affected Systems
{details['affected_systems'] or 'Not specified'}

## Timeline
"""
        
        for entry in details['timeline']:
            report += f"- **{entry['timestamp']}** - {entry['action']} (by {entry['performed_by']})\n"
            if entry['details']:
                report += f"  Details: {entry['details']}\n"
        
        report += "\n## Evidence Collected\n"
        if details['evidence']:
            for e in details['evidence']:
                report += f"- {e['description']} ({e['file_path']})\n"
                report += f"  Hash: {e['file_hash']}\n"
                report += f"  Collected by: {e['collected_by']} at {e['timestamp']}\n"
        else:
            report += "No evidence collected yet.\n"
        
        if details['resolved_at']:
            report += f"\n## Resolution\n"
            report += f"- **Resolved at**: {details['resolved_at']}\n"
        
        if details['closed_at']:
            report += f"- **Closed at**: {details['closed_at']}\n"
        
        return report
    
    def calculate_metrics(self, days: int = 30) -> Dict:
        """Calculate incident metrics for the specified period"""
        cutoff_date = datetime.now() - timedelta(days=days)
        cursor = self.conn.cursor()
        
        # Total incidents
        cursor.execute('''
            SELECT COUNT(*) FROM incidents 
            WHERE created_at >= ?
        ''', (cutoff_date.isoformat(),))
        total_incidents = cursor.fetchone()[0]
        
        # By severity
        cursor.execute('''
            SELECT severity, COUNT(*) FROM incidents 
            WHERE created_at >= ?
            GROUP BY severity
        ''', (cutoff_date.isoformat(),))
        by_severity = dict(cursor.fetchall())
        
        # By status
        cursor.execute('''
            SELECT status, COUNT(*) FROM incidents 
            WHERE created_at >= ?
            GROUP BY status
        ''', (cutoff_date.isoformat(),))
        by_status = dict(cursor.fetchall())
        
        # Average resolution time
        cursor.execute('''
            SELECT AVG(
                CAST((julianday(resolved_at) - julianday(created_at)) * 24 AS REAL)
            )
            FROM incidents 
            WHERE created_at >= ? AND resolved_at IS NOT NULL
        ''', (cutoff_date.isoformat(),))
        avg_resolution_hours = cursor.fetchone()[0] or 0
        
        # MTTR (Mean Time To Respond) - time to first timeline entry
        cursor.execute('''
            SELECT AVG(
                CAST((julianday(t.min_timestamp) - julianday(i.created_at)) * 24 * 60 AS REAL)
            )
            FROM incidents i
            JOIN (
                SELECT incident_id, MIN(timestamp) as min_timestamp
                FROM incident_timeline
                GROUP BY incident_id
            ) t ON i.incident_id = t.incident_id
            WHERE i.created_at >= ?
        ''', (cutoff_date.isoformat(),))
        mttr_minutes = cursor.fetchone()[0] or 0
        
        return {
            'period_days': days,
            'total_incidents': total_incidents,
            'by_severity': by_severity,
            'by_status': by_status,
            'avg_resolution_hours': round(avg_resolution_hours, 2),
            'mttr_minutes': round(mttr_minutes, 2)
        }
    
    def _trigger_notifications(self, incident_id: str, severity: str, event: str):
        """Trigger notifications based on incident severity and event"""
        notification_rules = {
            'P0': ['cto@sas-com.com', 'security-lead@sas-com.com', 'dev-lead@sas-com.com'],
            'P1': ['security-lead@sas-com.com', 'dev-lead@sas-com.com'],
            'P2': ['security-team@sas-com.com'],
            'P3': ['dev-team@sas-com.com']
        }
        
        recipients = notification_rules.get(severity, [])
        
        for recipient in recipients:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO notifications (incident_id, recipient, method, message)
                VALUES (?, ?, ?, ?)
            ''', (
                incident_id, 
                recipient, 
                'email',
                f"New {severity} incident {incident_id} has been {event}"
            ))
        
        self.conn.commit()
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description='Incident Tracker - Manage security incidents')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Create incident
    create_parser = subparsers.add_parser('create', help='Create a new incident')
    create_parser.add_argument('--severity', required=True, choices=['P0', 'P1', 'P2', 'P3'])
    create_parser.add_argument('--type', required=True, 
                              choices=[t.value for t in IncidentType])
    create_parser.add_argument('--title', required=True)
    create_parser.add_argument('--description', required=True)
    create_parser.add_argument('--systems', required=True, help='Affected systems')
    create_parser.add_argument('--reporter', required=True)
    
    # Update status
    update_parser = subparsers.add_parser('update', help='Update incident status')
    update_parser.add_argument('incident_id', help='Incident ID')
    update_parser.add_argument('--status', required=True, 
                               choices=[s.value for s in IncidentStatus])
    update_parser.add_argument('--user', required=True, help='User making the update')
    update_parser.add_argument('--notes', help='Additional notes')
    
    # Add evidence
    evidence_parser = subparsers.add_parser('add-evidence', help='Add evidence to incident')
    evidence_parser.add_argument('incident_id', help='Incident ID')
    evidence_parser.add_argument('--file', required=True, help='Evidence file path')
    evidence_parser.add_argument('--description', required=True)
    evidence_parser.add_argument('--collector', required=True)
    
    # Get details
    details_parser = subparsers.add_parser('details', help='Get incident details')
    details_parser.add_argument('incident_id', help='Incident ID')
    
    # List incidents
    list_parser = subparsers.add_parser('list', help='List incidents')
    list_parser.add_argument('--status', choices=[s.value for s in IncidentStatus])
    list_parser.add_argument('--severity', choices=['P0', 'P1', 'P2', 'P3'])
    list_parser.add_argument('--days', type=int, help='Last N days')
    
    # Generate report
    report_parser = subparsers.add_parser('report', help='Generate incident report')
    report_parser.add_argument('incident_id', help='Incident ID')
    
    # Calculate metrics
    metrics_parser = subparsers.add_parser('metrics', help='Calculate incident metrics')
    metrics_parser.add_argument('--days', type=int, default=30, help='Period in days')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize tracker
    tracker = IncidentTracker()
    
    try:
        if args.command == 'create':
            incident_id = tracker.create_incident(
                args.severity, args.type, args.title,
                args.description, args.systems, args.reporter
            )
            print(f"Incident ID: {incident_id}")
        
        elif args.command == 'update':
            tracker.update_incident_status(
                args.incident_id, args.status, args.user, args.notes
            )
        
        elif args.command == 'add-evidence':
            tracker.add_evidence(
                args.incident_id, args.file, args.description, args.collector
            )
        
        elif args.command == 'details':
            details = tracker.get_incident_details(args.incident_id)
            if details:
                print(json.dumps(details, indent=2, default=str))
            else:
                print(f"Incident {args.incident_id} not found")
        
        elif args.command == 'list':
            incidents = tracker.list_incidents(args.status, args.severity, args.days)
            for inc in incidents:
                print(f"{inc['incident_id']} | {inc['severity']} | {inc['status']} | {inc['title']}")
        
        elif args.command == 'report':
            report = tracker.generate_report(args.incident_id)
            print(report)
        
        elif args.command == 'metrics':
            metrics = tracker.calculate_metrics(args.days)
            print(f"\n📊 Incident Metrics (Last {metrics['period_days']} days)")
            print(f"Total Incidents: {metrics['total_incidents']}")
            print(f"By Severity: {metrics['by_severity']}")
            print(f"By Status: {metrics['by_status']}")
            print(f"Avg Resolution Time: {metrics['avg_resolution_hours']} hours")
            print(f"Mean Time To Respond: {metrics['mttr_minutes']} minutes")
    
    finally:
        tracker.close()

if __name__ == "__main__":
    main()