from .context import FSContext
from .identifiers import NamespaceIdentifier
import sys
import pathlib

def main():
    context = FSContext(NamespaceIdentifier('main'), root_path=pathlib.Path(sys.argv[1]))
    print(context.eval())


if __name__ == '__main__':
    main()
