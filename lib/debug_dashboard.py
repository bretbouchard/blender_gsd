"""
Debug Dashboard

A debugging and monitoring dashboard for Blender GSD projects.
Provides real-time visibility into task execution, renders, and system state.

Usage:
    blender-gsd dashboard
    blender-gsd dashboard --port 8080
"""

from __future__ import annotations
import json
import os
import sys
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import subprocess


class DashboardStatus(Enum):
    """Dashboard status."""
    IDLE = "idle"
    RUNNING = "running"
    ERROR = "error"
    COMPLETE = "complete"


@dataclass
class TaskStatus:
    """Status of a task execution."""
    task_id: str
    name: str
    status: str  # pending, running, complete, failed
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration: Optional[float] = None
    progress: float = 0.0
    error: Optional[str] = None
    output_files: List[str] = field(default_factory=list)


@dataclass
class RenderJob:
    """Render job status."""
    job_id: str
    scene: str
    output_path: str
    frame_start: int
    frame_end: int
    current_frame: int = 0
    status: str = "pending"
    samples: int = 0
    time_remaining: Optional[float] = None


@dataclass
class SystemMetrics:
    """System metrics."""
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    gpu_percent: Optional[float] = None
    gpu_memory: Optional[float] = None
    disk_free_gb: float = 0.0
    blender_instances: int = 0


