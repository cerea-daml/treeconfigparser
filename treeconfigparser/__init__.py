"""Custom configuration parser based on a tree.

.. include:: ./documentation.md
"""

from collections import OrderedDict
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL
from datetime import datetime

from path import Path
import numpy as np


class TreeConfigParser:
    """Configuration parser class.

    Attributes
    ----------
    tree : OrderedDict
        The tree of options. Each element is either a
        `TreeConfigParser` instance (for a subsection)
        or directly a string (for an option).
    """
    def __init__(self):
        self.tree = OrderedDict()

    def get(self, keylist, **kwargs):
        """Returns the option value.

        Uses the `string_conversion` function to convert the
        value to any type.

        Parameters
        ----------
        keylist : list of str
            The list of names which identify the option.
        **kwargs : dict
            Keyword arguments passed to the `string_conversion`
            function.

        Returns
        -------
        value
            The option value, with the requested type.

        Examples
        --------
        >>> config = TreeConfigParser()
        >>> config.set(['section1', 'subsection11', 'option1'],
        ...            value='1', update_tree=True)
        >>> config.get(['section1', 'subsection11', 'option1'])
        '1'
        >>> config.get(['section1', 'subsection11', 'option1'],
        ...            to_type='int')
        1
        """
        key = keylist[0]
        if len(keylist) > 1:
            return self.tree[key].get(keylist[1:], **kwargs)
        return string_conversion(self.tree[key], **kwargs)

    def set(self, keylist, value='', update_tree=False):
        """Sets an option value.

        Parameters
        ----------
        keylist : list of str
            The list of names which identify the option.
        value : str, optional
            The new value for the option.
        update_tree : bool, optional
            If *True*, new (sub)sections are created if necessary.

        Notes
        -----
        This method can only create new options. New sections can
        be created if they are necessary for a new option, but empty
        (sub)sections cannot be created.
        """
        key = keylist[0]
        if len(keylist) > 1:
            if update_tree and key not in self.tree:
                self.tree[key] = TreeConfigParser()
            self.tree[key].set(keylist[1:], value, update_tree)
        else:
            self.tree[key] = value

    def options(self, keylist=None):
        """Returns the list of options.

        Parameters
        ----------
        keylist : list of str, optional
            The list of names which identify the section for
            which we list the options (default: root).

        Returns
        -------
        option_list : odict_keys
            The list of options and subsections for the section.

        Examples
        --------
        >>> config = TreeConfigParser()
        >>> config.set(['option1'], value='1')
        >>> config.set(['section1', 'option2'],
        ...            value='2', update_tree=True)
        >>> config.set(['section1', 'subsection11', 'option3'],
        ...            value='3', update_tree=True)
        >>> config.options()
        odict_keys(['option1', 'section1'])
        >>> config.options(['section1'])
        odict_keys(['option2', 'subsection11'])
        """
        if keylist:
            return self.tree[keylist[0]].options(keylist[1:])
        return self.tree.keys()

    def remove_option(self, keylist):
        """Removes an option.

        Parameters
        ----------
        keylist : list of str
            The list of names which identify the option or
            subsection to remove.

        Notes
        -----
        After this option is removed, the parent section may
        be empty, but it is not removed.
        """
        key = keylist[0]
        if len(keylist) > 1:
            self.tree[key].remove_option(keylist[1:])
        else:
            del self.tree[key]

    def suboptions(self):
        """Returns the list of all (sub)options as keylists.

        Returns
        -------
        keylistlist : list of list of str
            The list of all available keylists.
            Each keylist identifies one option.

        Examples
        --------
        >>> config = TreeConfigParser()
        >>> config.set(['option1'], value='1')
        >>> config.set(['section1', 'option2'],
        ...            value='2', update_tree=True)
        >>> config.set(['section1', 'subsection11', 'option3'],
        ...            value='3', update_tree=True)
        >>> config.suboptions()
        [['option1'], ['section1', 'option2'], \
['section1', 'subsection11', 'option3']]
        """
        keylistlist = []
        for key in self.tree:
            if isinstance(self.tree[key], TreeConfigParser):
                for subkeylist in self.tree[key].suboptions():
                    keylistlist.append([key] + subkeylist)
            else:
                keylistlist.append([key])
        return keylistlist

    def merge(self, config, keylist=None, update_tree=False):
        """Merges an other configuration.

        The other configuration's options are inserted in
        the current tree, in a given section.

        Parameters
        ----------
        config : TreeConfigParser instance
            The other configuration.
        keylist : list of str, optional
            The list of names which identify the section
            in which the other configuration should be
            merged (default: root).
        update_tree : bool, optional
            If *True*, new (sub)sections are created if necessary.

        Notes
        -----
        Ensure that the section names of both configuration
        instances are compatible before merging. In case of
        conflict, the updated values are those of *config*.

        Examples
        --------
        >>> config = TreeConfigParser()
        >>> config.set(['option1'], value='1')
        >>> config.set(['section1', 'option2'], value='2',
        ...            update_tree=True)
        >>> other = TreeConfigParser()
        >>> other.set(['option2'], value='3')
        >>> other.set(['option3'], value='3')
        >>> config.merge(other, keylist=['section1'])
        >>> config.options()
        odict_keys(['option1', 'section1'])
        >>> config.options(['section1'])
        odict_keys(['option2', 'option3'])
        >>> config.get(['section1', 'option2'])
        '3'
        """
        if keylist:
            key = keylist[0]
            if update_tree and key not in self.tree:
                self.tree[key] = TreeConfigParser()
            self.tree[key].merge(config, keylist[1:], update_tree)
        else:
            for key in config.tree:
                if (key in self.tree
                        and isinstance(config.tree[key], TreeConfigParser)
                        and isinstance(self.tree[key], TreeConfigParser)):
                    self.tree[key].merge(config.tree[key],
                                         update_tree=update_tree)
                elif isinstance(config.tree[key], TreeConfigParser):
                    self.tree[key] = TreeConfigParser()
                    self.tree[key].merge(config.tree[key],
                                         update_tree=update_tree)
                else:
                    self.tree[key] = config.tree[key]

    def substitution(self, old_string, new_string, keylist=None):
        """Performs a string substitution.

        Replaces *old_string* by *new_string*. If *keylist*
        identifies an option, the substitution is applied
        only to that option. If *keylist* identifies a
        section, the substitution is applied to all
        options and subsections in that section.

        Uses the `str.replace` method.

        Parameters
        ----------
        old_string : str
            The old `str` pattern.
        new_string : str
            The new `str` pattern.
        keylist : list of str
            The list of names which identify the option
            or the section in which the substitution is applied
            (default: root).
        """
        if keylist:
            self.tree[keylist[0]].substitution(old_string, new_string,
                                               keylist[1:])
        else:
            for key in self.tree:
                if isinstance(self.tree[key], TreeConfigParser):
                    self.tree[key].substitution(old_string, new_string)
                else:
                    self.tree[key] = self.tree[key].replace(
                        old_string, new_string)

    def clone(self, keylist=None):
        """Return a copy of the (sub)configuration.

        Parameters
        ----------
        keylist : list of str, optional
            The list of names which identify the (sub)configuration
            to copy (default: root).

        Returns
        -------
        copy : TreeConfigParser instance
            The copy of the (sub)configuration.

        Examples
        --------
        >>> config = TreeConfigParser()
        >>> config.set(['section1', 'option1'], value='1',
        ...            update_tree=True)
        >>> other = config.clone(keylist=['section1'])
        >>> other.set(['option2'], value='2')
        >>> other.options()
        odict_keys(['option1', 'option2'])
        >>> config.options(['section1'])
        odict_keys(['option1'])
        """
        if keylist:
            return self.tree[keylist[0]].clone(keylist[1:])
        clone_cfg = TreeConfigParser()
        for key in self.tree:
            if isinstance(self.tree[key], TreeConfigParser):
                clone_cfg.tree[key] = self.tree[key].clone()
            else:
                clone_cfg.tree[key] = self.tree[key]
        return clone_cfg

    def subconfig(self, keylist=None):
        """Return a reference to the (sub)configuration.

        Parameters
        ----------
        keylist : list of str, optional
            The list of names which identify the (sub)configuration
            to reference (default: root).

        Returns
        -------
        copy : TreeConfigParser instance
            The reference to the (sub)configuration.

        Examples
        --------
        >>> config = TreeConfigParser()
        >>> config.set(['section1', 'option1'], value='1',
        ...            update_tree=True)
        >>> other = config.subconfig(keylist=['section1'])
        >>> other.set(['option2'], value='2')
        >>> other.options()
        odict_keys(['option1', 'option2'])
        >>> config.options(['section1'])
        odict_keys(['option1', 'option2'])
        """
        if keylist:
            return self.tree[keylist[0]].subconfig(keylist[1:])
        return self

    # pylint: disable=too-many-arguments,too-many-locals,too-many-statements
    def read_file(self,
                  file_name,
                  convention='py',
                  comment_char='#',
                  reference_char='%',
                  indentation=4):
        """Reads and parses *file_name*.

        This is the main method of the class.
        The options are inserted in the current tree.

        Parameters
        ----------
        file_name : str
            The name of the file to parse.
        convention : {'py', 'flat', 'cpp'}, optional
            The format of the file.
        comment_char : str, optional
            The character used to delimit comments in the file.
        reference_char : str, optional
            The character used to delimit cross-references
            in the file.
        indentation : int, optional
            The indentation used to add suboptions or
            subsections in the file when using the 'py' format.

        Raises
        ------
        CrossReferenceError
            If the cross-references cannot be solved.
        """
        def is_tree_node(line):
            line = line.strip()
            return len(line) > 2 and line[0] == '[' and line[-1] == ']'

        def update_keylist(keylist, depth, indentation):
            if depth % indentation:
                raise IndentationError(line)
            depth = depth // indentation
            if depth > len(keylist):
                raise IndentationError(line)
            return keylist[:depth]

        def extract_tree_node_py(keylist, line, indentation):
            key = line.strip()[1:-1]
            keylist = update_keylist(keylist, line.find(key) - 1, indentation)
            return keylist + [key]

        def extract_tree_node_flat(line):
            return line.strip()[1:-1]

        def extract_tree_leaf_py(keylist, line, indentation):
            if '=' in line:
                split = line.split('=', 1)
                key = split[0].strip()
                value = split[1].strip()
            else:
                key = line.strip()
                value = ''
            keylist = update_keylist(keylist, line.find(key), indentation)
            self.set(keylist + [key], value, update_tree=True)
            return keylist

        def extract_tree_leaf_flat(section, line):
            if '=' in line:
                split = line.split('=', 1)
                key = split[0].strip()
                value = split[1].strip()
            else:
                key = line.strip()
                value = ''
            self.set([section, key], value, update_tree=True)
            return section

        def extract_tree_leaf_cpp(line):
            if '=' in line:
                split = line.split('=', 1)
                key = split[0].strip()
                value = split[1].strip()
            else:
                key = line.strip()
                value = ''
            keylist = key.split('.')
            self.set(keylist, value, update_tree=True)

        def read_line_py(line, keylist, comment_char, indentation):
            line = line.split(comment_char)[0]
            if not line or line.isspace():
                return keylist
            if is_tree_node(line):
                return extract_tree_node_py(keylist, line, indentation)
            return extract_tree_leaf_py(keylist, line, indentation)

        def read_line_flat(line, section, comment_char):
            line = line.split(comment_char)[0]
            if not line or line.isspace():
                return section
            if is_tree_node(line):
                return extract_tree_node_flat(line)
            return extract_tree_leaf_flat(section, line)

        def read_line_cpp(line, comment_char):
            line = line.split(comment_char)[0].strip()
            if line and not line.isspace():
                extract_tree_leaf_cpp(line)

        def has_reference(value, reference_char):
            return len(value) > 2 and reference_char in value

        def extract_references(value, reference_char):
            return [
                ref for (i, ref) in enumerate(value.split(reference_char))
                if ref and i % 2
            ]

        def solve_references_string(value, max_rec, reference_char):
            if not has_reference(value, reference_char):
                return value
            if max_rec == 0:
                raise CrossReferenceError
            reflist = extract_references(value, reference_char)
            for ref in reflist:
                keylist = ref.split('.')
                subvalue = solve_references_keylist(keylist, max_rec - 1,
                                                    reference_char)
                value = value.replace(reference_char + ref + reference_char,
                                      subvalue)
            return value

        def solve_references_keylist(keylist, max_rec, reference_char):
            value = self.get(keylist)
            value = solve_references_string(value, max_rec, reference_char)
            self.set(keylist, value, update_tree=False)
            return value

        # read and parse file content
        lines = Path(file_name).lines(retain=False)
        if convention == 'py':
            keylist = []
            for line in lines:
                keylist = read_line_py(line, keylist, comment_char,
                                       indentation)
        elif convention == 'flat':
            section = None
            for line in lines:
                section = read_line_flat(line, section, comment_char)
        elif convention == 'cpp':
            for line in lines:
                read_line_cpp(line, comment_char)

        # solve references
        keylistlist = self.suboptions()
        max_rec = len(keylistlist) - 1
        for keylist in keylistlist:
            solve_references_keylist(keylist, max_rec, reference_char)

    def tofile(self, file_name, convention='py', indentation=4):
        """Writes the configuration options to a file.

        Once written, the file can be read and parsed by an other
        `TreeConfigParser` instance.

        Parameters
        ----------
        file_name : str
            The name of the file to write.
        convention : {'py', 'flat', 'cpp'}, optional
            The format of the file.
        indentation : int, optional
            The indentation used to add suboptions or
            subsections in the file when using the 'py' format.
        """
        def write_tree_node_line_py(depth, indentation, key):
            return [' ' * depth * indentation + f'[{key}]']

        def write_tree_leaf_line_py(depth, indentation, key, value):
            return [' ' * depth * indentation + f'{key} = {value}']

        def write_tree_leaf_line_cpp(keylist, value):
            return ['.'.join(keylist) + f' = {value}']

        def write_tree_py(tree, depth, indentation):
            lines = []
            for key in tree:
                if isinstance(tree[key], TreeConfigParser):
                    lines.extend(
                        write_tree_node_line_py(depth, indentation, key))
                    lines.extend(
                        write_tree_py(tree[key].tree, depth + 1, indentation))
                else:
                    lines.extend(
                        write_tree_leaf_line_py(depth, indentation, key,
                                                tree[key]))
            return lines

        def write_tree_cpp(tree, keylist):
            lines = []
            for key in tree:
                if isinstance(tree[key], TreeConfigParser):
                    lines.extend(
                        write_tree_cpp(tree[key].tree, keylist + [key]))
                else:
                    lines.extend(
                        write_tree_leaf_line_cpp(keylist + [key], tree[key]))
            return lines

        # write lines
        if convention == 'py':
            lines = write_tree_py(self.tree, 0, indentation)
        elif convention == 'flat':
            lines = write_tree_py(self.tree, 0, 0)
        elif convention == 'cpp':
            lines = write_tree_cpp(self.tree, [])
        Path(file_name).write_lines(lines)


