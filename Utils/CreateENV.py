from python_get_resolve import GetResolve
import os
import inspect

OUTPUT_ROOT = "../stubs/davinci_resolve"
os.makedirs(OUTPUT_ROOT, exist_ok=True)


def safe_signature(func):
    try:
        return str(inspect.signature(func))
    except Exception:
        return "(self, *args, **kwargs)"


def write_stub_file(class_name, methods, attributes):
    filepath = os.path.join(OUTPUT_ROOT, f"{class_name.lower()}.pyi")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"class {class_name}:\n")

        if not methods and not attributes:
            f.write("    pass\n")
            return

        for attr in attributes:
            f.write(f"    {attr}: object\n")

        for name, sig in methods.items():
            f.write(f"    def {name}{sig}: ...\n")

    print("Generated:", filepath)


def extract_object(obj, class_name):
    methods = {}
    attributes = []

    for name in dir(obj):
        if name.startswith("_"):
            continue

        try:
            value = getattr(obj, name)
        except Exception:
            continue

        if callable(value):
            methods[name] = safe_signature(value)
        else:
            attributes.append(name)

    write_stub_file(class_name, methods, attributes)


def main():
    resolve = GetResolve()
    if not resolve:
        raise RuntimeError("Resolve not found")

    pm = resolve.GetProjectManager()
    project = pm.GetCurrentProject()
    timeline = project.GetCurrentTimeline()
    fusion = resolve.Fusion()

    # 核心对象
    extract_object(resolve, "Resolve")
    extract_object(pm, "ProjectManager")
    extract_object(project, "Project")
    extract_object(timeline, "Timeline")
    extract_object(fusion, "Fusion")

    # bmd
    try:
        import bmd
        extract_object(bmd, "bmd")
    except Exception:
        print("bmd not available")

    # 生成 __init__.pyi
    with open(os.path.join(OUTPUT_ROOT, "__init__.pyi"), "w") as f:
        f.write("from .resolve import Resolve\n")
        f.write("from .projectmanager import ProjectManager\n")
        f.write("from .project import Project\n")
        f.write("from .timeline import Timeline\n")
        f.write("from .fusion import Fusion\n")
        f.write("from .bmd import bmd\n")

    print("Stub generation completed.")


if __name__ == "__main__":
    main()