from docx import Document
import re


def parse_quiz_file(file_path: str) -> list[dict]:
    """
    .docx fayldan savollarni o'qish.

    Format:
        Savol matni
        A) variant
        B) variant
        C) variant
        D) variant
        =B

    Qaytaradi: [{"question": ..., "a": ..., "b": ..., "c": ..., "d": ..., "answer": "B"}]
    """
    doc = Document(file_path)
    full_text = "\n".join([p.text for p in doc.paragraphs])

    questions = []
    blocks = re.split(r'\n{2,}', full_text.strip())

    for block in blocks:
        lines = [l.strip() for l in block.strip().splitlines() if l.strip()]
        if len(lines) < 6:
            continue

        question = lines[0]
        options = {}
        answer = None

        for line in lines[1:]:
            if re.match(r'^A\)', line, re.IGNORECASE):
                options['a'] = re.sub(r'^A\)\s*', '', line, flags=re.IGNORECASE).strip()
            elif re.match(r'^B\)', line, re.IGNORECASE):
                options['b'] = re.sub(r'^B\)\s*', '', line, flags=re.IGNORECASE).strip()
            elif re.match(r'^C\)', line, re.IGNORECASE):
                options['c'] = re.sub(r'^C\)\s*', '', line, flags=re.IGNORECASE).strip()
            elif re.match(r'^D\)', line, re.IGNORECASE):
                options['d'] = re.sub(r'^D\)\s*', '', line, flags=re.IGNORECASE).strip()
            elif re.match(r'^=[ABCD]$', line, re.IGNORECASE):
                answer = line[1].upper()

        if len(options) == 4 and answer:
            questions.append({
                "question": question,
                "a": options['a'],
                "b": options['b'],
                "c": options['c'],
                "d": options['d'],
                "answer": answer,
            })

    return questions
