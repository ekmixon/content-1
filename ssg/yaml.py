from __future__ import absolute_import
from __future__ import print_function

import codecs
import re
import sys
import yaml

from collections import OrderedDict

from .jinja import load_macros, process_file

try:
    from yaml import CSafeLoader as yaml_SafeLoader
except ImportError:
    from yaml import SafeLoader as yaml_SafeLoader


def _bool_constructor(self, node):
    return self.construct_scalar(node)


# Don't follow python bool case
yaml_SafeLoader.add_constructor(u'tag:yaml.org,2002:bool', _bool_constructor)


class DocumentationNotComplete(Exception):
    pass


def _save_rename(result, stem, prefix):
    result["{0}_{1}".format(prefix, stem)] = stem


def _open_yaml(stream, original_file=None, substitutions_dict={}):
    """
    Open given file-like object and parse it as YAML.

    Optionally, pass the path to the original_file for better error handling
    when the file contents are passed.

    Return None if it contains "documentation_complete" key set to "false".
    """
    try:
        yaml_contents = yaml.load(stream, Loader=yaml_SafeLoader)

        if yaml_contents.pop("documentation_complete", "true") == "false" and \
                substitutions_dict.get("cmake_build_type") != "Debug":
            raise DocumentationNotComplete("documentation not complete and not a debug build")

        return yaml_contents
    except DocumentationNotComplete as e:
        raise e
    except Exception as e:
        count = 0
        _file = original_file
        if not _file:
            _file = stream
        with open(_file, "r") as e_file:
            lines = e_file.readlines()
            for line in lines:
                count = count + 1
                if re.match(r"^\s*\t+\s*", line):
                    print(f"Exception while handling file: {_file}", file=sys.stderr)
                    print(
                        f"TabIndentationError: Line {count} contains tabs instead of spaces:",
                        file=sys.stderr,
                    )

                    print("%s\n\n" % repr(line.strip("\n")), file=sys.stderr)
                    sys.exit(1)

        print(f"Exception while handling file: {_file}", file=sys.stderr)
        raise e


def open_and_expand(yaml_file, substitutions_dict=None):
    """
    Process the file as a template, using substitutions_dict to perform
    expansion. Then, process the expansion result as a YAML content.

    See also: _open_yaml
    """
    if substitutions_dict is None:
        substitutions_dict = {}

    expanded_template = process_file(yaml_file, substitutions_dict)
    try:
        yaml_contents = _open_yaml(expanded_template, yaml_file, substitutions_dict)
    except yaml.scanner.ScannerError as e:
        print("A Jinja template expansion can mess up the indentation.")
        print("Please, check if the contents below are correctly expanded:")
        print(f"Source yaml: {yaml_file}")
        print(f"Expanded yaml:\n{expanded_template}")
        sys.exit(1)

    return yaml_contents


def open_and_macro_expand(yaml_file, substitutions_dict=None):
    """
    Do the same as open_and_expand, but load definitions of macros
    so they can be expanded in the template.
    """
    substitutions_dict = load_macros(substitutions_dict)
    return open_and_expand(yaml_file, substitutions_dict)


def open_raw(yaml_file):
    """
    Open given file-like object and parse it as YAML
    without performing any kind of template processing

    See also: _open_yaml
    """
    with codecs.open(yaml_file, "r", "utf8") as stream:
        yaml_contents = _open_yaml(stream, original_file=yaml_file)
    return yaml_contents


def ordered_load(stream, Loader=yaml.Loader, object_pairs_hook=OrderedDict):
    """
    Drop-in replacement for yaml.load(), but preserves order of dictionaries
    """
    class OrderedLoader(Loader):
        pass

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))
    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)
    return yaml.load(stream, OrderedLoader)


def ordered_dump(data, stream=None, Dumper=yaml.Dumper, **kwds):
    """
    Drop-in replacement for yaml.dump(), but preserves order of dictionaries
    """
    class OrderedDumper(Dumper):
        # fix tag indentations
        def increase_indent(self, flow=False, indentless=False):
            return super(OrderedDumper, self).increase_indent(flow, False)

    def _dict_representer(dumper, data):
        return dumper.represent_mapping(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
            data.items())

    def _str_representer(dumper, data):
        if '\n' in data:
            return dumper.represent_scalar(u'tag:yaml.org,2002:str', data,
                                           style='|')
        else:
            return dumper.represent_str(data)

    OrderedDumper.add_representer(OrderedDict, _dict_representer)
    OrderedDumper.add_representer(str, _str_representer)

    # Fix formatting by adding a space in between tasks
    unformatted_yaml = yaml.dump(data, None, OrderedDumper, **kwds)
    formatted_yaml = re.sub(r"[\n]+([\s]*)- name", r"\n\n\1- name", unformatted_yaml)

    return stream.write(formatted_yaml) if stream is not None else formatted_yaml


def _strings_to_list(one_or_more_strings):
    """
    Output a list, that either contains one string, or a list of strings.
    In Python, strings can be cast to lists without error, but with unexpected result.
    """
    if isinstance(one_or_more_strings, str):
        return [one_or_more_strings]
    else:
        return list(one_or_more_strings)


def update_yaml_list_or_string(current_contents, new_contents, prepend=False):
    result = []
    if current_contents:
        result += _strings_to_list(current_contents)
    if new_contents:
        if prepend:
            result = _strings_to_list(new_contents) + result
        else:
            result += _strings_to_list(new_contents)
    if not result:
        result = ""
    if len(result) == 1:
        result = result[0]
    return result