class DebugDashboard:
    """
    Debug dashboard for monitoring Blender GSD operations.

    Provides a web-based dashboard for real-time monitoring of:
    - Task execution status
    - Render job progress
    - System metrics
    - Error logs
    - Output file tracking
    """

    def __init__(
        self,
        project_path: Optional[Path] = None,
        port: int = 5000,
        auto_open: bool = True
    ):
        """
        Initialize debug dashboard.

        Args:
            project_path: Path to project root
            port: Port to serve dashboard on
            auto_open: Whether to open browser automatically
        """
        self.project_path = Path(project_path) if project_path else Path.cwd()
        self.port = port
        self.auto_open = auto_open
        self.status = DashboardStatus.IDLE

        # State tracking
        self.tasks: Dict[str, TaskStatus] = {}
        self.renders: Dict[str, RenderJob] = {}
        self.metrics = SystemMetrics()
        self.logs: List[Dict[str, Any]] = []
        self.errors: List[Dict[str, Any]] = []

        # Callbacks
        self._on_task_update: Optional[Callable] = None
        self._on_render_update: Optional[Callable] = None

        # Server
        self._server = None
        self._running = False

    def start(self) -> None:
        """Start the dashboard server."""
        self.status = DashboardStatus.RUNNING
        self._running = True

        # Start metrics collection thread
        metrics_thread = threading.Thread(target=self._collect_metrics, daemon=True)
        metrics_thread.start()

        # Start server (simple HTTP server)
        try:
            from http.server import HTTPServer, SimpleHTTPRequestHandler

            class DashboardHandler(SimpleHTTPRequestHandler):
                """Custom handler for dashboard."""

                dashboard = self

                def do_GET(self):
                    """Handle GET requests."""
                    if self.path == "/api/status":
                        self._send_json(self.dashboard.get_status())
                    elif self.path == "/api/tasks":
                        self._send_json(self.dashboard.get_tasks())
                    elif self.path == "/api/renders":
                        self._send_json(self.dashboard.get_renders())
                    elif self.path == "/api/metrics":
                        self._send_json(self.dashboard.get_metrics())
                    elif self.path == "/api/logs":
                        self._send_json(self.dashboard.get_logs())
                    elif self.path == "/api/errors":
                        self._send_json(self.dashboard.get_errors())
                    elif self.path == "/" or self.path == "/index.html":
                        self._send_html(self.dashboard._get_dashboard_html())
                    else:
                        super().do_GET()

                def _send_json(self, data):
                    """Send JSON response."""
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(data).encode())

                def _send_html(self, html):
                    """Send HTML response."""
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.end_headers()
                    self.wfile.write(html.encode())

                def log_message(self, format, *args):
                    """Suppress default logging."""
                    pass

            self._server = HTTPServer(("localhost", self.port), DashboardHandler)

            print(f"Dashboard running at http://localhost:{self.port}")

            if self.auto_open:
                import webbrowser
                webbrowser.open(f"http://localhost:{self.port}")

            self._server.serve_forever()

        except ImportError:
            print("HTTP server not available. Running in headless mode.")
            while self._running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self) -> None:
        """Stop the dashboard server."""
        self._running = False
        self.status = DashboardStatus.IDLE
        if self._server:
            self._server.shutdown()

    def register_task(self, task_id: str, name: str) -> None:
        """Register a new task for tracking."""
        self.tasks[task_id] = TaskStatus(
            task_id=task_id,
            name=name,
            status="pending"
        )
        self._log("info", f"Task registered: {name}")

    def update_task(
        self,
        task_id: str,
        status: Optional[str] = None,
        progress: Optional[float] = None,
        error: Optional[str] = None,
        output_files: Optional[List[str]] = None
    ) -> None:
        """Update task status."""
        if task_id not in self.tasks:
            return

        task = self.tasks[task_id]

        if status:
            task.status = status
            if status == "running":
                task.start_time = datetime.now().isoformat()
            elif status in ("complete", "failed"):
                task.end_time = datetime.now().isoformat()
                if task.start_time:
                    start = datetime.fromisoformat(task.start_time)
                    end = datetime.fromisoformat(task.end_time)
                    task.duration = (end - start).total_seconds()

        if progress is not None:
            task.progress = progress

        if error:
            task.error = error
            self._log("error", f"Task {task.name} error: {error}")

        if output_files:
            task.output_files = output_files

        if self._on_task_update:
            self._on_task_update(task)

    def register_render(
        self,
        job_id: str,
        scene: str,
        output_path: str,
        frame_start: int,
        frame_end: int,
        samples: int = 128
    ) -> None:
        """Register a new render job."""
        self.renders[job_id] = RenderJob(
            job_id=job_id,
            scene=scene,
            output_path=output_path,
            frame_start=frame_start,
            frame_end=frame_end,
            samples=samples
        )
        self._log("info", f"Render registered: {scene}")

    def update_render(
        self,
        job_id: str,
        current_frame: Optional[int] = None,
        status: Optional[str] = None,
        time_remaining: Optional[float] = None
    ) -> None:
        """Update render job status."""
        if job_id not in self.renders:
            return

        render = self.renders[job_id]

        if current_frame is not None:
            render.current_frame = current_frame

        if status:
            render.status = status

        if time_remaining is not None:
            render.time_remaining = time_remaining

        if self._on_render_update:
            self._on_render_update(render)

    def get_status(self) -> Dict[str, Any]:
        """Get overall dashboard status."""
        return {
            "status": self.status.value,
            "project_path": str(self.project_path),
            "total_tasks": len(self.tasks),
            "running_tasks": len([t for t in self.tasks.values() if t.status == "running"]),
            "complete_tasks": len([t for t in self.tasks.values() if t.status == "complete"]),
            "failed_tasks": len([t for t in self.tasks.values() if t.status == "failed"]),
            "active_renders": len([r for r in self.renders.values() if r.status == "running"]),
            "error_count": len(self.errors),
            "timestamp": datetime.now().isoformat()
        }

    def get_tasks(self) -> List[Dict[str, Any]]:
        """Get all task statuses."""
        return [asdict(t) for t in self.tasks.values()]

    def get_renders(self) -> List[Dict[str, Any]]:
        """Get all render job statuses."""
        return [asdict(r) for r in self.renders.values()]

    def get_metrics(self) -> Dict[str, Any]:
        """Get current system metrics."""
        return asdict(self.metrics)

    def get_logs(self) -> List[Dict[str, Any]]:
        """Get recent logs."""
        return self.logs[-100:]  # Last 100 logs

    def get_errors(self) -> List[Dict[str, Any]]:
        """Get error logs."""
        return self.errors

    def _log(self, level: str, message: str) -> None:
        """Add a log entry."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message
        }
        self.logs.append(entry)

        if level == "error":
            self.errors.append(entry)

    def _collect_metrics(self) -> None:
        """Collect system metrics in background."""
        while self._running:
            try:
                # CPU and memory
                try:
                    import psutil
                    self.metrics.cpu_percent = psutil.cpu_percent(interval=1)
                    self.metrics.memory_percent = psutil.virtual_memory().percent
                    self.metrics.disk_free_gb = psutil.disk_usage('/').free / (1024**3)
                except ImportError:
                    pass

                # Blender instances
                try:
                    result = subprocess.run(
                        ["pgrep", "-f", "blender"],
                        capture_output=True,
                        text=True
                    )
                    self.metrics.blender_instances = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
                except Exception:
                    pass

            except Exception as e:
                self._log("error", f"Metrics collection error: {e}")

            time.sleep(5)  # Update every 5 seconds

    def _get_dashboard_html(self) -> str:
        """Get dashboard HTML."""
        return """<!DOCTYPE html>
