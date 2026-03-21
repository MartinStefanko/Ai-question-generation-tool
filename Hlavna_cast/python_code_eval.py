import ast
import json
import os
import subprocess
import tempfile


PYTHON_TIMEOUT_SECONDS = 5


def evaluate_python_code_items(items, timeout_seconds: int = PYTHON_TIMEOUT_SECONDS):
    python_practical_items = [item for item in items if _is_python_practical_item(item)]
    python_items = [_normalize_python_item(item) for item in python_practical_items if _is_auto_testable_python_item(item)]

    syntax_report = {
        "stats": {
            "items_total": len(items),
            "python_practical_items": len(python_practical_items),
            "auto_testable_items": len(python_items),
            "tested_items": 0,
            "syntax_valid_items": 0,
            "syntax_valid_percent": 0.0,
        },
        "items": [],
    }
    runtime_report = {
        "stats": {
            "items_total": len(items),
            "python_practical_items": len(python_practical_items),
            "auto_testable_items": len(python_items),
            "tested_items": 0,
            "runtime_valid_items": 0,
            "runtime_valid_percent": 0.0,
        },
        "items": [],
    }
    correctness_report = {
        "stats": {
            "items_total": len(items),
            "python_practical_items": len(python_practical_items),
            "auto_testable_items": len(python_items),
            "tested_items": 0,
            "correct_items": 0,
            "correct_items_percent": 0.0,
            "test_cases_total": 0,
            "test_cases_passed": 0,
            "test_pass_rate_percent": 0.0,
        },
        "items": [],
    }

    for item in python_items:
        syntax_result = _check_python_syntax(item["kod_riesenia"])
        syntax_report["items"].append({
            "item_id": item["id"],
            "lo_id": item["lo_id"],
            "execution_mode": item["execution_mode"],
            "syntax_valid": syntax_result["valid"],
            "error": syntax_result["error"],
        })

        syntax_report["stats"]["tested_items"] += 1
        if syntax_result["valid"]:
            syntax_report["stats"]["syntax_valid_items"] += 1

        runtime_result = _check_python_runtime(item, syntax_result["valid"], timeout_seconds)
        runtime_report["items"].append({
            "item_id": item["id"],
            "lo_id": item["lo_id"],
            "execution_mode": item["execution_mode"],
            "runtime_valid": runtime_result["valid"],
            "timed_out": runtime_result["timed_out"],
            "error": runtime_result["error"],
        })

        runtime_report["stats"]["tested_items"] += 1
        if runtime_result["valid"]:
            runtime_report["stats"]["runtime_valid_items"] += 1

        correctness_result = _check_python_correctness(item, syntax_result["valid"], timeout_seconds)
        correctness_report["items"].append({
            "item_id": item["id"],
            "lo_id": item["lo_id"],
            "execution_mode": item["execution_mode"],
            "test_cases_total": correctness_result["test_cases_total"],
            "test_cases_passed": correctness_result["test_cases_passed"],
            "at_least_one_test_passed": correctness_result["at_least_one_test_passed"],
            "error": correctness_result["error"],
        })

        correctness_report["stats"]["tested_items"] += 1
        correctness_report["stats"]["test_cases_total"] += correctness_result["test_cases_total"]
        correctness_report["stats"]["test_cases_passed"] += correctness_result["test_cases_passed"]
        if correctness_result["at_least_one_test_passed"] and correctness_result["test_cases_total"] > 0:
            correctness_report["stats"]["correct_items"] += 1

    _finalize_syntax_report(syntax_report)
    _finalize_runtime_report(runtime_report)
    _finalize_correctness_report(correctness_report)
    return syntax_report, runtime_report, correctness_report


def _normalize_python_item(item):
    return {
        "id": item.get("id"),
        "lo_id": item.get("lo_id"),
        "kod_riesenia": str(item.get("kod_riesenia", "")).strip(),
        "execution_mode": str(item.get("execution_mode", "")).strip(),
        "function_name": str(item.get("function_name", "")).strip(),
        "automaticky_testovatelna": bool(item.get("automaticky_testovatelna", False)),
        "test_cases": item.get("test_cases", []),
    }


def _is_python_practical_item(item):
    return (
        item.get("typ") == "prakticka_uloha"
        and str(item.get("jazyk", "")).strip().lower() == "python"
        and str(item.get("kod_riesenia", "")).strip()
    )


def _is_auto_testable_python_item(item):
    return _is_python_practical_item(item) and bool(item.get("automaticky_testovatelna", False))


def _check_python_syntax(code):
    try:
        ast.parse(code)
        return {"valid": True, "error": ""}
    except SyntaxError as e:
        return {"valid": False, "error": f"{e.__class__.__name__}: {e}"}


def _check_python_runtime(item, syntax_valid, timeout_seconds):
    if not syntax_valid:
        return {"valid": False, "timed_out": False, "error": "Syntax invalid."}

    stdin_data = ""
    if item["execution_mode"] == "stdin_stdout" and item["test_cases"]:
        stdin_data = str(item["test_cases"][0].get("input", ""))

    try:
        result = _run_python_code(item["kod_riesenia"], stdin_data=stdin_data, timeout_seconds=timeout_seconds)
    except subprocess.TimeoutExpired:
        return {"valid": False, "timed_out": True, "error": f"Timeout after {timeout_seconds}s."}
    except Exception as e:
        return {"valid": False, "timed_out": False, "error": f"{e.__class__.__name__}: {e}"}

    if result.returncode != 0:
        return {"valid": False, "timed_out": False, "error": (result.stderr or "").strip()}
    return {"valid": True, "timed_out": False, "error": ""}


