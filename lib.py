# Add lib/ at the start of the include path.
# Do it this way rather than in appengine_config.py so it works in unittests.

import os
import sys

appdir = os.path.dirname(__file__)
libdir = os.path.join(appdir, 'lib')
sys.path.insert(0, libdir)
