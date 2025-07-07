'''python
import psutil
import os
import signal

def kill_process(pid):
    """
    Terminates a process by its PID, first gracefully (SIGTERM)
    and then forcefully (SIGKILL) if necessary.
    """
    try:
        proc = psutil.Process(pid)
        # First, try to terminate gracefully
        proc.terminate() 
        print(f"Sent SIGTERM to PID {pid}")
        try:
            # Wait for a moment to see if it exits
            proc.wait(timeout=2)
            print(f"Process {pid} terminated gracefully.")
            return True
        except psutil.TimeoutExpired:
            # If it's still alive, use the big hammer
            print(f"Process {pid} did not terminate, sending SIGKILL.")
            proc.kill()
            proc.wait()
            print(f"Process {pid} killed forcefully.")
            return True
    except psutil.NoSuchProcess:
        print(f"Error: Process {pid} not found.")
        return False
    except Exception as e:
        print(f"An error occurred while trying to kill process {pid}: {e}")
        return False
