from tools.base import BaseTool
import os


class FilesystemTool(BaseTool):

    def execute(self, filename):

        if not os.path.exists(filename):
            return "File not found."

        with open(filename, "r", encoding="utf-8") as file:
            return file.read()
        
    def read(self, filename):

         return self.execute(filename)   
    
    def write(self, filename, content):

        with open(filename, "w", encoding="utf-8") as file:
            file.write(content)

        return "✅ File updated."
    
    def list_directory(self, path="."):

        items = os.listdir(path)

        return "\n".join(items)
    

    def tree(self, path=".", prefix=""):

        output = ""

        items = sorted(os.listdir(path))

        for index, item in enumerate(items):

            full_path = os.path.join(path, item)

            connector = "└── " if index == len(items)-1 else "├── "

            output += prefix + connector + item + "\n"

            if os.path.isdir(full_path):

                extension = "    " if index == len(items)-1 else "│   "

                output += self.tree(full_path, prefix + extension)

        return output
    
    def read_project(self, path="."):

        project = ""

        for root, dirs, files in os.walk(path):

            for file in files:

                if file.endswith(".py"):

                    filepath = os.path.join(root, file)

                    try:

                        with open(filepath, "r", encoding="utf-8") as f:

                            project += f"\n\n===== {filepath} =====\n"

                            project += f.read()

                    except:

                        pass

        return project