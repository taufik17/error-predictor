from flask import Flask, redirect, request, render_template, send_file, url_for, session
import pandas as pd
from keras.models import load_model
import io
import base64

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Set a secret key for the session

# Enable debug mode
app.config['DEBUG'] = True

# Load model
model = load_model('best3299v2.h5', compile=False)

@app.route('/')
def home():
    csv_data = session.get('csv_data')
    csv_data_real = session.get('csv_data_real')
    result_html = session.get('result_html')
    csv_link = url_for('download') if session.get('result_base64') else None
    treshold_result = session.get('treshold_result')
    treshold_value = session.get('treshold_value')
    comparison_result = session.get('comparison_result')
    return render_template('index.html', csv_link=csv_link, csv_data=csv_data, csv_data_real=csv_data_real, result_html=result_html, treshold_result=treshold_result, treshold_value=treshold_value, comparison_result=comparison_result)

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return 'No file part'
    
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    
    # Read CSV file from FileStorage object
    df = pd.read_csv(file.stream)
    csv_data = df.to_csv(index=False)

    # Store the CSV data in the session
    session['csv_data'] = csv_data

    return render_template('index.html', csv_data=csv_data)

@app.route('/upload-real-data', methods=['POST'])
def upload_real_data():
    if 'file_real' not in request.files:
        return 'No file part for real data'
    
    file_real = request.files['file_real']
    if file_real.filename == '':
        return 'No selected file for real data'
    
    # Read CSV file from FileStorage object
    df_real = pd.read_csv(file_real.stream)
    csv_data_real = df_real.to_csv(index=False)

    # Store the CSV data in the session
    session['csv_data_real'] = csv_data_real

    return redirect(url_for('home'))


@app.route('/predict', methods=['POST'])
def predict():
    csv_data = session.get('csv_data')
    if not csv_data:
        return 'No CSV data'

    df = pd.read_csv(io.StringIO(csv_data))
    # Assuming the CSV file has columns 'out_cut', 'a', 'b', 'c', 'd'
    X = df[['out_cut', 'a', 'b', 'c', 'd']]
    
    # Memastikan model telah diload dengan benar
    if model is None:
        raise ValueError("Model belum diload dengan benar.")

    # Melakukan prediksi menggunakan model yang telah diload
    predictions = model.predict(X)

    # Membuat DataFrame untuk hasil prediksi
    result_df = pd.DataFrame(predictions, columns=['na', 'nb', 'nc', 'nd', 'flag'])
    result_csv = result_df.to_csv(index=False)

    # Create a bytes buffer for the CSV data
    result_buffer = io.BytesIO()
    result_buffer.write(result_csv.encode())
    result_buffer.seek(0)

    # Convert BytesIO to base64
    result_base64 = base64.b64encode(result_buffer.getvalue()).decode('utf-8')
    session['result_base64'] = result_base64

    result_html = result_df.to_html(classes='table table-striped table-bordered table-hover', index=False)
    result_html = result_html.replace('<th>', '<th style="text-align: center;">')
    session['result_html'] = result_html
    session['result_df'] = result_df.to_dict()

    return render_template('index.html', result_html=result_html, csv_data=csv_data, csv_link=url_for('download'))

@app.route('/calculate', methods=['POST'])
def calculate():
    treshold_str = request.form.get('treshold')
    if treshold_str is None:
        return 'Treshold value is missing', 400
    
    try:
        treshold = float(treshold_str)
    except ValueError:
        return 'Invalid treshold value', 400

    # Save the threshold value in the session
    session['treshold_value'] = treshold_str

    result_df_dict = session.get('result_df')
    if result_df_dict is None:
        return 'No prediction results found', 400

    # Convert the dictionary back to DataFrame
    result_df = pd.DataFrame(result_df_dict)

    # Reorder columns to 'na', 'nb', 'nc', 'nd', 'flag'
    columns_order = ['na', 'nb', 'nc', 'nd', 'flag']
    result_df = result_df[columns_order]

    # Apply the threshold calculation on all columns
    result_treshold = (result_df >= treshold).astype(int)

    # Check the results for debugging purposes
    # print("Result DataFrame:\n", result_df)
    # print("Threshold DataFrame:\n", result_treshold)

    # Convert result to HTML and store in session
    result_treshold_html = result_treshold.to_html(classes='table table-striped table-bordered table-hover', index=False)
    result_treshold_html = result_treshold_html.replace('<th>', '<th style="text-align: center;">')
    session['treshold_result'] = result_treshold_html

    return redirect(url_for('home'))

@app.route('/download')
def download():
    result_base64 = session.get('result_base64')
    if not result_base64:
        return 'No result to download'

    result_buffer = io.BytesIO(base64.b64decode(result_base64))
    result_buffer.seek(0)
    return send_file(result_buffer, as_attachment=True, download_name='predictions.csv')

@app.route('/clear')
def clear():
    # Clear the session data
    session.clear()
    return redirect(url_for('home'))

@app.route('/clear-data-real')
def clear_data_real():
    session.pop('csv_data_real', None)
    return redirect(url_for('home'))

@app.route('/get-hasil', methods=['POST'])
def get_hasil():
    csv_data_real = session.get('csv_data_real')
    treshold_result = session.get('treshold_result')

    if not csv_data_real or not treshold_result:
        return 'Data for comparison not found', 400

    df_real = pd.read_csv(io.StringIO(csv_data_real))
    df_treshold = pd.read_html(treshold_result)[0]

    # Assuming both dataframes have the same structure and column names
    comparison_result = (df_real == df_treshold).astype(str).replace({'True': 'sama', 'False': 'beda'})

    comparison_html = comparison_result.to_html(classes='table table-striped table-bordered table-hover', index=False).replace('<th>', '<th style="text-align: center;">')
    session['comparison_result'] = comparison_html

    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
