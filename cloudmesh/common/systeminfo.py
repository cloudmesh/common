import platform
import sys
import os
import socket
from pathlib import Path
from cloudmesh.common.util import readfile
from collections import OrderedDict
import pip
import psutil
import humanize
import re
import multiprocessing


def os_is_windows():
    """
    Checks if the os is windows

    :return: True is windows
    :rtype: bool
    """
    return platform.system() == "Windows"


# noinspection PyBroadException
def os_is_linux():
    """
    Checks if the os is linux

    :return: True is linux
    :rtype: bool
    """
    try:
        content = readfile('/etc/os-release')
        return platform.system() == "Linux" and "raspbian" not in content
    except:  # noqa: E722
        return False


def os_is_mac():
    """
    Checks if the os is macOS

    :return: True is macOS
    :rtype: bool
    """
    return platform.system() == "Darwin"


# noinspection PyBroadException
def os_is_pi():
    """
    Checks if the os is Raspberry OS

    :return: True is Raspberry OS
    :rtype: bool
    """
    try:
        content = readfile('/etc/os-release')
        return platform.system() == "Linux" and "raspbian" in content
    except:  # noqa: E722
        return False

def sys_user():
    if "COLAB_GPU" in os.environ:
        return "collab"
    try:
        if sys.platform == "win32":
            return os.environ["USERNAME"]
    except:
        pass
    try:
        return os.environ["USER"]
    except:
        pass
    try:
        if os.environ["HOME"] == "/root":
            return "root"
    except:
        pass

    return "None"


# noinspection PyPep8
def is_gitbash():
    """
    returns True if you run in a Windows gitbash

    :return: True if gitbash
    """
    try:
        exepath = os.environ['EXEPATH']
        return "Git" in exepath
    except:
        return False


def is_powershell():
    """
    True if you run in powershell

    :return: True if you run in powershell
    """
    # psutil.Process(parent_pid).name() returns -
    # cmd.exe for CMD
    # powershell.exe for powershell
    # bash.exe for git bash
    return (psutil.Process(os.getppid()).name() == "powershell.exe")


def is_cmd_exe():
    """
    return True if you run in a Windows CMD

    :return: True if you run in CMD
    """
    if is_gitbash():
        return False
    else:
        try:
            return os.environ['OS'] == 'Windows_NT'
        except:
            return False


def is_local(host):
    """
    Checks if the host is the localhost

    :param host: The hostname or ip
    :return: True if the host is the localhost
    """
    return host in ["127.0.0.1",
                    "localhost",
                    socket.gethostname(),
                    # just in case socket.gethostname() does not work  we also try the following:
                    platform.node(),
                    socket.gethostbyaddr(socket.gethostname())[0]
                    ]


def get_platform():
    if sys.platform == "darwin":
        return "macos"
    elif sys.platform == "win32":
        return "windows"
    try:
        content = readfile('/etc/os-release')
        if sys.platform == 'linux' and "raspbian" in content:
            return "raspberry"
        else:
            return sys.platform
    except:
        return sys.platform


def systeminfo(info=None, user=None, node=None):
    uname = platform.uname()
    mem = psutil.virtual_memory()

    # noinspection PyPep8
    def add_binary(value):
        try:
            r = humanize.naturalsize(value, binary=True)
        except:
            r = ""
        return r

    try:
        frequency = psutil.cpu_freq()
    except:
        frequency = None

    try:
        cores = psutil.cpu_count(logical=False)
    except:
        cores = "unkown"

    operating_system = get_platform()

    description = ""
    try:
        if operating_system == "macos":
            description = os.popen("sysctl -n machdep.cpu.brand_string").read()
        elif operating_system == "win32":
            description = platform.processor()
        elif operating_system == "linux":
            lines = readfile("/proc/cpuinfo").strip().splitlines()
            for line in lines:
                if "model name" in line:
                    description = re.sub(".*model name.*:", "", line, 1)
    except:
        pass


    data = OrderedDict({
        'cpu': description.strip(),
        'cpu_count': multiprocessing.cpu_count(),
        'cpu_threads': multiprocessing.cpu_count(),
        'cpu_cores': cores,
        'uname.system': uname.system,
        'uname.node': uname.node,
        'uname.release': uname.release,
        'uname.version': uname.version,
        'uname.machine': uname.machine,
        'uname.processor': uname.processor,
        'sys.platform': sys.platform,
        'python': sys.version,
        'python.version': sys.version.split(" ", 1)[0],
        'python.pip': pip.__version__,
        'user': sys_user(),
        'mem.percent': str(mem.percent) + " %",
        'frequency': frequency
    })
    for attribute in ["total",
                      "available",
                      "used",
                      "free",
                      "active",
                      "inactive",
                      "wired"
                      ]:
        try:
            data[f"mem.{attribute}"] = \
                humanize.naturalsize(getattr(mem, attribute), binary=True)
        except:
            pass
    # svmem(total=17179869184, available=6552825856, percent=61.9,

    if data['sys.platform'] == 'darwin':
        data['platform.version'] = platform.mac_ver()[0]
    elif data['sys.platform'] == 'win32':
        data['platform.version'] = platform.win32_ver()
    else:
        data['platform.version'] = uname.version

    try:
        release_files = Path("/etc").glob("*release")
        for filename in release_files:
            content = readfile(filename.resolve()).splitlines()
            for line in content:
                if "=" in line:
                    attribute, value = line.split("=", 1)
                    attribute = attribute.replace(" ", "")
                    data[attribute] = value
    except:
        pass
    if info is not None:
        data.update(info)
    if user is not None:
        data["user"] = user
    if node is not None:
        data["uname.node"] = node
    return dict(data)
