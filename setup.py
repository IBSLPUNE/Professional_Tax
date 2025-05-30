from setuptools import setup, find_packages

setup(
    name='professional_tax',
    version='1.0.0',
    description='Professional Tax calculation for ERPNext based on state formulas',
    author='Adarsh Jha',
    author_email='design@indibasolutions.com',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=['frappe']
)
