# Chr3D: End-to-End 3D Chromatin Analysis Pipeline


**Chr3D** is a unified, end-to-end framework for analyzing 3D chromatin architecture data. It supports bulk Hi-C, single-nucleus Hi-C, HiChIP and ChIA-PET through a single modular CLI & Python API.

**Note:** TUI Interface is also in development

# Supports

- ChiaPET
- HiChIP
- Hic
- snHIC
- HiGlass
- Restriction Site Generation & Detection
- File converters

# Docs

Check out the docs at [Chr3D Docs](https://chr3d.rudhrajoshi.me/)

# Install

Get the Chr3D pipeline running locally.

## Prerequisites

- **Conda** (Miniconda or Anaconda)
- **Git**

## 1. Clone the repository

```bash filename="Terminal"
git clone https://github.com/rudrajoshi2481/Chr3D.git
cd Chr3D
```

## 2. Run the install script

The repository includes an automated install script that sets up everything.

```bash filename="Terminal"
chmod +x install.sh
./install.sh
```

## 3. Activate and use

or check out the docs at [Chr3D Docs](https://chr3d.rudhrajoshi.me/)    

```bash filename="Terminal"
conda activate chr3d
chr3d --help
```

Or use the Python API:

```python filename="Python"
import chr3d as c3d
print(c3d.__version__)
```


## Future Plans & Fixes

- [ ] Removing counting before splitting files
- [ ] Update API make it even more flexible
- [ ] Add TUI based interface
- [ ] Add config file as input in Command & TUI
- [ ] Update Logging make it even more flexible
- [ ] Update file Conversion scripts


