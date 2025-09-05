import os

def get_tech_info():
    tech_info = {
        "alteryx": {"input_ext": [".yxmd"], "output_ext": ".yxmd"},
        "dbt": {"input_ext": [".sql"], "output_ext": ".sql"},
        "pyspark": {"input_ext": [".sql", ".py"], "output_ext": ".py"}
    }
    return tech_info


def ensure_folder(path):
    os.makedirs(path, exist_ok=True)
    return path

def get_input_folder(source):
    folder = f"./inputs/{source}/"
    ensure_folder(folder)
    return folder

def get_output_folder(target):
    folder = f"outputs/{target}/"
    ensure_folder(folder)
    return folder


def get_source_functional_logic_folder(target):
    folder = f"outputs/{target}/Source Functional Logic/"
    ensure_folder(folder)
    return folder

def get_converted_files_folder(target):
    folder = f"outputs/{target}/Converted FIles/"
    ensure_folder(folder)
    return folder

def get_target_functional_logic_folder(target):
    folder = f"outputs/{target}/Target Functional Logic/"
    ensure_folder(folder)
    return folder

def get_files(folder, source, exts=None):
    tech_info = get_tech_info()
    exts = tech_info[source]["input_ext"]
    files =[f for f in os.listdir(folder) if f.lower().endswith(tuple(exts))] 
    return files

def get_output_ext(target):
    tech_info = get_tech_info()
    return tech_info[target]["output_ext"]
