import dataclasses

from worlds.fm.utils import Constants


# Run this file with `python -m worlds.fm.tracker.export_constants` at the root of AP
def python_dataclass_to_java(dataclass):
    java_code: str = "package moe.maika.fmaptracker;\n\npublic class Constants {\n"

    for field in dataclasses.fields(dataclass):
        java_type: str = field.type.__name__
        value: str = str(field.default)
        if field.type.__name__ == "int":
            java_type = "long"
            value = f"{field.default}L"
        elif field.type.__name__ == "str":
            java_type = "String"
            value = f'"{field.default}"'
        java_code += f"    public static final {java_type} {field.name} = {value};\n"

    java_code += "}\n"
    return java_code


if __name__ == "__main__":
    with open("Constants.java", "w") as java_file:
        java_file.write(python_dataclass_to_java(Constants))
