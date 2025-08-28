"""Compatibility module for Python 3.13 which removed the cgi module."""
import sys
import html
import email.utils

try:
    import cgi
    cgi  # Make linter happy
    HAS_CGI = True
except ImportError:
    HAS_CGI = False

if not HAS_CGI:
    # Minimal reimplementation of cgi.parse_header
    def parse_header(line):
        """Parse a Content-type like header.
        
        Return the main content-type and a dictionary of parameters.
        """
        parts = _parseparam(';' + line)
        key = next(parts)
        pdict = {}
        for p in parts:
            i = p.find('=')
            if i >= 0:
                name = p[:i].strip().lower()
                value = p[i+1:].strip()
                if len(value) >= 2 and value[0] == value[-1] == '"':
                    value = value[1:-1]
                    value = value.replace('\\"', '"').replace('\\\\', '\\')
                pdict[name] = value
        return key, pdict

    def _parseparam(s):
        while s.startswith(';'):
            s = s[1:]
            end = s.find(';')
            while end > 0 and (s.count('"', 0, end) - s.count('\\"', 0, end)) % 2:
                end = s.find(';', end + 1)
            if end < 0:
                end = len(s)
            f = s[:end]
            yield f.strip()
            s = s[end:]

    # Patch the cgi module
    import sys
    from types import ModuleType
    
    class CgiModule(ModuleType):
        parse_header = staticmethod(parse_header)
    
    sys.modules['cgi'] = CgiModule('cgi')
    import cgi
    cgi.parse_header = parse_header
