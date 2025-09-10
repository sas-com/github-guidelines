#!/usr/bin/env python3
"""
Notification Handler - Multi-channel notification system for incident response
SAS Corporation - GitHub Security Team
"""

import json
import os
import sys
import argparse
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
import asyncio
import aiohttp

class NotificationChannel(Enum):
    EMAIL = "email"
    TEAMS = "teams"
    SLACK = "slack"
    SMS = "sms"
    WEBHOOK = "webhook"
    PAGERDUTY = "pagerduty"

class NotificationPriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class NotificationHandler:
    """Multi-channel notification handler for incident response"""
    
    def __init__(self, config_file: str = "/etc/incident-notifier/config.json"):
        self.config = self._load_config(config_file)
        self.notification_log = []
        
    def _load_config(self, config_file: str) -> Dict:
        """Load notification configuration"""
        default_config = {
            "email": {
                "enabled": True,
                "smtp_server": os.environ.get("SMTP_SERVER", "smtp.gmail.com"),
                "smtp_port": int(os.environ.get("SMTP_PORT", "587")),
                "smtp_user": os.environ.get("SMTP_USER", ""),
                "smtp_password": os.environ.get("SMTP_PASSWORD", ""),
                "from_address": os.environ.get("FROM_EMAIL", "security@sas-com.com")
            },
            "teams": {
                "enabled": True,
                "webhook_url": os.environ.get("TEAMS_WEBHOOK_URL", "")
            },
            "slack": {
                "enabled": False,
                "webhook_url": os.environ.get("SLACK_WEBHOOK_URL", ""),
                "token": os.environ.get("SLACK_TOKEN", "")
            },
            "sms": {
                "enabled": False,
                "api_key": os.environ.get("SMS_API_KEY", ""),
                "api_url": os.environ.get("SMS_API_URL", "")
            },
            "pagerduty": {
                "enabled": False,
                "api_key": os.environ.get("PAGERDUTY_API_KEY", ""),
                "service_id": os.environ.get("PAGERDUTY_SERVICE_ID", "")
            },
            "escalation": {
                "P0": {
                    "channels": ["email", "teams", "sms", "pagerduty"],
                    "recipients": {
                        "email": ["cto@sas-com.com", "security-lead@sas-com.com"],
                        "sms": ["+81-90-1234-5678", "+81-90-8765-4321"]
                    },
                    "delay_minutes": 0
                },
                "P1": {
                    "channels": ["email", "teams"],
                    "recipients": {
                        "email": ["security-lead@sas-com.com", "dev-lead@sas-com.com"]
                    },
                    "delay_minutes": 0
                },
                "P2": {
                    "channels": ["email", "teams"],
                    "recipients": {
                        "email": ["security-team@sas-com.com"]
                    },
                    "delay_minutes": 5
                },
                "P3": {
                    "channels": ["email"],
                    "recipients": {
                        "email": ["dev-team@sas-com.com"]
                    },
                    "delay_minutes": 15
                }
            }
        }
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge with default config
                    for key in loaded_config:
                        if key in default_config:
                            default_config[key].update(loaded_config[key])
                        else:
                            default_config[key] = loaded_config[key]
            except Exception as e:
                print(f"Warning: Could not load config file: {e}")
        
        return default_config
    
    async def send_notification(self, incident: Dict, priority: str, 
                               channels: List[str] = None) -> Dict:
        """Send notification through specified channels"""
        
        if channels is None:
            # Use default channels based on priority
            escalation = self.config.get("escalation", {}).get(priority, {})
            channels = escalation.get("channels", ["email"])
        
        results = {
            "success": [],
            "failed": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Prepare notification content
        content = self._prepare_content(incident, priority)
        
        # Send through each channel
        tasks = []
        for channel in channels:
            if channel == NotificationChannel.EMAIL.value:
                tasks.append(self._send_email(content, priority))
            elif channel == NotificationChannel.TEAMS.value:
                tasks.append(self._send_teams(content, priority))
            elif channel == NotificationChannel.SLACK.value:
                tasks.append(self._send_slack(content, priority))
            elif channel == NotificationChannel.SMS.value:
                tasks.append(self._send_sms(content, priority))
            elif channel == NotificationChannel.PAGERDUTY.value:
                tasks.append(self._send_pagerduty(content, priority))
        
        # Execute all notifications concurrently
        channel_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for channel, result in zip(channels, channel_results):
            if isinstance(result, Exception):
                results["failed"].append({
                    "channel": channel,
                    "error": str(result)
                })
            elif result:
                results["success"].append(channel)
            else:
                results["failed"].append({
                    "channel": channel,
                    "error": "Unknown error"
                })
        
        # Log notification
        self.notification_log.append({
            "timestamp": results["timestamp"],
            "incident_id": incident.get("incident_id"),
            "priority": priority,
            "channels": channels,
            "results": results
        })
        
        return results
    
    def _prepare_content(self, incident: Dict, priority: str) -> Dict:
        """Prepare notification content"""
        
        severity_emoji = {
            "P0": "🚨",
            "P1": "⚠️",
            "P2": "⚡",
            "P3": "ℹ️"
        }
        
        content = {
            "subject": f"{severity_emoji.get(priority, '📢')} [{priority}] Security Incident: {incident.get('incident_id', 'Unknown')}",
            "title": f"Security Incident Alert - {incident.get('title', 'Incident Detected')}",
            "priority": priority,
            "incident_id": incident.get("incident_id", "N/A"),
            "type": incident.get("type", "Unknown"),
            "severity": incident.get("severity", priority),
            "status": incident.get("status", "Open"),
            "description": incident.get("description", "No description provided"),
            "affected_systems": incident.get("affected_systems", "Not specified"),
            "reporter": incident.get("reporter", "System"),
            "timestamp": incident.get("timestamp", datetime.now().isoformat()),
            "actions_required": self._get_required_actions(priority),
            "response_url": incident.get("url", ""),
            "color": self._get_color_code(priority)
        }
        
        return content
    
    def _get_required_actions(self, priority: str) -> List[str]:
        """Get required actions based on priority"""
        
        actions = {
            "P0": [
                "Join emergency response call immediately",
                "Begin incident containment procedures",
                "Notify executive team",
                "Prepare for potential data breach notification"
            ],
            "P1": [
                "Review incident details",
                "Join incident response channel",
                "Begin investigation",
                "Assess impact scope"
            ],
            "P2": [
                "Review incident within 4 hours",
                "Assign to appropriate team member",
                "Schedule investigation"
            ],
            "P3": [
                "Add to backlog for review",
                "Schedule for next business day"
            ]
        }
        
        return actions.get(priority, ["Review incident details"])
    
    def _get_color_code(self, priority: str) -> str:
        """Get color code for priority level"""
        
        colors = {
            "P0": "#FF0000",  # Red
            "P1": "#FF8800",  # Orange
            "P2": "#FFAA00",  # Yellow
            "P3": "#0088FF",  # Blue
        }
        
        return colors.get(priority, "#808080")  # Gray default
    
    async def _send_email(self, content: Dict, priority: str) -> bool:
        """Send email notification"""
        
        if not self.config["email"]["enabled"]:
            return False
        
        try:
            # Get recipients
            escalation = self.config["escalation"].get(priority, {})
            recipients = escalation.get("recipients", {}).get("email", [])
            
            if not recipients:
                return False
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = content["subject"]
            msg['From'] = self.config["email"]["from_address"]
            msg['To'] = ", ".join(recipients)
            
            # HTML body
            html_body = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    .header {{ background-color: {content['color']}; color: white; padding: 20px; }}
                    .content {{ padding: 20px; }}
                    .field {{ margin: 10px 0; }}
                    .label {{ font-weight: bold; }}
                    .actions {{ background-color: #f0f0f0; padding: 15px; margin: 20px 0; }}
                    .footer {{ color: #666; font-size: 12px; padding: 20px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>{content['title']}</h1>
                </div>
                <div class="content">
                    <div class="field">
                        <span class="label">Incident ID:</span> {content['incident_id']}
                    </div>
                    <div class="field">
                        <span class="label">Priority:</span> {content['priority']}
                    </div>
                    <div class="field">
                        <span class="label">Type:</span> {content['type']}
                    </div>
                    <div class="field">
                        <span class="label">Status:</span> {content['status']}
                    </div>
                    <div class="field">
                        <span class="label">Description:</span><br>
                        {content['description']}
                    </div>
                    <div class="field">
                        <span class="label">Affected Systems:</span><br>
                        {content['affected_systems']}
                    </div>
                    <div class="field">
                        <span class="label">Reporter:</span> {content['reporter']}
                    </div>
                    <div class="field">
                        <span class="label">Time:</span> {content['timestamp']}
                    </div>
                    
                    <div class="actions">
                        <h3>Required Actions:</h3>
                        <ul>
                            {''.join(f"<li>{action}</li>" for action in content['actions_required'])}
                        </ul>
                    </div>
                    
                    {f'<p><a href="{content["response_url"]}">View Incident Details</a></p>' if content['response_url'] else ''}
                </div>
                <div class="footer">
                    <p>This is an automated notification from the SAS Security Incident Response System.</p>
                    <p>Do not reply to this email. For questions, contact security@sas-com.com</p>
                </div>
            </body>
            </html>
            """
            
            # Attach HTML
            msg.attach(MIMEText(html_body, 'html'))
            
            # Send email
            with smtplib.SMTP(self.config["email"]["smtp_server"], 
                             self.config["email"]["smtp_port"]) as server:
                server.starttls()
                if self.config["email"]["smtp_user"] and self.config["email"]["smtp_password"]:
                    server.login(self.config["email"]["smtp_user"], 
                               self.config["email"]["smtp_password"])
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            print(f"Email notification failed: {e}")
            return False
    
    async def _send_teams(self, content: Dict, priority: str) -> bool:
        """Send Microsoft Teams notification"""
        
        if not self.config["teams"]["enabled"] or not self.config["teams"]["webhook_url"]:
            return False
        
        try:
            # Create Teams message card
            message = {
                "@type": "MessageCard",
                "@context": "https://schema.org/extensions",
                "summary": content["subject"],
                "themeColor": content["color"].replace("#", ""),
                "title": content["title"],
                "sections": [
                    {
                        "activityTitle": f"Incident {content['incident_id']}",
                        "facts": [
                            {"name": "Priority", "value": content["priority"]},
                            {"name": "Type", "value": content["type"]},
                            {"name": "Status", "value": content["status"]},
                            {"name": "Affected Systems", "value": content["affected_systems"]},
                            {"name": "Reporter", "value": content["reporter"]},
                            {"name": "Time", "value": content["timestamp"]}
                        ]
                    },
                    {
                        "title": "Description",
                        "text": content["description"]
                    },
                    {
                        "title": "Required Actions",
                        "text": "\n".join(f"• {action}" for action in content["actions_required"])
                    }
                ],
                "potentialAction": []
            }
            
            # Add action button if URL provided
            if content.get("response_url"):
                message["potentialAction"].append({
                    "@type": "OpenUri",
                    "name": "View Incident",
                    "targets": [{"os": "default", "uri": content["response_url"]}]
                })
            
            # Send to Teams
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config["teams"]["webhook_url"],
                    json=message,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    return response.status == 200
                    
        except Exception as e:
            print(f"Teams notification failed: {e}")
            return False
    
    async def _send_slack(self, content: Dict, priority: str) -> bool:
        """Send Slack notification"""
        
        if not self.config["slack"]["enabled"] or not self.config["slack"]["webhook_url"]:
            return False
        
        try:
            # Create Slack message
            message = {
                "text": content["subject"],
                "attachments": [
                    {
                        "color": content["color"],
                        "title": content["title"],
                        "fields": [
                            {"title": "Incident ID", "value": content["incident_id"], "short": True},
                            {"title": "Priority", "value": content["priority"], "short": True},
                            {"title": "Type", "value": content["type"], "short": True},
                            {"title": "Status", "value": content["status"], "short": True},
                            {"title": "Affected Systems", "value": content["affected_systems"], "short": False},
                            {"title": "Description", "value": content["description"], "short": False},
                            {"title": "Required Actions", "value": "\n".join(f"• {a}" for a in content["actions_required"]), "short": False}
                        ],
                        "footer": "Security Incident Response",
                        "ts": int(datetime.now().timestamp())
                    }
                ]
            }
            
            # Add action button if URL provided
            if content.get("response_url"):
                message["attachments"][0]["actions"] = [
                    {
                        "type": "button",
                        "text": "View Incident",
                        "url": content["response_url"]
                    }
                ]
            
            # Send to Slack
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config["slack"]["webhook_url"],
                    json=message,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    return response.status == 200
                    
        except Exception as e:
            print(f"Slack notification failed: {e}")
            return False
    
    async def _send_sms(self, content: Dict, priority: str) -> bool:
        """Send SMS notification for critical incidents"""
        
        if not self.config["sms"]["enabled"] or priority not in ["P0", "P1"]:
            return False
        
        try:
            # Get SMS recipients
            escalation = self.config["escalation"].get(priority, {})
            recipients = escalation.get("recipients", {}).get("sms", [])
            
            if not recipients:
                return False
            
            # Create SMS message (limited to 160 characters)
            sms_text = f"{content['priority']} SECURITY INCIDENT {content['incident_id']}: {content['title'][:50]}. Check email/Teams for details."
            
            # Send SMS (implementation depends on SMS provider)
            # This is a placeholder for actual SMS API integration
            success = True
            for phone in recipients:
                # Actual SMS sending would go here
                print(f"SMS would be sent to {phone}: {sms_text}")
            
            return success
            
        except Exception as e:
            print(f"SMS notification failed: {e}")
            return False
    
    async def _send_pagerduty(self, content: Dict, priority: str) -> bool:
        """Send PagerDuty alert for critical incidents"""
        
        if not self.config["pagerduty"]["enabled"] or priority not in ["P0", "P1"]:
            return False
        
        try:
            # Create PagerDuty incident
            incident = {
                "incident": {
                    "type": "incident",
                    "title": content["title"],
                    "service": {
                        "id": self.config["pagerduty"]["service_id"],
                        "type": "service_reference"
                    },
                    "urgency": "high" if priority == "P0" else "low",
                    "body": {
                        "type": "incident_body",
                        "details": content["description"]
                    }
                }
            }
            
            # Send to PagerDuty
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.pagerduty.com/incidents",
                    json=incident,
                    headers={
                        "Authorization": f"Token token={self.config['pagerduty']['api_key']}",
                        "Accept": "application/vnd.pagerduty+json;version=2",
                        "Content-Type": "application/json"
                    }
                ) as response:
                    return response.status == 201
                    
        except Exception as e:
            print(f"PagerDuty notification failed: {e}")
            return False
    
    def get_notification_log(self) -> List[Dict]:
        """Get notification history"""
        return self.notification_log
    
    def test_channels(self) -> Dict:
        """Test all configured notification channels"""
        
        test_incident = {
            "incident_id": "TEST-001",
            "title": "Test Notification",
            "type": "test",
            "severity": "P3",
            "status": "testing",
            "description": "This is a test notification to verify channel configuration",
            "affected_systems": "None - This is a test",
            "reporter": "System Test",
            "timestamp": datetime.now().isoformat()
        }
        
        results = {}
        
        # Test each channel
        loop = asyncio.get_event_loop()
        
        for channel in NotificationChannel:
            if self.config.get(channel.value, {}).get("enabled", False):
                try:
                    result = loop.run_until_complete(
                        self.send_notification(test_incident, "P3", [channel.value])
                    )
                    results[channel.value] = "✅ Success" if channel.value in result["success"] else "❌ Failed"
                except Exception as e:
                    results[channel.value] = f"❌ Error: {str(e)}"
            else:
                results[channel.value] = "⚪ Disabled"
        
        return results

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description='Incident Notification Handler')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Send notification
    send_parser = subparsers.add_parser('send', help='Send incident notification')
    send_parser.add_argument('--incident-id', required=True)
    send_parser.add_argument('--title', required=True)
    send_parser.add_argument('--priority', required=True, choices=['P0', 'P1', 'P2', 'P3'])
    send_parser.add_argument('--type', default='unknown')
    send_parser.add_argument('--description', default='')
    send_parser.add_argument('--systems', default='')
    send_parser.add_argument('--reporter', default='System')
    send_parser.add_argument('--channels', nargs='+', 
                            choices=[c.value for c in NotificationChannel])
    
    # Test channels
    test_parser = subparsers.add_parser('test', help='Test notification channels')
    
    # Show config
    config_parser = subparsers.add_parser('config', help='Show configuration')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize handler
    handler = NotificationHandler()
    
    if args.command == 'send':
        incident = {
            "incident_id": args.incident_id,
            "title": args.title,
            "type": args.type,
            "severity": args.priority,
            "description": args.description,
            "affected_systems": args.systems,
            "reporter": args.reporter,
            "timestamp": datetime.now().isoformat()
        }
        
        # Send notification
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            handler.send_notification(incident, args.priority, args.channels)
        )
        
        print(f"✅ Successful channels: {', '.join(result['success'])}" if result['success'] else "")
        if result['failed']:
            print(f"❌ Failed channels: {result['failed']}")
    
    elif args.command == 'test':
        print("Testing notification channels...")
        results = handler.test_channels()
        
        print("\nChannel Test Results:")
        print("-" * 30)
        for channel, result in results.items():
            print(f"{channel:15} {result}")
    
    elif args.command == 'config':
        print(json.dumps(handler.config, indent=2))

if __name__ == "__main__":
    main()