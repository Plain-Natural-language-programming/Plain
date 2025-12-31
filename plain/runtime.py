"""Runtime executor for generated Python code."""

import sys
import io
from contextlib import redirect_stdout, redirect_stderr
from typing import Tuple, Optional


class Runtime:
    """Executes Python code safely and captures output."""
    
    def __init__(self):
        self._reset_namespace()
    
    def execute(self, code: str, capture_output: bool = True) -> Tuple[Optional[str], Optional[str], Optional[Exception]]:
        """Execute Python code and capture output.
        
        Args:
            code: Python code to execute
            capture_output: Whether to capture stdout/stderr
            
        Returns:
            Tuple of (stdout, stderr, exception)
        """
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        try:
            if capture_output:
                with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                    exec(code, self.globals)
            else:
                exec(code, self.globals)
            
            stdout = stdout_capture.getvalue() if capture_output else None
            stderr = stderr_capture.getvalue() if capture_output else None
            return (stdout, stderr, None)
            
        except Exception as e:
            stdout = stdout_capture.getvalue() if capture_output else None
            stderr = stderr_capture.getvalue() if capture_output else None
            return (stdout, stderr, e)
    
    def execute_file(self, code: str) -> Tuple[Optional[str], Optional[str], Optional[Exception]]:
        """Execute code as if it were a file (prints output automatically)."""
        return self.execute(code, capture_output=True)
    
    def reset(self):
        """Reset the execution environment."""
        self._reset_namespace()

    def _reset_namespace(self):
        """Initialize globals/locals with a predictable module context."""
        self.globals = {"__name__": "__main__"}
        self.locals = self.globals



