"""Flag tool calls that break a scenario arm's isolation rules (tests/scenarios.md, How to run).

The check is static: it reads the arm's recorded tool calls, never re-runs them. It resolves
relative paths against a tracked working directory (each shell call starts in the dispatching
session's directory), expands variables the call assigns, strips heredoc bodies while keeping
the commands after them, and follows files the arm wrote with a heredoc and then sourced or ran.
It follows `sh -c` strings, but cannot see inside Python or other interpreter scripts,
`find -exec`, or command substitutions; those limits are why a person adjudicates every flag
and reads every call that mentions `claude`, `codex`, or `copilot`.

Flag kinds:
- `outside-read`: a path outside the arm's run directory (reads) or outside WORKDIR (cd).
- `outside-write`: a path written outside WORKDIR, including UPSTREAM.
- `cli-prompt`: a claude/codex/copilot invocation outside the allowlist, which may send a prompt.
- `cli-session`: a bare `codex app-server`, allowed only if the JSON-RPC it was sent starts
  no turn; a person checks that.
- `cli-env`: a claude/codex/copilot invocation without its throwaway configuration variables
  exported and pointing inside WORKDIR.
- `remote-fetch`: git, curl, or wget given a remote URL; a person decides whether it is
  read-only documentation (allowed) or other remote contact.
- `relative-file-path`: a file tool given a relative path.
- `unparsed`: a shell command the tokenizer could not read.
- `sourced-unknown`: a sourced or executed file whose content the transcript does not show.
- `symlink-outside`: after the run, a symlink under WORKDIR that resolves outside the run
  directory (`symlink_flags`), which would let a later write reach a real tool home.
"""

from __future__ import annotations

import os
import re
import shlex
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

CLI_VARS = {
    "claude": ("CLAUDE_CONFIG_DIR",),
    "codex": ("CODEX_HOME",),
    "copilot": ("COPILOT_HOME", "COPILOT_CACHE_HOME"),
}
# Subcommands that manage plugins or MCP configuration and never send a prompt.
CLI_ALLOWED = {
    "claude": {"plugin", "mcp"},
    "codex": {"plugin", "mcp", "features"},
    "copilot": {"plugin", "mcp", "skill"},
}
# Subcommand pairs that run locally and send no prompt (adopted 2026-09-28, tests/scenarios.md).
CLI_LOCAL = {"codex": {("debug", "prompt-input"), ("app-server", "generate-json-schema")}}
# Global options whose next word is a value, not the subcommand.
OPTIONS_WITH_VALUE = {"--plugin-dir", "--disable", "--enable", "-c", "--config"}
HELP_WORDS = {"--version", "-V", "-v", "--help", "-h"}
PROMPT_FLAGS = {"-p", "--print", "--prompt"}
SYSTEM_PREFIXES = (
    "/dev/null",
    "/dev/stdin",
    "/dev/stdout",
    "/dev/stderr",
    "/usr/",
    "/bin/",
    "/opt/homebrew/",
)
MUTATING = {
    "mkdir",
    "rm",
    "rmdir",
    "touch",
    "mv",
    "chmod",
    "chown",
    "tee",
    "truncate",
    "tar",
    "unzip",
}
LAST_OPERAND_WRITES = {"cp", "rsync", "ln", "install"}
GIT_READ_ONLY = {
    "status",
    "log",
    "show",
    "diff",
    "rev-parse",
    "cat-file",
    "ls-tree",
    "ls-files",
    "ls-remote",
    "archive",
    "describe",
    "grep",
    "blame",
    "shortlog",
    "show-ref",
    "for-each-ref",
}
# Subcommands that only list when given no argument other than these flags.
GIT_LISTING = {
    "tag": {"-l", "--list", "-n"},
    "remote": {"-v", "--verbose"},
    "branch": {"-a", "-v", "--list", "-r"},
}
KEYWORDS = {
    "do",
    "then",
    "else",
    "elif",
    "if",
    "while",
    "until",
    "!",
    "{",
    "}",
    "time",
    "done",
    "fi",
    "for",
}
PATTERN_FIRST = {"grep", "egrep", "fgrep", "rg", "sed", "awk"}
WRAPPERS = {
    "env",
    "timeout",
    "gtimeout",
    "nohup",
    "command",
    "exec",
    "xargs",
    "perl",
    "script",
    "unbuffer",
}
REMOTE = re.compile(r"^(https?|ftp|ssh|git)://|^[\w.-]+@[\w.-]+:")
SEPARATORS = set(";&|\n()")
HEREDOC = re.compile(r"(?<!<)<<(?!<)-?\s*(?:'([^']+)'|\"([^\"]+)\"|\\?([A-Za-z_][A-Za-z0-9_]*))")
VAR = re.compile(r"\$(?:\{([A-Za-z_][A-Za-z0-9_]*)\}|([A-Za-z_][A-Za-z0-9_]*))")


