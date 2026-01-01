
"""Enhanced transpiler for Plain language with full natural English support."""

import ast
import keyword
import re
from dataclasses import dataclass
from typing import Optional, Set, Tuple, List, Dict, Union


@dataclass
class SourceLine:
    content: str
    indent: int
    line_no: int


@dataclass
class OutputLine:
    indent_offset: int
    text: str


@dataclass
class TranspileResult:
    lines: List[OutputLine]
    consumed: int = 1
    opens_block: bool = False
    block_type: Optional[str] = None
    block_name: Optional[str] = None
    block_params: Optional[List[str]] = None


@dataclass
class Block:
    indent: int
    block_type: str
    name: Optional[str] = None
    params: Optional[List[str]] = None


class EnhancedTranspiler:
    """Enhanced transpiler that converts natural English to Python code."""

    def __init__(self):
        """Initialize the enhanced transpiler."""
        self._library_patterns = {
            'json': [r'\bjson\.', r'json\.loads', r'json\.dumps', r'json\.load', r'json\.dump'],
            'os': [r'\bos\.', r'os\.path', r'os\.getenv', r'os\.environ', r'os\.system'],
            'sys': [
                r'\bsys\.',
                r'sys\.argv',
                r'sys\.exit',
                r'sys\.path',
                r'\bexit\b',
                r'\bquit\b',
                r'\bstop\s+program\b',
            ],
            'datetime': [r'\bdatetime\.', r'datetime\.now', r'from datetime', r'datetime\.today'],
            'time': [
                r'\btime\.',
                r'time\.sleep',
                r'time\.time',
                r'\bwait\b',
                r'\bsleep\b',
                r'\bdelay\b',
            ],
            'csv': [r'\bcsv\.', r'csv\.reader', r'csv\.writer', r'csv\.DictReader'],
            're': [r'\bre\.', r're\.search', r're\.match', r're\.findall'],
            'logging': [
                r'\blogging\.',
                r'logging\.info',
                r'logging\.error',
                r'logging\.debug',
                r'\blog\s+(?:debug|info|warning|error|critical)\b',
                r'\blogging\s+(?:debug|info|warning|error|critical)\b',
                r'\blogger\s+(?:debug|info|warning|error|critical)\b',
            ],
            'pathlib': [r'\bpathlib\.', r'Path\(', r'from pathlib'],
            'collections': [r'\bcollections\.', r'from collections'],
            'itertools': [r'\bitertools\.', r'from itertools'],
            'functools': [r'\bfunctools\.', r'from functools'],
            'asyncio': [r'\basyncio\.', r'async def', r'await ', r'from asyncio', r'async function'],
            'threading': [r'\bthreading\.', r'Thread\(', r'from threading'],
            'multiprocessing': [r'\bmultiprocessing\.', r'Process\(', r'from multiprocessing'],
            'sqlite3': [r'\bsqlite3\.', r'sqlite3\.connect', r'from sqlite3'],
            'urllib': [r'\burllib\.', r'urllib\.request', r'urllib\.parse'],
            'http': [r'\bhttp\.', r'http\.server', r'http\.client'],
            'email': [r'\bemail\.', r'from email'],
            'hashlib': [r'\bhashlib\.', r'hashlib\.md5', r'hashlib\.sha256'],
            'base64': [r'\bbase64\.', r'base64\.encode', r'base64\.decode'],
            'uuid': [r'\buuid\.', r'uuid\.uuid4', r'from uuid'],
            'random': [r'\brandom\.', r'random\.choice', r'random\.randint'],
            'math': [r'\bmath\.', r'math\.sqrt', r'math\.pi'],
            'statistics': [r'\bstatistics\.', r'from statistics'],
            'flask': [r'\bflask\.', r'from flask', r'Flask\(', r'@app\.route', r'jsonify\('],
            'django': [r'\bdjango\.', r'from django', r'Django', r'@csrf_exempt'],
            'fastapi': [r'\bfastapi\.', r'from fastapi', r'FastAPI\(', r'@app\.'],
            'tornado': [r'\btornado\.', r'from tornado'],
            'aiohttp': [r'\baiohttp\.', r'from aiohttp'],
            'requests': [r'\brequests\.', r'requests\.get', r'requests\.post', r'from requests'],
            'httpx': [r'\bhttpx\.', r'from httpx'],
            'urllib3': [r'\burllib3\.', r'from urllib3'],
            'sqlalchemy': [r'\bsqlalchemy\.', r'from sqlalchemy', r'SQLAlchemy', r'Base = declarative_base'],
            'psycopg2': [r'\bpsycopg2\.', r'from psycopg2'],
            'pymongo': [r'\bpymongo\.', r'from pymongo', r'MongoClient'],
            'redis': [r'\bredis\.', r'from redis', r'Redis\('],
            'pymysql': [r'\bpymysql\.', r'from pymysql'],
            'pandas': [r'\bpandas\.', r'import pandas', r'pd\.', r'DataFrame', r'Series'],
            'numpy': [r'\bnumpy\.', r'import numpy', r'np\.', r'array\(', r'ndarray'],
            'matplotlib': [r'\bmatplotlib\.', r'from matplotlib', r'plt\.', r'pyplot'],
            'seaborn': [r'\bseaborn\.', r'from seaborn', r'sns\.'],
            'scipy': [r'\bscipy\.', r'from scipy'],
            'sklearn': [r'\bsklearn\.', r'from sklearn', r'scikit-learn'],
            'unittest': [r'\bunittest\.', r'from unittest', r'TestCase', r'@unittest'],
            'pytest': [r'\bpytest\.', r'from pytest', r'@pytest', r'def test_'],
            'mock': [r'\bmock\.', r'from mock', r'@patch'],
            'click': [r'\bclick\.', r'from click', r'@click'],
            'typing': [r'\btyping\.', r'from typing', r'List\[', r'Dict\[', r'Optional\[', r'Union\['],
            'dataclasses': [r'\bdataclasses\.', r'from dataclasses', r'@dataclass'],
            'enum': [r'\benum\.', r'from enum', r'Enum'],
            'pydantic': [r'\bpydantic\.', r'from pydantic', r'BaseModel'],
            'configparser': [r'\bconfigparser\.', r'from configparser'],
            'yaml': [r'\byaml\.', r'import yaml', r'yaml\.load'],
            'toml': [r'\btoml\.', r'from toml'],
            'dotenv': [r'\bdotenv\.', r'from dotenv', r'load_dotenv'],
        }

        self._patterns = {
            'create_function': re.compile(
                r'^(?:create|make|build)\s+(?:a\s+)?function\s+(?:named|called)\s+(.+?)\s+that\s+takes\s+(.+?)\s+and\s+(returns|does)\s*(.*)$',
                re.IGNORECASE
            ),
            'define_function': re.compile(
                r'^define\s+(?:a\s+)?function\s+(?:named|called)\s+(.+?)\s+that\s+takes\s+(.+?)\s+and\s+(returns|does)\s*(.*)$',
                re.IGNORECASE
            ),

            'let': re.compile(r'^let\s+(\w+)\s+be\s+(.+)$', re.IGNORECASE),
            'set': re.compile(r'^set\s+(\w+)\s+to\s+(.+)$', re.IGNORECASE),
            'set_named': re.compile(
                r'^(?:set|let|assign)\s+(?:the\s+)?(.+?)\s+(?:to|as|be|equal\s+to)\s+(.+)$',
                re.IGNORECASE
            ),
            'create_variable': re.compile(
                r'^create\s+(?:a\s+)?(?:variable|list|dictionary|dict|map)\s+(?:named|called)\s+(.+?)(?:\s+with\s+(.+))?$',
                re.IGNORECASE
            ),
            'create_variable_set': re.compile(
                r'^create\s+(?:a\s+)?(?:variable|list|dictionary|dict|map)\s+(?:named|called)\s+(.+?)\s+set\s+to\s+(.+)$',
                re.IGNORECASE
            ),
            'increase': re.compile(r'^(?:increase|increment)\s+(.+?)\s+by\s+(.+)$', re.IGNORECASE),
            'decrease': re.compile(r'^(?:decrease|decrement|reduce)\s+(.+?)\s+by\s+(.+)$', re.IGNORECASE),

            'if_then_do_block': re.compile(r'^if\s+(.+?)\s+then\s+do\s*$', re.IGNORECASE),
            'if_do_block': re.compile(r'^if\s+(.+?)\s+do\s*$', re.IGNORECASE),
            'if_then_inline': re.compile(r'^if\s+(.+?)\s+then\s+(.+)$', re.IGNORECASE),
            'if_do_inline': re.compile(r'^if\s+(.+?)\s+do\s+(.+)$', re.IGNORECASE),
            'if_return': re.compile(r'^if\s+(.+?)\s+return\s+(.+)$', re.IGNORECASE),
            'elif_then_do_block': re.compile(r'^(?:elif|else\s+if)\s+(.+?)\s+then\s+do\s*$', re.IGNORECASE),
            'elif_do_block': re.compile(r'^(?:elif|else\s+if)\s+(.+?)\s+do\s*$', re.IGNORECASE),
            'elif_then_inline': re.compile(r'^(?:elif|else\s+if)\s+(.+?)\s+then\s+(.+)$', re.IGNORECASE),
            'elif_do_inline': re.compile(r'^(?:elif|else\s+if)\s+(.+?)\s+do\s+(.+)$', re.IGNORECASE),
            'else_do_block': re.compile(r'^(?:else|otherwise)\s+do\s*$', re.IGNORECASE),
            'else_inline': re.compile(r'^(?:else|otherwise)\s*,?\s+(.+)$', re.IGNORECASE),

            'for_each': re.compile(
                r'^for\s+each\s+(\w+)\s+in\s+(.+?)\s+do\s*(.*)$',
                re.IGNORECASE | re.DOTALL
            ),
            'for_each_in': re.compile(r'^for\s+each\s+(\w+)\s+in\s+(.+)$', re.IGNORECASE),
            'while_do': re.compile(r'^while\s+(.+?)\s+do\s*(.*)$', re.IGNORECASE),
            'repeat_times': re.compile(r'^repeat\s+(.+?)\s+times\s+do\s*(.*)$', re.IGNORECASE),
            'repeat_until': re.compile(r'^repeat\s+until\s+(.+?)\s+do\s*(.*)$', re.IGNORECASE),
            'repeat_while': re.compile(r'^repeat\s+while\s+(.+?)\s+do\s*(.*)$', re.IGNORECASE),
            'wait_sleep': re.compile(
                r'^(?:wait|sleep|delay)\s+(?:for\s+)?(.+?)(?:\s+(seconds?|minutes?|hours?|ms|milliseconds?))?$',
                re.IGNORECASE
            ),

            'print_numbers': re.compile(r'^print\s+numbers\s+from\s+(.+?)\s+to\s+(.+)$', re.IGNORECASE),
            'print': re.compile(r'^(?:print|show|display|echo|log)\s+(.+)$', re.IGNORECASE),
            'say_message': re.compile(r'^(?:say|tell|announce)\s+(.+)$', re.IGNORECASE),
            'log_message': re.compile(
                r'^(?:log|logging|logger)\s+(debug|info|warning|error|critical)\s+(.+)$',
                re.IGNORECASE
            ),

            'return': re.compile(r'^(?:return|give\s+back|send\s+back)\s+(.+)$', re.IGNORECASE),

            'call_function': re.compile(r'^(?:call|run|execute)\s+(.+?)(?:\s+with\s+(.+))?$', re.IGNORECASE),
            'call_with': re.compile(
                r'^([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*)\s+(?:with|using)\s+(.+)$',
                re.IGNORECASE
            ),
            'dot_call': re.compile(r'^([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+)\s+(.+)$', re.IGNORECASE),

            'class_inheritance': re.compile(
                r'^(?:create|make|define)\s+(?:a\s+)?class\s+(?:named|called)\s+(.+?)\s+that\s+(?:extends|inherits\s+from)\s+(.+)$',
                re.IGNORECASE
            ),
            'create_class': re.compile(
                r'^(?:create|make|define)\s+(?:a\s+)?class\s+(?:named|called)\s+(.+?)\s*$',
                re.IGNORECASE
            ),

            'string_length_comparison': re.compile(
                r'^if\s+the\s+length\s+of\s+string\s+(\w+)\s+is\s+'
                r'(bigger|greater|longer|smaller|less|shorter|equal|same)\s+than\s+string\s+(\w+)'
                r'(?:\s*,?\s*then\s*)?\s*return\s+(.+)$',
                re.IGNORECASE
            ),

            'try_block': re.compile(r'^try\s*(?::\s*)?(?:do\s*)?$', re.IGNORECASE),
            'catch': re.compile(
                r'^catch\s+(?:exception|error)?(?:\s+as\s+(\w+))?\s*:?\s*(?:do\s*(.*))?$',
                re.IGNORECASE
            ),
            'finally': re.compile(r'^finally\s*:?\s*(?:do\s*(.*))?$', re.IGNORECASE),
            'raise': re.compile(r'^raise\s+(.+)$', re.IGNORECASE),
            'throw': re.compile(r'^throw\s+(.+)$', re.IGNORECASE),
            'exit': re.compile(
                r'^(?:exit|quit|stop)(?:\s+program|\s+app|\s+script)?(?:\s+(?:with\s+code\s+)?(.+))?$',
                re.IGNORECASE
            ),

            'async_function': re.compile(
                r'^(?:create|make|define)\s+(?:an\s+)?async\s+function\s+(?:named|called)\s+(.+?)\s+that\s+takes\s+(.+?)\s+and\s+(returns|does)\s*(.*)$',
                re.IGNORECASE
            ),
            'await': re.compile(r'^await\s+(.+)$', re.IGNORECASE),

            'class_method': re.compile(
                r'^(?:create|make|define)\s+(?:a\s+)?class\s+method\s+(?:named|called)\s+(\w+)\s+in\s+class\s+(\w+)\s+that\s+takes\s+(.+?)\s+and\s+(returns|does)\s*(.*)$',
                re.IGNORECASE
            ),
            'instance_method': re.compile(
                r'^(?:create|make|define)\s+(?:a\s+)?method\s+(?:named|called)\s+(\w+)\s+in\s+class\s+(\w+)\s+that\s+takes\s+(.+?)\s+and\s+(returns|does)\s*(.*)$',
                re.IGNORECASE
            ),
            'static_method': re.compile(
                r'^(?:create|make|define)\s+(?:a\s+)?static\s+method\s+(?:named|called)\s+(\w+)\s+(?:in\s+class\s+(\w+)\s+)?that\s+takes\s+(.+?)\s+and\s+(returns|does)\s*(.*)$',
                re.IGNORECASE
            ),
            'property': re.compile(
                r'^create\s+(?:a\s+)?property\s+named\s+(\w+)\s+(?:in\s+class\s+(\w+)\s+)?that\s+returns\s+(.+)$',
                re.IGNORECASE
            ),

            'decorator': re.compile(r'^decorate\s+(\w+)\s+with\s+(.+)$', re.IGNORECASE),

            'with_as': re.compile(r'^with\s+(.+?)\s+as\s+(\w+)\s+do\s*(.*)$', re.IGNORECASE),
            'with_simple': re.compile(r'^with\s+(.+?)\s+do\s*(.*)$', re.IGNORECASE),

            'generator': re.compile(
                r'^(?:create|make|define)\s+(?:a\s+)?generator\s+(?:named|called)\s+(.+?)\s+that\s+takes\s+(.+?)\s+and\s+yields\s*(.*)$',
                re.IGNORECASE
            ),
            'yield': re.compile(r'^yield\s+(.+)$', re.IGNORECASE),
            'append_to_list': re.compile(r'^(?:add|append|push)\s+(.+?)\s+to\s+(?:the\s+)?(?:list\s+)?(.+)$', re.IGNORECASE),
            'prepend_to_list': re.compile(r'^prepend\s+(.+?)\s+to\s+(?:the\s+)?(?:list\s+)?(.+)$', re.IGNORECASE),
            'remove_from_list': re.compile(r'^(?:remove|delete)\s+(.+?)\s+from\s+(?:the\s+)?(?:list\s+)?(.+)$', re.IGNORECASE),
            'pop_from_list': re.compile(r'^pop\s+(?:from\s+)?(.+)$', re.IGNORECASE),
            'clear_list': re.compile(r'^(?:clear|empty)\s+(?:the\s+)?(?:list\s+)?(.+)$', re.IGNORECASE),
            'sort_list': re.compile(r'^(?:sort|order)\s+(?:the\s+)?(?:list\s+)?(.+)$', re.IGNORECASE),
            'reverse_list': re.compile(r'^(?:reverse)\s+(?:the\s+)?(?:list\s+)?(.+)$', re.IGNORECASE),

            'connect_db': re.compile(r'^connect\s+to\s+database\s+(.+)$', re.IGNORECASE),
            'query_db': re.compile(r'^query\s+database\s+with\s+(.+)$', re.IGNORECASE),
            'insert_db': re.compile(r'^insert\s+into\s+database\s+(.+)$', re.IGNORECASE),

            'type_hint': re.compile(r'^(\w+)\s*:\s*(.+)$', re.IGNORECASE),

            'list_comprehension': re.compile(
                r'^create\s+(?:a\s+)?list\s+of\s+(.+?)\s+for\s+each\s+(\w+)\s+in\s+(.+?)(?:\s+if\s+(.+))?$',
                re.IGNORECASE
            ),

            'lambda': re.compile(
                r'^create\s+(?:a\s+)?lambda\s+function\s+that\s+takes\s+(.+?)\s+and\s+returns\s+(.+)$',
                re.IGNORECASE
            ),

            'api_endpoint': re.compile(
                r'^create\s+(?:an\s+)?api\s+endpoint\s+at\s+(.+?)\s+that\s+(\w+)\s+and\s+returns\s+(.+)$',
                re.IGNORECASE
            ),
            'api_endpoint_block': re.compile(
                r'^create\s+(?:an\s+)?api\s+endpoint\s+at\s+(.+?)\s+that\s+(\w+)\s+and\s+does\s*$',
                re.IGNORECASE
            ),
            'async_api_endpoint': re.compile(
                r'^create\s+(?:an\s+)?async\s+api\s+endpoint\s+at\s+(.+?)\s+that\s+(\w+)\s+and\s+returns\s+(.+)$',
                re.IGNORECASE
            ),
            'async_api_endpoint_block': re.compile(
                r'^create\s+(?:an\s+)?async\s+api\s+endpoint\s+at\s+(.+?)\s+that\s+(\w+)\s+and\s+does\s*$',
                re.IGNORECASE
            ),
        }

        self.last_mapping: Dict[int, SourceLine] = {}
        self.last_source_lines: List[str] = []

    def transpile(self, plain_text: str, with_mapping: bool = False) -> Union[str, Tuple[str, Dict[int, SourceLine]]]:
        """Convert natural English to Python code."""
        if not plain_text.strip():
            raise ValueError("Input is empty.")

        self.last_mapping = {}
        self.last_source_lines = plain_text.splitlines()

        lines = self._tokenize_lines(plain_text)
        if not lines:
            raise ValueError("Input is empty.")

        indent_unit = self._infer_indent_unit(lines)
        features = self._detect_features(lines)

        all_code = '\n'.join(line.content for line in lines)
        detected_libraries = self._detect_libraries(all_code, features)

        imports = self._generate_imports(detected_libraries, features)

        python_lines: List[str] = []
        mapping: List[Optional[SourceLine]] = []
        if imports:
            python_lines.extend(imports)
            python_lines.append('')
            mapping.extend([None] * (len(imports) + 1))

        if features.get('flask_app'):
            python_lines.append('app = Flask(__name__, root_path=os.getcwd())')
            python_lines.append('')
            mapping.extend([None, None])

        stack: List[Block] = []
        endpoint_names: Set[str] = set()

        i = 0
        while i < len(lines):
            line = lines[i]

            while stack and line.indent <= stack[-1].indent:
                stack.pop()

            result = self._transpile_line(line, lines, i, indent_unit, stack, endpoint_names)

            for out in result.lines:
                python_lines.append(' ' * (line.indent + out.indent_offset * indent_unit) + out.text)
                mapping.append(line)

            if result.opens_block:
                block_type = result.block_type or "block"
                stack.append(
                    Block(
                        indent=line.indent,
                        block_type=block_type,
                        name=result.block_name,
                        params=result.block_params,
                    )
                )

            i += result.consumed

        if features.get('flask_app') and features.get('flask_run', True):
            python_lines.append('')
            python_lines.append('if __name__ == "__main__":')
            python_lines.append(' ' * indent_unit + 'app.run(debug=True, port=5000)')
            mapping.extend([None, None, None])

        python_code = '\n'.join(python_lines)
        mapping_dict = {idx + 1: src for idx, src in enumerate(mapping) if src is not None}
        self.last_mapping = mapping_dict

        if with_mapping:
            return python_code, mapping_dict
        return python_code

    def _transpile_line(
        self,
        line: SourceLine,
        all_lines: List[SourceLine],
        index: int,
        indent_unit: int,
        stack: List[Block],
        endpoint_names: Set[str],
    ) -> TranspileResult:
        """Transpile a single line or multi-line structure."""
        text = line.content.strip()
        current_function_params = self._current_function_params(stack)

        match = self._patterns['string_length_comparison'].match(text)
        if match:
            left = match.group(1)
            op_word = match.group(2)
            right = match.group(3)
            return_value = match.group(4)

            op_map = {
                'bigger': '>', 'greater': '>', 'longer': '>',
                'smaller': '<', 'less': '<', 'shorter': '<',
                'equal': '==', 'same': '=='
            }
            op = op_map.get(op_word.lower(), '>')

            otherwise_value = None
            consumed = 1
            if index + 1 < len(all_lines):
                next_line = all_lines[index + 1].content.strip()
                otherwise_match = self._patterns['else_inline'].match(next_line)
                if otherwise_match:
                    otherwise_value = otherwise_match.group(1).strip()
                    consumed = 2

            lines = [
                OutputLine(0, f"def program({left}, {right}):"),
                OutputLine(1, f"if len({left}) {op} len({right}):"),
                OutputLine(2, f"return {self._parse_value(return_value)}"),
            ]
            if otherwise_value is not None:
                lines.append(OutputLine(1, "else:"))
                lines.append(OutputLine(2, f"return {self._parse_value(otherwise_value)}"))
            return TranspileResult(lines=lines, consumed=consumed)

        match = self._patterns['async_api_endpoint'].match(text)
        if match:
            return self._render_api_endpoint(
                match.group(1),
                match.group(2),
                match.group(3),
                async_def=True,
                all_lines=all_lines,
                index=index,
                current_indent=line.indent,
                endpoint_names=endpoint_names,
            )

        match = self._patterns['async_api_endpoint_block'].match(text)
        if match:
            return self._render_api_endpoint(
                match.group(1),
                match.group(2),
                None,
                async_def=True,
                all_lines=all_lines,
                index=index,
                current_indent=line.indent,
                endpoint_names=endpoint_names,
            )

        match = self._patterns['api_endpoint'].match(text)
        if match:
            return self._render_api_endpoint(
                match.group(1),
                match.group(2),
                match.group(3),
                async_def=False,
                all_lines=all_lines,
                index=index,
                current_indent=line.indent,
                endpoint_names=endpoint_names,
            )

        match = self._patterns['api_endpoint_block'].match(text)
        if match:
            return self._render_api_endpoint(
                match.group(1),
                match.group(2),
                None,
                async_def=False,
                all_lines=all_lines,
                index=index,
                current_indent=line.indent,
                endpoint_names=endpoint_names,
            )

        match = self._patterns['print_numbers'].match(text)
        if match:
            return TranspileResult(lines=self._render_range_print(match.group(1), match.group(2)))

        match = self._patterns['elif_then_do_block'].match(text) or self._patterns['elif_do_block'].match(text)
        if match:
            condition = self._parse_condition(match.group(1))
            return self._render_block_header(
                f"elif {condition}:",
                all_lines,
                index,
                line.indent,
            )

        match = self._patterns['elif_then_inline'].match(text) or self._patterns['elif_do_inline'].match(text)
        if match:
            condition = self._parse_condition(match.group(1))
            return self._render_inline_block(
                f"elif {condition}:",
                match.group(2),
                current_params=current_function_params,
            )

        match = self._patterns['else_do_block'].match(text)
        if match:
            return self._render_block_header("else:", all_lines, index, line.indent)

        match = self._patterns['else_inline'].match(text)
        if match:
            return self._render_inline_block("else:", match.group(1), current_params=current_function_params)

        match = self._patterns['if_then_do_block'].match(text) or self._patterns['if_do_block'].match(text)
        if match:
            condition = self._parse_condition(match.group(1))
            return self._render_block_header(
                f"if {condition}:",
                all_lines,
                index,
                line.indent,
            )

        match = self._patterns['if_return'].match(text)
        if match:
            condition = self._parse_condition(match.group(1))
            return_value = self._parse_value(match.group(2), current_params=current_function_params)
            return self._render_inline_block(
                f"if {condition}:",
                f"return {return_value}",
                current_params=current_function_params,
            )

        match = self._patterns['if_then_inline'].match(text) or self._patterns['if_do_inline'].match(text)
        if match:
            condition = self._parse_condition(match.group(1))
            return self._render_inline_block(
                f"if {condition}:",
                match.group(2),
                current_params=current_function_params,
            )

        match = self._patterns['for_each'].match(text)
        if match:
            var = match.group(1)
            iterable = self._parse_expression(match.group(2))
            action = match.group(3).strip()
            if action:
                return self._render_inline_block(
                    f"for {var} in {iterable}:",
                    action,
                    current_params=current_function_params,
                )
            return self._render_block_header(
                f"for {var} in {iterable}:",
                all_lines,
                index,
                line.indent,
            )

        match = self._patterns['for_each_in'].match(text)
        if match:
            var = match.group(1)
            iterable = self._parse_expression(match.group(2))
            return self._render_block_header(
                f"for {var} in {iterable}:",
                all_lines,
                index,
                line.indent,
            )

        match = self._patterns['repeat_times'].match(text)
        if match:
            count_expr = self._parse_expression(match.group(1))
            action = match.group(2).strip()
            header = f"for _ in range({count_expr}):"
            if action:
                return self._render_inline_block(header, action, current_params=current_function_params)
            return self._render_block_header(
                header,
                all_lines,
                index,
                line.indent,
            )

        match = self._patterns['repeat_until'].match(text)
        if match:
            condition = self._parse_condition(match.group(1))
            action = match.group(2).strip()
            header = f"while not ({condition}):"
            if action:
                return self._render_inline_block(header, action, current_params=current_function_params)
            return self._render_block_header(
                header,
                all_lines,
                index,
                line.indent,
            )

        match = self._patterns['repeat_while'].match(text)
        if match:
            condition = self._parse_condition(match.group(1))
            action = match.group(2).strip()
            header = f"while {condition}:"
            if action:
                return self._render_inline_block(header, action, current_params=current_function_params)
            return self._render_block_header(
                header,
                all_lines,
                index,
                line.indent,
            )

        match = self._patterns['wait_sleep'].match(text)
        if match:
            duration = self._parse_duration(match.group(1), match.group(2))
            return TranspileResult(lines=[OutputLine(0, f"time.sleep({duration})")])

        match = self._patterns['while_do'].match(text)
        if match:
            condition = self._parse_condition(match.group(1))
            action = match.group(2).strip()
            if action:
                return self._render_inline_block(
                    f"while {condition}:",
                    action,
                    current_params=current_function_params,
                )
            return self._render_block_header(
                f"while {condition}:",
                all_lines,
                index,
                line.indent,
            )

        match = self._patterns['with_as'].match(text)
        if match:
            resource = self._parse_expression(match.group(1))
            var = match.group(2)
            action = match.group(3).strip()
            if action:
                return self._render_inline_block(
                    f"with {resource} as {var}:",
                    action,
                    current_params=current_function_params,
                )
            return self._render_block_header(
                f"with {resource} as {var}:",
                all_lines,
                index,
                line.indent,
            )

        match = self._patterns['with_simple'].match(text)
        if match:
            resource = self._parse_expression(match.group(1))
            action = match.group(2).strip()
            if action:
                return self._render_inline_block(
                    f"with {resource}:",
                    action,
                    current_params=current_function_params,
                )
            return self._render_block_header(
                f"with {resource}:",
                all_lines,
                index,
                line.indent,
            )

        match = self._patterns['try_block'].match(text)
        if match:
            return self._render_block_header("try:", all_lines, index, line.indent)

        match = self._patterns['catch'].match(text)
        if match:
            exc_name = match.group(1)
            action = match.group(2).strip() if match.group(2) else ""
            if exc_name:
                header = f"except Exception as {exc_name}:"
            else:
                header = "except Exception:"
            if action:
                return self._render_inline_block(header, action, current_params=current_function_params)
            return self._render_block_header(header, all_lines, index, line.indent)

        match = self._patterns['finally'].match(text)
        if match:
            action = match.group(1).strip() if match.group(1) else ""
            if action:
                return self._render_inline_block("finally:", action, current_params=current_function_params)
            return self._render_block_header("finally:", all_lines, index, line.indent)

        match = self._patterns['create_function'].match(text) or self._patterns['define_function'].match(text)
        if match:
            name = self._normalize_function_name(match.group(1))
            params_text = match.group(2).strip()
            action_type = match.group(3).strip().lower()
            body_text = match.group(4).strip()

            params = self._parse_parameters(params_text)
            header = f"def {name}({', '.join(params)}):"
            if body_text:
                body_lines = self._render_inline_body(action_type, body_text, current_params=params)
                return TranspileResult(lines=[OutputLine(0, header)] + body_lines)
            return self._render_block_header(
                header,
                all_lines,
                index,
                line.indent,
                block_type="def",
                block_params=params,
            )

        match = self._patterns['async_function'].match(text)
        if match:
            name = self._normalize_function_name(match.group(1))
            params_text = match.group(2).strip()
            action_type = match.group(3).strip().lower()
            body_text = match.group(4).strip()

            params = self._parse_parameters(params_text)
            header = f"async def {name}({', '.join(params)}):"
            if body_text:
                body_lines = self._render_inline_body(action_type, body_text, current_params=params)
                return TranspileResult(lines=[OutputLine(0, header)] + body_lines)
            return self._render_block_header(
                header,
                all_lines,
                index,
                line.indent,
                block_type="def",
                block_params=params,
            )

        match = self._patterns['generator'].match(text)
        if match:
            name = self._normalize_function_name(match.group(1))
            params_text = match.group(2).strip()
            yield_expr = match.group(3).strip()
            params = self._parse_parameters(params_text)
            header = f"def {name}({', '.join(params)}):"
            if yield_expr:
                if self._should_parse_inline_action(yield_expr):
                    action_lines = self._parse_inline_action(yield_expr, current_params=params)
                    if action_lines:
                        body_lines = [OutputLine(1 + item.indent_offset, item.text) for item in action_lines]
                        return TranspileResult(lines=[OutputLine(0, header)] + body_lines)
                yield_line = OutputLine(1, f"yield {self._parse_expression(yield_expr)}")
                return TranspileResult(lines=[OutputLine(0, header), yield_line])
            return self._render_block_header(
                header,
                all_lines,
                index,
                line.indent,
                block_type="def",
                block_params=params,
            )

        match = self._patterns['class_inheritance'].match(text)
        if match:
            name = self._normalize_class_name(match.group(1))
            parents_text = match.group(2)
            parents = []
            for parent in re.split(r'\s+and\s+|,\s*', parents_text):
                parent = parent.strip()
                if not parent:
                    continue
                if re.match(r'^[A-Za-z_]\w*(?:\.\w+)*$', parent):
                    parents.append(parent)
                else:
                    parents.append(self._normalize_class_name(parent))
            header = f"class {name}({', '.join(parents)}):"
            return self._render_block_header(header, all_lines, index, line.indent, block_type="class", block_name=name)

        match = self._patterns['create_class'].match(text)
        if match:
            name = self._normalize_class_name(match.group(1))
            header = f"class {name}:"
            return self._render_block_header(header, all_lines, index, line.indent, block_type="class", block_name=name)

        current_class = self._current_class(stack)

        match = self._patterns['class_method'].match(text)
        if match:
            return self._render_class_method(
                match.group(1),
                match.group(2),
                match.group(3),
                match.group(4),
                match.group(5),
                current_class,
                all_lines,
                index,
                line.indent,
                is_class_method=True,
            )

        match = self._patterns['static_method'].match(text)
        if match:
            return self._render_class_method(
                match.group(1),
                match.group(2),
                match.group(3),
                match.group(4),
                match.group(5),
                current_class,
                all_lines,
                index,
                line.indent,
                is_static_method=True,
            )

        match = self._patterns['instance_method'].match(text)
        if match:
            return self._render_class_method(
                match.group(1),
                match.group(2),
                match.group(3),
                match.group(4),
                match.group(5),
                current_class,
                all_lines,
                index,
                line.indent,
                is_instance_method=True,
            )

        match = self._patterns['property'].match(text)
        if match:
            prop_name = match.group(1)
            class_name = match.group(2)
            return_expr = match.group(3).strip()
            return self._render_property(
                prop_name,
                class_name,
                return_expr,
                current_class,
                all_lines,
                index,
                line.indent,
            )

        match = self._patterns['set_named'].match(text)
        if match:
            var = self._normalize_target(match.group(1))
            value = self._parse_expression(match.group(2))
            return TranspileResult(lines=[OutputLine(0, f"{var} = {value}")])

        match = self._patterns['let'].match(text) or self._patterns['set'].match(text)
        if match:
            var = self._normalize_target(match.group(1))
            value = self._parse_expression(match.group(2))
            return TranspileResult(lines=[OutputLine(0, f"{var} = {value}")])

        match = self._patterns['increase'].match(text)
        if match:
            target = self._normalize_target(match.group(1))
            amount = self._parse_expression(match.group(2))
            return TranspileResult(lines=[OutputLine(0, f"{target} += {amount}")])

        match = self._patterns['decrease'].match(text)
        if match:
            target = self._normalize_target(match.group(1))
            amount = self._parse_expression(match.group(2))
            return TranspileResult(lines=[OutputLine(0, f"{target} -= {amount}")])

        match = self._patterns['create_variable_set'].match(text)
        if match:
            var = self._normalize_target(match.group(1))
            value_text = match.group(2)
            kind = self._collection_kind_from_text(text)
            if kind == "list":
                value = self._parse_collection_initializer(value_text, "list")
            elif kind == "dictionary":
                value = self._parse_collection_initializer(value_text, "dictionary")
            else:
                value = self._parse_expression(value_text)
            return TranspileResult(lines=[OutputLine(0, f"{var} = {value}")])

        match = self._patterns['create_variable'].match(text)
        if match:
            var = self._normalize_target(match.group(1))
            value_text = match.group(2)
            kind = self._collection_kind_from_text(text)
            if kind == "list":
                value = self._parse_collection_initializer(value_text, "list")
            elif kind == "dictionary":
                value = self._parse_collection_initializer(value_text, "dictionary")
            else:
                value = self._parse_expression(value_text) if value_text else "None"
            return TranspileResult(lines=[OutputLine(0, f"{var} = {value}")])

        match = self._patterns['append_to_list'].match(text)
        if match:
            item = self._parse_expression(match.group(1))
            target = self._normalize_expression_target(match.group(2))
            return TranspileResult(lines=[OutputLine(0, f"{target}.append({item})")])

        match = self._patterns['prepend_to_list'].match(text)
        if match:
            item = self._parse_expression(match.group(1))
            target = self._normalize_expression_target(match.group(2))
            return TranspileResult(lines=[OutputLine(0, f"{target}.insert(0, {item})")])

        match = self._patterns['remove_from_list'].match(text)
        if match:
            item = self._parse_expression(match.group(1))
            target = self._normalize_expression_target(match.group(2))
            return TranspileResult(lines=[OutputLine(0, f"{target}.remove({item})")])

        match = self._patterns['pop_from_list'].match(text)
        if match:
            target = self._normalize_expression_target(match.group(1))
            return TranspileResult(lines=[OutputLine(0, f"{target}.pop()")])

        match = self._patterns['clear_list'].match(text)
        if match:
            target = self._normalize_expression_target(match.group(1))
            return TranspileResult(lines=[OutputLine(0, f"{target}.clear()")])

        match = self._patterns['sort_list'].match(text)
        if match:
            target = self._normalize_expression_target(match.group(1))
            return TranspileResult(lines=[OutputLine(0, f"{target}.sort()")])

        match = self._patterns['reverse_list'].match(text)
        if match:
            target = self._normalize_expression_target(match.group(1))
            return TranspileResult(lines=[OutputLine(0, f"{target}.reverse()")])

        match = self._patterns['print_numbers'].match(text)
        if match:
            return TranspileResult(lines=self._render_range_print(match.group(1), match.group(2)))

        match = self._patterns['say_message'].match(text)
        if match:
            message = self._parse_say_value(match.group(1))
            return TranspileResult(lines=[OutputLine(0, f"print({message})")])

        match = self._patterns['log_message'].match(text)
        if match:
            level = match.group(1).lower()
            message = self._parse_expression(match.group(2))
            return TranspileResult(lines=[OutputLine(0, f"logging.{level}({message})")])

        match = self._patterns['print'].match(text)
        if match:
            expr = self._parse_expression(match.group(1))
            return TranspileResult(lines=[OutputLine(0, f"print({expr})")])

        match = self._patterns['return'].match(text)
        if match:
            value = self._parse_value(match.group(1), current_params=current_function_params)
            return TranspileResult(lines=[OutputLine(0, f"return {value}")])

        match = self._patterns['await'].match(text)
        if match:
            expr = self._parse_expression(match.group(1))
            return TranspileResult(lines=[OutputLine(0, f"await {expr}")])

        match = self._patterns['raise'].match(text) or self._patterns['throw'].match(text)
        if match:
            expr = self._parse_expression(match.group(1))
            return TranspileResult(lines=[OutputLine(0, f"raise {expr}")])

        match = self._patterns['exit'].match(text)
        if match:
            code_text = match.group(1)
            if code_text:
                code_expr = self._parse_expression(code_text)
                return TranspileResult(lines=[OutputLine(0, f"sys.exit({code_expr})")])
            return TranspileResult(lines=[OutputLine(0, "sys.exit(0)")])

        match = self._patterns['yield'].match(text)
        if match:
            expr = self._parse_expression(match.group(1))
            return TranspileResult(lines=[OutputLine(0, f"yield {expr}")])

        match = self._patterns['call_function'].match(text)
        if match:
            func_name = self._normalize_expression_target(match.group(1))
            args_text = match.group(2) if match.group(2) else ""
            args = self._parse_function_arguments(args_text) if args_text else []
            args_str = ', '.join(args) if args else ''
            return TranspileResult(lines=[OutputLine(0, f"{func_name}({args_str})")])

        match = self._patterns['call_with'].match(text)
        if match:
            func_name = self._normalize_expression_target(match.group(1))
            args = self._parse_function_arguments(match.group(2))
            args_str = ', '.join(args) if args else ''
            return TranspileResult(lines=[OutputLine(0, f"{func_name}({args_str})")])

        match = self._patterns['decorator'].match(text)
        if match:
            target = match.group(1)
            decorator = self._parse_expression(match.group(2)).lstrip('@')
            return TranspileResult(lines=[OutputLine(0, f"{target} = {decorator}({target})")])

        match = self._patterns['list_comprehension'].match(text)
        if match:
            expr = self._parse_expression(match.group(1))
            var = match.group(2)
            iterable = self._parse_expression(match.group(3))
            condition = match.group(4)
            if condition:
                cond = self._parse_condition(condition)
                return TranspileResult(lines=[OutputLine(0, f"[{expr} for {var} in {iterable} if {cond}]")])
            return TranspileResult(lines=[OutputLine(0, f"[{expr} for {var} in {iterable}]")])

        match = self._patterns['lambda'].match(text)
        if match:
            params_text = match.group(1).strip()
            return_expr = match.group(2).strip()
            params = self._parse_parameters(params_text)
            expr = self._parse_expression(return_expr)
            return TranspileResult(lines=[OutputLine(0, f"lambda {', '.join(params)}: {expr}")])

        match = self._patterns['connect_db'].match(text)
        if match:
            db_url = self._parse_expression(match.group(1))
            return TranspileResult(lines=[OutputLine(0, f"db_connection = connect({db_url})")])

        match = self._patterns['query_db'].match(text)
        if match:
            query = self._parse_expression(match.group(1))
            return TranspileResult(lines=[OutputLine(0, f"result = db_connection.execute({query})")])

        match = self._patterns['insert_db'].match(text)
        if match:
            query = self._parse_expression(match.group(1))
            return TranspileResult(lines=[OutputLine(0, f"db_connection.execute({query})")])

        if self._looks_like_assignment(text):
            parts = text.split('=', 1)
            left = parts[0].strip()
            right = parts[1].strip() if len(parts) > 1 else ""
            if left and right:
                target = self._normalize_target(left)
                return TranspileResult(lines=[OutputLine(0, f"{target} = {self._parse_expression(right)}")])

        try:
            ast.parse(text)
            if text.endswith(':'):
                return self._render_block_header(text, all_lines, index, line.indent)
            return TranspileResult(lines=[OutputLine(0, text)])
        except Exception:
            pass

        return TranspileResult(lines=[OutputLine(0, self._parse_expression(text))])

    def _tokenize_lines(self, plain_text: str) -> List[SourceLine]:
        """Tokenize text into non-empty, non-comment lines preserving indentation."""
        lines: List[SourceLine] = []
        for idx, raw in enumerate(plain_text.splitlines(), 1):
            if not raw.strip():
                continue
            stripped = raw.lstrip()
            if stripped.startswith('#') or stripped.startswith('//'):
                continue
            indent = self._count_indent(raw)
            lines.append(SourceLine(content=stripped, indent=indent, line_no=idx))
        return lines

    def _count_indent(self, raw_line: str) -> int:
        """Count indentation (spaces) with tabs expanded to 4 spaces."""
        expanded = raw_line.expandtabs(4)
        return len(expanded) - len(expanded.lstrip(' '))

    def _infer_indent_unit(self, lines: List[SourceLine]) -> int:
        """Infer indentation width from the source."""
        indents = sorted(set(line.indent for line in lines if line.indent > 0))
        if not indents:
            return 4
        if len(indents) == 1:
            return indents[0]
        diffs = [b - a for a, b in zip(indents, indents[1:]) if b - a > 0]
        return min(diffs) if diffs else indents[0]

    def _detect_features(self, lines: List[SourceLine]) -> Dict[str, bool]:
        """Detect higher-level features like API endpoints."""
        features = {"flask_app": False, "flask_run": True}
        for line in lines:
            text = line.content
            if (self._patterns['api_endpoint'].match(text)
                    or self._patterns['api_endpoint_block'].match(text)
                    or self._patterns['async_api_endpoint'].match(text)
                    or self._patterns['async_api_endpoint_block'].match(text)):
                features["flask_app"] = True
            if "app.run" in text or "__name__" in text:
                features["flask_run"] = False
        return features

    def _current_class(self, stack: List[Block]) -> Optional[str]:
        for block in reversed(stack):
            if block.block_type == "class":
                return block.name
        return None

    def _current_function_params(self, stack: List[Block]) -> Optional[List[str]]:
        for block in reversed(stack):
            if block.block_type == "def":
                return block.params
        return None

    def _should_autopass(self, all_lines: List[SourceLine], index: int, current_indent: int) -> bool:
        if index + 1 >= len(all_lines):
            return True
        return all_lines[index + 1].indent <= current_indent

    def _looks_like_assignment(self, text: str) -> bool:
        if '=' not in text:
            return False
        if '==' in text or '!=' in text or '>=' in text or '<=' in text or ':=' in text:
            return False
        left, _, right = text.partition('=')
        if not left.strip() or not right.strip():
            return False
        if not self._is_assignable_expr(left.strip()):
            return False
        return True

    def _is_assignable_expr(self, expr: str) -> bool:
        try:
            node = ast.parse(expr, mode='eval').body
        except Exception:
            return False
        return isinstance(node, (ast.Name, ast.Attribute, ast.Subscript))

    def _normalize_target(self, text: str, default: str = "value") -> str:
        cleaned = text.strip()
        if not cleaned:
            return default
        if self._is_assignable_expr(cleaned):
            return cleaned
        return self._sanitize_identifier(cleaned, default=default)

    def _normalize_expression_target(self, text: str, default: str = "value") -> str:
        cleaned = text.strip()
        if not cleaned:
            return default
        if self._is_valid_python_expr(cleaned):
            return cleaned
        return self._sanitize_identifier(cleaned, default=default)

    def _sanitize_identifier(self, text: str, default: str = "value") -> str:
        cleaned = text.strip()
        if not cleaned:
            return default
        cleaned = re.sub(r'^(?:the|a|an|my|your|our|their)\s+', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'[^\w]+', '_', cleaned).strip('_')
        if not cleaned:
            cleaned = default
        if re.match(r'^\d', cleaned):
            cleaned = f"{default}_{cleaned}"
        cleaned = cleaned.lower()
        if keyword.iskeyword(cleaned):
            cleaned = f"{cleaned}_"
        return cleaned

    def _normalize_param_name(self, text: str) -> str:
        cleaned = text.strip()
        if not cleaned:
            return ""
        named_match = re.search(r'(?:named|called)\s+(.+)$', cleaned, re.IGNORECASE)
        if named_match:
            cleaned = named_match.group(1)
        cleaned = re.sub(r'^(?:the|a|an|my|your|our|their)\s+', '', cleaned, flags=re.IGNORECASE)
        type_match = re.match(
            r'^(?:list|array|set|tuple|dictionary|dict|map|collection|sequence)\s+of\s+(.+)$',
            cleaned,
            re.IGNORECASE,
        )
        if type_match:
            cleaned = type_match.group(1)
        cleaned = re.sub(r'^(?:the|a|an)\s+', '', cleaned, flags=re.IGNORECASE)
        return self._sanitize_identifier(cleaned, default="value")

    def _normalize_function_name(self, text: str) -> str:
        cleaned = text.strip()
        if re.match(r'^[A-Za-z_]\w*$', cleaned):
            return cleaned
        return self._sanitize_identifier(cleaned, default="function")

    def _normalize_class_name(self, text: str) -> str:
        cleaned = text.strip()
        if re.match(r'^[A-Za-z_]\w*$', cleaned):
            return cleaned
        identifier = self._sanitize_identifier(cleaned, default="class")
        parts = [part.capitalize() for part in identifier.split('_') if part]
        return ''.join(parts) or "ClassName"

    def _split_items(self, text: str) -> List[str]:
        if not text:
            return []
        items: List[str] = []
        buffer: List[str] = []
        in_quote: Optional[str] = None
        i = 0
        lower = text.lower()

        while i < len(text):
            ch = text[i]
            if ch in ('"', "'"):
                if in_quote == ch:
                    in_quote = None
                elif in_quote is None:
                    in_quote = ch
                buffer.append(ch)
                i += 1
                continue

            if in_quote is None:
                if ch == ',':
                    item = ''.join(buffer).strip()
                    if item:
                        items.append(item)
                    buffer = []
                    i += 1
                    continue

                if ch.isspace():
                    j = i
                    while j < len(text) and text[j].isspace():
                        j += 1
                    if lower.startswith('and', j) and (j + 3 == len(text) or text[j + 3].isspace()):
                        k = j + 3
                        while k < len(text) and text[k].isspace():
                            k += 1
                        item = ''.join(buffer).strip()
                        if item:
                            items.append(item)
                        buffer = []
                        i = k
                        continue

            buffer.append(ch)
            i += 1

        item = ''.join(buffer).strip()
        if item:
            items.append(item)
        return items

    def _collection_kind_from_text(self, text: str) -> str:
        lowered = text.lower()
        if re.search(r'\blist\b', lowered):
            return "list"
        if re.search(r'\b(dictionary|dict|map)\b', lowered):
            return "dictionary"
        return "variable"

    def _parse_say_value(self, text: str) -> str:
        cleaned = text.strip()
        if not cleaned:
            return "\"\""
        value_match = re.match(r'^(?:value|result)\s+of\s+(.+)$', cleaned, re.IGNORECASE)
        if value_match:
            return self._parse_expression(value_match.group(1))
        if (cleaned.startswith('"') and cleaned.endswith('"')) or (cleaned.startswith("'") and cleaned.endswith("'")):
            return cleaned
        if re.match(r'^-?\d+(\.\d+)?$', cleaned) or cleaned.lower() in ('true', 'false', 'none', 'null'):
            return self._parse_expression(cleaned)
        if self._is_valid_python_expr(cleaned):
            if re.match(r'^[A-Za-z_]\w*$', cleaned):
                return self._quote_string(cleaned)
            return self._parse_expression(cleaned)
        return self._quote_string(cleaned)

    def _looks_like_call_args(self, text: str) -> bool:
        lower = text.strip().lower()
        if lower.startswith((
            'is ', 'are ', 'was ', 'were ', 'has ', 'have ',
            'times ', 'plus ', 'minus ', 'divided ', 'over ', 'mod ', 'modulo ',
            'between ', 'greater ', 'less ', 'equals ', 'equal ', 'contains ',
            'starts ', 'ends ', 'and ', 'or ', 'not '
        )):
            return False
        return True

    def _maybe_parse_call_without_parens(self, text: str) -> Optional[str]:
        match = self._patterns['dot_call'].match(text)
        if not match:
            return None
        func_name = match.group(1)
        args_text = match.group(2).strip()
        if not args_text or not self._looks_like_call_args(args_text):
            return None
        args = self._parse_function_arguments(args_text)
        args_str = ', '.join(args) if args else ''
        return f"{func_name}({args_str})"

    def _parse_duration(self, value_text: str, unit_text: Optional[str]) -> str:
        value_expr = self._parse_expression(value_text)
        unit = unit_text.lower() if unit_text else "seconds"
        multipliers = {
            "ms": "0.001",
            "millisecond": "0.001",
            "milliseconds": "0.001",
            "second": "1",
            "seconds": "1",
            "minute": "60",
            "minutes": "60",
            "hour": "3600",
            "hours": "3600",
        }
        multiplier = multipliers.get(unit, "1")
        if multiplier == "1":
            return value_expr
        return f"({value_expr}) * {multiplier}"

    def _parse_collection_initializer(self, value_text: str, collection_type: str) -> str:
        if not value_text:
            return "[]" if collection_type == "list" else "{}"
        cleaned = value_text.strip()
        if cleaned.lower() in ("empty", "nothing", "none"):
            return "[]" if collection_type == "list" else "{}"
        if cleaned.startswith("[") or cleaned.startswith("{") or cleaned.startswith("("):
            return cleaned
        if collection_type == "list":
            cleaned = re.sub(
                r'^(?:with\s+)?(?:items|values|elements|entries)?\s*',
                '',
                cleaned,
                flags=re.IGNORECASE,
            )
            items = self._split_items(cleaned)
            parsed_items = [self._parse_expression(item) for item in items]
            return f"[{', '.join(parsed_items)}]" if parsed_items else "[]"
        if collection_type == "dictionary":
            cleaned = re.sub(
                r'^(?:with\s+)?(?:items|values|entries|pairs)?\s*',
                '',
                cleaned,
                flags=re.IGNORECASE,
            )
            pairs = self._split_items(cleaned)
            entries = []
            for pair in pairs:
                kv_match = re.match(r'^(.+?)\s*(?:=|:|to|->)\s*(.+)$', pair)
                if kv_match:
                    key = self._parse_value(kv_match.group(1).strip())
                    value = self._parse_expression(kv_match.group(2).strip())
                    entries.append(f"{key}: {value}")
                else:
                    key = self._parse_value(pair)
                    entries.append(f"{key}: None")
            return f"{{{', '.join(entries)}}}" if entries else "{}"
        return self._parse_expression(cleaned)

    def _should_parse_inline_action(self, text: str) -> bool:
        return (
            self._patterns['for_each'].match(text)
            or self._patterns['while_do'].match(text)
            or self._patterns['repeat_times'].match(text)
            or self._patterns['repeat_until'].match(text)
            or self._patterns['repeat_while'].match(text)
            or self._patterns['wait_sleep'].match(text)
            or self._patterns['if_return'].match(text)
            or self._patterns['if_then_inline'].match(text)
            or self._patterns['if_do_inline'].match(text)
            or self._patterns['yield'].match(text)
            or self._patterns['print_numbers'].match(text)
            or self._patterns['print'].match(text)
            or self._patterns['say_message'].match(text)
            or self._patterns['log_message'].match(text)
            or self._patterns['return'].match(text)
            or self._patterns['set_named'].match(text)
            or self._patterns['let'].match(text)
            or self._patterns['set'].match(text)
            or self._patterns['create_variable_set'].match(text)
            or self._patterns['create_variable'].match(text)
            or self._patterns['increase'].match(text)
            or self._patterns['decrease'].match(text)
            or self._patterns['append_to_list'].match(text)
            or self._patterns['prepend_to_list'].match(text)
            or self._patterns['remove_from_list'].match(text)
            or self._patterns['pop_from_list'].match(text)
            or self._patterns['clear_list'].match(text)
            or self._patterns['sort_list'].match(text)
            or self._patterns['reverse_list'].match(text)
            or self._patterns['call_function'].match(text)
            or self._patterns['call_with'].match(text)
            or self._patterns['dot_call'].match(text)
            or self._patterns['await'].match(text)
            or self._patterns['raise'].match(text)
            or self._patterns['throw'].match(text)
            or self._patterns['exit'].match(text)
        )

    def _render_block_header(
        self,
        header: str,
        all_lines: List[SourceLine],
        index: int,
        current_indent: int,
        block_type: Optional[str] = None,
        block_name: Optional[str] = None,
        block_params: Optional[List[str]] = None,
    ) -> TranspileResult:
        lines = [OutputLine(0, header)]
        if self._should_autopass(all_lines, index, current_indent):
            lines.append(OutputLine(1, "pass"))
            return TranspileResult(lines=lines, block_params=block_params)
        return TranspileResult(
            lines=lines,
            opens_block=True,
            block_type=block_type,
            block_name=block_name,
            block_params=block_params,
        )

    def _render_inline_block(
        self,
        header: str,
        action_text: str,
        current_params: Optional[List[str]] = None,
    ) -> TranspileResult:
        action_lines = self._parse_inline_action(action_text, current_params=current_params)
        if not action_lines:
            action_lines = [OutputLine(0, "pass")]
        lines = [OutputLine(0, header)]
        lines.extend([OutputLine(1 + item.indent_offset, item.text) for item in action_lines])
        return TranspileResult(lines=lines)

    def _render_inline_body(
        self,
        action_type: str,
        body_text: str,
        current_params: Optional[List[str]] = None,
    ) -> List[OutputLine]:
        if action_type == "returns":
            return [OutputLine(1, f"return {self._parse_value(body_text, current_params=current_params)}")]
        action_lines = self._parse_inline_action(body_text, current_params=current_params)
        if not action_lines:
            action_lines = [OutputLine(0, "pass")]
        return [OutputLine(1 + item.indent_offset, item.text) for item in action_lines]

    def _render_range_print(self, start_text: str, end_text: str) -> List[OutputLine]:
        start_expr = self._parse_expression(start_text)
        end_expr = self._parse_expression(end_text)
        range_end = self._increment_if_number(end_expr)
        if range_end is None:
            range_end = f"{end_expr} + 1"
        return [
            OutputLine(0, f"for number in range({start_expr}, {range_end}):"),
            OutputLine(1, "print(number)"),
        ]

    def _increment_if_number(self, value: str) -> Optional[str]:
        if re.match(r'^-?\d+$', value):
            return str(int(value) + 1)
        return None

    def _render_api_endpoint(
        self,
        path_text: str,
        method_text: str,
        return_expr: Optional[str],
        async_def: bool,
        all_lines: List[SourceLine],
        index: int,
        current_indent: int,
        endpoint_names: Set[str],
    ) -> TranspileResult:
        route = self._normalize_route(path_text)
        method = method_text.upper()
        params = self._extract_route_params(route)
        func_name = self._make_endpoint_name(method, path_text, endpoint_names)

        decorator = f"@app.route({route}, methods=[\"{method}\"])"
        def_prefix = "async def" if async_def else "def"
        header = f"{def_prefix} {func_name}({', '.join(params)}):"
        lines = [OutputLine(0, decorator), OutputLine(0, header)]

        if return_expr is not None:
            value = self._parse_value(return_expr)
            lines.append(OutputLine(1, f"return {value}"))
            return TranspileResult(lines=lines)

        if self._should_autopass(all_lines, index, current_indent):
            lines.append(OutputLine(1, "return \"\""))
            return TranspileResult(lines=lines)

        return TranspileResult(lines=lines, opens_block=True, block_type="def")

    def _normalize_route(self, path_text: str) -> str:
        path = path_text.strip()
        if (path.startswith('"') and path.endswith('"')) or (path.startswith("'") and path.endswith("'")):
            return path
        return f"\"{path}\""

    def _extract_route_params(self, route_literal: str) -> List[str]:
        route = route_literal.strip('"\'')
        return re.findall(r"<(?:[^:<>]+:)?([^<>]+)>", route)

    def _make_endpoint_name(self, method: str, path_text: str, used_names: Set[str]) -> str:
        cleaned = re.sub(r"[^\w]+", "_", path_text).strip('_')
        if not cleaned:
            cleaned = "root"
        base = f"{method.lower()}_{cleaned}"
        name = base
        counter = 2
        while name in used_names:
            name = f"{base}_{counter}"
            counter += 1
        used_names.add(name)
        return name

    def _render_class_method(
        self,
        method_name: str,
        class_name: Optional[str],
        params_text: str,
        action_type: str,
        body_text: str,
        current_class: Optional[str],
        all_lines: List[SourceLine],
        index: int,
        current_indent: int,
        is_class_method: bool = False,
        is_static_method: bool = False,
        is_instance_method: bool = False,
    ) -> TranspileResult:
        params = self._parse_parameters(params_text)
        user_params = list(params)
        action_type = action_type.strip().lower()
        body_text = body_text.strip()

        inside_target_class = current_class and (class_name is None or class_name == current_class)

        if inside_target_class:
            lines: List[OutputLine] = []
            if is_class_method:
                lines.append(OutputLine(0, "@classmethod"))
                params = ["cls"] + params
            elif is_static_method:
                lines.append(OutputLine(0, "@staticmethod"))
            else:
                params = ["self"] + params

            header = f"def {method_name}({', '.join(params)}):"
            lines.append(OutputLine(0, header))
            if body_text:
                lines.extend(
                    self._render_inline_body(
                        action_type,
                        body_text,
                        current_params=user_params,
                    )
                )
                return TranspileResult(lines=lines)
            if self._should_autopass(all_lines, index, current_indent):
                lines.append(OutputLine(1, "pass"))
                return TranspileResult(lines=lines)
            return TranspileResult(
                lines=lines,
                opens_block=True,
                block_type="def",
                block_params=user_params,
            )

        target_class = class_name or current_class
        if not target_class:
            header = f"def {method_name}({', '.join(params)}):"
            return TranspileResult(lines=[OutputLine(0, header), OutputLine(1, "pass")])

        func_name = f"_{target_class}_{method_name}"
        lines = [OutputLine(0, f"def {func_name}({', '.join(self._prefix_method_params(params, is_class_method, is_static_method))}):")]
        if body_text:
            lines.extend(
                self._render_inline_body(
                    action_type,
                    body_text,
                    current_params=user_params,
                )
            )
        else:
            lines.append(OutputLine(1, "pass"))

        if is_class_method:
            lines.append(OutputLine(0, f"{target_class}.{method_name} = classmethod({func_name})"))
        elif is_static_method:
            lines.append(OutputLine(0, f"{target_class}.{method_name} = staticmethod({func_name})"))
        else:
            lines.append(OutputLine(0, f"{target_class}.{method_name} = {func_name}"))

        return TranspileResult(lines=lines)

    def _prefix_method_params(self, params: List[str], is_class_method: bool, is_static_method: bool) -> List[str]:
        if is_static_method:
            return params
        prefix = "cls" if is_class_method else "self"
        return [prefix] + params

    def _render_property(
        self,
        prop_name: str,
        class_name: Optional[str],
        return_expr: str,
        current_class: Optional[str],
        all_lines: List[SourceLine],
        index: int,
        current_indent: int,
    ) -> TranspileResult:
        inside_target_class = current_class and (class_name is None or class_name == current_class)

        if inside_target_class:
            lines = [
                OutputLine(0, "@property"),
                OutputLine(0, f"def {prop_name}(self):"),
                OutputLine(1, f"return {self._parse_expression(return_expr)}"),
            ]
            return TranspileResult(lines=lines)

        target_class = class_name or current_class
        if not target_class:
            lines = [
                OutputLine(0, "@property"),
                OutputLine(0, f"def {prop_name}(self):"),
                OutputLine(1, f"return {self._parse_expression(return_expr)}"),
            ]
            return TranspileResult(lines=lines)

        func_name = f"_{target_class}_{prop_name}"
        lines = [
            OutputLine(0, f"def {func_name}(self):"),
            OutputLine(1, f"return {self._parse_expression(return_expr)}"),
            OutputLine(0, f"{target_class}.{prop_name} = property({func_name})"),
        ]
        return TranspileResult(lines=lines)

    def _parse_inline_action(self, action_text: str, current_params: Optional[List[str]] = None) -> List[OutputLine]:
        """Parse a single inline statement into output lines."""
        text = action_text.strip()
        if not text:
            return []

        match = self._patterns['print_numbers'].match(text)
        if match:
            return self._render_range_print(match.group(1), match.group(2))

        match = self._patterns['yield'].match(text)
        if match:
            expr = self._parse_expression(match.group(1))
            return [OutputLine(0, f"yield {expr}")]

        match = self._patterns['for_each'].match(text)
        if match:
            var = match.group(1)
            iterable = self._parse_expression(match.group(2))
            action = match.group(3).strip()
            if action:
                nested = self._parse_inline_action(action, current_params=current_params)
            else:
                nested = [OutputLine(0, "pass")]
            lines = [OutputLine(0, f"for {var} in {iterable}:")]
            lines.extend([OutputLine(1 + item.indent_offset, item.text) for item in nested])
            return lines

        match = self._patterns['repeat_times'].match(text)
        if match:
            count_expr = self._parse_expression(match.group(1))
            action = match.group(2).strip()
            if action:
                nested = self._parse_inline_action(action, current_params=current_params)
            else:
                nested = [OutputLine(0, "pass")]
            lines = [OutputLine(0, f"for _ in range({count_expr}):")]
            lines.extend([OutputLine(1 + item.indent_offset, item.text) for item in nested])
            return lines

        match = self._patterns['repeat_until'].match(text)
        if match:
            condition = self._parse_condition(match.group(1))
            action = match.group(2).strip()
            if action:
                nested = self._parse_inline_action(action, current_params=current_params)
            else:
                nested = [OutputLine(0, "pass")]
            lines = [OutputLine(0, f"while not ({condition}):")]
            lines.extend([OutputLine(1 + item.indent_offset, item.text) for item in nested])
            return lines

        match = self._patterns['repeat_while'].match(text)
        if match:
            condition = self._parse_condition(match.group(1))
            action = match.group(2).strip()
            if action:
                nested = self._parse_inline_action(action, current_params=current_params)
            else:
                nested = [OutputLine(0, "pass")]
            lines = [OutputLine(0, f"while {condition}:")]
            lines.extend([OutputLine(1 + item.indent_offset, item.text) for item in nested])
            return lines

        match = self._patterns['wait_sleep'].match(text)
        if match:
            duration = self._parse_duration(match.group(1), match.group(2))
            return [OutputLine(0, f"time.sleep({duration})")]

        match = self._patterns['while_do'].match(text)
        if match:
            condition = self._parse_condition(match.group(1))
            action = match.group(2).strip()
            if action:
                nested = self._parse_inline_action(action, current_params=current_params)
            else:
                nested = [OutputLine(0, "pass")]
            lines = [OutputLine(0, f"while {condition}:")]
            lines.extend([OutputLine(1 + item.indent_offset, item.text) for item in nested])
            return lines

        match = self._patterns['if_return'].match(text)
        if match:
            condition = self._parse_condition(match.group(1))
            value = self._parse_value(match.group(2), current_params=current_params)
            return [
                OutputLine(0, f"if {condition}:"),
                OutputLine(1, f"return {value}"),
            ]

        match = self._patterns['if_then_inline'].match(text) or self._patterns['if_do_inline'].match(text)
        if match:
            condition = self._parse_condition(match.group(1))
            nested = self._parse_inline_action(match.group(2), current_params=current_params)
            if not nested:
                nested = [OutputLine(0, "pass")]
            lines = [OutputLine(0, f"if {condition}:")]
            lines.extend([OutputLine(1 + item.indent_offset, item.text) for item in nested])
            return lines

        match = self._patterns['say_message'].match(text)
        if match:
            message = self._parse_say_value(match.group(1))
            return [OutputLine(0, f"print({message})")]

        match = self._patterns['log_message'].match(text)
        if match:
            level = match.group(1).lower()
            message = self._parse_expression(match.group(2))
            return [OutputLine(0, f"logging.{level}({message})")]

        call_expr = self._maybe_parse_call_without_parens(text)
        if call_expr:
            return [OutputLine(0, call_expr)]

        match = self._patterns['print'].match(text)
        if match:
            expr = self._parse_expression(match.group(1))
            return [OutputLine(0, f"print({expr})")]

        match = self._patterns['return'].match(text)
        if match:
            value = self._parse_value(match.group(1), current_params=current_params)
            return [OutputLine(0, f"return {value}")]

        match = self._patterns['set_named'].match(text)
        if match:
            var = self._normalize_target(match.group(1))
            value = self._parse_expression(match.group(2))
            return [OutputLine(0, f"{var} = {value}")]

        match = self._patterns['let'].match(text) or self._patterns['set'].match(text)
        if match:
            var = self._normalize_target(match.group(1))
            value = self._parse_expression(match.group(2))
            return [OutputLine(0, f"{var} = {value}")]

        match = self._patterns['increase'].match(text)
        if match:
            target = self._normalize_target(match.group(1))
            amount = self._parse_expression(match.group(2))
            return [OutputLine(0, f"{target} += {amount}")]

        match = self._patterns['decrease'].match(text)
        if match:
            target = self._normalize_target(match.group(1))
            amount = self._parse_expression(match.group(2))
            return [OutputLine(0, f"{target} -= {amount}")]

        match = self._patterns['create_variable_set'].match(text)
        if match:
            var = self._normalize_target(match.group(1))
            value_text = match.group(2)
            kind = self._collection_kind_from_text(text)
            if kind == "list":
                value = self._parse_collection_initializer(value_text, "list")
            elif kind == "dictionary":
                value = self._parse_collection_initializer(value_text, "dictionary")
            else:
                value = self._parse_expression(value_text)
            return [OutputLine(0, f"{var} = {value}")]

        match = self._patterns['create_variable'].match(text)
        if match:
            var = self._normalize_target(match.group(1))
            value_text = match.group(2)
            kind = self._collection_kind_from_text(text)
            if kind == "list":
                value = self._parse_collection_initializer(value_text, "list")
            elif kind == "dictionary":
                value = self._parse_collection_initializer(value_text, "dictionary")
            else:
                value = self._parse_expression(value_text) if value_text else "None"
            return [OutputLine(0, f"{var} = {value}")]

        match = self._patterns['append_to_list'].match(text)
        if match:
            item = self._parse_expression(match.group(1))
            target = self._normalize_expression_target(match.group(2))
            return [OutputLine(0, f"{target}.append({item})")]

        match = self._patterns['prepend_to_list'].match(text)
        if match:
            item = self._parse_expression(match.group(1))
            target = self._normalize_expression_target(match.group(2))
            return [OutputLine(0, f"{target}.insert(0, {item})")]

        match = self._patterns['remove_from_list'].match(text)
        if match:
            item = self._parse_expression(match.group(1))
            target = self._normalize_expression_target(match.group(2))
            return [OutputLine(0, f"{target}.remove({item})")]

        match = self._patterns['pop_from_list'].match(text)
        if match:
            target = self._normalize_expression_target(match.group(1))
            return [OutputLine(0, f"{target}.pop()")]

        match = self._patterns['clear_list'].match(text)
        if match:
            target = self._normalize_expression_target(match.group(1))
            return [OutputLine(0, f"{target}.clear()")]

        match = self._patterns['sort_list'].match(text)
        if match:
            target = self._normalize_expression_target(match.group(1))
            return [OutputLine(0, f"{target}.sort()")]

        match = self._patterns['reverse_list'].match(text)
        if match:
            target = self._normalize_expression_target(match.group(1))
            return [OutputLine(0, f"{target}.reverse()")]

        match = self._patterns['await'].match(text)
        if match:
            expr = self._parse_expression(match.group(1))
            return [OutputLine(0, f"await {expr}")]

        match = self._patterns['raise'].match(text) or self._patterns['throw'].match(text)
        if match:
            expr = self._parse_expression(match.group(1))
            return [OutputLine(0, f"raise {expr}")]

        match = self._patterns['exit'].match(text)
        if match:
            code_text = match.group(1)
            if code_text:
                code_expr = self._parse_expression(code_text)
                return [OutputLine(0, f"sys.exit({code_expr})")]
            return [OutputLine(0, "sys.exit(0)")]

        match = self._patterns['call_function'].match(text)
        if match:
            func_name = self._normalize_expression_target(match.group(1))
            args_text = match.group(2) if match.group(2) else ""
            args = self._parse_function_arguments(args_text) if args_text else []
            args_str = ', '.join(args) if args else ''
            return [OutputLine(0, f"{func_name}({args_str})")]

        match = self._patterns['call_with'].match(text)
        if match:
            func_name = self._normalize_expression_target(match.group(1))
            args = self._parse_function_arguments(match.group(2))
            args_str = ', '.join(args) if args else ''
            return [OutputLine(0, f"{func_name}({args_str})")]

        if self._looks_like_assignment(text):
            left, right = text.split('=', 1)
            target = self._normalize_target(left)
            value = self._parse_expression(right.strip())
            return [OutputLine(0, f"{target} = {value}")]

        return [OutputLine(0, self._parse_expression(text))]

    def _parse_parameters(self, params_text: str) -> List[str]:
        """Parse function parameters from natural English."""
        normalized = params_text.strip()
        if normalized.lower() in ('nothing', 'none', 'no parameters', 'no arguments'):
            return []

        number_match = re.match(r'^(?:the\s+)?(\w+)\s+numbers?$', normalized, re.IGNORECASE)
        if number_match:
            count_text = number_match.group(1)
            count = self._word_to_number(count_text)
            return [chr(ord('a') + i) for i in range(count)]

        params = []
        for part in re.split(r'\s+and\s+|,', normalized):
            part = part.strip()
            if not part:
                continue
            name = self._normalize_param_name(part)
            if name:
                params.append(name)
        return params

    def _parse_function_arguments(self, args_text: str) -> List[str]:
        """Parse function call arguments from natural English."""
        normalized = args_text.strip()
        if not normalized or normalized.lower() in ('nothing', 'none', 'no arguments'):
            return []

        args = self._split_items(normalized)
        parsed_args = []
        for arg in args:
            if (arg.startswith('"') and arg.endswith('"')) or (arg.startswith("'") and arg.endswith("'")):
                parsed_args.append(arg)
                continue
            kw_match = re.match(r'^(.+?)\s+(?:as|equals|=|to)\s+(.+)$', arg, re.IGNORECASE)
            if kw_match:
                key = self._normalize_param_name(kw_match.group(1))
                value = self._parse_expression(kw_match.group(2))
                parsed_args.append(f"{key}={value}")
                continue
            elif re.match(r'^-?\d+(\.\d+)?$', arg):
                parsed_args.append(arg)
            else:
                parsed_args.append(self._parse_expression(arg))

        return parsed_args

    def _parse_expression(self, expr: str) -> str:
        """Parse a natural English expression to Python."""
        expr = expr.strip()
        if not expr:
            return expr

        lower = expr.lower()
        if lower == 'true':
            return 'True'
        if lower == 'false':
            return 'False'
        if lower in ('none', 'null'):
            return 'None'
        if lower in ('one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten'):
            return str(self._word_to_number(lower))
        if lower.startswith('not '):
            return f"not {self._parse_expression(expr[4:])}"

        match = re.match(r'^(?:call|run|execute)\s+(.+?)(?:\s+with\s+(.+))?$', expr, re.IGNORECASE)
        if match:
            func_name = self._normalize_expression_target(match.group(1))
            args_text = match.group(2) if match.group(2) else ""
            args = self._parse_function_arguments(args_text) if args_text else []
            args_str = ', '.join(args) if args else ''
            return f"{func_name}({args_str})"

        match = re.match(r'^(?:value|result)\s+of\s+(.+)$', expr, re.IGNORECASE)
        if match:
            return self._parse_expression(match.group(1))

        match = re.match(r'^(?:ask|prompt|input)\s+(.+)$', expr, re.IGNORECASE)
        if match:
            prompt = self._parse_value(match.group(1))
            return f"input({prompt})"

        match = re.match(r'^(.+?)\s+(?:as|to)\s+(string|text)\s*$', expr, re.IGNORECASE)
        if match:
            return f"str({self._parse_expression(match.group(1))})"

        match = re.match(r'^(.+?)\s+(?:as|to)\s+(integer|int|whole\s+number)\s*$', expr, re.IGNORECASE)
        if match:
            return f"int({self._parse_expression(match.group(1))})"

        match = re.match(r'^(.+?)\s+(?:as|to)\s+(float|decimal|number)\s*$', expr, re.IGNORECASE)
        if match:
            return f"float({self._parse_expression(match.group(1))})"

        match = re.match(r'^(.+?)\s+(?:as|to)\s+(boolean|bool)\s*$', expr, re.IGNORECASE)
        if match:
            return f"bool({self._parse_expression(match.group(1))})"

        call_expr = self._maybe_parse_call_without_parens(expr)
        if call_expr:
            return call_expr

        match = re.match(r'^(?:length|len|size|count|number)\s+of\s+(.+)$', expr, re.IGNORECASE)
        if match:
            return f"len({self._parse_expression(match.group(1))})"

        match = re.match(r'^(?:sum|total)\s+of\s+(.+)$', expr, re.IGNORECASE)
        if match:
            items = self._split_items(match.group(1))
            if len(items) == 1:
                inner = self._parse_expression(items[0])
                return f"sum({inner})"
            parsed_items = [self._parse_expression(item) for item in items]
            return f"sum([{', '.join(parsed_items)}])"

        match = re.match(r'^(?:average|mean)\s+of\s+(.+)$', expr, re.IGNORECASE)
        if match:
            items = self._split_items(match.group(1))
            if len(items) == 1:
                inner = self._parse_expression(items[0])
                return f"(sum({inner}) / len({inner}))"
            parsed_items = [self._parse_expression(item) for item in items]
            return f"(sum([{', '.join(parsed_items)}]) / {len(parsed_items)})"

        match = re.match(r'^(?:min|minimum)\s+of\s+(.+)$', expr, re.IGNORECASE)
        if match:
            items = self._split_items(match.group(1))
            if len(items) == 1:
                return f"min({self._parse_expression(items[0])})"
            parsed_items = [self._parse_expression(item) for item in items]
            return f"min([{', '.join(parsed_items)}])"

        match = re.match(r'^(?:max|maximum)\s+of\s+(.+)$', expr, re.IGNORECASE)
        if match:
            items = self._split_items(match.group(1))
            if len(items) == 1:
                return f"max({self._parse_expression(items[0])})"
            parsed_items = [self._parse_expression(item) for item in items]
            return f"max([{', '.join(parsed_items)}])"

        match = re.match(r'^(?:uppercase|upper\s+case)\s+(?:of\s+)?(.+)$', expr, re.IGNORECASE)
        if match:
            return f"{self._parse_expression(match.group(1))}.upper()"

        match = re.match(r'^(?:lowercase|lower\s+case)\s+(?:of\s+)?(.+)$', expr, re.IGNORECASE)
        if match:
            return f"{self._parse_expression(match.group(1))}.lower()"

        match = re.match(r'^(?:title\s+case)\s+(?:of\s+)?(.+)$', expr, re.IGNORECASE)
        if match:
            return f"{self._parse_expression(match.group(1))}.title()"

        match = re.match(r'^(?:trim|strip)\s+(?:of\s+)?(.+)$', expr, re.IGNORECASE)
        if match:
            return f"{self._parse_expression(match.group(1))}.strip()"

        match = re.match(r'^(.+?)\s+does\s+not\s+contain\s+(.+)$', expr, re.IGNORECASE)
        if match:
            left = self._parse_expression(match.group(1))
            right = self._parse_expression(match.group(2))
            return f"{right} not in {left}"

        match = re.match(r'^(.+?)\s+contains\s+(.+)$', expr, re.IGNORECASE)
        if match:
            left = self._parse_expression(match.group(1))
            right = self._parse_expression(match.group(2))
            return f"{right} in {left}"

        match = re.match(r'^(.+?)\s+is\s+not\s+empty$', expr, re.IGNORECASE)
        if match:
            return f"len({self._parse_expression(match.group(1))}) != 0"

        match = re.match(r'^(.+?)\s+is\s+empty$', expr, re.IGNORECASE)
        if match:
            return f"len({self._parse_expression(match.group(1))}) == 0"

        match = re.match(r'^(.+?)\s+ends\s+with\s+(.+)$', expr, re.IGNORECASE)
        if match:
            return f"{self._parse_expression(match.group(1))}.endswith({self._parse_value(match.group(2))})"

        match = re.match(r'^(.+?)\s+starts\s+with\s+(.+)$', expr, re.IGNORECASE)
        if match:
            return f"{self._parse_expression(match.group(1))}.startswith({self._parse_value(match.group(2))})"

        match = re.match(r'^(?:minus|negative)\s+(.+)$', expr, re.IGNORECASE)
        if match:
            return f"-{self._parse_expression(match.group(1))}"

        match = re.match(r'^subtract\s+(.+?)\s+from\s+(.+)$', expr, re.IGNORECASE)
        if match:
            return f"{self._parse_expression(match.group(2))} - {self._parse_expression(match.group(1))}"

        match = re.match(r'^add\s+(.+?)\s+to\s+(.+)$', expr, re.IGNORECASE)
        if match:
            return f"{self._parse_expression(match.group(2))} + {self._parse_expression(match.group(1))}"

        match = re.match(r'^add\s+(.+?)\s+and\s+(.+)$', expr, re.IGNORECASE)
        if match:
            return f"{self._parse_expression(match.group(1))} + {self._parse_expression(match.group(2))}"

        match = re.match(r'^(.+?)\s+plus\s+(.+)$', expr, re.IGNORECASE)
        if match:
            return f"{self._parse_expression(match.group(1))} + {self._parse_expression(match.group(2))}"

        match = re.match(r'^(.+?)\s+minus\s+(.+)$', expr, re.IGNORECASE)
        if match:
            return f"{self._parse_expression(match.group(1))} - {self._parse_expression(match.group(2))}"

        match = re.match(r'^(.+?)\s+(?:times|multiplied\s+by|multiply\s+by)\s+(.+)$', expr, re.IGNORECASE)
        if match:
            return f"{self._parse_expression(match.group(1))} * {self._parse_expression(match.group(2))}"

        match = re.match(r'^(.+?)\s+(?:divided\s+by|over)\s+(.+)$', expr, re.IGNORECASE)
        if match:
            return f"{self._parse_expression(match.group(1))} / {self._parse_expression(match.group(2))}"

        match = re.match(r'^(.+?)\s+(?:mod|modulo)\s+(.+)$', expr, re.IGNORECASE)
        if match:
            return f"{self._parse_expression(match.group(1))} % {self._parse_expression(match.group(2))}"

        match = re.match(r'^(.+?)\s+(?:to\s+the\s+power\s+of|power\s+of|powered\s+by)\s+(.+)$', expr, re.IGNORECASE)
        if match:
            return f"{self._parse_expression(match.group(1))} ** {self._parse_expression(match.group(2))}"

        if (expr.startswith('"') and expr.endswith('"')) or (expr.startswith("'") and expr.endswith("'")):
            return expr

        if '+' in expr:
            parts = [p.strip() for p in expr.split('+')]
            parsed_parts = [self._parse_expression(p) for p in parts]
            return ' + '.join(parsed_parts)

        match = re.match(r'^(\w+)\s*\(([^)]*)\)$', expr)
        if match:
            return expr

        if re.match(r'^-?\d+(\.\d+)?$', expr):
            return expr

        if not self._is_valid_python_expr(expr):
            if re.match(r'^[A-Za-z_]\w*$', expr):
                return expr
            if re.search(r'\s', expr) or re.search(r'[^\w]', expr):
                return self._quote_string(expr)
            return self._quote_string(expr)
        return expr

    def _parse_condition(self, condition: str) -> str:
        """Parse a natural English condition to Python."""
        condition = condition.strip()
        if not condition:
            return condition

        if condition.lower().startswith('not '):
            return f"not ({self._parse_condition(condition[4:])})"

        match = re.match(r'^(.+?)\s+is\s+not\s+empty$', condition, re.IGNORECASE)
        if match:
            return f"len({self._parse_expression(match.group(1))}) != 0"

        match = re.match(r'^(.+?)\s+is\s+empty$', condition, re.IGNORECASE)
        if match:
            return f"len({self._parse_expression(match.group(1))}) == 0"

        match = re.match(r'^(.+?)\s+(?:does\s+not|doesn\'t)\s+contain\s+(.+)$', condition, re.IGNORECASE)
        if match:
            left = self._parse_expression(match.group(1))
            right = self._parse_expression(match.group(2))
            return f"{right} not in {left}"

        match = re.match(r'^(.+?)\s+contains\s+(.+)$', condition, re.IGNORECASE)
        if match:
            left = self._parse_expression(match.group(1))
            right = self._parse_expression(match.group(2))
            return f"{right} in {left}"

        match = re.match(r'^(.+?)\s+is\s+not\s+in\s+(.+)$', condition, re.IGNORECASE)
        if match:
            left = self._parse_expression(match.group(1))
            right = self._parse_expression(match.group(2))
            return f"{left} not in {right}"

        match = re.match(r'^(.+?)\s+is\s+in\s+(.+)$', condition, re.IGNORECASE)
        if match:
            left = self._parse_expression(match.group(1))
            right = self._parse_expression(match.group(2))
            return f"{left} in {right}"

        match = re.match(r'^(.+?)\s+has\s+(.+)$', condition, re.IGNORECASE)
        if match:
            left = self._parse_expression(match.group(1))
            right = self._parse_expression(match.group(2))
            return f"{right} in {left}"

        if re.search(r'\s+or\s+', condition, re.IGNORECASE):
            parts = re.split(r'\s+or\s+', condition, flags=re.IGNORECASE)
            parsed = [self._parse_condition(part) for part in parts]
            return ' or '.join(f"({part})" for part in parsed)

        if re.search(r'\s+and\s+', condition, re.IGNORECASE):
            protected = re.sub(
                r'(\bbetween\b[^\n]+?)\s+and\s+',
                r'\1 __between_and__ ',
                condition,
                flags=re.IGNORECASE,
            )
            parts = re.split(r'\s+and\s+', protected, flags=re.IGNORECASE)
            if len(parts) > 1:
                restored = [part.replace('__between_and__', 'and') for part in parts]
                parsed = [self._parse_condition(part) for part in restored]
                return ' and '.join(f"({part})" for part in parsed)

        match = re.match(r'^(.+?)\s+is\s+between\s+(.+?)\s+and\s+(.+)$', condition, re.IGNORECASE)
        if match:
            value = self._parse_expression(match.group(1))
            low = self._parse_expression(match.group(2))
            high = self._parse_expression(match.group(3))
            return f"{low} <= {value} <= {high}"

        match = re.match(
            r'^(.+?)\s+is\s+(?:greater|bigger|larger)\s+than\s+or\s+equal\s+to\s+(.+)$',
            condition,
            re.IGNORECASE,
        )
        if match:
            return f"{self._parse_expression(match.group(1))} >= {self._parse_expression(match.group(2))}"

        match = re.match(r'^(.+?)\s+is\s+at\s+least\s+(.+)$', condition, re.IGNORECASE)
        if match:
            return f"{self._parse_expression(match.group(1))} >= {self._parse_expression(match.group(2))}"

        match = re.match(r'^(.+?)\s+is\s+no\s+less\s+than\s+(.+)$', condition, re.IGNORECASE)
        if match:
            return f"{self._parse_expression(match.group(1))} >= {self._parse_expression(match.group(2))}"

        match = re.match(
            r'^(.+?)\s+is\s+(?:less|smaller)\s+than\s+or\s+equal\s+to\s+(.+)$',
            condition,
            re.IGNORECASE,
        )
        if match:
            return f"{self._parse_expression(match.group(1))} <= {self._parse_expression(match.group(2))}"

        match = re.match(r'^(.+?)\s+is\s+at\s+most\s+(.+)$', condition, re.IGNORECASE)
        if match:
            return f"{self._parse_expression(match.group(1))} <= {self._parse_expression(match.group(2))}"

        match = re.match(r'^(.+?)\s+is\s+no\s+more\s+than\s+(.+)$', condition, re.IGNORECASE)
        if match:
            return f"{self._parse_expression(match.group(1))} <= {self._parse_expression(match.group(2))}"

        match = re.match(r'^(.+?)\s+is\s+not\s+equal\s+to\s+(.+)$', condition, re.IGNORECASE)
        if match:
            left = self._parse_expression(match.group(1))
            right = self._parse_expression(match.group(2))
            return f"{left} != {right}"

        match = re.match(r'^(.+?)\s+does\s+not\s+equal\s+(.+)$', condition, re.IGNORECASE)
        if match:
            left = self._parse_expression(match.group(1))
            right = self._parse_expression(match.group(2))
            return f"{left} != {right}"

        match = re.match(r'^(.+?)\s+is\s+equal\s+to\s+(.+)$', condition, re.IGNORECASE)
        if match:
            left = self._parse_expression(match.group(1))
            right = self._parse_expression(match.group(2))
            return f"{left} == {right}"

        match = re.match(r'^(.+?)\s+equals\s+(.+)$', condition, re.IGNORECASE)
        if match:
            left = self._parse_expression(match.group(1))
            right = self._parse_expression(match.group(2))
            return f"{left} == {right}"

        match = re.match(r'^(.+?)\s+is\s+the\s+same\s+as\s+(.+)$', condition, re.IGNORECASE)
        if match:
            left = self._parse_expression(match.group(1))
            right = self._parse_expression(match.group(2))
            return f"{left} == {right}"

        match = re.match(r'^(.+?)\s+ends\s+with\s+(.+)$', condition, re.IGNORECASE)
        if match:
            return f"{self._parse_expression(match.group(1))}.endswith({self._parse_value(match.group(2))})"

        match = re.match(r'^(.+?)\s+starts\s+with\s+(.+)$', condition, re.IGNORECASE)
        if match:
            return f"{self._parse_expression(match.group(1))}.startswith({self._parse_value(match.group(2))})"

        match = re.match(r'^(.+?)\s+is\s+(greater|bigger|larger)\s+than\s+(.+)$', condition, re.IGNORECASE)
        if match:
            return f"{self._parse_expression(match.group(1))} > {self._parse_expression(match.group(3))}"

        match = re.match(r'^(.+?)\s+is\s+(less|smaller)\s+than\s+(.+)$', condition, re.IGNORECASE)
        if match:
            return f"{self._parse_expression(match.group(1))} < {self._parse_expression(match.group(3))}"

        match = re.match(r'^(.+?)\s+is\s+not\s+(.+)$', condition, re.IGNORECASE)
        if match:
            left = self._parse_expression(match.group(1))
            right = self._parse_expression(match.group(2))
            return f"{left} != {right}"

        match = re.match(r'^(.+?)\s+is\s+(.+)$', condition, re.IGNORECASE)
        if match:
            left = self._parse_expression(match.group(1))
            right = self._parse_expression(match.group(2))
            if right.lower() in ['true', 'false', 'none', 'null']:
                return f"{left} == {self._parse_expression(right)}"
            if right.lower() == 'empty':
                return f"len({left}) == 0"
            return f"{left} == {right}"

        return condition

    def _infer_param_aggregate(self, value: str, params: Optional[List[str]]) -> Optional[str]:
        """Infer simple aggregations like 'their sum' using available parameters."""
        if not params:
            return None
        cleaned_params = [p for p in params if p not in ("self", "cls")]
        if not cleaned_params:
            return None
        normalized = value.strip().lower()
        if not normalized:
            return None
        sum_patterns = (
            r'^(?:their|the)\s+sum\b',
            r'^(?:their|the)\s+total\b',
            r'^sum\s+of\s+them\b',
            r'^sum\s+of\s+their\b',
            r'^total\s+of\s+them\b',
        )
        for pattern in sum_patterns:
            if re.match(pattern, normalized):
                if len(cleaned_params) == 1:
                    return cleaned_params[0]
                if len(cleaned_params) == 2:
                    return f"{cleaned_params[0]} + {cleaned_params[1]}"
                return " + ".join(cleaned_params)
        return None

    def _parse_value(self, value: str, current_params: Optional[List[str]] = None) -> str:
        """Parse a value from natural English."""
        value = value.strip()

        lower = value.lower()
        if lower == 'true':
            return 'True'
        if lower == 'false':
            return 'False'
        if lower in ('none', 'null'):
            return 'None'

        if re.match(r'^-?\d+(\.\d+)?$', value):
            return value

        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            return value

        inferred = self._infer_param_aggregate(value, current_params)
        if inferred is not None:
            return inferred

        parsed = self._parse_expression(value)
        if parsed == value and not self._is_valid_python_expr(parsed):
            return self._quote_string(parsed)
        return parsed

    def _quote_string(self, value: str) -> str:
        escaped = value.replace('\\', '\\\\').replace('"', '\\"')
        return f"\"{escaped}\""

    def _is_valid_python_expr(self, expr: str) -> bool:
        try:
            ast.parse(expr, mode='eval')
            return True
        except Exception:
            return False

    def _word_to_number(self, word: str) -> int:
        """Convert word to number."""
        numbers = {
            'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
        }
        return numbers.get(word.lower(), 2)

    def _detect_libraries(self, code: str, features: Optional[Dict[str, bool]] = None) -> Set[str]:
        """Detect which libraries are being used."""
        detected = set()
        for lib, patterns in self._library_patterns.items():
            for pattern in patterns:
                if re.search(pattern, code, re.IGNORECASE):
                    detected.add(lib)
                    break
        if features and features.get("flask_app"):
            detected.add("flask")
            detected.add("os")
        return detected

    def _generate_imports(self, libraries: Set[str], features: Optional[Dict[str, bool]] = None) -> List[str]:
        """Generate import statements with proper formatting for enterprise libraries."""
        imports: List[str] = []
        stdlib = {
            'json', 'os', 'sys', 'datetime', 'time', 'csv', 're', 'logging', 'pathlib',
            'collections', 'itertools', 'functools', 'asyncio', 'threading', 'multiprocessing',
            'sqlite3', 'urllib', 'http', 'email', 'hashlib', 'base64', 'uuid', 'random',
            'math', 'statistics', 'unittest', 'configparser', 'enum', 'dataclasses', 'typing'
        }

        special_imports = {
            'datetime': "from datetime import datetime, timedelta",
            'typing': "from typing import List, Dict, Optional, Union, Any, Tuple, Callable",
            'pathlib': "from pathlib import Path",
            'collections': "from collections import defaultdict, Counter, deque",
            'itertools': "from itertools import chain, combinations, permutations",
            'functools': "from functools import wraps, lru_cache",
            'asyncio': "import asyncio",
            'unittest': "import unittest",
            'enum': "from enum import Enum",
            'dataclasses': "from dataclasses import dataclass, field",
        }

        web_frameworks = {
            'flask': "from flask import Flask, request, jsonify, render_template, send_file, send_from_directory",
            'django': "from django.http import HttpResponse, JsonResponse",
            'fastapi': "from fastapi import FastAPI, HTTPException",
            'tornado': "import tornado.web",
            'aiohttp': "import aiohttp",
        }

        databases = {
            'sqlalchemy': "from sqlalchemy import create_engine, Column, Integer, String, ForeignKey\n"
                          "from sqlalchemy.ext.declarative import declarative_base\n"
                          "from sqlalchemy.orm import sessionmaker",
            'psycopg2': "import psycopg2",
            'pymongo': "from pymongo import MongoClient",
            'redis': "import redis",
            'pymysql': "import pymysql",
        }

        data_science = {
            'pandas': "import pandas as pd",
            'numpy': "import numpy as np",
            'matplotlib': "import matplotlib.pyplot as plt",
            'seaborn': "import seaborn as sns",
        }

        http_clients = {
            'requests': "import requests",
            'httpx': "import httpx",
        }

        testing = {
            'pytest': "import pytest",
            'mock': "from unittest.mock import Mock, patch",
        }

        config = {
            'yaml': "import yaml",
            'toml': "import toml",
            'dotenv': "from dotenv import load_dotenv",
        }

        all_special = {
            **special_imports,
            **web_frameworks,
            **databases,
            **data_science,
            **http_clients,
            **testing,
            **config,
        }

        for lib in sorted(libraries):
            if lib in all_special:
                import_lines = all_special[lib].split('\n')
                imports.extend(import_lines)
            elif lib in stdlib:
                imports.append(f"import {lib}")
            else:
                imports.append(f"import {lib}")

        return imports