<html>
<head>
    <title>Blender GSD Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a2e;
            color: #eee;
            padding: 20px;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 1px solid #333;
        }
        .header h1 { color: #0f0; }
        .status { padding: 5px 15px; border-radius: 15px; font-size: 12px; }
        .status.running { background: #0f0; color: #000; }
        .status.idle { background: #666; }
        .status.error { background: #f00; }
        .status.complete { background: #00f; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .card {
            background: #16213e;
            border-radius: 10px;
            padding: 20px;
        }
        .card h2 {
            font-size: 14px;
            text-transform: uppercase;
            color: #888;
            margin-bottom: 15px;
        }
        .metric { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #333; }
        .metric-label { color: #888; }
        .metric-value { font-weight: bold; }
        .progress-bar {
            height: 8px;
            background: #333;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 5px;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #0f0, #00f);
            transition: width 0.3s;
        }
        .task-item { padding: 10px 0; border-bottom: 1px solid #333; }
        .task-name { font-weight: bold; margin-bottom: 5px; }
        .task-status { font-size: 12px; }
        .log { font-family: monospace; font-size: 12px; padding: 5px 0; }
        .log.error { color: #f66; }
        .log.info { color: #6f6; }
        .log.warn { color: #ff6; }
        .refresh-btn {
            background: #0f0;
            color: #000;
            border: none;
            padding: 8px 16px;
            border-radius: 5px;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Blender GSD Dashboard</h1>
        <div>
            <span class="status" id="main-status">Loading...</span>
            <button class="refresh-btn" onclick="refresh()">Refresh</button>
        </div>
    </div>

    <div class="grid">
        <div class="card">
            <h2>System Metrics</h2>
            <div id="metrics">
                <div class="metric"><span class="metric-label">CPU</span><span class="metric-value" id="cpu">-</span></div>
                <div class="metric"><span class="metric-label">Memory</span><span class="metric-value" id="memory">-</span></div>
                <div class="metric"><span class="metric-label">Disk Free</span><span class="metric-value" id="disk">-</span></div>
                <div class="metric"><span class="metric-label">Blender Instances</span><span class="metric-value" id="blender">-</span></div>
            </div>
        </div>

        <div class="card">
            <h2>Tasks</h2>
            <div id="tasks">
                <p style="color: #666;">No tasks running</p>
            </div>
        </div>

        <div class="card">
            <h2>Renders</h2>
            <div id="renders">
                <p style="color: #666;">No renders active</p>
            </div>
        </div>

        <div class="card">
            <h2>Recent Logs</h2>
            <div id="logs">
                <p style="color: #666;">No logs</p>
            </div>
        </div>
    </div>

    <script>
        async function fetchAPI(endpoint) {
            try {
                const response = await fetch(endpoint);
                return await response.json();
            } catch (e) {
                console.error('API error:', e);
                return null;
            }
        }

        async function refresh() {
            // Status
            const status = await fetchAPI('/api/status');
            if (status) {
                document.getElementById('main-status').textContent = status.status.toUpperCase();
                document.getElementById('main-status').className = 'status ' + status.status;
            }

            // Metrics
            const metrics = await fetchAPI('/api/metrics');
            if (metrics) {
                document.getElementById('cpu').textContent = metrics.cpu_percent.toFixed(1) + '%';
                document.getElementById('memory').textContent = metrics.memory_percent.toFixed(1) + '%';
                document.getElementById('disk').textContent = metrics.disk_free_gb.toFixed(1) + ' GB';
                document.getElementById('blender').textContent = metrics.blender_instances;
            }

            // Tasks
            const tasks = await fetchAPI('/api/tasks');
            if (tasks && tasks.length > 0) {
                const tasksHTML = tasks.map(t => `
                    <div class="task-item">
                        <div class="task-name">${t.name}</div>
                        <div class="task-status">${t.status} ${t.progress > 0 ? '(' + (t.progress * 100).toFixed(0) + '%)' : ''}</div>
                        <div class="progress-bar"><div class="progress-fill" style="width: ${t.progress * 100}%"></div></div>
                    </div>
                `).join('');
                document.getElementById('tasks').innerHTML = tasksHTML;
            }

            // Renders
            const renders = await fetchAPI('/api/renders');
            if (renders && renders.length > 0) {
                const rendersHTML = renders.map(r => {
                    const progress = (r.current_frame - r.frame_start) / (r.frame_end - r.frame_start);
                    return `
                        <div class="task-item">
                            <div class="task-name">${r.scene}</div>
                            <div class="task-status">Frame ${r.current_frame}/${r.frame_end} (${(progress * 100).toFixed(0)}%)</div>
                            <div class="progress-bar"><div class="progress-fill" style="width: ${progress * 100}%"></div></div>
                        </div>
                    `;
                }).join('');
                document.getElementById('renders').innerHTML = rendersHTML;
            }

            // Logs
            const logs = await fetchAPI('/api/logs');
            if (logs && logs.length > 0) {
                const logsHTML = logs.slice(-10).map(l => `
                    <div class="log ${l.level}">[${l.timestamp.split('T')[1].split('.')[0]}] ${l.message}</div>
                `).join('');
                document.getElementById('logs').innerHTML = logsHTML;
            }
        }

        // Initial load
        refresh();

        // Auto-refresh every 2 seconds
        setInterval(refresh, 2000);
    </script>
</body>
</html>"""


def start_dashboard(
    project_path: Optional[str] = None,
    port: int = 5000,
    auto_open: bool = True
) -> DebugDashboard:
    """
    Convenience function to start a dashboard.

    Args:
        project_path: Path to project
        port: Port to serve on
        auto_open: Open browser automatically

    Returns:
        Dashboard instance
    """
    dashboard = DebugDashboard(
        project_path=Path(project_path) if project_path else None,
        port=port,
        auto_open=auto_open
    )

    # Run in background thread
    import threading
    thread = threading.Thread(target=dashboard.start, daemon=True)
    thread.start()

    return dashboard


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Blender GSD Debug Dashboard")
    parser.add_argument("--port", type=int, default=5000, help="Port to serve on")
    parser.add_argument("--no-open", action="store_true", help="Don't open browser")
    parser.add_argument("project_path", nargs="?", default=".", help="Project path")

    args = parser.parse_args()

    dashboard = DebugDashboard(
        project_path=Path(args.project_path),
        port=args.port,
        auto_open=not args.no_open
    )
    dashboard.start()
