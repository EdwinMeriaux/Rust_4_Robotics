# Compiler and flags
CC = gcc
CFLAGS = -Wall -O2 -Wno-format-truncation

LDFLAGS = -lpng -ljson-c -lpthread

# Target executable
TARGET = bresenham_c

# Source file
SRC = bresenham_c.c

# Build target
all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) $(SRC) -o $(TARGET) $(LDFLAGS)

# Clean target
clean:
	rm -f $(TARGET)
