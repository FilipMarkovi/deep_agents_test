def calculate_average(scores):
    total = sum(scores)
    average = total / len(scores)
    print("The calculated average score is: " + str(average))
    return average

if __name__ == "__main__":
    calculate_average([])
