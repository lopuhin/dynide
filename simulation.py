import pickle
import sys, os
import re
import traceback
from types import FunctionType, FileType
import copy_reg
from StringIO import StringIO

"""
 An attempt to provide hints on run-time errors in an editor like emacs

 Hit Alt+e, and you will see the output of the given function, executed with the
 same argument as it was called the last time (if is has ever been called with the
 @pickling_decorator). Or Alt+p, and it will be called with the same args, as
 butlast time. You can add and remove pickling_decorator from all functions in the
 module using commands Ctrl+c Ctrl+a and Ctrl+c Ctrl+g.
 The output will be shown in echo area or in a separate buffer. If there was an
 exception, current point will be moved to the line in this file that caused it

 TODO:
  * support for bound methods
  * refactor pickling_decorator, so that it can be more flexible in where
    to save the args of functions.

"""

storate_root = '/tmp'
root = '/home/kostia/chtd'
sys.path = [root, root + '/lib', root + '/mcxgp'] + sys.path
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

in_pickling_decorator = False

try:
    from django.http import HttpRequest
    from django.utils.decorators import MethodDecoratorAdaptor
except ImportError:
    pass


def safe_type_check(obj, type_name):
    if type_name in globals() and isinstance(obj, globals()[type_name]):
        return True


def call_fn_butlast(module_name, fn_name, fn_path):
    return call_fn(module_name, fn_name, fn_path, butlast_args = True)
    

def call_fn(module_name, fn_name, fn_path, butlast_args = False):
    ''' Call function fn_name from module_name with the same arguments as last time,
    or with the same as butlast time, if butlast_args is True '''
    try:
        from dynide.autocomplete import py_file_suffix
        striped = lambda s: s[:-len(py_file_suffix)] \
                  if s.endswith(py_file_suffix) else s
        with open('%s/%s.%s' % (storate_root, striped(module_name), fn_name),
                  'rb') as f:
            args_n_kwargs = pickle.load(f)[1 if butlast_args else 0]
            fn = getattr(__import__(module_name, globals(), locals(), fn_name), fn_name)
            if hasattr(fn, '__pickling_decorator_applied__') and \
                   not args_n_kwargs is None:
                args, kwargs = args_n_kwargs
                kwargs['__catch_errors__'] = True
                capture = StringIO()
                saved_stdout = sys.stdout
                sys.stdout = capture
                try:
                    fn(*args, **kwargs)
                except Exception as e:
                    format_exc(e, fn_path)
                else:
                    pass #print 'Return value: %s' % repr(result)
                finally:
                    sys.stdout = saved_stdout
                    print capture.getvalue().encode('utf-8')
            else:
                print 'Syntax OK'
    except IOError as e:
        print e
        try:
            __import__(module_name)
        except Exception as e:
            format_exc(e, fn_path)
        else:
            print 'Syntax OK'


def reduce_file(f):
    return file_ctor, (f.name, f.mode)

def file_ctor(filename, mode):
    f = open(filename, mode)
    return f

copy_reg.pickle(FileType, reduce_file)


def pickling_decorator(fn, _fn_name, _fn_file):
    ''' Try to pickle all arguments of the function. Also catch all exceptions, 
    print traceback and file/lineno info. But do it only when called via call_fn '''
    def inner_fn(*args, **kwargs):
        catch_errors = False
        if '__catch_errors__' in kwargs:
            catch_errors = True
            del kwargs['__catch_errors__']
        for arg in args:
             # fix to pickle django request obj
            if safe_type_check(arg, 'HttpRequest'):
                arg.user = arg.user
                arg._raw_post_data = arg._get_raw_post_data()
                arg._files = arg.FILES
                arg._get = arg.GET
                arg._request = arg.REQUEST
                arg.META['wsgi.input'] = '' 
        path = '%s/%s.%s' % (
            storate_root, get_module_name(os.path.abspath(_fn_file)), _fn_name)
        last_args_kwargs = None
        try: # first try to load butlast args
            with open(path, 'rb') as f:
                last_args_kwargs = pickle.load(f)[1]
        except IOError:
            pass
        # pickle args only if they are not the same as before
        try:
            if not pickle.dumps((args, kwargs)) == pickle.dumps(last_args_kwargs):
                with open(path, 'wb') as out:
                    pickle.dump(((args, kwargs), last_args_kwargs), out)
        except (TypeError, pickle.PickleError) as e:
            #print _fn_name, e
            if os.path.isfile(path):
                os.remove(path)
        global in_pickling_decorator
        if not in_pickling_decorator and catch_errors:
            in_pickling_decorator = True
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                format_exc(e, _fn_file)
            finally:
                in_pickling_decorator = False
        else:
            return fn(*args, **kwargs)
    # to that we can pickle functions, that have pickling_decorator applied to them
    for attr in ('__name__', '__module__'):
        setattr(inner_fn, attr, getattr(fn, attr))
    inner_fn.__pickling_decorator_applied__ = True
    return inner_fn


def disable_pickling_decorator(fn):
    fn.__pickling_decorator_disabled__ = True
    return fn


def apply_to_all_fn(globals_, file_):
    ''' Apply pickling decorator to all function in the module '''
    for name, item in globals_.iteritems():
        if isinstance(item, FunctionType) or \
               safe_type_check(item, 'MethodDecoratorAdaptor') and \
               not hasattr(item, '__pickling_decorator_disabled__'):
            globals_[name] = pickling_decorator(item, name, file_)

    
def format_exc(exception, current_file):
    ''' Print exception traceback, and, as the last string,
    file and line number where the exception occured '''
    traceback_str = traceback.format_exc(exception).strip()
    print traceback_str.strip()
    line_number = None
    norm = lambda f: os.path.abspath(f.replace('.pyc', '.py'))
    for filename, line in re.findall('File "([^"]+)", line (\d+)', traceback_str):
        if norm(filename) == norm(current_file):
            line_number = line
    if line_number:
        print '|'.join(('exception', norm(current_file), line_number)).strip()


def get_module_name(abs_path):
    ''' Get a module name of file, that should be on PYTHONPATH '''
    for path in sys.path:
        if abs_path.startswith(path):
            ext = abs_path.split('.')[-1]
            return abs_path[len(path):-len(ext)].replace('/', '.').strip('.')


def get_fn_name(abs_path, line_number):
    ''' Name of the function that is first top-level fn higher than line_number '''
    name = None
    with open(abs_path) as f:
        for i, line in enumerate(f):
            match = re.match('def (\w+)\(', line)
            if match:
                name = match.groups()[0]
            if i + 1 >= int(line_number):
                return name

            
def simulate():
    option, abs_path, call_line, _ = sys.argv[1:]
    globals()[option](get_module_name(abs_path),
                      get_fn_name(abs_path, call_line),
                      abs_path)

if __name__ == '__main__':
    if len(sys.argv) == 5:
        simulate()



