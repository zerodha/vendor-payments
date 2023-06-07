from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

# get version from __version__ variable in vendor_payments/__init__.py
from vendor_payments import __version__ as version

setup(
    name="vendor_payments",
    version=version,
    description="Vendor Payments",
    author="Frappe",
    author_email="vendor_payments@gmail.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)
