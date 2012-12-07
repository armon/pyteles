from setuptools import setup, Command
import pyteles

# Get the long description by reading the README
try:
    readme_content = open("README.md").read()
except:
    readme_content = ""

# Create the actual setup method
setup(name='pyteles',
      version=pyteles.__version__,
      description='Client library to interface with Teles servers',
      long_description=readme_content,
      author='Armon Dadgar',
      author_email='armon.dadgar@gmail.com',
      maintainer='Armon Dadgar',
      maintainer_email='armon.dadgar@gmail.com',
      url="https://github.com/armon/pyteles/",
      license="MIT License",
      keywords=["teles", "r-tree","client"],
      py_modules=['pyteles'],
      classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Topic :: Database",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries",
    ]
      )
