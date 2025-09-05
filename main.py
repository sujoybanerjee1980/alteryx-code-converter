
import os, json, shutil
from fastapi import FastAPI, UploadFile, File, Form, Request, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse, Response
from fastapi.responses import JSONResponse
from vertexai.generative_models import GenerativeModel as genai
import pandas as pd
from openai import AzureOpenAI as Agenai
import csv, io
from agents.utils_agent import get_input_folder, get_output_folder, get_source_functional_logic_folder, get_converted_files_folder, get_target_functional_logic_folder, get_files
from agents.conversion_agent import convert_files
from agents.extraction_agent import extract_files, extracted_output_files
from agents.lineage_agent import generate_lineage_reports
from agents.llm_agent import get_llm


app = FastAPI()
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

with open("config.json", "r") as config_file:
    config = json.load(config_file)
# API_KEY = config["api_key"]
# API_BASE = config["azure_endpoint"]
# API_VERSION = config["api_version"]
# DEPLOYMENT_ID = config["default_model"]

# llm_client = Agenai(api_key=API_KEY, azure_endpoint=API_BASE, api_version=API_VERSION)
# Ggenai.configure(api_key="AIzaSyCv3b6uhEf2jk88tcrT553JtGYb6FxvXu0")


# API ROUTES

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...), source: str = Form(...)):
    input_folder = get_input_folder(source)
    filepath = os.path.join(input_folder, file.filename)
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"filename": file.filename}


# MAIN EXTRACT LOGIC
@app.post("/extract-logic/")
async def extract_logic(
    ai: str = Form(...),
    model: str = Form(...),
    source: str = Form(...),
    target: str = Form(...)
):
    
    prompt_template = config.get("extraction_prompt_template", None)
    results, progress, extract_logic_input_tokens_list, extract_logic_output_tokens_list = extract_files(source, target, model, ai, prompt_template)
   
    return {"results": results, "extract_progress": progress, "extract_logic_input_tokens_list": extract_logic_input_tokens_list, "extract_logic_output_tokens_list": extract_logic_output_tokens_list}

# MAIN CONVERT LOGIC (Handles Any Tech)
@app.post("/convert/")
async def convert(
    ai: str = Form(...),
    model: str = Form(...),
    source: str = Form(...),
    target: str = Form(...)
):
    prompt_template = config.get("conversion_prompt_template", None)
    conversion_results, dashboard_results, progress, converted_input_tokens_list, converted_output_tokens_list = convert_files(source, target, model, ai, prompt_template)
    
    return {"conversion_results": conversion_results,
             "dashboard_results": dashboard_results,
             "convert_progress": progress,
             "converted_input_tokens_list": converted_input_tokens_list,
             "converted_output_tokens_list": converted_output_tokens_list
    }

@app.post("/extract-output-logic/")
async def extract_output_logic(
    body: dict = Body(...)
):
    ai = body.get("ai")
    model = body.get("model")
    target = body.get("target")
    files = body.get("files", [])  

    prompt_template = config.get("extraction_prompt_template", None)
    results, progress = extracted_output_files(target, files, prompt_template, model, ai)

    return {"results": results, "extract_output_progress": progress}


@app.post("/download-report")
async def download_report(request: Request):
    conversion_data = await request.json()
    fieldnames = list(conversion_data[0].keys()) if conversion_data else []
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    for row in conversion_data:
        writer.writerow(row)
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="text/csv",)

