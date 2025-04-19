# importing the multiprocessing module
import multiprocessing

def print_cube(num):
    """
    function to print cube of given num
    """
    print("Cube: {}".format(num * num * num))

def print_square(num):
    """
    function to print square of given num
    """
    print("Square: {}".format(num * num))

if __name__ == "__main__":
    # creating processes
    process_list = []
    for i in range(2):
        p = multiprocessing.Process(target=print_square, args=(10, ))
        p.start()
        process_list.append(p)
        #p2 = multiprocessing.Process(target=print_cube, args=(10, ))

    for p in process_list:
        p.join()

    # both processes finished
    print("Done!")
