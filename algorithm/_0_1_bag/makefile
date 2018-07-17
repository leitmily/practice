CC := g++
CFLAGS := -Wall -g --std=c++11 -lpthread

OBJECTS := bag_0_1_finite.o
TARGET := test


$(TARGET): $(OBJECTS)
	$(CC) $(CFLAGS) -o $(TARGET) $(OBJECTS)
$(OBJS) : %.o: %.cpp
	$(CC) $(CFLAGS) -c $<

.PHONY:clean
clean:
	-rm -f $(TARGET) *.o