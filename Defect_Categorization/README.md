# Defect Categorization Project

This project is an AI-based defect categorization tool designed to help users analyze and categorize defects efficiently. The application provides a user-friendly interface for uploading defect data, processing it using AI algorithms, and displaying the results in a visually appealing format.

## Project Structure

The project consists of the following files and directories:

- **templates/**: Contains HTML templates for rendering the web pages.
  - `results.html`: Displays the processing results, including defect distribution charts and categorized defects in a table.

- **static/**: Contains static assets such as CSS, JavaScript, and images.
  - **css/**: Custom styles for the application.
    - `style.css`: Defines styles for various elements to enhance the visual appearance.
  - **js/**: JavaScript functionality for interactivity.
    - `script.js`: Handles user events and DOM manipulation.
  - **images/**: Contains image assets.
    - `logo.png`: Logo for the web application.

- `app.py`: The main application file that serves as the entry point for the application. It handles routing, rendering templates, and managing application logic.

- `requirements.txt`: Lists the Python dependencies required for the project.

- `.gitignore`: Specifies files and directories to be ignored by Git.

## Setup Instructions

1. **Clone the repository**:
   ```
   git clone https://github.com/Manasvi24092003/Defect_Categorization.git
   cd Defect_Categorization
   ```

2. **Install dependencies**:
   It is recommended to use a virtual environment. You can create one using:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
   Then install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. **Run the application**:
   Start the application by running:
   ```
   python app.py
   ```
   The application will be accessible at `http://127.0.0.1:5000`.

## Usage

- Upload your defect data through the provided interface.
- The application will process the data and categorize defects using AI algorithms.
- View the results, including defect distribution and categorized defects, in the results section.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any suggestions or improvements.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.