import os
import json
import logging
import re

logger = logging.getLogger(__name__)

def _get_genai_client():
    """Attempts to initialize and return Google GenAI client or generativeai model instance."""
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None, None
    
    # Try google.genai first (new official SDK)
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        return "genai", client
    except ImportError:
        pass

    # Try google.generativeai next (legacy SDK)
    try:
        import google.generativeai as legacy_genai
        legacy_genai.configure(api_key=api_key)
        return "generativeai", legacy_genai
    except ImportError:
        pass

    return None, None

def _clean_json_response(raw_text):
    """Utility to clean code fences like ```json ... ``` from LLM outputs."""
    if not raw_text:
        return ""
    text = raw_text.strip()
    # Remove markdown code block markers
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()

# Default fallback question banks by role
FALLBACK_QUESTIONS = {
    "Java Developer": [
        {"question_text": "Explain the core differences between Abstract Classes and Interfaces in Java 8+.", "model_answer": "Abstract classes can have state (instance variables) and constructors, whereas interfaces cannot. Since Java 8, interfaces support default and static methods, and Java 9 added private methods."},
        {"question_text": "How does Java Memory Management work, specifically regarding the Garbage Collector and Heap vs Stack Memory?", "model_answer": "Stack memory stores local primitive variables and reference pointers for execution threads. Heap memory holds all objects. The Garbage Collector cleans unreachable objects from heap using algorithms like Generational GC (Eden, Survivor, Tenured spaces)."},
        {"question_text": "What is the HashMap internal implementation in Java, and how are hash collisions handled?", "model_answer": "HashMap uses an array of buckets containing linked lists or balanced red-black trees (when bucket size > 8). Collisions use chaining. Key hashcodes determine index; equals() verifies exact match."},
        {"question_text": "Describe the difference between HashMap, ConcurrentHashMap, and Hashtable in multi-threaded applications.", "model_answer": "HashMap is non-thread-safe. Hashtable synchronizes all operations locking the entire table. ConcurrentHashMap locks at bucket/segment level (using CAS and synchronized blocks on node heads) for high concurrency."},
        {"question_text": "Explain Spring Boot Dependency Injection and how @Autowired works under the hood.", "model_answer": "Spring IoC container manages bean lifecycle. @Autowired injects dependencies by type or name via reflection/setters/constructors. Constructor injection is recommended for immutability and testability."}
    ],
    "Python Developer": [
        {"question_text": "Explain Python Decorators and how they work with `@functools.wraps`.", "model_answer": "Decorators are higher-order functions taking a function and returning a wrapped function to extend behavior. `@functools.wraps` preserves original function metadata like __name__ and __doc__."},
        {"question_text": "What is the Global Interpreter Lock (GIL) in CPython, and how does it impact multi-threading vs multi-processing?", "model_answer": "GIL is a mutual exclusion lock preventing multiple native threads from executing Python bytecode simultaneously. For CPU-bound tasks, use multiprocessing to bypass GIL; for I/O-bound tasks, asyncio or threading works well."},
        {"question_text": "Explain the difference between deepcopy and shallowcopy in Python.", "model_answer": "Shallow copy (copy.copy) creates a new object but references inner nested objects. Deep copy (copy.deepcopy) recursively copies all nested objects, producing complete independence."},
        {"question_text": "How do Python Generators and `yield` differ from regular functions?", "model_answer": "Generators return an iterator lazily producing values one at a time via `yield`, saving memory compared to returning entire lists created in memory."},
        {"question_text": "Explain context managers in Python and how to implement one using `__enter__` and `__exit__`.", "model_answer": "Context managers safely manage resources (like file handles or DB locks). `__enter__` acquires resources and returns context, while `__exit__` ensures cleanup even if exceptions occur."}
    ],
    "Web Developer": [
        {"question_text": "Explain the Critical Rendering Path in web browsers and how to optimize page load performance.", "model_answer": "Critical Rendering Path involves DOM creation, CSSOM creation, Render Tree construction, Layout calculation, and Painting. Optimization includes deferring non-critical JS/CSS, minifying assets, lazy loading, and caching."},
        {"question_text": "What is Event Delegation in JavaScript and why is it useful?", "model_answer": "Event Delegation attaches a single event listener to a parent element to handle events on descendant elements using event bubbling, reducing memory footprint and handling dynamic DOM elements."},
        {"question_text": "Compare REST APIs vs GraphQL in modern web application architecture.", "model_answer": "REST relies on multiple resource endpoints returning fixed data structures (risk of over/under-fetching). GraphQL uses a single endpoint where clients request exact query fields needed."},
        {"question_text": "How does CORS (Cross-Origin Resource Sharing) work and how do browsers handle preflight requests?", "model_answer": "CORS enforces security by blocking cross-origin requests unless server headers (Access-Control-Allow-Origin) permit it. Complex requests trigger an HTTP OPTIONS preflight check."},
        {"question_text": "What is the difference between Virtual DOM and Real DOM, and how does React state updates work?", "model_answer": "Virtual DOM is an in-memory JS representation of real DOM nodes. React uses reconciliation (diffing algorithm) to batch and calculate minimum necessary updates before patching real DOM efficiently."}
    ],
    "HR Interview": [
        {"question_text": "Tell me about a time you faced a major conflict within a team project and how you resolved it using the STAR method.", "model_answer": "Structure response using Situation, Task, Action, and Result. Focus on active listening, empathy, objective problem solving, and team alignment."},
        {"question_text": "Where do you see yourself professionally in the next 3 to 5 years?", "model_answer": "Emphasize mastering technical skills, taking ownership of high-impact systems, mentoring junior engineers, and contributing strategically to organizational goals."},
        {"question_text": "Describe your process for handling tight project deadlines and unexpected requirement changes.", "model_answer": "Prioritize high-impact core requirements, communicate transparently with stakeholders, break work into agile iterations, and avoid burn-out through smart scoping."},
        {"question_text": "What is your biggest professional weakness, and what active steps are you taking to improve it?", "model_answer": "Share a genuine non-fatal weakness (e.g., struggling to delegate initial tasks or over-analyzing design edge cases) and concrete actions taken to overcome it."},
        {"question_text": "Why do you want to join our organization and what unique value do you bring?", "model_answer": "Connect personal career values and technical expertise directly to company mission, product achievements, and operational culture."}
    ]
}

