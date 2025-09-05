import os
from agents.utils_agent import get_input_folder, get_files, get_output_ext, get_converted_files_folder, get_source_functional_logic_folder
from datetime import datetime
import xml.etree.ElementTree as ET
from vertexai.generative_models import GenerativeModel as genai
import re
import time
from vertexai.preview.language_models import ChatModel
from agents.llm_agent import get_llm
from agents.coding_standards_agent import pyspark_coding_standards, dbt_coding_standards
from agents.extraction_agent import count_input_tokens


def get_template(workflow_text, extracted_func_logic, source, target, out_ext, standards, prompt_template = None):


    prompt_template = (f"""Convert the following {source.capitalize()} workflow into a fully functional {target.capitalize()} script. 
            only use the output format specified: {out_ext.upper()}.

            Follow These {target} coding standards:
            {standards}

            Instructions:
            -Do not mix multiple languages (eg. SQL, Python etc).
            -only use the {out_ext.upper()} format.
            -Do not include any explanation or extra text - output only the converted code.
            -If any values/variables contains "ID_" just keep the exact value dont change.
            -Add meaningful and helpful comments in the code where appropriate. 
            ##Source code workflow
            ({source.capitalize()}) : {workflow_text}
            ##Source Functional Logic
            ({source.capitalize()} functional logic): {extracted_func_logic}
            Converted ({target.capitalize()}) code in {out_ext.upper()}:
            
            """)
    return prompt_template

def conversion_prompt(workflow_text,extracted_func_logic, source, target, out_ext, prompt_template = None):
    if not prompt_template:
        if target == "dbt":
            standards = dbt_coding_standards()
            prompt_template = get_template(workflow_text, extracted_func_logic, source, target, out_ext, standards, prompt_template = None)
        elif target == "pyspark":
            standards = pyspark_coding_standards()
            prompt_template = get_template(workflow_text, extracted_func_logic, source, target, out_ext, standards, prompt_template = None)
        
        else:
            prompt_template = (f"""Convert the following {source.capitalize()} workflow into a fully functional {target.capitalize()} script. 
                only use the output format specified: {out_ext.upper()}.

                Instructions:
                -Do not mix multiple languages (eg. SQL, Python etc).
                -only use the {out_ext.upper()} format.
                -Do not include any explanation or extra text - output only the converted code.
                -Add meaningful and helpful comments in the code where appropriate.
                ##Source workflow
                ({source.capitalize()}) : {workflow_text}
                ##Source Functional Logic
                ({source.capitalize()} functional logic): {extracted_func_logic}
                Converted ({target.capitalize()}) code in {out_ext.upper()}:""")
        return prompt_template

def convert_files(source, target, model, ai_provider, prompt_template=None):
    get_llm(ai_provider)
    model = genai(model)
    input_folder = get_input_folder(source)
    output_folder = get_converted_files_folder(target)
    files = get_files(input_folder, source)
    output_ext = get_output_ext(target)
    no_of_files = 0
    start_time = time.time()
    conversion_results = []
    dashboard_results = []
    input_tokens_list = 0
    output_tokens_list = 0

    progress = {"current": 0, "total": len(files)}
    for idx, filename in enumerate(files):
        with open(os.path.join(input_folder, filename), "r", encoding="utf-8") as fin:
            workflow_text = fin.read()
        output_ext = get_output_ext(target)

        basename = os.path.splitext(filename)[0]
        src_func_logic_folder = get_source_functional_logic_folder(target)
        src_func_logic_path = os.path.join(src_func_logic_folder, f"{basename}_{source}_logic.md")
        if(os.path.exists(src_func_logic_path)):
            with open(src_func_logic_path, "r", encoding="utf-8") as flogic:
                extracted_logic_text = flogic.read()
        else:
            extracted_logic_text = ""
            masked_func_logic, func_mapping = "", {}

        prompt = conversion_prompt(workflow_text, extracted_logic_text, source, target, output_ext, prompt_template)
        # add message
        try:
            if ai_provider == "azure":
                llm_client = get_llm(ai_provider)
                response = llm_client.chat.completions.create(model = model, messages = messages)
                code = response.choices[0].message.content.strip()
            elif ai_provider == "google":
                response = model.generate_content(messages)
                code = response.text.strip()
                
                input_tokens = count_input_tokens(messages)
                output_tokens=count_input_tokens(code)
            else:
                code = "Unknown AI provider"
        except Exception as e:
            code = f"Error: {str(e)}"
        

        base = os.path.splitext(filename)[0]
        outname = f"{base}_{source}_to_{target}{output_ext}"
        output_path = os.path.join(output_folder, outname)
        with open(output_path, "w", encoding="utf-8") as fout:
            fout.write(code)
        conversion_results.append({
            "Input File": filename, 
            "Output File": output_path.replace(output_folder, ""),
            "Time Generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        no_of_files += 1
        progress["current"] = idx+1
        input_tokens_list += input_tokens
        output_tokens_list += output_tokens
        
    end_time = time.time()
    time_taken_sec = end_time - start_time
    if time_taken_sec>60:
        time_taken_str = f"{int(time_taken_sec)//60} Minutes"
    else:
        time_taken_str = f"{int(time_taken_sec)} Seconds"
    dashboard_results.append({
            "source" : source,
            "target" : target,
            "artefactsConverted" : no_of_files,
            "timeTaken" : time_taken_str

    })
    
    return conversion_results, dashboard_results, progress, input_tokens_list, output_tokens_list