@dataclass(frozen=True)
class Flag:
    call: int
    kind: str
    detail: str

    def __str__(self) -> str:
        where = f"#{self.call}" if self.call >= 0 else "after the run"
        return f"{where} {self.kind}: {self.detail}"


@dataclass
class Layout:
    """Where one arm may work. `run_dir` is the private directory holding WORKDIR and UPSTREAM;
    None for plan-2a records, whose WORKDIRs shared one parent."""

    work: str
    upstream: str | None
    run_dir: str | None
    home: str
    start_cwd: str


@dataclass
class _Shell:
    cwd: str
    env: dict[str, str] = field(default_factory=dict)
    exported: set[str] = field(default_factory=set)


def _inside(path: str, root: str | None) -> bool:
    return root is not None and (path == root or path.startswith(root.rstrip("/") + "/"))


def _norm(path: str) -> str:
    return os.path.normpath(path) if path.startswith("/") else path


def split_heredocs(command: str) -> tuple[str, list[str]]:
    """Return the command with heredoc bodies removed, and the bodies in order."""
    lines, kept, bodies = command.split("\n"), [], []
    i = 0
    while i < len(lines):
        line = lines[i]
        kept.append(line)
        i += 1
        for match in HEREDOC.finditer(line):
            delim = next(g for g in match.groups() if g)
            body = []
            while i < len(lines) and lines[i].strip() != delim:
                body.append(lines[i])
                i += 1
            i += 1  # the terminator line
            bodies.append("\n".join(body))
    return "\n".join(kept), bodies


def _tokens(text: str) -> list[str]:
    lex = shlex.shlex(text, posix=True, punctuation_chars=";&|<>()\n")
    lex.whitespace = " \t\r"
    lex.whitespace_split = True
    lex.commenters = ""
    return list(lex)


def _commands(tokens: list[str]) -> list[list[str]]:
    out, current = [], []
    for tok in tokens:
        if (
            tok
            and set(tok) <= SEPARATORS | {"<", ">"}
            and set(tok) & SEPARATORS
            and not re.fullmatch(r"[<>]+&?|&>+", tok)
        ):
            if current:
                out.append(current)
            current = []
        else:
            current.append(tok)
    if current:
        out.append(current)
    return out


