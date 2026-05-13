import streamlit as st
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Replace OpenAI with Hugging Face InferenceClient
from huggingface_hub import InferenceClient

# Initialize HF client with your token
# Get free token from https://huggingface.co/settings/tokens
HF_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")
client = InferenceClient(token=HF_API_TOKEN)

# Recommended free models for MCQ generation:
# - "microsoft/phi-2" (2.7B params, runs well on CPU)
# - "google/flan-t5-large" (780M params, good for structured output)
# - "mistralai/Mistral-7B-Instruct-v0.2" (7B, might be slower on CPU)
MODEL_NAME = "microsoft/phi-2"  # Best balance for your hardware


@st.cache_data
def fetch_questions(text_content, quiz_level, num_questions=25):
    """
    Generate MCQs using Hugging Face's free inference API
    """

    # Updated JSON structure for 25 questions
    RESPONSE_JSON = {
        "mcqs": []
    }

    # Add 25 question placeholders
    for i in range(num_questions):
        RESPONSE_JSON["mcqs"].append({
            "mcq": f"multiple choice question{i + 1}",
            "options": {
                "a": "choice here1",
                "b": "choice here2",
                "c": "choice here3",
                "d": "choice here4",
            },
            "correct": "correct choice option in the form of a, b, c or d",
        })

    PROMPT_TEMPLATE = f"""
    Text: {{text_content}}
    You are an expert in generating MCQ type quizzes. 
    Given the above text, create a quiz of EXACTLY {num_questions} multiple choice questions keeping difficulty level as {{quiz_level}}.
    Make sure the questions are not repeated and all questions must be based solely on the provided text.

    Format your response as a JSON object with this exact structure:
    {json.dumps(RESPONSE_JSON, indent=2)}

    Important: 
    - Return ONLY valid JSON, no other text
    - Generate exactly {num_questions} MCQs
    - Each MCQ must have 4 options (a, b, c, d)
    - Each must have a correct answer (a, b, c, or d)
    """

    formatted_template = PROMPT_TEMPLATE.format(
        text_content=text_content,
        quiz_level=quiz_level
    )

    try:
        # Make API request using Hugging Face
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": "You are a quiz generator. Always respond with valid JSON only."
                },
                {
                    "role": "user",
                    "content": formatted_template
                }
            ],
            temperature=0.3,
            max_tokens=4000,  # Increased for 25 questions
            top_p=0.95
        )

        # Extract and parse JSON response
        extracted_response = response.choices[0].message.content

        # Clean the response (remove any markdown formatting if present)
        extracted_response = extracted_response.strip()
        if extracted_response.startswith('```json'):
            extracted_response = extracted_response[7:]
        if extracted_response.startswith('```'):
            extracted_response = extracted_response[3:]
        if extracted_response.endswith('```'):
            extracted_response = extracted_response[:-3]

        result = json.loads(extracted_response)
        return result.get("mcqs", [])

    except Exception as e:
        st.error(f"Error generating questions: {str(e)}")
        st.info(
            "Note: Free tier has rate limits. Consider adding a small delay between requests or upgrading to PRO plan ($9/month) for higher limits.")
        return []


def main():
    st.title("Quiz Generator App (Powered by Hugging Face)")
    st.caption(f"Using model: {MODEL_NAME} | Free tier with rate limits")

    # Text input for user to paste content
    text_content = st.text_area("Paste the text content here:", height=200)

    # Dropdown for selecting quiz level
    quiz_level = st.selectbox("Select quiz level:", ["Easy", "Medium", "Hard"])
    quiz_level_lower = quiz_level.lower()

    # Number of questions selector
    num_questions = st.slider("Number of questions:", min_value=5, max_value=25, value=25, step=5)

    # Initialize session_state
    if 'quiz_generated' not in st.session_state:
        st.session_state.quiz_generated = False

    # Track if Generate Quiz button is clicked
    if not st.session_state.quiz_generated:
        st.session_state.quiz_generated = st.button("Generate Quiz")

    if st.session_state.quiz_generated:
        if not text_content.strip():
            st.error("Please paste some text content first!")
            st.session_state.quiz_generated = False
            return

        with st.spinner(f"Generating {num_questions} questions... This may take a moment."):
            questions = fetch_questions(
                text_content=text_content,
                quiz_level=quiz_level_lower,
                num_questions=num_questions
            )

        if not questions:
            st.error("Failed to generate questions. Please try again or reduce the number of questions.")
            return

        # Display questions with radio buttons
        selected_options = []
        correct_answers = []

        for idx, question in enumerate(questions):
            st.subheader(f"Question {idx + 1}: {question['mcq']}")
            options = list(question["options"].values())
            selected_option = st.radio(
                "Select your answer:",
                options,
                key=f"q_{idx}",
                index=None,
                label_visibility="collapsed"
            )
            selected_options.append(selected_option)
            correct_answers.append(question["options"][question["correct"]])
            st.divider()

        # Submit button
        if st.button("Submit Quiz"):
            marks = 0
            st.header("📊 Quiz Result:")

            for i, question in enumerate(questions):
                selected_option = selected_options[i]
                correct_option = correct_answers[i]

                with st.expander(f"Question {i + 1}: {question['mcq']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**You selected:** {selected_option}")
                    with col2:
                        st.write(f"**Correct answer:** {correct_option}")

                    if selected_option == correct_option:
                        marks += 1
                        st.success("✅ Correct!")
                    else:
                        st.error("❌ Incorrect")

            st.subheader(f"🎯 You scored **{marks}** out of **{len(questions)}**")
            percentage = (marks / len(questions)) * 100
            st.progress(percentage / 100)
            st.write(f"**Percentage:** {percentage:.1f}%")


if __name__ == "__main__":
    main()