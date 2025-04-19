# Compiler and flags
CC = gcc
CFLAGS = -Wall -O2 \
	-I/opt/homebrew/opt/libpng/include \
	-I/opt/homebrew/opt/json-c/include

LDFLAGS = -L/opt/homebrew/opt/libpng/lib \
	-L/opt/homebrew/opt/json-c/lib \
	-lpng -lpthread -ljson-c

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
