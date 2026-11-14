import sys
import ollama

LLM_MODEL = "gemma2:2b"


def init_ollama():
    print("  Checking Ollama...")
    try:
        ollama.list()
    except Exception:
        print("❌ Ollama not running! Start it with: sudo systemctl enable --now ollama")
        sys.exit(1)

#if the user says shut down, goodbye, exit or any related words respond with SHUTDOWN and don't consider stop because it may be for motors.

def generate_response(user_text):
    print("💭 Thinking...")

    system_prompt = """
        You are Orex, a friendly voice-assistant robot that controls your motors for movement created by Amro.
        Convert voice commands to motor controls while being friendly.

        if it's a movement command, respond with motor control instructions only in the format:
        MOVE <direction> <duration> <speed> 
        where <direction> is FORWARD, BACKWARD, LEFT, or RIGHT, <duration> is in seconds, and <speed> is a number between 200 and 250.
        For example: MOVE FORWARD 2 220
        
        
        If it's not a movement command, respond normally but keep it concise and friendly.
        """
    try:
        resp = ollama.chat(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text}
            ],
            options={
                "temperature": 0.3,
                "num_predict": 50,
                "top_p": 0.6,
            }
        )
        return resp["message"]["content"].strip()
    except Exception as e:
        print(f"❌ LLM Error: {e}")
        return "I'm sorry, I had trouble processing that."
