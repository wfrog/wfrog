import optparse
import sys, StringIO
import re

TITLE1=1
TITLE2=2
TITLE3=3
SPACE=4
PROP=5
BULLET=6
HIDDEN=7

prop_re = re.compile('^ *[a-z]+.*\[.*\].*:$')
hidden_re = re.compile('^ [^ ]+.*$')
inline_element = re.compile('(![a-z-]*)')

def parse_mark(line):
    if line.strip().startswith("---"):
        return TITLE2
    elif line.strip() == '':
        return SPACE
    elif line.strip().startswith('[') and line.strip().endswith(']'):
        return TITLE3
    elif prop_re.match(line):
        return PROP
    elif line.strip().startswith('- '):
        return BULLET
    elif hidden_re.match(line):
        return HIDDEN
    else:
        return 0

def format_text(line):
    formatted =''
    parts = line.split("'")
    if len(parts) > 1:
        open = True
        count = len(parts)
        for part in parts:
            formatted = formatted + part
            count = count - 1
            if count > 0:
                if open:
                    formatted = formatted + '<i>'
                else:
                    formatted = formatted + '</i>'
                open = not open
        line = formatted

    tokens = inline_element.split(line)
    if len(tokens) > 1:
        for i in range(0, len(tokens)-1):
            if inline_element.match(tokens[i]):
                tokens[i] = '<a href="'+tokens[i].replace('!','')+'.html">'+tokens[i]+'</a>'
        line = ''.join(tokens)
    return line


def format(line, context={}):

    if parse_mark(line) == TITLE3:
        token = line.split('[')[1].strip().split(']')[0]
        return token
    elif line.strip().startswith('!') and not context['title-line']:
        token = line.strip()[1:]
        return '<b><a href="'+token+'.html">'+line.strip()+'</a></b>'
    elif line.strip().startswith('>'):
        return ''
    elif parse_mark(line) == PROP:
        if line.find('(optional)') > 0:
            result = '<i>'+line.replace('[', '</i>[').replace('(optional)', '')
        else:
            result = line
        result = result.strip()[:-1]
        result = result.replace('[', '</b><tt>[')
        result = result.replace(']', ']</tt>')

        return '<b>' + result + '<br>'
    elif parse_mark(line) == BULLET:
        if line.find(':') > 0:
            line = line.replace(' - ', ' - <b>')
            line = line.replace(':', '</b>:')
        return '<li>'+format_text(line.replace(' - ', ''))
    elif parse_mark(line) == HIDDEN:
        return ''
    else:
        return format_text(line)

def to_content(buffer, line, context):
    mark = parse_mark(line)
    if mark == TITLE2:
        if False and context.has_key('start_title2'): #disabled
            prefix = '<hr>'
        else:
            prefix=''
            context['start_title2']=True
        return (buffer, prefix+'<h2>', '</h2>', True)
    if mark == TITLE3:
        buffer.write(format(line))
        return (buffer, '<h2>', '</h2>', True)
    if mark == SPACE:
        if hasattr(buffer, 'bullet'):
            buffer.write('</ul>')
            return (buffer, '', '', True)
        else:
            if not buffer.getvalue().strip() == '':
                return (buffer, '', '<br><br>', True)
            else:
                return (buffer, '', '', True)
    if mark == BULLET:
        if not hasattr(buffer, 'bullet'):
            buffer.write('<ul>')
            buffer.bullet = True
        buffer.write(format(line))
        return (buffer, '', '', False)
    else:
        if context['title-line']:

            buffer.write('<h1>')
            if line.strip().find('[') > 0:
                line = line.replace('[', '</h1><tt>[')
                buffer.write(line)
                buffer.write('</tt><p/>')
            else:
                buffer.write(line)
                buffer.write('</h1>')
            context['title-line'] = False
            return (buffer, '', '', True)
        else:
            buffer.write(format(line, context))
            return (buffer, '', '', False)

def treat_line(buffer, line, output, context):
    if buffer == None:
        buffer = StringIO.StringIO()

    ( buffer, prefix, suffix, end ) = to_content(buffer, line, context)

    if end:
        output.write(prefix+buffer.getvalue()+suffix)
        output.write('\n')
        buffer = None

    return buffer

def write_header(output):
    output.write('<html><head><title>wfrog - configuration</title></head><body>')


def write_footer(output):
    output.write('</body></html>')

# TODO: footer
# Lines to hide: space instead of ' > '
def process(input, output, header='', footer='', first_line_title=False):

    line = 1
    buffer = None

    write_header(output)
    output.write(header)
    context = { 'title-line' : first_line_title }
    while line:
        line = input.readline()
        buffer = treat_line(buffer, line, output, context)
    treat_line(buffer, '', output, context)
    output.write(footer)
    write_footer(output)


def main():
    opt_parser = optparse.OptionParser()

    opt_parser.add_option("-H", "--header", dest="header", default='',
                  help="Header on generated page", metavar="HTML")
    opt_parser.add_option("-F", "--footer", dest="footer", default='',
                  help="Footer on generated page", metavar="HTML")

    opt_parser.add_option("-t", "--first-line-title", action="store_true", dest="first_line_title", help="Makes the first non empty line a main title.")

    (options, args) = opt_parser.parse_args()

    process(sys.stdin, sys.stdout, header=options.header, footer=options.footer, first_line_title=options.first_line_title)

if __name__ == "__main__":
    main()
