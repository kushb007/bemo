import gradio as gr
import os
import json
from werkzeug.utils import secure_filename
from bemo import app, db
from bemo.models import Problem

# Ensure the problem data directory exists
# app.config['UPLOAD_FOLDER'] is set in bemo/__init__.py to os.getcwd()+'/bemo/static/'
PROBLEM_DATA_FOLDER = os.path.join(app.config['UPLOAD_FOLDER'], 'problem_data')
os.makedirs(PROBLEM_DATA_FOLDER, exist_ok=True)

def save_input_output_pairs(input_texts, output_texts, title):
    """Save input-output pairs as separate files and return JSON lists of file paths."""
    input_paths = []
    output_paths = []
    
    safe_title = secure_filename(title)
    problem_dir = os.path.join(PROBLEM_DATA_FOLDER, safe_title)
    print(f"Saving problem data to: {problem_dir}")
    os.makedirs(problem_dir, exist_ok=True)
    
    for i, (input_text, output_text) in enumerate(zip(input_texts, output_texts)):
        input_filename = f"input_{i}.txt"
        output_filename = f"output_{i}.txt"
        
        input_full_path = os.path.join(problem_dir, input_filename)
        output_full_path = os.path.join(problem_dir, output_filename)
        
        with open(input_full_path, "w") as f:
            f.write(input_text)
        with open(output_full_path, "w") as f:
            f.write(output_text)
            
        # Store path relative to problem_data folder, as expected by routes.py
        # routes.py does: open(app.config['UPLOAD_FOLDER']+'/problem_data/'+input_file,'r')
        input_paths.append(f"{safe_title}/{input_filename}")
        output_paths.append(f"{safe_title}/{output_filename}")

    return json.dumps(input_paths), json.dumps(output_paths)

def add_problem(title, statement, tags, rating, test_cases):
    # Use the app context to access the database
    with app.app_context():
        if Problem.query.filter_by(title=title).first():
            return f"Error: Problem '{title}' already exists."

        # Gradio dataframe returns a list of lists [[input, output], ...]
        # Filter out empty rows if any
        valid_cases = [case for case in test_cases if case[0] or case[1]]
        
        if not valid_cases:
             return "Error: At least one test case is required."

        inputs = [case[0] for case in valid_cases]
        outputs = [case[1] for case in valid_cases]

        # Save files
        input_paths, output_paths = save_input_output_pairs(inputs, outputs, title)

        # Process tags
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]

        new_problem = Problem(
            title=title,
            statement=statement,
            tags=json.dumps(tag_list),
            rating=int(rating),
            cases=len(inputs),
            inputs=input_paths,
            outputs=output_paths,
            solved=0
        )

        db.session.add(new_problem)
        db.session.commit()
        return f"Problem '{title}' added successfully with {len(inputs)} test cases!"

def add_test_case(test_cases):
    test_cases.append(["", ""])
    return test_cases

# Initial test cases
initial_test_cases = [["", ""]]

with gr.Blocks() as interface:
    gr.Markdown("# Add a New Problem")
    gr.Markdown("Fill out the form below to add a new problem.")
    
    with gr.Row():
        title = gr.Textbox(label="Title", placeholder="Enter problem title")
        rating = gr.Number(label="Rating", value=1500)
    
    statement = gr.Textbox(label="Statement", placeholder="Enter problem statement", lines=5)
    tags = gr.Textbox(label="Tags (comma-separated)", placeholder="e.g. arrays, dynamic programming")

    gr.Markdown("### Test Cases")
    test_case_display = gr.Dataframe(
        headers=["Input", "Output"], 
        datatype=["str", "str"], 
        value=initial_test_cases,
        interactive=True, 
        label="Test Cases", 
        type="array", 
        col_count=2
    )
    
    add_case_button = gr.Button("Add Another Test Case")
    add_case_button.click(add_test_case, inputs=[test_case_display], outputs=[test_case_display])

    submit_button = gr.Button("Submit Problem", variant="primary")
    output_text = gr.Textbox(label="Result", interactive=False)

    submit_button.click(
        add_problem,
        inputs=[title, statement, tags, rating, test_case_display],
        outputs=output_text
    )

if __name__ == "__main__":
    interface.launch()
