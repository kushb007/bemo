# Bemo - Copilot Instructions

## Project Overview
Bemo is a competitive programming platform for rural Indian high schools. Users can solve coding problems, submit solutions for automated judging, and track their progress. The platform uses Auth0 for authentication and Judge0 API for code execution.

## Architecture

### Core Components
- **Flask Application** ([bemo/__init__.py](bemo/__init__.py)): Initializes app with SQLAlchemy, OAuth (Auth0), and Flask-Caching
- **Routes** ([bemo/routes.py](bemo/routes.py)): 373 lines handling authentication, problem display, submission, and user management
- **Models** ([bemo/models.py](bemo/models.py)): Three SQLAlchemy models - `User`, `Problem`, `Submission`
- **Forms** ([bemo/forms.py](bemo/forms.py)): WTForms for user registration (`Confirm`), profile pictures (`Picture`), and code submission (`Code`)

### Database Structure
- **SQLite** (`site.db`) with three tables:
  - `User`: Auth0 integration (`sub` field), scoring (`score`, `contribution`), profile management
  - `Problem`: Stores problem metadata and references to test case files (inputs/outputs stored as JSON arrays of file paths in `problem_data/`)
  - `Submission`: Tracks Judge0 execution tokens, check count with exponential backoff, and per-case results

