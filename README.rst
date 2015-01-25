Deduplicated
============

Check duplicated files.

Exemple of use
--------------

.. code-block:: bash

  # Update directory cache
  $ deduplicated update /path/for/check

  # List duplicated files in directory cache
  $ deduplicated duplicated /path/for/check

  # Update and list duplicated files
  $ deduplicated check /path/for/check

  # Check if file in directory cache
  $ deduplicated indir myfile /path/for/check

  # Start web version, connect http://127.0.0.1:5050
  $ deduplicated-web
