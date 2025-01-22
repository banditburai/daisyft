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
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
    
    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals"""
        if self.done:  # Prevent multiple shutdowns
            return
        self.done = True
        console.print("\n[yellow]Shutting down...[/yellow]")
        self.cleanup()
        sys.exit(0)
    
    def _setup_process_group(self, process):
        """Set up process group for better control"""
        if hasattr(process, 'pid'):
            try:
                os.setpgrp()  # Create new process group
            except Exception:
                pass  # Might fail on Windows
    
    def add_process(self, process):
        """Add a process to manage"""
        self._setup_process_group(process)
        self.processes.append(process)
    
    def cleanup(self):
        """Clean up all processes"""
        for process in reversed(self.processes):  # Reverse order for child processes
            try:
                # Try to get process group ID
                try:
                    pgid = os.getpgid(process.pid)
                except:
                    pgid = None
                
                # Send interrupt signal first for graceful shutdown
                if pgid and pgid != os.getpgid(0):  # Don't kill our own process group
                    os.killpg(pgid, signal.SIGINT)
                else:
                    process.send_signal(signal.SIGINT)
                
                # Wait briefly for graceful shutdown
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    # Force kill if taking too long
                    if pgid and pgid != os.getpgid(0):
                        os.killpg(pgid, signal.SIGKILL)
                    else:
                        process.kill()
                    process.wait(timeout=1)
            except:
                pass  # Process might already be dead
        
        # Clear process list
        self.processes.clear()
        
        # Brief pause to ensure all processes are cleaned up
        time.sleep(0.2) 