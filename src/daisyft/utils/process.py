import signal
import subprocess
import os
from ..utils.console import console

class ProcessManager:
    """Manage multiple subprocesses cleanly"""
    def __init__(self):
        self.processes = []
        self._setup_signal_handlers()
        self.done = False
    
    def _setup_signal_handlers(self):
        """Set up signal handlers for clean shutdown"""
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
    
    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals"""
        if self.done:  # Prevent multiple shutdowns
            return
        self.done = True
        console.print("\n[yellow]Gracefully shutting down...[/yellow]")
        self.cleanup()
        console.print("[green]✓[/green] Done")
        os._exit(0)
    
    def add_process(self, process):
        """Add a process to manage"""
        self.processes.append(process)
    
    def cleanup(self):
        """Clean up all processes"""
        for process in reversed(self.processes):
            try:
                if process.poll() is not None:  # Skip if process already ended
                    continue
                    
                # Send interrupt signal
                if os.name != 'nt':
                    os.killpg(os.getpgid(process.pid), signal.SIGINT)
                
                # Wait for graceful shutdown
                try:
                    process.wait(timeout=0.5)
                except subprocess.TimeoutExpired:
                    # Force kill if timeout
                    if os.name != 'nt':
                        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                    process.wait(timeout=1)
            except:
                pass  # Process might already be dead
        
        self.processes.clear()
