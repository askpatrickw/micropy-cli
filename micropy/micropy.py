# -*- coding: utf-8 -*-

from pathlib import Path

from micropy.logger import ServiceLog
from micropy.stubs import Stub
from rshell import main as rsh
import requests
import tempfile

class MicroPy:
    """Parent class for handling setup and variables"""
    TEMPLATE = Path(__file__).parent / 'template'
    FILES = Path.home() / '.micropy'
    STUB_DIR = FILES / 'stubs'
    CREATE_STUBS = FILES / 'createstubs.py'
    CREATE_STUBS_URL = "https://git.io/fjRiM"
    STUBS = [Stub(i) for i in STUB_DIR.iterdir()]

    def __init__(self):
        setup = self.setup()
        self.log = ServiceLog('MicroPy', 'bright_blue', root=True)
        self.log.debug("\n---- MicropyCLI Session ----")
        if setup:
            self.log.info("Missing .micropy folder, created it.")

    def setup(self):
        """creates necessary directories for micropy"""
        if not self.FILES.exists():
            self.FILES.mkdir()
            return True
        return False

    def add_stub(self, path):
        """Adds stub to micropy folder

        :param str path: path of stub to add

        """
        stub_path = Path(path)
        self.log.info(f"Adding $[{stub_path.name}] to stubs...")
        stub = Stub.create_from_path(self.STUB_DIR, stub_path)
        self.STUBS.append(stub)
        self.log.success("Done!")
        return stub

    def retrieve_create_script(self):
        """Retrieves createstubs.py"""
        if self.CREATE_STUBS.exists():
            self.CREATE_STUBS.unlink()
        self.log.info("Retrieving $[createstubs.py] from $[Josverl/micropython-stubber]...")
        content = requests.get(self.CREATE_STUBS_URL)
        self.CREATE_STUBS.write_text(content.text)
        self.log.info(f"$[createstubs.py] written to {self.CREATE_STUBS}")
        self.log.success("Done!")
        return self.CREATE_STUBS

    def create_stubs(self, port):
        """Create stubs from a pyboard

        :param str port: port of pyboard

        """
        create_script = self.retrieve_create_script()
        self.log.info(f"Connecting to PyBoard @ $[{port}]...")
        rsh.ASCII_XFER = False
        rsh.connect(port)
        self.log.success("Connected!")
        dev = rsh.DEVS[0]
        self.log.info("Uploading $[createstubs.py]...")
        rsh.cp(str(create_script.absolute()), f"{dev.name_path}/{create_script.name}")
        self.log.success("Done!")
        self.log.info("Executing $[createstubs.py]")
        pyb = dev.pyb
        pyb.enter_raw_repl()
        pyb.exec("import createstubs")
        pyb.exit_raw_repl()
        self.log.success("Done!")
        self.log.info("Downloading Stubs...")
        stub_name = rsh.auto(rsh.listdir_stat, f'{dev.name_path}/stubs', show_hidden=False)[0][0]
        with tempfile.TemporaryDirectory() as tmpdir:
            rsh.rsync(f"{dev.name_path}/stubs", tmpdir, recursed=True, mirror=False, dry_run=False, print_func=lambda *args: None, sync_hidden=False)
            stub_out = Path(tmpdir) / stub_name
            self.log.info(f"Adding $[{stub_name}] to micropy stubs...")
            self.STUBS.append(Stub.create_from_path(self.STUB_DIR, stub_out))
        self.log.success("Done!")
        return self.list_stubs()


    def list_stubs(self):
        """Lists all available stubs"""
        self.log.info("$w[Available Stubs:]")
        [self.log.info(i.name) for i in self.STUBS]
        self.log.info(f"$[Total Stubs:] {len(self.STUBS)}")
        