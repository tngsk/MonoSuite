"""Small syntax primitives shared by the parser and importers."""
import re


def fence_open(line):
    match = re.fullmatch(r' {0,3}(`{3,}|~{3,})(.*)', line.rstrip('\r\n'))
    if not match or (match[1][0] == '`' and '`' in match[2]):
        return None
    return match


def fence_close(line, fence):
    return bool(re.fullmatch(r' {0,3}' + re.escape(fence[0]) + '{' + str(len(fence)) + r',}[ \t]*', line.rstrip('\r\n')))


def image_line(line):
    match = re.fullmatch(r'\s*!\[([^\]]*)\]\((.+)\)\s*', line)
    return dict(alt=match[1], source=match[2]) if match else None
