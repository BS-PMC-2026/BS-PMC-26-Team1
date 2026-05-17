import sys
import io
import traceback
import threading

def _run_isolated(code, test_cases, return_dict):
    safe_env = {
        '__builtins__': {
            'len': len, 'print': print, 'range': range, 'int': int, 'str': str,
            'float': float, 'bool': bool, 'list': list, 'dict': dict, 'set': set,
            'tuple': tuple, 'sum': sum, 'min': min, 'max': max, 'abs': abs,
            'Exception': Exception, 'ValueError': ValueError, 'TypeError': TypeError
        }
    }
    
    try:
        exec(code, safe_env)
    except Exception as e:
        return_dict['error'] = True
        return_dict['output_log'] = f"Syntax/Compile Error:\n{str(e)}"
        return_dict['passed'] = 0
        return
        
    if 'solve' not in safe_env:
        return_dict['error'] = True
        return_dict['output_log'] = "Error: Could not find function 'solve(a, b)'. Did you rename it?"
        return_dict['passed'] = 0
        return
        
    solve_func = safe_env['solve']
    passed_count = 0
    output_log_lines = []

    for i, tc in enumerate(test_cases):
        inputs = tc.get('inputs', [])
        expected = tc.get('expected', None)
        
        captured_output = io.StringIO()
        sys.stdout = captured_output
        
        try:
            result = solve_func(*inputs)
            printed = captured_output.getvalue()
            
            if result == expected:
                passed_count += 1
                output_log_lines.append(f"Test {i+1} Passed | Inputs: {inputs} -> Got: {result}")
            else:
                output_log_lines.append(f"Test {i+1} Failed | Inputs: {inputs} -> Expected: {expected}, Got: {result}")
                
            if printed:
                output_log_lines.append(f"  [Prints]: {printed.strip()}")
                
        except Exception as e:
            output_log_lines.append(f"Test {i+1} Runtime Error: {str(e)}")
        finally:
            sys.stdout = sys.__stdout__

    return_dict['error'] = False
    return_dict['output_log'] = "\n".join(output_log_lines)
    return_dict['passed'] = passed_count

def run_student_code(code: str, test_cases: list):
    """
    Safely MVP executes python code against an array of test cases using threading
    to avoid Windows multiprocessing recursive spawning crashes.
    """
    return_dict = {}
    
    t = threading.Thread(target=_run_isolated, args=(code, test_cases, return_dict))
    t.start()
    
    # 2.0 Second Execution Timeout 
    t.join(timeout=2.0)
    
    if t.is_alive():
        return {
            "output_log": "Timeout Error: Code execution took longer than 2.0 seconds. Possible infinite loop.",
            "passed": 0,
            "total": len(test_cases)
        }
        
    return {
        "output_log": return_dict.get('output_log', 'Unknown Error'),
        "passed": return_dict.get('passed', 0),
        "total": len(test_cases)
    }


def normalize_language(language):
    """
    Normalize programming language input to a consistent internal value.
    """
    if not language:
        return "python"

    lang = str(language).strip().lower()

    aliases = {
        "py": "python",
        "python3": "python",
        "python": "python",
        "js": "javascript",
        "javascript": "javascript",
        "java": "java",
        "c++": "cpp",
        "cpp": "cpp",
        "c": "c",
    }

    return aliases.get(lang, lang)


def default_compiler_label(language=None):
    """
    Return a readable compiler/interpreter label for the selected language.
    """
    lang = normalize_language(language)

    labels = {
        "python": "Python 3.11",
        "javascript": "Node.js",
        "java": "Java JDK",
        "cpp": "G++",
        "c": "GCC",
    }

    return labels.get(lang, "Default Compiler")


def default_environment_label(language=None):
    """
    Return a readable runtime/environment label for the selected language.
    """
    lang = normalize_language(language)

    environments = {
        "python": "Python Runtime Environment",
        "javascript": "Node.js Runtime Environment",
        "java": "Java Runtime Environment",
        "cpp": "C++ Runtime Environment",
        "c": "C Runtime Environment",
    }

    return environments.get(lang, "Default Runtime Environment")
