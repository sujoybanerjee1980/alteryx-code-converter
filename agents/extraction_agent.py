import os
from agents.utils_agent import get_input_folder, get_files, get_tech_info, get_target_functional_logic_folder, get_source_functional_logic_folder, get_converted_files_folder
from vertexai.preview.language_models import ChatModel
from agents.llm_agent import get_llm
from vertexai.generative_models import GenerativeModel as genai
import tiktoken

def count_input_tokens(text:str,model="gpt-4o-mini")->int:
    encoding=tiktoken.encoding_for_model(model)
    return(len(encoding.encode(text)))



def extraction_output_prompt(converted_code, target, prompt_template = None):
    input_extension = get_tech_info()
    if not prompt_template:
        prompt_template = (f"""You are expert at explaining the functional logic of {target} workflow files.
        You will be given an {target} workflow file with {input_extension[target]["input_ext"]} extension.
        {target} workflow file : {converted_code}
        Please extract the input, tools , output and connections in the workflow.
        Briefly explain in simple language what each tool does and what are its input and output.
        Please put all the tools information as a table: Tool ID, Description, Input, Output.
        Please provide text-based workflow diagram(ASCII Art) with all connections and ToolID for each node.
        """
        )

        return prompt_template.replace("{source}", target) + "\n" + converted_code


def extraction_prompt(workflow_text, source, prompt_template = None):
    input_extension = get_tech_info()
    if not prompt_template:
        prompt_template = (f"""You are expert at explaining the functional logic of {source} workflow files.
        You will be given an {source} workflow file with {input_extension[source]["input_ext"]} extension.
        {source} workflow file : {workflow_text}
        Please extract the input, tools , output and connections in the workflow.
        Briefly explain in simple language what each tool does and what are its input and output.
        Please put all the tools information as a table: Tool ID, Description, Input, Output.
        Please provide text-based workflow diagram(ASCII Art) with all connections and ToolID for each node."""
        )
        return prompt_template.replace("{source}", source) + "\n" + workflow_text



def extract_files(source, target, model, ai_provider, prompt_template = None):
    get_llm(ai_provider)
    model = genai(model)
    
    input_folder = get_input_folder(source)
    output_folder = get_source_functional_logic_folder(target)
    files = get_files(input_folder, source)
    results = {}
    input_tokens_list = 0
    output_tokens_list = 0
    progress = {"current": 0, "total": len(files)}
    for idx, filename in enumerate(files):
        with open(os.path.join(input_folder, filename), "r", encoding="utf-8") as fin:
            workflow_text = fin.read()
        
        prompt = extraction_prompt(workflow_text, source, prompt_template)
        messages = f"role: system, content: You are an AI expert extracting logic from {source}, role: user, content: {prompt}"
        try:
            if ai_provider == "azure":
                llm_client = get_llm(ai_provider)
                response = llm_client.chat.completions.create(model = model, messages = messages)
                explanation = response.choices[0].message.content.strip()
            elif ai_provider == "google":
                response = model.generate_content(messages)
                explanation = response.text.strip()
                input_tokens = count_input_tokens(messages)
                output_tokens=count_input_tokens(explanation)

            else:
                explanation = "Unknown AI provider"
        except Exception as e:
            explanation = f"Error: {str(e)}"

        base = os.path.splitext(filename)[0]
        ext = ".md"
        outname = f"{base}_{source}_logic{ext}"
        output_path = os.path.join(output_folder, outname)
        with open(output_path, "w", encoding="utf-8") as fout:
            fout.write(explanation)
        results[filename] = explanation
        progress["current"] = idx+1
        input_tokens_list += input_tokens
        output_tokens_list += output_tokens
    return results, progress, input_tokens_list, output_tokens_list


def extracted_output_files(target, files, prompt_template, model, ai_provider):
    #get_llm(ai_provider)
    model = genai(model)

    converted_output_folder = get_converted_files_folder(target)
    target_output_folder = get_target_functional_logic_folder(target)
    results = {}
    progress = {"current": 0, "total": len(files)}
    for idx, relpath in enumerate(files):
        filename = os.path.basename(relpath)
        filepath = os.path.join(converted_output_folder, filename)
        base = os.path.splitext(filename)[0]
        logic_outname = f"{base}_logic.md"
        logic_path = os.path.join(target_output_folder, logic_outname)

        if not os.path.isfile(filepath):
            results[filename] = "File not found"
            continue

        with open(filepath, "r", encoding="utf-8") as fin:
            workflow_text = fin.read()

        # Use same extraction logic as extraction_agent
        prompt = extraction_output_prompt(workflow_text, target, prompt_template)
        messages = f"role: system, content: You are an AI expert extracting logic from {target}, role: user, content: {prompt}"

        try:
            if ai_provider == "azure":
                llm_client = get_llm(ai_provider)
                response = llm_client.chat.completions.create(model=model, messages=messages)
                explanation = response.choices[0].message.content.strip()
            elif ai_provider == "google":
                response = model.generate_content(messages)
                explanation = response.text.strip()
                input_tokens = count_input_tokens(messages)
                output_tokens=count_input_tokens(explanation)
            else:
                explanation = "Unknown AI provider"
        except Exception as e:
            explanation = f"Error: {str(e)}"
        
        try:
            with open(logic_path, "w", encoding="utf-8") as fout:
                fout.write(explanation)
        except Exception as e:
            explanation = f"\n\n (Saving to {logic_path} failed : {str(e)}"
        results[filename] = explanation
        progress["current"] = idx+1
    return results, progress

