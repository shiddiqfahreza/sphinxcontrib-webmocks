# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

long_desc = '''
This package contains the webmocks Sphinx extension.

.. _Sphinx: http://sphinx.pocoo.org/

This extension enable you to create web mock-ups in your Sphinx document.
Following code is sample::

   :Name: :text:`Input your name`
   :Address: :text:`Input your address`

   :button:`Cancel` :button:`OK`

See more examples and output images in http://packages.python.org/sphinxcontrib-webmocks/ .
'''

requires = ['Sphinx>=0.6']

setup(
    name='sphinxcontrib-webmocks',
    version='0.1.0',
    url='http://bitbucket.org/tk0miya/sphinxcontrib-webmocks',
    download_url='http://pypi.python.org/pypi/sphinxcontrib-webmocks',
    license='BSD',
    author='Takeshi Komiya',
    author_email='i.tkomiya@gmail.com',
    description='Sphinx "webmocks" extension',
    long_description=long_desc,
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Documentation',
        'Topic :: Utilities',
    ],
    platforms='any',
    packages=find_packages(),
    include_package_data=True,
    install_requires=requires,
    namespace_packages=['sphinxcontrib'],
)
