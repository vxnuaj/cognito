# Getting Started with Orgo

## 1. Install the SDK
```bash
pip install orgo
```

## 2. Set up environment
```bash
export ORGO_API_KEY=your_api_key
```
Or add to `.env`:
```
ORGO_API_KEY=your_api_key
```
Get an API key: [Create an account](https://orgo.ai).

## 3. Connect to a computer
```python
from orgo import Computer
computer = Computer()  # Uses ORGO_API_KEY
# Or connect to existing:
computer = Computer(project_id="existing_id")
```

## 4. Perform actions
```python
computer.left_click(100, 200)
computer.right_click(300, 400)
computer.double_click(500, 300)
computer.type("Hello world")
computer.key("Enter")
screenshot = computer.screenshot()
computer.stop()    # Optional
computer.start()   # Optional
computer.restart() # Optional
```

## 5. Use Claude with natural language
Install Anthropic SDK:
```bash
pip install anthropic
```
Set Anthropic API key:
```python
import os
os.environ["ANTHROPIC_API_KEY"] = "your_anthropic_api_key"
```
Control with Claude:
```python
computer.prompt("Open Firefox and search for 'Anthropic Claude'")
```

## Complete Example
```python
import os
from orgo import Computer

os.environ["ORGO_API_KEY"] = "your_orgo_api_key"
os.environ["ANTHROPIC_API_KEY"] = "your_anthropic_api_key"

computer = Computer()

try:
    def progress_callback(event_type, event_data):
        if event_type == "text":
            print(f"Claude: {event_data}")
        elif event_type == "tool_use":
            print(f"Action: {event_data['action']}")
        elif event_type == "error":
            print(f"Error: {event_data}")

    messages = computer.prompt(
        "Open Firefox, go to anthropic.com, and take a screenshot",
        callback=progress_callback,
        model="claude-sonnet-4-20250514",
        thinking_enabled=True,
        max_iterations=10
    )

    print("Task complete!")
finally:
    computer.destroy()  # Free up project slot
```

## Manual Agent Loop
```python
import os
import anthropic
from orgo import Computer

os.environ["ORGO_API_KEY"] = "your_orgo_api_key"
api_key = "your_anthropic_api_key"

computer = Computer()
client = anthropic.Anthropic(api_key=api_key)

try:
    messages = [{"role": "user", "content": "Open Firefox and go to anthropic.com"}]
    tools = [{"type": "computer_20250124", "name": "computer", "display_width_px": 1024, "display_height_px": 768, "display_number": 1}]

    response = client.beta.messages.create(
        model="claude-sonnet-4-20250514",
        messages=messages,
        tools=tools,
        betas=["computer-use-2025-01-24"],
        max_tokens=4096
    )
    messages.append({"role": "assistant", "content": response.content})

    while True:
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                action = block.input.get("action")
                result = None
                if action == "screenshot":
                    response_data = computer.screenshot_base64()
                    result = {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": response_data
                        }
                    }
                elif action == "left_click":
                    x, y = block.input.get("coordinate", [0, 0])
                    computer.left_click(x, y)
                    result = {"type": "text", "text": f"Left click at ({x}, {y}) successful"}
                elif action == "type":
                    text = block.input.get("text", "")
                    computer.type(text)
                    result = {"type": "text", "text": f"Typed: {text}"}
                
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": [result] if result else [{"type": "text", "text": "Action completed"}]
                })
        
        if not tool_results:
            break
            
        messages.append({"role": "user", "content": tool_results})
        
        response = client.beta.messages.create(
            model="claude-sonnet-4-20250514",
            messages=messages,
            tools=tools,
            betas=["computer-use-2025-01-24"],
            max_tokens=4096
        )
        
        messages.append({"role": "assistant", "content": response.content})
    
    print("Task complete!")
finally:
    computer.destroy()
```