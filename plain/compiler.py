"""Compiler that converts .pln files to Python code."""

import ast
from pathlib import Path
from typing import Optional, Tuple
from .enhanced_transpiler import EnhancedTranspiler


class Compiler:
    """Compiles .pln files to Python code using enhanced transpilation."""
    
    def __init__(self, transpiler=None):
        """Initialize the compiler.
        
        Args:
            transpiler: Transpiler instance (creates enhanced one if not provided)
        """
        self.transpiler = transpiler or EnhancedTranspiler()
    
    def read_pl_file(self, file_path: str) -> str:
        """Read a .pln file and return its contents.
        
        Args:
            file_path: Path to the .pln file
            
        Returns:
            File contents as string
            
        Raises:
            FileNotFoundError: If file doesn't exist
            IOError: If file cannot be read
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not path.suffix == ".pln":
            raise ValueError(f"File must have .pln extension: {file_path}")
        
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    
    def validate_python(self, code: str) -> Tuple[bool, Optional[str]]:
        """Validate Python code syntax.
        
        Args:
            code: Python code to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            ast.parse(code)
            return (True, None)
        except SyntaxError as e:
            error_msg = f"Syntax error at line {e.lineno}: {e.msg}"
            if e.text:
                error_msg += f"\n  {e.text.strip()}"
            return (False, error_msg)
        except Exception as e:
            return (False, f"Validation error: {str(e)}")
    
    def compile(self, file_path: str, validate: bool = True) -> str:
        """Compile a .pln file to Python code.
        
        Args:
            file_path: Path to the .pln file
            validate: Whether to validate the generated Python code
            
        Returns:
            Generated Python code as string
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If generated code is invalid
            Exception: If compilation fails
        """
        plain_text = self.read_pl_file(file_path)
        
        if not plain_text.strip():
            raise ValueError(f"File is empty: {file_path}")
        
        python_code = self.transpiler.transpile(plain_text)
        
        if validate:
            is_valid, error_msg = self.validate_python(python_code)
            if not is_valid:
                raise ValueError(f"Generated Python code is invalid:\n{error_msg}\n\nGenerated code:\n{python_code}")
        
        return python_code
    
    def compile_to_file(self, file_path: str, output_path: str, validate: bool = True) -> str:
        """Compile a .pln file and save to a .py file.
        
        Args:
            file_path: Path to the .pln file
            output_path: Path to save the .py file
            validate: Whether to validate the generated Python code
            
        Returns:
            Path to the generated .py file
            
        Raises:
            FileNotFoundError: If input file doesn't exist
            ValueError: If generated code is invalid
            IOError: If output file cannot be written
            Exception: If compilation fails
        """
        python_code = self.compile(file_path, validate=validate)
        
        output = Path(output_path)
        try:
            output.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise IOError(f"Cannot create output directory: {str(e)}")
        
        try:
            with open(output, "w", encoding="utf-8") as f:
                f.write(python_code)
        except Exception as e:
            raise IOError(f"Cannot write to output file {output_path}: {str(e)}")
        
        return str(output)