@app.post("/generate-lineage-dashboard/")
async def generate_lineage_dashboard(request: Request):
    data = await request.json()
    source_logic = data.get("source_logic", {})
    target_logic = data.get("target_logic", {})
    model = data.get("model")
    ai = data.get("ai")
    target = data.get("target")
    source = data.get("source")
    output_folder = get_output_folder(target)

    if not (source_logic and target_logic and isinstance(source_logic, dict) and isinstance(target_logic, dict)):
        return JSONResponse({"success": False, "msg": "Source and/or Target logic missing or invalid."})

    lineage_csvs, testcase_csvs, n_files, all_avg_completion = generate_lineage_reports(
        source_logic, target_logic, model, ai, output_folder, source, target
    )
  

    return {
        "lineage_ready": True, "testcase_ready": True, "n_files": n_files,
        "lineage_folder": os.path.relpath(os.path.dirname(lineage_csvs[0]), start=".") if lineage_csvs else "",
        "testcase_folder": os.path.relpath(os.path.dirname(testcase_csvs[0]), start=".") if testcase_csvs else "",
        "lineage_files": [os.path.basename(p) for p in lineage_csvs],
        "testcase_files": [os.path.basename(p) for p in testcase_csvs],
        "avg_completion_per_file": all_avg_completion,
        "msg": f"Lineage and Testcase reports saved in {os.path.dirname(lineage_csvs[0])} and {os.path.dirname(testcase_csvs[0])}, respectively"
    }

@app.get("/lineage-summary")
async def lineage_summary(target: str, filename: str):

    
    folder = os.path.join(get_output_folder(target), "lineage_reports")
    excel_path = os.path.join(folder, filename)
    if not os.path.isfile(excel_path):
        return JSONResponse({"success": False, "msg": f"File {filename} not found"}, status_code=404)
    try:
        df = pd.read_excel(excel_path)

        columns = []
        for i in [
            "S.No",
            "Business Functional Logic",
            "Source Functional Logic Description",
            "Target Functional Logic Description"
        ]:
            for col in df.columns:
                if i.lower().replace('.','').replace(' ','') in col.lower().replace('.','').replace(' ', ''):
                    columns.append(col)
                    break
            if len(columns) == 4:
                break
        
        if len(columns)<4:
            columns = df.columns[:4]
        data = [
            {col: str(row.get(col, "")) for col in columns}
            for idx, row in df[columns].iterrows()
        ]
        return {"success": True, "columns": columns, "data": data}
    except Exception as ex:
        return JSONResponse({"success": False, "msg": str(ex)}, status_code=500)


@app.get("/download-lineage-report/")
async def download_lineage_report(target: str, filename: str):
    folder = os.path.join(get_output_folder(target), "lineage_reports")
    fpath = os.path.join(folder, filename)
    if not os.path.isfile(fpath):
        return JSONResponse({"success": False, "msg": f"File {filename} not found"}, status_code=404)
 
    return FileResponse(fpath, filename=filename, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.get("/download-testcase-report/")
async def download_testcase_report(target: str, filename: str):
    folder = os.path.join(get_output_folder(target), "testcase_reports")
    fpath = os.path.join(folder, filename)
    if not os.path.isfile(fpath):
        return JSONResponse({"success": False, "msg": f"File {filename} not found"}, status_code=404)

    return FileResponse(fpath, filename=filename, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


@app.get("/view-file/")
async def view_file(target: str = Query(...), type: str = Query(...), filename: str = Query(...)):
    folder_map = {
        "source_functional_logic": get_source_functional_logic_folder(target),
        "target_functional_logic": get_target_functional_logic_folder(target),
        "converted_files": get_converted_files_folder(target),
    }
    
    root = folder_map.get(type)
    if not root:
        return Response("Invalid Type.", status_code=400)
    path = os.path.join(root, filename)
    if not os.path.isfile(path):
        return Response("File not found.", status_code=404)
    with open(path, "r",  encoding="utf-8") as f:
        content = f.read()
    return Response(content, media_type="text/plain")


from fastapi.security import HTTPBasicCredentials, HTTPBasic
from fastapi import HTTPException
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from agents.llm_agent import decrypts


import json
security = HTTPBasic()
load_dotenv()
@app.post("/api/login")
async def login(credentials: dict):
    with open("secret.key","rb") as key_file:
        key=key_file.read()
    cipher=Fernet(key)
    users=decrypts("users",cipher)
    users=json.loads(users)

    username = credentials["username"]
  
    password = credentials["password"]
    if username in users and users[username] == password:
        
        return {"message": "Login successful"}
    else:
        raise HTTPException(status_code=401, detail="Incorrect username or password")