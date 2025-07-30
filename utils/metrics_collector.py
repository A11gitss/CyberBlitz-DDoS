import time
from datetime import datetime
import json
import csv
from pathlib import Path
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
import threading
import queue
import logging

logger = logging.getLogger(__name__)

@dataclass
class AttackMetrics:
    timestamp: float
    requests_per_second: float
    latency: float
    success_rate: float
    bandwidth: float
    errors: Dict[str, int]
    response_codes: Dict[str, int]

class MetricsCollector:
    def __init__(self, attack_name: str, target: str):
        self.attack_name = attack_name
        self.target = target
        self.start_time = time.time()
        self.metrics: List[AttackMetrics] = []
        self.metrics_queue = queue.Queue()
        self.is_collecting = True
        self._collector_thread = threading.Thread(target=self._collect_metrics)
        self._collector_thread.daemon = True
        self._collector_thread.start()

    def _collect_metrics(self):
        while self.is_collecting or not self.metrics_queue.empty():
            try:
                metric = self.metrics_queue.get(timeout=1)
                self.metrics.append(metric)
                self.metrics_queue.task_done()
            except queue.Empty:
                if not self.is_collecting:
                    break
                continue

    def add_metric(self, **kwargs):
        metric = AttackMetrics(
            timestamp=time.time(),
            **kwargs
        )
        self.metrics_queue.put(metric)

    def stop_collecting(self):
        self.is_collecting = False
        # Wait for the queue to be processed
        self.metrics_queue.join()
        self._collector_thread.join()

    def export_metrics(self, format: str = 'json') -> str:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"logs/metrics_{self.attack_name}_{timestamp}.{format}"
        Path(filename).parent.mkdir(exist_ok=True)

        # Drain the queue one last time
        while not self.metrics_queue.empty():
            try:
                self.metrics.append(self.metrics_queue.get_nowait())
            except queue.Empty:
                break

        if not self.metrics:
            logger.warning(f"No metrics collected for attack {self.attack_name}. Exporting empty file.")
            with open(filename, 'w') as f:
                if format == 'json':
                    f.write("[]")
                elif format == 'html':
                    f.write("<html><body>No metrics collected.</body></html>")
            return filename

        if format == 'json':
            with open(filename, 'w') as f:
                json.dump([asdict(m) for m in self.metrics], f, indent=2)
        elif format == 'csv':
            with open(filename, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=asdict(self.metrics[0]).keys())
                writer.writeheader()
                writer.writerows([asdict(m) for m in self.metrics])
        elif format == 'html':
            self._generate_html_report(filename)

        return filename

    def _generate_html_report(self, filename: str):
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        timestamps = [(m.timestamp - self.start_time) for m in self.metrics]
        
        # Latency Graph on primary Y-axis
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=[m.latency for m in self.metrics],
            name="Latency (ms)",
            line=dict(color='blue')
        ), secondary_y=False)
        
        # RPS Graph on secondary Y-axis
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=[m.requests_per_second for m in self.metrics],
            name="Requests/sec",
            line=dict(color='green')
        ), secondary_y=True)
        
        # Success Rate on secondary Y-axis (since its range is 0-100)
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=[m.success_rate for m in self.metrics],
            name="Success Rate (%)",
            line=dict(color='red')
        ), secondary_y=True)

        fig.update_layout(
            title_text=f"<b>Attack Metrics: {self.attack_name} on {self.target}</b>",
            template="plotly_white"
        )

        # Set axis titles
        fig.update_xaxes(title_text="Time (seconds)")
        fig.update_yaxes(title_text="<b>Latency (ms)</b>", secondary_y=False)
        fig.update_yaxes(title_text="<b>RPS & Success Rate</b>", secondary_y=True)

        fig.write_html(filename)