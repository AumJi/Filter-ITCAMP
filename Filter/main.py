import ollama
import dotenv, os
import json

from .system_prompt import SYSTEM_SPLIT_GROUP_PROMPT, SYSTEM_SCORE_FOR_DEK_D_PROMPT

dotenv.load_dotenv()

def load_few_shot_examples() -> str:
    try:
        example_path = os.path.join(os.path.dirname(__file__), "Prompt", "example.json")
        with open(example_path, "r", encoding="utf-8") as f:
            examples = json.load(f)
        
        formatted_examples = "\n\nFEW-SHOT EXAMPLES:\n"
        for score, cases in examples.items():
            formatted_examples += f"--- {score.upper()} ---\n"
            for i, case in enumerate(cases):
                formatted_examples += f"Example {i+1}:\n"
                formatted_examples += f"Input: {case['text']}\n"
                formatted_examples += f"Explanation: {case['explanation']}\n\n"
        return formatted_examples
    except Exception as e:
        print(f"Warning: Failed to load few-shot examples: {e}")
        return ""

FEW_SHOT_PROMPT_TEXT = load_few_shot_examples()


def evaluate_applicant_group(answer_text: str) -> dict:
    """
    Evaluates an applicant's answer into one group (pass, human_review, likely_ai)
    using the provided System prompt logic. Output is formatted strictly as JSON.
    """
    response = ollama.chat(
        model=os.getenv("MODEL_NAME","qwen3:8b"),
        messages=[
            {'role': 'system', 'content': SYSTEM_SPLIT_GROUP_PROMPT},
            {'role': 'user', 'content': answer_text}
        ],
        format='json'
    )
    
    return json.loads(response['message']['content'])

def evaluate_applicant_score_dek_d(answer_text: str, ai_likelihood_percent: int = 0) -> dict:
    """
    Grades the applicant's answer dynamically from 0 to 10 using the standard Prompts provided.
    Requires exactly two decision making data points. Output formatted strictly as JSON.
    """
    
    # Combine the system prompt with our loaded few-shot examples
    full_system_prompt = SYSTEM_SCORE_FOR_DEK_D_PROMPT + FEW_SHOT_PROMPT_TEXT
    
    # Format the user input to include the required ai_likelihood_percent as per the system prompt
    formatted_user_input = (
        f"Câu hỏi: เหตุผลในการเลือกมหาวิทยาลัย\n" # Optional Context
        f"คำตอบของผู้สมัคร: {answer_text}\n"
        f"ai_likelihood_percent: {ai_likelihood_percent}\n"
    )

    response = ollama.chat(
        model=os.getenv("MODEL_NAME","qwen3:8b"),
        messages=[
            {'role': 'system', 'content': full_system_prompt},
            {'role': 'user', 'content': formatted_user_input}
        ],
        format='json'
    )
    
    return json.loads(response['message']['content'])


if __name__ == "__main__":
    sample_answer = """1. คณะ สาขาของมหาวิทยาลัยตรงกับสิ่งที่เราสนใจมากแค่ไหน
สำหรับผม ผมจะตัดสินใจเก็บมาเป็นตัวเลือกจากข้อนี้ก่อนเป็นอันดับแรก เพราะมีความสำคัญว่าสายที่เราจะไปตรงกับมหาวิทยาลัยนี้มากขนาดไหน และเราต้องเลือกให้ถูกจุด
2. ที่อยู่ของมหาวิทยาลัย / ที่อยู่บ้าน
ในส่วนของที่อยู่ผมก็มีความคิดว่าถ้าใกล้บ้านที่สุดจะเป็นอันดีสำหรับผมและครอบครัวครับ เพราะจะได้มีเวลากลับบ้านไปหาที่บ้านเป็นครั้ง ๆ ด้วย แต่ถึงยังไงก็ต้องอยู่ให้ได้หากจำเป็นต้องอยู่ไกลบ้านจริง ๆ
3. ค่าเทอม / ค่ารถ หรือค่าต่าง ๆ รอบ ๆ มหาวิทยาลัย
ในส่วนนี้ผมก็ต้องมีการพิจารณาว่าค่าใช้จ่ายต่าง ๆ เกินงบของตนเองไหม เพราะว่าถ้าหากราคาของใช้พื้นที่โดยรอบรวมถึงค่าเทอมของมหาวิทยาลัยแพงเกินไป จะทำให้เกิดความเครียดมาก ๆ เรื่องการหาเงินเข้าศีกษาหรือใช้ชีวิต ผมจึงคิดว่าเลือกเอาที่ตนเองเลือกไหวก่อน
4. ตัวเราเอง และคนในครอบครัวมีความเห็นในด้านบวกเกี่ยวกับมหาวิทยาลัยนั้น ๆ
ข้อนี้ผมก็ให้ว่าสำคัญพอตัวครับ เพื่อจะให้คนในครอบครัวรวมถึงตัวเราสบายใจกับมหาวิทยาลัยนั้น ๆ ด้วย แล้วก็เป็นการพูดคุยกันเพื่อปรับตัวให้เข้ากับมหาวิทยาลัยด้วยครับ
5. สภาพสังคมทั้งในและนอกมหาวิทยาลัยอันตรายไหม
ในข้อนี้ผมให้เป็นข้อสุดท้ายครับเพราะว่าเรื่องความไม่ปลอดภัยตามพื้นที่ก็ลดน้อยลงแล้ว แต่ถึงอย่างไรก็ต้องมีพิจารณาไว้บ้างในบางสถานที่และสถานการณ์ เพื่อไม่ให้ตนเองไปอยู่ในจุดที่วุ่นวายและมรสุมครับ"""
    print("--- Evaluating Group ---")
    group_result = evaluate_applicant_group(sample_answer)
    print(json.dumps(group_result, indent=2, ensure_ascii=False))
    
    if group_result["group"] == "pass":
        print("\n--- Evaluating Score Dek-D ---")
        # Extract ai_likelihood percentage, assuming it's returned by group evaluation
        # For this example, we default to 0 if not present
        ai_likelihood = int(group_result.get("ai_likelihood_0_10", 0) * 10)
        
        score_result = evaluate_applicant_score_dek_d(sample_answer, ai_likelihood_percent=ai_likelihood)
        print(json.dumps(score_result, indent=2, ensure_ascii=False))
        json.dumps(score_result)
