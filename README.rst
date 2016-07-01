####################################
A Jupyter/IPython kernel for EclairJS
####################################

eclairjs-kernel has been developed for use specifically with
`Jupyter Notebook` and eclairjs-node. It can also be loaded as an `IPython`
extension allowing for `eclairjs` code in the same `notebook`
as `python` code.


Installation
============

**Development version**

.. code-block:: bash

   export SPARK_HOME="<spark 1.6.0 distribution>"

   export ECLAIRJS_NASHORN_HOME="<location of eclairjs-nashron jar>"

   pip install git+https://github.com/bpburns/eclairjs-kernel.git

Requires
========

- System installation of Apache Spark 1.6.0
- System installation of eclarjs-nashorn >= 0.5
- Notebook (IPython/Jupyter Notebook >= 4.0)
- Metakernel
