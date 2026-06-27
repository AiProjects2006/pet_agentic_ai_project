import json
import re
from typing import Any

import gradio as gr
import ollama

DEFAULT_MODEL = "llama3.1"
MAX_QUESTIONS = 10


def _extract_json(text: str) -> Any:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}|\[.*\]", text, re.DOTALL)
    if match:
        candidate = match.group(0)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    raise ValueError("Model did not return valid JSON.")


def _build_prompt(content: str, num_questions: int, difficulty: str) -> str:
    return f"""You are a quiz generator.
Create exactly {num_questions} quiz questions from the content below.
Difficulty: {difficulty}.
Return ONLY valid JSON, no markdown, no code fences, no extra text.

Use this JSON shape:
{{
  "quiz_title": "Short title",
  "questions": [
    {{
      "question": "Question text",
      "options": ["A", "B", "C", "D"],
      "answer": "Correct option text",
      "explanation": "Short explanation"
    }}
  ]
}}

Rules:
- Make the questions based only on the provided content.
- For each question, include 4 options.
- Keep answers unambiguous.
- If the content is short, ask simpler factual questions.

Content:
{content}
"""


def generate_quiz(content: str, num_questions: int, difficulty: str, model: str):
    if not content or not content.strip():
        hidden_questions = [gr.update(visible=False, value=None, choices=[]) for _ in range(MAX_QUESTIONS)]
        return ({"quiz_title": "", "questions": []}, "Please paste some content first.", *hidden_questions, "")

    prompt = _build_prompt(content.strip(), num_questions, difficulty)

    try:
        response = ollama.chat(
            model=model,
            messages=[
                {"role": "system", "content": "You generate quizzes in valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            format="json",
        )
        raw_text = response["message"]["content"]
        data = _extract_json(raw_text)
    except Exception as exc:
        hidden_questions = [gr.update(visible=False, value=None, choices=[]) for _ in range(MAX_QUESTIONS)]
        return (
            {"quiz_title": "", "questions": []},
            "## Error\n"
            f"Could not generate quiz.\n\n"
            f"**Details:** {exc}\n\n"
            "Make sure Ollama is running and the selected model is installed.",
            *hidden_questions,
            "",
        )

    quiz_title = data.get("quiz_title", "Generated Quiz") if isinstance(data, dict) else "Generated Quiz"
    questions = data.get("questions", []) if isinstance(data, dict) else []

    if not questions:
        hidden_questions = [gr.update(visible=False, value=None, choices=[]) for _ in range(MAX_QUESTIONS)]
        return (
            {"quiz_title": "", "questions": []},
            "## No quiz questions were returned. Try different content or a different model.",
            *hidden_questions,
            "",
        )

    questions = questions[:MAX_QUESTIONS]

    quiz_state = {"quiz_title": quiz_title, "questions": questions}
    title_md = f"# {quiz_title}"
    instruction_md = "Select one answer for each question, then click **Submit Answers** to reveal your score, correct answers, and explanations."

    question_updates = []
    for index in range(MAX_QUESTIONS):
        if index < len(questions):
            item = questions[index]
            question = item.get("question", f"Question {index + 1}")
            options = item.get("options", [])
            question_updates.append(
                gr.update(
                    label=f"{index + 1}. {question}",
                    choices=options,
                    value=None,
                    visible=True,
                )
            )
        else:
            question_updates.append(gr.update(visible=False, value=None, choices=[]))

    return (quiz_state, title_md, *question_updates, instruction_md)


def grade_quiz(quiz_state: dict, *answers: str) -> str:
    questions = (quiz_state or {}).get("questions", [])
    if not questions:
        return "Generate a quiz first."

    total = len(questions)
    correct = 0
    output = [f"# Score: 0/{total}", ""]

    for index, item in enumerate(questions, start=1):
        selected_answer = answers[index - 1] if index - 1 < len(answers) else None
        question = item.get("question", "")
        answer = item.get("answer", "")
        explanation = item.get("explanation", "")

        is_correct = selected_answer == answer
        if is_correct:
            correct += 1

        output.append(f"## {index}. {question}")
        output.append(f"**Your answer:** {selected_answer or 'No answer selected'}")
        output.append(f"**Correct answer:** {answer}")
        output.append(f"**Result:** {'Correct' if is_correct else 'Incorrect'}")
        if explanation:
            output.append(f"**Explanation:** {explanation}")
        output.append("")

    output[0] = f"# Score: {correct}/{total}"
    return "\n".join(output)


with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# Quiz Generator")
    gr.Markdown("Paste any lesson, article, notes, or paragraph and generate multiple-choice quizzes from it.")

    with gr.Row():
        content_input = gr.Textbox(
            label="Content",
            placeholder="Paste the text you want to turn into quizzes...",
            lines=14,
        )

    with gr.Row():
        questions_input = gr.Slider(
            minimum=1,
            maximum=20,
            value=5,
            step=1,
            label="Number of Questions",
        )
        difficulty_input = gr.Dropdown(
            choices=["easy", "medium", "hard"],
            value="medium",
            label="Difficulty",
        )
        model_input = gr.Textbox(
            label="Ollama Model",
            value=DEFAULT_MODEL,
            placeholder="Example: llama3.1 or llama3.1:8b",
        )

    generate_button = gr.Button("Generate Quiz", variant="primary")
    quiz_state = gr.State({"quiz_title": "", "questions": []})
    quiz_title_markdown = gr.Markdown()
    quiz_instructions = gr.Markdown()

    answer_components = []
    for index in range(MAX_QUESTIONS):
        answer_components.append(
            gr.Radio(
                label=f"Question {index + 1}",
                choices=[],
                visible=False,
                interactive=True,
            )
        )

    submit_button = gr.Button("Submit Answers")
    results_markdown = gr.Markdown()

    generate_button.click(
        fn=generate_quiz,
        inputs=[content_input, questions_input, difficulty_input, model_input],
        outputs=[quiz_state, quiz_title_markdown, *answer_components, quiz_instructions],
    )

    submit_button.click(
        fn=grade_quiz,
        inputs=[quiz_state, *answer_components],
        outputs=results_markdown,
    )

if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft())