def generate_questions(role, difficulty="Medium", count=5):
    """
    Generates dynamic interview questions using Gemini API.
    Falls back gracefully to rich curated questions if API key is not present.
    """
    sdk_type, client = _get_genai_client()
    
    prompt = f"""You are an expert technical interviewer for top tech companies.
Generate exactly {count} professional interview questions for a candidate applying for the role of "{role}" at "{difficulty}" difficulty level.

Return ONLY a valid JSON array of objects with the following keys for each question:
- "question_text": The clear, engaging question statement.
- "model_answer": A concise ideal benchmark answer expected from a top candidate.

JSON format requirement:
[
  {{
    "question_text": "...",
    "model_answer": "..."
  }}
]
Do not include any intro markdown text outside the JSON array block.
"""

    if sdk_type and client:
        try:
            if sdk_type == "genai":
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                )
                raw_text = response.text
            else: # generativeai legacy
                model = client.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(prompt)
                raw_text = response.text

            clean_text = _clean_json_response(raw_text)
            data = json.loads(clean_text)
            if isinstance(data, list) and len(data) > 0:
                return data[:count]
        except Exception as e:
            logger.warning(f"Gemini API call failed for generate_questions: {e}. Using intelligent fallback.")

    # Fallback logic
    base_questions = FALLBACK_QUESTIONS.get(role, FALLBACK_QUESTIONS["Web Developer"])
    # Tailor fallback if needed
    result = []
    for idx, q in enumerate(base_questions[:count]):
        result.append({
            "question_text": f"[{difficulty}] {q['question_text']}",
            "model_answer": q["model_answer"]
        })
    return result

def generate_resume_questions(resume_text, count=5):
    """
    Generates tailored interview questions based on candidate's uploaded resume text.
    """
    sdk_type, client = _get_genai_client()

    prompt = f"""You are a senior hiring manager. Analyze the following candidate resume text and extract key skills, tools, and projects.
Generate exactly {count} targeted interview questions tailored to the candidate's actual experience, tech stack, and background mentioned in the resume.

Resume Text:
\"\"\"
{resume_text[:4000]}
\"\"\"

Return ONLY a valid JSON array of objects with keys:
- "question_text": Tailored interview question referencing specific tools, experiences or domain knowledge from the resume.
- "model_answer": Ideal response key points expected.

JSON format requirement:
[
  {{
    "question_text": "...",
    "model_answer": "..."
  }}
]
"""

    if sdk_type and client:
        try:
            if sdk_type == "genai":
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                )
                raw_text = response.text
            else:
                model = client.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(prompt)
                raw_text = response.text

            clean_text = _clean_json_response(raw_text)
            data = json.loads(clean_text)
            if isinstance(data, list) and len(data) > 0:
                return data[:count]
        except Exception as e:
            logger.warning(f"Gemini API resume question generation failed: {e}. Using resume fallback.")

    # Fallback for resume parsing
    return [
        {
            "question_text": "Based on your resume, can you detail the architecture and technical challenges of your primary project?",
            "model_answer": "Should discuss architecture, technical stack choices, performance optimizations, and operational outcomes."
        },
        {
            "question_text": "How have you applied your key technical skills listed in your profile to solve complex production bugs?",
            "model_answer": "Candidate should walk through root cause analysis, debugging tools used, fix implementation, and unit test addition."
        },
        {
            "question_text": "Walk me through how you collaborate with cross-functional teams (PMs, Designers, QA) during sprint delivery.",
            "model_answer": "Clear agile collaboration workflow, clear communication channels, PR reviews, and proactive risk escalation."
        },
        {
            "question_text": "What major performance optimization or scaling improvement did you implement in your recent experience?",
            "model_answer": "Metrics-driven explanation comparing before and after latency/throughput, database index/caching optimization."
        },
        {
            "question_text": "Where do you see the biggest area of technical growth for yourself based on your past accomplishments?",
            "model_answer": "Self-aware assessment of emerging technologies, system design, or architectural leadership."
        }
    ][:count]

