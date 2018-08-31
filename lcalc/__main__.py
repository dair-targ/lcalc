import lcalc


def main():
    context = lcalc.FSContext(lcalc.NamespaceIdentifier('main'))
    print(context.eval())


if __name__ == '__main__':
    main()
