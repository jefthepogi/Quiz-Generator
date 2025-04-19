import os
from flask import Flask, request, render_template, redirect, url_for
from groq import Groq
import json
import pypdfium2 as pdfium
import re


app = Flask(__name__) # Initialize Flask app
jsonData = ""
items = 0
resultData = dict()

def get_ai_response(text, items: int): # Function to call the AI API
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": 'The questions you must ask must be relevant to the purpose of the whole text, for instance, scientific literatures must adhere to scientific questions. Avoid including superfluous informations like marginal data if there are any present. ' +
                'Create a' + f"{items}" + '-item quiz from the content below and extract it in a json object format like {quiz: [{question:, choices:, correctanswer:}]}:\n' + text
            },
            {
                "role": "assistant",
                "content": "json"    
            }
        ],
        model="llama-3.3-70b-versatile",
        temperature=0.3,
    )
    return response.choices[0].message.content

def validate_json(response):
    try:
        # print(response)
        return json.loads(response)
    except json.JSONDecodeError:
        print("invalid json format.")
        return None

def extractPDF(data: bytes) -> str:
    text = ""
    pdf = pdfium.PdfDocument(data)
    
    # Regex to match alphanumeric characters, spaces, and basic punctuation
    regex = re.compile(r"[^a-zA-Z0-9\s.,!?;:\-()'\"\n]")
    
    for i in range(len(pdf)):
        page = pdf.get_page(i)
        textpage = page.get_textpage()
        page_text = textpage.get_text_range()
        
        # Remove unwanted symbols using regex
        cleaned_text = regex.sub("", page_text)
        text += cleaned_text + "\n"

    return text

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generating", methods=["POST", "GET"])
def generateQuiz():
    global jsonData
    global items
    text = ""
    if request.method == "POST":
        fieldname = "usrinput"
        if fieldname in request.form:
            text = request.form.get(fieldname, "")
            print("text mode")
        elif fieldname in request.files:
            file = request.files.get(fieldname)
            file.save(f"uploads/{file.filename}")
            with open(f"uploads/{file.filename}", "rb") as f:
                data = f.read()
            text = extractPDF(data)
            print("document mode")

        items = request.form.get("quantity", 0)
        jsonData = validate_json(get_ai_response(text, items))
        return redirect(url_for("generated"))
    # request.method == "GET":
    return redirect(url_for("index"))
    
@app.route("/generated")
def generated():
    if jsonData == "":
        print("error: empty json data.")
        redirect(url_for("index"))
    return render_template("generate.html", responseData=jsonData, totalItems=items)

@app.route("/submitting", methods=["POST", "GET"])
def submitting():
    global resultData
    if request.method == "POST":
        result_json = request.form.get("usr-result", "")
        resultData = validate_json(result_json)
        return redirect(url_for("results"))
    return redirect(url_for("index"))

@app.route("/results")
def results():
    return render_template("results.html", resultData=resultData)

if __name__ == "__main__":
    app.run(host="localhost", port=8080, debug=True)