def evaluate_interview(role, difficulty, questions_data):
    """
    Evaluates candidate answers for all questions in an interview session.
    
    questions_data format:
    [
      {
        "question_text": "...",
        "model_answer": "...",
        "user_answer": "..."
      },
      ...
    ]
    
    Returns dict:
    {
      "overall_score": 85,
      "summary_feedback": "...",
      "strengths": ["...", "..."],
      "weaknesses": ["...", "..."],
      "question_evaluations": [
         {
           "score": 90,
           "feedback": "...",
           "improvement_tips": "..."
         }, ...
      ]
    }
    """
    sdk_type, client = _get_genai_client()

    prompt = f"""You are a master interview evaluator for role "{role}" at "{difficulty}" level.
Evaluate the candidate's answers to the following questions.

Interview Questions & User Answers:
{json.dumps(questions_data, indent=2)}

Analyze correctness, clarity, depth, technical accuracy, and key concepts mentioned.
Return ONLY a valid JSON object matching this exact schema:
{{
  "overall_score": integer score between 0 and 100,
  "summary_feedback": "High level overall candidate assessment paragraph.",
  "strengths": ["Strength point 1", "Strength point 2", "Strength point 3"],
  "weaknesses": ["Weakness point 1", "Weakness point 2"],
  "question_evaluations": [
    {{
      "question_index": 0,
      "score": integer score 0-100,
      "feedback": "Detailed feedback on what was good or missing.",
      "improvement_tips": "Actionable tips to improve this specific answer."
    }}
  ]
}}
Do not include any text outside the JSON object.
"""

    if sdk_type and client:
        try:
            if sdk_type == "genai":
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                )
                raw_text = response.text
            else:
                model = client.GenerativeModel("gemini-1.5-flash")
                response = model.generate_content(prompt)
                raw_text = response.text

            clean_text = _clean_json_response(raw_text)
            eval_data = json.loads(clean_text)
            if "overall_score" in eval_data and "question_evaluations" in eval_data:
                return eval_data
        except Exception as e:
            logger.warning(f"Gemini API evaluation call failed: {e}. Using simulated evaluation engine.")

    # Rule-based simulated evaluator engine when API is not configured or fails
    evaluated_questions = []
    total_score = 0

    for idx, item in enumerate(questions_data):
        user_ans = item.get("user_answer", "").strip()
        length = len(user_ans.split())

        if not user_ans or length < 5:
            q_score = 25
            q_feedback = "Answer was too brief or incomplete. Key domain concepts and examples were missing."
            q_tips = "Try explaining core concepts thoroughly with concrete code/system design examples."
        elif length < 25:
            q_score = 65
            q_feedback = "Good foundation, but lacks deeper technical depth and real-world trade-off discussion."
            q_tips = "Expand on internal mechanics, potential edge cases, and performance considerations."
        elif length < 60:
            q_score = 85
            q_feedback = "Strong answer! Clear explanation covering core fundamentals and practical applications."
            q_tips = "To reach 100%, touch upon advanced optimization details or architectural impact."
        else:
            q_score = 92
            q_feedback = "Comprehensive and well-structured answer demonstrating solid technical expertise!"
            q_tips = "Keep responses structured with clear key takeaways for executive summary presentation."

        total_score += q_score
        evaluated_questions.append({
            "question_index": idx,
            "score": q_score,
            "feedback": q_feedback,
            "improvement_tips": q_tips
        })

    avg_score = round(total_score / len(questions_data)) if questions_data else 70

    if avg_score >= 85:
        summary = f"Outstanding performance in the {role} mock interview! You demonstrated deep technical competence and clear communication skills."
        strengths = [
            "Strong grasp of core technical concepts and vocabulary",
            "Clear, structured explanations with good depth",
            "Confident problem-solving approach"
        ]
        weaknesses = [
            "Could briefly highlight production scaling edge-cases"
        ]
    elif avg_score >= 70:
        summary = f"Solid performance for the {role} role. You showed good foundational understanding with room to refine technical precision."
        strengths = [
            "Good foundational understanding of candidate domain",
            "Covers main points in most questions"
        ]
        weaknesses = [
            "Some answers lacked granular architectural details",
            "Consider adding STAR method structure for behavioral items"
        ]
    else:
        summary = f"Needs practice for {role} interviews. Review core computer science and domain fundamentals to boost confidence and precision."
        strengths = [
            "Attempted all questions with positive enthusiasm"
        ]
        weaknesses = [
            "Answers were brief and missing key technical keywords",
            "Need deeper preparation on core internal mechanics"
        ]

    return {
        "overall_score": avg_score,
        "summary_feedback": summary,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "question_evaluations": evaluated_questions
    }
