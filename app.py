# app.py (simplified version without scikit-learn)
import os
import pandas as pd
import numpy as np
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
import io
import re
from collections import Counter
import json

app = Flask(__name__)
app.secret_key = 'defect-categorization-secret-key-2023'

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx', 'csv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Predefined categories for fallback (extracted from your data)
PREDEFINED_CATEGORIES = {
    'report': 'Report',
    'notification': 'Notifications',
    'generate': 'Generate Study Structure',
    'mcc': 'MCC master data sync',
    'migration': 'Document Migration',
    'r&a': 'R&A Task',
    'error': 'Error',
    'activity': 'Document->Activity list',
    'my sites': 'My Sites Overview page',
    'approval': 'Approval task',
    'access': 'access RCM instance',
    'property': 'Property',
    'reference': 'References',
    'print': 'Print Button',
    'file': 'File Document',
    'view': 'View',
    'review': 'Review Task',
    'workflow': 'Workflow',
    'bookmark': 'Bookmark',
    'user': 'Users Access',
    'upgrade': 'Upgrade eTMF Structures',
    'study overview': 'eTMF>Study Overview'
}

# Simple keyword-based categorization
def categorize_defect(defect_summary):
    if pd.isna(defect_summary):
        return 'Uncategorized'
        
    summary_lower = str(defect_summary).lower()
    
    # Check for specific keywords and patterns
    for keyword, category in PREDEFINED_CATEGORIES.items():
        if keyword in summary_lower:
            return category
    
    # Additional pattern matching
    if any(word in summary_lower for word in ['login', 'password', 'authentication']):
        return 'Authentication'
    elif any(word in summary_lower for word in ['profile', 'user management']):
        return 'User Management'
    elif 'ra task' in summary_lower or 'read & acknowledge' in summary_lower:
        return 'R&A Task'
    elif any(word in summary_lower for word in ['dashboard', 'ui', 'interface']):
        return 'UI/Dashboard'
    elif any(word in summary_lower for word in ['email', 'notification']):
        return 'Notifications'
    elif any(word in summary_lower for word in ['sync', 'synchroniz']):
        return 'Synchronization'
    elif any(word in summary_lower for word in ['pdf', 'view', 'display']):
        return 'View'
    elif any(word in summary_lower for word in ['task', 'assign']):
        return 'Task Management'
    
    return 'Uncategorized'

# Check if file extension is allowed
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Preprocess text
def preprocess_text(text):
    if pd.isna(text):
        return ""
    # Convert to lowercase and remove special characters
    text = str(text).lower()
    text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
    return text

# Home page
@app.route('/')
def index():
    return render_template('index.html')

# Upload and process file
@app.route('/upload', methods=['POST'])
def upload_file():
    # Check if a file was uploaded
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(request.url)
    
    file = request.files['file']
    
    # Check if filename is empty
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(request.url)
    
    # Check if file is allowed
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Read the file
        try:
            if filename.endswith('.xlsx'):
                df = pd.read_excel(filepath)
            else:
                df = pd.read_csv(filepath)
        except Exception as e:
            flash(f'Error reading file: {str(e)}', 'error')
            return redirect(request.url)
        
        # Check if required column exists
        if 'Defect Summary' not in df.columns:
            flash('File must contain a "Defect Summary" column', 'error')
            return redirect(request.url)
        
        # Categorize defects
        df['Predicted Feature'] = df['Defect Summary'].apply(categorize_defect)
        
        # Create visualization data
        category_counts = df['Predicted Feature'].value_counts().reset_index()
        category_counts.columns = ['Category', 'Count']
        
        # Convert to JSON for Chart.js
        chart_data = {
            'labels': category_counts['Category'].tolist(),
            'data': category_counts['Count'].tolist(),
            'colors': ['#6a11cb', '#2575fc', '#28a745', '#dc3545', '#ffc107', 
                      '#17a2b8', '#6610f2', '#fd7e14', '#20c997', '#e83e8c']
        }
        
        # Prepare download data
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        output.seek(0)
        download_data = output.getvalue()
        
        flash('Defects categorized successfully using keyword matching', 'success')
        return render_template('results.html', 
                              table=df.to_html(classes='table table-striped', index=False),
                              chart_data=json.dumps(chart_data),
                              download_data=download_data,
                              mode='prediction')
    
    flash('Invalid file type. Please upload a CSV or Excel file.', 'error')
    return redirect(request.url)

# Download results
@app.route('/download')
def download_file():
    download_data = request.args.get('data')
    if download_data:
        return send_file(
            io.BytesIO(eval(download_data)),
            download_name='defects_with_predictions.xlsx',
            as_attachment=True,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    flash('No data to download', 'error')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)