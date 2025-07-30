import json
import csv
import os
from datetime import datetime

def export_metrics_to_file(metrics, format_type, output_dir='logs'):
    """Export metrics to a file in the specified format."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if format_type.lower() == 'json':
        filename = os.path.join(output_dir, f'metrics_{timestamp}.json')
        with open(filename, 'w') as f:
            json.dump(metrics, f, indent=2)
            
    elif format_type.lower() == 'csv':
        filename = os.path.join(output_dir, f'metrics_{timestamp}.csv')
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Metric', 'Value'])
            for key, value in metrics.items():
                writer.writerow([key, value])
                
    elif format_type.lower() == 'html':
        filename = os.path.join(output_dir, f'metrics_{timestamp}.html')
        html_content = """
        <html>
        <head>
            <title>Attack Metrics Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #4FC3F7; color: white; }
                tr:nth-child(even) { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <h1>Attack Metrics Report</h1>
            <p>Generated: {}</p>
            <table>
                <tr><th>Metric</th><th>Value</th></tr>
                {}
            </table>
        </body>
        </html>
        """.format(
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            ''.join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in metrics.items())
        )
        with open(filename, 'w') as f:
            f.write(html_content)
            
    return filename
