from os import PathLike


import os


class TemplateEngine:
    def __init__(self, dir: PathLike) -> None:
        self.dir = dir if dir.endswith("/") else dir + "/"
        self.files = self.load_templates()

    def load_templates(self) -> list:
        files: list = []
        for file in os.listdir(self.dir):
            if file.endswith(".html"):
                files.append(file)
        return files

    def get_content(self, filename: str) -> bytes:
        with open(f"{self.dir}{filename}", "r") as f:
            data: str = f.read()
        return (data, bytes(data, "utf-8"))

    def render(self, template: str, **kwargs) -> bytes:
        if template in self.files:
            content: str = self.get_content(template)[0]
            for var in kwargs.keys():
                if "{{ %s }}" % var in content or "{{%s}}" % var:
                    content = content.replace("{{ %s }}" % var, kwargs.get(
                        var)).replace("{{%s}}" % var, kwargs.get(var))
            return bytes(content, "utf-8")
        else:
            raise FileNotFoundError("No such template exists")
