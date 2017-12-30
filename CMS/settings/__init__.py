import os


if os.uname().nodename == 'production_host':
    from .deploy import *
else:
    from .develop import *
