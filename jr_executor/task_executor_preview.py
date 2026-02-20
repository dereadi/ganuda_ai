import os

def preview_task_executor() -> None:
    """
    Preview the first 10 lines of the task_executor.py file.
    """
    file_path = '/ganuda/jr_executor/task_executor.py'
    
    if not os.path.exists(file_path):
        print(f"File {file_path} does not exist.")
        return
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()[:10]
            for line in lines:
                print(line, end='')
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")

if __name__ == "__main__":
    preview_task_executor()