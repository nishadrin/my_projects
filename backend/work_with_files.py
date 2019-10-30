class work_with_files():
    """Save to file and read in different ways"""

    def read_lines_from_file(path):
        with open(path, "r", encoding="utf-8") as file:
            return [line.strip() for line in file.readlines()]

    def write_to_json_file(path, courses):
        with open(path, "w", encoding="utf-8") as file:
            file.write(json.dumps(courses, ensure_ascii=False))
        return True

    def write_lines_in_file(path, lines):
        with open(path, "w", encoding="utf-8") as file:
            [file.writelines(line) for line in lines]
        return True

    def save_text_in_file(path, text):
        with open(path, "w", encoding="utf-8") as file:
            file.write(text)
        return True
