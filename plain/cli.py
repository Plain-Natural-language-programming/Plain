"""CLI interface for Plain language."""

import sys
from pathlib import Path

import click

try:
    from . import __version__
    from .compiler import Compiler
    from .runtime import Runtime
    from .repl import REPL
    from .enhanced_transpiler import EnhancedTranspiler
except ImportError:
    import os

    package_root = os.path.dirname(os.path.dirname(__file__))
    if package_root not in sys.path:
        sys.path.insert(0, package_root)
    from plain import __version__
    from plain.compiler import Compiler
    from plain.runtime import Runtime
    from plain.repl import REPL
    from plain.enhanced_transpiler import EnhancedTranspiler


@click.group()
@click.version_option(version=__version__)
def main():
    """Plain - A natural language programming language."""
    pass


@main.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--no-validate", is_flag=True, help="Skip Python syntax validation")
@click.option("--verbose", "-v", is_flag=True, help="Show generated Python code")
def run(file_path: str, no_validate: bool, verbose: bool):
    """Compile and execute a .pln file."""
    try:
        compiler = Compiler()
        
        if verbose:
            click.echo("Compiling...")
        
        python_code = compiler.compile(file_path, validate=not no_validate)
        
        if verbose:
            click.echo("\nGenerated Python code:")
            click.echo("-" * 60)
            click.echo(python_code)
            click.echo("-" * 60)
            click.echo("\nExecuting...\n")
        
        runtime = Runtime()
        stdout, stderr, exception = runtime.execute_file(python_code)
        
        if stdout:
            click.echo(stdout, nl=False)
        
        if stderr:
            click.echo(stderr, nl=False, err=True)
        
        if exception:
            click.echo(f"Error: {type(exception).__name__}: {exception}", err=True)
            sys.exit(1)
            
    except ImportError as e:
        click.echo(f"Error: {str(e)}", err=True)
        click.echo("Install required packages with: pip install -r requirements.txt", err=True)
        sys.exit(1)
    except FileNotFoundError as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)
    except ValueError as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {str(e)}", err=True)
        sys.exit(1)


@main.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option("-o", "--output", type=click.Path(), help="Output file path")
@click.option("--no-validate", is_flag=True, help="Skip Python syntax validation")
def compile_cmd(file_path: str, output: str, no_validate: bool):
    """Compile a .pln file to Python code."""
    try:
        compiler = Compiler()
        
        if output:
            output_path = output
        else:
            input_path = Path(file_path)
            output_path = str(input_path.with_suffix(".py"))
        
        click.echo(f"Compiling {file_path}...")
        result_path = compiler.compile_to_file(file_path, output_path, validate=not no_validate)
        click.echo(f"Successfully compiled to {result_path}")
        
    except ImportError as e:
        click.echo(f"Error: {str(e)}", err=True)
        click.echo("Install required packages with: pip install -r requirements.txt", err=True)
        sys.exit(1)
    except FileNotFoundError as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)
    except ValueError as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {str(e)}", err=True)
        sys.exit(1)


@main.command()
@click.option("--verbose", "-v", is_flag=True, help="Show generated Python code")
def repl(verbose: bool):
    """Start an interactive REPL."""
    try:
        repl_instance = REPL(verbose=verbose, use_enhanced=True)
        repl_instance.run()
        
    except ImportError as e:
        click.echo(f"Error: {str(e)}", err=True)
        click.echo("Install required packages with: pip install -r requirements.txt", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error starting REPL: {str(e)}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
