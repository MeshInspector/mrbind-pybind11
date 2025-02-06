cmake_minimum_required(VERSION 3.10)

set (CMAKE_CXX_STANDARD 17) # For `std::filesystem::weakly_canonical()`.

# Attempt to add link library "Python::Python" to target "pybind11nonlimitedapi_3.X" which is not built in this directory.
# This is allowed only when policy CMP0079 is set to NEW.
cmake_policy(SET CMP0079 NEW)

if (MSVC)
  # Don't assume that extern C functions don't throw exceptions, because ours do throw.
  # The default flag is `/EHsc`, while we want only `/EHs`, so we remove the `c` part with this `/EHc-`.
  add_compile_options( /EHc- )
endif()

if (DEFINED PYBIND11_NONLIMITEDAPI_PYTHON_HEADERS_VERSION)
  find_package(Python ${PYBIND11_NONLIMITEDAPI_PYTHON_HEADERS_VERSION} EXACT REQUIRED COMPONENTS Interpreter Development)
else()
  find_package(Python REQUIRED COMPONENTS Interpreter Development)
endif()

option(PYBIND11_NONLIMITEDAPI_BUILD_STUBS "" ON)

set(PYBIND11_NONLIMITEDAPI_PYTHON_MIN_VERSION_HEX "" CACHE STRING "A hex Python version to bake into the library, e.g. `0x030800f0` for 3.8 (the `f0` suffix is always there and means a release version).")
set(PYBIND11_NONLIMITEDAPI_SUFFIX "" CACHE STRING "A custom suffix to append to the built library name. Should normally be `[_AppName][_X.Y]`, where X,Y is the Python version.")
set(PYBIND11_NONLIMITEDAPI_LIBRARY_OUTPUT_DIR "" CACHE PATH "Replaces the library installation path for the shim.")

include(GNUInstallDirs)

set(PYBIND11_NONLIMITEDAPI_INSTALL_LIBDIR_STUBS "${CMAKE_INSTALL_LIBDIR}" CACHE PATH "Where to install the stub library.")
set(PYBIND11_NONLIMITEDAPI_INSTALL_LIBDIR_SHIMS "${CMAKE_INSTALL_LIBDIR}" CACHE PATH "Where to install the shim library.")

if (${PYBIND11_NONLIMITEDAPI_BUILD_STUBS})
  project(pybind11nonlimitedapi_stubs)
  add_library(${PROJECT_NAME} SHARED non_limited_api_stubs.cpp)

  # Probably not the smartest move to mark this directory private, but it's easier than figuring out the proper way.
  target_include_directories(${PROJECT_NAME} PRIVATE ../../include)
  target_include_directories(${PROJECT_NAME} PUBLIC ${Python_INCLUDE_DIRS})
  target_compile_definitions(${PROJECT_NAME} PUBLIC PYBIND11_NONLIMITEDAPI_LIB_SUFFIX_FOR_MODULE=\"${PYBIND11_NONLIMITEDAPI_SUFFIX}\")

  # We don't link the entire `Python::Python` here because that's minor-version-dependent. It's not entirely clear to me what's the stable-ABI equivalent.
  # On Mac and Linux, not linking anything at all seems to work so far. But on Windows the Python header forces `python3.lib` (in this case,
  #   but in generaldepends on `Py_LIMITED_API` and some other things), so we need the correct library directories to be set.
  if (MSVC)
    target_link_directories(${PROJECT_NAME} PUBLIC ${Python_LIBRARY_DIRS})
  endif()

  install(TARGETS ${PROJECT_NAME} EXPORT ${PROJECT_NAME}
    ARCHIVE DESTINATION ${PYBIND11_NONLIMITEDAPI_INSTALL_LIBDIR_STUBS}
    LIBRARY DESTINATION ${PYBIND11_NONLIMITEDAPI_INSTALL_LIBDIR_STUBS}
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
  )
  install(
    EXPORT ${PROJECT_NAME}
    NAMESPACE pybind11nonlimitedapi::
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/pybind11nonlimitedapi/cmake
  )

  if (APPLE)
    target_link_options(${PROJECT_NAME} PRIVATE -undefined dynamic_lookup)
  endif()
endif()

if (PYBIND11_NONLIMITEDAPI_PYTHON_MIN_VERSION_HEX STREQUAL "")
  message("Not building shim because no Python version is specified.")
else()
  set(PYBIND11_NONLIMITEDAPI_LIBNAME "pybind11nonlimitedapi${PYBIND11_NONLIMITEDAPI_SUFFIX}_${Python_VERSION_MAJOR}.${Python_VERSION_MINOR}")
  project(${PYBIND11_NONLIMITEDAPI_LIBNAME})
  add_library(${PROJECT_NAME} SHARED non_limited_api.cpp)

  # Probably not the smartest move to mark this directory private, but it's easier than figuring out the proper way.
  target_include_directories(${PROJECT_NAME} PRIVATE ../../include)
  target_include_directories(${PROJECT_NAME} PUBLIC ${Python_INCLUDE_DIRS})
  target_link_libraries(${PROJECT_NAME} PUBLIC pybind11nonlimitedapi_stubs)
  target_link_libraries(${PROJECT_NAME} PUBLIC Python::Python)

  if (APPLE)
    target_link_options(${PROJECT_NAME} PRIVATE -undefined dynamic_lookup)
  endif()

  if (NOT("${PYBIND11_NONLIMITEDAPI_LIBRARY_OUTPUT_DIR}" STREQUAL ""))
    set_target_properties(${PROJECT_NAME} PROPERTIES LIBRARY_OUTPUT_DIRECTORY ${PYBIND11_NONLIMITEDAPI_LIBRARY_OUTPUT_DIR})
  endif()

  install(TARGETS ${PROJECT_NAME} EXPORT ${PROJECT_NAME}
    ARCHIVE DESTINATION ${PYBIND11_NONLIMITEDAPI_INSTALL_LIBDIR_SHIMS}
    LIBRARY DESTINATION ${PYBIND11_NONLIMITEDAPI_INSTALL_LIBDIR_SHIMS}
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
  )
  install(
    EXPORT ${PROJECT_NAME}
    NAMESPACE pybind11nonlimitedapi::
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/pybind11nonlimitedapi/cmake
  )
endif()
