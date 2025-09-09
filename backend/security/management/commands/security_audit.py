"""
Django management command to run security audit
"""

from django.core.management.base import BaseCommand
from security.audit import run_security_audit, get_security_score
import json


class Command(BaseCommand):
    help = 'Run security audit on the application'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--format',
            choices=['json', 'text'],
            default='text',
            help='Output format (default: text)'
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output file path (optional)'
        )
        parser.add_argument(
            '--score-only',
            action='store_true',
            help='Show only the security score'
        )
    
    def handle(self, *args, **options):
        """Run the security audit"""
        
        if options['score_only']:
            score_info = get_security_score()
            if options['format'] == 'json':
                output = json.dumps(score_info, indent=2)
            else:
                output = f"Security Score: {score_info['score']}/100 (Grade: {score_info['grade']})\n"
                output += f"Critical Issues: {score_info['critical_issues']}\n"
                output += f"Warnings: {score_info['warnings']}\n"
                output += f"Last Audit: {score_info['last_audit']}\n"
        else:
            # Run full audit
            self.stdout.write("Running security audit...")
            report = run_security_audit()
            
            if options['format'] == 'json':
                output = json.dumps(report, indent=2)
            else:
                output = self._format_text_report(report)
        
        # Output results
        if options['output']:
            with open(options['output'], 'w') as f:
                f.write(output)
            self.stdout.write(
                self.style.SUCCESS(f'Audit report saved to {options["output"]}')
            )
        else:
            self.stdout.write(output)
    
    def _format_text_report(self, report):
        """Format report as readable text"""
        output = []
        
        # Header
        output.append("=" * 60)
        output.append("SECURITY AUDIT REPORT")
        output.append("=" * 60)
        output.append(f"Audit Date: {report['audit_timestamp']}")
        output.append("")
        
        # Summary
        summary = report['summary']
        output.append("SUMMARY")
        output.append("-" * 20)
        output.append(f"Critical Issues: {summary['critical_issues']}")
        output.append(f"Warnings: {summary['warnings']}")
        output.append(f"Total Items: {summary['total_items']}")
        output.append("")
        
        # Critical Issues
        if report['critical_issues']:
            output.append("CRITICAL ISSUES")
            output.append("-" * 20)
            for issue in report['critical_issues']:
                output.append(f"• {issue['issue']} ({issue['category']})")
                output.append(f"  {issue['description']}")
                output.append(f"  → {issue['recommendation']}")
                output.append("")
        
        # Warnings
        if report['warnings']:
            output.append("WARNINGS")
            output.append("-" * 20)
            for warning in report['warnings']:
                output.append(f"• {warning['issue']} ({warning['category']}) - {warning['severity']}")
                output.append(f"  {warning['description']}")
                output.append(f"  → {warning['recommendation']}")
                output.append("")
        
        # Top Recommendations
        if report['recommendations']:
            output.append("TOP RECOMMENDATIONS")
            output.append("-" * 20)
            for i, rec in enumerate(report['recommendations'], 1):
                output.append(f"{i}. {rec}")
            output.append("")
        
        return "\n".join(output)