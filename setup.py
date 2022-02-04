import email
import setuptools

with open("README.md", "r", encoding="utf-8") as readme_file:
    readme = readme_file.read()

requirements = ['pandas>=1.1.0', 'numpy>=1.19.0']

setuptools.setup(
    name="lidarToGeo",
    version="1.0.0",
    author="Jabor047",
    email="gkkarobia@gmail.com",
    description="A package that get lidar data from an s3 bucket and converts it to Geo raster",
    long_description=readme,
    long_description_content_type="text/markdown",
    python_requires=">=3.7",
    install_requires=requirements,
    url="https://github.com/Jabor047/LidarToGeo",
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    test_suite="tests"
)
