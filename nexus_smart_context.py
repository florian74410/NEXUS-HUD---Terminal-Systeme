"""NEXUS Smart Context: safe contextual lookup, never sends raw terminal lines."""
from __future__ import annotations
import json, os, re, urllib.parse, urllib.request
from dataclasses import dataclass

# Block entire hover tokens rather than attempting to sanitize only a substring.
IPV4 = re.compile(r'(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])')
IPV6 = re.compile(r'(?<!\w)(?:[a-fA-F0-9]{0,4}:){2,}[a-fA-F0-9:]*')
SENSITIVE = re.compile(r'(?i)(password|passwd|passphrase|pwd|secret|token|api[_-]?key|auth(?:orization)?|bearer|credential|private[_-]?key|user(?:name)?|login|pseudo|identifiant|\bid\b|uid|gid|session[_-]?id|client[_-]?id)')
ASSIGNMENT = re.compile(r'(?i)(?:password|passwd|passphrase|token|secret|api[_-]?key|authorization|username|user|login|pseudo|id)\s*[:=]\s*\S+')
PORT = re.compile(r'(?i)(?:\b(?:port|--port|-p|listen|bind)\s*[=: ]\s*|:)(\d{1,5})\b')
WORD = re.compile(r'[\w][\w.\-]{1,63}',re.UNICODE)

@dataclass(frozen=True)
class SafeContext:
    word:str
    query:str

def excluded(word:str, line:str='', start:int=-1, end:int=-1, known_identities=()) -> bool:
    if not word or len(word)>64 or SENSITIVE.search(word) or ASSIGNMENT.search(word):return True
    if word.casefold() in {str(i).casefold() for i in known_identities}:return True
    if IPV4.search(word) or IPV6.search(word) or '@' in word:return True
    if re.fullmatch(r'\d{1,5}',word):return True # conservative: numeric values may be ports or IDs
    if start>=0 and end>=start and line:
        for match in list(IPV4.finditer(line))+list(IPV6.finditer(line))+list(ASSIGNMENT.finditer(line))+list(PORT.finditer(line)):
            if start < match.end() and end > match.start():return True
        # A hostname/IP/username token adjacent to @, or secret assignment, is excluded.
        if (start>0 and line[start-1] in '@:') or (end<len(line) and line[end:end+1]=='@'):return True
    return False

def safe_query(word:str,line:str='',start:int=-1,end:int=-1,known_identities=()) -> SafeContext|None:
    if excluded(word,line,start,end,known_identities):return None
    # Never send raw lines: they may contain passwords, personal data, SSH hosts, IDs.
    # Only allow a short generic command keyword and a fixed language/context prefix.
    if not WORD.fullmatch(word) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{1,39}',word):return None
    return SafeContext(word,'Explique brièvement en français la commande ou notion Linux : '+word)

class ContextLookup:
    """HTTPS API. Configure a trusted JSON endpoint; no scraping or browser opening."""
    def __init__(self,endpoint=None):
        self.endpoint=endpoint or os.environ.get('NEXUS_CONTEXT_ENDPOINT','')
    def lookup(self,context:SafeContext) -> str:
        if not self.endpoint.startswith('https://'):
            return 'Service HTTPS non configuré.'
        # User-configured endpoint expected to return JSON {"summary": "..."}.
        query=urllib.parse.urlencode({'q':context.query,'lang':'fr'})
        url=self.endpoint+('&' if '?' in self.endpoint else '?') +query
        request=urllib.request.Request(url,headers={'Accept':'application/json','User-Agent':'NEXUS-Terminal/1.3'})
        with urllib.request.urlopen(request,timeout=6) as response:
            if response.status!=200:raise ValueError('Réponse HTTP '+str(response.status))
            payload=response.read(16384)
        data=json.loads(payload.decode('utf-8'))
        summary=data.get('summary','') if isinstance(data,dict) else ''
        return str(summary).strip()[:280] or 'Aucune explication disponible.'