### External Dependencies
- **Auth0**: OAuth authentication - requires `AUTH0_CLIENT_ID`, `AUTH0_CLIENT_SECRET`, `AUTH0_DOMAIN` in `.env`
- **Judge0 API**: Code execution via RapidAPI - hardcoded API key in [routes.py:31-34](bemo/routes.py#L31-L34)
- **Square**: Payment integration - requires `SQUARE_ACCESS_TOKEN` in `.env`

## Critical Workflows

### Running the Application
```bash
# Activate virtual environment
source env/bin/activate  # or env/Scripts/activate on Windows

# Run development server
python run.py  # Starts on 0.0.0.0:8080
```

### Database Initialization
Database auto-creates on first run via `app.app_context().push()` in [__init__.py](bemo/__init__.py). No migration system - schema changes require manual DB updates.

### Adding Problems
Use Gradio interface in [addProblem.py](addProblem.py):
```bash
python addProblem.py  # Launches Gradio UI
```
- Creates problem entries in DB and saves test case files to `bemo/static/problem_data/{title}/input_{i}.txt` and `output_{i}.txt`
- File paths stored as JSON arrays in `Problem.inputs` and `Problem.outputs`

### Code Submission Flow
1. User submits code via ACE editor or file upload ([problem.html](bemo/templates/problem.html))
2. Code base64-encoded and batch-submitted to Judge0 ([routes.py:207-230](bemo/routes.py#L207-L230))
3. Submission tokens stored in `Submission.tokens` as JSON array
4. Results checked with exponential backoff: `min(60^checks, 10000)` seconds ([routes.py:254](bemo/routes.py#L254))
5. Status displayed with emoji indicators (✅ ❌ 💥 ⚙️) in [submission.html](bemo/templates/submission.html)

## Project-Specific Patterns

### Session Management
- Auth0 callback stores user profile in `session['profile']` and database ID in `session['id']`
- The `@requires_auth` decorator checks for `session['id']` but doesn't redirect on failure (incomplete implementation)

### File Upload Patterns
- Profile pictures: Random hex name, thumbnail to 125x125, saved to `bemo/static/pics/`
- Problem test cases: Saved to `bemo/static/problem_data/{secure_filename(title)}/`
- Always use `secure_filename()` for user-provided filenames

### JSON-in-Database Pattern
All array/list data stored as JSON strings: `Problem.tags`, `Problem.inputs`, `Problem.outputs`, `Submission.tokens`, `Submission.status`. Always use `json.loads()` and `json.dumps()` when reading/writing.

### Language ID Hardcoding
Judge0 submissions hardcoded to C++ (`language_id='52'`) in [routes.py:214](bemo/routes.py#L214). TODO comment indicates this should be dynamic.

## Known Issues & TODOs

- [ ] Language selection hardcoded to C++ (line 214 in routes.py)
- [ ] User-problem solve relationship should be many-to-many, currently single (line 302)
- [ ] Payment/reward system for first solvers incomplete (line 313)
- [ ] No database migration system - CockroachDB planned per README
- [ ] Judge0 API key hardcoded in routes.py - should move to environment variables
- [ ] Exponential backoff can lead to very long wait times (up to 10000 seconds)

## Development Guidelines

### Adding New Routes
- Use `@app.route()` decorator in [routes.py](bemo/routes.py)
- Add `@requires_auth` if authentication needed
- Query user with `User.query.filter_by(id=session['id']).first()` for authenticated routes
- Pass `user` object to templates for consistent UI (navbar, profile)

### Working with Templates
- Base template: [layout.html](bemo/templates/layout.html) - includes Bootstrap 4, ACE editor, highlight.js
- Templates use Jinja2 with `{{ user }}` context for conditional rendering
- ACE editor configured in `#editor` div for code input

### Environment Configuration
Required `.env` file in `bemo/` directory:
```
APP_SECRET_KEY=<flask-secret>
AUTH0_CLIENT_ID=<auth0-client-id>
AUTH0_CLIENT_SECRET=<auth0-client-secret>
AUTH0_DOMAIN=<auth0-domain>
SQUARE_ACCESS_TOKEN=<square-token>
```

### Test Data
- `dm-code_contests/`: DeepMind Code Contests dataset in Riegeli format (128 shards)
- [pw_finetuning.ipynb](pw_finetuning.ipynb): Jupyter notebook for fine-tuning LLaMA 3.1 8B on problem descriptions

## Planned Development: AI-Powered Problem Generation

### Current State
The project includes infrastructure for LLM-based problem generation using open-source models:
- **Dataset**: DeepMind Code Contests (128 training shards) in `dm-code_contests/`
- **Fine-tuning Notebook**: [pw_finetuning.ipynb](pw_finetuning.ipynb) demonstrates QLoRA fine-tuning of LLaMA 3.1 8B
- **System Prompt**: Multi-agent approach where LLM acts as "problem writer" to revise and improve problem descriptions

### Proposed Architecture for Problem Generation

#### Phase 1: Problem Description Generation
**Approach**: Fine-tune LLaMA 3.1 8B on the `description` field of Code Contests dataset
- Use QLoRA (4-bit quantization) for memory efficiency on consumer GPUs
- LoRA config: `r=8`, target all linear layers, `nf4` quantization
- Training: 3 epochs with gradient accumulation (batch size 4)
- **Output**: Natural language problem statements with input/output specifications

**Prompt Template**:
```
System: You are a creative problem writer for high school competitive programming...
User: Create a problem involving [arrays/graphs/dynamic programming] suitable for difficulty [800-1500]
Assistant: [Generated problem description]
```

#### Phase 2: Test Case Generation
**Challenge**: Generate both inputs and expected outputs that validate solutions

**Option A - Rule-Based Generators**:
- Parse problem constraints from LLM-generated description (input ranges, bounds)
- Generate random inputs using constraint-aware algorithms
- Execute a reference solution (human-written or LLM-generated) to create outputs
- **Pros**: Guaranteed correctness, fast generation
- **Cons**: Requires reference solution, limited creativity

**Option B - LLM-Generated Test Cases**:
- Fine-tune separate model on input/output pairs from Code Contests
- Use few-shot prompting with examples from similar problem types
- Validate generated test cases by:
  1. Checking format compliance (parseable, within constraints)
  2. Running through multiple LLM-generated solutions for consistency
  3. Manual review for edge cases
- **Pros**: More diverse test cases, can generate tricky edge cases
- **Cons**: Correctness not guaranteed, requires validation

**Option C - Hybrid Approach** (Recommended):
```python
def generate_problem_with_tests(difficulty, topic):
    # 1. Generate problem description
    description = llm_generate_problem(difficulty, topic)
    
    # 2. Generate reference solution
    solution = llm_generate_solution(description, language='cpp')
    
    # 3. Generate test inputs (LLM creates creative edge cases)
    test_inputs = llm_generate_inputs(description, count=10)
    
    # 4. Validate solution compiles and runs
    if not compile_and_validate(solution, test_inputs[0]):
        return retry_or_fallback()
    
    # 5. Generate outputs by running reference solution
    test_outputs = [execute_solution(solution, inp) for inp in test_inputs]
    
    # 6. Verify with secondary LLM-generated solution
    alt_solution = llm_generate_solution(description, language='python')
    verify_consistency(alt_solution, test_inputs, test_outputs)
    
    return Problem(description, test_inputs, test_outputs)
```

#### Phase 3: Quality Assurance Pipeline
1. **Automated Checks**:
   - Constraint validation (input sizes within bounds)
   - Time limit verification (reference solution runs in <1s)
   - Test case diversity (different edge cases covered)
   - Difficulty estimation (based on algorithmic complexity)

2. **Human Review Queue**:
   - Flag problems with inconsistent outputs
   - Review for clarity and mathematical correctness
   - Validate problem statements are understandable for target audience

3. **Community Testing**:
   - Beta-test generated problems with small user group
   - Track solve rates and submission patterns
   - Iterate on problems that are too easy/hard/unclear

#### Implementation Considerations

**Model Selection**:
- **LLaMA 3.1 8B**: Good balance for problem descriptions (current choice)
- **DeepSeek Coder**: Better for solution generation and code understanding
- **Mixtral 8x7B**: Higher quality but requires more VRAM (consider for hosted deployment)

**Data Augmentation**:
- Synthetic problem variations: "Convert this array problem to use strings instead"
- Difficulty adjustments: "Make this problem easier by removing constraint X"
- Topic mixing: Combine multiple algorithmic concepts

**Integration with `addProblem.py`**:
```python
# New function to add alongside manual problem entry
def generate_and_add_problem(difficulty, topic):
    with app.app_context():
        # Generate using LLM pipeline
        problem_data = llm_problem_pipeline.generate(difficulty, topic)
        
        # Create database entry
        new_problem = Problem(
            title=problem_data['title'],
            statement=problem_data['description'],
            tags=json.dumps(problem_data['tags']),
            rating=difficulty,
            cases=len(problem_data['inputs']),
            inputs=problem_data['input_paths'],
            outputs=problem_data['output_paths']
        )
        db.session.add(new_problem)
        db.session.commit()
```

**Deployment Strategy**:
- Run generation offline as batch job (not real-time)
- Store generated problems in queue for human review
- Gradually introduce AI problems mixed with manual ones
- Track metrics: solve rate, rating accuracy, user engagement

### Next Steps
1. Complete fine-tuning experiments in [pw_finetuning.ipynb](pw_finetuning.ipynb)
2. Build test case generation module with validation
3. Create Gradio interface for problem review and approval
4. Integrate with existing [addProblem.py](addProblem.py) workflow
5. A/B test AI vs manual problems to measure quality

## Common Pitfalls
1. **Path Issues**: Upload folder is `os.getcwd()+'/bemo/static/'` - relative to project root
2. **Auth Flow**: `new_login` route creates user accounts - requires both form submission and picture upload
3. **Submission Polling**: Avoid rapid refreshes - backoff timing prevents overloading Judge0
4. **Database Access**: Always work within `app.app_context()` when running standalone scripts (see addProblem.py)
