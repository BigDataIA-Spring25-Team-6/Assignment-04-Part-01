import redis
from litellm import completion
from dotenv import load_dotenv
import os

load_dotenv()


MODEL_API_KEYS = {
    "gpt-4o": {"model": "gpt-4o", "api_key": os.getenv("OPENAI_API_KEY")},  
    "gemini-flash": {"model": "gemini-2.0-flash-exp", "api_key": os.getenv("GOOGLE_API_KEY")},  
    "deepseek": {"model": "deepseek/deepseek-chat", "api_key": os.getenv("DEEPSEEK_API_KEY")}, 
    "claude": {"model": "claude-3-5-sonnet-20240620", "api_key": os.getenv("ANTHROPIC_API_KEY")},  
    "grok": {"model": "xai/grok-2-1212", "api_key": os.getenv("GROK_API_KEY")},  
}

# Connect to Redis
redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)

# Redis stream keys
TASK_STREAM = "task_stream"
RESULT_STREAM = "result_stream"

def process_task(task):
    print("in process_task")
    task_type = task.get("task_type")
    model_name = task.get("model_name")
    document_content = task.get("document_content")
    
    if not model_name or not document_content:
        print("Invalid task data")
        return
    
    api_details = MODEL_API_KEYS.get(model_name)
    if not api_details:
        print(f"Invalid model name: {model_name}")
        return
    model = api_details["model"]
    api_key = api_details["api_key"]
    
    try:
        if task_type == "summarize":
            print("in summarize")
            print(f"Model: {model}, API Key: {api_key}")
            response = completion(
                model=model,
                messages=[{"role": "user", "content": f"Summarize this document:\n{document_content}"}],
                max_tokens=200,
                api_key=api_key,
            )
            print(f"LiteLLM Response: {response}")
            summary = response["choices"][0]["message"]["content"]
            redis_client.hset(RESULT_STREAM, task["id"], summary)
            print(f"Summary processed for Task ID {task['id']}")
        
        elif task_type == "ask_question":
            print("in question")
            print(f"Model: {model}, API Key: {api_key}")
            question = task.get("question")
            if not question:
                print("Invalid question data")
                return
            
            response = completion(
                model=model,
                messages=[
                    {"role": "system", "content": f"This is a document:\n{document_content}"},
                    {"role": "user", "content": question},
                ],
                max_tokens=150,
                api_key=api_key,
            )
            answer = response["choices"][0]["message"]["content"]
            redis_client.hset(RESULT_STREAM, task["id"], answer)
            print(f"Answer processed for Task ID {task['id']}")
        
        else:
            print(f"Unknown task type: {task_type}")
    
    except Exception as e:
        print(f"Error processing Task ID {task['id']}: {str(e)}")

# Listen for new tasks in the stream
while True:
    entries = redis_client.xread({TASK_STREAM: "$"}, block=0)  # Block until new entries arrive
    for stream_name, messages in entries:
        for message_id, message_data in messages:
            print(f"Processing Task ID {message_id}")
            process_task({"id": message_id, **message_data})
