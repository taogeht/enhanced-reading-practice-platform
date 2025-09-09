"""
Security audit utilities and automated security checks
"""

import os
import subprocess
import json
import logging
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone
import re

logger = logging.getLogger('security')

User = get_user_model()


class SecurityAuditor:
    """
    Automated security audit system
    """
    
    def __init__(self):
        self.audit_results = []
        self.warnings = []
        self.critical_issues = []
    
    def run_full_audit(self):
        """
        Run complete security audit
        """
        logger.info("Starting comprehensive security audit")
        
        # Configuration audits
        self.audit_django_settings()
        self.audit_middleware_configuration()
        self.audit_database_configuration()
        
        # Code security audits
        self.audit_dependencies()
        self.audit_user_permissions()
        self.audit_authentication_settings()
        
        # Runtime security audits
        self.audit_failed_login_attempts()
        self.audit_suspicious_activities()
        self.audit_file_permissions()
        
        # Generate report
        report = self.generate_audit_report()
        
        logger.info(f"Security audit completed. Found {len(self.critical_issues)} critical issues, {len(self.warnings)} warnings")
        
        return report
    
    def audit_django_settings(self):
        """
        Audit Django security settings
        """
        issues = []
        
        # Check DEBUG setting
        if settings.DEBUG:
            self.critical_issues.append({
                'category': 'Configuration',
                'issue': 'DEBUG is enabled',
                'severity': 'CRITICAL',
                'description': 'DEBUG mode exposes sensitive information and should be disabled in production',
                'recommendation': 'Set DEBUG = False in production settings'
            })
        
        # Check SECRET_KEY
        if hasattr(settings, 'SECRET_KEY'):
            if len(settings.SECRET_KEY) < 50:
                self.critical_issues.append({
                    'category': 'Configuration',
                    'issue': 'Weak SECRET_KEY',
                    'severity': 'CRITICAL',
                    'description': 'SECRET_KEY is too short or weak',
                    'recommendation': 'Use a strong, randomly generated SECRET_KEY of at least 50 characters'
                })
        
        # Check ALLOWED_HOSTS
        if not settings.ALLOWED_HOSTS or '*' in settings.ALLOWED_HOSTS:
            self.critical_issues.append({
                'category': 'Configuration',
                'issue': 'Insecure ALLOWED_HOSTS',
                'severity': 'HIGH',
                'description': 'ALLOWED_HOSTS is empty or contains wildcard',
                'recommendation': 'Set specific hostnames in ALLOWED_HOSTS'
            })
        
        # Check security headers
        security_settings = [
            ('SECURE_BROWSER_XSS_FILTER', True),
            ('SECURE_CONTENT_TYPE_NOSNIFF', True),
            ('X_FRAME_OPTIONS', 'DENY'),
        ]
        
        for setting, expected in security_settings:
            if not hasattr(settings, setting) or getattr(settings, setting) != expected:
                self.warnings.append({
                    'category': 'Configuration',
                    'issue': f'Missing or incorrect {setting}',
                    'severity': 'MEDIUM',
                    'description': f'{setting} should be set to {expected}',
                    'recommendation': f'Set {setting} = {expected}'
                })
        
        # Check HTTPS settings
        if not settings.DEBUG:
            https_settings = [
                'SESSION_COOKIE_SECURE',
                'CSRF_COOKIE_SECURE',
                'SECURE_HSTS_SECONDS'
            ]
            
            for setting in https_settings:
                if not hasattr(settings, setting) or not getattr(settings, setting):
                    self.warnings.append({
                        'category': 'Configuration',
                        'issue': f'Missing HTTPS setting: {setting}',
                        'severity': 'MEDIUM',
                        'description': f'{setting} should be enabled for HTTPS',
                        'recommendation': f'Enable {setting} for production'
                    })
    
    def audit_middleware_configuration(self):
        """
        Audit middleware security configuration
        """
        required_middleware = [
            'django.middleware.security.SecurityMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
        ]
        
        middleware_list = getattr(settings, 'MIDDLEWARE', [])
        
        for required in required_middleware:
            if required not in middleware_list:
                self.warnings.append({
                    'category': 'Middleware',
                    'issue': f'Missing security middleware: {required}',
                    'severity': 'HIGH',
                    'description': f'Required security middleware {required} is not configured',
                    'recommendation': f'Add {required} to MIDDLEWARE setting'
                })
        
        # Check middleware order
        security_middleware = 'django.middleware.security.SecurityMiddleware'
        if security_middleware in middleware_list:
            index = middleware_list.index(security_middleware)
            if index > 2:  # Should be near the top
                self.warnings.append({
                    'category': 'Middleware',
                    'issue': 'SecurityMiddleware not at top of stack',
                    'severity': 'MEDIUM',
                    'description': 'SecurityMiddleware should be placed early in middleware stack',
                    'recommendation': 'Move SecurityMiddleware to the top of MIDDLEWARE list'
                })
    
    def audit_database_configuration(self):
        """
        Audit database security configuration
        """
        db_config = settings.DATABASES.get('default', {})
        
        # Check for SQLite in production
        if not settings.DEBUG and db_config.get('ENGINE') == 'django.db.backends.sqlite3':
            self.warnings.append({
                'category': 'Database',
                'issue': 'SQLite used in production',
                'severity': 'MEDIUM',
                'description': 'SQLite is not recommended for production use',
                'recommendation': 'Use PostgreSQL or MySQL for production'
            })
        
        # Check for empty database password
        if 'PASSWORD' in db_config and not db_config['PASSWORD']:
            self.critical_issues.append({
                'category': 'Database',
                'issue': 'Empty database password',
                'severity': 'CRITICAL',
                'description': 'Database password is empty',
                'recommendation': 'Set a strong database password'
            })
    
    def audit_dependencies(self):
        """
        Audit Python dependencies for known vulnerabilities
        """
        try:
            # Check if safety is available
            result = subprocess.run(['safety', 'check', '--json'], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                vulnerabilities = json.loads(result.stdout)
                for vuln in vulnerabilities:
                    self.critical_issues.append({
                        'category': 'Dependencies',
                        'issue': f'Vulnerable dependency: {vuln.get("package", "unknown")}',
                        'severity': 'HIGH',
                        'description': vuln.get('advisory', 'Known security vulnerability'),
                        'recommendation': f'Update to version {vuln.get("analyzed_version", "latest")}'
                    })
            
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            self.warnings.append({
                'category': 'Dependencies',
                'issue': 'Could not run dependency vulnerability check',
                'severity': 'LOW',
                'description': 'Safety tool not available for dependency scanning',
                'recommendation': 'Install safety: pip install safety'
            })
    
    def audit_user_permissions(self):
        """
        Audit user permissions and access patterns
        """
        # Check for users with excessive permissions
        superusers = User.objects.filter(is_superuser=True).count()
        if superusers > 2:
            self.warnings.append({
                'category': 'User Management',
                'issue': f'Too many superusers ({superusers})',
                'severity': 'MEDIUM',
                'description': 'Large number of superuser accounts increases risk',
                'recommendation': 'Review and reduce number of superuser accounts'
            })
        
        # Check for inactive admin accounts
        inactive_admins = User.objects.filter(
            Q(is_staff=True) | Q(is_superuser=True),
            is_active=False
        ).count()
        
        if inactive_admins > 0:
            self.warnings.append({
                'category': 'User Management',
                'issue': f'Inactive admin accounts ({inactive_admins})',
                'severity': 'LOW',
                'description': 'Inactive admin accounts should be cleaned up',
                'recommendation': 'Remove or properly deactivate unused admin accounts'
            })
        
        # Check for users without recent activity
        thirty_days_ago = timezone.now() - timedelta(days=30)
        stale_users = User.objects.filter(
            last_login__lt=thirty_days_ago,
            is_active=True
        ).count()
        
        if stale_users > 10:
            self.warnings.append({
                'category': 'User Management',
                'issue': f'Many stale user accounts ({stale_users})',
                'severity': 'LOW',
                'description': 'Large number of inactive user accounts',
                'recommendation': 'Review and deactivate unused accounts'
            })
    
    def audit_authentication_settings(self):
        """
        Audit authentication configuration
        """
        # Check password validators
        password_validators = getattr(settings, 'AUTH_PASSWORD_VALIDATORS', [])
        
        required_validators = [
            'django.contrib.auth.password_validation.MinimumLengthValidator',
            'django.contrib.auth.password_validation.CommonPasswordValidator',
        ]
        
        configured_validators = [v['NAME'] for v in password_validators]
        
        for required in required_validators:
            if required not in configured_validators:
                self.warnings.append({
                    'category': 'Authentication',
                    'issue': f'Missing password validator: {required.split(".")[-1]}',
                    'severity': 'MEDIUM',
                    'description': f'Password validation is incomplete',
                    'recommendation': f'Add {required} to AUTH_PASSWORD_VALIDATORS'
                })
        
        # Check session settings
        session_age = getattr(settings, 'SESSION_COOKIE_AGE', 1209600)  # Default is 2 weeks
        if session_age > 86400:  # More than 1 day
            self.warnings.append({
                'category': 'Authentication',
                'issue': 'Long session timeout',
                'severity': 'LOW',
                'description': f'Session timeout is {session_age/3600:.1f} hours',
                'recommendation': 'Consider shorter session timeout for security'
            })
    
    def audit_failed_login_attempts(self):
        """
        Audit recent failed login attempts
        """
        # Check cache for recent failed attempts
        failed_attempts_pattern = "login_attempts_*"
        cache_keys = cache.keys(failed_attempts_pattern)
        
        high_failure_ips = []
        for key in cache_keys:
            attempts = cache.get(key, 0)
            if attempts > 10:  # High number of failures
                ip = key.replace('login_attempts_', '')
                high_failure_ips.append((ip, attempts))
        
        if high_failure_ips:
            self.warnings.append({
                'category': 'Authentication',
                'issue': f'High failed login attempts from {len(high_failure_ips)} IPs',
                'severity': 'MEDIUM',
                'description': f'IPs with high failure rates: {high_failure_ips[:5]}',
                'recommendation': 'Monitor and consider blocking persistent attackers'
            })
    
    def audit_suspicious_activities(self):
        """
        Audit for suspicious activities in recent logs
        """
        # This would typically check log files for suspicious patterns
        # For now, we'll check for basic patterns
        
        suspicious_patterns = [
            'SQL injection attempt',
            'XSS attempt',
            'Path traversal attempt',
            'Suspicious user agent',
        ]
        
        # In a real implementation, this would parse log files
        # For now, we'll just note that log monitoring should be in place
        self.audit_results.append({
            'category': 'Monitoring',
            'issue': 'Log monitoring status',
            'severity': 'INFO',
            'description': 'Automated log analysis should be configured',
            'recommendation': 'Implement automated log analysis for security events'
        })
    
    def audit_file_permissions(self):
        """
        Audit file system permissions
        """
        sensitive_files = [
            settings.BASE_DIR / 'db.sqlite3',
            settings.BASE_DIR / 'manage.py',
        ]
        
        for file_path in sensitive_files:
            if file_path.exists():
                stat = file_path.stat()
                permissions = oct(stat.st_mode)[-3:]
                
                # Check if file is world-readable
                if permissions[-1] in ['4', '5', '6', '7']:
                    self.warnings.append({
                        'category': 'File Permissions',
                        'issue': f'World-readable file: {file_path.name}',
                        'severity': 'MEDIUM',
                        'description': f'File {file_path} has permissions {permissions}',
                        'recommendation': f'Restrict permissions: chmod 640 {file_path}'
                    })
    
    def generate_audit_report(self):
        """
        Generate comprehensive audit report
        """
        report = {
            'audit_timestamp': datetime.now().isoformat(),
            'summary': {
                'critical_issues': len(self.critical_issues),
                'warnings': len(self.warnings),
                'info_items': len(self.audit_results),
                'total_items': len(self.critical_issues) + len(self.warnings) + len(self.audit_results)
            },
            'critical_issues': self.critical_issues,
            'warnings': self.warnings,
            'audit_results': self.audit_results,
            'recommendations': self._generate_recommendations()
        }
        
        # Store report in cache for dashboard access
        cache.set('security_audit_report', report, 3600)  # 1 hour
        
        return report
    
    def _generate_recommendations(self):
        """
        Generate priority-ordered recommendations
        """
        all_issues = self.critical_issues + self.warnings
        
        # Group by category
        categories = {}
        for issue in all_issues:
            category = issue['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(issue)
        
        recommendations = []
        
        # Critical issues first
        critical_recommendations = [
            issue['recommendation'] for issue in self.critical_issues
        ]
        
        # Then high-priority warnings
        high_priority_warnings = [
            issue['recommendation'] for issue in self.warnings
            if issue['severity'] in ['HIGH', 'MEDIUM']
        ]
        
        recommendations.extend(critical_recommendations)
        recommendations.extend(high_priority_warnings)
        
        return recommendations[:10]  # Top 10 recommendations


def run_security_audit():
    """
    Convenience function to run security audit
    """
    auditor = SecurityAuditor()
    return auditor.run_full_audit()


def get_security_score():
    """
    Calculate overall security score based on audit results
    """
    # Get latest audit report
    report = cache.get('security_audit_report')
    if not report:
        # Run audit if no recent report
        report = run_security_audit()
    
    critical_count = report['summary']['critical_issues']
    warning_count = report['summary']['warnings']
    
    # Calculate score (100 - deductions)
    score = 100
    score -= critical_count * 20  # 20 points per critical issue
    score -= warning_count * 5    # 5 points per warning
    
    # Minimum score is 0
    score = max(0, score)
    
    return {
        'score': score,
        'grade': _get_security_grade(score),
        'critical_issues': critical_count,
        'warnings': warning_count,
        'last_audit': report['audit_timestamp']
    }


def _get_security_grade(score):
    """
    Convert security score to letter grade
    """
    if score >= 90:
        return 'A'
    elif score >= 80:
        return 'B'
    elif score >= 70:
        return 'C'
    elif score >= 60:
        return 'D'
    else:
        return 'F'