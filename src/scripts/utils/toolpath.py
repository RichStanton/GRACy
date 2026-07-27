"""Put GRACy's bundled conda bin directories on PATH — see issue #33.

GRACy invokes its tools by absolute path (`<install>/src/conda/bin/<tool>`), so PATH is not
needed to *find* them. The problem is what those tools do internally: some bundled wrappers
shell out to bare command names. `src/conda/bin/varscan` runs plain `java`, so on a machine
with no system java it exits 127 — and because every call site uses `os.system(...)`, which
discards the exit code, the pipeline carries on and applies an empty VCF.

That is a silent-wrong-output failure, and it is not confined to SNP calling: the assembly
module's consensus steps call varscan too (assemblyQt.py 532/599/666/1005).

Prepending our own bins to PATH fixes varscan and hardens every other wrapper against the
same class of problem, without changing how any tool is invoked.
"""

import os

_BIN_DIRS = (("src", "conda", "bin"), ("src", "conda2", "bin"))


def _bin_dirs(installation_directory):
    """The conda bin directories GRACy ships, in priority order."""
    root = installation_directory.rstrip(os.sep).rstrip("/")
    return [os.path.join(root, *parts) for parts in _BIN_DIRS]


def tool_path_env(installation_directory, env=None):
    """Return a copy of `env` with GRACy's conda bins prepended to PATH.

    Use this when building the environment for a subprocess. Pass `env=None` to base it on
    the current process environment.
    """
    env = dict(os.environ if env is None else env)
    wanted = _bin_dirs(installation_directory)
    current = env.get("PATH", "")
    existing = [p for p in current.split(os.pathsep) if p and p not in wanted]
    env["PATH"] = os.pathsep.join(wanted + existing)
    return env


def ensure_tool_path(installation_directory):
    """Prepend GRACy's conda bins to this process's PATH. Idempotent.

    Call it once, early, wherever `installationDirectory` becomes known — child processes
    started afterwards inherit it.
    """
    os.environ["PATH"] = tool_path_env(installation_directory, os.environ)["PATH"]
    return os.environ["PATH"]
