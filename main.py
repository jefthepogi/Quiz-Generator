import os
from flask import Flask, request, render_template, redirect, url_for
from groq import Groq
import json

# Initialize Flask app
app = Flask(__name__)
jsonData = ""
items = 0
resultData = dict()

# Function to call the AI API
def get_ai_response(user_input, items: int):
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": 'Create a' + f"{items}" + '-item quiz from the content below and extract it in a json object format like {quiz: [{question:, choices:, correctanswer:}]}:\n' + user_input + "\n",
            },
            {
                "role": "assistant",
                "content": "```json"
            }
        ],
        model="llama-3.3-70b-versatile",
        temperature=0.4,
    )
    return response.choices[0].message.content.replace("```", "")

def validate_json(response):
    try:
        print(response)
        return json.loads(response)
    except json.JSONDecodeError:
        print("invalid json format.")
        return None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generating", methods=["POST", "GET"])
def generateQuiz():
    global jsonData
    global items
    if request.method == "POST":
        # Get the form data
        user_input = request.form.get("usrinput", "")  # This matches the form field name "usrinput"
        items = request.form.get("quantity", 0)
        jsonData = validate_json(get_ai_response(user_input, items))
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