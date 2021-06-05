import sys
import copy
import json
import urllib.parse
from pathlib import Path
from collections import namedtuple

import numpy as np

from .util import find_files

TocEntry = namedtuple('TocEntry', 'sample stage section version full_version name offset offset_link link')

N5_FILE_SERVER = "http://emdata4.int.janelia.org:9999"

NG_HOST = "http://neuroglancer-demo.appspot.com"

DEFAULT_NG_SETTINGS = {
  "dimensions": {
    "x": [8e-9, "m"],
    "y": [8e-9, "m"],
    "z": [8e-9, "m"],
  },
  "layers": [
    {
      "name": "grayscale",
      "type": "image",
      "source": {
        "url": "n5://http://emdata4.int.janelia.org:9999/Z0720_07m_BR/render/Sec27/v1_acquire_trimmed_align___20210413_164713/",
        "transform": {
          "matrix": [
            [1,0,0,0],
            [0,1,0,0],
            [0,0,1,0]
          ],
          "outputDimensions": {
            "x": [8e-9, "m"],
            "y": [8e-9, "m"],
            "z": [8e-9, "m"],
          }
        }
      }
    }
  ]
}

def find_volumes(root_dir, exclude_dirs):
    # Find json files, but don't look in s0, s1, etc., or the explicitly excluded directories.
    # We could probably do this with
    attrs_files = find_files(root_dir, '.json', ["s[0-9]+", "[0-9]+", *exclude_dirs])
    vol_attrs = {}
    for p in attrs_files:
        p = p[len(root_dir)+1:]  # strip {root_dir}/ prefix
        fullpath = f'{root_dir}/{p}'
        with open(fullpath, 'r') as f:
            try:
                a = json.load(f)
            except Exception as ex:
                print(f"Failed to parse {fullpath}:\n{ex}", file=sys.stderr)
                continue

            if 'scales' in a:
                vol_attrs[p] = a
    return vol_attrs


def links_for_volumes(vol_attrs):
    links = {}
    for p, a in vol_attrs.items():
        links[p] = construct_nglink(p, a)
    return links


def construct_nglink(path, attrs, nghost=NG_HOST, n5server=N5_FILE_SERVER):
    path = Path(path)
    sample, stage, section, full_version = path.parts[-5:-1]
    version = full_version.split('_')[0]

    name = f"{stage}-{section}-{version}"
    if 'translate' in attrs:
        offset = attrs['translate']
        offset_str = ', '.join(map(str, offset))
    else:
        offset = [0,0,0]
        offset_str = 'OFFSET-MISSING'

    transform = [[1,0,0,0],
                 [0,1,0,0],
                 [0,0,1,0]]
    transform = np.array(transform)
    transform[:, -1] = offset

    ng = copy.deepcopy(DEFAULT_NG_SETTINGS)
    ng["layers"][0]["name"] = f"{name}-bdv-offset"
    ng["layers"][0]["source"]["url"] = f"n5://{n5server}/{path.parent}"
    ng["layers"][0]["source"]["transform"]["matrix"] = transform.tolist()

    # If possible, return two links (with offset and without)
    if offset_str != 'OFFSET-MISSING':
        offset_link = nghost + '/#!' + urllib.parse.quote(json.dumps(ng))
    else:
        offset_link = None

    ng["layers"][0]["name"] = f"{name}-NO-OFFSET"
    del ng["layers"][0]["source"]["transform"]
    link = nghost + '/#!' + urllib.parse.quote(json.dumps(ng))

    return TocEntry(sample, stage, section, version, full_version, name, offset_str, offset_link, link)
