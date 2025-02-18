from setuptools import setup, find_packages

setup(
    name="document-qa",
    version="0.1.0",
    packages=find_packages(where="backend"),
    package_dir={"": "backend"},
    install_requires=[
        "fastapi>=0.115.2",
        "uvicorn>=0.24.0",
        "python-multipart>=0.0.6",
        "groq>=0.4.1",
        "python-magic>=0.4.27",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.1",
            "black>=23.7.0",
            "mypy>=1.5.1",
            "ruff>=0.0.287",
        ]
    },
    python_requires=">=3.11",
) 