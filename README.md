## This is a fork of [pybind11](https://github.com/pybind/pybind11) that builds stable-ABI Python modules

— i.e. the resulting modules can run on multiple different Python versions.

### Is this production ready?

Yes, sort of! While it still has rough edges, we [are using it in production](https://pypi.org/project/meshlib/).

### How does it work?

The version-dependent code was moved to a tiny shared library. You must build a copy of it for each Python version you want to support (3.8, 3.9, etc), and ship all those with your module.

### How to use?

This isn't header-only unlike the upstream Pybind. You must build the `pybind11nonlimitedapi_stubs` shared library and link your code against it.

Link against `python3.lib` on Windows (as opposed to a version-specific `python3??.lib`). On Mac, pass `-Xlinker -undefined -Xlinker dynamic_lookup` and don't link Python at all (same as you would normally do with upstream Pybind). On Linux don't link Python at all (undefined references are not checked during library linking).

You must also build N `pybind11nonlimitedapi_MyLib_3.??` shared libraries, for each Python version you want to support (3.8, 3.9, etc), and distribute them as a part of your wheel. The correct library is selected at runtime.

Replace `MyLib` with the name of your library, using `-DPYBIND11_NONLIMITEDAPI_SUFFIX=MyLib` CMake flag. Since those libraries are not renamed when building a wheel, we must ensure the name is unique to avoid conflicts between different modules using this library.

Your own code needs be built with `-DPy_LIMITED_API=0x030800f0` (or any other value) and `-DPYBIND11_NONLIMITEDAPI_LIB_SUFFIX_FOR_MODULE=MyLib` (this must match the shim library naming, see above).

Then the `pybind11nonlimitedapi_MyLib_3.??` libraries must be distributed in the same directory as the `.pyd`/`.so` modules (or you can set `PYBIND11_NONLIMITEDAPI_SHIM_PATHS_RELATIVE_TO_LIBRARY_DIR` macro to a path relative to the modules, see that macro definition for details).

When baking the modules into a wheel, the `pybind11nonlimitedapi_MyLib_3.??` libraries must stay in the same directory as the modules. They don't get their names mangled.

If you use `delvewheel` on Windows, don't forget to add `--analyze-existing` to process the `pybind11nonlimitedapi_MyLib_3.??` libraries too.
