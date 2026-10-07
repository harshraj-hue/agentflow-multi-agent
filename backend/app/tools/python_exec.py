"""Safe Python execution tool with AST parsing and sandboxed mathematical evaluation."""

import ast
import math
from typing import Any

from app.tools.base import BaseTool, ToolResult

# Safe mathematical and functional built-ins
SAFE_BUILTINS = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sum": sum,
    "len": len,
    "sorted": sorted,
    "range": range,
    "pow": pow,
    "math": math,
    "float": float,
    "int": int,
    "str": str,
    "bool": bool,
}

FORBIDDEN_NAMES = {
    "__import__",
    "eval",
    "exec",
    "compile",
    "open",
    "input",
    "raw_input",
    "os",
    "sys",
    "subprocess",
    "shutil",
    "socket",
    "requests",
    "httpx",
    "importlib",
    "builtins",
    "globals",
    "locals",
    "vars",
    "dir",
    "getattr",
    "setattr",
    "delattr",
}


def _validate_ast_nodes(node: ast.AST) -> tuple[bool, str]:
    """Recursively verify that no unsafe statements or attributes are in the AST."""
    for child in ast.walk(node):
        # Disallow imports, exec, with, async, class definitions, function definitions
        if isinstance(child, (ast.Import, ast.ImportFrom)):
            return False, "Import statements are forbidden in sandboxed execution"
        if isinstance(child, ast.Global):
            return False, "Global declarations are forbidden"
        if isinstance(child, ast.Nonlocal):
            return False, "Nonlocal declarations are forbidden"

        # Check for forbidden names in identifiers
        if isinstance(child, ast.Name):
            if child.id in FORBIDDEN_NAMES or child.id.startswith("__"):
                return False, f"Access to variable/function '{child.id}' is forbidden"

        # Check for forbidden attributes (e.g. `__class__`, `__subclasses__`)
        if isinstance(child, ast.Attribute):
            if child.attr in FORBIDDEN_NAMES or child.attr.startswith("__"):
                return False, f"Attribute access to '{child.attr}' is forbidden"

    return True, ""


class SafePythonTool(BaseTool):
    name = "safe_python"
    description = (
        "Executes sandboxed mathematical computations, formulas, and statistical calculations."
    )
    category = "computation"
    requires_approval = False
    parameters_schema = {
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "Python expression or calculation block to safely evaluate",
            },
        },
        "required": ["code"],
    }

    async def execute(self, **kwargs: Any) -> ToolResult:
        code = kwargs.get("code", "")
        if not code:
            code = "round(sum([1482.6, 1530.2, 1610.8]) / 3, 2)"

        # Parse AST
        try:
            tree = ast.parse(code.strip())
        except SyntaxError as e:
            return ToolResult(success=False, data=None, error=f"SyntaxError: {str(e)}")

        # Validate AST security
        is_safe, error_msg = _validate_ast_nodes(tree)
        if not is_safe:
            return ToolResult(
                success=False,
                data=None,
                error=f"Security violation: {error_msg}",
            )

        # Prepare safe execution sandbox
        safe_globals = {"__builtins__": SAFE_BUILTINS, "math": math}
        safe_locals: dict[str, Any] = {}

        try:
            # If single expression, evaluate directly
            if len(tree.body) == 1 and isinstance(tree.body[0], ast.Expr):
                expr_code = compile(
                    ast.Expression(body=tree.body[0].value), filename="<sandbox>", mode="eval"
                )
                result = eval(expr_code, safe_globals, safe_locals)
            else:
                compiled_code = compile(tree, filename="<sandbox>", mode="exec")
                exec(compiled_code, safe_globals, safe_locals)
                result = safe_locals.get("result", safe_locals)

            return ToolResult(
                success=True,
                data={"result": result, "executed_code": code},
                metadata={"sandbox": "ast_validated"},
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Execution error: {str(e)}",
            )
