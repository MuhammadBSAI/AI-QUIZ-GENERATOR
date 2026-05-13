import streamlit as st
from pythonutils import read_pdf, read_docx, read_pptx
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# ================= MODEL =================
model_name = "google/flan-t5-large"

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

# ================= UI =================
st.set_page_config(page_title="AI Quiz Generator")
st.title("📚 AI Automatic Quiz Generator")
st.write("Upload PDF / DOCX / PPTX → Generate 25 MCQs")

file = st.file_uploader("Upload file", type=["pdf", "docx", "pptx"])

# ================= MCQ GENERATOR =================
def generate_mcq(text):

    all_mcqs = ""

    # split text into chunks (VERY IMPORTANT FIX)
    chunks = [text[i:i+1200] for i in range(0, len(text), 1200)]

    for chunk in chunks[:5]:  # limit for speed

        prompt = f"""
You are a teacher.

Generate 5 multiple choice questions (MCQs).

RULES:
- 4 options (A, B, C, D)
- Only ONE correct answer
- No explanation
- Strict format

TEXT:
{chunk}

FORMAT:
Q:
A)
B)
C)
D)
Answer:
"""

        inputs = tokenizer(prompt, return_tensors="pt", truncation=True)

        outputs = model.generate(
            **inputs,
            max_new_tokens=500,
            num_beams=5
        )

        result = tokenizer.decode(outputs[0], skip_special_tokens=True)

        all_mcqs += "\n\n" + result

    return all_mcqs


# ================= MAIN APP =================
if file:

    file_type = file.name.split(".")[-1]

    if file_type == "pdf":
        text = read_pdf(file)
    elif file_type == "docx":
        text = read_docx(file)
    else:
        text = read_pptx(file)

    st.success("File uploaded successfully!")

    if st.button("Generate 25 MCQs"):

        with st.spinner("Generating MCQs..."):

            quiz = generate_mcq(text[:3000])  # safety limit

        st.subheader("📘 Generated Quiz")
        st.write(quiz)