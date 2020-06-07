
# fake module that resides in my lib folder and
# imports the actual implementation

from pathlib import Path

here = Path(__file__).absolute().parent
name = here.stem


import sys
sys.path.insert(0, str(here))
del sys.modules[name]
module = __import__(name)
del sys.path[0]

del Path, here, name, sys
globals().update(module.__dict__)
