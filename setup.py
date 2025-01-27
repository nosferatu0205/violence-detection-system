from setuptools import setup, find_packages

setup(
    name="violence-detection-system",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'opencv-python',
        'numpy',
        'tensorflow',
        'PyQt5',
        'joblib'
    ],
)