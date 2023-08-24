import setuptools

with open("README.md", "r") as f:
  package_details = f.read()

setuptools.setup(
  name="node_rotator",
  version="1.0.0",
  author="Abdullah Barrak.",
  author_email="abdullah@abarrak.com",
  description="A automated rotation tool for maintenance and patching of kubernetes nodes.",
  long_description=package_details,
  long_description_content_type="text/markdown",
  url="https://github.com/abarrak/node-rotator",
  packages=setuptools.find_packages(),
  install_requires=[
    'oci',
    'kubernetes',
    'typer[all]',
  ],
  tests_require=[
    'pytest'
  ],
  download_url="https://github.com/abarrak/node-rotator"
)
