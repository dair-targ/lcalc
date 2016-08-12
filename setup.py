from setuptools import setup, find_packages

setup(
    name='picalc',
    version='1.0',
    packages=find_packages(),
    url='',
    license='GPLv3',
    author='Vladimir Berkutov',
    author_email='vladimir.berkutov@gmail.com',
    description='Lambda Calculus',

    install_require=[
        'parsec>=3.0',
    ],

    test_suite='nose.collector',
    tests_require=[
        'nose>=1.3.7'
    ],
)
