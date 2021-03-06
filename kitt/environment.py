import inspect
import os
import re
import sys

from .utils import get_extension, get_process_output


def write_environment_yaml(path: str, **kwargs):
    """Store information about the environment into the passed YAML file"""
    assert get_extension(path) in (".yml", ".yaml")

    import yaml

    data = get_environment()
    if kwargs:
        data["user_data"] = kwargs

    # move environment to the end of the file
    if "env" in data:
        data["zzz_env"] = data["env"]
        del data["env"]

    with open(path, "w") as f:
        yaml.dump(data, f)


def get_environment():
    return {
        "args": " ".join([sys.executable] + sys.argv),
        "git": get_git_info(),
        "packages": get_packages_info(),
        "env": os.environ.copy(),
    }


def get_git_info():
    changed = get_process_output(["git", "diff", "--name-status", "HEAD"]).splitlines()
    changed = [line.strip() for line in changed]

    return {
        "branch": get_process_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]),
        "sha": get_process_output(["git", "rev-parse", "HEAD"]),
        "changes": changed,
    }


def get_packages_info():
    package_regex = re.compile(r"^(.*)==(.*)$")
    packages = {}

    for line in get_process_output(["pip", "freeze"]).splitlines():
        match = package_regex.match(line.strip())
        if match:
            packages[match.group(1)] = match.group(2)

    return packages


def get_arguments(index=0):
    """Returns arguments of a function in the current call stack.
    :param index: 0 - calling function, 1 - parent of calling function etc.
    """
    frame = inspect.currentframe()
    frames = inspect.getouterframes(frame)
    if len(frames) < index + 2:
        return None
    parent_frame = frames[index + 1]
    args = inspect.getargvalues(parent_frame.frame)
    context = {}

    def assign(names):
        for name in names:
            if name in args.locals:
                context[name] = args.locals[name]

    assign(args.args)
    assign([args.keywords])
    assign([args.varargs])
    return context
