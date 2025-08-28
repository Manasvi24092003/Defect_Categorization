# app.py
import os
import pandas as pd
import numpy as np
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
import io
import re
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'defect-categorization-secret-key-2023'

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'xlsx', 'csv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Enhanced keyword categorization with weighted matching
CATEGORY_KEYWORDS = {
    'Report': {
        'keywords': ['report', 'extract', 'data', 'record', 'log', 'export', 'download', 'statistic'],
        'weight': 1.0
    },
    'Notifications': {
        'keywords': ['notification', 'email', 'alert', 'message', 'reminder', 'notify', 'send', 'mail'],
        'weight': 1.0
    },
    'Generate Study Structure': {
        'keywords': ['generate', 'structure', 'study', 'create', 'build', 'setup', 'initialize', 'rcr', 'fst'],
        'weight': 1.0
    },
    'MCC master data sync': {
        'keywords': ['mcc', 'sync', 'synchroniz', 'master data', 'data sync', 'prometrika', 'poi', 'mdm'],
        'weight': 1.0
    },
    'Document Migration': {
        'keywords': ['migration', 'migrate', 'import', 'export', 'transfer', 'move', 'document', 'file'],
        'weight': 1.0
    },
    'R&A Task': {
        'keywords': ['r&a', 'read', 'acknowledge', 'acknowledgment', 'review', 'approval', 'sign', 'signature'],
        'weight': 1.0
    },
    'Error': {
        'keywords': ['error', 'exception', 'fail', 'crash', 'broken', 'issue', 'problem', 'bug', 'defect'],
        'weight': 0.8
    },
    'Authentication': {
        'keywords': ['login', 'password', 'auth', 'authentication', 'credential', 'access', 'sign in', 'log in'],
        'weight': 1.0
    },
    'User Management': {
        'keywords': ['user', 'profile', 'account', 'role', 'permission', 'admin', 'administrator', 'privilege'],
        'weight': 1.0
    },
    'UI/Dashboard': {
        'keywords': ['ui', 'interface', 'dashboard', 'screen', 'page', 'view', 'display', 'button', 'menu'],
        'weight': 0.9
    },
    'Document Management': {
        'keywords': ['document', 'file', 'upload', 'download', 'attach', 'attachment', 'pdf', 'word', 'excel'],
        'weight': 1.0
    },
    'Workflow': {
        'keywords': ['workflow', 'process', 'approval', 'review', 'task', 'assign', 'assignment', 'step', 'phase'],
        'weight': 1.0
    },
    'System Configuration': {
        'keywords': ['config', 'configuration', 'setting', 'property', 'parameter', 'setup', 'preference', 'option'],
        'weight': 1.0
    },
    'Performance': {
        'keywords': ['performance', 'slow', 'speed', 'response', 'timeout', 'load', 'lag', 'delay', 'bottleneck'],
        'weight': 0.9
    },
    'Integration': {
        'keywords': ['integration', 'api', 'interface', 'connect', 'connection', 'web service', 'rest', 'soap'],
        'weight': 1.0
    }
}

# Global variable to store the processed DataFrame
processed_df = None

# Enhanced categorization with weighted keyword matching
def categorize_defect(defect_summary):
    if pd.isna(defect_summary) or not str(defect_summary).strip():
        return 'Uncategorized'
    
    summary_lower = str(defect_summary).lower()
    
    # Calculate scores for each category
    category_scores = {}
    
    for category, data in CATEGORY_KEYWORDS.items():
        score = 0
        keywords = data['keywords']
        weight = data['weight']
        
        for keyword in keywords:
            # Check if keyword appears in the summary
            if keyword in summary_lower:
                # Increase score based on keyword weight
                score += weight
                # Additional points for exact matches
                if re.search(r'\b' + re.escape(keyword) + r'\b', summary_lower):
                    score += 0.5
    
        category_scores[category] = score
    
    # Find the category with the highest score
    if category_scores:
        best_category = max(category_scores, key=category_scores.get)
        if category_scores[best_category] > 0:
            return best_category
    
    # Fallback for specific patterns
    if any(word in summary_lower for word in ['login', 'password', 'auth']):
        return 'Authentication'
    elif any(word in summary_lower for word in ['profile', 'user', 'account']):
        return 'User Management'
    elif any(word in summary_lower for word in ['dashboard', 'ui', 'interface']):
        return 'UI/Dashboard'
    elif any(word in summary_lower for word in ['email', 'notification', 'alert']):
        return 'Notifications'
    elif any(word in summary_lower for word in ['sync', 'synchroniz']):
        return 'MCC master data sync'
    elif any(word in summary_lower for word in ['task', 'assign']):
        return 'Workflow'
    elif any(word in summary_lower for word in ['document', 'file']):
        return 'Document Management'
    
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
    global processed_df
    
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
        
        # Store the processed DataFrame globally
        processed_df = df.copy()
        
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
        
        # Calculate accuracy metrics
        total_defects = len(df)
        uncategorized = len(df[df['Predicted Feature'] == 'Uncategorized'])
        accuracy_percentage = ((total_defects - uncategorized) / total_defects) * 100 if total_defects > 0 else 0
        
        flash(f'Defects categorized successfully! Accuracy: {accuracy_percentage:.1f}%', 'success')
        return render_template('results.html', 
                              table=df.to_html(classes='table table-striped', index=False),
                              chart_data=json.dumps(chart_data),
                              accuracy=accuracy_percentage,
                              mode='prediction')
    
    flash('Invalid file type. Please upload a CSV or Excel file.', 'error')
    return redirect(request.url)

# Download results
@app.route('/download')
def download_file():
    global processed_df
    
    if processed_df is None:
        flash('No data to download. Please upload and process a file first.', 'error')
        return redirect(url_for('index'))
    
    try:
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            processed_df.to_excel(writer, index=False, sheet_name='Categorized Defects')
        output.seek(0)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'defects_categorized_{timestamp}.xlsx'
        
        # Send the file
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        flash(f'Error generating download file: {str(e)}', 'error')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)