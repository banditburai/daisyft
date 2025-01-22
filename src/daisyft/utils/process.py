import signal
import sys
import subprocess
import os
import time
from rich.console import Console

console = Console()

class ProcessManager:
    """Manage multiple subprocesses cleanly"""
    def __init__(self):
        self.processes = []
        self._setup_signal_handlers()
        self.done = False
    
    def _setup_signal_handlers(self):
        """Set up signal handlers for clean shutdown"""
        # Handle both SIGINT (Ctrl+C) and SIGTERM
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
    
    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals"""
        if self.done:  # Prevent multiple shutdowns
            return
        self.done = True
        console.print("\n[yellow]Shutting down...[/yellow]")
        self.cleanup()
        # Print a completion message before exiting
        console.print("[green]✓[/green] Done")
        os._exit(0)
    
    def add_process(self, process):
        """Add a process to manage"""
        self.processes.append(process)
    
    def cleanup(self):
        """Clean up all processes"""
        for process in reversed(self.processes):  # Reverse order for child processes
            try:
                if process.poll() is None:  # Only if process is still running
                    # Try to get process group
                    try:
                        if os.name != 'nt':
                            os.killpg(os.getpgid(process.pid), signal.SIGINT)
                        else:
                            process.send_signal(signal.CTRL_C_EVENT)
                    except:
                        # Fallback to regular termination
                        process.terminate()
                    
                    # Wait briefly for graceful shutdown
                    try:
                        process.wait(timeout=0.5)
                    except subprocess.TimeoutExpired:
                        # Force kill if taking too long
                        if os.name != 'nt':
                            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                        else:
                            process.kill()
                        process.wait(timeout=1)
            except:
                pass  # Process might already be dead
        
        # Clear process list
        self.processes.clear()
        
        # Brief pause to ensure all processes are cleaned up
        # time.sleep(0.2) 