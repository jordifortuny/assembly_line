# Readme

This repository contains the code to obtain the optimal solution of the multi-model line balancing problem as explained in:

Fortuny-Santos, J.; Ruiz-de-Arbulo-López, P.; Cuatrecasas-Arbós, L.; Fortuny-Profitós, J. Balancing Workload and Workforce Capacity in Lean Management: Application to Multi-Model Assembly Lines. Appl. Sci. 2020, 10, 8829. https://doi.org/10.3390/app10248829

## Dependencies

This code was tested on python 3.7.6 and only uses two python libraries that can be installed as follows:

```bash
pip install pandas=1.0.0
pip install -U -user ortools=7.5.7466
```

This code reads from an Excel file that details the number of models, tasks, the precedences and the workloads of such tasks. An example of such file can be requested at jordi@arcvi.io

## Execution

To execute the code it is only needed to run it from a command line:

```bash
python assembly_line.py
```
