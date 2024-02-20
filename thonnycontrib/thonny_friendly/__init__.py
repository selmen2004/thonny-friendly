from thonny.languages import tr
import os.path
import re
import subprocess
from logging import getLogger
from typing import Iterable

from thonny import  get_workbench, ui_utils
from thonny.assistance import SubprocessProgramAnalyzer, add_program_analyzer
from thonny.running import get_front_interpreter_for_subprocess

from thonny.config_ui import ConfigurationPage

logger = getLogger(__name__)


class FriendlyAnalyzer(SubprocessProgramAnalyzer):
    def is_enabled(self):
        return get_workbench().get_option("assistance.use_friendly")

    def start_analysis(self, main_file_path, imported_file_paths: Iterable[str]) -> None:
        self.interesting_files = [main_file_path] + list(imported_file_paths)

        args = [
            get_front_interpreter_for_subprocess(),
            "-m",
            "friendly_traceback",
            "--formatter",
            "thonnycontrib.thonny_friendly.parser.parseable",
            "--lang",
            "fr",
#            "--ignore-missing-imports",
#            "--check-untyped-defs",
#            "--warn-redundant-casts",
#            "--warn-unused-ignores",
#            "--show-column-numbers",
            main_file_path,
        ] + list(imported_file_paths)

        logger.debug("Running friendly: %s", " ".join(args))

        # TODO: ignore "... need type annotation" messages



        env = os.environ.copy()
        mypypath = get_workbench().get_option("assistance.mypypath")
        if mypypath:
            env["MYPYPATH"] = mypypath

        self._proc = ui_utils.popen_with_ui_thread_callback(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            env=env,
            on_completion=self._parse_and_output_warnings,
            # Specify a cwd which is not ancestor of user files.
            # This gives absolute filenames in the output.
            # Note that mypy doesn't accept when cwd is sys.prefix
            # or dirname(sys.executable)
            cwd=os.path.dirname(__file__),
        )

    def _parse_and_output_warnings(self, pylint_proc, out_lines, err_lines):
        if err_lines:
            logger.warning("Friendly: " + "".join(err_lines))
            print("Friendly errors: " + "".join(err_lines))
        if out_lines:
            logger.warning("Friendly out: " + "".join(out_lines))
            print ("Friendly out: " + "".join(out_lines))
        warnings=[]
        file_name = None
        line_number = None
        for line in  "".join(out_lines).split('\n\n') + "".join(err_lines).split('\n\n'):
            atts = {
                "filename": file_name,
                "explanation": None,
                "lineno": line_number,
                "kind": "warning",
                "title": "Warning",
                "msg": "Warning",
                "group": "0",
                "col_offset": 0,
                "symbol": "friendly-warning"
            }
            if "Simulated Python Traceback:" in line:
                match = re.search(r'File "(.*?)", line (\d+)', line)
                if match:
                    file_name = match.group(1)
                    line_number = int(match.group(2))
                    atts['filename'] = file_name
                    atts['lineno'] = line_number
                atts['explanation'] = line.split(':', 1)[1].strip()
                atts['msg'] = "Simulated Python Traceback"
                warnings.append(atts.copy())
            elif "Shortened Traceback:" in line:
                atts['explanation'] = line.split(':', 1)[1].strip()
                atts['msg'] = "Shortened Traceback"
                warnings.append(atts.copy())
            elif "Generic:" in line:
                atts['explanation'] = line.split(':', 1)[1].strip()
                atts['msg'] = "Generic"
                warnings.append(atts.copy())
            elif "Cause:" in line:
                atts['explanation'] = line.split(':', 1)[1].strip()
                atts['msg'] = "Cause"
                warnings.append(atts.copy())
            elif "Exception Raised Header:" in line:
                atts['explanation'] = line.split(':', 1)[1].strip()
                atts['msg'] = "Exception Raised Header"
                warnings.append(atts.copy())
        """ def parse_traceback(output):
            # Define regular expressions to extract file name and line number
            file_pattern = r'File "(.*?)", line (\d+)'
            
            # Search for file name and line number in the traceback
            match = re.search(file_pattern, output)
            if match:
                file_name = match.group(1)
                line_number = int(match.group(2))
                return file_name, line_number
            else:
                return None, None
        file_name, line_number = parse_traceback("".join(out_lines))
        print(file_name, line_number)
        atts = {
                    "filename": file_name,
                    "explanation" : "".join(out_lines),
                    "lineno": line_number,
                    "kind": "a",  # always "error" ?
                    "title": "tiiitle",
                    "msg": "Explication",
                    "group": "0",
                    "helpfull":"helpfull",
                    "confusing":"confusing",
                    "col_offset": 0,
                    "symbol" : "friendly-error"

                }
        warnings.append(atts) """

        """ for line in out_lines:
            m = re.match(r"(.*?):(\d+)(:(\d+))?:(.*?):(.*)", line.strip())
            if m is not None:
                message = m.group(6).strip()
                if message == "invalid syntax":
                    continue  # user will see this as Python error

                filename = m.group(1)
                if filename not in self.interesting_files:
                    logger.warning("MyPy: " + line)
                    continue

                atts = {
                    "filename": filename,
                    "lineno": int(m.group(2)),
                    "kind": m.group(5).strip(),  # always "error" ?
                    "msg": message,
                    "group": "warnings",
                }
                if m.group(3):
                    # https://github.com/thonny/thonny/issues/598
                    atts["col_offset"] = max(int(m.group(4)) - 1, 0)

                # TODO: add better categorization and explanation
                atts["symbol"] = "mypy-" + atts["kind"]
                warnings.append(atts)
            else:
                logger.error("Can't parse MyPy line: " + line.strip())
 """
        self.completion_handler(self, warnings)

class FriendlyConfigPage(ConfigurationPage):
    def __init__(self, master):
        super().__init__(master)
        self.add_checkbox("assistance.use_friendly","Friendly", row=4, columnspan=2,tooltip="Afficher les suggestions Friendly")


def load_plugin():
    add_program_analyzer(FriendlyAnalyzer)
    get_workbench().set_default("assistance.use_friendly", True)
    get_workbench().add_configuration_page("friendly", tr("Friendly"), FriendlyConfigPage, 90)
    

