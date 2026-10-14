import json
import time

class AIService:    
    def call_ai_model_with_json(self, model, client, message, system_message = None):
        messages = []
        if system_message:
            messages.append(system_message)
        messages.append(message)

        response = client.chat.completions.create(model=model, messages=messages, response_format={'type': 'json_object'})
        raw_json = response.choices[0].message.content
        time.sleep(5)
        data_file = json.loads(raw_json)
        return data_file

