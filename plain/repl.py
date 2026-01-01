"""Interactive REPL for Plain language."""

import sys
from typing import Optional
from .enhanced_transpiler import EnhancedTranspiler
from .runtime import Runtime


class REPL:
    """Interactive REPL for testing plain text statements."""
    
    def __init__(self, transpiler=None, verbose: bool = False):
        """Initialize the REPL.
        
        Args:
            transpiler: Transpiler instance (creates enhanced one if not provided)
            verbose: Whether to show generated Python code
        """
        self.transpiler = transpiler or EnhancedTranspiler()
        self.runtime = Runtime()
        self.verbose = verbose
        self.history = []
    
    def _print_banner(self):
        """Print REPL welcome banner."""
        print("Plain Language REPL")
        print("Type your plain text descriptions and they will be converted to Python and executed.")
        print("Type 'exit', 'quit', or 'q' to exit.")
        print("Type 'verbose' to toggle showing generated Python code.")
        print("Type 'reset' to reset the execution environment.")
        print("Type 'history' to see your input history.")
        print("-" * 60)
    
    def _process_command(self, command: str) -> bool:
        """Process special REPL commands.
        
        Args:
            command: The command to process
            
        Returns:
            True if command was handled, False otherwise
        """
        cmd = command.strip().lower()
        
        if cmd in ("exit", "quit", "q"):
            print("Goodbye!")
            return True
        
        if cmd == "verbose":
            self.verbose = not self.verbose
            print(f"Verbose mode: {'ON' if self.verbose else 'OFF'}")
            return True
        
        if cmd == "reset":
            self.runtime.reset()
            print("Execution environment reset.")
            return True
        
        if cmd == "history":
            if self.history:
                print("\nHistory:")
                for i, item in enumerate(self.history[-10:], 1):  # Show last 10
                    print(f"  {i}. {item[:50]}...")
            else:
                print("No history yet.")
            return True
        
        return False
    
    def _execute_plain_text(self, plain_text: str):
        """Execute plain text by transpiling and running it."""
        try:
            python_code, mapping = self.transpiler.transpile(plain_text, with_mapping=True)
            
            if self.verbose:
                print("\nGenerated Python code:")
                print("-" * 60)
                print(python_code)
                print("-" * 60)
            
            stdout, stderr, exception = self.runtime.execute_file(
                python_code,
                filename="<repl>",
                line_mapping=mapping,
                source_lines=getattr(self.transpiler, "last_source_lines", None),
            )
            
            if stdout:
                print(stdout, end="")
            
            if stderr:
                print(stderr, end="", file=sys.stderr)
            
            if exception:
                if not stderr:
                    detail = getattr(self.runtime, "last_error", None)
                    if detail:
                        print(detail, file=sys.stderr)
                    else:
                        print(f"Error: {type(exception).__name__}: {exception}", file=sys.stderr)
                
        except Exception as e:
            print(f"Error: {str(e)}", file=sys.stderr)
    
    def run(self):
        """Start the REPL loop."""
        self._print_banner()
        
        try:
            while True:
                try:
                    user_input = input("\nplain> ").strip()
                    
                    if not user_input:
                        continue
                    
                    self.history.append(user_input)
                    
                    if self._process_command(user_input):
                        if user_input.lower() in ("exit", "quit", "q"):
                            break
                        continue
                    
                    self._execute_plain_text(user_input)
                    
                except KeyboardInterrupt:
                    print("\n\nInterrupted. Type 'exit' to quit or continue.")
                except EOFError:
                    print("\nGoodbye!")
                    break
                    
        except Exception as e:
            print(f"REPL error: {str(e)}", file=sys.stderr)
            sys.exit(1)



