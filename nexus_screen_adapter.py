"""Read-only screen snapshots for local tmux-backed N3XV5 terminal panes.

This is a Python adapter, NOT a native QTermWidget patch. Only local tmux
sessions are supported. Remote SSH panes deliberately have no hover capture.
"""
from __future__ import annotations
import re
import subprocess

SESSION = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")
TOKEN = re.compile(r"[^\s|;&<>]+")
TRIM = '\"\'`(),[]{}'

class TmuxScreenAdapter:
    def __init__(self, session_name):
        self.session = session_name if isinstance(session_name,str) and SESSION.fullmatch(session_name) else None

    def snapshot(self):
        if not self.session:return None
        try:
            result=subprocess.run(
                ['tmux','capture-pane','-p','-J','-t',f'={self.session}:', '-S','0'],
                capture_output=True,text=True,timeout=0.6,check=False)
        except (OSError,subprocess.TimeoutExpired):return None
        if result.returncode:return None
        # No terminal text is logged, sent to the web, or persisted.
        return result.stdout.splitlines()

    def word_at(self,row,col,pos=None):
        lines=self.snapshot()
        if lines is None or row<0 or row>=len(lines):return None
        line=lines[row]
        if col<0 or col>=len(line):return None
        for match in TOKEN.finditer(line):
            if match.start()<=col<match.end():
                raw=match.group();word=raw.strip(TRIM)
                if not word:return None
                start=match.start()+len(raw)-len(raw.lstrip(TRIM))
                return word,line,start,start+len(word),pos
        return None
