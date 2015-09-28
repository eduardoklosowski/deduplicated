from setuptools import find_packages, setup


version = __import__('deduplicated').__version__
with open('README.rst', 'rb') as f:
    long_description = f.read().decode('utf-8')


setup(
    name='deduplicated',
    version=version,
    packages=find_packages(),

    extras_require={
        'web': ['Flask'],
    },

    author='Eduardo Klosowski',
    author_email='eduardo_klosowski@yahoo.com',

    description='Check duplicated files',
    long_description=long_description,
    license='MIT',
    url='https://github.com/eduardoklosowski/deduplicated',

    include_package_data=True,
    zip_safe=False,

    entry_points={
        'console_scripts': [
            'deduplicated = deduplicated.cmd:main',
            'deduplicated-web = deduplicated.web:main [web]'
        ],
    },

    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Archiving',
    ],
)
