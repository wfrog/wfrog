import sys, StringIO


TITLE1=1
TITLE2=2
TITLE3=3
SPACE=4

def parse_mark(line):
    if line.strip().startswith("---"):
        return TITLE2
    elif line.strip() == '':
        return SPACE
    elif line.strip().startswith('[') and line.strip().endswith(']'):
        return TITLE3
    else:
        return 0

def format(line):
    if parse_mark(line) == TITLE3:
        token = line.split('[')[1].strip().split(']')[0]
        return token
    if line.strip().startswith('!'):
        token = line.strip()[1:]
        return '<b><a href="'+token+'.html">'+line.strip()+'</a></b>'
    elif line.strip().startswith('>'):
        return ''
    else:
        return line

def to_content(buffer, line):
    mark = parse_mark(line)
    if mark == TITLE2:
        return (buffer, '<h2>', '</h2>', True)
    if mark == TITLE3:
        buffer.write(format(line))
        return (buffer, '<h2>', '</h2>', True)
    if mark == SPACE:
        if not buffer.getvalue().strip() == '':
            return (buffer, '', '<br><br>', True)
        else:
            return (buffer, '', '', True)
    else:
        buffer.write(format(line))
        return (buffer, '', '', False)

def treat_line(buffer, line, output):
    if buffer == None:
        buffer = StringIO.StringIO()

    ( buffer, prefix, suffix, end ) = to_content(buffer, line)

    if end:
        output.write(prefix+buffer.getvalue()+suffix)
        output.write('\n')
        buffer = None

    return buffer

def write_header(output):
    output.write('<html><body>')


def write_footer(output):
    output.write('</body></html>')

def process(input, output):

    line = 1
    buffer = None

    write_header(output)
    while line:
        line = input.readline()
        buffer = treat_line(buffer, line, output)
    treat_line(buffer, '', output)
    write_footer(output)

process(sys.stdin, sys.stdout)