class Checker:
    def __init__(self, layout: Layout) -> None:
        self.layout = layout
        self.files: dict[str, str] = {}  # heredoc bodies written to a path, by resolved path
        self.flags: list[Flag] = []
        self.index = 0

    # --- paths -----------------------------------------------------------------------------
    def expand(self, word: str, shell: _Shell) -> str | None:
        """Expand ~ and $VARS; None when a variable is unknown."""
        if word == "~" or word.startswith("~/"):
            word = shell.env.get("HOME", self.layout.home) + word[1:]
        unknown = False

        def sub(m: re.Match[str]) -> str:
            nonlocal unknown
            name = m.group(1) or m.group(2)
            if name == "PWD":
                return shell.cwd
            if name == "HOME":
                return shell.env.get("HOME", self.layout.home)
            if name in shell.env:
                return shell.env[name]
            unknown = True
            return m.group(0)

        out = VAR.sub(sub, word)
        return None if unknown else out

    def resolve(self, word: str, shell: _Shell) -> str | None:
        """An absolute, normalized path for a word that names a path, else None."""
        value = self.expand(word, shell)
        if value is None:
            return None
        value = value.removeprefix("file://")
        if value.startswith("/"):
            return _norm(value)
        if (
            value in (".", "..")
            or value.startswith(("./", "../"))
            or ("/" in value and not re.match(r"^[a-z][a-z0-9+.-]*:", value))
        ):
            return _norm(str(PurePosixPath(shell.cwd) / value))
        return None

    def check_read(self, path: str, what: str) -> None:
        lay = self.layout
        allowed = (lay.work, lay.upstream, lay.run_dir)
        if path.startswith(SYSTEM_PREFIXES) or any(_inside(path, root) for root in allowed):
            return
        self.flag("outside-read", f"{what} {path}")

    def check_write(self, path: str, what: str) -> None:
        if path.startswith("/dev/") or _inside(path, self.layout.work):
            return
        self.flag("outside-write", f"{what} {path}")

    def flag(self, kind: str, detail: str) -> None:
        item = Flag(self.index, kind, detail[:200])
        if item not in self.flags:
            self.flags.append(item)

    # --- shell -----------------------------------------------------------------------------
    def run_shell(self, command: str, shell: _Shell) -> None:
        text, bodies = split_heredocs(command)
        try:
            tokens = _tokens(text)
        except ValueError as exc:
            self.flag("unparsed", f"{exc}: {command[:120]!r}")
            return
        for words in _commands(tokens):
            self.simple(words, shell, bodies)

    def simple(self, words: list[str], shell: _Shell, bodies: list[str]) -> None:
        words = list(words)
        # redirections: collect targets, drop them from the argument list
        args, writes, heredoc = [], [], None
        i = 0
        while i < len(words):
            tok = words[i]
            if tok in (">", ">>", ">|", "&>", "&>>") and i + 1 < len(words):
                writes.append(words[i + 1])
                i += 2
            elif tok in (">&", "<&") and i + 1 < len(words):
                i += 2
            elif tok == "<" and i + 1 < len(words):
                args.append(words[i + 1])
                i += 2
            elif tok == "<<" and i + 1 < len(words):
                heredoc = bodies.pop(0) if bodies else None
                i += 2
            elif (
                re.fullmatch(r"\d+", tok)
                and i + 1 < len(words)
                and words[i + 1] in (">", ">>", ">&", "<")
            ):
                i += 1  # file-descriptor number before a redirection
            else:
                args.append(tok)
                i += 1
        for target in writes:
            path = self.resolve(target, shell)
            if path is None and target and "/" not in target and "$" not in target:
                path = _norm(str(PurePosixPath(shell.cwd) / target))  # bare file name
            if path is not None:
                self.check_write(path, "redirect to")
                if heredoc is not None:
                    self.files[path] = heredoc
        inline: dict[str, str] = {}
        if len(args) >= 3 and args[0] == "for" and args[2] == "in":
            shell.env[args[1]] = f"loop-{args[1]}"  # any value: a path segment, never a root
            return
        while args and args[0] in KEYWORDS:
            args.pop(0)
        while args and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", args[0]):
            name, value = args.pop(0).split("=", 1)
            inline[name] = self.expand(value, shell) or value
        if not args:
            shell.env.update(inline)
            return
        if args[0] == "unset":
            for item in args[1:]:
                shell.env.pop(item, None)
                shell.exported.discard(item)
            return
        if args[0] == "export":
            for item in args[1:]:
                if "=" in item:
                    name, value = item.split("=", 1)
                    shell.env[name] = self.expand(value, shell) or value
                    shell.exported.add(name)
                else:
                    shell.exported.add(item)
            return
        args = self.unwrap(args, inline)
        if not args:
            return
        name = args[0] if args[0] in (".", "..") else PurePosixPath(args[0]).name
        if name in ("cd", "pushd"):
            target = self.resolve(args[1], shell) if len(args) > 1 else self.layout.home
            if target is None:
                return
            if not (_inside(target, self.layout.work) or _inside(target, self.layout.upstream)):
                self.flag("outside-read", f"cd {target}")
            shell.cwd = target
            return
        if name in (".", "source"):
            self.follow(args[1:2], shell, shell)
            return
        if name in ("sh", "bash", "zsh") and len(args) > 2 and args[1] == "-c":
            sub = _Shell(shell.cwd, {**shell.env, **inline}, shell.exported | set(inline))
            self.run_shell(args[2], sub)
            return
        if name in ("sh", "bash", "zsh") and heredoc is not None and len(args) == 1:
            self.run_shell(heredoc, _Shell(shell.cwd, dict(shell.env), set(shell.exported)))
            return
        if name in ("sh", "bash", "zsh") and len(args) > 1 and not args[1].startswith("-"):
            self.follow(args[1:2], shell, _Shell(shell.cwd, dict(shell.env), set(shell.exported)))
        elif args[0].startswith(("/", "./", "$")) and not name.startswith("python"):
            path = self.resolve(args[0], shell)
            if path is not None and path in self.files:
                self.follow(
                    args[0:1], shell, _Shell(shell.cwd, dict(shell.env), set(shell.exported))
                )
            elif path is not None and _inside(path, self.layout.run_dir or self.layout.work):
                self.flag("sourced-unknown", args[0])  # a script whose content was never seen
        if name in ("git", "curl", "wget") and any(REMOTE.match(a) for a in args[1:]):
            # step 5: a deliberate remote fetch is contact unless it is read-only documentation
            self.flag("remote-fetch", " ".join(args)[:120])
        if name in CLI_VARS:
            self.cli(name, args[1:], shell, inline)
        self.paths(name, args, shell)

    def unwrap(self, args: list[str], inline: dict[str, str]) -> list[str]:
        """Strip wrappers such as `env -u X`, `timeout 60`, and `perl -e '... exec @ARGV'`."""
        while args and PurePosixPath(args[0]).name in WRAPPERS:
            head = PurePosixPath(args.pop(0)).name
            if head == "perl":
                if len(args) >= 2 and args[0] == "-e" and "exec @ARGV" in args[1]:
                    args = args[2:]
                    continue
                return ["perl", *args]
            while args and (
                args[0].startswith("-")
                or (head in ("timeout", "gtimeout") and re.fullmatch(r"[\d.]+[smhd]?", args[0]))
            ):
                opt = args.pop(0)
                if head == "env" and opt in ("-u", "--unset") and args:
                    inline[args.pop(0)] = ""  # removed for this command only
            while head == "env" and args and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", args[0]):
                key, value = args.pop(0).split("=", 1)
                inline[key] = value
            if head in ("timeout", "gtimeout") and args and re.fullmatch(r"[\d.]+[smhd]?", args[0]):
                args.pop(0)
            if head == "script" and args:
                args.pop(0)  # the typescript file; what follows is the command it runs
        return args

    def follow(self, operand: list[str], shell: _Shell, into: _Shell) -> None:
        if not operand:
            return
        path = self.resolve(operand[0], shell)
        if path is None or path not in self.files:
            self.flag("sourced-unknown", operand[0])
            return
        self.run_shell(self.files[path], into)

    def cli(self, tool: str, rest: list[str], shell: _Shell, inline: dict[str, str]) -> None:
        if (rest and rest[0] in {"help", *HELP_WORDS}) or HELP_WORDS & set(rest) - {"-v"}:
            return  # version or help output only (tests/scenarios.md, How to run)
        words, skip = [], False
        for w in rest:
            if skip:
                skip = False
            elif w in OPTIONS_WITH_VALUE:
                skip = True
            elif not w.startswith("-"):
                words.append(w)
        sub, sub2 = (words + [None, None])[:2]
        if tool == "codex" and sub == "sandbox" and "--" in rest:
            # `codex sandbox -- CMD` runs CMD locally under Codex's sandbox: check CMD itself
            self.simple(rest[rest.index("--") + 1 :], shell, [])
        elif (
            tool == "codex"
            and sub == "app-server"
            and sub2 is None
            and not PROMPT_FLAGS & set(rest)
        ):
            # allowed only if the JSON-RPC sent starts no turn (tests/scenarios.md step 5)
            self.flag("cli-session", f"{tool} {' '.join(rest)[:120]}")
        elif PROMPT_FLAGS & set(rest) or not (
            sub in CLI_ALLOWED[tool] or (sub, sub2) in CLI_LOCAL.get(tool, set())
        ):
            self.flag("cli-prompt", f"{tool} {' '.join(rest)[:120]}")
        for var in CLI_VARS[tool]:
            value = (
                inline[var]
                if var in inline
                else (shell.env.get(var) if var in shell.exported else None)
            )
            path = self.resolve(value, shell) if value else None
            if path is None or not _inside(path, self.layout.work):
                self.flag("cli-env", f"{tool} without {var} inside WORKDIR")

    def global_git_config(self, shell: _Shell) -> None:
        """`git config --global` writes GIT_CONFIG_GLOBAL, else ~/.gitconfig or the XDG file."""
        home, env = self.layout.home, shell.env
        if "GIT_CONFIG_GLOBAL" in shell.exported:
            targets = [env["GIT_CONFIG_GLOBAL"]]
        else:
            # an XDG_CONFIG_HOME the call did not set is the session's own, assumed real
            targets = [
                env.get("HOME", home) + "/.gitconfig",
                env.get("XDG_CONFIG_HOME", home + "/.config") + "/git/config",
            ]
        for target in targets:
            path = self.resolve(target, shell)
            self.check_write(path or target, "git config --global")

    def paths(self, name: str, args: list[str], shell: _Shell) -> None:
        if name in ("echo", "printf"):
            return  # data, not paths; their redirections were checked already
        operands = args[1:]
        if name in PATTERN_FIRST and "-e" not in operands:
            first = next((n for n, w in enumerate(operands) if not w.startswith("-")), None)
            if first is not None:
                operands = operands[:first] + operands[first + 1 :]
        # JSON, quoted text, and patterns are data, not paths
        operands = [w for w in operands if not (w[:1] in "{[" or '"' in w or " " in w or "|" in w)]
        git_cwd = None
        if name == "git":
            while len(operands) >= 2 and operands[0] in ("-C", "-c"):
                if operands[0] == "-C":
                    git_cwd = self.resolve(operands[1], shell)
                operands = operands[2:]
        resolved = [p for p in (self.resolve(w, shell) for w in operands) if p is not None]
        if name == "git":
            sub = operands[0] if operands else ""
            listing = sub in GIT_LISTING and set(operands[1:]) <= GIT_LISTING[sub]
            mutating = (
                sub not in GIT_READ_ONLY and not listing and not (sub == "tag" and "-l" in operands)
            )
            repo = git_cwd or shell.cwd
            if sub == "config" and not {"--list", "-l", "--get", "--get-all"} & set(operands):
                if "--system" in operands:
                    self.check_write("/etc/gitconfig", "git config --system")
                if "--global" in operands:
                    self.global_git_config(shell)
            if mutating:
                self.check_write(repo, f"git {sub} in")
                for p in resolved:
                    self.check_write(p, f"git {sub}")
            else:
                self.check_read(repo, f"git {sub} in")
                for p in resolved:
                    self.check_read(p, f"git {sub}")
            return
        writes_all = (
            name in MUTATING
            or (name == "sed" and any(a.startswith("-i") for a in operands))
            or (name == "perl" and any(re.fullmatch(r"-\w*i\w*", a) for a in operands))
        )
        if writes_all or name in LAST_OPERAND_WRITES:
            # a bare file name is a path here: resolve it against the working directory
            files = [w for w in operands if not w.startswith(("-", "+"))]
            if name in ("chmod", "chown") and files:
                files = files[1:]  # the mode or owner
            resolved = []
            for w in files:
                p = self.resolve(w, shell)
                if p is None and "$" not in w and "=" not in w and not w.isdigit():
                    p = _norm(str(PurePosixPath(shell.cwd) / w))
                if p is not None:
                    resolved.append(p)
        for n, p in enumerate(resolved):
            if writes_all or (name in LAST_OPERAND_WRITES and n == len(resolved) - 1):
                self.check_write(p, name)
            else:
                self.check_read(p, name)

    # --- entry -----------------------------------------------------------------------------
    def check(self, calls: list[dict]) -> list[Flag]:
        for self.index, call in enumerate(calls):
            tool, inp = call["tool"], call["input"]
            if tool == "Bash":
                self.run_shell(inp.get("command", ""), _Shell(self.layout.start_cwd))
                continue
            for key in ("file_path", "path", "notebook_path"):
                value = inp.get(key)
                if not isinstance(value, str):
                    continue
                if not value.startswith("/"):
                    self.flag("relative-file-path", f"{tool} {key}={value}")
                    continue
                path = _norm(value)
                if tool == "Write" and isinstance(inp.get("content"), str):
                    self.files[path] = inp["content"]  # a script run later is followed
                if tool in ("Write", "Edit", "NotebookEdit"):
                    self.check_write(path, tool)
                else:
                    self.check_read(path, tool)
        return self.flags


def check_calls(calls: list[dict], layout: Layout) -> list[Flag]:
    return Checker(layout).check(calls)


def symlink_flags(work: Path, run_dir: Path) -> list[Flag]:
    """Symlinks left under `work` whose targets resolve outside `run_dir` (call -1)."""
    root = run_dir.resolve()
    flags = []
    for dirpath, dirnames, filenames in os.walk(work):
        for name in dirnames + filenames:
            path = Path(dirpath) / name
            if path.is_symlink():
                target = path.resolve()
                if target != root and root not in target.parents:
                    flags.append(Flag(-1, "symlink-outside", f"{path} -> {target}"))
    return flags
