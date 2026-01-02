# Chr3D Conda Packaging Guide

This guide explains how to build, test, and publish Chr3D as a conda package.

## Prerequisites

```bash
conda create -n conda-build-env -c conda-forge conda-build anaconda-client
conda activate conda-build-env
```

---

## Local Development Testing

### Option 1: Quick Local Build (Recommended for Testing)

Build directly from the local source without needing a GitHub release:

```bash
cd /path/to/Chr3D

conda build conda-recipe --no-anaconda-upload
```

### Option 2: Build with Local Source Path

Edit `conda-recipe/meta.yaml` to use local source:

```yaml
source:
  path: ..
```

Then build:

```bash
conda build conda-recipe
```

---

## Install Locally Built Package

After building, install from the local conda-bld directory:

```bash
conda install --use-local chr3d
```

Or specify the exact path:

```bash
conda install /path/to/miniconda3/conda-bld/noarch/chr3d-3.2.0-py_0.tar.bz2
```

---

## Test the Installation

```bash
conda activate chr3d-env

chr3d --help

python -c "import chr3d as c3d; print(c3d.__version__)"
```

---

## Full Local Testing Workflow

```bash
conda activate conda-build-env

cd /path/to/Chr3D

conda build conda-recipe --no-anaconda-upload

conda create -n chr3d-test -c local chr3d -y

conda activate chr3d-test

chr3d --help

python -c "import chr3d; print('Success!')"

conda deactivate
conda env remove -n chr3d-test
```

---

## Publishing to Anaconda Cloud (Personal Channel)

### 1. Create Account
Go to https://anaconda.org and create an account.

### 2. Login
```bash
anaconda login
```

### 3. Upload Package
```bash
anaconda upload /path/to/conda-bld/noarch/chr3d-3.2.0-py_0.tar.bz2
```

### 4. Users Can Install
```bash
conda install -c YOUR_USERNAME chr3d
```

---

## Publishing to Bioconda (Recommended)

Bioconda is the standard channel for bioinformatics tools.

### 1. Fork bioconda-recipes
```bash
git clone https://github.com/YOUR_USERNAME/bioconda-recipes
cd bioconda-recipes
git remote add upstream https://github.com/bioconda/bioconda-recipes
git fetch upstream
git checkout -b add-chr3d upstream/master
```

### 2. Create Recipe
```bash
mkdir -p recipes/chr3d
cp /path/to/Chr3D/conda-recipe/meta.yaml recipes/chr3d/
cp /path/to/Chr3D/conda-recipe/build.sh recipes/chr3d/
```

### 3. Update meta.yaml for Bioconda

Update the source section with the correct SHA256:

```bash
curl -sL https://github.com/rudrajoshi2481/Chr3D/archive/refs/tags/v3.2.0.tar.gz | sha256sum
```

Replace `PLACEHOLDER_SHA256` in meta.yaml with the actual hash.

### 4. Lint the Recipe
```bash
conda install -c conda-forge bioconda-utils

bioconda-utils lint --packages chr3d
```

### 5. Test Build with Docker
```bash
bioconda-utils build --docker --packages chr3d
```

### 6. Submit Pull Request
```bash
git add recipes/chr3d/
git commit -m "Add chr3d: Chromatin 3D structure analysis pipeline"
git push origin add-chr3d
```

Then create a Pull Request on GitHub to bioconda/bioconda-recipes.

---

## Creating a GitHub Release (Required for Bioconda)

Before submitting to Bioconda, create a release on GitHub:

### 1. Tag the Release
```bash
git tag -a v3.2.0 -m "Release v3.2.0"
git push origin v3.2.0
```

### 2. Create Release on GitHub
- Go to https://github.com/rudrajoshi2481/Chr3D/releases
- Click "Create a new release"
- Select tag v3.2.0
- Add release notes
- Publish

### 3. Get SHA256 Hash
```bash
curl -sL https://github.com/rudrajoshi2481/Chr3D/archive/refs/tags/v3.2.0.tar.gz | sha256sum
```

Update `conda-recipe/meta.yaml` with this hash.

---

## Troubleshooting

### Build Fails with Missing Dependencies
Ensure all dependencies are available on conda-forge or bioconda:
```bash
conda search -c conda-forge -c bioconda PACKAGE_NAME
```

### Import Errors After Installation
Check that the package structure is correct:
```bash
python -c "import chr3d; print(chr3d.__file__)"
```

### CLI Not Found
Verify entry points in meta.yaml match pyproject.toml:
```yaml
entry_points:
  - chr3d = chr3d.cli:main
```

---

## Package Structure

```
Chr3D/
├── conda-recipe/
│   ├── meta.yaml      # Package metadata and dependencies
│   └── build.sh       # Build script
├── src/
│   └── chr3d/         # Python package
├── pyproject.toml     # Python package config
├── LICENSE            # MIT License
└── README.md          # Documentation
```

---

## Version Updates

When releasing a new version:

1. Update version in `pyproject.toml`
2. Update version in `conda-recipe/meta.yaml`
3. Create new git tag
4. Create GitHub release
5. Update SHA256 hash in meta.yaml
6. Rebuild and upload

---

## Quick Reference Commands

```bash
conda build conda-recipe

conda install --use-local chr3d

conda build purge

anaconda upload /path/to/package.tar.bz2

conda search -c YOUR_CHANNEL chr3d
```
