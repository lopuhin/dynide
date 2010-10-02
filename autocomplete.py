import sys, os
from subprocess import Popen, PIPE
import itertools


def get_expression(program, lineno):
    ''' Return an expression from line @lineno, that can span multiple lines,
    as a single line: parse , ( / { [''' 
    pass


# first some parsing stuff

ident_chars = '_1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'

def search_b(string, skip = '', stop = ''):
    ''' Search from the end of @string backward, skipping all symbols
    from @skip (or all, if not given), and stopping when we can not skip or encounter
    symbol from @stop.
    Return position in @string where the match stopped. '''
    pos = 0
    for pos, c in enumerate(reversed(string)):
        if skip and c not in skip: break
        if stop and c in stop: break
    return len(string) - pos


def search_b_balanced(string, openc, closec, level = 0):
    ''' Search from the end of @string that ends with @closec backwards, till we
    find balanced with @closec @openc.
    Return position in @string where the match stopped. '''
    stop = openc + closec
    assert string[-1] in stop
    level += 1 if string[-1] == closec else -1
    if level == 0:
        return len(string) - 1
    ind = search_b(string[:-1], stop = stop)
    assert ind > 0
    return search_b_balanced(string[:ind], openc, closec, level)


# injecting functions, printing completion variants into pyhon source code

def inject_completions(expression, pos):
    ''' Inject function, that prints all completions for symbol ending at @pos
    into @expression. @expressiong  is a full expression on one string.
    Return modified expression. '''
    # TODO - remove part of the idendifier to the right of cursor
    expr = expression[:pos] # relevant for us part of the expression
    # find out where identifier we want to complete starts
    ident_index = search_b(expr, ident_chars)
    ident = expr[ident_index:]
    # TODO - case when index == 0
    if expr[ident_index - 1] == '.': # this is a method name
        obj_index = search_b_obj(expr[:ident_index])
        return expr[:obj_index] + \
               'autocomplete._pr_methods(%s, "%s")' % (
            expr[obj_index:ident_index - 1], ident) + expression[pos:]
    else: # this is some variable
        return expr[:ident_index] + 'autocomplete._pr_vars("%s")' % ident + \
               expression[pos:]

    
def search_b_obj(expression):
    ''' Search backward to the place where object, ending at expression end, starts '''
    index = len(expression) - 1
    while expression[index] == '.':
        if expression[index - 1] == ')': # should skip all inside ()
            index = search_b_balanced(expression[:index], '(', ')')
        index = search_b(expression[:index], ident_chars) - 1 # skip an identifier
    return index + 1


# functions that print completions

completions_list_prefix = 'listing completions:' 

def print_ordered_completions(completions, start = ''):
    ''' Filtering and ordering of completions '''
    # TODO - move items starting with _ to end, and mabe list already used items first
    print completions_list_prefix
    print '\n'.join(sorted(set(c for c in completions if c.startswith(start))))
    sys.exit()
    
def _pr_methods(obj, start = ''):
    print_ordered_completions(dir(obj), start)

def _pr_vars(start):
    print_ordered_completions(itertools.chain(locals(), globals()), start)


# manipulating files and calling simulation

py_file_suffix = '_autocomplete_temp_file'
simulation_abs_path = '/home/kostia/chtd/lib/dynide/simulation.py'

def print_completions(abs_path, call_line, pos_in_line):
    ''' Print completions at given cursor pos in given file to stdout:
    In order to do it, we make a modified copy of the file by @abs_path,
    and call simulation.py as a separate process, capture its output, and remove
    the file we created. '''
    with open(abs_path) as in_file:
        lines = in_file.readlines()
    # TODO - normalize expression, if it spans multiple lines
    lines[call_line - 1] = inject_completions(lines[call_line - 1], pos_in_line)
    temp_py_file = abs_path.rsplit('.', 1)[0] + py_file_suffix + '.py'
    with open(temp_py_file, 'w') as out_file:
        out_file.writelines(lines)
    output = Popen(['python', simulation_abs_path, 'call_fn', temp_py_file,
                    str(call_line), str(pos_in_line)], stdout = PIPE).communicate()[0]
    os.unlink(temp_py_file)
    if output.startswith(completions_list_prefix):
        print output.split('\n', 1)[1].strip()


def autocomplete():
    option, abs_path, call_line, pos_in_line = sys.argv[1:]
    globals()[option](abs_path, int(call_line), int(pos_in_line))

if __name__ == '__main__':
    if len(sys.argv) == 5:
        autocomplete()
    
