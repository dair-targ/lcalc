import lcalc


def main():
    context = lcalc.FSContext(lcalc.NamespaceIdentifier('main'))
    print(lcalc.run(context))


if __name__ == '__main__':
    main()
