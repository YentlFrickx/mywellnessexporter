import io

from flask import Flask, request, flash, redirect, send_file
import json
import os
import mywellnessfit
app=Flask(__name__)

ALLOWED_EXTENSIONS = {'json'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/uploadjson', methods=['POST','GET'])
def uploadJson():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect("index.html")
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect("index.html")
        if file and allowed_file(file.filename):
            data = file.read()
            jsonData = json.loads(data.decode('utf-8'))
            jsonData["data"]["time"] = request.form["time"]
            filePath = mywellnessfit.convert(jsonData)

            return_data = io.BytesIO()
            with open(filePath, 'rb') as fo:
                return_data.write(fo.read())
            # (after writing, cursor will be at last byte, so move it to start)
            return_data.seek(0)

            os.remove(filePath)

            return send_file(return_data, mimetype='application/vnd.ant.fit',
                             download_name='converted.fit')

            # return send_file(filePath, as_attachment=True)

@app.route("/")
def index():
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form action='/uploadjson' method=post enctype=multipart/form-data>
      <input type=file name=file required>
      <input type="time" name="time" required>
      <input type=submit value=Upload>
    </form>'''