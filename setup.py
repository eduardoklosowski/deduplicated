from setuptools import find_packages, setup


version = __import__('deduplicated').__version__


setup(
    name='deduplicated',
    version=version,
    description='Check duplicated files',
    author='Eduardo Klosowski',
    author_email='eduardo_klosowski@yahoo.com',
    license='MIT',
    packages=find_packages(),
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'deduplicated = deduplicated.cmd:main',
        ],
    },
)
