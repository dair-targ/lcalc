from setuptools import setup

__version__ = '1.0'


setup(
    name='lcalc',
    version=__version__,
    packages=['lcalc'],
    url='https://github.com/dair-targ/lcalc',
    download_url='https://github.com/dair-targ/lcalc/tarball/%s' % __version__,
    license='GPLv3',
    author='Vladimir Berkutov',
    author_email='vladimir.berkutov@gmail.com',
    description='Lambda Calculus implementation',

    install_require=[
        'parsec>=3.0',
    ],

    test_suite='nose.collector',
    tests_require=[
        'nose>=1.3.7'
    ],
)
