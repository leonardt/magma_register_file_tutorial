An example of defining and verifying a register file generator in Python using
magma.

The notebooks are intended to be read in the following order:
* [1-Register File Example.ipynb](./Register File Example.ipynb)
* [2-Defining an APB Model in Python.ipynb](./2-Defining an APB Model in Python.ipynb)
* [3-Verifying The Register File.ipynb](./3-Verifying The Register File.ipynb)
* [4-Using the Register File.ipynb](./4-Using the Register File.ipynb)

This example has also been implemented as a set of Python files, which may be
useful for those interested in seeing how this could be implemented outside of
the notebook environment. **NOTE** that the `.py` implementation is slightly
different than the `.ipynb` implementation because they were not developed at
the same time.

The files are organized as follows:
* [apb.py](./apb.py) - Defines a set of type constructors for the APB
  interface.
* [apb_model.py](./apb_model.py) - Implements a cycle-accurate functional
  model of an APB master used to generate input stimuli for the register file
  tests.
* [reg_file.py](./reg_file.py) - Defines a magma register file generator
* [top.py](./top.py) - Provides an example of a top generator that uses the
  register file generator

Each file has a corresponding `test_<file>.py` that contains tests for the
units defined in the file.

[waveform.py](./waveform.py) defines a helper class for drawing waveforms using
the wavedrom format.
