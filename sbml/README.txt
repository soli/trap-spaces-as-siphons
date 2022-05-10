Original SBML-Qual models

Converted to BoolNet format with

```
for file in *.sbml ; do java -jar GINsim-3.0.0b-with-deps.jar -lqm $file ${file%%sbml}bnet ; done
```
