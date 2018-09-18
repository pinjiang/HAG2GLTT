from distutils.core import setup
import py2exe
from glob import glob
import matplotlib
import sys
sys.path.append("D:\\Temp")
data_files1 = [("Microsoft.VC90.CRT",glob(r'D:\Temp\*.*'))]
#print(data_files)
data_files2 = matplotlib.get_py2exe_datafiles()
#print(matplotlib.get_py2exe_datafiles())
data_files = data_files1 + data_files2
#data_files.append(matplotlib.get_py2exe_datafiles())
setup(
    options={'py2exe': { "includes" : ["matplotlib.backends.backend_tkagg"] }},
    data_files = data_files,
    windows = ["G2GMeasurementTool.py"]
)