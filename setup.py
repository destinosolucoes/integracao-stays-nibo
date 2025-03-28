from setuptools import setup, find_packages

setup(
    name="destino-bsm",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "requests",
        "fake-useragent",
        "python-dateutil",
        "python-dotenv",
        "sqlmodel",
        "pymysql",
    ],
    extras_require={
        "dev": [
            "pytest",
            "pytest-asyncio",
        ],
    },
) 