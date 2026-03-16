import os
import numpy as np

from highlight import highlight_changes, highlight_error
from matrix import create_matrix


if __name__ == "__main__":
    n = input("Введите число: ")

    k = 0
    arr = list(n)

    while 2 ** k < len(arr) + k:
        index = 2 ** k
        arr.insert(len(arr) - index + 1, "_")
        k += 1

    modified = "".join(arr)

    print("Без контрольной суммы:\t", modified)


    matrix = create_matrix(arr)

    for col in range(len(matrix[0])):
        num_index = -1
        num_sum = 0
        for row in range(len(matrix)):
            if matrix[row][col] == "1":
                if arr[-row - 1] == "_":
                    num_index = -row - 1
                else:
                    num_sum += int(arr[-row - 1])

        arr[num_index] = str(num_sum % 2)
    
    result = "".join(arr)

    print("С контрольной суммой:\t", highlight_changes(modified, result))      

    os.system("pause")


    print(f"Правильное число:\t{result}")
    n = input("Неправльное число:\t")

    arr = list(n)
    new_columns = []

    for col in range(len(matrix[0])):
        nums_sum = 0
        for row in range(len(matrix)):
            if matrix[row][col] == "1":
                nums_sum += int(arr[-row - 1])
        if nums_sum % 2 != 0:
            new_columns.append(matrix[:, col].reshape(-1, 1))
    
    new_matrix = np.hstack(new_columns) if new_columns else np.empty((len(matrix), 0))

    for row in range(len(new_matrix)):
        if all(cell == "1" for cell in new_matrix[row]):
            unconnect_num = arr[-row - 1]
            if unconnect_num == "1":
                arr[-row - 1] = "0"
            else:
                arr[-row - 1] = "1"
            break
    
    corrected_result = "".join(arr)

    print(f"Испарвленное число:\t{highlight_error(n, corrected_result)}")