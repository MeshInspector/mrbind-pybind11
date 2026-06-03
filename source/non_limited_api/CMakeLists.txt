cmake_minimum_required(VERSION 3.10)

set (CMAKE_CXX_STANDARD 17) # For `std::filesystem::weakly_canonical()`.

# Attempt to add link library "Python::Python" to target "pybind11nonlimitedapi_3.X" which is not built in this directory.
# This is allowed only when policy CMP0079 is set to NEW.
cmake_policy(SET CMP0079 NEW)

if (MSVC)
  # Don't assume that extern C functions don't throw exceptions, because ours do throw.
  # The default flag is `/EHsc`, while we want only `/EHs`, so we remove the `c` part with this `/EHc-`.
  add_compile_options( /EHc- )
  # Disabling following warnings:
  #   warning C4191: 'reinterpret_cast': unsafe conversion
  set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /wd4191")
endif()

if (NOT WIN32)
  # Get rid of `-Wl,-z,defs` if someone has added it to our flags.
  # On platforms other than Windows, we rely on not linking Python and
  #   not getting undefined references from that (because any form of linking there would lock us to a specific minor version).
  string(REPLACE "-Wl,-z,defs" "" CMAKE_SHARED_LINKER_FLAGS "${CMAKE_SHARED_LINKER_FLAGS}")
endif()

if (DEFINED PYBIND11_NONLIMITEDAPI_PYTHON_HEADERS_VERSION)
  find_package(Python ${PYBIND11_NONLIMITEDAPI_PYTHON_HEADERS_VERSION} EXACT REQUIRED COMPONENTS Interpreter Development)
else()
  find_package(Python REQUIRED COMPONENTS Interpreter Development)
endif()

option(PYBIND11_NONLIMITEDAPI_BUILD_STUBS "Build the stubs library." ON)

set(PYBIND11_NONLIMITEDAPI_PYTHON_MIN_VERSION_HEX "0x030800f0" CACHE STRING "A hex Python version to bake into the library, e.g. `0x030800f0` for 3.8 (the `f0` suffix is always there and means a release version).")
set(PYBIND11_NONLIMITEDAPI_SUFFIX "" CACHE STRING "A custom suffix to append to the built library name.")
set(PYBIND11_NONLIMITEDAPI_LIBRARY_OUTPUT_DIR "" CACHE PATH "Replaces the library installation path for the shim.")

include(GNUInstallDirs)

set(PYBIND11_NONLIMITEDAPI_INSTALL_LIBDIR_STUBS "${CMAKE_INSTALL_LIBDIR}" CACHE PATH "Where to install the stub library.")
set(PYBIND11_NONLIMITEDAPI_INSTALL_LIBDIR_SHIMS "${CMAKE_INSTALL_LIBDIR}" CACHE PATH "Where to install the shim library.")

option(PYBIND11_NONLIMITEDAPI_INSTALL_EXPORTS "Whether to install the cmake configs for our libraries." OFF)

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

  install(
    TARGETS ${PROJECT_NAME}
    EXPORT ${PROJECT_NAME}-targets
    ARCHIVE DESTINATION ${PYBIND11_NONLIMITEDAPI_INSTALL_LIBDIR_STUBS}
    LIBRARY DESTINATION ${PYBIND11_NONLIMITEDAPI_INSTALL_LIBDIR_STUBS}
  )
  if (PYBIND11_NONLIMITEDAPI_INSTALL_EXPORTS)
    install(
      EXPORT ${PROJECT_NAME}-targets
      NAMESPACE pybind11nonlimitedapi::
      DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/pybind11nonlimitedapi
    )
  endif()

  if (APPLE)
    target_link_options(${PROJECT_NAME} PRIVATE -undefined dynamic_lookup)
  endif()
endif()

if ("${PYBIND11_NONLIMITEDAPI_SUFFIX}" STREQUAL "")
  message("Not building shim because PYBIND11_NONLIMITEDAPI_SUFFIX is not specified")
else()
  if (NOT "${PYBIND11_NONLIMITEDAPI_SUFFIX}" STREQUAL "")
    set(PYBIND11_NONLIMITEDAPI_UNDERSCORE "_")
  else()
    set(PYBIND11_NONLIMITEDAPI_UNDERSCORE "")
  endif()

  set(PYBIND11_NONLIMITEDAPI_LIBNAME "pybind11nonlimitedapi_${PYBIND11_NONLIMITEDAPI_SUFFIX}_${Python_VERSION_MAJOR}.${Python_VERSION_MINOR}")
  project(${PYBIND11_NONLIMITEDAPI_LIBNAME})
  add_library(${PROJECT_NAME} SHARED non_limited_api.cpp)

  # Probably not the smartest move to mark this directory private, but it's easier than figuring out the proper way.
  target_include_directories(${PROJECT_NAME} PRIVATE ../../include)
  target_include_directories(${PROJECT_NAME} PUBLIC ${Python_INCLUDE_DIRS})
  if (PYBIND11_NONLIMITEDAPI_BUILD_STUBS)
    target_link_libraries(${PROJECT_NAME} PUBLIC pybind11nonlimitedapi_stubs)
  else()
    find_package(pybind11nonlimitedapi REQUIRED)
    target_link_libraries(${PROJECT_NAME} PUBLIC pybind11nonlimitedapi::pybind11nonlimitedapi_stubs)
  endif()

  if (MSVC)
    target_link_libraries(${PROJECT_NAME} PUBLIC python${Python_VERSION_MAJOR}${Python_VERSION_MINOR})
  else()
    target_link_libraries(${PROJECT_NAME} PUBLIC Python::Python)
  endif()

  if (APPLE)
    target_link_options(${PROJECT_NAME} PRIVATE -undefined dynamic_lookup)
  endif()

  if (NOT("${PYBIND11_NONLIMITEDAPI_LIBRARY_OUTPUT_DIR}" STREQUAL ""))
    # For Windows.
    set_target_properties(${PROJECT_NAME} PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${PYBIND11_NONLIMITEDAPI_LIBRARY_OUTPUT_DIR}")
    # For everything else...
    set_target_properties(${PROJECT_NAME} PROPERTIES LIBRARY_OUTPUT_DIRECTORY "${PYBIND11_NONLIMITEDAPI_LIBRARY_OUTPUT_DIR}")
  endif()

  install(
    TARGETS ${PROJECT_NAME}
    EXPORT ${PROJECT_NAME}-targets
    ARCHIVE DESTINATION ${PYBIND11_NONLIMITEDAPI_INSTALL_LIBDIR_SHIMS}
    LIBRARY DESTINATION ${PYBIND11_NONLIMITEDAPI_INSTALL_LIBDIR_SHIMS}
  )
  if (PYBIND11_NONLIMITEDAPI_INSTALL_EXPORTS)
    install(
      EXPORT ${PROJECT_NAME}-targets
      NAMESPACE pybind11nonlimitedapi::
      DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/pybind11nonlimitedapi
    )
  endif()
endif()

if (PYBIND11_NONLIMITEDAPI_INSTALL_EXPORTS)
  include(CMakePackageConfigHelpers)
  configure_package_config_file(
    pybind11nonlimitedapi-config.cmake.in
    ${CMAKE_CURRENT_BINARY_DIR}/pybind11nonlimitedapi-config.cmake
    INSTALL_DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/pybind11nonlimitedapi
  )
  install(
    FILES ${CMAKE_CURRENT_BINARY_DIR}/pybind11nonlimitedapi-config.cmake
    DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/pybind11nonlimitedapi
  )
endif()
