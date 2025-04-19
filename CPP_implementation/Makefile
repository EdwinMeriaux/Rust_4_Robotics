# Compiler and flags
CXX := g++
CXXFLAGS := -Wall -O2 -std=c++17

# Homebrew paths
INCLUDE_PATH := -I/opt/homebrew/include
LIBRARY_PATH := -L/opt/homebrew/lib

# Libraries
LIBS := -lpng -ljsoncpp -pthread

# Target binary and source file
TARGET := bresenham_cpp
SRC := bresenham_cpp.cpp

# Build rule
all: $(TARGET)

$(TARGET): $(SRC)
	$(CXX) $(CXXFLAGS) $(INCLUDE_PATH) $(LIBRARY_PATH) -o $@ $^ $(LIBS)

# Clean rule
clean:
	rm -f $(TARGET)

.PHONY: all clean
