from .context import FSContext
from .identifiers import NamespaceIdentifier, AbsoluteIdentifier, RelativeIdentifier
import sys
import pathlib
import argparse
import typing


def get_entry_point(value: str) -> typing.Tuple[pathlib.Path, str]:
    parts = value.rsplit(':', 2)
    definition = parts[1] if len(parts) == 2 else 'main'
    path = pathlib.Path(parts[0])
    if path.is_dir():
        path = path / 'main.lcalc'
    return path.absolute(), definition


def main():
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument('entry_point', action='store', help='Entry point - directory, file, or a function')
    args = argument_parser.parse_args()

    entry_path, entry_func = get_entry_point(args.entry_point)
    namespace_identifier = NamespaceIdentifier(entry_path.name.replace('.lcalc', ''))

    context = FSContext(
        namespace_identifier=namespace_identifier,
        root_path=entry_path.parent,
    )
    print(context.eval(
        absolute_identifier=AbsoluteIdentifier(namespace_identifier, RelativeIdentifier(entry_func))
    ))


if __name__ == '__main__':
    main()
