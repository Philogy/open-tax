from setuptools import setup, find_packages


with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()


setup(
    # metadata
    name='open_tax',
    version='0.0.1',
    description='Open-Source E2E Crypto Tax & Accounting Framework',
    long_description_content_type='text/markdown',
    long_description=long_description,
    packages=find_packages(include=['open_tax']),
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10'
    ],
    author='Philogy',
    url='https://github.com/Philogy/open-tax',
    install_requires=[
        'toolz',
        'beancount >= 2.0.0',
        'python-dotenv',
        'requests'
    ]
)
