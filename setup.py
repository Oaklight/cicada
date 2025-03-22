from setuptools import find_packages, setup

setup(
    name="cicada-agent",
    version="0.6.0",  # Update this as needed
    author="Oaklight",
    author_email="oaklight@gmx.com",
    description="A Python package for the Cicada project",
    long_description=open("README_en.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/Oaklight/cicada",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        # Minimal dependencies for core functionality
        "openai>=1.6.8",
        "pydantic>=2.10.6",
        "httpx>=0.28.1",
        "pyyaml>=6.0.2",
        "blessed>=1.20.0",
        "pillow>=11.1.0",
        "toolregistry>=0.2.0",
    ],
    extras_require={
        "core": [],
        "full": [
            "gmsh>=4.13.1",
            "plyfile==1.1",
            "trimesh==4.5.1",
            "pyglet<2",
            "pyrender==0.1.45",
            "build123d==0.8.0",
            "psycopg2-binary==2.9.10",
            "sqlalchemy==2.0.36",
            "pgvector==0.3.6",
            "sqlite-vec==0.1.6",
            "questionary==2.1.0",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
)
