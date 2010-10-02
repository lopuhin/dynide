Dynamic IDE for Python
======================

The main idea is to use run-time information to make life of developer easier in
such aspects as:
 * debugging in the editor, when you can evalute the function or the method
   you are writing with the same arguments as before. So you can invoke it once for
   real, and then invoke it in the editor, and see its return value and debugging output
 * smart code-completion, using run-time value information. When we know the values
   of all arguments of the function, we can invoke part of the function to determine
   the values of local variables, and provide accurate information on avalible methods


Dynamic debugging
-----------------

Python module is connected with the editor (emacs, but it should be easy to write
bindings to other editsor as well) via a very simple interface - editor invokes
python script with 4 args - option (currently "call_fn" | "call_fn_butlast"),
absolute path to the file, line number of cursor, and position in line.
The script determines
in which function the cursor is, checks if if knows any aruments to this function.
If there are, it invokes the function with the given argument, prints all output from
the function, and its return value. If there is an exception (even a syntax error),
it prints the stacktrace, and enough information for the editor to jump to the place
of the exception in the current file. If the function has no known arguments,
then the script just imports given file, and again lets the editor jump to the line
of the error in the file.


How are the arguments of the functions recorded
-----------------------------------------------

The function arguments are recorded via function decorator simulation.pickling_decorator

TODO - continue

Smart auto-complete
-------------------

Smart auto-complete uses full run-time information, so it has informations of actual
values of objects and can provide completion variants based on them.
The main idea is to modify the source code and execute modified source with the last
args, like in dynamic debugging. We modify source in such a way that function is
executed as normal till it reaches the place where we want to auto-complete, and
at that place we insert an invocation of function that prints all variants to stdout
and termenates execution. So we can get auto-complete even inside list comprehensions
(but I still have to think about auto-complete in generator expressions and
lambda expressions that are not invoced in this function).

We can not modify the file beeing edited, so instead we create a copy, and apply
source modifications to it, then invoke function via simulation.py, and delete the file.
(TODO - its possible to optimize it and not make a copy of the whole file,
but maybe its not worth it).
But in order to use simulation.py via its standart interface, we need some way to
associate function from modified file with the same named function from unmodified
(perhaps, we'll just need to strip some pre-defined suffix from the name of the file
at the place where we are looking for saved function args).

The input interface is the same as the interface of simulation.py
From command line args we get action, the name of the file, line number and position in
current line, and output completion variants, one on each line.


Auto-removing of pickling decorators (or how to live well with the others)
--------------------------------------------------------------------------

In order to live well with other programmers, working on the same project with you,
and to avoid caching of input arguments to function in production usage, there is
an easy way to remove all traces of this pickling decorators, for example before
commit, or after you finished debugging some part of the system. In the editor
you just specify the directory or a file where you want to clean up,
and run the command. Another useful facility could be removing all traces before
commit, and then placing them back (but maybe we should not do it).

foo
