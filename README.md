This implements a one-page flask server to search for N5 volumes in a particular directory and show a table of contents for them, with neuroglancer links to each volume that was found.  The non-standard `"translation"` key is read from the `attributes.json` file, and used to populate neuroglancer's `"transformation"` matrix.