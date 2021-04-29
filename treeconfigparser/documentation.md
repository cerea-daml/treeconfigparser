
This package provides the `TreeConfigParser` class, which
can be used to parse configuration files.
The options are organised using a hierarchy of sections
and can be accessed using the `TreeConfigParser.get` method.

Main usage
----------

A configuration file can be read and parsed as follows:

    >>> config = TreeConfigParser()
    >>> config.read_file(file_name)

Equivalently, one can use the `fromfile` function as follows:

    >>> config = fromfile(file_name)

Supported formats
-----------------

Currently, three formats are supported for configuration files: 
the 'py' format, the 'flat' format, and the 'cpp' format. The
'py' and 'cpp' formats support an arbitrary hierarchy depth,
while the 'flat' format only supports one level of hierarchy. 

The following option hierarchy:

    section1
        |
        - option1 = val1
    section2
        |
        - option2 = val2

can be constructed with this file under the 'flat' format:

    [section1]
    option1 = val1
    [section2]
    option2 = val2

The following option hierarchy:

    section1
        |
        - option1 = val1
        |
        - subsection11
        |   |
        |   - option2 = val2
        |
        - subsection12
        |   |
        |   - option3 = val3

can be constructed with this file under the 'py' format:

    [section1]
        option1 = val1
        [subsection11]
            option2 = val2
        [subsection12]
            option3 = val3

with this file under the 'cpp' format:

    section1.option1 = val1
    section1.subsection11.option2 = val2
    section1.subsection12.option3 = val3

and cannot be constructed under the 'flat' format. 

Comments can be included in the configuration file using a dedicated
character (usually '#'). Everything which is on the right of this
comment character is ignored by the parser.

The parser supports cross-references in the file.
For example, the following ('py'-formatted) file:

    [section1]
        option1 = a
        option2 = %section1.option1%b

is translated into the following option hierarchy:

    section1
        |
        - option1 = a
        |
        - option2 = ab

as long as the cross-reference character is set to '%'.

Access to options
-----------------

Once the file has been parsed, the options can be accessed
using the section and option names. For example, if the
option hierarchy is

    section1
        |
        - option1 = 1
        |
        - subsection11
        |   |
        |   - option2 = 2
        |
        - subsection12
        |   |
        |   - option3 = 3

then individual options can be accessed as follows:

    >>> config.get(['section1', 'option1'])
    '1'
    >>> config.get(['section1', 'subsection11', 'option2'])
    '2'
    >>> config.get(['section1', 'subsection12', 'option3'])
    '3'

Optionnaly, an option can be converted to a different type
using the `string_conversion` function:

    >>> config.get(['section1', 'option1'], to_type='int')
    1

Programmatic usage
------------------

Alternatively, options can be added to a configuration using
the `TreeConfigParser.set` method. For example, the 
following option hierarchy:

    section1
        |
        - option1 = 1
        |
        - subsection11
        |   |
        |   - option2 = 2
        |
        - subsection12
        |   |
        |   - option3 = 3

can be constructed as follows:

    >>> config = TreeConfigParser()
    >>> config.set(['section1', 'option1'], 
    ...            value='1', update_tree=True)
    >>> config.set(['section1', 'subsection11', 'option2'],
    ...            value='2', update_tree=True)
    >>> config.set(['section1', 'subsection12', 'option3'],
    ...            value='3', update_tree=True)

Many more manipulations are possible using the `TreeConfigParser` 
methods. Finally, the configuration can be written to a file using
the `TreeConfigParser.tofile` method. 