class CrossReferenceError(Exception):
    """Exception class for cross-reference errors in config files."""


def string_conversion(value, to_type='string', **kwargs):
    """Converts a string to the given type.

    Parameters
    ----------
    value : string
        The string to convert.
    to_type : {'string', 'path', 'bool', 'int', 'float', 'stringlist', \
'log_level', 'np_fromfile', 'datetime'}, optional
        The conversion to use.
    **kwargs : dict
        Keyword arguments passed to the conversion function.
        See the details below.

    Other parameters
    ----------------
    use_eval : bool, optional
        For the **string to int** and **string to float** conversions:
        enables the use of the `eval` function (default: *False*).
    sep : str, optional
        For the **string to stringlist** conversion:
        delimiter for the `split` function (default: *None*).
    maxsplit : int, optional
        For the **string to stringlist** conversion:
        maximum number of splits for the `split` function (default: -1).
    dtype : data-type, optional
        For the **string to np_fromfile** conversion:
        data type of the returned array (default `float`).
    count : int, optional
        For the **string to np_fromfile** conversion:
        number of items to read (default -1).
    offset : int, optional
        For the **string to np_fromfile** conversion:
        the offset (in bytes) from the file's current position (default 0).
    convention : str, optional
        For the **string to datetime** conversion:
        format used in the `datetime.strptime` function
        (default: '%Y-%m-%d').
        Special cases are created for 'polyphemus_date'
        ('%Y-%m-%d'), 'polyphemus_datetime' ('%Y-%m-%d_%H-%M'),
        and 'ecmwf_datetime' ('%Y-%m-%dT%H:%M:%SZ').

    Returns
    -------
    converted_value
        The converted string.

    Notes
    -----
    **String to string**: no conversion is performed, directly returns
    *value*.

    **String to path**: converts the value to a `path.Path` instance.

    **String to bool**: converts the value to a boolean.

    - Returns *True* if *value* is 'true', 'yes', 'on', '1'.
    - Returns *False* if *value* is 'false', 'no', 'off', or '0'.
    - Raises a `ValueError` otherwise.

    The comparison is case-insensitive.

    **String to int**: converts the value to an integer. Use the `eval`
    function if *use_eval* is True.

    **String to float**: converts the value to a real. Use the `eval`
    function if *use_eval* is True.

    **String to stringlist**: converts the value to a list of strings
    using the `split` function.

    **String to log_level**: converts the value to a `logging` level.

    - Returns `logging.DEBUG` if value is 'debug'.
    - Returns `logging.INFO` if value is 'info'.
    - Returns `logging.WARNING` if value is 'warning'.
    - Returns `logging.ERROR` if value is 'error'.
    - Returns `logging.CRITICAL` if value is 'critical'.
    - Raises `ValueError` otherwise.

    The comparison is case-insensitive.

    **String to np_fromfile** The value is assumed to be the name of
    a binary file. It is converted to a `numpy.ndarray` using the
    `numpy.fromfile` function.

    **String to datetime**: converts the value to a
    `datetime.datetime` instance using the `datetime.strptime` function.

    Examples
    --------
    >>> string_conversion('abc')
    'abc'
    >>> string_conversion('/usr/bin', to_type='path')
    Path('/usr/bin')
    >>> string_conversion('true', to_type='bool')
    True
    >>> string_conversion('On', to_type='bool')
    True
    >>> string_conversion('0', to_type='bool')
    False
    >>> string_conversion('-10', to_type='int')
    -10
    >>> string_conversion('3/2', to_type='float', use_eval=True)
    1.5
    >>> string_conversion('a   bc def   g hi', to_type='stringlist')
    ['a', 'bc', 'def', 'g', 'hi']
    """
    def string_to_string(value):
        return value

    def string_to_path(value):
        return Path(value)

    def string_to_bool(value):
        if value.lower() in ['true', 'yes', 'on', '1']:
            return True
        if value.lower() in ['false', 'no', 'off', '0']:
            return False
        return ValueError(f'"{value}" cannot be converted to bool')

    def string_to_int(value, use_eval=False):
        return int(eval(value)) if use_eval else int(value)  # pylint: disable=eval-used

    def string_to_float(value, use_eval=False):
        return float(eval(value)) if use_eval else float(value)  # pylint: disable=eval-used

    def string_to_stringlist(value, sep=None, maxsplit=-1):
        return value.split(sep, maxsplit)

    def string_to_log_level(value):
        levels = {
            'debug': DEBUG,
            'info': INFO,
            'warning': WARNING,
            'error': ERROR,
            'critical': CRITICAL
        }
        if value.lower() in levels:
            return levels[value.lower()]
        raise ValueError(f'"{value}" cannot be converted to logging level')

    def string_to_np_fromfile(value, dtype=float, count=-1, offset=0):
        return np.fromfile(value, dtype=dtype, count=count, offset=offset)

    def string_to_datetime(value, convention='%Y-%m-%d'):
        if convention.lower() in ['polyphemus_date']:
            convention = '%Y-%m-%d'
        elif convention.lower() in ['polyphemus_datetime']:
            convention = '%Y-%m-%d_%H-%M'
        elif convention.lower() in ['ecmwf_datetime']:
            convention = '%Y-%m-%dT%H:%M:%SZ'
        return datetime.strptime(value, convention)

    conversions = {
        'string': string_to_string,
        'path': string_to_path,
        'bool': string_to_bool,
        'int': string_to_int,
        'float': string_to_float,
        'stringlist': string_to_stringlist,
        'log_level': string_to_log_level,
        'np_fromfile': string_to_np_fromfile,
        'datetime': string_to_datetime,
    }

    if to_type in conversions:
        return conversions[to_type](value, **kwargs)
    raise TypeError(f'unkown conversion "string to {to_type}"')


def fromfile(file_name, **kwargs):
    """Reads and parses a configuration file.

    Parameters
    ----------
    file_name : string
        The name of the file to parse.
    **kwargs : dict
        Keyword arguments passed to the `TreeConfigParser.read_file`
        method.

    Returns
    -------
    config : TreeConfigParser
        The configuration.

    Notes
    -----
    This function creates an empty `TreeConfigParser` instance and
    uses the `TreeConfigParser.read_file` method to parse the file.
    """
    config = TreeConfigParser()
    config.read_file(file_name, **kwargs)
    return config
