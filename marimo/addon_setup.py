import contextlib
import io
import logging
import pkgutil
import subprocess
import sys
import threading
import traceback
from typing import Iterable, Callable, Any


def _invoke_callback(callback=None, *args):
    if callback is None:
        return
    try:
        callback(*args)
    except Exception as e:
        logging.exception("Callback failed:", exc_info=e)


class Executor:
    def __init__(self):
        self._is_running = False
        self._return_value = None
        self._exception = None
        self._process = None
        self._exit_code = -1
        self._command_line = ''

    def exec_function(self, function, *args, line_callback=None, finally_callback=None):
        class OutBuffer(io.StringIO):
            def write(self, text: str) -> int:
                _invoke_callback(line_callback, text)
                return super().write(text)

            def writelines(self, lines: Iterable[str]) -> None:
                lines_buffer = list(l for l in lines)
                for line in lines_buffer:
                    _invoke_callback(line_callback, line)
                return super().writelines(lines_buffer)

        def _run_background():
            buffer = OutBuffer()
            try:
                with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
                    self._return_value = function(*args)
            except Exception as exception:
                self._exception = exception
                self.write_exception(exception, line_callback=line_callback)
            finally:
                self._is_running = False
                _invoke_callback(finally_callback, self)

        self._is_running = True
        self._return_value = None
        self._exception = None

        thread = threading.Thread(target=_run_background)
        thread.daemon = True
        thread.start()

    @staticmethod
    def write_exception(exception: Exception, line_callback=None):
        if exception is None:
            return
        for line in (l for f in traceback.format_exception(exception) for l in f.splitlines()):
            _invoke_callback(line_callback, line)

    def exec_command(self, *args, line_callback=None, finally_callback: Callable[["Executor"], Any] = None):
        if self.is_running:
            raise ValueError(f"Process is running: pid={self._process.pid}")

        self._exit_code = -1
        self._command_line = ' '.join(args)
        self._process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        def _enqueue_output():
            encoding = sys.getdefaultencoding()
            input_text_io = self._process.stdout

            buffer: bytearray
            while self._process.poll() is None:
                for buffer in iter(input_text_io.readline, b''):
                    text = buffer.decode(encoding).rstrip()
                    _invoke_callback(line_callback, text)

            input_text_io.close()
            self._exit_code = self._process.poll()
            self._process = None

        self.exec_function(_enqueue_output, finally_callback=finally_callback)

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def return_value(self):
        return self._return_value

    @property
    def exception(self) -> Exception:
        return self._exception

    @property
    def command_line(self) -> int:
        return self._command_line

    @property
    def exit_code(self) -> int:
        return self._exit_code


class Installer(Executor):
    dependencies = [
        # For maintainable cli
        "click>=8.0,<9",
        # For python 3.8 compatibility
        "importlib_resources>=5.10.2; python_version < \"3.9\"",
        # code completion
        "jedi>=0.18.0",
        # compile markdown to html
        "markdown>=3.4,<4",
        # add features to markdown
        "pymdown-extensions>=9.0,<11",
        # syntax highlighting of code in markdown
        "pygments>=2.13,<3",
        # for reading, writing configs
        "tomlkit>= 0.12.0",
        # web server
        # - 0.22.0 introduced timeout-graceful-shutdown, which we use
        "uvicorn >= 0.22.0",
        # web framework
        # - 0.26.1 introduced lifespans, which we use
        # - starlette 0.36.0 introduced a bug
        "starlette>=0.26.1,!=0.36.0",
        # websockets for use with starlette
        "websockets >= 10.0.0,<13.0.0",
        # python <=3.10 compatibility
        "typing_extensions>=4.4.0; python_version < \"3.10\"",
        # for rst parsing
        "docutils>=0.17.0",
        # for cell formatting; if user version is not compatible, no-op
        # so no lower bound needed
        "black"
    ]

    def __init__(self):
        super().__init__()

    def get_required_modules(self) -> dict[str, bool]:
        modules = {d.split(">=")[0].strip(): False for d in self.dependencies}
        for m in pkgutil.iter_modules():
            if m.name in modules:
                modules[m.name] = True
            elif m.name == "pymdownx":
                modules["pymdown-extensions"] = True
        return modules

    def install_python_modules(self, line_callback=None, finally_callback=None):

        site_packages_path = next((p for p in sys.path if p.endswith('site-packages')), None)
        target_option = ['--target', site_packages_path] if site_packages_path else []

        self.exec_command(
            sys.executable, '-m', 'ensurepip',
            line_callback=line_callback,
            finally_callback=lambda e: e.exec_command(
                sys.executable, '-m', 'pip', 'install',
                *target_option,
                '--disable-pip-version-check',
                '--no-input',
                '--exists-action', 'i',
                *[name for name, installed in self.get_required_modules().items() if not installed],
                line_callback=line_callback, finally_callback=finally_callback
            )
        )

    def uninstall_python_modules(self, line_callback=None, finally_callback=None):
        self.exec_command(
            sys.executable, '-m', 'pip', 'uninstall',
            '--yes',
            *[name for name, installed in self.get_required_modules().items() if installed],
            line_callback=line_callback, finally_callback=finally_callback
        )

    def list_python_modules(self, line_callback=None, finally_callback=None):
        self.exec_command(
            sys.executable, '-m', 'pip', 'list', '-v',
            line_callback=line_callback, finally_callback=finally_callback
        )


class Server(Executor):
    def __init__(self):
        super().__init__()
        self._port = None

    def exec_function(self, function, *args, line_callback=None, finally_callback=None):
        def _run_background():
            try:
                self._return_value = function(*args)
            except Exception as exception:
                self._exception = exception
                self.write_exception(exception, line_callback=line_callback)
            finally:
                self._is_running = False
                _invoke_callback(finally_callback, self)

        self._is_running = True
        self._return_value = None
        self._exception = None

        thread = threading.Thread(target=_run_background)
        thread.daemon = True
        thread.start()

    def start(self, port, line_callback=None, finally_callback=None):
        def server_thread_function(port: int):
            from marimo._server.start import start
            from marimo._server.utils import find_free_port
            self._port = find_free_port(port)
            start(
                development_mode=True,
                quiet=False,
                host="",
                port=self._port,
                headless=False,
                filename=None,
                mode='edit',
                include_code=True,
                watch=False,
            )
        # self.exec_function(server_thread_function, port, line_callback=line_callback, finally_callback=finally_callback)
        thread = threading.Thread(target=server_thread_function, args=(port,))
        thread.daemon = True
        thread.start()

    def stop(self):
        raise NotImplementedError()

    @property
    def port(self):
        return self._port


installer = Installer()
server = Server()
