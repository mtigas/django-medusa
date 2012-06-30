from setuptools import setup, find_packages

install_requires = [
    'django',
]

version = __import__('django_medusa').get_version()

setup(name='django-medusa',
    version=version,
    description='A Django static website generator.',
    author='Mike Tigas', # update this as needed
    author_email='mike@tig.as', # update this as needed
    url='https://github.com/mtigas/django-medusa/',
    download_url='https://github.com/mtigas/django-medusa/downloads',
    packages=find_packages(),
    install_requires=install_requires,
    license='MIT',
    keywords='django static staticwebsite staticgenerator publishing',
    classifiers=["Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ],
)