def _check_python_correctness(item, syntax_valid, timeout_seconds):
    test_cases = item.get("test_cases", [])
    if not syntax_valid:
        return _empty_correctness("Syntax invalid.", len(test_cases))
    if not test_cases:
        return _empty_correctness("No test cases.", 0)

    passed = 0
    first_error = ""

    for test_case in test_cases:
        try:
            if item["execution_mode"] == "stdin_stdout":
                run = _run_python_code(
                    item["kod_riesenia"],
                    stdin_data=str(test_case.get("input", "")),
                    timeout_seconds=timeout_seconds,
                )
                if run.returncode != 0:
                    if not first_error:
                        first_error = (run.stderr or "").strip() or "Runtime error."
                    continue
                actual = _normalize_text_output(run.stdout)
                expected = _normalize_text_output(test_case.get("expected_output", ""))
                if actual == expected:
                    passed += 1

            elif item["execution_mode"] == "function" and item.get("function_name"):
                function_result = _run_python_function_test(
                    code=item["kod_riesenia"],
                    function_name=item["function_name"],
                    test_input=test_case.get("input", []),
                    timeout_seconds=timeout_seconds,
                )
                if not function_result["ok"]:
                    if not first_error:
                        first_error = function_result["error"]
                    continue
                if _normalize_structured_value(function_result["result"]) == _normalize_structured_value(
                    test_case.get("expected_output", "")
                ):
                    passed += 1
            else:
                if not first_error:
                    first_error = "Unsupported execution_mode."
        except subprocess.TimeoutExpired:
            if not first_error:
                first_error = f"Timeout after {timeout_seconds}s."
        except Exception as e:
            if not first_error:
                first_error = f"{e.__class__.__name__}: {e}"

    total = len(test_cases)
    return {
        "test_cases_total": total,
        "test_cases_passed": passed,
        "at_least_one_test_passed": passed > 0,
        "error": first_error,
    }


def _run_python_code(code, stdin_data="", timeout_seconds=PYTHON_TIMEOUT_SECONDS):
    with tempfile.TemporaryDirectory() as temp_dir:
        script_path = os.path.join(temp_dir, "solution.py")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(code)
        return subprocess.run(
            ["python", script_path],
            input=str(stdin_data),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            cwd=temp_dir,
        )


def _run_python_function_test(code, function_name, test_input, timeout_seconds):
    with tempfile.TemporaryDirectory() as temp_dir:
        solution_path = os.path.join(temp_dir, "solution.py")
        runner_path = os.path.join(temp_dir, "runner.py")

        with open(solution_path, "w", encoding="utf-8") as f:
            f.write(code)

        payload = json.dumps(test_input, ensure_ascii=False)
        runner_code = (
            "import json\n"
            "import solution\n"
            f"args = json.loads({json.dumps(payload, ensure_ascii=False)})\n"
            "if not isinstance(args, list):\n"
            "    args = [args]\n"
            f"result = getattr(solution, {json.dumps(function_name, ensure_ascii=False)})(*args)\n"
            "print(json.dumps(result, ensure_ascii=False))\n"
        )
        with open(runner_path, "w", encoding="utf-8") as f:
            f.write(runner_code)

        run = subprocess.run(
            ["python", runner_path],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            cwd=temp_dir,
        )
        if run.returncode != 0:
            return {"ok": False, "error": (run.stderr or "").strip() or "Runtime error.", "result": None}

        stdout = (run.stdout or "").strip()
        try:
            parsed = json.loads(stdout)
        except json.JSONDecodeError:
            parsed = stdout
        return {"ok": True, "error": "", "result": parsed}


def _normalize_text_output(value):
    return str(value).strip().replace("\r\n", "\n")


def _normalize_structured_value(value):
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except TypeError:
        return str(value).strip()


def _empty_correctness(error, test_cases_total):
    return {
        "test_cases_total": test_cases_total,
        "test_cases_passed": 0,
        "at_least_one_test_passed": False,
        "error": error,
    }


def _finalize_syntax_report(report):
    tested = report["stats"]["tested_items"]
    valid = report["stats"]["syntax_valid_items"]
    report["stats"]["syntax_valid_percent"] = round((valid / tested) * 100, 2) if tested else 0.0


def _finalize_runtime_report(report):
    tested = report["stats"]["tested_items"]
    valid = report["stats"]["runtime_valid_items"]
    report["stats"]["runtime_valid_percent"] = round((valid / tested) * 100, 2) if tested else 0.0


def _finalize_correctness_report(report):
    tested = report["stats"]["tested_items"]
    correct_items = report["stats"]["correct_items"]
    total_cases = report["stats"]["test_cases_total"]
    passed_cases = report["stats"]["test_cases_passed"]
    report["stats"]["correct_items_percent"] = round((correct_items / tested) * 100, 2) if tested else 0.0
    report["stats"]["test_pass_rate_percent"] = round((passed_cases / total_cases) * 100, 2) if total_cases else 0.0
