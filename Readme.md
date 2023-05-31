# pyPDFReader
Toolkits to pre-process text to be trained using NLP

**1) Installing conda environment**

```
    conda env create --name pyPDFReader --file requirements.yaml 
```

or

```
    pip install -r requirements.txt
```

**2) Updating conda environment**

```
    conda env export > requirements.yaml
```

or

```
    pip list --format=freeze > requirements.txt
```

**3) Using as git submodule**

```
git submodule add -b main https://github.com/fmorenovr/pyPDFReader.git path_to_install/pyPDFReader
git submodule update --remote
```
