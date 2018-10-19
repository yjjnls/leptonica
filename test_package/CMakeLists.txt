cmake_minimum_required(VERSION 2.8.11)
project(test_package)

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()

add_executable(${PROJECT_NAME} test_package.cpp)
if(CMAKE_SYSTEM_NAME STREQUAL Emscripten)
    list(REMOVE_ITEM CONAN_LIBS jpeg  )
    set(COMPILE_FLAGS " -Wno-missing-prototypes")
    set(LINK_FLAGS " -Wno-missing-prototypes")
    set_property(TARGET ${PROJECT_NAME} PROPERTY LINK_FLAGS ${LINK_FLAGS})
endif()
target_link_libraries(${PROJECT_NAME} ${CONAN_LIBS})
