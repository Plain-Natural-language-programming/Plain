"""Runtime executor for generated Python code."""

import sys
import io
import builtins
import threading
import traceback
from contextlib import redirect_stdout, redirect_stderr
from typing import Dict, List, Optional, Tuple


class Runtime:
    """Executes Python code safely and captures output."""
    
    def __init__(self):
        self._reset_namespace()
        self._safe_builtins = self._build_safe_builtins()
        self.last_error: Optional[str] = None

    def _build_safe_builtins(self) -> Dict[str, object]:
        """Create a restricted set of builtins for safe execution."""
        allowed = [
            "abs",
            "all",
            "any",
            "bool",
            "dict",
            "enumerate",
            "float",
            "int",
            "len",
            "list",
            "max",
            "min",
            "print",
            "range",
            "round",
            "str",
            "sum",
            "zip",
            "sorted",
            "set",
            "tuple",
            "Exception",
            "__build_class__",
        ]
        safe: Dict[str, object] = {name: getattr(builtins, name) for name in allowed if hasattr(builtins, name)}

        def _blocked_import(*_args, **_kwargs):
            raise ImportError("Imports are disabled in safe mode")

        safe["__import__"] = _blocked_import
        return safe

    def _get_exec_globals(self, safe_mode: bool) -> Dict[str, object]:
        """Return the globals mapping to use for execution."""
        if not safe_mode:
            return self.globals
        exec_globals = dict(self.globals)
        exec_globals["__builtins__"] = self._safe_builtins
        return exec_globals

    def _format_exception(
        self,
        exception: Exception,
        filename: str,
        line_mapping: Optional[Dict[int, object]],
        source_lines: Optional[List[str]],
    ) -> str:
        frames = traceback.extract_tb(exception.__traceback__) if exception.__traceback__ else []
        target_frame = None
        for frame in reversed(frames):
            if frame.filename == filename:
                target_frame = frame
                break
        if target_frame is None and frames:
            target_frame = frames[-1]

        py_line = target_frame.lineno if target_frame else None
        source_line = None
        if line_mapping and py_line in line_mapping:
            source_line = line_mapping.get(py_line)

        original_line_no = getattr(source_line, "line_no", None)
        original_text = None
        if source_line is not None:
            indent = getattr(source_line, "indent", 0)
            content = getattr(source_line, "content", "")
            original_text = (" " * indent) + content
        elif not line_mapping and source_lines and py_line and 1 <= py_line <= len(source_lines):
            original_line_no = py_line
            original_text = source_lines[py_line - 1]

        parts = []
        location = filename or "<string>"
        if original_line_no is not None:
            parts.append(f"{location}:{original_line_no}")
        elif py_line is not None:
            parts.append(f"{location} (python line {py_line})")
        else:
            parts.append(location)

        if original_text:
            parts.append(f"Plain: {original_text}")

        parts.append(f"{type(exception).__name__}: {exception}")
        return "\n".join(parts)
    
    def execute(
        self,
        code: str,
        capture_output: bool = True,
        filename: Optional[str] = None,
        line_mapping: Optional[Dict[int, object]] = None,
        source_lines: Optional[List[str]] = None,
        timeout: Optional[float] = None,
        safe_mode: bool = False,
    ) -> Tuple[Optional[str], Optional[str], Optional[Exception]]:
        """Execute Python code and capture output."""
        self.last_error = None
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        exec_globals = self._get_exec_globals(safe_mode)
        exec_filename = filename or "<string>"
        exception: Optional[Exception] = None

        try:
            code_obj = compile(code, exec_filename, "exec")
        except Exception as exc:
            code_obj = None
            exception = exc

        def runner():
            nonlocal exception
            if code_obj is None:
                return
            try:
                if capture_output:
                    with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                        exec(code_obj, exec_globals)
                else:
                    exec(code_obj, exec_globals)
            except Exception as exc:
                exception = exc

        if timeout is not None:
            thread = threading.Thread(target=runner, daemon=True)
            thread.start()
            thread.join(timeout)
            if thread.is_alive():
                exception = TimeoutError(f"Execution exceeded timeout of {timeout} seconds")
                self.reset()
        else:
            runner()

        stdout = stdout_capture.getvalue() if capture_output else None
        stderr = stderr_capture.getvalue() if capture_output else None

        if exception:
            formatted = self._format_exception(exception, exec_filename, line_mapping, source_lines)
            self.last_error = formatted
            if capture_output:
                if formatted:
                    if stderr and not stderr.endswith("\n"):
                        stderr_capture.write("\n")
                    stderr_capture.write(formatted)
                    if not formatted.endswith("\n"):
                        stderr_capture.write("\n")
                    stderr = stderr_capture.getvalue()
                stdout = stdout_capture.getvalue()
            else:
                if formatted:
                    sys.stderr.write(formatted)
                    if not formatted.endswith("\n"):
                        sys.stderr.write("\n")
            return (stdout, stderr, exception)

        return (
            stdout_capture.getvalue() if capture_output else None,
            stderr_capture.getvalue() if capture_output else None,
            None,
        )

    def execute_file(
        self,
        code: str,
        filename: Optional[str] = None,
        line_mapping: Optional[Dict[int, object]] = None,
        source_lines: Optional[List[str]] = None,
        timeout: Optional[float] = None,
        safe_mode: bool = False,
    ) -> Tuple[Optional[str], Optional[str], Optional[Exception]]:
        """Execute code as if it were a file (prints output automatically)."""
        return self.execute(
            code,
            capture_output=True,
            filename=filename,
            line_mapping=line_mapping,
            source_lines=source_lines,
            timeout=timeout,
            safe_mode=safe_mode,
        )
    
    def reset(self):
        """Reset the execution environment."""
        self._reset_namespace()

    def _reset_namespace(self):
        """Initialize globals/locals with a predictable module context."""
        self.globals = {"__name__": "__main__"}
        self.locals = self.globals



