import signal
import sys
import subprocess
from rich.console import Console

console = Console()

class ProcessManager:
    """Manage multiple subprocesses cleanly"""
    def __init__(self):
        self.processes = []
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """Set up signal handlers for clean shutdown"""
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
    
    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals"""
        console.print("\n[yellow]Shutting down...[/yellow]")
        self.cleanup()
        sys.exit(0)
    
    def add_process(self, process):
        """Add a process to manage"""
        self.processes.append(process)
    
    def cleanup(self):
        """Clean up all processes"""
        for process in self.processes:
            try:
                # Send interrupt signal first for graceful shutdown
                process.send_signal(signal.SIGINT)
                
                # Wait briefly for graceful shutdown
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    # Force kill if taking too long
                    process.kill()
                    process.wait()
            except:
                pass  # Process might already be dead 