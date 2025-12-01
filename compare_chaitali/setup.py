import setuptools
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()
setuptools.setup(
    name="Ele_Product_compare_chaitali",
    version="0.2.1",
    author="Example Author",
    author_email="x24215449@nicrl.ie",
    description="A package which can compare 2 products",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pypa/sampleproject",
    packages=["Ele_Product_compare_chaitali"],  
    package_dir={"Ele_Product_compare_chaitali": "."},
    install_requires=['boto3'],
    classifiers=[
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    ],
    python_requires='>=3.9',
    )